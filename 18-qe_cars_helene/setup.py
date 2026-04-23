try:
  from datetime import datetime
  from os import environ
  import os
  from typing import Dict
  import argparse
  #import boto3  
  from base64 import b64decode
  from pymongo import MongoClient
  from pymongo.errors import EncryptionError, OperationFailure, CollectionInvalid, ServerSelectionTimeoutError, ConnectionFailure
  from bson.codec_options import CodecOptions
  from bson.binary import STANDARD
  from pymongo.encryption import ClientEncryption, AutoEncryptionOpts
except ImportError as e:  
    print(f"Import error: {e}")  
    exit(1)

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
  
# ============================================================================  
# Database Helper Functions  
# ============================================================================  
  
def mdb_client(db_data, auto_encryption_opts=None) -> tuple[MongoClient | None, str | None]:  
    """  
    Create a MongoDB client with optional TLS and automatic encryption configuration.  
      
    Establishes a connection to MongoDB with support for TLS certificates and  
    Queryable Encryption automatic encryption options.  
      
    Args:  
        db_data (dict): Database configuration dictionary containing:  
            - DB_CONNECTION_STRING: MongoDB connection URI  
            - DB_TIMEOUT: Server selection timeout in milliseconds  
            - DB_TLS: Boolean indicating if TLS should be enabled  
            - DB_TLS_PEM: Optional path to client certificate file  
            - DB_TLS_CA: Path to certificate authority file  
        auto_encryption_opts (AutoEncryptionOpts, optional): Automatic encryption configuration  
            for Queryable Encryption. Defaults to None  
      
    Returns:  
        tuple[pymongo.MongoClient | None, str | None]: A tuple containing:  
            - MongoDB client instance if successful, None if error occurs  
            - Error message string if error occurs, None if successful  
    """  
    try:  
        if db_data['DB_TLS'] is True:  
            if db_data['DB_TLS_PEM'] is not None:  
                client = MongoClient(  
                    db_data['DB_CONNECTION_STRING'],  
                    serverSelectionTimeoutMS=db_data['DB_TIMEOUT'],  
                    tls=True,  
                    tlsCertificateKeyFile=db_data['DB_TLS_PEM'],  
                    tlsCAFile=db_data['DB_TLS_CA'],  
                    auto_encryption_opts=auto_encryption_opts  
                )  
            else:  
                client = MongoClient(  
                    db_data['DB_CONNECTION_STRING'],  
                    serverSelectionTimeoutMS=db_data['DB_TIMEOUT'],  
                    tls=True,  
                    tlsCAFile=db_data['DB_TLS_CA'],  
                    auto_encryption_opts=auto_encryption_opts  
                )  
        else:  
            client = MongoClient(  
                db_data['DB_CONNECTION_STRING'],  
                serverSelectionTimeoutMS=db_data['DB_TIMEOUT'],  
                auto_encryption_opts=auto_encryption_opts  
            )  
        if auto_encryption_opts is None:  
            client.admin.command('hello')  
        return client, None  
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:  
        return None, f"Cannot connect to database, please check settings in config file: {e}"  
  

# ===========================================================================
# AWS STS Token Retrieval
# ===========================================================================
def getAWSToken(assumed_role_arn: str) -> tuple[dict | None, str | None]:  
    """  
    Assume an AWS IAM role and retrieve temporary security credentials.  
      
    Uses AWS STS (Security Token Service) to assume a specified IAM role and obtain  
    temporary credentials for accessing AWS services like KMS.  
      
    Args:  
        assumed_role_arn (str): Amazon Resource Name (ARN) of the IAM role to assume  
      
    Returns:  
        tuple[dict | None, str | None]: A tuple containing:  
            - Credentials dictionary with AccessKeyId, SecretAccessKey, and SessionToken  
              if successful, None if error occurs  
            - Error message string if error occurs, None if successful  
    """  
    try:  
        sts_client = boto3.client('sts')  
        assumed_role_object = sts_client.assume_role(  
            RoleArn=assumed_role_arn,  
            RoleSessionName="applicationSession",  
            DurationSeconds=3600  
        )  
        return assumed_role_object['Credentials'], None  
    except boto3.exceptions.Boto3Error as e:  
        return None, f"AWS Token error: {e}"  
    except Exception as e:  
        return None, f"Unexpected AWS error: {e}"  

