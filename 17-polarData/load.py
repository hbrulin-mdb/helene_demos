#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ingest_radar_mongo.py

Objectif
--------
Ingestion de documents "scan" (avec plots imbriqués) dans 2 collections MongoDB :
  - scans : 1 document par scan (métadonnées + position plateforme)
  - plots : 1 document par plot (données dérivées + indexables + plot_geo)


Sorties
-------
- Insertion batch en 2 étapes :
    a) insert_many scans → récupération des _id
    b) insert_many plots avec scan_id = _id du scan
- Création d’index recommandés (time, 2dsphere, az/range/alt, cartesian)

Hypothèses importantes
----------------------
- time_validity en microsecondes (epoch us) dans les données d'entrée.
- platform_latitude/platform_longitude semblent être en radians (comme ton exemple).
- plot_geo est calculé par approximation locale :
      lat2 = lat + north / R
      lon2 = lon + east / (R*cos(lat))
  avec R=6378137 m
  => OK pour des fenêtres locales (quelques dizaines de km). Pour du précis WGS84,
     faire ENU/ECEF avec GeographicLib/pyproj côté ingestion.

Dépendances
-----------
  pip install pymongo

Exemples
--------

  # Drop + génération synthétique
  python ingest_radar_mongo.py --mongo mongodb://localhost:27017 --db radar --drop --generate --n_scans 200 --plots_per_scan 50
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import random
import time
from typing import Any, Dict, Iterable, List, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

WGS84_R = 6378137.0  # m (approx sphérique)


# ----------------------------
# Temps / conversions
# ----------------------------

