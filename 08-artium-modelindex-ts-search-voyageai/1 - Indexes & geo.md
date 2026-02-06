# Show data with compass, in table and doc format
# Show schema analysis, show geo data
# Run simple queries and showcase the indexing rules

## single field
{name: "DEVICE-0000"}
-> show explain
-> create index on name
-> show explain again
-> projection

## ESR rule - good order

Filter : 
{
  manufacturer: "acme",
  created_at: { $gte: ISODate("2025-01-01T00:00:00Z"), $lt: ISODate("2026-03-01T00:00:00Z") }
}

sort: 
{ updated_at: -1 }

Index : { manufacturer: 1, updated_at: -1, created_at: -1 }

## ESR rule - bad order

db.devices.createIndex({ created_at: -1, manufacturer: 1, updatedAt: -1 })

run same query

## Show geo queries

- “What devices are within 5 km of a point”
{
  geo: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [-76.21770646980633, 58.1401548976479] 
      },
      $maxDistance: 5000 // meters
    }
  }
}

- combine with filter

{
  manufacturer: "cotep",
  geo: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [-76.21770646980633, 58.1401548976479] 
      },
      $maxDistance: 10000
    }
  }
}

- devices within a polygon
{
  geo: {
    $geoWithin: {
      $geometry: {
        type: "Polygon",
        coordinates: [
          [
            [
              -122.60830267443292,
              56.73239054966211
            ],
            [
              -165.7512686150816,
              -44.735605020297584
            ],
            [
              -29.4957207460302,
              -53.74762306540304
            ],
            [
              -122.60830267443292,
              56.73239054966211
            ]
          ]
        ]
      }
    }
  }
}