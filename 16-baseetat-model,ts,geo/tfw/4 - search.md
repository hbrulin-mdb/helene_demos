# Show index

{
  "mappings": {
    "dynamic": false,
    "fields": {
      "equipement": { "type": "autocomplete" },
      "rame": { "type": "autocomplete" },
      "source": { "type": "string" },
      "events": {
        "type": "document",
        "fields": {
          "mesure": { "type": "string" },
          "valeur": { "type": "string" },
          "date_etat": { "type": "date" }
        }
      },
      "geolocations": {
        "type": "document",
        "fields": {
          "timestamp": { "type": "date" },
          "location": { "type": "geo" }
        }
      },
      "date_etat": { "type": "date" }
    }
  }
}


{
  "mappings": {
    "dynamic": false,
    "fields": {
      "date_etat": {
        "type": "date"
      },
      "equipement": {
        "type": "autocomplete"
      },
      "events": {
        "fields": {
          "date_etat": {
            "type": "date"
          },
          "mesure": {
            "type": "string"
          },
          "valeur": {
            "type": "string"
          }
        },
        "type": "document"
      },
      "geolocations": {
        "fields": {
          "location": {
            "type": "geo"
          },
          "timestamp": {
            "type": "date"
          }
        },
        "type": "document"
      },
      "rame": {
        "type": "autocomplete"
      },
      "source": {
        "maxGrams": 15,
        "minGrams": 2,
        "tokenization": "edgeGram",
        "type": "autocomplete"
      }
    }
  }
}

minGrams → the smallest substring length to index.

maxGrams → the largest substring length to index.

---- 
# Autocomplete

db.history.aggregate([
  {
    $search: {
      index: "default",
      autocomplete: {
        query: "35",
        path: "rame"
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 0,
      rame: 1,
      equipement: 1,
      source: 1
    }
  }
])

# Full text search

The following query searches for documents where the plot field contains the phrase with a maximum distance of 10 between terms.

db.history.aggregate([
  {
    $search: {
      index: "default",
      autocomplete: {
        query: "tsp_oca",  
        path: "source",
        fuzzy: {
          maxEdits: 2,        // Levenshtein distance (1 or 2 edits allowed)
          prefixLength: 1,    // require first char to match
          maxExpansions: 50   // how many variations to check
        }
      }
    }
  },
  {
    $project: {
      _id: 0,
      equipement: 1,
      rame: 1,
      source: 1
    }
  }
])




db.history.aggregate([
  {
    $search: {
      index: "default",
      wildcard: {
        query: "Door*",
        path: "events.mesure",
        allowAnalyzedField: true
      }
    }
  },
  {
    $project: {
      _id: 0,
      rame: 1,
      equipement: 1,
      "events.mesure": 1,
      "events.valeur": 1
    }
  }
])

Show only the Door Operations : 
db.history.aggregate([
  {
    $search: {
      index: "default",
      wildcard: {
        query: "Door*",
        path: "events.mesure",
        allowAnalyzedField: true
      }
    }
  },
  {
    $project: {
      _id: 0,
      rame: 1,
      equipement: 1,
      events: {
        $filter: {
          input: "$events",
          as: "event",
          cond: { $regexMatch: { input: "$$event.mesure", regex: "^Door", options: "i" } }
        }
      }
    }
  },
  {
    $project: {
      "events.mesure": 1,
      "events.valeur": 1,
      rame: 1,
      equipement: 1
    }
  }
])


# Geo Search - Find trains within 500m

db.history.aggregate([
  {
    $search: {
      index: "default",
      geoWithin: {
        circle: {
          center: { type: "Point", coordinates: [2.226, 48.95] },
          radius: 500
        },
        path: "geolocations.location"
      }
    }
  },
  {
    $project: {
      _id: 0,
      rame: 1,
      equipement: 1,
      "geolocations.location": 1
    }
  }
])

-----

# Compound Query: Doors open near a point in timeframe

db.history.aggregate([
  {
    $search: {
      index: "default",
      compound: {
        must: [
          {
            text: { query: "Door_Open", path: "events.mesure" }
          },
          {
            geoWithin: {
              circle: {
                center: { type: "Point", coordinates: [2.226, 48.95] },
                radius: 300
              },
              path: "geolocations.location"
            }
          }
        ],
        filter: [
          {
            range: {
              path: "events.date_etat",
              gte: ISODate("2025-05-16T10:00:00Z"),
              lte: ISODate("2025-05-16T10:20:00Z")
            }
          }
        ]
      }
    }
  },
  {
    $project: {
      _id: 0,
      rame: 1,
      equipement: 1,
      "events.mesure": 1,
      "events.valeur": 1,
      "events.date_etat": 1,
      "geolocations.location": 1
    }
  }
])