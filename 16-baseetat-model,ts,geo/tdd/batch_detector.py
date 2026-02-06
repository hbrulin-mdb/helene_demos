from pymongo import MongoClient
import certifi

MONGO_URI = os.getenv("MONGODB_URI", "")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["train_demo"]

positions_col = db["train_positions"]
zones_col = db["zones"]

def detect_zone_events(train_id: str):
    # 1️⃣ Fetch all positions sorted by time
    positions = list(positions_col.find({"trainId": train_id}).sort("ts", 1))
    if not positions:
        print(f"No positions found for train {train_id}")
        return []

    events = []
    prev_inside = False
    prev_zones = []

    for pos in positions:
        loc = pos["loc"]

        # 2️⃣ Find zones that contain the train position
        zones = list(zones_col.find({
            "geometry": {"$geoIntersects": {"$geometry": loc}}
        }, {"name": 1, "_id": 0}))

        inside = len(zones) > 0

        # 3️⃣ Detect transitions
        if not prev_inside and inside:
            events.append({
                "trainId": train_id,
                "ts": pos["ts"],
                "eventType": "ENTER",
                "zones": [z["name"] for z in zones]
            })
        elif prev_inside and not inside:
            events.append({
                "trainId": train_id,
                "ts": pos["ts"],
                "eventType": "EXIT",
                "zones": [z["name"] for z in prev_zones]
            })

        prev_inside = inside
        prev_zones = zones

    return events


if __name__ == "__main__":
    train_ids = db.train_positions.distinct("trainId")

    print("🚦 Zone Entry/Exit Events:")
    for tid in train_ids:
        events = detect_zone_events(tid)
        for e in events:
            print(e)