def epoch_us_to_datetime(epoch_us: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(epoch_us / 1_000_000, tz=dt.timezone.utc)

def rad_to_deg(rad: float) -> float:
    return rad * 180.0 / math.pi

def normalize_deg_0_360(deg: float) -> float:
    x = deg % 360.0
    return x + 360.0 if x < 0 else x


# ----------------------------
# Parsing / lecture NDJSON
# ----------------------------

def iter_ndjson(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"NDJSON invalide ligne {line_no}: {e}") from e


# ----------------------------
# plot_geo approx (ENU->LL)
# ----------------------------

def platform_ll_from_scan(scan: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Retourne (lat_deg, lon_deg, alt_m) de la plateforme.
    Si les champs sont en radians (typique), conversion -> degrés.
    """
    plat_lat = float(scan.get("platform_latitude", 0.0))
    plat_lon = float(scan.get("platform_longitude", 0.0))

    # Heuristique : rad si valeurs proches des bornes rad
    if abs(plat_lat) <= (math.pi / 2 + 0.2) and abs(plat_lon) <= (math.pi + 0.2):
        lat_deg = rad_to_deg(plat_lat)
        lon_deg = rad_to_deg(plat_lon)
    else:
        lat_deg = plat_lat
        lon_deg = plat_lon

    alt_m = float(scan.get("platform_alt_m", 0.0) or 0.0)
    return lat_deg, lon_deg, alt_m

def approx_plot_geo(lat_deg: float, lon_deg: float, east_m: float, north_m: float) -> Tuple[float, float]:
    """
    Approximation locale autour de (lat, lon):
      dLat = north/R
      dLon = east/(R*cos(lat))
    """
    lat_rad = math.radians(lat_deg)
    dlat = north_m / WGS84_R
    denom = WGS84_R * max(1e-9, math.cos(lat_rad))
    dlon = east_m / denom
    lat2 = lat_rad + dlat
    lon2 = math.radians(lon_deg) + dlon
    return math.degrees(lat2), math.degrees(lon2)


# ----------------------------
# Transformation scan -> docs
# ----------------------------

def build_docs_from_scan(scan: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Transforme 1 scan d'entrée en:
      - scan_doc pour collection `scans`
      - plot_docs[] pour collection `plots` (sans scan_id, ajouté après insert scan)
    """
    scan_tv_raw = scan.get("time_validity")
    scan_tv = epoch_us_to_datetime(int(scan_tv_raw)) if scan_tv_raw is not None else dt.datetime.now(dt.timezone.utc)

    lat_deg, lon_deg, plat_alt_m = platform_ll_from_scan(scan)

    scan_doc: Dict[str, Any] = {
        "time_validity": scan_tv,
        "sensor_id": int(scan.get("sensor_id", 0)),
        "task_scan_number": int(scan.get("task_scan_number", 0)),
        "sequence_number": int(scan.get("sequence_number", 0)),
        "face_id": int(scan.get("face_id", 0)),
        "sector_number": int(scan.get("sector_number", 0)),
        "sector_azimuth_rad": float(scan.get("sector_azimuth", 0.0)),
        "platform_heading_rad": float(scan.get("platform_heading", 0.0)),
        "platform_roll_rad": float(scan.get("platform_roll", 0.0)),
        "platform_pitch_rad": float(scan.get("platform_pitch", 0.0)),
        "platform_geo": {"type": "Point", "coordinates": [lon_deg, lat_deg]},
        "platform_alt_m": plat_alt_m,
    }

    plots_in = scan.get("plot", []) or []
    plot_docs: List[Dict[str, Any]] = []

    for p in plots_in:
        ptv_raw = p.get("time_validity")
        ptv = epoch_us_to_datetime(int(ptv_raw)) if ptv_raw is not None else scan_tv

        polar = p.get("polar_position", {}) or {}
        cart = p.get("cartesian_position", {}) or {}

        r_m = float(polar.get("range", 0.0))
        az_rad = float(polar.get("azimuth", 0.0))
        el_rad = float(polar.get("elevation", 0.0))
        az_deg = normalize_deg_0_360(rad_to_deg(az_rad))

        x = float(cart.get("x", 0.0))
        y = float(cart.get("y", 0.0))
        z = float(cart.get("z", 0.0))

        # Hypothèse (documentée) : z=Up (m) => altitude approx = alt plateforme + z
        alt_m = plat_alt_m + z

        # Hypothèse (documentée) : x=East, y=North
        lat2_deg, lon2_deg = approx_plot_geo(lat_deg, lon_deg, east_m=x, north_m=y)

        plot_docs.append({
            "time_validity": ptv,
            "sensor_id": scan_doc["sensor_id"],
            "task_scan_number": scan_doc["task_scan_number"],
            "plot_number": int(p.get("plot_number", -1)),
            "polar": {"range_m": r_m, "az_rad": az_rad, "el_rad": el_rad},
            "az_deg_0_360": az_deg,
            "range_m": r_m,
            "alt_m": alt_m,
            "cartesian": {"x": x, "y": y, "z": z},
            "plot_geo": {"type": "Point", "coordinates": [lon2_deg, lat2_deg]},
        })

    return scan_doc, plot_docs


# ----------------------------
# Données synthétiques
# ----------------------------

def generate_synthetic_scans(n_scans: int, plots_per_scan: int) -> Iterable[Dict[str, Any]]:
    base_time = dt.datetime(2022, 8, 23, tzinfo=dt.timezone.utc)
    # Autour de Paris mais en radians pour imiter l'exemple
    base_lat = math.radians(48.8566)
    base_lon = math.radians(2.3522)

    for i in range(n_scans):
        tv = int((base_time + dt.timedelta(seconds=i * 2)).timestamp() * 1_000_000)
        plat_lat = base_lat + random.uniform(-1e-5, 1e-5)
        plat_lon = base_lon + random.uniform(-1e-5, 1e-5)

        scan = {
            "message_ident": 1,
            "sequence_number": 900 + i,
            "time_validity": tv,
            "sensor_id": 1,
            "sector_number": random.randint(1, 32),
            "face_id": 1,
            "task_nr": 14748,
            "task_scan_number": 55000 + i,
            "sector_azimuth": random.uniform(0, 2 * math.pi),
            "platform_heading": random.uniform(-math.pi, math.pi),
            "platform_roll": random.uniform(-0.05, 0.05),
            "platform_pitch": random.uniform(-0.05, 0.05),
            "platform_latitude": plat_lat,
            "platform_longitude": plat_lon,
            "number_of_plots": plots_per_scan,
            "plot": [],
        }

        for p in range(plots_per_scan):
            ptv = tv + random.randint(-200_000, 200_000)
            r = random.uniform(5_000, 120_000)
            az = random.uniform(0, 2 * math.pi)
            el = random.uniform(-0.01, 0.2)

            # cart local cohérent avec l'hypothèse x=East,y=North,z=Up
            east = r * math.cos(el) * math.sin(az)
            north = r * math.cos(el) * math.cos(az)
            up = r * math.sin(el)

            scan["plot"].append({
                "time_validity": ptv,
                "task_scan_number": scan["task_scan_number"],
                "plot_number": p,
                "cartesian_position": {"x": east, "y": north, "z": up},
                "polar_position": {"range": r, "azimuth": az, "elevation": el},
            })

        yield scan


# ----------------------------
# Mongo / index / insert
# ----------------------------

def create_indexes(scans: Collection, plots: Collection) -> None:
    # scans
    scans.create_index([("sensor_id", 1), ("time_validity", 1)])
    scans.create_index([("task_scan_number", 1)])
    scans.create_index([("platform_geo", "2dsphere")])

    # plots
    plots.create_index([("sensor_id", 1), ("time_validity", 1)])
    plots.create_index([("task_scan_number", 1), ("time_validity", 1)])
    plots.create_index([("scan_id", 1)])
    plots.create_index([("sensor_id", 1), ("time_validity", 1), ("az_deg_0_360", 1), ("range_m", 1), ("alt_m", 1)])
    plots.create_index([("plot_geo", "2dsphere")])
    plots.create_index([("sensor_id", 1), ("time_validity", 1), ("cartesian.x", 1), ("cartesian.y", 1)])
    plots.create_index([("sensor_id", 1), ("time_validity", 1), ("cartesian.x", 1), ("cartesian.y", 1), ("cartesian.z", 1)])


def flush_batches(scans_col: Collection, plots_col: Collection,
                  scan_batch: List[Dict[str, Any]],
                  plots_wrapped: List[List[Dict[str, Any]]]) -> Tuple[int, int]:
    """
    Insert scans, then insert plots with scan_id.
    """
    try:
        res = scans_col.insert_many(scan_batch, ordered=False)
    except BulkWriteError as e:
        raise RuntimeError(f"BulkWriteError scans: {e.details}") from e

    scan_ids = res.inserted_ids
    plots_to_insert: List[Dict[str, Any]] = []

    for sid, plot_list in zip(scan_ids, plots_wrapped):
        for pd in plot_list:
            pd["scan_id"] = sid
            plots_to_insert.append(pd)

    if plots_to_insert:
        try:
            plots_col.insert_many(plots_to_insert, ordered=False)
        except BulkWriteError as e:
            raise RuntimeError(f"BulkWriteError plots: {e.details}") from e

    return len(scan_ids), len(plots_to_insert)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingestion radar -> MongoDB (scans + plots).")
    ap.add_argument("--mongo", required=True, help="Mongo URI, ex: mongodb://localhost:27017")
    ap.add_argument("--db", required=True, help="DB name, ex: radar")
    ap.add_argument("--input", help="Fichier NDJSON (un scan JSON par ligne)")
    ap.add_argument("--generate", action="store_true", help="Générer des données synthétiques")
    ap.add_argument("--n_scans", type=int, default=100, help="Nb scans synthétiques")
    ap.add_argument("--plots_per_scan", type=int, default=20, help="Nb plots/scan synthétiques")
    ap.add_argument("--batch", type=int, default=200, help="Batch size scans")
    ap.add_argument("--drop", action="store_true", help="Drop collections avant ingestion")
    args = ap.parse_args()

    client = MongoClient(args.mongo)
    db = client[args.db]
    scans_col = db["scans"]
    plots_col = db["plots"]

    if args.drop:
        scans_col.drop()
        plots_col.drop()

    create_indexes(scans_col, plots_col)

    if args.generate:
        scan_iter = generate_synthetic_scans(args.n_scans, args.plots_per_scan)
    else:
        if not args.input:
            raise SystemExit("ERREUR: fournir --input (NDJSON) ou utiliser --generate.")
        scan_iter = iter_ndjson(args.input)

    t_start = time.time()
    total_scans = 0
    total_plots = 0

    scan_batch: List[Dict[str, Any]] = []
    plots_wrapped: List[List[Dict[str, Any]]] = []

    for scan in scan_iter:
        scan_doc, plot_docs = build_docs_from_scan(scan)
        scan_batch.append(scan_doc)
        plots_wrapped.append(plot_docs)

        if len(scan_batch) >= args.batch:
            n_s, n_p = flush_batches(scans_col, plots_col, scan_batch, plots_wrapped)
            total_scans += n_s
            total_plots += n_p
            scan_batch.clear()
            plots_wrapped.clear()

    if scan_batch:
        n_s, n_p = flush_batches(scans_col, plots_col, scan_batch, plots_wrapped)
        total_scans += n_s
        total_plots += n_p

    elapsed = time.time() - t_start
    print(json.dumps({
        "action": "ingest",
        "db": args.db,
        "inserted_scans": total_scans,
        "inserted_plots": total_plots,
        "elapsed_sec": round(elapsed, 3),
        "assumptions": [
            "plot_geo: approx locale (x=East, y=North) autour de la plateforme",
            "alt_m = platform_alt_m + cartesian.z (hypothèse z=Up)",
            "platform_lat/long: conversion rad->deg si valeurs compatibles radians",
        ],
        "indexes": [
            "plots.plot_geo 2dsphere",
            "plots (sensor_id, time_validity)",
            "plots (sensor_id, time_validity, az_deg_0_360, range_m, alt_m)",
            "plots (sensor_id, time_validity, cartesian.x, cartesian.y[, cartesian.z])",
        ]
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
