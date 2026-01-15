#!/usr/bin/env python3
"""
Fetch OpenStreetMap building footprints via Overpass API and export as STL.
"""

from __future__ import annotations

import argparse
import math
from typing import Dict, Iterable, List, Tuple

import requests
import trimesh


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DEFAULT_HEIGHT_M = 10.0
LEVEL_HEIGHT_M = 3.0


def meters_per_degree_lon(lat: float) -> float:
    return 111_320.0 * math.cos(math.radians(lat))


def project_lonlat(lon: float, lat: float, lat0: float, lon0: float) -> Tuple[float, float]:
    x = (lon - lon0) * meters_per_degree_lon(lat0)
    y = (lat - lat0) * 111_320.0
    return x, y


def overpass_query(south: float, west: float, north: float, east: float) -> str:
    return f"""
    [out:json][timeout:25];
    (
      way["building"]({south},{west},{north},{east});
      relation["building"]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """


def fetch_osm(south: float, west: float, north: float, east: float) -> dict:
    response = requests.get(
        OVERPASS_URL,
        params={"data": overpass_query(south, west, north, east)},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def polygon_area(coords: List[Tuple[float, float]]) -> float:
    area = 0.0
    for i in range(len(coords)):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % len(coords)]
        area += x1 * y2 - x2 * y1
    return area * 0.5


def is_point_in_triangle(p, a, b, c) -> bool:
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    b1 = sign(p, a, b) < 0.0
    b2 = sign(p, b, c) < 0.0
    b3 = sign(p, c, a) < 0.0
    return (b1 == b2) and (b2 == b3)


def triangulate_polygon(coords: List[Tuple[float, float]]) -> List[Tuple[int, int, int]]:
    if len(coords) < 3:
        return []
    # Remove duplicate last point if present
    if coords[0] == coords[-1]:
        coords = coords[:-1]
    if len(coords) < 3:
        return []

    # Ensure counter-clockwise
    if polygon_area(coords) < 0:
        coords = list(reversed(coords))

    indices = list(range(len(coords)))
    triangles = []

    def is_ear(i_prev, i_curr, i_next) -> bool:
        a = coords[i_prev]
        b = coords[i_curr]
        c = coords[i_next]
        if polygon_area([a, b, c]) <= 0:
            return False
        for idx in indices:
            if idx in (i_prev, i_curr, i_next):
                continue
            if is_point_in_triangle(coords[idx], a, b, c):
                return False
        return True

    guard = 0
    while len(indices) > 2 and guard < 10_000:
        guard += 1
        ear_found = False
        for i in range(len(indices)):
            i_prev = indices[i - 1]
            i_curr = indices[i]
            i_next = indices[(i + 1) % len(indices)]
            if is_ear(i_prev, i_curr, i_next):
                triangles.append((i_prev, i_curr, i_next))
                indices.pop(i)
                ear_found = True
                break
        if not ear_found:
            break
    return triangles


def build_mesh_from_polygon(
    coords: List[Tuple[float, float]],
    height_m: float,
    origin_lat: float,
    origin_lon: float,
) -> trimesh.Trimesh:
    coords_2d = [project_lonlat(lon, lat, origin_lat, origin_lon) for lon, lat in coords]
    triangles = triangulate_polygon(coords_2d)
    if not triangles:
        return trimesh.Trimesh()

    vertices = []
    for x, y in coords_2d:
        vertices.append([x, y, 0.0])
    for x, y in coords_2d:
        vertices.append([x, y, height_m])

    faces = []
    n = len(coords_2d)
    for a, b, c in triangles:
        faces.append([a, b, c])
        faces.append([a + n, c + n, b + n])

    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n])
        faces.append([i, j + n, i + n])

    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def parse_buildings(osm: dict) -> Iterable[Tuple[List[int], Dict[str, str]]]:
    ways = {}
    nodes = {}
    relations = []
    for element in osm.get("elements", []):
        if element["type"] == "node":
            nodes[element["id"]] = (element["lon"], element["lat"])
        elif element["type"] == "way":
            ways[element["id"]] = element
        elif element["type"] == "relation":
            relations.append(element)

    for way in ways.values():
        tags = way.get("tags", {})
        if "building" not in tags:
            continue
        yield way.get("nodes", []), tags

    for relation in relations:
        tags = relation.get("tags", {})
        if "building" not in tags:
            continue
        for member in relation.get("members", []):
            if member.get("role") != "outer":
                continue
            if member.get("type") != "way":
                continue
            way = ways.get(member.get("ref"))
            if way:
                yield way.get("nodes", []), tags

    return nodes


def get_height(tags: Dict[str, str]) -> float:
    if "height" in tags:
        try:
            return float(tags["height"])
        except ValueError:
            pass
    if "building:levels" in tags:
        try:
            return float(tags["building:levels"]) * LEVEL_HEIGHT_M
        except ValueError:
            pass
    return DEFAULT_HEIGHT_M


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OSM buildings and export STL.")
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    osm = fetch_osm(args.south, args.west, args.north, args.east)
    elements = osm.get("elements", [])
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}

    origin_lat = (args.south + args.north) / 2.0
    origin_lon = (args.west + args.east) / 2.0

    meshes = []
    for node_ids, tags in parse_buildings(osm):
        coords = []
        for node_id in node_ids:
            coord = nodes.get(node_id)
            if coord:
                coords.append(coord)
        if len(coords) < 3:
            continue
        height = get_height(tags)
        mesh = build_mesh_from_polygon(coords, height, origin_lat, origin_lon)
        if mesh.faces.size > 0:
            meshes.append(mesh)

    if not meshes:
        raise SystemExit("No building meshes generated in bounding box")

    combined = trimesh.util.concatenate(meshes)
    combined.export(args.out)
    print(f"Saved STL to {args.out}")


if __name__ == "__main__":
    main()

