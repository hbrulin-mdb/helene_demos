from pymongo import MongoClient
from bson.son import SON
import certifi


MONGO_URI =  os.getenv("MONGODB_URI", "")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["train_demo"]
positions = db["train_positions"]
zones = db["zones"]

train_state = {}  # {trainId: {"inside": bool, "zones": [zone_names]}}

print("🔍 Listening for real-time train position inserts... (Ctrl+C to stop)")

with positions.watch(full_document='updateLookup') as stream:
    for change in stream:
        if change["operationType"] != "insert":
            continue

        pos = change["fullDocument"]
        train_id = pos["trainId"]
        loc = pos["loc"]

        # Find zones that contain this point
        inside_zones = list(zones.find({
            "geometry": {"$geoIntersects": {"$geometry": loc}}
        }))

        prev_state = train_state.get(train_id, {"inside": False, "zones": []})
        is_inside = len(inside_zones) > 0

        if not prev_state["inside"] and is_inside:
            print(f"🚉 Train {train_id} ENTERED zone(s): {[z['name'] for z in inside_zones]}")
        elif prev_state["inside"] and not is_inside:
            print(f"🚉 Train {train_id} EXITED zone(s): {[z['name'] for z in prev_state['zones']]}")

        # Update state
        train_state[train_id] = {"inside": is_inside, "zones": inside_zones}