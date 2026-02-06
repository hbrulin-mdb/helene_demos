- Montrer les différents manières de visualiser la données : 
- vision sous forme de table

----

- Query 1 : 
{ equipement: "mcg", rame: "351L" }

- Montrer l'explain, car ils vont retrouver ça dans leur contexte SQL. 

- créer index

equipement: 1, rame: 1, date_etat: 1, source: 1

- remontrer l'explain : là j'utilise l'index, mais il y a tjrs un fetch

- project

{ _id: 0, rame: 1, equipement: 1 }

- Show the export to driver code.

----------------

- Aggregation : 

Count how many times each event type occurred per equipement per day and show the first and last GPS coordinates for that day
- CREATE A VIEW FROM DROP DOWN MENU 



- Validation Rules 


{
  $jsonSchema: {
    bsonType: "object",
    required: [ "equipement", "rame", "date_etat", "source", "events", "geolocations" ],
    properties: {
      equipement: {
        bsonType: "string",
        description: "must be a string and is required"
      },
      rame: {
        bsonType: "string",
        description: "must be a string and is required"
      },
      date_etat: {
        bsonType: "date",
        description: "must be a date and is required"
      },
      source: {
        bsonType: "string",
        description: "must be a string and is required"
      },
      events: {
        bsonType: "array",
        description: "must be an array of event objects",
        items: {
          bsonType: "object",
          required: [ "mesure", "valeur", "date_etat" ],
          properties: {
            mesure: { bsonType: "string" },
            valeur: { bsonType: "string" },
            date_etat: { bsonType: "date" }
          }
        }
      },
      geolocations: {
        bsonType: "array",
        description: "must be an array of geolocation objects",
        items: {
          bsonType: "object",
          required: [ "timestamp", "location" ],
          properties: {
            timestamp: { bsonType: "date" },
            location: {
              bsonType: "object",
              required: [ "type", "coordinates" ],
              properties: {
                type: { enum: [ "Point" ] },
                coordinates: {
                  bsonType: "array",
                  minItems: 2,
                  maxItems: 2,
                  items: { bsonType: "double" }
                }
              }
            }
          }
        }
      }
    }
  }
}


Explaining : 

- "equipement", "rame", "date_etat", "source", "events", "geolocations" are required.

- events must contain objects with mesure (string), valeur (string), date_etat (date).

- geolocations must contain objects with timestamp (date) and a valid GeoJSON Point with [lng, lat] doubles.

-----
- Schema Analysis

- analyse schema : avec GEOLOC -> faire une shape et montrer que la query est générée


On verra les autres outils qui aide à l'analyse avec Théo sur le monitoring. 
