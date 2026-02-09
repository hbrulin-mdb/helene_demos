# Show how to pin FCV

Connect to each member to the admin db (use port forwarding for each pod) and run db.version() : 

Also check FCV: db.adminCommand({ getParameter: 1, featureCompatibilityVersion: 1 })

It’s recommended to be on the latest patch release for your major version before upgrades.

Check that they are both version 8.0. 

# Launcg a temporary pod to run the scripts 

Why? because port forwarding breaks during failovers.

start temporary writer pod : 
```sh
kubectl -n tenant-thales run writer --rm -it \
  --image=python:3.12-slim \
  --restart=Never \
  -- bash
```

From inside the pod, my mongodb dns is : thales-mongodb-svc.tenant-thales.svc.cluster.local:27017

For replicaset, use : mongodb://thales-mongodb-svc.tenant-thales.svc.cluster.local:27017/?replicaSet=thales-mongodb&retryWrites=true&w=majority

# Create a simple write loop that survives failover 

```sh
pip install --no-cache-dir pymongo==4.*
```

Create writer.py script and copy the content of script in the folder :

```sh
cat > writer.py <<'PY'
import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError

URI = "mongodb://<USER>>:<PASSWORD>@thales-mongodb-svc.tenant-thales.svc.cluster.local:27017/?replicaSet=thales-mongodb&retryWrites=true&w=majority"

def make_client():
    # serverSelectionTimeoutMS keeps reconnects snappy during failover
    return MongoClient(URI, serverSelectionTimeoutMS=2000)

i = 0
client = make_client()
coll = client.demo.retry_writes

while True:
    try:
        doc = {"_id": i, "ts": time.time()}
        coll.insert_one(doc)   # retryable write (when supported by deployment + write concern)
        print(f"inserted {i}")
        i += 1
        time.sleep(0.2)
    except PyMongoError as e:
        print(f"write failed (will retry): {type(e).__name__}: {e}")
        # Recreate client on network/primary changes
        try:
            client.close()
        except Exception:
            pass
        time.sleep(0.5)
        client = make_client()
        coll = client.demo.retry_writes
PY
```

Launch script : 
```sh
python writer.py
```

It should start writing

# Replace the content of thales-mongodb.yaml resource with the content of the upgrade yaml file (in filder upgradefiles)

```sh
kubectl apply -f thales-mongodb.yaml
```

- Watch events : 
```sh
kubectl -n tenant-thales get mongodb thales-mongodb -w 
```
- See messages : 
```sh
kubectl -n tenant-thales describe mongodb thales-mongodb
```
-> check for warning events at the bottom
- watch stateful set roll : 
```sh
kubectl -n tenant-thales get pods -l app=thales-mongodb -w
```

- Check db.version and fcv again, on the primary
The version is now upgrades, but not FCV. 

- Check other pods : 
```sh
kubectl port-forward -n tenant-thales pod/thales-mongodb-1 27017:27017
kubectl port-forward -n tenant-thales pod/thales-mongodb-2 27017:27017
```

# Update fcv in the thales-mongodb.yaml file and reapply 
note : il faut mettre 8.2, pas 8.2.4

WARNING - you can't go back after, if you want to redo the demo, go to next step 
```sh
kubectl apply -f thales-mongodb.yaml
```

# rollback to 8.0.10 before upgrading fcv 

```sh
kubectl -n tenant-thales patch mongodb thales-mongodb --type=merge -p \
'{"spec":{"version":"8.0.10"}}'
```