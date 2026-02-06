export const config = {
  mongoUri: "mongodb://ec2-13-38-15-105.eu-west-3.compute.amazonaws.com:27017",
  dbName: "amadeus",
  collName: "pnr",

  kafkaBrokers: (process.env.KAFKA_BROKERS || "localhost:9092").split(","),
  kafkaClientId: "mongo-cs-demo",
  kafkaTopic: "pnr-events",

  //loadgen config
  //BULK_SIZE controls how many MongoDB write operations are sent in one bulkWrite() call by your load generator.
  tps: Number(1000),
  bulkSize: Number(100),
  mixInsert: Number(40),
  mixUpsert: Number(30),
  mixUpdate: Number(30),

  // batching
  batchSize: Number(500),
  flushIntervalMS: Number(500),

  // change stream behavior
  fullDocument: "updateLookup", // “When an UPDATE happens, fetch the full document after the update and include it in the change event.”
  resumeTokenPath: "./resume-token.json",
};
