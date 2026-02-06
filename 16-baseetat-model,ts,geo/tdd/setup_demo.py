from pymongo import MongoClient
from datetime import datetime
import certifi

MONGO_URI = os.getenv("MONGODB_URI", "")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["train_demo"]

# --- Zones collection ---
db.create_collection("zones")
db.zones.create_index([("geometry", "2dsphere")])

db.zones.insert_many([
    {
        "_id": "zoneA",
        "name": "Central Station Zone",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [12.490, 41.890],
                [12.495, 41.890],
                [12.495, 41.895],
                [12.490, 41.895],
                [12.490, 41.890]
            ]]
        }
    },
    {
        "_id": "zoneB",
        "name": "Maintenance Depot",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [12.500, 41.890],
                [12.505, 41.890],
                [12.505, 41.895],
                [12.500, 41.895],
                [12.500, 41.890]
            ]]
        }
    }
])

# --- Regular train_positions collection ---
db.create_collection("train_positions")
db.train_positions.create_index([("loc", "2dsphere")])
db.train_positions.create_index("trainId")
db.train_positions.create_index("ts")

# --- Sample Data ---
positions = [
    {
        "trainId": "T1",
        "ts": datetime(2025, 10, 10, 8, 0, 0),
        "loc": {"type": "Point", "coordinates": [12.488, 41.889]},  # outside
    },
    {
        "trainId": "T1",
        "ts": datetime(2025, 10, 10, 8, 1, 0),
        "loc": {"type": "Point", "coordinates": [12.492, 41.892]},  # inside zoneA
    },
    {
        "trainId": "T1",
        "ts": datetime(2025, 10, 10, 8, 2, 0),
        "loc": {"type": "Point", "coordinates": [12.493, 41.894]},  # still inside
    },
    {
        "trainId": "T1",
        "ts": datetime(2025, 10, 10, 8, 3, 0),
        "loc": {"type": "Point", "coordinates": [12.487, 41.888]},  # outside again
    },
]

db.train_positions.insert_many(positions)

print("✅ Demo setup complete! Collections created: zones + train_positions")