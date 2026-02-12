#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
query_radar_mongo.py

Objectif
--------
Exécuter indépendamment des requêtes sur la collection `plots` (et parfois `scans`)
pour des cas spatio-temporels radar.

Chaque requête est une sous-commande CLI, ex :
  - q_az       : temps + fenêtre azimutale (wrap 0/360)
  - q_geo_alt  : temps + distance géodésique (nearSphere) + altitude
  - q_eu2d     : temps + distance euclidienne 2D (cartesian x/y)
  - q_eu3d     : temps + distance euclidienne 3D (cartesian x/y/z)
  - q_delta    : temps + (delta az < N° AND delta range < M km AND delta alt < P m) dans repère radar

Sortie
------
Chaque commande imprime un JSON documenté :
  - paramètres
  - nb candidats (préfiltre) / nb résultats
  - durée
  - exemples de hits (max 5) avec champs utiles

Dépendances
-----------
  pip install pymongo

Exemples
--------
  python query_radar_mongo.py --mongo mongodb://localhost:27017 --db radar q_az \
      --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z --a0 350 --a1 10

  python query_radar_mongo.py --mongo mongodb://localhost:27017 --db radar q_geo_alt \
      --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z --lat 48.8566 --lon 2.3522 --radius_m 20000 --alt0 0 --alt1 12000

  python query_radar_mongo.py --mongo mongodb://localhost:27017 --db radar q_eu2d \
      --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z --cx 0 --cy 0 --radius_m 5000

  python query_radar_mongo.py --mongo mongodb://localhost:27017 --db radar q_eu3d \
      --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z --cx 0 --cy 0 --cz 0 --radius_m 5000

  python query_radar_mongo.py --mongo mongodb://localhost:27017 --db radar q_delta \
      --t0 2022-08-23T00:00:00Z --t1 2022-08-25T00:00:00Z \
      --az_center 5 --daz_deg 2 --range_center_km 60 --drange_km 5 --alt_center_m 3000 --dalt_m 500
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import time
from typing import Any, Dict, List, Optional

from pymongo import MongoClient

# ----------------------------
# Utils
# ----------------------------

def parse_iso8601(s: str) -> dt.datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc)

def ensure_utc(d: dt.datetime) -> dt.datetime:
    if d.tzinfo is None:
        return d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)

def normalize_deg_0_360(deg: float) -> float:
    x = deg % 360.0
    return x + 360.0 if x < 0 else x

def time_filter(t0: dt.datetime, t1: dt.datetime) -> Dict[str, Any]:
    return {"time_validity": {"$gte": ensure_utc(t0), "$lte": ensure_utc(t1)}}

def az_window_query(field: str, a0_deg: float, a1_deg: float) -> Dict[str, Any]:
    """
    Fenêtre azimutale [a0,a1] en degrés, wrap 360->0 géré.
    """
    a0 = normalize_deg_0_360(a0_deg)
    a1 = normalize_deg_0_360(a1_deg)
    if a0 <= a1:
        return {field: {"$gte": a0, "$lte": a1}}
    return {"$or": [{field: {"$gte": a0, "$lte": 360.0}}, {field: {"$gte": 0.0, "$lte": a1}}]}

def pretty_result(action: str, params: Dict[str, Any], t_start: float, n_candidates: int, hits: List[Dict[str, Any]]) -> None:
    elapsed = time.time() - t_start
    print(json.dumps({
        "action": action,
        "params": params,
        "candidates_examined": n_candidates,
        "hits_returned": len(hits),
        "elapsed_sec": round(elapsed, 4),
        "sample_hits": hits[: min(5, len(hits))],
        "output_notes": [
            "sample_hits est tronqué à 5 éléments.",
            "Les champs Date sont sérialisés en string via default=str."
        ]
    }, indent=2, default=str))


# ----------------------------
# Requêtes
# ----------------------------

