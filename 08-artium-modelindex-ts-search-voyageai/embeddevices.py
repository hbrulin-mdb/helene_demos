#!/usr/bin/env python3
import os
import time
import requests
from pymongo import MongoClient, UpdateOne
import certifi

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")  # your MongoDB URI, with credentials
DB_NAME = "artium"
COLL_NAME = "devices"

ATLAS_AI_API_KEY = os.getenv("ATLAS_AI_API_KEY", "")  # the key you generated in Atlas AI Model Service
MODEL = os.getenv("VOYAGE_MODEL", "voyage-4")     # voyage-4 / voyage-4-large / voyage-4-lite, etc.
OUTPUT_DIM = int(os.getenv("VOYAGE_DIM", "1024")) # supported: 256/512/1024/2048 for Voyage 4 series :contentReference[oaicite:2]{index=2}

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.2"))

EMBEDDING_FIELD = "embedding"   # where we store vectors
TEXT_FIELD = "search_text"      # where we store the string we embed

API_URL = "https://ai.mongodb.com/v1/embeddings"  # Atlas Embedding API :contentReference[oaicite:3]{index=3}


def build_search_text(d: dict) -> str:
    # Make this descriptive but not huge (keep it < ~1-2k chars).
    tags = d.get("tags") or []
    region = d.get("region") or d.get("meta", {}).get("region") or ""
    station = d.get("station") or d.get("meta", {}).get("station") or ""

    parts = [
        f"Device {d.get('name','')}".strip(),
        f"Manufacturer {d.get('manufacturer','')}".strip(),
        f"Generation {d.get('generation','')}".strip(),
        f"Technology {d.get('technology','')}".strip(),
        ("Tags: " + ", ".join(tags)) if tags else "",
        f"Region {region}".strip() if region else "",
        f"Station {station}".strip() if station else "",
    ]
    # include a couple additional_data keys if present and small
    ad = d.get("additional_data")
    if isinstance(ad, dict):
        # pick a couple stable keys if they exist
        for k in ["serial_number", "model", "screen_size", "os"]:
            if k in ad:
                parts.append(f"{k}: {ad[k]}")
    return ". ".join([p for p in parts if p])


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not ATLAS_AI_API_KEY:
        raise SystemExit("Missing ATLAS_AI_API_KEY env var.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ATLAS_AI_API_KEY}",
    }
    payload = {
        "input": texts,
        "model": MODEL,
        "output_dimension": OUTPUT_DIM,
        "output_dtype": "float",
        # "input_type": "document"  # optional; some clients use this; the Atlas API supports retrieval-optimized modes depending on endpoint/model
    }

    r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    # Response shape is like OpenAI-style: { data: [{ embedding: [...] }, ...] }
    return [row["embedding"] for row in data["data"]]


def main():
    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    col = client[DB_NAME][COLL_NAME]

    # only embed docs missing embedding
    cursor = col.find(
        { EMBEDDING_FIELD: { "$exists": False } },
        projection={"_id": 1, "name": 1, "manufacturer": 1, "generation": 1, "technology": 1, "tags": 1, "region": 1, "station": 1, "additional_data": 1},
        batch_size=1000
    )

    batch_docs = []
    total = 0

    for d in cursor:
        batch_docs.append(d)
        if len(batch_docs) >= BATCH_SIZE:
            total += process_batch(col, batch_docs)
            batch_docs = []
            time.sleep(SLEEP_SEC)

    if batch_docs:
        total += process_batch(col, batch_docs)

    print(f"Done. Embedded/updated {total} devices.")
    print(f"Model={MODEL} dim={OUTPUT_DIM} field={EMBEDDING_FIELD}")


def process_batch(col, docs):
    texts = [build_search_text(d) for d in docs]
    vectors = embed_texts(texts)

    ops = []
    for d, text, vec in zip(docs, texts, vectors):
        ops.append(
            UpdateOne(
                {"_id": d["_id"]},
                {"$set": {"search_text": text, "embedding": vec}}
            )
        )

    res = col.bulk_write(ops, ordered=False)
    # bulk_write returns counts; modified_count can be 0 if values identical
    return res.modified_count + res.upserted_count


if __name__ == "__main__":
    main()
