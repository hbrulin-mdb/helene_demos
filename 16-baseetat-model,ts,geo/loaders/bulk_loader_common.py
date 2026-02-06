
#!/usr/bin/env python3
import argparse
import json
import os
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from pymongo.errors import BulkWriteError
import certifi


def load_template_document(path: str):
    """
    Load a single JSON document to be duplicated.
    Accepts:
      - a plain JSON object file
      - a JSON array (uses the first element)
      - a JSONL/NDJSON file (uses the first non-empty line)
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().lstrip()
        if not content:
            raise ValueError("Template file is empty.")
        if content[0] == "{":
            return json.loads(content)
        if content[0] == "[":
            arr = json.loads(content)
            if not arr:
                raise ValueError("JSON array is empty.")
            return arr[0]
        # Assume JSONL / NDJSON
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            return json.loads(line)
    raise ValueError("Could not parse a JSON document from the file.")

def gen_batch(template_doc: dict, batch_size: int, no_ids: bool):
    """
    Create a batch of `batch_size` docs. If no_ids is False, ensure each doc
    has no _id so MongoDB will generate unique ObjectIds.
    """
    batch = []
    for _ in range(batch_size):
        doc = dict(template_doc)  # shallow copy is fine for typical docs
        if not no_ids and "_id" in doc:
            del doc["_id"]
        batch.append(doc)
    return batch

def main():
    parser = argparse.ArgumentParser(description="Duplicate-insert a JSON document into MongoDB in large volumes efficiently.")
    parser.add_argument("--uri", default=os.getenv("MONGODB_URI"), help="MongoDB Atlas connection string (or set MONGODB_URI).")
    parser.add_argument("--db", default=os.getenv("MONGODB_DB", "test"), help="Database name (default: test or MONGODB_DB).")
    parser.add_argument("--collection", required=True, help="Target collection name.")
    parser.add_argument("--file", required=True, help="Path to the JSON template (object/array/JSONL supported).")
    parser.add_argument("--count", type=int, required=True, help="How many documents to insert in total.")
    parser.add_argument("--batch-size", type=int, default=1000, help="Insert batch size (default: 1000).")
    parser.add_argument("--unordered", action="store_true", help="Use unordered bulk inserts for speed (default).")
    parser.add_argument("--ordered", dest="unordered", action="store_false", help="Use ordered inserts (slower).")
    parser.set_defaults(unordered=True)
    parser.add_argument("--no-ids", action="store_true",
                        help="Keep any _id in the template as-is (NOT recommended). By default, _id is removed so the server generates unique ObjectIds.")
    args = parser.parse_args()

    if not args.uri:
        raise SystemExit("Missing MongoDB URI. Pass --uri or set MONGODB_URI.")

    client = MongoClient(args.uri, retryWrites=True, tlsCAFile=certifi.where())
    db = client.get_database(args.db)
    coll = db.get_collection(args.collection).with_options(write_concern=WriteConcern(w=1))

    template = load_template_document(args.file)

    total = args.count
    batch_size = max(1, args.batch_size)
    inserted = 0

    print(f"Starting inserts into {db.name}.{coll.name}: total={total:,}, batch_size={batch_size}, unordered={args.unordered}")
    try:
        while inserted < total:
            remaining = total - inserted
            n = min(batch_size, remaining)
            batch = gen_batch(template, n, no_ids=args.no_ids)
            result = coll.insert_many(batch, ordered=not args.unordered)
            inserted += len(result.inserted_ids)
            if inserted % (batch_size * 10) == 0 or inserted == total:
                print(f"Progress: {inserted:,}/{total:,}")
    except BulkWriteError as bwe:
        print("BulkWriteError:", bwe.details)
        raise
    finally:
        client.close()

    print(f"Done. Inserted {inserted:,} documents into {db.name}.{coll.name}.")

if __name__ == "__main__":
    main()