# ===========================================================================
# Retrieve or Create Data Encryption Keys (DEKs)
# ===========================================================================
def get_create_deks(  
  client: MongoClient,  
  provider_name: str,  
  kms_provider: dict,  
  key_vault_namespace: str,
  customer_master_key_attributes: dict,  
  dek_key_alt_names: list[str]
) -> list[Dict]:  
  """  
  Create or retrieve Data Encryption Keys (DEKs) by their alternate names.  
  """  
  client_encryption = None  
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
      try:  
        if client_encryption is None:  
          client_encryption = ClientEncryption(  
            kms_provider,  
            key_vault_namespace,  
            client,  
            CodecOptions(uuid_representation=STANDARD)  
          )  
            
        key = client_encryption.create_data_key(  
          kms_provider=provider_name,  
          master_key=customer_master_key_attributes,  
          key_alt_names=[dek]  
        )  
          
        if key:  
          dek_keys.append({"_id": key, "keyAltNames": [dek]})  
          print(f"Created new DEK: {dek}")  
        else:  
          if client_encryption:  
            client_encryption.close()  
          print("Cannot create DEK, failing")  
          return []  
      except EncryptionError as e:  
        print(f"ClientEncryption error: {e}")  
        if client_encryption:  
          client_encryption.close()  
        return []  
      
  if client_encryption:  
    client_encryption.close()  
    
  return dek_keys  

# ===========================================================================
# Create Encrypted Collection with Encrypted Fields
# ===========================================================================
def create_collection(
  client: MongoClient,
  kms_provider: dict,
  kms_provider_name: str,
  master_key_attributes: dict,
  key_vault_namespace: str,
  encrypted_db_name: str,
  encrypted_coll_name: str,
  schema_map_fields: dict,
  config_data: dict
) -> bool:
          
  # Create schema map  
  encrypted_fields_map = {  
      f"{encrypted_db_name}.{encrypted_coll_name}": schema_map_fields  
  }  
    
  # Create AutoEncryptionOpts  
  auto_encryption = AutoEncryptionOpts(  
      kms_providers=kms_provider,  
      key_vault_namespace=key_vault_namespace,  
      encrypted_fields_map=encrypted_fields_map,  
      bypass_auto_encryption=True
  )

  encrypted_client, err = mdb_client(config_data, auto_encryption_opts=auto_encryption)
  if err:  
    print(f"{RED}Failed to create encrypted client: {err}{RESET}")  
    return False
  print(f"{GREEN}✅ Encrypted client created successfully{RESET}")
    
  # Create ClientEncryption for manual operations for legacy method (if needed) 
  #client_encryption = ClientEncryption(  
  #    kms_providers=kms_provider,
  #    key_vault_namespace=key_vault_namespace,
  #    key_vault_client=client,
  #    codec_options=CodecOptions(uuid_representation=STANDARD)  
  #)  
  #print("✅ ClientEncryption created")  
  #db = client[encrypted_db_name]
    
  # Create collection if it doesn't exist  
  try: 
      encrypted_client[encrypted_db_name].create_collection(encrypted_coll_name)
      # The following is the legacy method
      #client_encryption.create_encrypted_collection( 
      #    database=db, 
      #    name=encrypted_coll_name,
      #    kms_provider=kms_provider_name,
      #    master_key=master_key_attributes,
      #    encrypted_fields=schema_map_fields,
      #    check_exists=True
      #)  
      print("✅ Collection created")
      encrypted_client.close()
      return True
  except CollectionInvalid:  
      print("Collection already exists") 
      return True
  except OperationFailure as e:  
      print(f"Could not create collection: {e}")
      return False

# ===========================================================================
# Check if Encrypted Collection Exists and Has Correct Schema
# ===========================================================================
def check_encrypted_collection(client: MongoClient, encrypted_db_name: str, encrypted_coll_name: str) -> bool:
  """Check if the encrypted collection exists and has the correct encrypted fields.
  
  Returns True if the collection exists and has the correct schema, False otherwise.
  """
  try:
    coll_info = client[encrypted_db_name].list_collections(filter={"name": encrypted_coll_name})
    for coll in coll_info:
      if coll["name"] == encrypted_coll_name:
        options = coll.get("options", {})
        encrypted_fields = options.get("encryptedFields", {})
        print(f"{YELLOW}Encrypted collection exists and defined as:{RESET}")
        print(encrypted_fields.get("fields", []))
        return True
    print(f"{RED}Encrypted collection does not exist{RESET}")
    return False
  except Exception as e:
    print(f"Error checking encrypted collection: {e}")
    return False
  
