#!/usr/bin/env python3

import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import certifi

from pymongo import MongoClient, ASCENDING


# ---------------------------
# Config
# ---------------------------
MONGODB_URI =  os.getenv("MONGODB_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")  # your MongoDB URI, with credentials
DB_NAME = "artium"

EVENTS_COLL = "status_events"

DEVICE_COUNT = 200
EVENT_SEED = 42

CLEAR_EVENTS = os.getenv("CLEAR_EVENTS", "true").lower() in {"1", "true", "yes", "y"}

DEFAULT_START = "2025-12-01T00:00:00Z"
DEFAULT_END = "2026-02-04T00:00:00Z"
GEN_START = os.getenv("GEN_START", DEFAULT_START)
GEN_END = os.getenv("GEN_END", DEFAULT_END)


def parse_iso_z(s: str) -> datetime:
    # accepts "...Z" or "...+00:00"
    s2 = s.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(s2).astimezone(timezone.utc)


START_DT = parse_iso_z(GEN_START)
END_DT = parse_iso_z(GEN_END)

# ---------------------------
# Generation model
# ---------------------------
STATES = ["nominal", "degraded", "offline"]
AVAILABLE_STATES = {"nominal", "degraded"}

TRANSITIONS: Dict[str, List[Tuple[str, float]]] = {
    "nominal":  [("nominal", 0.90), ("degraded", 0.08), ("offline", 0.02)],
    "degraded": [("nominal", 0.35), ("degraded", 0.55), ("offline", 0.10)],
    "offline":  [("nominal", 0.70), ("degraded", 0.10), ("offline", 0.20)],
}

DURATION_MINMAX: Dict[str, Tuple[int, int]] = {
    "nominal":  (60, 12 * 60),
    "degraded": (15, 6 * 60),
    "offline":  (5, 3 * 60),
}


def rand_str(prefix: str = "", n: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choice(chars) for _ in range(n))


def pick_next_state(cur: str) -> str:
    r = random.random()
    acc = 0.0
    for st, p in TRANSITIONS[cur]:
        acc += p
        if r <= acc:
            return st
    return TRANSITIONS[cur][-1][0]


def pick_duration_minutes(state: str) -> int:
    lo, hi = DURATION_MINMAX[state]
    return random.randint(lo, hi)


def generate_device_meta() -> dict:
    manufacturers = ["cotep", "acme", "globex", "initech", "umbrella"]
    regions = ["QC", "IDF", "NAQ", "ARA", "OCC"]

    region = random.choice(regions)
    station = f"ST-{region}-{random.randint(1, 20):03d}"

    return {
        "screen_id": f"BEC-{region}-{random.randint(1, 999):03d}",
        "manufacturer": random.choice(manufacturers),
        "region": region,
        "station": station,
    }


def generate_events_for_device(meta: dict, start: datetime, end: datetime) -> List[dict]:
    events = []
    t = start

    cur = random.choices(
        STATES,
        weights=[0.85, 0.10, 0.05],
        k=1
    )[0]

    reasons = ["", "network", "power", "software", "unknown"]

    while t < end:
        events.append({
            "ts": t,
            "state": cur,
            "available": cur in AVAILABLE_STATES,
            "reason": random.choice(reasons),
            "meta": meta
        })

        t = t + timedelta(minutes=pick_duration_minutes(cur))
        cur = pick_next_state(cur)

    return events


def chunked(seq, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# ---------------------------
# Main
# ---------------------------
def main():
    random.seed(EVENT_SEED)

    if END_DT <= START_DT:
        raise ValueError("GEN_END must be after GEN_START")

    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]

    # Create time-series collection if missing
    if EVENTS_COLL not in db.list_collection_names():
        db.create_collection(
            EVENTS_COLL,
            timeseries={
                "timeField": "ts",
                "metaField": "meta",
                "granularity": "minutes",
            }
        )

    events_col = db[EVENTS_COLL]

    # Useful indexes for Compass filtering
    events_col.create_index([("meta.screen_id", ASCENDING), ("ts", ASCENDING)])
    events_col.create_index([("meta.station", ASCENDING), ("ts", ASCENDING)])
    events_col.create_index([("meta.region", ASCENDING), ("ts", ASCENDING)])
    events_col.create_index([("meta.manufacturer", ASCENDING), ("ts", ASCENDING)])

    if CLEAR_EVENTS:
        events_col.delete_many({})

    # Generate fleet
    metas = [generate_device_meta() for _ in range(DEVICE_COUNT)]

    # Generate events
    all_events: List[dict] = []
    for meta in metas:
        all_events.extend(generate_events_for_device(meta, START_DT, END_DT))

    # Insert in chunks
    CHUNK = 50_000
    inserted = 0
    for batch in chunked(all_events, CHUNK):
        res = events_col.insert_many(batch, ordered=False)
        inserted += len(res.inserted_ids)

    print(f"Inserted {inserted} status events into {DB_NAME}.{EVENTS_COLL}")
    print(f"Devices: {DEVICE_COUNT}")
    print(f"Range: {START_DT.isoformat()} → {END_DT.isoformat()}")


if __name__ == "__main__":
    main()