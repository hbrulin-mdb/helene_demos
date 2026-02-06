"""
Seed MongoDB Atlas with radar documents.

Prereqs:
  pip install pymongo dnspython

Run:
  python seed_radar_docs.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from pymongo import MongoClient, UpdateOne
import certifi


# ===============================
# MongoDB Atlas Configuration
# ===============================
MONGODB_ATLAS_URI = (
    "mongodb+srv://<username>:<password>@<cluster-url>/" # Replace with your MongoDB Atlas connection string
)

DB_NAME = "radar"
COLLECTION_NAME = "radars"


# ===============================
# Constants
# ===============================
AIRCRAFT_TYPES = ["aircraft", "drone", "helicopter"]
TRACKING_QUALITIES = ["stable", "intermittent", "lost", "reacquired"]
SPEED_VARIATIONS = ["normal", "erratic", "accelerating", "decelerating"]


# ===============================
# Document Generator
# ===============================
def make_doc(i: int, now_utc: datetime) -> Dict[str, Any]:
    _id = f"radar_{i:03d}"

    created_at = now_utc - timedelta(minutes=random.randint(10, 180))
    last_update = created_at + timedelta(seconds=random.randint(30, 3600))

    signal_strength = round(random.uniform(0.2, 0.99), 2)

    x = round(random.uniform(-5000, 5000), 1)
    y = round(random.uniform(-5000, 5000), 1)
    z = round(random.uniform(0, 15000), 1)

    lon = round(random.uniform(1.8, 3.2), 6)
    lat = round(random.uniform(48.3, 49.2), 6)

    speed = round(random.uniform(0, 350), 1)
    heading = round(random.uniform(0, 359.9), 1)
    vertical_speed = round(random.uniform(-30, 30), 1)

    detection_score = round(random.uniform(0, 1), 2)
    tracking_quality = random.choice(TRACKING_QUALITIES)

    if speed < 60:
        level, label = 1, "low"
    elif speed < 180:
        level, label = 2, "low"
    elif speed < 260:
        level, label = 3, "medium"
    else:
        level, label = 4, "high"

    return {
        "_id": _id,
        "type": random.choice(AIRCRAFT_TYPES),
        "signal_strength": signal_strength,
        "metadata": {
            "created_at": created_at,
            "last_update": last_update,
            "sources": [
                f"src_{random.choice(['A','B','C'])}{random.randint(1,99):02d}",
                f"src_{random.choice(['A','B','C'])}{random.randint(1,99):02d}",
            ],
        },
        "position": {
            "xyz": {"x": x, "y": y, "z": z, "unit": "meters"},
            "geo": {"type": "Point", "coordinates": [lon, lat]},
        },
        "velocity": {
            "speed": speed,
            "heading": heading,
            "vertical_speed": vertical_speed,
            "unit": "m/s",
        },
        "threat_assessment": {
            "level": level,
            "label": label,
            "dynamic_factors": {
                "speed_variation": random.choice(SPEED_VARIATIONS),
                "trajectory_deviation": random.choice([True, False]),
            },
        },
        "detection_quality": {
            "detection_score": detection_score,
            "tracking_quality": tracking_quality,
        },
    }


# ===============================
# Indexes
# ===============================
def ensure_indexes(collection) -> None:
    collection.create_index([("position.geo", "2dsphere")])
    collection.create_index([("metadata.last_update", 1)])


# ===============================
# Main
# ===============================
def main(count: int = 100, upsert: bool = False) -> None:
    #client = MongoClient(MONGODB_ATLAS_URI, tlsCAFile=certifi.where())
    client = MongoClient(MONGODB_ATLAS_URI)

    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    ensure_indexes(collection)

    now_utc = datetime.now(timezone.utc)
    docs: List[Dict[str, Any]] = [make_doc(i + 1, now_utc) for i in range(count)]

    if upsert:
        ops = [
            UpdateOne({"_id": d["_id"]}, {"$set": d}, upsert=True)
            for d in docs
        ]
        result = collection.bulk_write(ops, ordered=False)
        print(
            f"Upserted {len(result.upserted_ids or [])} documents "
            f"into {DB_NAME}.{COLLECTION_NAME}"
        )
    else:
        collection.insert_many(docs, ordered=False)
        print(f"Inserted {len(docs)} documents into {DB_NAME}.{COLLECTION_NAME}")

    client.close()


if __name__ == "__main__":
    main(count=200, upsert=False)
