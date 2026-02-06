import { MongoClient } from "mongodb";
import { Kafka } from "kafkajs";
import fs from "fs";
import { config } from "./config.js";

// where did I stop ? so change stream can resume from that point
function loadResumeToken() {
  try {
    if (!fs.existsSync(config.resumeTokenPath)) return null;
    const raw = fs.readFileSync(config.resumeTokenPath, "utf8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

//persists where change stream stopped
function saveResumeToken(token) {
  try {
    fs.writeFileSync(config.resumeTokenPath, JSON.stringify(token), "utf8");
  } catch (e) {
    console.error("Failed to save resume token:", e);
  }
}

// label event type in kafka topic
function labelEvent(change) {
  const op = change.operationType;

    if (op === "insert") {
    const marker =
      change.fullDocument?.writeType ||
      change.fullDocument?.meta?.lastWrite;

    if (marker === "upsert") return "UPSERT";
    return "INSERT";
  }

  if (op === "update") {
    const marker =
      change.fullDocument?.writeType ||
      change.fullDocument?.meta?.lastWrite;

    if (marker === "upsert") return "UPSERT";
    return "UPDATE";
  }
  if (op === "replace") return "REPLACE";
  if (op === "delete") return "DELETE"; 
  return op?.toUpperCase() || "UNKNOWN";
}

async function main() {
  const kafka = new Kafka({
    clientId: config.kafkaClientId,
    brokers: config.kafkaBrokers,
  });

  const producer = kafka.producer({
    allowAutoTopicCreation: true,
  });

  await producer.connect();
  console.log("Kafka producer connected:", config.kafkaBrokers.join(","));

  const mongo = new MongoClient(config.mongoUri, {
    maxPoolSize: 50,
  });
  await mongo.connect();
  console.log("Mongo connected.");

  const coll = mongo.db(config.dbName).collection(config.collName);

  const resumeToken = loadResumeToken();

  //config for change streams
  const watchOptions = {
    fullDocument: config.fullDocument, // "updateLookup" is in the config
    ...(resumeToken ? { resumeAfter: resumeToken } : {}),
  };

  // Only listen to inserts + updates, upserts are updates with a special marker
  const pipeline = [
    {
      $match: {
        operationType: { $in: ["insert", "update"] },
      },
    },
  ];

  console.log("Starting change stream...", {
    db: config.dbName,
    collection: config.collName,
    fullDocument: config.fullDocument,
    resume: Boolean(resumeToken),
  });

  //Start the watch
  const changeStream = coll.watch(pipeline, watchOptions);

  let buffer = [];
  let bufferedSince = Date.now();

  // takes all buffered MongoDB change events and sends them to Kafka as one batch.
  async function flush(reason) {
    if (buffer.length === 0) return;

    const messages = buffer.map((evt) => ({
      key: evt.key, 
      value: JSON.stringify(evt.value),
      headers: {
        op: Buffer.from(evt.value.op), 
      },
    }));

    await producer.send({
      topic: config.kafkaTopic,
      messages,
    });

    const dt = Date.now() - bufferedSince;
    console.log(
      `Flushed ${buffer.length} msgs to Kafka (${reason}). Took ~${dt}ms.`
    );

    buffer = [];
    bufferedSince = Date.now();
  }

  // time-based flush we don’t wait forever at low traffic. 
  const flushInterval = setInterval(() => {
    flush("timer").catch((e) => console.error("Timer flush error:", e));
  }, config.flushIntervalMS);

  const shutdown = async () => {
    console.log("Shutting down...");
    clearInterval(flushInterval);
    try {
      await flush("shutdown");
    } catch (e) {
      console.error("Flush on shutdown failed:", e);
    }
    try {
      await changeStream.close();
    } catch {}
    try {
      await mongo.close();
    } catch {}
    try {
      await producer.disconnect();
    } catch {}
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  //event processing
  for await (const change of changeStream) {
    // Persist resume token frequently so restart continues cleanly
    if (change?._id) saveResumeToken(change._id);

    const opLabel = labelEvent(change);

    const rloc = change.fullDocument?.rloc || change.documentKey?.rloc || null;

    // Build event payload sent to Kafka
    const payload = {
      op: opLabel, // INSERT | UPSERT | UPDATE
      ts: change.clusterTime, 
      ns: change.ns, // { db, coll }
      rloc,
      documentKey: change.documentKey,
      // For updates and upserts, include updateDescription (what changed)
      updateDescription: change.updateDescription,
      // include full document snapshot (with updateLookup)
      fullDocument: change.fullDocument,
    };

    buffer.push({
      key: rloc ? String(rloc) : String(change.documentKey?._id ?? ""),
      value: payload,
    });

    if (buffer.length >= config.batchSize) {
      await flush("batchSize");
    }
  }
}

main().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
