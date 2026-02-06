# create atlas sharded cluster
# load demo data

# show data in compass

# Show shards 
```sh
mongosh "mongodb+srv://cluster1.bwqnw.mongodb.net/" --apiVersion 1 --username helenebrulin
sh.status()

```

# Show doc to shard mapping
In compass, filter : {location: "US"} 
-> Show the explain output