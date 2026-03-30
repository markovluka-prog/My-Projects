"""
Lego Technic style cross assembly (top view, isolated render)
- Central open gap
- 4 curved black connector arms (N/E/S/W)
- 4 separate turquoise connector blocks (one per arm)
- Small white hinge pieces after each turquoise block
- End pieces: black slim plates (top/bottom), cream wide tray-like pieces (left/right)
- White and dark-blue pin details near hinges
"""
import bpy
import math
import os

# Clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)


def mat(name, rgb, rough=0.35, metal=0.0, spec=0.55, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = emit
    return m


M_BLACK = mat("Black", (0.08, 0.08, 0.09), rough=0.35, spec=0.60, emit=0.0)
M_TURQ = mat("Turquoise", (0.00, 0.90, 0.75), rough=0.22, spec=0.70, emit=0.55)
M_WHITE = mat("White", (0.76, 0.76, 0.74), rough=0.34, spec=0.46, emit=0.0)
M_CREAM = mat("Cream", (0.90, 0.78, 0.55), rough=0.32, spec=0.48, emit=0.28)
M_BLUE = mat("BluePin", (0.05, 0.20, 0.82), rough=0.26, spec=0.62, emit=0.32)


def asgn(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def box(name, loc, sx, sy, sz, m):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    asgn(o, m)
    return o


def cyl(name, loc, r, h, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r, depth=h, location=loc, rotation=rot, vertices=verts
    )
    o = bpy.context.active_object
    o.name = name
    asgn(o, m)
    return o


def curved_arm(name, p0, p1, p2, radius, m):
    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.fill_mode = 'FULL'
    cd.bevel_depth = radius
    cd.bevel_resolution = 8
    sp = cd.splines.new('BEZIER')
    sp.bezier_points.add(2)

    bp = sp.bezier_points[0]
    bp.co = p0
    bp.handle_left_type = 'VECTOR'
    bp.handle_right_type = 'VECTOR'

    bp = sp.bezier_points[1]
    bp.co = p1
    bp.handle_left_type = 'ALIGNED'
    bp.handle_right_type = 'ALIGNED'

    bp = sp.bezier_points[2]
    bp.co = p2
    bp.handle_left_type = 'VECTOR'
    bp.handle_right_type = 'VECTOR'

    obj = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(obj)
    cd.materials.append(m)
    return obj


# Scale (meters)
U = 0.008
BH = U * 0.78
BW = U * 2.0

CENTER_GAP = U * 1.05
BLOCK_OFFSET = U * 3.0
ARM_Z = BH * 0.32
ARM_R = U * 0.24
ARM_BEND = U * 0.78

HINGE_T = U * 0.62
HINGE_Z = BH * 0.44

# End piece sizes (half extents)
TB_END_X = BW * 0.48
TB_END_Y = U * 2.45
TB_END_Z = BH * 0.30

LR_END_X = U * 2.35
LR_END_Y = BW * 0.70
LR_END_Z = BH * 0.30

# Turquoise blocks positions (separate, not merged)
DIRS = {
    'N': (0.0, 1.0),
    'E': (1.0, 0.0),
    'S': (0.0, -1.0),
    'W': (-1.0, 0.0),
}

block_centers = {
    k: (dx * BLOCK_OFFSET, dy * BLOCK_OFFSET, 0.0)
    for k, (dx, dy) in DIRS.items()
}

# 1) Curved black arms from central gap to each turquoise block
for k, (dx, dy) in DIRS.items():
    start = (dx * CENTER_GAP * 0.5, dy * CENTER_GAP * 0.5, ARM_Z)
    end = (dx * (BLOCK_OFFSET - BW * 0.50), dy * (BLOCK_OFFSET - BW * 0.50), ARM_Z)

    # Clockwise pinwheel bend: perpendicular offset
    px, py = dy, -dx
    mid = (
        dx * (BLOCK_OFFSET * 0.56) + px * ARM_BEND,
        dy * (BLOCK_OFFSET * 0.56) + py * ARM_BEND,
        ARM_Z,
    )
    curved_arm(f"Arm_{k}", start, mid, end, ARM_R, M_BLACK)

# 2) Four turquoise connector blocks + visible hole pattern
HOLE_R = U * 0.17
HOLE_Z = BH * 0.55
hole_pattern = [
    (-0.34, -0.34), (0.34, -0.34),
    (-0.34, 0.34), (0.34, 0.34),
    (0.0, 0.0), (0.0, 0.72),
]

for k, (cx, cy, cz) in block_centers.items():
    box(f"Turq_{k}", (cx, cy, cz), BW * 0.50, BW * 0.50, BH * 0.50, M_TURQ)
    for i, (px, py) in enumerate(hole_pattern):
        hx = cx + px * BW * 0.5
        hy = cy + py * BW * 0.5
        cyl(f"Hole_{k}_{i}", (hx, hy, HOLE_Z), HOLE_R, U * 0.30, M_BLUE)

# 3) Hinges + end plates + pin accents
for k, (dx, dy) in DIRS.items():
    cx, cy, _ = block_centers[k]

    # Hinge center (between turquoise block and end piece)
    hx = cx + dx * (BW * 0.50 + HINGE_T * 0.5)
    hy = cy + dy * (BW * 0.50 + HINGE_T * 0.5)

    if k in ('N', 'S'):
        box(f"Hinge_{k}", (hx, hy, 0), BW * 0.48, HINGE_T * 0.50, HINGE_Z * 0.50, M_WHITE)

        ex = hx + dx * (HINGE_T * 0.5 + TB_END_X)
        ey = hy + dy * (HINGE_T * 0.5 + TB_END_Y)
        box(f"End_{k}", (ex, ey, 0), TB_END_X, TB_END_Y, TB_END_Z, M_BLACK)

        # small cap at far end
        cap_y = ey + dy * (TB_END_Y + U * 0.16)
        box(f"EndCap_{k}", (ex, cap_y, 0), TB_END_X * 0.18, U * 0.18, TB_END_Z * 0.92, M_BLACK)

    else:
        box(f"Hinge_{k}", (hx, hy, 0), HINGE_T * 0.50, BW * 0.48, HINGE_Z * 0.50, M_WHITE)

        ex = hx + dx * (HINGE_T * 0.5 + LR_END_X)
        ey = hy + dy * (HINGE_T * 0.5 + LR_END_Y)

        # cream base tray
        box(f"End_{k}", (ex, ey, 0), LR_END_X, LR_END_Y, LR_END_Z, M_CREAM)

        # shallow recessed look via side rails
        rail_th = U * 0.14
        box(f"RailTop_{k}", (ex, ey + LR_END_Y - rail_th, LR_END_Z * 0.2), LR_END_X * 0.94, rail_th, LR_END_Z * 0.55, M_CREAM)
        box(f"RailBot_{k}", (ex, ey - LR_END_Y + rail_th, LR_END_Z * 0.2), LR_END_X * 0.94, rail_th, LR_END_Z * 0.55, M_CREAM)

        # side cutout hints near outer edge
        notch_x = ex + dx * (LR_END_X * 0.78)
        box(f"NotchTop_{k}", (notch_x, ey + LR_END_Y * 0.56, 0), U * 0.20, U * 0.20, LR_END_Z * 0.60, M_WHITE)
        box(f"NotchBot_{k}", (notch_x, ey - LR_END_Y * 0.56, 0), U * 0.20, U * 0.20, LR_END_Z * 0.60, M_WHITE)

    # pin accents near hinge (white + dark blue)
    pin_base = (
        cx + dx * (BW * 0.46),
        cy + dy * (BW * 0.46),
        BH * 0.56,
    )

    if k in ('N', 'S'):
        p1 = (pin_base[0] - U * 0.26, pin_base[1], pin_base[2])
        p2 = (pin_base[0] + U * 0.26, pin_base[1], pin_base[2])
    else:
        p1 = (pin_base[0], pin_base[1] - U * 0.26, pin_base[2])
        p2 = (pin_base[0], pin_base[1] + U * 0.26, pin_base[2])

    cyl(f"PinW_{k}", p1, U * 0.11, U * 0.24, M_WHITE)
    cyl(f"PinB_{k}", p2, U * 0.11, U * 0.24, M_BLUE)

# 4) Camera (strictly top view, auto-fit)
def model_bounds_xy():
    xs = []
    ys = []
    for o in bpy.context.scene.objects:
        if o.type in {"MESH", "CURVE"}:
            # For curve objects dimensions are valid after depsgraph eval
            cx, cy, _ = o.location
            sx = max(o.dimensions.x * 0.5, U * 0.08)
            sy = max(o.dimensions.y * 0.5, U * 0.08)
            xs.extend([cx - sx, cx + sx])
            ys.extend([cy - sy, cy + sy])
    if not xs:
        return (-0.05, 0.05, -0.05, 0.05)
    return (min(xs), max(xs), min(ys), max(ys))


x0, x1, y0, y1 = model_bounds_xy()
cx = (x0 + x1) * 0.5
cy = (y0 + y1) * 0.5
span_x = x1 - x0
span_y = y1 - y0
span = max(span_x, span_y)
margin = 1.18

bpy.ops.object.camera_add(location=(cx, cy, 1.0), rotation=(0, 0, 0))
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = span * margin
cam.data.clip_start = 0.001
bpy.context.scene.camera = cam

# 5) Light
bpy.ops.object.light_add(type='AREA', location=(0.0, 0.0, 0.8))
key = bpy.context.active_object
key.data.energy = 26.0
key.data.size = 0.30

bpy.ops.object.light_add(type='SUN', location=(0.25, -0.2, 0.9))
fill = bpy.context.active_object
fill.data.energy = 0.55
fill.rotation_euler = (math.radians(28), 0, math.radians(-22))

bpy.ops.object.light_add(type='AREA', location=(-0.25, 0.22, 0.65))
rim = bpy.context.active_object
rim.data.energy = 9.0
rim.data.size = 0.20

# 6) Transparent world for isolation
scene = bpy.context.scene
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.35, 0.35, 0.37, 1)
bg.inputs["Strength"].default_value = 0.25
scene.render.film_transparent = False

# 7) Render
out = os.path.dirname(os.path.abspath(__file__))
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = os.path.join(out, "zvezda_luki_render.png")
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -0.85
scene.view_settings.gamma = 1.0

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "zvezda_luki.blend"))
bpy.ops.render.render(write_still=True)
print(f"✓ {len(scene.objects)} objects -> {scene.render.filepath}")
