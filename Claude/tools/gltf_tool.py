#!/usr/bin/env python3
"""
gltf_tool.py - Create and edit GLB 3D models from JSON scene descriptions

Usage:
  python3 gltf_tool.py create scene.json output.glb
  python3 gltf_tool.py edit   model.glb  changes.json [output.glb]
  python3 gltf_tool.py info   model.glb

Scene JSON format:
{
  "objects": [
    {
      "name": "unique_id",
      "type": "box|sphere|cylinder|cone|plane",
      "position": [x, y, z],
      "rotation": [rx, ry, rz],
      "scale": [sx, sy, sz],
      "color": [r, g, b],
      "opacity": 1.0
    }
  ]
}

Changes JSON format (for edit command):
{
  "add":    [ ...objects... ],
  "remove": [ "name1", "name2" ],
  "modify": [ ...objects with updated properties... ]
}
"""

import sys
import json
import re
import math
import numpy as np
import trimesh
from trimesh import transformations


def euler_to_matrix(rx_deg, ry_deg, rz_deg):
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)
    Rx = transformations.rotation_matrix(rx, [1, 0, 0])
    Ry = transformations.rotation_matrix(ry, [0, 1, 0])
    Rz = transformations.rotation_matrix(rz, [0, 0, 1])
    return Rz @ Ry @ Rx


def build_mesh(obj):
    t = obj.get("type", "box").lower()
    scale = obj.get("scale", [1, 1, 1])
    sx, sy = scale[0], scale[1]
    sz = scale[2] if len(scale) > 2 else scale[1]

    if t == "box":
        mesh = trimesh.creation.box(extents=[sx, sy, sz])
    elif t == "sphere":
        mesh = trimesh.creation.icosphere(radius=sx / 2, subdivisions=3)
    elif t == "cylinder":
        mesh = trimesh.creation.cylinder(radius=sx / 2, height=sz, sections=32)
    elif t == "cone":
        mesh = trimesh.creation.cone(radius=sx / 2, height=sz, sections=32)
    elif t == "plane":
        mesh = trimesh.creation.box(extents=[sx, sy, max(sz * 0.02, 0.005)])
    else:
        print(f"  Warning: unknown type '{t}', using box")
        mesh = trimesh.creation.box(extents=[sx, sy, sz])

    color = obj.get("color", [0.5, 0.5, 0.5])
    opacity = obj.get("opacity", 1.0)
    rgba = [int(c * 255) for c in color] + [int(opacity * 255)]
    mesh.visual.face_colors = rgba

    pos = obj.get("position", [0, 0, 0])
    rot = obj.get("rotation", [0, 0, 0])
    T = np.eye(4)
    T[:3, 3] = pos
    transform = T @ euler_to_matrix(*rot)
    mesh.apply_transform(transform)

    return mesh


def scene_from_data(data):
    scene = trimesh.Scene()
    for obj in data.get("objects", []):
        name = obj.get("name")
        if not name:
            print("  Warning: object without name, skipping")
            continue
        mesh = build_mesh(obj)
        scene.add_geometry(mesh, node_name=name)
    return scene


def load_json(path):
    """Load JSON with support for // line comments."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"//[^\n]*", "", text)
    return json.loads(text)


def cmd_create(scene_path, output_path):
    data = load_json(scene_path)
    scene = scene_from_data(data)
    glb = scene.export(file_type="glb")
    with open(output_path, "wb") as f:
        f.write(glb)
    print(f"Created: {output_path}  ({len(scene.geometry)} objects)")


def cmd_info(model_path):
    scene = trimesh.load(model_path)
    if isinstance(scene, trimesh.Scene):
        print(f"File:    {model_path}")
        print(f"Objects: {len(scene.geometry)}")
        for name, geom in scene.geometry.items():
            size = (geom.bounds[1] - geom.bounds[0]).round(3)
            center = geom.centroid.round(3)
            print(f"  {name}: size={list(size)}  center={list(center)}")
    else:
        print(f"File: {model_path}")
        size = (scene.bounds[1] - scene.bounds[0]).round(3)
        print(f"Size: {list(size)}")


def cmd_edit(model_path, changes_path, output_path=None):
    if output_path is None:
        output_path = model_path

    scene = trimesh.load(model_path)
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene([scene])

    changes = load_json(changes_path)

    for name in changes.get("remove", []):
        if name in scene.geometry:
            scene.delete_geometry(name)
            print(f"Removed: {name}")
        else:
            print(f"  Warning: '{name}' not found")

    for obj in changes.get("modify", []):
        name = obj.get("name")
        if name in scene.geometry:
            scene.delete_geometry(name)
            scene.add_geometry(build_mesh(obj), node_name=name)
            print(f"Modified: {name}")
        else:
            print(f"  Warning: '{name}' not found for modify")

    for obj in changes.get("add", []):
        name = obj.get("name")
        scene.add_geometry(build_mesh(obj), node_name=name)
        print(f"Added: {name}")

    glb = scene.export(file_type="glb")
    with open(output_path, "wb") as f:
        f.write(glb)
    print(f"Saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: python3 gltf_tool.py create scene.json output.glb")
            sys.exit(1)
        cmd_create(sys.argv[2], sys.argv[3])

    elif cmd == "info":
        if len(sys.argv) < 3:
            print("Usage: python3 gltf_tool.py info model.glb")
            sys.exit(1)
        cmd_info(sys.argv[2])

    elif cmd == "edit":
        if len(sys.argv) < 4:
            print("Usage: python3 gltf_tool.py edit model.glb changes.json [output.glb]")
            sys.exit(1)
        output = sys.argv[4] if len(sys.argv) > 4 else None
        cmd_edit(sys.argv[2], sys.argv[3], output)

    else:
        print(f"Unknown command: {cmd}\nCommands: create, edit, info")
        sys.exit(1)


if __name__ == "__main__":
    main()
