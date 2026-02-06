# “Afficher toutes les positions dans cette zone de la carte”

{
  location: {
    $geoWithin: {
      $geometry: {
        type: "Polygon",
        coordinates: [[
          [2.50, 48.65],
          [2.60, 48.65],
          [2.60, 48.72],
          [2.50, 48.72],
          [2.50, 48.65]
        ]]
      }
    }
  },
  UtcObservation: {
    $gte: ISODate("2026-01-22T10:00:00Z"),
    $lte: ISODate("2026-01-22T12:00:00Z")
  }
}

# “Quelles rames sont passées à moins de 500 m de ce point ?”
{
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [2.5474, 48.6681]
      },
      $maxDistance: 500
    }
  },
  UtcObservation: {
    $gte: ISODate("2026-01-22T11:00:00Z"),
    $lte: ISODate("2026-01-22T11:30:00Z")
  }
}

# “Montre-moi les 50 points les plus proches”`
{
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [2.5474, 48.6681]
      },
      $maxDistance: 1000
    }
  }
}

# Heatmap – densité de passages
[
  {
    $match: {
      UtcObservation: {
        $gte: ISODate("2026-01-22T00:00:00Z"),
        $lte: ISODate("2026-01-22T23:59:59Z")
      }
    }
  },
  {
    $group: {
      _id: {
        lon: { $round: [{ $arrayElemAt: ["$location.coordinates", 0] }, 3] },
        lat: { $round: [{ $arrayElemAt: ["$location.coordinates", 1] }, 3] }
      },
      count: { $sum: 1 }
    }
  }
]

# points aberrants dans une zone
{
  Aberrant: true,
  location: {
    $geoWithin: {
      $geometry: {
        type: "Polygon",
        coordinates: [[
          [2.52, 48.66],
          [2.58, 48.66],
          [2.58, 48.70],
          [2.52, 48.70],
          [2.52, 48.66]
        ]]
      }
    }
  }
}
