- show the different families of TS

-  Latest docs for one radar (any family)

{ "meta.radar_id": "R-012" }
sort : { "ts": -1 }

- Hourly trend: average CPU by site (system family)

[
  { $match: { "meta.metric_family": "radar_system" } },
  {
    $group: {
      _id: {
        site: "$meta.site",
        hour: { $dateTrunc: { date: "$ts", unit: "hour" } }
      },
      avg_cpu: { $avg: "$cpu_pct" },
      avg_ram_used: { $avg: "$ram_used_mb" },
      samples: { $sum: 1 }
    }
  },
  { $sort: { "_id.hour": 1, "_id.site": 1 } }
]

- Window function : finding big jumps in temperature per radar

[
  { $match: { "meta.metric_family": "radar_health" } },
  { $sort: { "meta.radar_id": 1, ts: 1 } },
  {
    $setWindowFields: {
      partitionBy: "$meta.radar_id",
      sortBy: { ts: 1 },
      output: {
        prev_temp: { $shift: { output: "$temperature_c", by: -1 } },
        prev_ts: { $shift: { output: "$ts", by: -1 } }
      }
    }
  },
  {
    $set: {
      temp_delta: { $subtract: ["$temperature_c", "$prev_temp"] },
      seconds_since_prev: { $dateDiff: { startDate: "$prev_ts", endDate: "$ts", unit: "second" } }
    }
  },
  { $match: { temp_delta: { $gte: 8 } } },
  {
    $project: {
      _id: 0,
      ts: 1,
      radar_id: "$meta.radar_id",
      site: "$meta.site",
      temperature_c: 1,
      prev_temp: 1,
      temp_delta: 1,
      seconds_since_prev: 1
    }
  },
  { $sort: { temp_delta: -1 } },
  { $limit: 50 }
]

- “Worst offenders” composite score (network + health + system) : make this based on range of a day

[
  {
    $match: {
      ts: {
  			$gte: ISODate("2026-01-13T00:00:00Z"),
  			$lt:  ISODate("2026-01-14T00:00:00Z")
				},
      "meta.metric_family": { $in: ["radar_system", "radar_network", "radar_health"] }
    }
  },
  {
    $group: {
      _id: "$meta.radar_id",

      avg_cpu: {
        $avg: {
          $cond: [
            { $eq: ["$meta.metric_family", "radar_system"] },
            "$cpu_pct",
            "$$REMOVE"
          ]
        }
      },

      avg_loss: {
        $avg: {
          $cond: [
            { $eq: ["$meta.metric_family", "radar_network"] },
            "$packet_loss_pct",
            "$$REMOVE"
          ]
        }
      },

      avg_temp: {
        $avg: {
          $cond: [
            { $eq: ["$meta.metric_family", "radar_health"] },
            "$temperature_c",
            "$$REMOVE"
          ]
        }
      },

      samples: { $sum: 1 },
      first_ts: { $min: "$ts" },
      last_ts: { $max: "$ts" }
    }
  },
  {
    $set: {
      // Toy scoring model: tune weights to your SLOs
      score: {
        $add: [
          { $multiply: [{ $ifNull: ["$avg_cpu", 0] }, 0.4] },
          { $multiply: [{ $ifNull: ["$avg_loss", 0] }, 8.0] },
          { $multiply: [{ $ifNull: ["$avg_temp", 0] }, 0.5] }
        ]
      }
    }
  },
  {
    $project: {
      _id: 0,
      radar_id: "$_id",
      score: 1,
      avg_cpu: 1,
      avg_loss: 1,
      avg_temp: 1,
      samples: 1,
      first_ts: 1,
      last_ts: 1
    }
  },
  { $sort: { score: -1, samples: -1 } },
  { $limit: 20 }
]