def create_key_vault_index(client: MongoClient, key_vault_namespace: str) -> bool:
  """Create a unique index on the keyAltNames field in the key vault collection."""
  try:
    db_name, coll_name = key_vault_namespace.split(".")
    client[db_name][coll_name].create_index("keyAltNames", unique=True, partialFilterExpression={"keyAltNames": {"$exists": True}})
    print(f"{GREEN}✅ Unique index on keyAltNames created in key vault collection{RESET}")
    return True
  except Exception as e:
    print(f"Error creating index on key vault collection: {e}")
    return False
  
def check_key_vault_index(client: MongoClient, key_vault_namespace: str) -> bool:
  """Check if the unique index on keyAltNames exists in the key vault collection."""
  try:
    db_name, coll_name = key_vault_namespace.split(".")
    indexes = client[db_name][coll_name].index_information()
    for index in indexes.values():
      if index.get("key") == [("keyAltNames", 1)] and index.get("unique") is True:
        print(f"{GREEN}✅ Unique index on keyAltNames exists in key vault collection{RESET}")
        return True
    print(f"{RED}Unique index on keyAltNames does not exist in key vault collection{RESET}")
    return False
  except Exception as e:
    print(f"Error checking index on key vault collection: {e}")
    return False

def check_create_keyvault(client: MongoClient, key_vault_namespace: str) -> bool:
  """Check if the key vault collection exists, and create it if it doesn't."""
  try:
    db_name, coll_name = key_vault_namespace.split(".")
    if coll_name in client[db_name].list_collection_names():
      print(f"{GREEN}Key vault collection already exists, skipping creation{RESET}")
      index_correct = check_key_vault_index(client, key_vault_namespace)
      if not index_correct:
        index_created = create_key_vault_index(client, key_vault_namespace)
        if not index_created:
          print(f"{RED}Failed to create correct index on existing key vault collection{RESET}")
          return False
      return True
    else:
      client[db_name].create_collection(coll_name)
      correct_index = create_key_vault_index(client, key_vault_namespace)
      if not correct_index:
        print(f"{RED}Failed to create correct index on key vault collection{RESET}")
        return False
      print(f"{GREEN}✅ Key vault collection created{RESET}")
      return True
  except Exception as e:
    print(f"Error creating key vault collection: {e}")
    return False

def parse_args():
    parser = argparse.ArgumentParser(description="Database configuration")

    parser.add_argument(
        "--db-connection-string",
        default="mongodb://localhost:27017/?retryWrites=true&w=majority",
        help="MongoDB connection string (default: %(default)s)"
    )
    parser.add_argument(
        "--db-timeout",
        type=int,
        default=5000,
        help="Database timeout in milliseconds (default: %(default)s)"
    )
    parser.add_argument(
        "--db-tls-pem",
        default=None,
        help="Path to TLS PEM file (default: %(default)s)"
    )
    parser.add_argument(
        "--db-tls",
        action="store_true",
        default=False,
        help="Enable TLS for database connection (default: %(default)s)"
    )
    parser.add_argument(
        "--db-tls-ca",
        default=None,
        help="Path to TLS CA file (default: %(default)s)"
    )
    parser.add_argument(
        "--key-vault-namespace",
        default="__encryption.__keyVault",
        help="Key vault namespace (default: %(default)s)"
    )
    parser.add_argument(
        "--encrypted-db-name",
        default="companyData",
        help="Encrypted database name (default: %(default)s)"
    )
    parser.add_argument(
        "--encrypted-coll-name",
        default="employees",
        help="Encrypted collection name (default: %(default)s)"
    )

    return parser.parse_args()

