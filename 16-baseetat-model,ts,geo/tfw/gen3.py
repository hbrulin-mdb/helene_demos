from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import certifi

# -----------------------
# MongoDB Connection
# -----------------------
MONGO_URI = os.getenv("MONGODB_URI", "")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["baseetat"]
collection = db["train_ts"]

# -----------------------
# Config
# -----------------------
trains = [
    {"equipement": "mcg", "rame": "351L", "source": "tssp_oca"},
    {"equipement": "tgv", "rame": "742B", "source": "tssp_oca"}
]

start_time = datetime(2025, 5, 16, 8, 0, 0)   # simulation start
minutes_to_generate = 120                     # 2 hours of data
interval = 30                                 # one record every 30s

# -----------------------
# Synthetic Data Generator
# -----------------------
def generate_event(ts):
    # Randomly decide event type and value
    if random.random() < 0.3:
        return {"event_type": "Door_Open", "event_value": random.choice(["true", "false"])}
    else:
        return {"event_type": "Brake_Applied", "event_value": round(random.uniform(0, 1), 2)}

def generate_geolocation(ts, base_lat, base_lon, step):
    # Drift coordinates slightly
    lat = base_lat + (random.uniform(-0.0001, 0.0001) * step)
    lon = base_lon + (random.uniform(-0.0001, 0.0001) * step)
    return {"type": "Point", "coordinates": [lon, lat]}

# -----------------------
# Main Data Insertion
# -----------------------
docs = []

for train in trains:
    base_lat = 48.95
    base_lon = 2.23
    step = 0

    for i in range(0, minutes_to_generate * 60, interval):
        ts = start_time + timedelta(seconds=i)
        step += 1

        event = generate_event(ts)
        location = generate_geolocation(ts, base_lat, base_lon, step)

        doc = {
            "metadata": train,
            "date_etat": ts,
            # Single event fields
            "event_type": event["event_type"],
            "event_value": event["event_value"],
            # GeoJSON Point directly
            "location": location
        }

        docs.append(doc)

# Bulk insert
if docs:
    collection.insert_many(docs)
    print(f"Inserted {len(docs)} synthetic documents into train_ts ✅")
