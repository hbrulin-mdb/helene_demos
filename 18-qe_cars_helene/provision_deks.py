import argparse
from base64 import b64decode

import certifi
from pymongo import MongoClient
from pymongo.encryption import ClientEncryption
from pymongo.encryption_options import AutoEncryptionOpts  # noqa: F401  (imported for parity)
from bson.codec_options import CodecOptions

KMS_PROVIDER_NAME = "local"
LOCAL_MASTER_KEY = b64decode(
    "b7csKuW8B1zoGeA+JLg3puwpBiMMig/Pk/k707SgFmNa5pQmW5pHT8JKKShQ8Myl7jZ5Hzy2l3oCqqSUgmUDRCxcp2/j7Y7GT/F55dTEjeu5tf4WCZuBZ5qBcBQ7FW1X"
)
KEY_VAULT_NAMESPACE = "__encryption.__keyVault"
DEK_KEY_ALT_NAMES = [
    "dek_name_vin",
    "dek_name_license_plate",
    "dek_name_model",
]


def build_client(uri: str, ca: str | None, pem: str | None) -> MongoClient:
    if pem:
        return MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsCertificateKeyFile=pem,
            tlsCAFile=ca,
        )
    kwargs = {"serverSelectionTimeoutMS": 5000}
    if uri.startswith("mongodb+srv://"):
        kwargs["tlsCAFile"] = certifi.where()
    return MongoClient(uri, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision DEKs for Queryable Encryption")
    parser.add_argument("--mongo", required=True, help="MongoDB connection string")
    parser.add_argument("--mongo-ca", default=None)
    parser.add_argument("--mongo-pem", default=None)
    args = parser.parse_args()

    client = build_client(args.mongo, args.mongo_ca, args.mongo_pem)

    vault_db, vault_coll = KEY_VAULT_NAMESPACE.split(".")
    vault = client[vault_db][vault_coll]
    vault.create_index(
        "keyAltNames",
        unique=True,
        partialFilterExpression={"keyAltNames": {"$exists": True}},
    )

    kms_providers = {KMS_PROVIDER_NAME: {"key": LOCAL_MASTER_KEY}}

    client_encryption = ClientEncryption(
        kms_providers=kms_providers,
        key_vault_namespace=KEY_VAULT_NAMESPACE,
        key_vault_client=client,
        codec_options=CodecOptions(),
    )

    try:
        for alt_name in DEK_KEY_ALT_NAMES:
            existing = vault.find_one({"keyAltNames": alt_name}, {"_id": 1})
            if existing:
                print(f"[skip] DEK already exists: {alt_name} (_id={existing['_id']})")
                continue
            key_id = client_encryption.create_data_key(
                KMS_PROVIDER_NAME, key_alt_names=[alt_name]
            )
            print(f"[created] DEK: {alt_name} (_id={key_id})")
    finally:
        client_encryption.close()
        client.close()


if __name__ == "__main__":
    main()
