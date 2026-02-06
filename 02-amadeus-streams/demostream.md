# MongoDB Change Streams Demo

## Overview

- The loadgen.js script generates inserts, updates and upserts to PNR data and batches them to a MongoDB replicaset. The data loaded is based on the pnr.json example in the folder
- The change-stream-to-kafka.js script listens to Inserts, Upserts, and Updates, and reacts to events by inserting them into a Kafka topic, specifying whether it's an insert, an upsert or an update in the messages HEADERS. 
- Configuration for the transactions, the kafka batches, and the change streams can be found in the config.js file.

Defaults : 
- 1000 TPS / sec max
- Bulk Size : 100
- 40% inserts, 30% upserts, 30% updates
- Flush to kafka batch : 500 messages 
- Flush to kafka max interval : 500 ms

Kafka runs locally with docker compose, in KRaft mode (not relying on zookeeper for metadata management). 
The topic pnr-events created with 6 partitions.

# Requirements
- Docker
- node & npm
- kcat

# Pre-demo set up 
## Kafka
```sh
docker compose up -d
docker compose logs -f kafka kafka-init

## get your compose network name :
docker network ls | grep "$(basename "$PWD")"

## start a consumer
docker run --rm -it --network amadeus_default apache/kafka:latest \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9093 \
  --topic pnr-events \
  --property print.key=true \
  --property key.separator=" | " \
  --property print.headers=true \
  --from-beginning

## Test the consumer - Start a producer
docker run --rm -it --network amadeus_default apache/kafka:latest \
  /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server kafka:9093 \
  --topic pnr-events

## Paste the following message in the producer
{"op":"INSERT","rloc":"I3BV9A","demo":"ok"}
```

## Node
```sh
npm init -y
npm i mongodb kafkajs uuid
```

## Config
Change the default configuration, notably the mongodb connection string and namespace info.

# Run the demo 

## Open the following terminals : 
- Terminal A : Kafka Consumer (launcged during setup)
- Terminal B : Will launch the listen script
- Terminal C : Will launch the load generation
- Terminal D : Will run kcat

## Open Compass and show empty collection

## Show the load config and explain : TPS, batch writes, 40% inserts, 30% upserts, 30% updates

## Show the code in change-stream-to-kafka

- changeStream = coll.watch(pipeline, watchOptions)

Then for each event in "for await (const change of changeStream)", we : 
- Save the token to persist the stream position to disk
- Label the event : Insert, Update, Upsert
- Build the kafka payload : op type, ts, ns updateDescription, fullDocument config
- Buffer the outgoing kafka messages : buffer.push({ key, value })
- When buffer is full or 500ms have passed, flush to Kafka
- Buffer is cleared and we loop to next event


## Terminal B 
```sh
node change-stream-to-kafka.js
```
The script starts listening. 

## Terminal C : 
```sh
node loadgen.js
```

It starts loading : 
```sh
~547 ops/s (last 2.2s), rloc pool=642
~552 ops/s (last 2.2s), rloc pool=1320
```

## Watch the inserts and the batch flushes to Kafka in Terminals B and C
## Watch the consumer get the messages in Terminal A 
## Terminal D 

Check the formatted output of the messages, show the different types of events, and the updateDescription field that is generated in the payload :

```sh
kcat -b localhost:9092 -t pnr-events -C -o beginning \
  -f 'Key: %k | Headers: %h | Partition: %p | Offset: %o\nValue: %s\n\n'
```
Optional : grep the required op type :   
```sh
kcat -b localhost:9092 -t pnr-events -C -o beginning \
  -f 'Key: %k | Headers: %h | Partition: %p | Offset: %o\nValue: %s\n\n' | grep UPSERT
```

## Look at the documents in Compass

## Stop the loading script and watch the flushes to Kafka stop. 





