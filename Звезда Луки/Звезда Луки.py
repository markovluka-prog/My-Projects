import bpy, math
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

S      = 0.001
A      = 14 * S
H      = 6  * S
TUBE_R = A / 6
DIST   = 21 * S - TUBE_R

ARC_CX = DIST * 0.50 + 1*S
ARC_R  = DIST * 0.30

mat_teal = bpy.data.materials.new("Teal")
mat_teal.use_nodes = True
mat_teal.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.11, 0.62, 0.46, 1.0)

mat_black = bpy.data.materials.new("Black")
mat_black.use_nodes = True
mat_black.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)

mat_white = bpy.data.materials.new("White")
mat_white.use_nodes = True
mat_white.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.95, 0.95, 0.90, 1.0)

# 4 teal-блока
for i, pos in enumerate([(0,DIST,0),(0,-DIST,0),(-DIST,0,0),(DIST,0,0)]):
    bpy.ops.mesh.primitive_cube_add(location=pos)
    o = bpy.context.active_object
    o.name = f"TealBlock_{i}"
    o.scale = (A/2, A/2, H/2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat_teal)

def cyl(name, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    length = math.sqrt(dx**2 + dy**2)
    if length < 0.00001:
        return
    rot = Vector((dx, dy, 0)).normalized().to_track_quat('Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_cylinder_add(
        radius=TUBE_R, depth=length,
        location=((x1+x2)/2, (y1+y2)/2, 0),
        rotation=rot
    )
    bpy.context.active_object.name = name
    bpy.context.active_object.data.materials.append(mat_black)

def pipe(name, cx, cy, a_start, segments=10):
    pts = [
        (cx + ARC_R * math.cos(math.radians(a_start + 90*s/segments)),
         cy + ARC_R * math.sin(math.radians(a_start + 90*s/segments)))
        for s in range(segments+1)
    ]
    for s in range(segments):
        cyl(f"{name}_{s}", pts[s][0], pts[s][1], pts[s+1][0], pts[s+1][1])
    for ax, ay, sign in [(pts[0][0], pts[0][1], 1), (pts[-1][0], pts[-1][1], -1)]:
        suf = "s1" if sign == 1 else "s2"
        if abs(ax) > abs(ay):
            cyl(f"{name}_{suf}", ax, ay, math.copysign(DIST - A/2, ax), ay)
        else:
            cyl(f"{name}_{suf}", ax, ay, ax, math.copysign(DIST - A/2, ay))

pipe("TR",  ARC_CX,  ARC_CX, 180)
pipe("TL", -ARC_CX,  ARC_CX, 270)
pipe("BL", -ARC_CX, -ARC_CX,   0)
pipe("BR",  ARC_CX, -ARC_CX,  90)

# ВРАЩАЮЩИЕ УЗЛЫ (не моделируются, только описание):
# Каждая труба соединяется с teal-блоком через штырь (ось вращения).
# Блок (0, +DIST)  — штыри по оси X: трубы вращаются вокруг X
# Блок (0, -DIST)  — штыри по оси X: трубы вращаются вокруг X
# Блок (-DIST, 0)  — штыри по оси Y: трубы вращаются вокруг Y
# Блок (+DIST, 0)  — штыри по оси Y: трубы вращаются вокруг Y
# Каждый блок имеет 2 штыря (по одному с каждой стороны входа трубы).
# Итого: 8 вращающих узлов, степень свободы каждого = 1 ось (360°).

# Плечи — плоские пластины с плавным загибом вниз
ARM_L   = A * 2.2
ARM_W   = A
ARM_TH  = H * 0.8
BEND_R  = A * 0.4
BEND_SEG = 8

def add_arm(name, ox, oy, dx, dy, mat):
    import bmesh, mathutils

    BEND_ANGLE = math.radians(80)
    VERT_L     = ARM_L / 3 * 4/3
    SEGS       = 16   # сегментов дуги

    # half-sizes поперечного сечения пластины
    hw = ARM_W  / 2   # ширина (перпендикулярна плоскости загиба)
    hh = ARM_TH / 2   # толщина (в плоскости загиба)

    # Ось ширины (постоянна вдоль всей руки, всегда перпендикулярна плоскости загиба)
    if abs(dx) > abs(dy):
        w_ax = Vector((0, 1, 0))   # X-рука: ширина по Y
    else:
        w_ax = Vector((1, 0, 0))   # Y-рука: ширина по X

    # Строим список центральных точек + тангентов
    # 1) горизонтальный участок: от начала (ox,oy,0) до конца (ex,ey,0)
    ex = ox + dx * ARM_L
    ey = oy + dy * ARM_L

    spine = []

    # горизонталь
    t_horiz = Vector((dx, dy, 0)).normalized()
    spine.append((Vector((ox, oy, 0)), t_horiz, hw, hh))
    spine.append((Vector((ex, ey, 0)), t_horiz, hw, hh))

    # дуга 120°
    for s in range(SEGS + 1):
        a = BEND_ANGLE * s / SEGS
        horiz = BEND_R * math.sin(a)
        vert  = BEND_R * (1 - math.cos(a))
        pt    = Vector((ex + dx * horiz, ey + dy * horiz, -vert))
        tang  = Vector((dx * math.cos(a), dy * math.cos(a), -math.sin(a))).normalized()
        spine.append((pt, tang, hw, hh))

    # блок вниз от конца дуги — вдоль тангента конца дуги
    bend_end = spine[-1][0].copy()
    t_end    = spine[-1][1].copy()
    spine.append((bend_end + t_end * VERT_L, t_end, hw, hh))

    # Генерируем меш через bmesh (sweep профиля прямоугольника вдоль spine)
    bm = bmesh.new()

    def make_profile(pt, tang, width_ax, hw, hh):
        """Возвращает 4 вершины прямоугольного профиля."""
        t_ax = tang.normalized()
        w    = width_ax.normalized()
        # перевычисляем h_ax чтобы был точно перпендикулярен
        h_ax = t_ax.cross(w).normalized()
        w    = h_ax.cross(t_ax).normalized()
        corners = []
        for sw in (-1, 1):
            for sh in (-1, 1):
                corners.append(bm.verts.new(pt + w * (sw * hw) + h_ax * (sh * hh)))
        return corners  # порядок: (-w,-h),(-w,+h),(+w,-h),(+w,+h)

    profiles = []
    for (pt, tang, hw_, hh_) in spine:
        profiles.append(make_profile(pt, tang, w_ax, hw_, hh_))

    # соединяем профили квадами
    for i in range(len(profiles) - 1):
        a = profiles[i]
        b = profiles[i+1]
        # грани: bottom, top, left, right, + торцы
        bm.faces.new([a[0], a[2], b[2], b[0]])  # -h face
        bm.faces.new([a[1], b[1], b[3], a[3]])  # +h face
        bm.faces.new([a[0], b[0], b[1], a[1]])  # -w face
        bm.faces.new([a[2], a[3], b[3], b[2]])  # +w face

    # торцы
    bm.faces.new(profiles[0])
    bm.faces.new(list(reversed(profiles[-1])))

    bm.normal_update()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.materials.append(mat)

add_arm("ArmT",  0,        DIST + A/2,  0,  1, mat_white)
add_arm("ArmB",  0,       -DIST - A/2,  0, -1, mat_white)
add_arm("ArmL", -DIST - A/2, 0,        -1,  0, mat_black)
add_arm("ArmR",  DIST + A/2, 0,         1,  0, mat_black)

# Колёса — бобина: узко→дуга наружу→узко, с отверстием
WHEEL_R_WIDE   = A / 2 / 1.5
WHEEL_R_NARROW = WHEEL_R_WIDE * 0.6
WHEEL_HOLE     = WHEEL_R_NARROW * 1.75   # большое отверстие
WHEEL_H        = H * 1.5
PROF_SEGS      = 32

tile_positions = [(0, DIST), (0, -DIST), (-DIST, 0), (DIST, 0)]

for (tx, ty) in tile_positions:
    import bmesh as bm_mod
    bm2 = bm_mod.new()
    ring_segs = 32
    wz = H / 2 - H * 0.75  # опущено на 0.75*H

    # Профиль: узко(низ) → дуга наружу → узко(верх)
    # r(t) = NARROW + (WIDE-NARROW) * sin(pi*t)  где t от 0 до 1
    profile = []
    for i in range(PROF_SEGS + 1):
        t = i / PROF_SEGS
        r = WHEEL_R_NARROW + (WHEEL_R_WIDE - WHEEL_R_NARROW) * math.sin(math.pi * t)
        z = wz + WHEEL_H * t
        profile.append((r, z))

    outer_rings = []
    inner_rings = []
    for (r, z) in profile:
        outer = []
        inner = []
        for s in range(ring_segs):
            angle = 2 * math.pi * s / ring_segs
            ca, sa = math.cos(angle), math.sin(angle)
            outer.append(bm2.verts.new((tx + ca*r,          ty + sa*r,          z)))
            inner.append(bm2.verts.new((tx + ca*WHEEL_HOLE, ty + sa*WHEEL_HOLE, z)))
        outer_rings.append(outer)
        inner_rings.append(inner)

    for i in range(len(profile) - 1):
        for s in range(ring_segs):
            n = (s + 1) % ring_segs
            bm2.faces.new([outer_rings[i][s], outer_rings[i][n], outer_rings[i+1][n], outer_rings[i+1][s]])
            bm2.faces.new([inner_rings[i][s], inner_rings[i+1][s], inner_rings[i+1][n], inner_rings[i][n]])

    for s in range(ring_segs):
        n = (s + 1) % ring_segs
        bm2.faces.new([outer_rings[0][s],  inner_rings[0][s],  inner_rings[0][n],  outer_rings[0][n]])
        bm2.faces.new([outer_rings[-1][s], outer_rings[-1][n], inner_rings[-1][n], inner_rings[-1][s]])

    # плоское дно отверстия
    cap_z = H / 2 + WHEEL_H * 0.05
    cap_verts = []
    for s in range(ring_segs):
        angle = 2 * math.pi * s / ring_segs
        ca, sa = math.cos(angle), math.sin(angle)
        cap_verts.append(bm2.verts.new((tx + ca * WHEEL_HOLE, ty + sa * WHEEL_HOLE, cap_z)))
    center_bot = bm2.verts.new((tx, ty, cap_z))
    for s in range(ring_segs):
        n = (s + 1) % ring_segs
        bm2.faces.new([center_bot, cap_verts[s], cap_verts[n]])

    bm2.normal_update()
    wname = f"Wheel_{tx:.3f}_{ty:.3f}"
    wmesh = bpy.data.meshes.new(wname)
    bm2.to_mesh(wmesh)
    bm2.free()
    wobj = bpy.data.objects.new(wname, wmesh)
    bpy.context.collection.objects.link(wobj)
    wmesh.materials.append(mat_black)

print("Готово")

# ВРАЩАЮЩИЕ УЗЛЫ (не моделируются, только описание):
# Каждая труба соединяется с teal-блоком через штырь (ось вращения Z).
# Блок (0, +DIST)  — штыри на X=±A/2: трубы TR и TL вращаются вокруг Z
# Блок (0, -DIST)  — штыри на X=±A/2: трубы BR и BL вращаются вокруг Z
# Блок (-DIST, 0)  — штыри на Y=±A/2: трубы TL и BL вращаются вокруг Z
# Блок (+DIST, 0)  — штыри на Y=±A/2: трубы TR и BR вращаются вокруг Z
# Итого: 8 вращающих узлов, ось Z, по 90° в каждую сторону.

# ============================================================
# АНИМАЦИЯ — руки опускаются вниз (кадры 1→250)
# Pivot = центр teal-блока, ось перпендикулярна руке
# Трубы парентятся к рукам и следуют за ними
# ============================================================

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end   = 250

ANIM_ANGLE = math.radians(90)  # до фото 2 ~65°

def add_arm_anim(pivot_name, pivot_loc, arm_name, tube_names, wheel_name, rot_axis, angle):
    """Pivot на центре блока, рука + трубы + колесо вращаются вместе."""
    # Создаём Empty и сразу ставим правильную позицию
    pivot = bpy.data.objects.new(pivot_name, None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = pivot_loc
    pivot.rotation_mode = 'XYZ'
    bpy.context.view_layer.update()

    # Парентим всё к pivot
    children = [arm_name, wheel_name] + tube_names
    for cname in children:
        obj = bpy.data.objects.get(cname)
        if obj is None:
            continue
        mat = obj.matrix_world.copy()
        obj.parent = pivot
        obj.matrix_parent_inverse = pivot.matrix_world.inverted()
        obj.matrix_world = mat

    # Keyframes: 1=0°, 250=angle
    for frame, t in [(1, 0.0), (80, 0.2), (180, 0.75), (250, 1.0)]:
        bpy.context.scene.frame_set(frame)
        a = angle * t
        if rot_axis == 'X':
            pivot.rotation_euler = (a, 0, 0)
        elif rot_axis == 'Y':
            pivot.rotation_euler = (0, a, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame)

# ArmT (белая, вдоль Y) — pivot на (0, DIST, 0), ось X, вниз = -angle
add_arm_anim("Piv_ArmT", (0, DIST, 0),
    "ArmT",
    ["TealBlock_0"],
    f"Wheel_0.000_{DIST:.3f}",
    'Y', -ANIM_ANGLE)

add_arm_anim("Piv_ArmB", (0, -DIST, 0),
    "ArmB",
    ["TealBlock_1"],
    f"Wheel_0.000_{-DIST:.3f}",
    'Y', -ANIM_ANGLE)

add_arm_anim("Piv_ArmL", (-DIST, 0, 0),
    "ArmL",
    ["TealBlock_2"],
    f"Wheel_{-DIST:.3f}_0.000",
    'X', ANIM_ANGLE)

add_arm_anim("Piv_ArmR", (DIST, 0, 0),
    "ArmR",
    ["TealBlock_3"],
    f"Wheel_{DIST:.3f}_0.000",
    'X', ANIM_ANGLE)

bpy.context.scene.frame_set(1)
print("Анимация добавлена")
