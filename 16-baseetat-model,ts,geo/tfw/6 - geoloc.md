db.collection.createIndex({ "geolocations.location": "2dsphere" })

In compass : 
- fiond documents within 500m :

{
  "geolocations.location": {
    $near: {
      $geometry: { type: "Point", coordinates: [2.226, 48.95] },
      $maxDistance: 500 
    }
  }
}

---

docs within a polygon. 
{
  "geolocations.location": {
    $geoWithin: {
      $geometry: {
        type: "Polygon",
        coordinates: [[
          [2.224, 48.949],
          [2.227, 48.949],
          [2.227, 48.951],
          [2.224, 48.951],
          [2.224, 48.949]
        ]]
      }
    }
  }
}
----

# find events near a location : Aggregation

find trains within 2 kilometers from [2.226, 48.95] which have a Door_Open events.measure 

on voit calcul distance.

----

find the latest geolocation point for rame 351L 

-------
# ça marche aussi avec les timeseries
# Analyses de points chauds : aggregation pipeline on timeseries collection

Run “count how many Brake_Applied I have for each rame in a given location, and sort by the highest count” 