def cmd_q_az(plots, args) -> None:
    """
    temps + fenêtre azimutale (wrap)
    """
    t0 = parse_iso8601(args.t0)
    t1 = parse_iso8601(args.t1)
    q = {"$and": [time_filter(t0, t1), az_window_query("az_deg_0_360", args.a0, args.a1)]}
    if args.sensor_id is not None:
        q["$and"].append({"sensor_id": args.sensor_id})

    start = time.time()
    hits = list(plots.find(
        q,
        projection={"_id": 0, "time_validity": 1, "scan_id": 1, "task_scan_number": 1, "plot_number": 1, "az_deg_0_360": 1, "range_m": 1, "alt_m": 1},
        limit=args.limit
    ))
    n = plots.count_documents(q)
    pretty_result("q_az", {
        "time_utc": [args.t0, args.t1],
        "az_window_deg": [args.a0, args.a1],
        "sensor_id": args.sensor_id,
        "limit": args.limit,
        "wrap_logic": "si a0>a1 => [a0..360] U [0..a1]"
    }, start, n, hits)

def cmd_q_geo_alt(plots, args) -> None:
    """
    temps + géodésique + altitude
    Utilise index 2dsphere sur plot_geo.
    """
    t0 = parse_iso8601(args.t0)
    t1 = parse_iso8601(args.t1)

    # Remarque : $nearSphere doit être au niveau du champ geo
    q: Dict[str, Any] = {
        **time_filter(t0, t1),
        "plot_geo": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [args.lon, args.lat]},
                "$maxDistance": args.radius_m
            }
        },
        "alt_m": {"$gte": args.alt0, "$lte": args.alt1}
    }
    if args.sensor_id is not None:
        q["sensor_id"] = args.sensor_id

    start = time.time()
    hits = list(plots.find(
        q,
        projection={"_id": 0, "time_validity": 1, "plot_geo": 1, "alt_m": 1, "range_m": 1, "az_deg_0_360": 1},
        limit=args.limit
    ))

    # Compte "candidats" : préfiltre hors geo (car compter avec $nearSphere est moins interprétable)
    pre = {k: v for k, v in q.items() if k != "plot_geo"}
    n = plots.count_documents(pre)

    pretty_result("q_geo_alt", {
        "time_utc": [args.t0, args.t1],
        "center_lonlat": [args.lon, args.lat],
        "radius_m": args.radius_m,
        "alt_m_window": [args.alt0, args.alt1],
        "sensor_id": args.sensor_id,
        "limit": args.limit,
        "note": "candidates_examined = count du préfiltre (sans nearSphere)."
    }, start, n, hits)

def cmd_q_eu2d(plots, args) -> None:
    """
    temps + distance euclidienne 2D dans cartesian.x/y

    Pattern MongoDB classique :
      1) préfiltre indexable par bounding box (carré)
      2) post-filtre exact (cercle) côté client
    """
    t0 = parse_iso8601(args.t0)
    t1 = parse_iso8601(args.t1)

    q: Dict[str, Any] = {
        **time_filter(t0, t1),
        "cartesian.x": {"$gte": args.cx - args.radius_m, "$lte": args.cx + args.radius_m},
        "cartesian.y": {"$gte": args.cy - args.radius_m, "$lte": args.cy + args.radius_m},
    }
    if args.sensor_id is not None:
        q["sensor_id"] = args.sensor_id

    start = time.time()
    # On prend plus que limit pour compenser le post-filtre cercle
    candidates = list(plots.find(
        q,
        projection={"_id": 0, "time_validity": 1, "plot_number": 1, "cartesian": 1, "range_m": 1, "az_deg_0_360": 1},
        limit=args.limit * 30
    ))

    r2 = args.radius_m * args.radius_m
    hits: List[Dict[str, Any]] = []
    for d in candidates:
        dx = float(d["cartesian"]["x"]) - args.cx
        dy = float(d["cartesian"]["y"]) - args.cy
        if dx*dx + dy*dy <= r2:
            d["distance_m"] = math.sqrt(dx*dx + dy*dy)
            hits.append(d)
            if len(hits) >= args.limit:
                break

    pretty_result("q_eu2d", {
        "time_utc": [args.t0, args.t1],
        "center_xy_m": [args.cx, args.cy],
        "radius_m": args.radius_m,
        "sensor_id": args.sensor_id,
        "limit": args.limit,
        "note": "candidates_examined = nb docs après bounding box; post-filtre exact 2D côté client."
    }, start, len(candidates), hits)

