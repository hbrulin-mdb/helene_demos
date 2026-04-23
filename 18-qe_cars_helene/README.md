# Queryable Encryption with Prefix Querying on Cars

This is a modified version of Brett's demo which is under this repo : https://github.com/beergeek/qe_cars. 

This repo tracks the changes I made to the repo and the information I was missing when running it for the first time : 

# Prerequisites I had to do before using the demo

## MongoDB Version must be 8.2+. 

As of April 2026, you cannot use an Atlas cluster because you can’t set the featureFlagQETextSearchPreview.  -> You must run a local mdb. 

## crypt_shared
Go to the MongoDB Enterprise download page:
👉 https://www.mongodb.com/try/download/enterprise
Then:
- Select the same version as your MongoDB server
- Select your platform (Linux / macOS / Windows)
- In Package, choose: crypt_shared

Then I changed main.py so it take the path of crypt_shared as a cli argument. 

## Script to provision DEKs

I created a script called provision_deks to provision DEKs for my cluster so that Brett's script can use them. 


# Run it 

## Brett's prereq

```sh
source venv/bin/activate
pip3 install fastapi uvicorn pydantic "pymongo[encryption]" faker PyQt6 requests
```

## Start MongoDB Server 

1. Create a data dir:
```sh                                                                                          
mkdir mongo-data
```   

2. Start mongod as a single-node replica set with the preview flag (adjust--dbpath and the mongod path to where you unpacked mdb server download):

```sh
/Users/helene.brulin/Desktop/mongodb-macos-aarch64-enterprise--8.3.0-rc5/bin/mongod \
  --dbpath /Users/helene.brulin/Desktop/qe_cars/mongo-data \
  --port 27017 \
  --bind_ip 127.0.0.1 \
  --replSet rs0 \
  --setParameter featureFlagQETextSearchPreview=true
```
  Leave it running in that terminal.          

3. In a second terminal, initiate the replica set (once):

```sh
mongosh "mongodb://127.0.0.1:27017" --eval 'rs.initiate()'
```

## Provision DEKs
```sh
python3 provision_deks.py --mongo "mongodb://127.0.0.1:27017/?replicaSet=rs0"
```


## Run the server 
```sh
  python3 main.py --mongo "mongodb://127.0.0.1:27017/?replicaSet=rs0" --srv-port 8000 --crypt-shared-lib /Users/helene.brulin/Desktop/mongo_crypt_shared_v1-macos-arm64-enterprise-8.3.0-rc5/lib/mongo_crypt_v1.dylib
```

## Run the client
```sh
python client.py
```

## Insert Documents
In the Insert tab of the client, click Insert Documents.
Then you can search by prefix by VIN or license plate.  -> needs at least 3 characters.
Check into Compass that the fields are indeed crypted inside MongoDB.