db.createCollection("metrics", {
  timeseries: {
    timeField: "ts",
    metaField: "meta",
    granularity: "seconds"
  }
})



# Système embarqué radar
{
  "ts": ISODate("2026-01-13T10:15:00Z"),
  "meta": {
    "site": "A1",
    "radar_id": "R-042",
    "metric_family": "radar_system"
  },
  "cpu_pct": 37.4,
  "ram_used_mb": 1820,
  "ram_total_mb": 4096,
  "disk_used_gb": 21.7,
  "disk_free_gb": 8.3
}


# réaseau
{
  "ts": ISODate("2026-01-13T10:15:00Z"),
  "meta": {
    "site": "A1",
    "radar_id": "R-042",
    "uplink": "lte",
    "metric_family": "radar_network"
  },
  "rtt_ms": 48,
  "packet_loss_pct": 0.9,
  "tx_bytes": 82349213,
  "rx_bytes": 231992131,
  "signal_rsrp_dbm": -97
}

# santé radar
{
  "ts": ISODate("2026-01-13T10:15:00Z"),
  "meta": {
    "site": "A1",
    "radar_id": "R-042",
    "vendor": "AcmeRadar",
    "model": "XR-500",
    "metric_family": "radar_health"
  },
  "temperature_c": 54.8,
  "supply_voltage_v": 23.9,
  "fan_rpm": 3120,
  "error_rate_pct": 0.2
}
