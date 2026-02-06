#!/usr/bin/env python3
"""
Seed a MongoDB Atlas Time Series collection with Prometheus + Telegraf-like metrics.

- Creates a time series collection (if it doesn't exist)
- Inserts >= 200 *distinct* documents across 3 metric families:
  - radar_system
  - radar_network
  - radar_health

How to run:
  1) pip install pymongo
  2) export MONGODB_ATLAS_URI='mongodb+srv://USER:PASS@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority'
     (Windows PowerShell) $env:MONGODB_ATLAS_URI="mongodb+srv://..."
  3) python seed_timeseries_radar.py

Optional env vars:
  - MONGODB_DB        (default: "observability")
  - MONGODB_COLL      (default: "radar_metrics_ts")
  - DOC_COUNT         (default: 240)   # must be >= 200
"""

import os
import sys
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import certifi


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be an integer, got: {raw!r}")


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def round1(x: float) -> float:
    return float(f"{x:.1f}")


def make_system_doc(ts: datetime, site: str, radar_id: str) -> Dict[str, Any]:
    # Prometheus-like gauges + Telegraf-like host stats
    ram_total = random.choice([2048, 4096, 8192, 16384])
    ram_used = int(clamp(random.gauss(ram_total * 0.45, ram_total * 0.12), 256, ram_total))
    disk_used = round1(clamp(random.gauss(22.0, 6.5), 2.0, 120.0))
    disk_free = round1(clamp(random.gauss(10.0, 4.0), 1.0, 200.0))
    cpu_pct = round1(clamp(random.gauss(38.0, 12.0), 0.2, 99.8))

    return {
        "ts": ts,
        "meta": {
            "site": site,
            "radar_id": radar_id,
            "metric_family": "radar_system",
            # Optional: "source" to show where it could originate
            "source": random.choice(["prometheus", "telegraf"]),
        },
        "cpu_pct": cpu_pct,
        "ram_used_mb": ram_used,
        "ram_total_mb": ram_total,
        "disk_used_gb": disk_used,
        "disk_free_gb": disk_free,
    }


def make_network_doc(ts: datetime, site: str, radar_id: str) -> Dict[str, Any]:
    uplink = random.choice(["lte", "ethernet", "satcom", "wifi"])
    # Simulate counters and network quality
    rtt_ms = int(clamp(random.gauss(55 if uplink == "lte" else 18, 12), 1, 600))
    packet_loss = round1(clamp(abs(random.gauss(0.6, 0.8)), 0.0, 25.0))

    # Monotonic-ish counters per document (not per radar stream) for realism:
    tx_bytes = random.randint(100_000, 200_000_000)
    rx_bytes = tx_bytes + random.randint(50_000, 500_000_000)

    # LTE-only-ish metric; for non-LTE keep but vary realistically
    base_rsrp = -97 if uplink == "lte" else -70
    signal_rsrp = int(clamp(random.gauss(base_rsrp, 6), -125, -50))

    return {
        "ts": ts,
        "meta": {
            "site": site,
            "radar_id": radar_id,
            "uplink": uplink,
            "metric_family": "radar_network",
            "source": random.choice(["prometheus", "telegraf"]),
        },
        "rtt_ms": rtt_ms,
        "packet_loss_pct": packet_loss,
        "tx_bytes": tx_bytes,
        "rx_bytes": rx_bytes,
        "signal_rsrp_dbm": signal_rsrp,
    }


def make_health_doc(ts: datetime, site: str, radar_id: str) -> Dict[str, Any]:
    vendor = random.choice(["AcmeRadar", "SkyScan", "NorthWave", "OmniDetect"])
    model = random.choice(["XR-500", "XR-700", "ARX-2", "PulseX", "Vigil-9"])

    temperature = round1(clamp(random.gauss(52.0, 6.0), -10.0, 95.0))
    supply_v = round1(clamp(random.gauss(24.0, 0.9), 18.0, 28.0))
    fan_rpm = int(clamp(random.gauss(3100, 450), 0, 9000))
    error_rate = round1(clamp(abs(random.gauss(0.15, 0.25)), 0.0, 12.0))

    return {
        "ts": ts,
        "meta": {
            "site": site,
            "radar_id": radar_id,
            "vendor": vendor,
            "model": model,
            "metric_family": "radar_health",
            "source": random.choice(["prometheus", "telegraf"]),
        },
        "temperature_c": temperature,
        "supply_voltage_v": supply_v,
        "fan_rpm": fan_rpm,
        "error_rate_pct": error_rate,
    }


def ensure_timeseries_collection(db, coll_name: str) -> None:
    existing = set(db.list_collection_names())
    if coll_name in existing:
        return

    try:
        db.create_collection(
            coll_name,
            timeseries={
                "timeField": "ts",
                "metaField": "meta",
                "granularity": "minutes",
            },
            expireAfterSeconds=None,  # set an int if you want TTL expiration
        )
    except CollectionInvalid:
        # Another process may have created it between checks
        pass


def main() -> int:
    uri = "mongodb+srv://<username>:<password>@<cluster-url>/" # Replace with your MongoDB Atlas connection string

    db_name = os.getenv("MONGODB_DB", "observability").strip() or "observability"
    coll_name = os.getenv("MONGODB_COLL", "radar_metrics_ts").strip() or "radar_metrics_ts"
    doc_count = env_int("DOC_COUNT", 240)
    if doc_count < 200:
        print("ERROR: DOC_COUNT must be >= 200.", file=sys.stderr)
        return 2

    random.seed()  # system entropy

    #client = MongoClient(uri, tlsCAFile=certifi.where())
    client = MongoClient(uri)
    db = client[db_name]
    ensure_timeseries_collection(db, coll_name)
    coll = db[coll_name]

    # Build a realistic fleet
    sites = ["A1", "A2", "B1", "B2", "C1"]
    radar_ids = [f"R-{n:03d}" for n in range(1, 31)]  # 30 radars

    # Start time around your example date; spread data across ~2 days by minutes
    base_ts = datetime(2026, 1, 13, 10, 15, tzinfo=timezone.utc)

    docs: List[Dict[str, Any]] = []
    for i in range(doc_count):
        site = random.choice(sites)
        radar_id = random.choice(radar_ids)

        # Unique-ish timestamp per doc (minute resolution); add jitter so docs differ
        ts = base_ts + timedelta(minutes=i) + timedelta(seconds=random.randint(0, 50))

        family_choice = i % 3
        if family_choice == 0:
            doc = make_system_doc(ts, site, radar_id)
        elif family_choice == 1:
            doc = make_network_doc(ts, site, radar_id)
        else:
            doc = make_health_doc(ts, site, radar_id)

        # Add an extra tag to guarantee uniqueness even if randoms collide
        # (still keeps the document structure clean and queryable)
        doc["meta"]["sample_id"] = f"s-{i:05d}"

        docs.append(doc)

    # Bulk insert
    result = coll.insert_many(docs, ordered=False)

    print(f"Connected to Atlas, DB={db_name}, collection={coll_name}")
    print(f"Inserted {len(result.inserted_ids)} documents (>= 200) into a time series collection.")
    print("Example query (mongosh):")
    print(f'  db.{coll_name}.find({{"meta.metric_family":"radar_network"}}).sort({{"ts":-1}}).limit(3)')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
