import argparse
from base64 import b64decode
import sys
from fastapi.concurrency import asynccontextmanager
import uvicorn
import random
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from pymongo.encryption import AutoEncryptionOpts
from faker import Faker
from bson import ObjectId
import certifi

# Setup Faker for random data
fake = Faker()
parser = argparse.ArgumentParser(description="FastAPI MongoDB Server")
parser.add_argument("--mongo", required=True, help="MongoDB connection string", default="https://127.0.0.1:27017")
parser.add_argument("--mongo-ca", default=None)
parser.add_argument("--mongo-pem", default=None)
parser.add_argument("--srv-cert", help="Path to SSL certificate file")
parser.add_argument("--srv-key", help="Path to SSL key file")
parser.add_argument("--srv-port", type=int, default=8000)
parser.add_argument("--crypt-shared-lib", default=None, help="Path to mongo_crypt_v1 shared library")
    
args, unknown = parser.parse_known_args()

# --- Database Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    kms_provider_name = "local"
    kms_provider = {  
        kms_provider_name: {  
          "key": b64decode("b7csKuW8B1zoGeA+JLg3puwpBiMMig/Pk/k707SgFmNa5pQmW5pHT8JKKShQ8Myl7jZ5Hzy2l3oCqqSUgmUDRCxcp2/j7Y7GT/F55dTEjeu5tf4WCZuBZ5qBcBQ7FW1X")
        }  
      }  
    
    key_vault_namespace = "__encryption.__keyVault"
    encrypted_db_name = "vehicle_db"
    encrypted_coll_name = "vehicles"
    config_data = {  
            "DB_CONNECTION_STRING": args.mongo,  
            "DB_TIMEOUT": 5000,  
            "DB_TLS_PEM": args.mongo_pem, 
            "DB_TLS_CA": args.mongo_ca 
        }
    client, err = mdb_client(config_data)  
    if err:  
        raise Exception(f"Cannot connect to MongoDB: {err}")  
    
    dek_key_alt_names = [  
      "dek_name_vin",  
      "dek_name_license_plate",
      "dek_name_model"
    ]
    
    dek_keys = get_deks(  
            client,   
            key_vault_namespace,   
            dek_key_alt_names  
        )

    schema_map_fields = {  
      "fields": [  
        {  
          "path": "VIN",  
          "bsonType": "string",  
          "keyId": next(dek["_id"] for dek in dek_keys if "dek_name_vin" in dek["keyAltNames"]),  
          "queries": [ 
            {
              "queryType": "prefixPreview",  # prefix queryable
              "strMinQueryLength": 3,
              "strMaxQueryLength": 12,
              "caseSensitive": False,
              "diacriticSensitive": False,
              "contention": 8
            },
          ]
        },  
        {  
          "path": "licensePlate",  
          "bsonType": "string",  
          "keyId": next(dek["_id"] for dek in dek_keys if "dek_name_license_plate" in dek["keyAltNames"]),  
          "queries": [
            {
              "queryType": "prefixPreview",  # prefix queryable
              "strMinQueryLength": 3,
              "strMaxQueryLength": 12,
              "caseSensitive": False,
              "diacriticSensitive": False,
              "contention": 8
            },
          ]
        }
      ]  
    }  

    client.close() # Close the non-encrypted client as we will create a new one with encryption options
    # Create schema map  
    encrypted_fields_map = {  
        f"{encrypted_db_name}.{encrypted_coll_name}": schema_map_fields  
    }  

    # Create AutoEncryptionOpts
    auto_encryption = AutoEncryptionOpts(
        kms_providers=kms_provider,
        key_vault_namespace=key_vault_namespace,
        encrypted_fields_map=encrypted_fields_map,
        crypt_shared_lib_path=args.crypt_shared_lib,
        crypt_shared_lib_required=bool(args.crypt_shared_lib),
    )
    
    # Startup: Initialize MongoDB connection
    print(f"Connecting to MongoDB at {args.mongo} for encrypted client...")
    app.state.encrypted_db_client, err = mdb_client(config_data, auto_encryption_opts=auto_encryption)
    if err:
        raise Exception(f"Cannot connect to MongoDB: {err}")
    app.state.vehicles_col = app.state.encrypted_db_client["vehicle_db"]["vehicles"]
    
    yield # The app handles requests during this time
    
    # Shutdown: Clean up the connection
    print("Closing MongoDB connection...")
    app.state.encrypted_db_client.close()

app = FastAPI(title="Vehicle Data API", lifespan=lifespan)
  
# ============================================================================  
# Database Helper Functions  
# ============================================================================  
  
