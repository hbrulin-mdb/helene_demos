# show the docs

We have restructured slightly so equipement, rame, and source live in a metadata field (best practice for time-series collections).
We have our events with a location Point object - we'll see geoloc later, and events values and they are uatomatically bucketed by mongodb, no need to do it yourself. 

# find 

{ "metadata.equipement": "mcg", "metadata.rame": "351L" }

# find with date : 
{
  date_etat: { $gte: ISODate("2025-05-16T00:00:00Z"), $lt: ISODate("2025-05-17T00:00:00Z") }
}



# Count events per day for each rame

# get first and last GPS coordinated per day per rame

# what is the avg Brake_Applied valeur per day



# Window function

A moving average is a way of smoothing values over time.
Instead of looking at just the current event, we also look at some previous events and compute an average.

Imagine we want to see how the brak
e pressure evolves over time for one train. We’ll use:
- $unwind on events

- $match only Brake_Applied events

- $setWindowFields to compute a 3-event moving average - “3-event” means we look at the current event plus the 2 previous ones. At each point in time, the average is taken over 3 consecutive data points.


db.train_ts.aggregate([
  // 1. Keep only Brake_Applied events
  { $match: { event_type: "Brake_Applied" } },

  // 2. Sort by time (important for windows!)
  { $sort: { date_etat: 1 } },

  // 3. Apply window functions
  {
    $setWindowFields: {
      partitionBy: "$metadata.rame",   // one rolling calc per train (rame)
      sortBy: { date_etat: 1 },
      output: {
        prevBrake: {
          $shift: {
            output: "$event_value",
            by: -1,              // look 1 event back
            default: null
          }
        },
        movingAvgBrake: {
          $avg: "$event_value",
          window: { documents: [ -2, 0 ] } // 3-event rolling average
        }
      }
    }
  },

  // 4. Clean up output
  {
    $project: {
      _id: 0,
      rame: "$metadata.rame",
      eventTime: "$date_etat",
      brakeValue: "$event_value",
      prevBrake: 1,
      movingAvgBrake: 1
    }
  }
]);
