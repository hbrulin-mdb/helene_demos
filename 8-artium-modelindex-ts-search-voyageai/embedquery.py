#!/usr/bin/env python3
import os, json, requests, sys

ATLAS_AI_API_KEY = os.getenv("ATLAS_AI_API_KEY", "")  # the key you generated in Atlas AI Model Service
MODEL = os.getenv("VOYAGE_MODEL", "voyage-4")
OUTPUT_DIM = int(os.getenv("VOYAGE_DIM", "1024"))
API_URL = "https://ai.mongodb.com/v1/embeddings"

def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python embed_query.py "your query text here"')

    query = sys.argv[1]
    r = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ATLAS_AI_API_KEY}",
        },
        json={
            "input": [query],
            "model": MODEL,
            "output_dimension": OUTPUT_DIM,
            "output_dtype": "float",
            # "input_type": "query"
        },
        timeout=60
    )
    r.raise_for_status()
    vec = r.json()["data"][0]["embedding"]
    print(json.dumps(vec))

if __name__ == "__main__":
    main()
