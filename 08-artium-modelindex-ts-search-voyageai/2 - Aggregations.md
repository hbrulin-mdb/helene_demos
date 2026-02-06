# show the TS collection

# Availability of screen  over last 7 days

[
  // parameters inside the pipeline (easy to edit)
  {
    $set: {
      screenId: "BEC-QC-760",
      end: "$$NOW",
      start: { $dateSubtract: { startDate: "$$NOW", unit: "day", amount: 7 } }
    }
  },

  // keep only this device, and all events up to 'end'
  {
    $match: {
      $expr: {
        $and: [
          { $eq: ["$meta.screen_id", "$screenId"] },
          { $lt: ["$ts", "$end"] }
        ]
      }
    }
  },

  // compute next event time per device
  {
    $setWindowFields: {
      partitionBy: "$meta.screen_id",
      sortBy: { ts: 1 },
      output: {
        next_ts: { $shift: { output: "$ts", by: 1 } }
      }
    }
  },

  // clamp each segment to [start, end]
  {
    $addFields: {
      seg_start: { $cond: [{ $lt: ["$ts", "$start"] }, "$start", "$ts"] },
      seg_end: {
        $cond: [
          { $or: [{ $eq: ["$next_ts", null] }, { $gt: ["$next_ts", "$end"] }] },
          "$end",
          "$next_ts"
        ]
      }
    }
  },

  // keep only segments overlapping the window
  {
    $match: {
      $expr: { $gt: ["$seg_end", "$start"] }
    }
  },

  // compute durations
  {
    $addFields: {
      seg_ms: { $subtract: ["$seg_end", "$seg_start"] },
      up_ms: {
        $cond: ["$available", { $subtract: ["$seg_end", "$seg_start"] }, 0]
      }
    }
  },

  // aggregate availability
  {
    $group: {
      _id: "$meta.screen_id",
      up_ms: { $sum: "$up_ms" },
      total_ms: { $sum: "$seg_ms" }
    }
  },
  {
    $addFields: {
      availability: { $divide: ["$up_ms", "$total_ms"] },
      up_hours: { $divide: ["$up_ms", 1000 * 60 * 60] },
      total_hours: { $divide: ["$total_ms", 1000 * 60 * 60] }
    }
  }
]


--> Output : 

_id           "BEC-QC-760"
up_ms         604800000 - uptime
total_ms      604800000 - time window that was evaluated
availability  1 - 100% availability
up_hours      168 - conversion to hours
total_hours   168



# “Top 10 worst devices by availability”
[
  // Keep events up to the window end so we can cap the last segment at end
  { $match: { ts: { $lt: ISODate("2026-01-01T00:00:00Z") } } },

  // Per device, compute the next event time
  {
    $setWindowFields: {
      partitionBy: "$meta.screen_id",
      sortBy: { ts: 1 },
      output: { next_ts: { $shift: { output: "$ts", by: 1 } } }
    }
  },

  // Clamp each segment to Dec window
  {
    $addFields: {
      seg_start: {
        $cond: [
          { $lt: ["$ts", ISODate("2025-12-01T00:00:00Z")] },
          ISODate("2025-12-01T00:00:00Z"),
          "$ts"
        ]
      },
      seg_end: {
        $cond: [
          {
            $or: [
              { $eq: ["$next_ts", null] },
              { $gt: ["$next_ts", ISODate("2026-01-01T00:00:00Z")] }
            ]
          },
          ISODate("2026-01-01T00:00:00Z"),
          "$next_ts"
        ]
      }
    }
  },

  // Keep only segments overlapping the window
  { $match: { $expr: { $gt: ["$seg_end", "$seg_start"] } } },

  // Duration + uptime duration
  {
    $addFields: {
      seg_ms: { $subtract: ["$seg_end", "$seg_start"] },
      up_ms: { $cond: ["$available", { $subtract: ["$seg_end", "$seg_start"] }, 0] }
    }
  },

  // Aggregate per device
  {
    $group: {
      _id: "$meta.screen_id",
      up_ms: { $sum: "$up_ms" },
      total_ms: { $sum: "$seg_ms" }
    }
  },

  // Availability + nice hours
  {
    $addFields: {
      availability: { $divide: ["$up_ms", "$total_ms"] },
      down_ms: { $subtract: ["$total_ms", "$up_ms"] },
      down_hours: { $divide: [{ $subtract: ["$total_ms", "$up_ms"] }, 1000 * 60 * 60] }
    }
  },

  // Worst = lowest availability (tie-breaker: more downtime)
  { $sort: { availability: 1, down_ms: -1 } },
  { $limit: 10 }
]


# mean time to repair per screen id

[
  {
    $setWindowFields: {
      partitionBy: "$meta.screen_id",
      sortBy: { ts: 1 },
      output: {
        next_state: { $shift: { output: "$state", by: 1 } },
        next_ts: { $shift: { output: "$ts", by: 1 } }
      }
    }
  },
  {
    $match: {
      state: "offline",
      next_state: { $ne: "offline" },
      next_ts: { $ne: null }
    }
  },
  { $addFields: { repair_ms: { $subtract: ["$next_ts", "$ts"] } } },
  {
    $group: {
      _id: "$meta.screen_id",
      mttr_ms: { $avg: "$repair_ms" },
      repairs: { $sum: 1 }
    }
  },
  { $sort: { mttr_ms: -1 } }
]



# mean time between failure 

[
  {
    $setWindowFields: {
      partitionBy: "$meta.screen_id",
      sortBy: { ts: 1 },
      output: {
        prev_state: { $shift: { output: "$state", by: -1 } },
        prev_failure_ts: {
          $shift: {
            output: {
              $cond: [{ $eq: ["$state", "offline"] }, "$ts", null]
            },
            by: -1
          }
        }
      }
    }
  },
  {
    $match: {
      state: "offline",
      prev_state: { $ne: "offline" } // offline start
    }
  },
  {
    $setWindowFields: {
      partitionBy: "$meta.screen_id",
      sortBy: { ts: 1 },
      output: {
        prev_offline_start: { $shift: { output: "$ts", by: -1 } }
      }
    }
  },
  {
    $addFields: {
      interval_ms: { $subtract: ["$ts", "$prev_offline_start"] }
    }
  },
  { $match: { interval_ms: { $gt: 0 } } },
  {
    $group: {
      _id: "$meta.screen_id",
      mtbf_ms: { $avg: "$interval_ms" },
      failures: { $sum: 1 }
    }
  },
  { $sort: { mtbf_ms: 1 } }
]



