# Montrer la structure des documends, les types : 

- Objet radar structuré, hiérarchique, avec position xyz ainsi que de la data stockée sour format geo, menace, incertitude, qualité, tableaux et arrays... 

# Montrer vision sous forme de table

# Montrer schema analysis

# Requêtes simples

- tous les radars de type aicraft

{
  "type": "aircraft"
}

- project : juste leur type, id, et signal-Streght : 

{
  "_id": 1,
  "type": 1,
  "signal_strength": 1
}

- radars avec un signal fort

{
  "signal_strength": { "$gt": 0.8 }
}

{
  "_id": 1,
  "signal_strength": 1,
  "detection_quality.detection_score": 1
}


- chercher dans tableau

{
  "metadata.sources": "src_A01"
}

{
  "_id": 1,
  "metadata.sources": 1,
  "metadata.last_update": 1
}

- et je peux bien sûr mélanger tous ces filtres


# Requêtes géo

- Filtre géospatial (dans un rayon de 50 km autour de Paris)

{
  "position.geo": {
    "$near": {
      "$geometry": {
        "type": "Point",
        "coordinates": [2.3522, 48.8566]
      },
      "$maxDistance": 50000
    }
  }
}

- objets dans un polygone

{
  "position.geo": {
    "$geoWithin": {
      "$polygon": [
        [1.9, 48.6],
        [2.9, 48.6],
        [2.9, 49.1],
        [1.9, 49.1],
        [1.9, 48.6]
      ]
    }
  }
}

- objet en dehors d'un rayon

{
  "position.geo": {
    "$not": {
      "$geoWithin": {
        "$centerSphere": [
          [2.3522, 48.8566],
          0.00314
        ]
      }
    }
  }
}


- objets géo + menacae elevée

{
  "position.geo": {
    "$near": {
      "$geometry": {
        "type": "Point",
        "coordinates": [2.3522, 48.8566]
      },
      "$maxDistance": 50000
    }
  },
  "threat_assessment.level": { "$gte": 3 }
}

# Facilité d'update, changement de schema 

faire filtre aircraft
{
  "type": "aircraft"
}

puis update : 
{
  "$set": { "metadata.operator": "ops_team_1" }
}

je peux avoir des docs complètement différents au sein de la même collection, les faire coexister, les indexer différemment, les faire évoluer à tout moment, sans downtime, sans valeur null etc... 