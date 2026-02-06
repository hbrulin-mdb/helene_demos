#!/usr/bin/env python3
import os
import random
import string
from datetime import datetime, timedelta, timezone
import certifi

from pymongo import MongoClient


# -----------------------------

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")  # your MongoDB URI, with credentials
DB_NAME = "artium"
COLLECTION_NAME = "devices"
DOC_COUNT = 500


# -----------------------------
# Random helpers
# -----------------------------
def rand_str(prefix="", length=8):
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choice(chars) for _ in range(length))


def rand_ipv4():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def rand_geo_point():
    # GeoJSON expects [longitude, latitude]
    return {
        "type": "Point",
        "coordinates": [
            random.uniform(-180, 180),
            random.uniform(-85, 85),
        ],
    }


def make_additional_data():
    # Exactly 2 fields, as requested
    return [
        {"key": "serial_number", "value": rand_str("SN_", 10)},
        {"key": "cpu_usage", "value": random.randint(0, 100)},
    ]


# -----------------------------
# Document factory
# -----------------------------
def make_document(i: int) -> dict:
    now = datetime.now(timezone.utc)

    return {
        "name": f"DEVICE-{i:04d}",
        "manufacturer": random.choice(
            ["acme", "globex", "initech", "umbrella", "cotep"]
        ),
        "generation": random.choice(
            ["AO2021", "AO2022", "AO2023", "AO2024"]
        ),
        "technology": random.choice(
            ["TFT_IP", "LCD_IP", "EINK_IP"]
        ),
        "initialized": random.choice([True, False]),

        "network": {
            "hostname": f"device-{i}.example.internal",
            "ip_address": rand_ipv4(),
        },

        "external_id": {
            "id_live": rand_str("LIVE_", 8),
            "id_pasteli": rand_str("PAST_", 8),
        },

        "additional_data": make_additional_data(),

        "geo": rand_geo_point(),

        "tags": random.sample(
            ["prod", "test", "edge", "kiosk", "player", "monitoring"],
            k=random.randint(0, 3),
        ),

        "created_at": now,
        "updated_at": now,
    }


# -----------------------------
# Main
# -----------------------------
def main():
    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Create 2dsphere index on geo field
    collection.create_index([("geo", "2dsphere")])

    docs = [make_document(i) for i in range(DOC_COUNT)]

    result = collection.insert_many(docs, ordered=False)

    print(
        f"Inserted {len(result.inserted_ids)} documents into "
        f"{DB_NAME}.{COLLECTION_NAME}"
    )


if __name__ == "__main__":
    main()