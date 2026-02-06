# Positions d’un engin sur une période
{
  "OriginePosition": "Z20507",
  "UtcObservation": {
    "$gte": ISODate("2026-01-22T10:00:00Z"),
    "$lte": ISODate("2026-01-22T12:00:00Z")
  }
}

# Recherches multi-critères
{
  "Pays": "FR",
  "data_mr.serie.code_serie_racine": "Z20500",
  "Aberrant": false,
  "VitesseInstantanee": { "$gt": 5 },
  "UtcObservation": {
    "$gte": ISODate("2026-01-22T00:00:00Z"),
    "$lte": ISODate("2026-01-22T23:59:59Z")
  }
}

# Points aberrants pour maintenance
{
  "Aberrant": true,
  "UtcObservation": {
    "$gte": ISODate("2026-01-22T00:00:00Z"),
    "$lte": ISODate("2026-01-23T00:00:00Z")
  }
}

# Agreg - Vitesse moyenne par engin 
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
      _id: "$OriginePosition",
      vitesse_moyenne: { $avg: "$VitesseInstantanee" },
      vitesse_max: { $max: "$VitesseInstantanee" },
      nb_points: { $sum: 1 }
    }
  },
  {
    $sort: { vitesse_moyenne: -1 }
  }
]


# Série temporelle vitesse (exploitable par chart Javascript)
[
  {
    $match: {
      OriginePosition: "Z20507",
      UtcObservation: {
        $gte: ISODate("2026-01-22T11:00:00Z"),
        $lte: ISODate("2026-01-22T12:00:00Z")
      }
    }
  },
  {
    $project: {
      _id: 0,
      t: "$UtcObservation",
      v: "$VitesseInstantanee"
    }
  },
  {
    $sort: { t: 1 }
  }
]


# taux d'anomalies par engin
[
  {
    $match: {
      UtcObservation: {
        $gte: ISODate("2026-01-01T00:00:00Z"),
        $lte: ISODate("2026-01-31T23:59:59Z")
      }
    }
  },
  {
    $group: {
      _id: "$OriginePosition",
      total: { $sum: 1 },
      aberrants: {
        $sum: {
          $cond: ["$Aberrant", 1, 0]
        }
      }
    }
  },
  {
    $project: {
      taux_aberration: {
        $divide: ["$aberrants", "$total"]
      }
    }
  }
]

# préparer la donnée pour affichage carte
[
  {
    $match: {
      OriginePosition: "Z20507",
      location: { $ne: null },
      UtcObservation: {
        $gte: ISODate("2026-01-22T11:00:00Z"),
        $lte: ISODate("2026-01-22T12:00:00Z")
      }
    }
  },
  {
    $project: {
      _id: 0,
      location: 1,
      vitesse: "$VitesseInstantanee",
      t: "$UtcObservation"
    }
  }
]
