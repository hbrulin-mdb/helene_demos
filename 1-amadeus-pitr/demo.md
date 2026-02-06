# Demo setup

## Deploy a replicaset with Ops Manager

Do not activate backups yet for the replicaset (but you can activate the backup agent and monitoring agent in Servers list).

## Create a worker VM (t2.large) in the same Security Group

## Prepare the worker VM

Log in to the machine : 
```sh
ssh -i "heleneom.pem" ec2-user@ec2-35-181-55-113.eu-west-3.compute.amazonaws.com
```

Install dependencies : 
```sh
# python
sudo dnf install -y python3-pip
python3 -m pip install --user pymongo

# Mongosh - double check with private IP that the cluster is accessible
curl -LO https://downloads.mongodb.com/compass/mongosh-2.2.12-linux-x64.tgz
tar -xzf mongosh-2.2.12-linux-x64.tgz
sudo mv mongosh-2.2.12-linux-x64/bin/mongosh /usr/local/bin/
mongosh --version
mongosh "mongodb://ip-172-31-41-251.eu-west-3.compute.internal:27017" 
```

## Copy the necessary scripts into Worker VM
- load.py
- del.py

## Load data into the cluster

```sh
python3 load.py \
  --uri "mongodb://ip-172-31-41-251.eu-west-3.compute.internal:27017" \
  --db loadtest --coll events \
  --target-gb 1 \
  --doc-kb 16 \
  --batch 2000 \
  --w 1
```

WARNING : This is likely to crash ops manager if you load too much at once. I prefer to use the config above, and run it multiple times until I get 10GB of data on disk.  

## In Ops Manager 

Enable backups for the replicaset, wait for the first snapshot to be taken. -> takes approximately 15mn. 

## Prepare a Timer
To time the restore. 

# Demo Rundown

## Show the database stats

Example : 
- 517440 documents
- storage size : 10.31GB

## Explain backup cursors and PITR.

WiredTiger backup cursors allow for hot backup without having to stop the instance. They are a server-side cursor that pin a consistent snapshot of the database and exposes the exact files (WiredTiger data + journal) you need to copy to get a valid backup.

How does it works? The local agent opens a backup cursor on the mongod instance and it creates a snapshot, pinning WiredTiger tables + journal files. The writes can continue, there's no lock on the database

So backup cursors : 
- Pin a single logical timestamp
- Freeze a consistent view of all data files
- Guarantee “this is a valid recovery baseline”
-> this is the anchor of PITR.

In parallel, the agent is also copying all the oplog (tailing it), capturing all changes after that snapshot, for PITR recovery. On restore, data will be restored from the backup cursor snapshot, and all changes since its timestamp will be replayed from oplog. 

## Where is the backup data stored? Show the storage options in Admin - Backups
- For the snapshots : file system (local, enabled by default), blockstore (replicaset), S3 blockstore
- For the oplog : filesystem, S3 oplog storage

In the demo, the created stores are : 
- FS store
- oplog colocated with appdb (not recommended for production.)

## Show how to edit Snapshot Schedule
Project - Continuous Backup - Three Dots - Edit Snapshots Schedule
You also configure PITR there.

Look at the data about the replicaset's last and next snapshot, the last oplog slice...

## Show the snapshots themselves

## Start deleting documents 

The del script deletes 2% of total documents at random, each iteration. Make sure to use --sleep to avoid stressing the cluster. 

Be ready to show updated nb of docs quickly, before going to the restore. 

```sh
python3 -u del.py \
  --uri "mongodb://ip-172-31-41-251.eu-west-3.compute.internal:27017" \
  --percent 1 \
  --batch 1000 \
  --w 1
  --sleep-ms 500
```


## Restore - 1mn back

- Go back to continuous backup -> Click Restore or download - select PITR 
- Look at the restorable time ranges. 
- Restore one mn back. ! START THE TIMER. !
- Click View Status and watch the steps in real time. 


What happens behind the scenes ? 
- Restore files from the backup cursor snapshot
- Start mongod in recovery mode
- Apply journal records
- Replay oplog entries
- Stop exactly at the requested timestamp


## Go back to nb of documents and confirm it is back to previous state

