import os
import json
from pymongo import MongoClient
from datetime import datetime, timezone
import certifi

MONGO_URI = os.getenv("MONGODB_URI", "")
DB_NAME = "baseetat" 
COLLECTION_NAME = "history_events"  

def find_probable_location_timeseries():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Confirm the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB.")

        target_rame = "351L"
        target_event_timestamp = datetime(2025, 6, 24, 8, 43, 30, 456000, tzinfo=timezone.utc)

        pipeline = [
            # Stage 1: Match only geolocation events for the correct train.
            # This is very fast because 'meta' and 'timestamp' are indexed.
            {
                "$match": {
                    "meta.rame": target_rame,
                    "type": "geolocation"
                }
            },
            # Stage 2: Calculate the absolute time difference (in milliseconds).
            {
                "$addFields": {
                    "time_difference": {
                        "$abs": {
                            "$subtract": ["$timestamp", target_event_timestamp]
                        }
                    }
                }
            },
            # Stage 3: Sort by the time difference to find the closest match.
            {
                "$sort": {
                    "time_difference": 1
                }
            },
            # Stage 4: Keep only the single best match.
            {
                "$limit": 1
            },
            # Stage 5: (Optional) Project a clean output.
            {
                "$project": {
                    "_id": 0,
                    "found_for_rame": "$meta.rame",
                    "target_event_timestamp": target_event_timestamp,
                    "probable_location": "$location",
                    "location_timestamp": "$timestamp",
                    "time_difference_ms": "$time_difference"
                }
            }
        ]

        # Execute the aggregation
        cursor = collection.aggregate(pipeline)
        result = list(cursor)

        # --- Display the Result ---
        if result:
            print("\nFound the most probable location:")
            print(json.dumps(result[0], indent=2, default=str))
        else:
            print(f"\nCould not find a location for rame '{target_rame}' near the specified time.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the connection is closed
        client.close()
        print("\nConnection to MongoDB closed.")

if __name__ == "__main__":
    find_probable_location_timeseries()