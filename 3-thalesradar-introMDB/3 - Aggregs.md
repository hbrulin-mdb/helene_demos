# How many docs by type
Add a group stage : 

    {
      "_id": "$type",
      "count": { "$sum": 1 }
    }

Add a sort stage : 
{
  count: -1
}

# Show export to language

# Average speed per threat level
type it and show


# Create a View and show it

A view in MongoDB is:

- a stored aggregation pipeline
- no data is stored
- always reads fresh data
- similar to a SQL view

retriggered à chaque fois que la data change. 

# I also have the possibility to do materialized views : $out, $merge -> c'est moi qui contrôle l'exécution du pipeline, et je peux lire à tout moment le résultat de l'aggrégation précédente

- par exemple, si jhe veux computer un score de risque, qui prend en compte le niveau de menace, la vitesse, et la qualité du score de qualité de détection : 

[
  {
    "$addFields": {
      "risk_score": {
        "$add": [
          { "$multiply": ["$threat_assessment.level", 10] },
          { "$divide": ["$velocity.speed", 50] },
          {
            "$multiply": [
              { "$subtract": [1, "$detection_quality.detection_score"] },
              5
            ]
          }
        ]
      }
    }
  },
  { "$sort": { "risk_score": -1, "metadata.last_update": -1 } },
  { "$limit": 50 },
  {
    "$project": {
      "_id": 1,
      "type": 1,
      "risk_score": { "$round": ["$risk_score", 2] },
      "threat_level": "$threat_assessment.level",
      "threat_label": "$threat_assessment.label",
      "speed": "$velocity.speed",
      "detection_score": "$detection_quality.detection_score",
      "last_update": "$metadata.last_update",
      "coords": "$position.geo.coordinates"
    }
  },
  { "$out": "mv_risk_leaderboard_out" }
]

A la fin de ce pipeline, j'ai $out, qui va stocker dans ma vue matérialisée : 
- $out replaces the entire target collection every time you run it. recrée la totalité de la materialized view. 
- Great for “nightly rebuild” style jobs.


- Je peux aussi faire de l'incremental refresh, avec le stage $merge : 

[
  {
    "$addFields": {
      "risk_score": {
        "$add": [
          { "$multiply": ["$threat_assessment.level", 10] },
          { "$divide": ["$velocity.speed", 50] },
          {
            "$multiply": [
              { "$subtract": [1, "$detection_quality.detection_score"] },
              5
            ]
          }
        ]
      }
    }
  },
  {
    "$project": {
      "_id": 1,
      "type": 1,
      "risk_score": { "$round": ["$risk_score", 2] },
      "threat_level": "$threat_assessment.level",
      "threat_label": "$threat_assessment.label",
      "speed": "$velocity.speed",
      "heading": "$velocity.heading",
      "detection_score": "$detection_quality.detection_score",
      "last_update": "$metadata.last_update",
      "coords": "$position.geo.coordinates",
      "mv_refreshed_at": "$$NOW"
    }
  },
  {
    "$merge": {
      "into": "mv_risk_leaderboard_merge",
      "on": "_id",
      "whenMatched": "replace",
      "whenNotMatched": "insert"
    }
  }
]

- note the score of radar.001 
- go back to radar, filter { "_id": "radar_001" }, update : { "$set": { "threat_assessment.level": 4, "velocity.speed": 320 } }
- rerun the merge 
- go to the materialized view and refresh - see the new score



# jointure

- rappel data that is accessed together is stored together, c'est la force du modèle document
- mais si je crée par exemple une autre collection, sources, parce que j'ai de la data relative à mes sources sur mon radar, mais que je sais que je ne vais pas query cette data fréquemment en même temps que celle relative à la collection radar, mais que c'est quand même une possibilité que ce soit le cas : 


show the collection sources 
{ "_id": "src_A01", "name": "Primary Radar A01", "site": "Paris-North", "reliability": 0.92 }
{ "_id": "src_B07", "name": "Secondary Radar B07", "site": "Paris-East", "reliability": 0.78 }
{ "_id": "src_C12", "name": "Mobile Unit C12", "site": "Field Unit", "reliability": 0.65 }


- ensuite je peux faire des jointures : 

“Give me radars that have at least one joined source whose reliability is ≥ 0.8.”

- filter based on joined data attributes :

[
  {
    "$lookup": {
      "from": "sources",
      "localField": "metadata.sources",
      "foreignField": "_id",
      "as": "source_docs"
    }
  },
  {
    "$match": {
      "source_docs": {
        "$elemMatch": { "reliability": { "$gte": 0.8 } }
      }
    }
  },
  {
    "$project": {
      "_id": 1,
      "type": 1,
      "speed": "$velocity.speed",
      "sources": "$metadata.sources",
      "source_docs.name": 1,
      "source_docs.reliability": 1
    }
  },
  { "$limit": 20 }
]


