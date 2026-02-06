import os
import json
from pymongo import MongoClient
from datetime import datetime, timezone
import certifi

MONGO_URI = os.getenv("MONGODB_URI", "")   
DB_NAME = "baseetat" 
COLLECTION_NAME = "history"     

def find_probable_location():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        client.admin.command('ping')
        print("Successfully connected to MongoDB.")

        target_rame = "351L"

        # IMPORTANT: To query BSON dates, we must use timezone-aware datetime objects.
        # MongoDB stores dates in UTC, so we specify timezone.utc.
        target_date = datetime(2025, 5, 16, 0, 0, 0, tzinfo=timezone.utc)
        target_event_timestamp = datetime(2025, 5, 16, 10, 15, 32, tzinfo=timezone.utc)

        pipeline = [
            # Stage 1: Match the specific train document for the given day.
            {
                "$match": {
                    "rame": target_rame,
                    "date_etat": target_date
                }
            },
            # Stage 2: Deconstruct the geolocations array.
            {
                "$unwind": "$geolocations"
            },
            # Stage 3: Calculate the absolute time difference.
            {
                "$addFields": {
                    "time_difference": {
                        "$abs": {
                            "$subtract": ["$geolocations.timestamp", target_event_timestamp]
                        }
                    }
                }
            },
            # Stage 4: Sort by the time difference to find the closest.
            {
                "$sort": {
                    "time_difference": 1
                }
            },
            # Stage 5: Keep only the top result.
            {
                "$limit": 1
            },
            # Stage 6: Project to get a clean, final output.
            {
                "$project": {
                    "_id": 0,
                    "rame": "$rame",
                    "target_event_timestamp": target_event_timestamp,
                    "probable_location": "$geolocations.location",
                    "location_timestamp": "$geolocations.timestamp",
                    "time_difference_ms": "$time_difference"
                }
            }
        ]

        # Execute the aggregation. This returns a cursor.
        cursor = collection.aggregate(pipeline)

        # Convert the cursor to a list to get the results.
        result = list(cursor)

        # --- Display the Result ---
        if result:
            print("\nFound the most probable location:")
            # Use json.dumps for pretty printing the result dictionary.
            # default=str is used to handle non-serializable types like datetime.
            print(json.dumps(result[0], indent=2, default=str))
        else:
            print(f"\nCould not find a location for rame '{target_rame}' on {target_date.date()}.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensures that the client connection is closed when the script finishes.
        client.close()
        print("\nConnection to MongoDB closed.")


if __name__ == "__main__":
    find_probable_location()