def mdb_client(db_data, auto_encryption_opts=None) -> tuple[MongoClient | None, str | None]:  
    try:  
        if db_data['DB_TLS_PEM']:
                client = MongoClient(  
                    db_data['DB_CONNECTION_STRING'],  
                    serverSelectionTimeoutMS=db_data['DB_TIMEOUT'],  
                    tls=True,  
                    tlsCertificateKeyFile=db_data['DB_TLS_PEM'],  
                    tlsCAFile=db_data['DB_TLS_CA'],  
                    auto_encryption_opts=auto_encryption_opts  
                )  
        else:
            kwargs = {
                "serverSelectionTimeoutMS": db_data['DB_TIMEOUT'],
                "auto_encryption_opts": auto_encryption_opts,
            }
            if db_data['DB_CONNECTION_STRING'].startswith("mongodb+srv://"):
                kwargs["tlsCAFile"] = certifi.where()
            client = MongoClient(db_data['DB_CONNECTION_STRING'], **kwargs)
        if auto_encryption_opts is None:  
            client.admin.command('hello') 
        else:
            dbs = client.admin.command('listDatabases') 
            print(dbs)
        return client, None  
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:  
        return None, f"Cannot connect to database, please check settings in config file: {e}"   

  
def get_deks(  
  client: MongoClient, 
  key_vault_namespace: str,
  dek_key_alt_names: list[str]
) -> list[Dict]:  
  """  
  Create or retrieve Data Encryption Keys (DEKs) by their alternate names.  
  """  
  dek_keys = []  
      
  for dek in dek_key_alt_names:
    if len(key_vault_namespace.split(".")) != 2:
      print("key_vault_namespace must be in the format 'db.collection'")
      return []
    key = client[key_vault_namespace.split(".")[0]][key_vault_namespace.split(".")[1]].find_one(  
      {"keyAltNames": dek},  
      {"_id": 1, "keyAltNames": 1}  
    )  
      
    if key:
      dek_keys.append({"_id": key["_id"], "keyAltNames": key["keyAltNames"]})  
      print(f"Found existing DEK: {dek}")
    else:
      print(f"DEK with keyAltName '{dek}' not found in key vault collection")  
    
  return dek_keys  

# --- Models ---

class VehicleSearchQuery(BaseModel):
    term: str

# --- API Endpoints ---

@app.post("/generate/{count}")
async def generate_vehicles(count: int, request: Request):
    if count <= 0:
        raise HTTPException(status_code=400, detail="Count must be greater than 0")
    
    docs = []
    for _ in range(count):
        doc = {
            "VIN": fake.bothify(text='??##########').upper(),
            "licensePlate": fake.bothify(text='#?##??').upper(),
            "version": fake.bothify(text='??#').upper(),
            "model": f"CLS{fake.random_number(digits=10)}",
            "name": f"{fake.first_name().lower()}",
            "manufacturer": random.choice(["renault"]),
            "energySource": random.choice(["petrol", "diesel", "electric", "hybrid"]),
            "vehicleType": random.choice(["passenger car", "truck", "bus", "van"]),
            "kilometres": random.randint(0, 300000)
        }
        docs.append(doc)
    
    print(f"Client details: {request.app.state.vehicles_col}")
    result = request.app.state.vehicles_col.insert_many(docs)
    return {"inserted_count": len(result.inserted_ids)}

@app.post("/search")
async def search_vehicles(query: VehicleSearchQuery, request: Request):
    # Build the $match stage dynamically
    print(f"Search term: {query.term}")
    match_stage = []
    match_stage.append({
        "$encStrStartsWith": {
            "input": "$VIN",
            "prefix": query.term
        }
    })
    match_stage.append({
        "$encStrStartsWith": {
            "input": "$licensePlate",
            "prefix": query.term
        }
    })
    #match_stage.append(["$model", query.term])
            
    
    if not match_stage:
        raise HTTPException(status_code=400, detail="Provide at least one search field")

    pipeline = [{"$match": {"$expr": {"$or": match_stage}}},{"$project": {"__safeContent__": 0}}]
    print(f"Pipeline: {pipeline}")
    cursor = request.app.state.vehicles_col.aggregate(pipeline)
    
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId to string for JSON
        results.append(doc)
        
    return results

@app.get("/vehicles")
async def get_latest_vehicles(request: Request, limit: int = 10):
    """Fetches the latest documents up to the specified limit."""
    cursor = request.app.state.vehicles_col.find({},{"__safeContent__": 0}).limit(limit).sort({"_id": -1})
    
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"]) # Convert ObjectId to string for JSON
        results.append(doc)
        
    return results


if __name__ == "__main__":   

    # Run Server
    config = {
        "app": "main:app", # Assumes file is named main.py
        "host": "0.0.0.0",
        "port": args.srv_port,
        "reload": True
    }

    if args.srv_cert and args.srv_key:
        config["ssl_certfile"] = args.srv_cert
        config["ssl_keyfile"] = args.srv_key
        print(f"Starting server with HTTPS on port {args.srv_port}")
    else:
        print(f"Starting server with HTTP on port {args.srv_port}")

    uvicorn.run(**config)