def cmd_q_eu3d(plots, args) -> None:
    """
    temps + distance euclidienne 3D dans cartesian.x/y/z

    Même pattern :
      1) bounding box 3D
      2) post-filtre exact (sphère) côté client
    """
    t0 = parse_iso8601(args.t0)
    t1 = parse_iso8601(args.t1)

    q: Dict[str, Any] = {
        **time_filter(t0, t1),
        "cartesian.x": {"$gte": args.cx - args.radius_m, "$lte": args.cx + args.radius_m},
        "cartesian.y": {"$gte": args.cy - args.radius_m, "$lte": args.cy + args.radius_m},
        "cartesian.z": {"$gte": args.cz - args.radius_m, "$lte": args.cz + args.radius_m},
    }
    if args.sensor_id is not None:
        q["sensor_id"] = args.sensor_id

    start = time.time()
    candidates = list(plots.find(
        q,
        projection={"_id": 0, "time_validity": 1, "plot_number": 1, "cartesian": 1, "range_m": 1, "az_deg_0_360": 1},
        limit=args.limit * 50
    ))

    r2 = args.radius_m * args.radius_m
    hits: List[Dict[str, Any]] = []
    for d in candidates:
        dx = float(d["cartesian"]["x"]) - args.cx
        dy = float(d["cartesian"]["y"]) - args.cy
        dz = float(d["cartesian"]["z"]) - args.cz
        if dx*dx + dy*dy + dz*dz <= r2:
            d["distance_m"] = math.sqrt(dx*dx + dy*dy + dz*dz)
            hits.append(d)
            if len(hits) >= args.limit:
                break

    pretty_result("q_eu3d", {
        "time_utc": [args.t0, args.t1],
        "center_xyz_m": [args.cx, args.cy, args.cz],
        "radius_m": args.radius_m,
        "sensor_id": args.sensor_id,
        "limit": args.limit,
        "note": "candidates_examined = nb docs après bounding box; post-filtre exact 3D côté client."
    }, start, len(candidates), hits)

def cmd_q_delta(plots, args) -> None:
    """
    temps + delta azimuth < N degrés AND delta range < M km AND delta altitude < P m
    dans l'espace radar (az_deg_0_360, range_m, alt_m).

    Wrap 360->0 géré autour de az_center.
    """
    t0 = parse_iso8601(args.t0)
    t1 = parse_iso8601(args.t1)

    az_center = normalize_deg_0_360(args.az_center)
    az_q = az_window_query("az_deg_0_360", az_center - args.daz_deg, az_center + args.daz_deg)

    r_center_m = args.range_center_km * 1000.0
    dr_m = args.drange_km * 1000.0
    r_q = {"range_m": {"$gte": r_center_m - dr_m, "$lte": r_center_m + dr_m}}

    alt_q = {"alt_m": {"$gte": args.alt_center_m - args.dalt_m, "$lte": args.alt_center_m + args.dalt_m}}

    q = {"$and": [time_filter(t0, t1), az_q, r_q, alt_q]}
    if args.sensor_id is not None:
        q["$and"].append({"sensor_id": args.sensor_id})
    if args.task_scan_number is not None:
        q["$and"].append({"task_scan_number": args.task_scan_number})

    start = time.time()
    hits = list(plots.find(
        q,
        projection={"_id": 0, "time_validity": 1, "task_scan_number": 1, "plot_number": 1, "az_deg_0_360": 1, "range_m": 1, "alt_m": 1},
        limit=args.limit
    ))
    n = plots.count_documents(q)

    pretty_result("q_delta", {
        "time_utc": [args.t0, args.t1],
        "az_center_deg": args.az_center,
        "delta_az_deg": args.daz_deg,
        "range_center_km": args.range_center_km,
        "delta_range_km": args.drange_km,
        "alt_center_m": args.alt_center_m,
        "delta_alt_m": args.dalt_m,
        "sensor_id": args.sensor_id,
        "task_scan_number": args.task_scan_number,
        "limit": args.limit,
        "wrap_logic": "fenêtre az gère le passage 360->0"
    }, start, n, hits)


