import os
import random
import json
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import certifi

# --- Configuration ---
# Adjust these settings to match your MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI", "")
DB_NAME = "baseetat" 
COLLECTION_NAME = "history"     
NUM_DOCUMENTS_TO_CREATE = 50

def generate_random_timestamp(day_date):
    """Generates a random, timezone-aware timestamp for a given day."""
    random_seconds = random.randint(0, 86399)
    return day_date + timedelta(seconds=random_seconds)

def generate_data_and_insert():
    """
    Generates realistic sample data and inserts it into a MongoDB collection.
    """
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    print(f"--- Preparing to generate {NUM_DOCUMENTS_TO_CREATE} documents ---")

    try:
        # Drop the collection for a clean slate
        print(f"Dropping collection '{COLLECTION_NAME}' to ensure a fresh start...")
        db.drop_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Info: Collection probably didn't exist. {e}")

    documents = []
    
    # Pools of data for randomization
    rames = ["401A", "402B", "351L", "505X", "608Z"]
    event_types = {
        "Door_Operation": ["OPEN", "CLOSE", "LOCKED"],
        "Brake_Applied": lambda: round(random.uniform(0.1, 1.0), 2),
        "HVAC_Status": ["ON", "OFF", "ECO"],
        "Pantograph_Status": ["UP", "DOWN"],
        "Speed_Report": lambda: random.randint(40, 160)
    }
    
    start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(NUM_DOCUMENTS_TO_CREATE):
        doc_date = start_date - timedelta(days=i)
        
        # --- Generate Discrete Events ---
        events = []
        num_events = random.randint(15, 50)
        for _ in range(num_events):
            mesure = random.choice(list(event_types.keys()))
            valeur_generator = event_types[mesure]
            valeur = valeur_generator() if callable(valeur_generator) else random.choice(valeur_generator)
            
            events.append({
                "mesure": mesure,
                "valeur": str(valeur), # Store all values as strings for consistency
                "date_etat": generate_random_timestamp(doc_date)
            })
        
        # Sort events chronologically
        events.sort(key=lambda x: x['date_etat'])

        # --- Generate Geolocation History ---
        geolocations = []
        num_geo_points = random.randint(500, 2000)
        
        # Start each journey near Paris
        lat, lon = (48.8566, 2.3522)
        
        for _ in range(num_geo_points):
            # Simulate movement by adding a small random offset
            lat += random.uniform(-0.005, 0.005)
            lon += random.uniform(-0.005, 0.005)
            
            geolocations.append({
                "timestamp": generate_random_timestamp(doc_date),
                "location": {
                    "type": "Point",
                    "coordinates": [round(lon, 7), round(lat, 7)] # [longitude, latitude]
                }
            })
            
        # Sort geolocations chronologically
        geolocations.sort(key=lambda x: x['timestamp'])

        # --- Assemble the Final Document ---
        document = {
            "equipement": random.choice(["mcg", "tgv", "z2n"]),
            "rame": random.choice(rames),
            "date_etat": doc_date,
            "source": "tssp_oca_generated",
            "events": events,
            "geolocations": geolocations
        }
        documents.append(document)
        print(f"Generated document {i+1}/{NUM_DOCUMENTS_TO_CREATE} for date {doc_date.date()}")

    # --- Insert into MongoDB ---
    if documents:
        print("\nInserting generated documents into MongoDB...")
        collection.insert_many(documents)
        print(f"Successfully inserted {len(documents)} documents into '{COLLECTION_NAME}'.")
    else:
        print("No documents were generated.")
        
    client.close()
    print("\nConnection to MongoDB closed.")

if __name__ == "__main__":
    generate_data_and_insert()