db.createCollection("train_ts", {
  timeseries: {
    timeField: "date_etat",
    metaField: "metadata",
    granularity: "seconds"
  }
});




db.train_status_ts.insertMany([
  {
    metadata: { equipement: "mcg", rame: "351L", source: "tssp_oca" },
    date_etat: ISODate("2025-05-16T00:00:00.000Z"),
    events: [
      { mesure: "Door_Open", valeur: "true", date_etat: ISODate("2025-05-16T10:15:30.000Z") },
      { mesure: "Brake_Applied", valeur: "0.8", date_etat: ISODate("2025-05-16T10:15:32.000Z") }
    ],
    geolocations: [
      { timestamp: ISODate("2025-05-16T10:10:05.000Z"), location: { type: "Point", coordinates: [ 2.2259058, 48.9499931 ] }},
      { timestamp: ISODate("2025-05-16T10:10:15.000Z"), location: { type: "Point", coordinates: [ 2.2261011, 48.9499855 ] }}
    ]
  },
  {
    metadata: { equipement: "mcg", rame: "351L", source: "tssp_oca" },
    date_etat: ISODate("2025-05-17T00:00:00.000Z"),
    events: [
      { mesure: "Door_Open", valeur: "false", date_etat: ISODate("2025-05-17T09:05:10.000Z") }
    ],
    geolocations: [
      { timestamp: ISODate("2025-05-17T09:00:00.000Z"), location: { type: "Point", coordinates: [ 2.2359058, 48.9599931 ] }}
    ]
  }
]);