# ----------------------------
# CLI
# ----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Requêtes radar spatio-temporelles (MongoDB).")
    p.add_argument("--mongo", required=True, help="Mongo URI, ex: mongodb://localhost:27017")
    p.add_argument("--db", required=True, help="DB name, ex: radar")

    sub = p.add_subparsers(dest="cmd", required=True)

    # q_az
    qa = sub.add_parser("q_az", help="temps + fenêtre azimutale (wrap 0/360).")
    qa.add_argument("--t0", required=True, help="ISO8601 UTC, ex 2022-08-23T00:00:00Z")
    qa.add_argument("--t1", required=True, help="ISO8601 UTC")
    qa.add_argument("--a0", type=float, required=True, help="Azimut début (deg)")
    qa.add_argument("--a1", type=float, required=True, help="Azimut fin (deg)")
    qa.add_argument("--sensor_id", type=int, default=None)
    qa.add_argument("--limit", type=int, default=50)
    qa.set_defaults(func=cmd_q_az)

    # q_geo_alt
    qg = sub.add_parser("q_geo_alt", help="temps + géodésique nearSphere + altitude.")
    qg.add_argument("--t0", required=True)
    qg.add_argument("--t1", required=True)
    qg.add_argument("--lat", type=float, required=True, help="Latitude deg")
    qg.add_argument("--lon", type=float, required=True, help="Longitude deg")
    qg.add_argument("--radius_m", type=float, required=True, help="Rayon en mètres")
    qg.add_argument("--alt0", type=float, required=True, help="Altitude min (m)")
    qg.add_argument("--alt1", type=float, required=True, help="Altitude max (m)")
    qg.add_argument("--sensor_id", type=int, default=None)
    qg.add_argument("--limit", type=int, default=50)
    qg.set_defaults(func=cmd_q_geo_alt)

    # q_eu2d
    q2 = sub.add_parser("q_eu2d", help="temps + distance euclidienne 2D (cartesian x/y).")
    q2.add_argument("--t0", required=True)
    q2.add_argument("--t1", required=True)
    q2.add_argument("--cx", type=float, required=True, help="Centre X (m)")
    q2.add_argument("--cy", type=float, required=True, help="Centre Y (m)")
    q2.add_argument("--radius_m", type=float, required=True, help="Rayon (m)")
    q2.add_argument("--sensor_id", type=int, default=None)
    q2.add_argument("--limit", type=int, default=50)
    q2.set_defaults(func=cmd_q_eu2d)

    # q_eu3d
    q3 = sub.add_parser("q_eu3d", help="temps + distance euclidienne 3D (cartesian x/y/z).")
    q3.add_argument("--t0", required=True)
    q3.add_argument("--t1", required=True)
    q3.add_argument("--cx", type=float, required=True, help="Centre X (m)")
    q3.add_argument("--cy", type=float, required=True, help="Centre Y (m)")
    q3.add_argument("--cz", type=float, required=True, help="Centre Z (m)")
    q3.add_argument("--radius_m", type=float, required=True, help="Rayon (m)")
    q3.add_argument("--sensor_id", type=int, default=None)
    q3.add_argument("--limit", type=int, default=50)
    q3.set_defaults(func=cmd_q_eu3d)

    # q_delta
    qd = sub.add_parser("q_delta", help="temps + delta az/range/alt (repère radar).")
    qd.add_argument("--t0", required=True)
    qd.add_argument("--t1", required=True)
    qd.add_argument("--az_center", type=float, required=True, help="Az centre (deg)")
    qd.add_argument("--daz_deg", type=float, required=True, help="Delta az (deg)")
    qd.add_argument("--range_center_km", type=float, required=True, help="Range centre (km)")
    qd.add_argument("--drange_km", type=float, required=True, help="Delta range (km)")
    qd.add_argument("--alt_center_m", type=float, required=True, help="Alt centre (m)")
    qd.add_argument("--dalt_m", type=float, required=True, help="Delta alt (m)")
    qd.add_argument("--sensor_id", type=int, default=None)
    qd.add_argument("--task_scan_number", type=int, default=None)
    qd.add_argument("--limit", type=int, default=50)
    qd.set_defaults(func=cmd_q_delta)

    return p

def main() -> None:
    args = build_parser().parse_args()
    client = MongoClient(args.mongo)
    db = client[args.db]
    plots = db["plots"]
    args.func(plots, args)

if __name__ == "__main__":
    main()