def main():
      
  # Configuration  
  args = parse_args()
  aws = None

  config_data = {
      "DB_CONNECTION_STRING": args.db_connection_string,
      "DB_TIMEOUT":           args.db_timeout,
      "DB_TLS_PEM":           args.db_tls_pem,
      "DB_TLS":               args.db_tls,
      "DB_TLS_CA":            args.db_tls_ca,
      "KEY_VAULT_NAMESPACE":  args.key_vault_namespace,
      "ENCRYPTED_DB_NAME":    args.encrypted_db_name,
      "ENCRYPTED_COLL_NAME":  args.encrypted_coll_name,
  }
  print(config_data)
  if config_data["DB_TLS"] and config_data["DB_TLS_CA"] is None:
    raise Exception(f"{RED}TLS is enabled but DB_TLS_CA is not set{RESET}")
    
  # Initialize standard client  
  print("Connecting to MongoDB...")  
  client, err = mdb_client(config_data)  
  if err:  
    raise Exception(f"{RED}Cannot connect to MongoDB: {err}{RESET}")  
  print(f"{GREEN}✅ Connected to MongoDB{RESET}")  
    
  if aws:
    # AWS KMS Configuration  
    cmk = environ.get("AWS_KEY_ARN")  
    if cmk is None:  
      raise Exception(f"{RED}AWS_KEY_ARN environment variable not set{RESET}")  

    cmk_region = environ.get("AWS_KEY_REGION")  
    if cmk_region is None:  
      raise Exception(f"{RED}AWS_KEY_REGION environment variable not set{RESET}")  

    assumed_role_arn = environ.get("AWS_ASSUME_ROLE_ARN")  
    if assumed_role_arn is None:  
      raise Exception(f"{RED}AWS_ASSUME_ROLE_ARN environment variable not set{RESET}")  
    
  #print("Assuming AWS role...")  
  #assumed_role_object, err = getAWSToken(assumed_role_arn)  
  #if err is not None:  
  #  raise Exception(f"{RED}{err}{RESET}")
  
  kms_provider_name = "local" # Change to "aws" if using AWS KMS instead of local master key
  encrypted_db_name = config_data["ENCRYPTED_DB_NAME"]
  encrypted_coll_name = config_data["ENCRYPTED_COLL_NAME"]
  key_vault_namespace = config_data["KEY_VAULT_NAMESPACE"]
    
  kms_provider = {  
    kms_provider_name: {  
      "key": b64decode("b7csKuW8B1zoGeA+JLg3puwpBiMMig/Pk/k707SgFmNa5pQmW5pHT8JKKShQ8Myl7jZ5Hzy2l3oCqqSUgmUDRCxcp2/j7Y7GT/F55dTEjeu5tf4WCZuBZ5qBcBQ7FW1X")
      #"accessKeyId": assumed_role_object['AccessKeyId'],  
      #"secretAccessKey": assumed_role_object['SecretAccessKey'],  
      #"sessionToken": assumed_role_object['SessionToken']  
    }  
  }  
  #print(f"{GREEN}✅ AWS credentials obtained{RESET}")  
    
  #customer_master_key_attributes = {  
  #  "key": cmk,  
  #  "region": cmk_region  
  #}  
    
  # Create or retrieve DEKs  
  print(f"{CYAN}Creating/retrieving Data Encryption Keys...{RESET}")  
  dek_key_alt_names = [  
    "dek_name_vin", 
    "dek_name_license_plate", 
    "dek_name_model"
  ]

  success = check_create_keyvault(client, key_vault_namespace)
  if not success:
    raise Exception(f"{RED}Failed to check/create key vault collection{RESET}")
    
  dek_keys = get_create_deks(  
    client,  
    kms_provider_name,  
    kms_provider,  
    key_vault_namespace,
    None,  # customer_master_key_attributes is not used with local KMS
    dek_key_alt_names  
  )  
  
  if len(dek_keys) != len(dek_key_alt_names):  
    raise Exception(f"{RED}Could not create or get all DEKs{RESET}")  
  
  print(f"{GREEN}✅ DEKs ready: {', '.join(dek['keyAltNames'][0] for dek in dek_keys)}{RESET}")
    
  # Define encrypted fields  
  fields = {  
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
  
  print(f"{GREEN}✅ Created/retrieved {len(dek_keys)} DEKs{RESET}")
  print("fields map:")
  print(fields)

  exists = check_encrypted_collection(client, encrypted_db_name, encrypted_coll_name)
  if exists:
    print(f"{YELLOW}Encrypted collection already exists, skipping creation. We recommend checking the schema and DEKs.{RESET}")
  else:
    create_collection(
      client,
      kms_provider,
      kms_provider_name,
      None,
      key_vault_namespace,
      encrypted_db_name,
      encrypted_coll_name,
      fields,
      config_data
    )  
    print(f"{GREEN}✅ Encrypted collection created with defined schema{RESET}")

if __name__ == "__main__":
  main()