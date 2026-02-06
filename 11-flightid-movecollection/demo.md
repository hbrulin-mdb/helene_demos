# Connect
mongosh "mongodb+srv://cluster2.bwqnw.mongodb.net/" --apiVersion 1 --username helenebrulin

use sample_mflix

# show the cluster

show the two shards


# check state

To get a list of the available shard IDs, run sh.status()

On voit les shards, et les databases avec quel shard est leur primary

Pick a collection in explorer : Check where is the collection :

```js
db.comments.aggregate( [
  { $collStats: {} },
  { $project: { "shard": 1 } }
] )
```


# Move Collection

```js
db.adminCommand(
  {
    moveCollection: "sample_mflix.comments",
    toShard: "config"
  }
)

db.adminCommand(
  {
    moveCollection: "sample_mflix.comments",
    toShard: "atlas-rv741n-shard-0"
  }
)
```

350 seconds environ, 5 minutes

# monitor

```js
db.getSiblingDB("admin").aggregate( [
   { $currentOp: { allUsers: true, localOps: false } },
   {
      $match: {
      type: "op",
      "originatingCommand.reshardCollection": "sample_mflix.comments"
      }
   }
] )
```

-> On peut voir qu'on cherche une opération de resharding, moveCollection s'apparente à un resharding. 

```sh
db.getSiblingDB("admin").aggregate([
  { $currentOp: { allUsers: true, localOps: false } },
  {
    $match: {
      type: "op",
      "originatingCommand.reshardCollection": "sample_mflix.comments",
      desc: /RecipientService/
    }
  },
  {
    $project: {
      _id: 0,
      totalOperationTimeElapsedSecs: 1,
      remainingOperationTimeEstimatedSecs: 1,
      recipientState: 1,
      approxDocumentsToCopy: 1,
      approxBytesToCopy: 1,
      bytesCopied: 1,
      documentsCopied: 1
    }
  }
])
```

The Resharding Recipient Service is the engine that receives, clones, and syncs data on shards that will own the collection after resharding.
here I have two, one is the secondary that ill catch up after the primary's metrics which are elevant for the actual progress. 


The $currentOp pipeline outputs:

- totalOperationTimeElapsedSecs: elapsed operation time in seconds

- remainingOperationTimeEstimatedSecs: estimated time remaining in seconds for the current moveCollection operation. It is returned as -1 when a new moveCollection operation starts.

- documents Copied, bytesCopied, documentsToCopy, BytesToCopy

- there is a cloning state, and then an applying phase 


# confirm the move

```js
db.comments.aggregate( [
  { $collStats: {} },
  { $project: { "shard": 1 } }
] )
```


# Monitor bytes transferred

## Connect to a single shard - the recepient

```js
use config
db.shards.find().pretty()
```

```sh
mongosh "mongodb://atlas-rv741n-config-00-00.bwqnw.mongodb.net:27017" --username helenebrulin

# Shard 1
mongosh "mongodb://atlas-rv741n-config-00-00.bwqnw.mongodb.net:27017,atlas-rv741n-config-00-01.bwqnw.mongodb.net:27017,atlas-rv741n-config-00-02.bwqnw.mongodb.net:27017/?replicaSet=atlas-rv741n-config-0" --username helenebrulin

# shard 2
mongosh "mongodb://atlas-rv741n-shard-00-00.bwqnw.mongodb.net:27017,atlas-rv741n-shard-00-01.bwqnw.mongodb.net:27017,atlas-rv741n-shard-00-02.bwqnw.mongodb.net:27017/?replicaSet=atlas-rv741n-shard-0" --username helenebrulin
```

## run command on each shard
db.runCommand(
   {
     serverStatus: 1
   }
)

-> Show : shardingStatistics.resharding.active.bytesCopied

Number of bytes copied from donor shards to recipient shards for the current resharding operation. Number is set to 0 when a new resharding operation starts.