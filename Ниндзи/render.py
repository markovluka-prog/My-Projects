import bpy
import math
from mathutils import Vector

# ── Сброс ─────────────────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ── Рендер ────────────────────────────────────────────────────────
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light      = 'MATCAP'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows    = True
scene.display.shading.show_specular_highlight = True
scene.render.resolution_x  = 1280
scene.render.resolution_y  = 720
scene.render.fps           = 24
scene.frame_start          = 1
scene.frame_end            = 576
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format              = 'MPEG4'
scene.render.ffmpeg.codec               = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.filepath = '/workspaces/My-Projects/Ниндзи/Ниндзи.mp4'

# ── Материалы ─────────────────────────────────────────────────────
def make_mat(name, color, roughness=0.6, metallic=0.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    out  = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value  = (*color, 1)
    bsdf.inputs['Roughness'].default_value   = roughness
    bsdf.inputs['Metallic'].default_value    = metallic
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1)
        bsdf.inputs['Emission Strength'].default_value = 2.0
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m

def make_wood_mat(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    out   = nodes.new('ShaderNodeOutputMaterial')
    bsdf  = nodes.new('ShaderNodeBsdfPrincipled')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value  = 15.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.7
    mix   = nodes.new('ShaderNodeMixRGB')
    mix.inputs['Color1'].default_value = (*color, 1)
    dark = tuple(max(0, c-0.15) for c in color)
    mix.inputs['Color2'].default_value = (*dark, 1)
    links.new(noise.outputs['Fac'],   mix.inputs['Fac'])
    links.new(mix.outputs['Color'],   bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.75
    links.new(bsdf.outputs['BSDF'],   out.inputs['Surface'])
    return m

MAT_OCEAN    = make_mat("ocean",   (0.04,0.22,0.55), roughness=0.05, metallic=0.1)
MAT_HULL1    = make_wood_mat("hull1", (0.45,0.28,0.10))
MAT_HULL2    = make_wood_mat("hull2", (0.30,0.30,0.40))
MAT_SAIL     = make_mat("sail",    (0.90,0.85,0.72), roughness=0.9)
MAT_SAIL_F   = make_mat("sail_f",  (0.70,0.70,0.82), roughness=0.9)
MAT_MAST     = make_mat("mast",    (0.55,0.38,0.18), roughness=0.8)
MAT_ROPE     = make_mat("rope",    (0.55,0.45,0.25), roughness=0.9)
MAT_RICHARD  = make_mat("richard", (0.75,0.08,0.08), roughness=0.7)
MAT_SOKOLIN  = make_mat("sokolin", (0.08,0.08,0.70), roughness=0.7)
MAT_BEN      = make_mat("ben",     (0.08,0.60,0.12), roughness=0.7)
MAT_ZHEN     = make_mat("zhen",    (0.75,0.60,0.05), roughness=0.7)
MAT_ZANTIO   = make_mat("zantio",  (0.85,0.85,0.85), roughness=0.7)
MAT_SKIN     = make_mat("skin",    (0.85,0.65,0.48), roughness=0.8)
MAT_SWORD    = make_mat("sword",   (0.75,0.75,0.80), roughness=0.2, metallic=0.9)
MAT_SKY_EMIS = make_mat("sky_bg",  (0.40,0.62,0.92), emission=(0.40,0.62,0.92))
MAT_CLOUD    = make_mat("cloud",   (0.95,0.95,0.98), roughness=1.0)

# ── Хелперы геометрии ─────────────────────────────────────────────
def obj(name, loc=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
    o = bpy.context.active_object
    o.name = name
    o.location = loc
    o.scale = scale
    o.rotation_euler = tuple(math.radians(r) for r in rot)
    return o

def cube(name, loc, scale, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = obj(name, loc, scale, rot)
    o.data.materials.append(mat)
    return o

def cyl(name, loc, r, h, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc)
    o = obj(name, loc, rot=rot)
    o.data.materials.append(mat)
    return o

def sph(name, loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc,
        segments=16, ring_count=8)
    o = obj(name, loc)
    o.data.materials.append(mat)
    return o

def cone(name, loc, r1, r2, h, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h,
        location=loc)
    o = obj(name, loc, rot=rot)
    o.data.materials.append(mat)
    return o

# ── Корабль ───────────────────────────────────────────────────────
def make_ship(prefix, x, y, hull_mat, sail_mat, big=False):
    W = 2.2 if big else 1.4
    L = 6.0 if big else 4.0
    H = 0.7 if big else 0.5

    parts = []
    # Корпус
    parts.append(cube(f"{prefix}_hull",    (x,y,H/2),          (L,W,H),      hull_mat))
    # Нос (заострённый — конус)
    parts.append(cone(f"{prefix}_bow",     (x+L/2+0.3, y, H/2), 0.01, W/2, H, hull_mat, (0,90,0)))
    # Корма закруглённая
    parts.append(cube(f"{prefix}_stern",   (x-L/2+0.3, y, H/2+0.25), (0.6,W,0.5), hull_mat))
    # Палуба
    parts.append(cube(f"{prefix}_deck",    (x,y,H+0.05),        (L+0.3,W+0.1,0.1), hull_mat))
    # Перила (4 стороны)
    parts.append(cube(f"{prefix}_rail_l",  (x,y+W/2+0.05,H+0.3),(L,0.08,0.5), hull_mat))
    parts.append(cube(f"{prefix}_rail_r",  (x,y-W/2-0.05,H+0.3),(L,0.08,0.5), hull_mat))
    # Мачта 1
    mh = 4.5 if big else 3.5
    parts.append(cyl(f"{prefix}_mast1",   (x+0.5 if big else x+0.3, y, H+mh/2), 0.1 if big else 0.07, mh, MAT_MAST))
    # Рей
    yw = 2.0 if big else 1.4
    parts.append(cyl(f"{prefix}_yard1",   (x+0.5 if big else x+0.3, y, H+mh-0.8), 0.05, yw*2, MAT_MAST, rot=(0,90,0)))
    # Парус 1
    parts.append(cube(f"{prefix}_sail1",  (x+0.55 if big else x+0.35, y, H+mh-1.5), (0.05,yw*1.9,1.8 if big else 1.3), sail_mat))
    # Мачта 2 (большой корабль)
    if big:
        parts.append(cyl(f"{prefix}_mast2",  (x-1.5, y, H+3.5), 0.09, 4.0, MAT_MAST))
        parts.append(cyl(f"{prefix}_yard2",  (x-1.5, y, H+3.2), 0.05, 3.8, MAT_MAST, rot=(0,90,0)))
        parts.append(cube(f"{prefix}_sail2", (x-1.5, y, H+2.5), (0.05,3.6,1.5), sail_mat))
    # Пушки
    for sign in [-0.4, 0.4]:
        parts.append(cyl(f"{prefix}_cannon_{sign}", (x+sign*L*0.25, y+W/2, H+0.25), 0.1, 0.7, MAT_SWORD, rot=(0,90,0)))
    return parts

# ── Персонаж ──────────────────────────────────────────────────────
def make_char(name, x, y, z, body_mat, has_sword=False):
    parts = {}
    # Торс
    parts['torso'] = cube(f"{name}_torso", (x,y,z+0.55), (0.28,0.22,0.45), body_mat)
    # Голова
    parts['head']  = sph(f"{name}_head",  (x,y,z+1.02), 0.18, MAT_SKIN)
    # Шея
    parts['neck']  = cyl(f"{name}_neck",  (x,y,z+0.85), 0.06, 0.18, MAT_SKIN)
    # Ноги
    parts['leg_l'] = cyl(f"{name}_legl",  (x+0.08,y,z+0.18), 0.07, 0.42, body_mat)
    parts['leg_r'] = cyl(f"{name}_legr",  (x-0.08,y,z+0.18), 0.07, 0.42, body_mat)
    # Руки
    parts['arm_l'] = cyl(f"{name}_arml",  (x+0.2, y,z+0.65), 0.05, 0.38, body_mat, rot=(0,0,25))
    parts['arm_r'] = cyl(f"{name}_armr",  (x-0.2, y,z+0.65), 0.05, 0.38, body_mat, rot=(0,0,-25))
    # Меч
    if has_sword:
        parts['sword_blade'] = cube(f"{name}_blade", (x-0.38,y,z+0.55), (0.04,0.04,0.75), MAT_SWORD)
        parts['sword_guard'] = cube(f"{name}_guard", (x-0.38,y,z+0.2),  (0.04,0.22,0.06), MAT_SWORD)
    # Маска ниндзя (полоска)
    mask_mat = make_mat(f"{name}_mask", (0.05,0.05,0.05))
    parts['mask'] = cube(f"{name}_mask", (x,y-0.17,z+1.02), (0.36,0.02,0.10), mask_mat)
    return parts

# ── Сцена ─────────────────────────────────────────────────────────
# Небо
bpy.ops.mesh.primitive_plane_add(size=300, location=(0,0,-0.5))
o = bpy.context.active_object; o.name="ocean_plane"; o.data.materials.append(MAT_OCEAN)

# Горизонт-фон
cube("sky_bg", (0,80,15), (300,1,40), MAT_SKY_EMIS)

# Облака
for i,(cx,cy,cz,sx,sy) in enumerate([(20,60,12,8,3),(-10,65,14,6,2),(-30,62,11,10,4)]):
    cube(f"cloud_{i}", (cx,cy,cz), (sx,sy,1.5), MAT_CLOUD)

# Корабли
make_ship("R", -7,  0, MAT_HULL1, MAT_SAIL,   big=False)
make_ship("F",  7,  0, MAT_HULL2, MAT_SAIL_F, big=True)

# Персонажи — флагман
make_char("Sokolin", 6.2, -0.5, 1.2, MAT_SOKOLIN, has_sword=True)
make_char("Ben",     7.5,  0.4, 1.2, MAT_BEN,     has_sword=False)
make_char("Zhen",    8.2, -0.3, 1.2, MAT_ZHEN,    has_sword=True)
make_char("Zantio",  7.0,  0.8, 1.2, MAT_ZANTIO,  has_sword=False)

# Ричард — малый корабль
make_char("Richard", -7.0, 0.0, 1.0, MAT_RICHARD, has_sword=True)

# ── Освещение ─────────────────────────────────────────────────────
# Солнце
bpy.ops.object.light_add(type='SUN', location=(15,-5,20))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 5.0
sun.data.color  = (1.0, 0.95, 0.82)
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

# Заполняющий свет — небо
bpy.ops.object.light_add(type='AREA', location=(0,-20,10))
sky_light = bpy.context.active_object
sky_light.name = "SkyFill"
sky_light.data.energy = 200
sky_light.data.color  = (0.5, 0.7, 1.0)
sky_light.data.size   = 20
sky_light.rotation_euler = (math.radians(60), 0, 0)

# Подсвет воды
bpy.ops.object.light_add(type='AREA', location=(0,0,-1))
water_light = bpy.context.active_object
water_light.data.energy = 50
water_light.data.color  = (0.15, 0.35, 0.7)
water_light.data.size   = 40

# ── Камера ────────────────────────────────────────────────────────
bpy.ops.object.camera_add(location=(0,-20,8))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 35
scene.camera  = cam

def kf_loc(obj, loc, f):
    obj.location = loc
    obj.keyframe_insert("location", frame=f)

def kf_rot(obj, rot_deg, f):
    obj.rotation_euler = tuple(math.radians(r) for r in rot_deg)
    obj.keyframe_insert("rotation_euler", frame=f)

def kf_vis(obj, vis, f):
    obj.hide_render   = not vis
    obj.hide_viewport = not vis
    obj.keyframe_insert("hide_render",   frame=f)
    obj.keyframe_insert("hide_viewport", frame=f)

# ── Титры ─────────────────────────────────────────────────────────
def add_title(text, fs, fe, z=5, size=1.0):
    bpy.ops.object.text_add(location=(0,-14,z))
    t = bpy.context.active_object
    t.name = f"T_{fs}"
    t.data.body    = text
    t.data.align_x = 'CENTER'
    t.data.size    = size
    t.rotation_euler = (math.radians(90),0,0)
    tm = make_mat(f"tm_{fs}", (1,1,1), emission=(1,1,1))
    tm.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 3.0
    t.data.materials.append(tm)
    kf_vis(t, False,  1)
    kf_vis(t, False, fs-1)
    kf_vis(t, True,  fs)
    kf_vis(t, True,  fe)
    kf_vis(t, False, fe+1)

add_title("НИНДЗИ",                    1,  72,  z=5.5, size=1.4)
add_title("Часть пятая",              73, 120,  z=5.0, size=0.8)
add_title("Морской бой",             121, 168,  z=5.0, size=0.9)
add_title("Зантио — новый капитан",  169, 216,  z=5.0, size=0.7)
add_title("А Б О Р Д А Ж !",        217, 264,  z=5.5, size=1.2)
add_title("Шквальный ветер!",        289, 336,  z=5.5, size=1.0)
add_title("Прыжок Ричарда",          337, 384,  z=5.0, size=0.8)
add_title("Зантио, ВОН!",            432, 480,  z=5.5, size=1.2)
add_title("Продолжение следует...",  504, 576,  z=5.0, size=0.7)

# ── Анимация кораблей ─────────────────────────────────────────────
ship_r = bpy.data.objects["R_hull"]
ship_f = bpy.data.objects["F_hull"]
ric_t  = bpy.data.objects["Richard_torso"]
ric_h  = bpy.data.objects["Richard_head"]
zan_t  = bpy.data.objects["Zantio_torso"]
zan_h  = bpy.data.objects["Zantio_head"]

# Малый корабль маневрирует
for f, x, y in [(1,-7,0),(72,-7,0),(120,-5,1.5),(150,-3,-1),(192,-6,0),(216,-7,0),
                (288,-7,0),(350,-3,0),(390,4,0),(432,4,0),(576,4,0)]:
    kf_loc(ship_r, (x,y,0), f)
    kf_loc(ric_t,  (x,y,1.0), f)
    kf_loc(ric_h,  (x,y,1.62), f)

# Прыжок Ричарда (воздух)
kf_loc(ric_t, (-3, 0, 1.0), 337)
kf_loc(ric_t, ( 0, 0, 3.5), 362)   # в воздухе
kf_loc(ric_t, ( 6, 0, 1.2), 388)
kf_loc(ric_h, (-3, 0, 1.62), 337)
kf_loc(ric_h, ( 0, 0, 4.12), 362)
kf_loc(ric_h, ( 6, 0, 1.82), 388)

# Флагман надвигается
for f, x in [(1,7),(216,7),(288,7),(320,2),(336,1),(432,1),(576,1)]:
    kf_loc(ship_f, (x,0,0), f)

# Шквал — флагман разворачивает боком
kf_rot(ship_f, (0,0,0),  288)
kf_rot(ship_f, (0,0,50), 306)
kf_rot(ship_f, (0,0,0),  336)

# Зантио вылетает за борт
kf_loc(zan_t, (7.0, 0.8, 1.2),  432)
kf_loc(zan_t, (7.0,-10.0,-3.0), 476)
kf_rot(zan_t, (0,0,0),   432)
kf_rot(zan_t, (80,0,45), 476)
kf_loc(zan_h, (7.0, 0.8, 1.82), 432)
kf_loc(zan_h, (7.0,-10.0,-2.3), 476)

# ── Анимация камеры ───────────────────────────────────────────────
for f, loc, rot in [
    (1,   ( 0,-20, 8),  (68,0,  0)),
    (72,  ( 0,-20, 8),  (68,0,  0)),
    (144, (-9,-14, 6),  (72,0,-12)),
    (216, ( 0,-18, 7),  (68,0,  0)),
    (264, ( 4,-12, 5),  (74,0, 15)),
    (310, (-2,-10, 6),  (70,0, -8)),
    (360, ( 1,-14, 8),  (62,0,  4)),
    (420, ( 5,-12, 5),  (72,0, 12)),
    (480, ( 0,-20, 8),  (68,0,  0)),
    (576, ( 0,-20, 8),  (68,0,  0)),
]:
    kf_loc(cam, loc, f)
    kf_rot(cam, rot, f)

# ── Рендер ────────────────────────────────────────────────────────
print("Начинаю рендер... 576 кадров, 1280x720, Cycles 32spp")
bpy.ops.render.render(animation=True)
print("Готово! → /workspaces/My-Projects/Ниндзи/Ниндзи.mp4")
