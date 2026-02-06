import { MongoClient } from "mongodb";
import { v4 as uuidv4 } from "uuid";
import { config } from "./config.js";

function randomRloc() {
  // 6 chars A-Z0-9-ish; quick demo generator
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let s = "";
  for (let i = 0; i < 6; i++) s += chars[Math.floor(Math.random() * chars.length)];
  return s;
}

function makePnr(rloc, now = new Date()) {
  const in1d = new Date(now.getTime() + 24 * 3600 * 1000);
  const in2d = new Date(now.getTime() + 48 * 3600 * 1000);
  const in1y = new Date(now.getTime() + 365 * 24 * 3600 * 1000);

  return {
    rloc,
    schemaVersion: "2.0",
    creationDate: now,
    purgeDate: in1y,
    creatingAgencyId: "NCE1A0950",
    passengers: [
      { passengerId: 1, firstName: "WEI", lastName: "ALI", title: "MRS", type: "ADT", loyaltyProgram: null },
      { passengerId: 2, firstName: "MOHAMED", lastName: "DUPONT", title: "MRS", type: "ADT", loyaltyProgram: null },
      { passengerId: 3, firstName: "WEI", lastName: "JONES", title: "MRS", type: "ADT", loyaltyProgram: null },
    ],
    itinerary: [
      {
        segmentId: 1,
        type: "FLIGHT",
        status: "CONFIRMED",
        carrierCode: "SQ",
        flightNumber: 276,
        origin: "FRA",
        destination: "JFK",
        departureDate: in1d,
        arrivalDate: new Date(in1d.getTime() + 60 * 60 * 1000),
        bookingClass: "Y",
      },
      {
        segmentId: 2,
        type: "HOTEL",
        status: "CONFIRMED",
        chainCode: "HL",
        propertyCode: "NYC001",
        checkInDate: new Date(in1d.getTime() + 60 * 60 * 1000),
        checkOutDate: new Date(in2d.getTime() + 60 * 60 * 1000),
      },
    ],
    contact: {
      email: "wei.ali@example.com",
      mobile: "+33612345678",
      notificationPreference: "SMS",
    },
    ticketing: {
      ticketTimeLimit: in2d,
      status: "TICKETED",
      tickets: [
        { passengerId: 1, ticketNumber: "176-826001315" },
        { passengerId: 2, ticketNumber: "176-487442784" },
        { passengerId: 3, ticketNumber: "176-946167870" },
      ],
    },
    specialServiceRequests: [{ code: "VGML", status: "HK", passengerId: 1 }],
    version: 1,
    lastUpdated: now,

    meta: {
      lastWrite: "insert", // overwritten as "upsert" when upsert creates doc
      traceId: uuidv4(),
    },
  };
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  const TPS = config.tps;
  const BULK_SIZE = config.bulkSize;

  const mixInsert = config.mixInsert;
  const mixUpsert = config.mixUpsert;
  const mixUpdate = config.mixUpdate;

  const mongo = new MongoClient(config.mongoUri, { maxPoolSize: 50 });
  await mongo.connect();

  const coll = mongo.db(config.dbName).collection(config.collName);

  // Ensure rloc is unique-ish so upserts/updates are meaningful
  await coll.createIndex({ rloc: 1 }, { unique: true });

  console.log("Loadgen connected. Target:", { TPS, BULK_SIZE, mixInsert, mixUpsert, mixUpdate });

  let opsSent = 0;
  let lastLog = Date.now();

  // Pre-generate some rlocs so updates have existing docs to hit
  const existingRlocs = [];

  while (true) {
    const start = Date.now();

    const ops = [];
    for (let i = 0; i < BULK_SIZE; i++) {
      const roll = Math.random() * 100;

      if (roll < mixInsert) {
        // INSERT: new rloc
        const rloc = randomRloc();
        existingRlocs.push(rloc);

        const doc = makePnr(rloc, new Date());
        doc.meta.lastWrite = "insert";

        ops.push({ insertOne: { document: doc } });
      } else if (roll < mixInsert + mixUpsert) {
          const now = new Date();
          // UPSERT: choose sometimes a new rloc (causing insert), sometimes existing (causing update)
          const createNew = existingRlocs.length === 0 || Math.random() < 0.5;
          const rloc = createNew
            ? randomRloc()
            : existingRlocs[Math.floor(Math.random() * existingRlocs.length)];

          if (createNew) existingRlocs.push(rloc);

          ops.push({
            updateOne: {
              filter: { rloc },
              update: {
                // Always updated (existing doc OR newly inserted doc)
                $set: {
                  lastUpdated: now,
                  schemaVersion: "2.0",
                  writeType: "upsert"
                },

                // Only set when the upsert inserts a brand new doc
                $setOnInsert: {
                  rloc,
                  creationDate: now,
                  purgeDate: new Date(now.getTime() + 365 * 24 * 3600 * 1000),
                  creatingAgencyId: "NCE1A0950"
                },

                $inc: { version: 1 },
              },
              upsert: true,
            },
  });
      } else {
        // UPDATE: must target existing doc; if none exist, fallback to insert
        if (existingRlocs.length === 0) {
          const rloc = randomRloc();
          existingRlocs.push(rloc);
          const doc = makePnr(rloc, new Date());
          doc.meta.lastWrite = "insert";
          ops.push({ insertOne: { document: doc } });
          continue;
        }

        const rloc = existingRlocs[Math.floor(Math.random() * existingRlocs.length)];
        const now = new Date();

        ops.push({
          updateOne: {
            filter: { rloc },
            update: {
              $set: {
                lastUpdated: now,
                "ticketing.status": Math.random() < 0.5 ? "TICKETED" : "PENDING",
                "itinerary.0.status": Math.random() < 0.5 ? "CONFIRMED" : "CHANGED",
                "meta.lastWrite": "update",
              },
              $inc: { version: 1 },
            },
            upsert: false,
          },
        });
      }
    }

    try {
      // unordered for max throughput
      await coll.bulkWrite(ops, { ordered: false });
      opsSent += ops.length;
    } catch (e) {
      // ignore duplicate key errors from inserts
      if (e?.code !== 11000) console.error("bulkWrite error:", e);
    }

    // throttle to TPS
    const elapsed = Date.now() - start;
    const targetMsPerBulk = Math.floor((BULK_SIZE / TPS) * 1000);
    const sleepMs = Math.max(0, targetMsPerBulk - elapsed);
    if (sleepMs > 0) await sleep(sleepMs);

    // periodic log
    const now = Date.now();
    if (now - lastLog >= 2000) {
      const seconds = (now - lastLog) / 1000;
      const tps = Math.round(opsSent / seconds);
      console.log(`~${tps} ops/s (last ${seconds.toFixed(1)}s), rloc pool=${existingRlocs.length}`);
      opsSent = 0;
      lastLog = now;
    }
  }
}

main().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});
