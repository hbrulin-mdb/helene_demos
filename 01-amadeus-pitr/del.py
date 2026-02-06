#!/usr/bin/env python3
import argparse
import time
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.write_concern import WriteConcern


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser(description="Randomly delete documents using deleteOne()")
    p.add_argument("--uri", required=True, help="MongoDB URI")
    p.add_argument("--db", default="loadtest")
    p.add_argument("--coll", default="events")
    p.add_argument("--percent", type=float, default=2.0, help="Percent of docs to delete")
    p.add_argument("--batch", type=int, default=1000, help="Deletes per batch")
    p.add_argument("--w", default="1", help='Write concern: 1 or "majority"')
    p.add_argument("--journal", action="store_true")
    p.add_argument("--sleep-ms", type=int, default=0, help="Sleep between batches (throttle)")
    args = p.parse_args()

    if not (0 < args.percent < 100):
        raise SystemExit("--percent must be between 0 and 100")

    w_val = int(args.w) if str(args.w).isdigit() else args.w
    wc = WriteConcern(w=w_val, j=args.journal)

    print(f"[{now()}] Connecting...")
    client = MongoClient(args.uri)
    coll = client[args.db].get_collection(args.coll, write_concern=wc)

    total_docs = coll.estimated_document_count()
    target = int(total_docs * (args.percent / 100.0))

    print(f"[{now()}] Collection size ≈ {total_docs:,}")
    print(f"[{now()}] Will randomly delete {target:,} docs ({args.percent}%)")

    deleted = 0
    start = time.time()

    while deleted < target:
        batch_target = min(args.batch, target - deleted)

        for _ in range(batch_target):
            doc = coll.aggregate(
                [{"$sample": {"size": 1}}, {"$project": {"_id": 1}}]
            ).next()

            coll.delete_one({"_id": doc["_id"]})
            deleted += 1

        elapsed = time.time() - start
        rate = deleted / elapsed if elapsed > 0 else 0

        print(
            f"[{now()}] deleted={deleted:,}/{target:,} "
            f"rate={rate:,.0f} docs/s"
        )

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    elapsed = time.time() - start
    print(
        f"[{now()}] DONE deleted={deleted:,} docs in {elapsed:.1f}s "
        f"({deleted/elapsed:,.0f} docs/s)"
    )


if __name__ == "__main__":
    main()
