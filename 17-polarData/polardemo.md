# Accompanying slides

[Link](https://docs.google.com/presentation/d/1tyyB9HzyiFby4aSb7pviat-P0LPsgEDc6RZ9g_lUTmA/edit?slide=id.g3bf7d8d5f77_0_10096#slide=id.g3bf7d8d5f77_0_10096)

# ingest
```sh
python3 load.py --mongo "mongodb://<admin>:>pwd>@localhost:27017/?authSource=admin&directConnection=true" --db radar --drop --generate --n_scans 200 --plots_per_scan 50
```

# query temps + fenêtre azimutale

```sh
python3 queries.py --mongo "mongodb://<admin>:<pwd>@localhost:27017/?authSource=admin&directConnection=true" --db radar q_az --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z --a0 350 --a1 10
```

## Cas A — pas de wrap (A ≤ B), ex: 30° → 80°

```js
{
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  az_deg_0_360: { $gte: 30, $lte: 80 }
}
```

## Cas B — wrap (A > B), ex: 350° → 10°
```js
{
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  $or: [
    { az_deg_0_360: { $gte: 350, $lte: 360 } },
    { az_deg_0_360: { $gte: 0, $lte: 10 } }
  ]
}
```

# Temps + geodésique + altitude
```js
{
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  plot_geo: {
    $nearSphere: {
      $geometry: { type: "Point", coordinates: [2.3522, 48.8566] },
      $maxDistance: 20000
    }
  },
  alt_m: { $gte: 0, $lte: 12000 }
}
```

# Temps + distance euclidienne 2D (cartesian.x/y)

## Bounding box
```js
{
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  "cartesian.x": { $gte: -5000, $lte: 5000 },
  "cartesian.y": { $gte: -5000, $lte: 5000 }
}
```
## Cercle 
```js
[
  {
    $match: {
      time_validity: {
        $gte: ISODate("2022-08-23T00:00:00Z"),
        $lte: ISODate("2022-08-25T00:00:00Z")
      },
      "cartesian.x": { $gte: -5000, $lte: 5000 },
      "cartesian.y": { $gte: -5000, $lte: 5000 }
    }
  },
  {
    $addFields: {
      distance2_m2: {
        $add: [
          { $pow: [{ $subtract: ["$cartesian.x", 0] }, 2] },
          { $pow: [{ $subtract: ["$cartesian.y", 0] }, 2] }
        ]
      }
    }
  },
  { $match: { distance2_m2: { $lte: 25000000 } } },
  {
    $addFields: {
      distance_m: { $sqrt: "$distance2_m2" }
    }
  },
  { $sort: { distance_m: 1 } },
  { $limit: 50 },
  {
    $project: {
      _id: 0,
      time_validity: 1,
      plot_number: 1,
      cartesian: 1,
      range_m: 1,
      az_deg_0_360: 1,
      alt_m: 1,
      distance_m: 1
    }
  }
]
```
# Temps + distance euclidienne 3D (cartesian.x/y/z)

## Bounding box

```js
{
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  "cartesian.x": { $gte: -5000, $lte: 5000 },
  "cartesian.y": { $gte: -5000, $lte: 5000 },
  "cartesian.z": { $gte: -5000, $lte: 5000 }
}
## Exact circle

[
  {
    $match: {
      time_validity: {
        $gte: ISODate("2022-08-23T00:00:00Z"),
        $lte: ISODate("2022-08-25T00:00:00Z")
      },
      "cartesian.x": { $gte: -5000, $lte: 5000 },
      "cartesian.y": { $gte: -5000, $lte: 5000 },
      "cartesian.z": { $gte: -5000, $lte: 5000 }
    }
  },
  {
    $addFields: {
      distance2_m2: {
        $add: [
          { $pow: [{ $subtract: ["$cartesian.x", 0] }, 2] },
          { $pow: [{ $subtract: ["$cartesian.y", 0] }, 2] },
          { $pow: [{ $subtract: ["$cartesian.z", 0] }, 2] }
        ]
      }
    }
  },
  { $match: { distance2_m2: { $lte: 25000000 } } },
  { $addFields: { distance_m: { $sqrt: "$distance2_m2" } } },
  { $sort: { distance_m: 1 } },
  { $limit: 50 },
  {
    $project: {
      _id: 0,
      time_validity: 1,
      plot_number: 1,
      cartesian: 1,
      range_m: 1,
      az_deg_0_360: 1,
      alt_m: 1,
      distance_m: 1
    }
  }
]
```

# Temps + “delta azimuth < N° AND delta range < M km AND delta altitude < P m” - filtre dans repère radar

```js
{
  task_scan_number: 55091,
  time_validity: {
    $gte: ISODate("2022-08-23T00:00:00Z"),
    $lte: ISODate("2022-08-25T00:00:00Z")
  },
  $or: [
    { az_deg_0_360: { $gte: 356, $lte: 360 } },
    { az_deg_0_360: { $gte: 0, $lte: 6 } }
  ],
  range_m: { $gte: 55000, $lte: 65000 },
  alt_m: { $gte: 2500, $lte: 3500 }
}
```

Range_m (radar → objet)  : C’est directement la valeur polar_position.range mais stockée comme champ simple indexable 


on utilise alt_m, qui est l'altitude absolue -> il faudrait mieux alt_rel.