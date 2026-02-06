import random
import time
from datetime import datetime
from pymongo import MongoClient
import certifi

MONGO_URI = os.getenv("MONGODB_URI", "")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["train_demo"]
positions_col = db["train_positions"]

# Define trains and base coordinates (near Rome, Italy — same as earlier demo)
trains = {
    "T1": {"lon": 12.488, "lat": 41.889},  # starts outside zoneA
    "T2": {"lon": 12.501, "lat": 41.891},  # starts near zoneB
}

# Movement settings
STEP = 0.001  # degrees per update (~100m)
SLEEP = 2     # seconds between position updates

def random_move(train):
    """Move a train randomly within a small bounding box."""
    # Random small change in position
    delta_lon = random.choice([-STEP, 0, STEP])
    delta_lat = random.choice([-STEP, 0, STEP])
    train["lon"] += delta_lon
    train["lat"] += delta_lat
    return train

def insert_position(train_id, lon, lat):
    """Insert one new GPS point into MongoDB."""
    doc = {
        "trainId": train_id,
        "ts": datetime.utcnow(),
        "loc": {"type": "Point", "coordinates": [lon, lat]},
    }
    positions_col.insert_one(doc)
    print(f"📡 Inserted position for {train_id}: {lon:.5f}, {lat:.5f}")

if __name__ == "__main__":
    print("🚉 Real-time position ingestion started. Ctrl+C to stop.")

    try:
        while True:
            for tid, pos in trains.items():
                pos = random_move(pos)
                insert_position(tid, pos["lon"], pos["lat"])
            time.sleep(SLEEP)
    except KeyboardInterrupt:
        print("\n🛑 Stopped real-time ingestion.")
