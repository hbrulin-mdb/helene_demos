#!/usr/bin/env python3
import argparse
import base64
import os
import time
from datetime import datetime, timezone
from xmlrpc import client

from pymongo import MongoClient, InsertOne
from pymongo.errors import BulkWriteError
from pymongo.write_concern import WriteConcern



def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_payload_bytes(payload_len: int) -> str:
    """
    Return a base64 string whose decoded size is ~payload_len bytes.
    Base64 expands by ~4/3, so compute the raw bytes length accordingly.
    """
    if payload_len <= 0:
        return ""
    raw_len = (payload_len * 3) // 4  # approximate inverse of base64 expansion
    raw = os.urandom(raw_len)
    return base64.b64encode(raw).decode("ascii")


def connect(uri: str, appname: str, timeout_ms: int):
    client = MongoClient(
        uri,
        appname=appname,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
        socketTimeoutMS=timeout_ms,
        retryWrites=True,
    )
    # Force a round-trip to fail fast if URI is wrong / unreachable
    client.admin.command("ping")
    return client


def main():
    p = argparse.ArgumentParser(description="Load generator: bulk inserts to reach target GB.")
    p.add_argument("--uri", required=True, help="MongoDB connection URI (replica set URI recommended).")
    p.add_argument("--db", default="loadtest", help="Database name.")
    p.add_argument("--coll", default="events", help="Collection name.")
    p.add_argument("--target-gb", type=float, default=30.0, help="Approx GB of payload to insert.")
    p.add_argument("--doc-kb", type=int, default=16, help="Approx size per doc payload in KB.")
    p.add_argument("--batch", type=int, default=2000, help="Docs per bulk write.")
    p.add_argument("--w", default="1", help='Write concern w (e.g. "1" or "majority").')
    p.add_argument("--journal", action="store_true", help="Use j=true in write concern.")
    p.add_argument("--timeout-ms", type=int, default=20000, help="Socket/server selection timeout.")
    p.add_argument("--id-prefix", default="host", help="Prefix for _id generation.")
    args = p.parse_args()

    target_bytes = int(args.target_gb * (1024**3))
    payload_bytes = args.doc_kb * 1024

    print(f"[{now_iso()}] Connecting...")
    client = connect(args.uri, appname="rs-loadgen", timeout_ms=args.timeout_ms)

    wc_kwargs = {"w": args.w}
    if args.journal:
        wc_kwargs["j"] = True

    db = client[args.db]
    wc = WriteConcern(**wc_kwargs)
    coll = db.get_collection(args.coll, write_concern=wc)


    # To reduce memory, build payload template once per process
    payload = make_payload_bytes(payload_bytes)

    inserted_payload = 0
    inserted_docs = 0
    start = time.time()
    last_print = start

    print(
        f"[{now_iso()}] Starting load: target={args.target_gb} GB, "
        f"doc_payload~{args.doc_kb} KB, batch={args.batch}, w={args.w}{', j=true' if args.journal else ''}"
    )

    seq = 0
    while inserted_payload < target_bytes:
        ops = []
        # Generate one batch
        for _ in range(args.batch):
            seq += 1
            doc = {
                "_id": f"{args.id_prefix}-{os.getpid()}-{seq}",
                "ts": datetime.now(timezone.utc),
                "kind": "synthetic",
                "payload_b64": payload,
                "n": seq,
            }
            ops.append(InsertOne(doc))

        try:
            res = coll.bulk_write(ops, ordered=False)
            n = res.inserted_count
        except BulkWriteError as bwe:
            # If duplicate keys happen, count successful inserts
            n = bwe.details.get("nInserted", 0)

        inserted_docs += n
        inserted_payload += n * payload_bytes

        now = time.time()
        if now - last_print >= 2.0:
            elapsed = now - start
            gb = inserted_payload / (1024**3)
            rate_mb_s = (inserted_payload / (1024**2)) / elapsed if elapsed > 0 else 0.0
            print(
                f"[{now_iso()}] inserted_docs={inserted_docs:,} "
                f"approx_payload={gb:,.2f} GB "
                f"rate={rate_mb_s:,.1f} MB/s"
            )
            last_print = now

    elapsed = time.time() - start
    gb = inserted_payload / (1024**3)
    rate_mb_s = (inserted_payload / (1024**2)) / elapsed if elapsed > 0 else 0.0
    print(
        f"[{now_iso()}] DONE: inserted_docs={inserted_docs:,} "
        f"approx_payload={gb:,.2f} GB elapsed={elapsed:,.1f}s rate={rate_mb_s:,.1f} MB/s"
    )


if __name__ == "__main__":
    main()
