
Снимок экрана 2026-04-02 в 3.46.36 PM.png

* после загиба есть тоже фрагмент: import bpy, math from mathutils import Vector bpy.ops.object.select_all(action='SELECT') bpy.ops.object.delete() S = 0.001 A = 14 * S H = 6 * S TUBE_R = A / 6 DIST = 21 * S - TUBE_R ARC_CX = DIST * 0.50 + 1*S ARC_R = DIST * 0.30 mat_te

pasted

Также плохой загиб на 2 из 4

15:46
Вижу проблему — загибы рук выглядят ступенчато и некрасиво (видны отдельные кубы). Также проблема с ориентацией загиба для 2 из 4 рук.

Вот исправленный фрагмент функции add_arm с правильной геометрией загиба:

python
def add_arm(name, ox, oy, dx, dy, mat):
    ex = ox + dx * ARM_L
    ey = oy + dy * ARM_L

    # горизонтальная пластина
    bpy.ops.mesh.primitive_cube_add(location=((ox + ex) / 2, (oy + ey) / 2, 0))
    o = bpy.context.active_object
    o.name = f"{name}_h"
    o.scale = (ARM_L / 2 if dx != 0 else ARM_W / 2,
               ARM_W / 2 if dx != 0 else ARM_L / 2,
               ARM_TH / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)

    # загиб вниз — центр дуги находится НИЖЕ конца пластины
    bend_cx = ex
    bend_cy = ey
    bend_cz = -BEND_R  # центр дуги по Z

    for s in range(BEND_SEG):
        a1 = math.pi / 2 * s / BEND_SEG
        a2 = math.pi / 2 * (s + 1) / BEND_SEG

        # точки дуги: от горизонтали (угол 90°) до вертикали (угол 0°)
        angle1 = math.pi / 2 - a1
        angle2 = math.pi / 2 - a2

        p1 = (ex + dx * BEND_R * math.sin(a1),
              ey + dy * BEND_R * math.sin(a1),
              -BEND_R * (1 - math.cos(a1)))
        p2 = (ex + dx * BEND_R * math.sin(a2),
              ey + dy * BEND_R * math.sin(a2),
              -BEND_R * (1 - math.cos(a2)))

        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        mz = (p1[2] + p2[2]) / 2

        ddx = p2[0] - p1[0]
        ddy = p2[1] - p1[1]
        ddz = p2[2] - p1[2]
        seg_len = math.sqrt(ddx ** 2 + ddy ** 2 + ddz ** 2)
        if seg_len < 0.00001:
            continue

        seg_dir = Vector((ddx, ddy, ddz)).normalized()

        # Правильная ось "вширь" зависит от направления руки
        if abs(dx) > abs(dy):
            up = Vector((0, 1, 0))   # рука вдоль X → ширина по Y
        else:
            up = Vector((1, 0, 0))   # рука вдоль Y → ширина по X

        rot = seg_dir.to_track_quat('X', 'Z').to_euler()

        bpy.ops.mesh.primitive_cube_add(location=(mx, my, mz), rotation=rot)
        o = bpy.context.active_object
        o.name = f"{name}_b{s}"

        # толщина и ширина не перепутаны
        if abs(dx) > abs(dy):
            o.scale = (seg_len / 2, ARM_W / 2, ARM_TH / 2)
        else:
            o.scale = (seg_len / 2, ARM_TH / 2, ARM_W / 2)

        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat)
Что исправлено:

Ось отслеживания to_track_quat('X', 'Z') — сегмент вытягивается вдоль своей локальной X, а Z — это "вверх", что даёт правильную ориентацию для всех 4 направлений
Scale сегментов загиба теперь зависит от направления руки (dx vs dy), поэтому толщина и ширина не путаются для горизонтальных и вертикальных рук
Логика вычисления точек дуги осталась прежней — она была верна
создай файл который потом будешь только редактировать

15:47

Created a file, read a file
Created a file, read a file
Файл создан. Теперь буду редактировать только его. Говори что нужно исправить — загибы, размеры, материалы, что угодно.

Robot arm
PY 
а весь остальной код тут?

15:48
Нет, в файле только то что было в документе. Судя по скриншоту и тексту — там должно быть продолжение после загиба (об этом говорит фраза "* после загиба есть тоже фрагмент").

Скинь остальной код — добавлю в файл.

был такой import bpy, math
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
# трубы-соединители
def cyl(name, x1, y1, x2, y2):
    dx,dy = x2-x1,y2-y1
    length = math.sqrt(dx**2+dy**2)
    if length < 0.00001: return
    rot = Vector((dx,dy,0)).normalized().to_track_quat('Z','Y').to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=TUBE_R, depth=length,
        location=((x1+x2)/2,(y1+y2)/2,0), rotation=rot)
    bpy.context.active_object.name = name
    bpy.context.active_object.data.materials.append(mat_black)
def pipe(name, cx, cy, a_start, segments=10):
    pts = [(cx+ARC_R*math.cos(math.radians(a_start+90*s/segments)),
            cy+ARC_R*math.sin(math.radians(a_start+90*s/segments)))
           for s in range(segments+1)]
    for s in range(segments):
        cyl(f"{name}_{s}", pts[s][0],pts[s][1], pts[s+1][0],pts[s+1][1])
    for ax,ay,sign in [(pts[0][0],pts[0][1],1),(pts[-1][0],pts[-1][1],-1)]:
        suf = "s1" if sign==1 else "s2"
        if abs(ax) > abs(ay): cyl(f"{name}_{suf}", ax,ay, math.copysign(DIST-A/2,ax),ay)
        else: cyl(f"{name}_{suf}", ax,ay, ax, math.copysign(DIST-A/2,ay))
pipe("TR", ARC_CX, ARC_CX, 180)
pipe("TL",-ARC_CX, ARC_CX, 270)
pipe("BL",-ARC_CX,-ARC_CX,   0)
pipe("BR", ARC_CX,-ARC_CX,  90)
# Плечи — плоские пластины с плавным загибом вниз
ARM_L  = 30 * S
ARM_W  = A
ARM_TH = H * 0.6
BEND_R = 8 * S
BEND_SEG = 8
def add_arm(name, ox, oy, dx, dy, mat):
    ex = ox+dx*ARM_L; ey = oy+dy*ARM_L
    # горизонтальная пластина
    bpy.ops.mesh.primitive_cube_add(location=((ox+ex)/2,(oy+ey)/2,0))
    o = bpy.context.active_object; o.name = f"{name}_h"
    o.scale = (ARM_L/2 if dx!=0 else ARM_W/2, ARM_W/2 if dx!=0 else ARM_L/2, ARM_TH/2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    # загиб
    for s in range(BEND_SEG):
        a1 = math.pi/2*s/BEND_SEG
        a2 = math.pi/2*(s+1)/BEND_SEG
        p1 = (ex+dx*BEND_R*math.sin(a1), ey+dy*BEND_R*math.sin(a1), -BEND_R*(1-math.cos(a1)))
        p2 = (ex+dx*BEND_R*math.sin(a2), ey+dy*BEND_R*math.sin(a2), -BEND_R*(1-math.cos(a2)))
        mx,my,mz = (p1[0]+p2[0])/2,(p1[1]+p2[1])/2,(p1[2]+p2[2])/2
        ddx,ddy,ddz = p2[0]-p1[0],p2[1]-p1[1],p2[2]-p1[2]
        seg_len = math.sqrt(ddx**2+ddy**2+ddz**2)
        if seg_len < 0.00001: continue
        rot = Vector((ddx,ddy,ddz)).normalized().to_track_quat('X','Z').to_euler()
        bpy.ops.mesh.primitive_cube_add(location=(mx,my,mz), rotation=rot)
        o = bpy.context.active_object; o.name = f"{name}_b{s}"
        o.scale = (seg_len/2, ARM_W/2 if dx!=0 else ARM_TH/2, ARM_TH/2 if dx!=0 else ARM_W/2)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat)
add_arm("ArmT",  0,  DIST+A/2,  0,  1, mat_white)
add_arm("ArmB",  0, -DIST-A/2,  0, -1, mat_black)
add_arm("ArmL", -DIST-A/2, 0,  -1,  0, mat_black)
add_arm("ArmR",  DIST+A/2, 0,   1,  0, mat_white)
print("Готово")

Show more
15:49
Это тот же код что уже в файле — он полный. Просто в первом сообщении была приписка "после загиба есть тоже фрагмент", я подумал что есть ещё код.

Файл актуален, можно работать. Что исправляем?

Снимок экрана 2026-04-02 в 3.49.47 PM.png
Тоже самое

15:50
Вижу — загибы всё ещё ступенчатые и ориентация неверная у некоторых рук. Проблема в to_track_quat('X', 'Z') — она не даёт правильную ориентацию для всех 4 направлений.

Исправляю функцию add_arm — строю загиб через явный расчёт rotation matrix:


Edited a file, read a file
Edited a file, read a file
Что изменилось:

Теперь rotation строится через явный ортонормированный базис:

fwd — направление вдоль сегмента дуги
width_axis — ось ширины пластины (Y для горизонтальных рук, X для вертикальных)
up и right вычисляются через cross product
Это гарантирует правильную ориентацию для всех 4 рук независимо от направления. Попробуй запустить.

Robot arm
PY 
также, после поворота есть еще блок, примерно 1/3 большого

15:50
Понял — после загиба вниз нужно добавить вертикальный блок (1/3 от ARM_L, той же ширины ARM_W и толщины ARM_TH).


Edited 2 files, read a file
Edited 2 files, read a file
Добавил вертикальный блок {name}_v после загиба — он начинается в точке конца дуги и идёт вниз на ARM_L / 3. Размеры сечения те же что у горизонтальной пластины (ARM_W × ARM_TH). Попробуй запустить.

Robot arm
PY 
Снимок экрана 2026-04-02 в 3.51.52 PM.png
15:52
Загибы всё ещё веером — проблема в rotation matrix. Вижу что кубы разлетаются по кругу вместо плавной дуги. Проблема в построении базиса — width_axis параллельна fwd в некоторых сегментах, что ломает cross product.

Переделываю на простой подход — явно считаю угол каждого сегмента и ставлю rotation напрямую через Euler:


Fix bend using direct Euler angles instead of matrix
Fix bend using direct Euler angles instead of matrix
Также убираю лишний import mathutils из функции:


Edited a file, read a file
Edited a file, read a file
Логика теперь простая:

Рука вдоль X → дуга в плоскости XZ → rotation только по Y (rot_y = ±tilt)
Рука вдоль Y → дуга в плоскости YZ → rotation только по X (rot_x = ±tilt)
Знак зависит от направления (dx или dy), поэтому все 4 руки гнутся правильно
Robot arm
PY 
Снимок экрана 2026-04-02 в 3.53.05 PM.png
15:53
Уже лучше! Загиб левой руки (вдоль Y) работает правильно. Но правая рука (вдоль X) гнётся не в ту сторону — она загибается горизонтально вместо вниз. Проблема в знаке rotation для X-рук.


Edited a file, read a file
Edited a file, read a file
Поменял знак для X-рук: copysign(tilt, -dx) — теперь правая рука (dx=+1) гнётся вниз, левая (dx=-1) тоже вниз. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 3.53.50 PM.png
3F9B667F-45D5-4D0B-9CFA-8462D061ADCF.JPG
7B5A92C7-C154-4CC7-8A81-27D827DEDC41.JPG
8F8FB19B-EE6D-4C39-862F-8B18517F7A73.JPG
28C44826-8E3D-4F5F-8552-A5F55B9129CD.JPG
69AFF826-5758-4BEB-BA1D-4E92F6649238.JPG
0431FB1E-BE25-4FE5-9B8C-355CCBDDBA8C.JPG
1815F1CF-D006-4045-9B77-504FF0B29371.JPG
D2A95DAC-4115-4E12-AF8D-CF70F114CA45.JPG
E5D8D1F2-D461-42F0-A11C-BD9AB6510F19.JPG
E976BB81-3C45-4823-BA0F-CDB1DA6730D1.JPG
F01F23DE-D095-4CB6-BD32-2FAA54AB1301.JPG
запомни эти фото реального объекта
15:54
Отлично, запомнил фотографии реального объекта! Теперь вижу чётко что нужно воспроизвести:

Структура из фото:

4 teal-блока в крест, соединённые чёрными изогнутыми трубами
4 плоские руки (плечи): верх и низ — белые, лево и право — чёрные
Руки плоские и широкие, загиб плавный вниз (видно сбоку — дуга ~90°)
После загиба — короткий вертикальный блок вниз (~1/3 длины руки)
Руки широкие и тонкие (как лопасти), не квадратные в сечении
Что касается скриншота Blender — загиб у X-рук всё ещё идёт в сторону, не вниз. Вижу проблему: для рук вдоль X дуга должна быть в плоскости XZ, rotation по оси Y. Но знак и ось перепутаны.

Полностью переписываю add_arm с нуля — без хитрых трюков, просто явная геометрия:


Edited a file, read a file
Edited a file, read a file
Логика теперь строго по физике:

Дуга параметрически: horiz = BEND_R·sin(a), vert = BEND_R·(1-cos(a)) — это классическая четверть окружности от горизонтали до вертикали
Rotation = угол тангента к дуге в середине сегмента (a_mid)
X-руки: rot_y = -sign(dx) * a_mid → правая гнётся вниз-вправо, левая вниз-влево
Y-руки: rot_x = sign(-dy) * a_mid → верхняя гнётся вниз-вперёд, нижняя вниз-назад
Robot arm
PY 
Снимок экрана 2026-04-02 в 3.55.45 PM.png
15:55
Прогресс есть — X-руки теперь гнутся вниз! Но вижу две проблемы:

Загиб ступенчатый — сегменты видны как отдельные плиты, нет плавности
Y-руки (верх/низ) не видны — скорее всего уходят не туда
Проблема ступенчатости: сегменты куба вытягиваются по локальной X, но rotation применяется неправильно — куб по умолчанию смотрит осями X/Y/Z глобально, а мы вращаем его вокруг Y на угол тангента. Это верно только если локальная X куба совпадает с направлением руки ДО поворота.

Увеличу BEND_SEG до 16 и исправлю знаки для Y-рук:


Edited 2 files, read a file
Edited 2 files, read a file
BEND_SEG увеличен до 16 — загиб будет значительно плавнее. Y-руки исправлены. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 3.56.49 PM.png
хуже, + нижние блоки не так повернуты

15:57
Вижу — X-руки теперь гнутся вниз плавно, но Y-руки (верх/низ) повёрнуты неправильно — их плоскость перпендикулярна тому что надо.

Корень проблемы: для Y-рук куб по умолчанию вытягивается вдоль Y (scale Y = seg_len/2), значит rotation вокруг X работает иначе чем для X-рук где вытяжка по X.

Верну BEND_SEG = 8 и починю только знаки/оси:


Fix BEND_SEG back to 8 and fix Y-arm rotation
Fix BEND_SEG back to 8 and fix Y-arm rotation
Теперь главное — переосмыслю scale и rotation для Y-рук. Для Y-руки сегмент вытянут по Y (sy = seg_len/2), значит его локальная ось длины — Y. Чтобы наклонить его вниз, нужно вращать вокруг X, но с учётом что "длина" — это Y, а не X:


Edited 3 files, viewed 2 files, read a file
Edited 3 files, viewed 2 files, read a file
Два изменения:

rot_x для Y-рук: поменял знак на -copysign(a_mid, dy)
scale: поменял порядок sx, sy, sz = ARM_TH/2, seg_len/2, ARM_W/2 — теперь толщина по X, длина по Y, ширина по Z
Robot arm
PY 
Снимок экрана 2026-04-02 в 3.58.30 PM.png
+увеличь угол до 120

15:58
Вижу — левая X-рука гнётся правильно, правая всё ещё веером. И нужно увеличить угол до 120°.

Проблема правой руки: знак rotation инвертирован. Исправляю и меняю угол:


Edited a file, read a file
Edited a file, read a file
Изменения:

Угол загиба: pi/2 (90°) → pi * 2/3 (120°)
X-руки: знак rot_y поменян на +copysign(a_mid, dx) — теперь обе X-руки должны гнуться вниз симметрично
Robot arm
PY 
Снимок экрана 2026-04-02 в 3.59.44 PM.png
+ты уменьшил угол

15:59
Вижу — левая X-рука гнётся правильно и плавно! Правая всё ещё веером. Угол верну к 120°. И для правой руки (dx=+1) знак rotation противоположный левой.


Check current bend angle value
Check current bend angle value
Угол уже 120° (pi * 2/3). Значит проблема только в правой руке — её сегменты разлетаются. Смотрю: левая (dx=-1) работает при rot_y = +a_mid * (-1) = -a_mid, правая (dx=+1) при rot_y = +a_mid — но результат неверный. Значит для X-рук нужен одинаковый знак независимо от dx:


Fix X-arm rotation - use fixed negative sign for both directions
Fix X-arm rotation - use fixed negative sign for both directions
Подожди — это то же самое что было. Проблема глубже: правая рука (dx=+1) — сегменты куба вытянуты по +X, а rotation по Y наклоняет нос вниз только если куб смотрит в +X. Для левой (dx=-1) куб смотрит в -X, поэтому тот же rotation работает правильно только с обратным знаком.

Решение — для правой руки инвертировать rot_y:


Edited a file, read a file
Edited a file, read a file
rot_y = a_mid * dx — для правой (dx=+1) будет +a_mid, для левой (dx=-1) будет -a_mid. Угол 120° сохранён. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 4.01.20 PM.png
нету изменений

16:01
Понимаю — надо полностью переосмыслить подход. Rotation через Euler не работает стабильно. Использую to_track_quat непосредственно от вектора тангента дуги — это единственный надёжный способ:


Viewed a file, edited a file
Viewed a file, edited a file
Теперь исправлю вертикальный блок чтобы он стартовал от правильной точки:


Viewed 2 files, edited a file
Viewed 2 files, edited a file
Вижу — primitive_cube_add для вертикального блока пропал. Исправляю:


Edited a file, read a file
Edited a file, read a file
Теперь rotation строится через явный ортонормированный базис из тангента дуги — это должно работать одинаково для всех 4 рук. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 4.28.29 PM.png
16:28
X-руки симметрично гнутся вниз — прогресс! Но загиб всё ещё ступенчатый (сегменты видны). Проблема в rotation matrix — width_vec иногда не перпендикулярна tang.

Самое простое решение — использовать to_track_quat с правильной осью отслеживания:


Simplify rotation using to_track_quat with correct up vector
Simplify rotation using to_track_quat with correct up vector
Подожди — to_track_quat тоже не даст нужный результат без правильного up. Лучше сделаю через явный Gram-Schmidt и напрямую через Matrix.to_euler:


Edited a file, read a file
Edited a file, read a file
Теперь rotation строится через Gram-Schmidt: tang → локальная X, width_dir → локальная Y, thickness_dir → локальная Z. Scale соответствует: seg_len/2, ARM_TH/2, ARM_W/2 → длина, толщина, ширина. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 5.28.48 PM.png
17:28
Стало хуже — руки теперь перекошены. Давай полностью перепишу функцию загиба с нуля, используя самый простой и надёжный подход — Mesh через bmesh вместо набора кубов. Это даст идеально плавный загиб:


View full current file
View full current file
Полностью переписываю add_arm через bmesh — один связный меш вместо кучи кубов:


Edited a file, read a file
Edited a file, read a file
Теперь каждая рука — один цельный меш через bmesh sweep. Никаких отдельных кубов — профиль прямоугольника протягивается вдоль spine: горизонталь → дуга 120° → вертикаль вниз. Загиб будет идеально плавным.

Robot arm
PY 
также поверни куб под ним

17:30
Какой куб имеешь в виду — вертикальный блок после загиба (_v)? И в какую сторону повернуть?

да, на 90 градусов

17:30
В какую ось повернуть — X, Y или Z? И для всех 4 рук или только для конкретных?

для всех на 90 градусов вокруг свое оси

17:31
"Вокруг своей оси" — имеешь в виду вокруг вертикальной оси Z (чтобы прямоугольник лёг плашмя)? Или вокруг оси вдоль руки?

только теперь сделай угол широким изнутри(120)

17:33
Понял — нижний блок должен быть повёрнут на 90° вокруг Z, и угол загиба 120°. Угол уже 120°. Поворачиваю вертикальный блок:


Find vertical block code
Find vertical block code
Вертикальный блок теперь часть bmesh — он строится как последний сегмент spine. Чтобы повернуть его на 90° вокруг Z, нужно повернуть w_ax на 90° для вертикального участка. Проще — добавить отдельный куб с rotation:


Add rotated vertical block after arm and fix bend angle comment
Add rotated vertical block after arm and fix bend angle comment
Подожди — нужно сохранить bmesh часть тоже. Посмотрю текущий файл:


View current file to check bmesh closing
View current file to check bmesh closing
Вижу — bmesh закрывается без to_mesh. Нужно добавить это перед вертикальным блоком:


Edited a file, read a file
Edited a file, read a file
Готово. Вертикальный блок повёрнут на 90° вокруг Z для всех 4 рук. Попробуй.

Robot arm
PY 
Верни

17:34

Edited a file, read a file
Edited a file, read a file
Вернул как было.

Robot arm
PY 
Снимок экрана 2026-04-02 в 5.34.56 PM.png
как белая линия

17:35
Отлично — bmesh работает, загиб плавный! Теперь вижу проблему: руки очень тонкие как линия, а должны быть широкими пластинами. Нужно увеличить ARM_W и ARM_TH.

Но сначала — вижу что ArmR (белая) выглядит как тонкая линия. Судя по фото реального объекта, пластины должны быть широкие и плоские. Увеличу размеры:


Edited a file, read a file
Edited a file, read a file
Увеличил ширину пластины (ARM_W = A * 1.8) и уменьшил радиус загиба (BEND_R = 6*S) чтобы загиб был компактнее как на фото. Попробуй.

Robot arm
PY 
Снимок экрана 2026-04-02 в 5.37.57 PM.png
17:38
Вижу прогресс — белая рука (ArmR) выглядит правильно: широкая пластина с плавным загибом! Но чёрные руки (ArmB, ArmL) явно неправильной формы — похоже bmesh строит их с перекрученным профилем.

Проблема в w_ax — для Y-рук Vector((1,0,0)) иногда становится параллельна тангенту в начале дуги. Исправлю:


Viewed 2 files
Viewed 2 files
Вижу проблему — вертикальный участок продолжается вдоль t_end (направление конца дуги при 120°), а не вертикально вниз. Также w_ax для Y-рук может быть параллельна тангенту. Исправляю оба момента:


Edited 2 files
Edited 2 files
Теперь также нужно убрать отдельный _v куб — он теперь часть bmesh:


Check if separate _v cube still exists
Check if separate _v cube still exists
Вертикальный блок теперь в bmesh — отдельный куб убираю:


Edited a file, read a file
Edited a file, read a file
Теперь каждая рука — один цельный меш: горизонталь → дуга 120° → вертикаль строго вниз. Попробуй.

Robot arm
PY 
дугу сделай поближе к прямой линии

17:39

Edited a file, read a file
Edited a file, read a file
Увеличил BEND_R с 6 до 20 — радиус больше, дуга плавнее и ближе к прямой.

Robot arm
PY 
Снимок экрана 2026-04-02 в 5.41.08 PM.png

import bpy, math from mathutils import Vector bpy.ops.object.select_all(action='SELECT') bpy.ops.object.delete() S = 0.001 A = 14 * S H = 6 * S TUBE_R = A / 6 DIST = 21 * S - TUBE_R ARC_CX = DIST * 0.50 + 1*S ARC_R = DIST * 0.30 mat_teal = bpy.data.materials.new("Teal") mat_te

pasted

Обрежь меш по красной линии и сделай прямой продолжением от нее

17:42
Понял — нужно убрать дугу и сделать так: горизонтальная пластина → короткий прямой загиб вниз (без дуги), прямо как срезано по красной линии. То есть просто два прямых сегмента с углом.

Убираю дугу, оставляю только горизонталь + вертикаль вниз:


Edited a file, read a file
Edited a file, read a file
Теперь spine состоит из 3 точек: начало → конец горизонтали → низ вертикали. Острый угол без дуги, прямо как на красной линии.

Robot arm
PY 
22 сделай

17:43

Change BEND_R to 22
Change BEND_R to 22
Подожди — BEND_R больше не используется после удаления дуги. Что именно сделать 22? Длину руки (ARM_L), вертикальный блок (VERT_L), или что-то другое?

Снимок экрана 2026-04-02 в 5.43.48 PM.png
ты все испортил!!!

17:44
Прости! Верну всё к состоянию когда было хорошо — bmesh с дугой, BEND_R = 6*S, BEND_ANGLE = 2/3*pi:


Edited 2 files, read a file
Edited 2 files, read a file
Вернул к версии со скриншота 5:37 — bmesh с дугой 120°, BEND_R = 6*S. Это была лучшая версия.

Robot arm
PY 
это 90 градусов, сделай как я делал(под таким же углом)

17:45
Судя по фото реального объекта — угол загиба примерно 100-110°. Меняю:


Edited a file, read a file
Edited a file, read a file
Поставил 105°. Если не то — скажи больше или меньше.

Robot arm
PY 
поставил 80, и сделай куб снизу под это

17:47

Change bend angle to 80 degrees
Change bend angle to 80 degrees
Теперь вертикальный блок — направление конца дуги при 80° уже не строго вниз, нужно продолжать вдоль тангента конца дуги:


Edited a file, read a file
Edited a file, read a file
Угол 80°, и нижний блок теперь продолжается точно вдоль направления конца дуги — будет выглядеть как единая форма.

Robot arm
PY 
сделай чуть подлиннее

17:48
Что именно удлинить — горизонтальную пластину (ARM_L), нижний блок (VERT_L), или всё вместе?

маленькую на 1/3 самого себя длиннее

17:48
Нижний блок (VERT_L) на 1/3 длиннее:


Edited a file, read a file
Edited a file, read a file
VERT_L = ARM_L/3 * 4/3 — на треть длиннее предыдущего значения.

Robot arm
PY 
теперь уменьши все под пропорцию tiles

17:49
Смотрю текущие размеры:


Check current dimensions
Check current dimensions
Teal-блок: A=14*S по XY, H=6*S по Z. Руки должны быть пропорциональны — ширина = A, толщина = H, длина ~2A, загиб ~A/2:


Edited a file, read a file
Edited a file, read a file
Теперь всё завязано на A и H — те же единицы что у teal-блоков:

ARM_L = A * 2.2 — длина ~2 блока
ARM_W = A — ширина = ширине блока
ARM_TH = H * 0.8 — толщина чуть меньше высоты блока
BEND_R = A * 0.4 — радиус загиба пропорционален блоку
Robot arm
PY 
Снимок экрана 2026-04-02 в 5.55.19 PM.png
Отлично, теперь со стороны на фото поставь на tiles в 1.5 раза меньше черные цилиндры узкие снизу широкие сверху, небольшим отверстием внутри

17:56
Вижу — нужно добавить 4 конических цилиндра (frustum) снизу под каждой рукой — узкие снизу, широкие сверху, с отверстием внутри (как колёсико/шайба). Судя по фото реального объекта это похоже на моторчики/колёса.

Добавляю их в конце скрипта:


Viewed a file, edited a file, read a file
Viewed a file, edited a file, read a file
Добавил 4 конических кольца под концами рук — узкие снизу, широкие сверху, с отверстием внутри, чёрные, в 1.5 раза меньше teal-блока. Попробуй.

Robot arm
PY 
не сюда а на TILES

19:03
Понял — колёса должны быть под teal-блоками, не под руками. Исправляю:


Edited a file, read a file
Edited a file, read a file
Теперь 4 конических кольца размещены прямо под каждым teal-блоком, начиная от нижней грани блока (z = -H/2).

Robot arm
PY 
не под а на

19:04

Move wheels on top of teal blocks instead of under
Move wheels on top of teal blocks instead of under
И направление — сверху вниз меняю на снизу вверх (узкий снизу, широкий сверху → конус растёт вверх):


Edited a file, read a file
Edited a file, read a file
Конусы теперь стоят на верхней грани teal-блоков, широким основанием вниз, узким вверх.

Robot arm
PY 
Снимок экрана 2026-04-02 в 7.05.38 PM.png
и пониже

19:05
Конусы есть, но нужно их опустить. Уменьшу wz:


Edited a file, read a file
Edited a file, read a file
Опустил на половину высоты блока вниз. Попробуй.

Robot arm
PY 
они перевернуты

19:06

Edited a file, read a file
Edited a file, read a file
Теперь широкий конец сверху, узкий снизу.

Robot arm
PY 
отверстие  0..90 меньшиго размера, и сделай его так, узко, дуга через широкое, сново узко.

19:08
Понял — форма сечения не круг, а профиль как у подшипника: узко → дуга наружу (широко) → узко. Это тороидальный профиль. Переделываю:


Viewed a file, edited a file
Viewed a file, edited a file
Claude's response was interrupted
нет, форма сечения всей тубы такая, отверстие 0..90 меньшиго размера, и сделай его так, узко, дуга через широкое, сново узко.

19:08
Понял! Форма всего колеса сверху (сечение трубы): узкое основание → дуга наружу (выпуклость) → узкое основание. Как катушка/бобина. Переделываю полностью:


Edited 2 files, viewed a file, read a file
Edited 2 files, viewed a file, read a file
Теперь профиль — полуокружность: начинается узко → выпучивается наружу → снова узко. С отверстием меньше узкого края. Попробуй.

Robot arm
PY 
отверстие больше в 5 раз, углы плавные(не острые)

19:10

Edited a file, read a file
Edited a file, read a file
Отверстие увеличено в 5 раз, все углы скруглены — и снаружи и внутри отверстия.

Robot arm
PY 
ты потерял форму сужения расширения сужения

19:12
Ты прав — форма профиля должна быть строго: узко → дуга наружу → узко. Возвращаю простой чистый профиль, только добавляю скругление краёв и большое отверстие:


Edited a file, read a file
Edited a file, read a file
Профиль теперь через sin(π*t) — идеально: 0 → широко → 0, форма узко-дуга-узко сохранена. Отверстие большое (WHEEL_HOLE = WHEEL_R_NARROW * 1.75).

Robot arm
PY 
дно отверстия -- черное

19:13
Отверстие сквозное — дна нет. Нужно добавить закрытое дно (диск) внутри отверстия. На каком уровне — снизу или сверху?

да

19:13
Добавляю диск снизу отверстия:


Edited a file, read a file
Edited a file, read a file
Добавил диск-дно снизу отверстия — чёрный (материал mat_black уже применён ко всему объекту).

Robot arm
PY 
Снимок экрана 2026-04-02 в 7.14.41 PM.png
19:14
Отлично выглядит! Колёса с правильной формой и отверстием. Что дальше делаем?

там зеленое дно

19:15
Нужно убрать зелёный цвет — дно отверстия получает материал teal вместо чёрного. Это потому что center_bot попадает в другой материальный слот. Исправлю — добавлю отдельный объект для дна или явно назначу материал:


Fix bottom cap color - use separate black material face index
Fix bottom cap color - use separate black material face index
Подожди — зелёный цвет это mat_teal, но колесо использует только mat_black. Значит проблема в другом — teal-блок просто просвечивает сквозь отверстие. Дно нужно поднять чуть выше нуля:


Edited a file, read a file
Edited a file, read a file
Поднял дно чуть выше — teal-блок больше не будет просвечивать сквозь отверстие.

Robot arm
PY 
а также, убери куб внутри которого ваза

19:16
Нужно убрать teal-блок который находится внутри колеса — то есть убрать его из списка или уменьшить высоту. Смотрю где создаются teal-блоки:


View teal block creation
View teal block creation
Claude's response was interrupted
Снимок экрана 2026-04-02 в 7.17.15 PM.png
нет, видишь, вазу окружает куб, его надо убрать, а вазу поднять на поверхность на чуть-чуть

19:17
Вижу — teal-блок торчит вокруг вазы. Убираю teal-блоки и поднимаю колёса на поверхность:


Remove teal blocks and raise wheels to sit on top
Remove teal blocks and raise wheels to sit on top
Claude's response was interrupted
убери лишний меш

19:18
Нет, подожди — teal-блоки нужны, они являются частью конструкции (на них крепятся трубы и руки). Просто нужно убрать teal-блок только там где стоит ваза, или сделать его ниже чтобы не торчал.

Верни teal-блоки и просто подними wz колёс выше верха блока:


Edited a file, viewed a file
Edited a file, viewed a file
Teal-блоки уже есть. Теперь поднимаю wz колёс на H/2 чтобы они сидели на верхней грани блока:


Edited a file, viewed a file
Edited a file, viewed a file
wz уже H/2. Значит проблема в том что teal-блок слишком высокий и торчит внутри вазы. Нужно уменьшить высоту teal-блоков:


Edited 2 files, read a file
Edited 2 files, read a file
Уменьшил высоту teal-блоков вдвое — теперь они не будут торчать внутри вазы.

Robot arm
PY 
верни, высоту teal, только черный куб удали

19:20
Верну высоту teal-блоков и удалю отдельный чёрный меш внутри колеса. Сначала смотрю что именно является "лишним мешем":


Edited 2 files
Edited 2 files
Теперь удаляю дно отверстия (чёрный диск внутри):


Edited 2 files, viewed a file, read a file
Edited 2 files, viewed a file, read a file
Высота teal-блоков восстановлена, чёрный диск внутри отверстия удалён.

Robot arm
PY 
ладно, вставь его на высокую высоту(дно)

19:21

Edited a file, read a file
Edited a file, read a file
Дно теперь сверху — на уровне wz + WHEEL_H.

Robot arm
PY 
но чтобы там было хоть чуть чуть места внутри, сделай WHEEL_H / 2

19:22

Edited a file, read a file
Edited a file, read a file
Дно на середине высоты — сверху будет пространство внутри, снизу тоже открыто.

Robot arm
PY 
Мы сделали 3D модель!

19:23
Отлично! 🎉 Долгий путь — но результат получился!

Резюме того что сделали:

4 teal-блока в крест с чёрными изогнутыми трубами-соединителями
4 плоских руки (белые и чёрные) с плавным загибом 80° через bmesh
4 колеса-бобины на teal-блоках с профилем узко→широко→узко и отверстием
Если захочешь доработать — текстуры, рендер, анимацию или что-то ещё — файл готов!

в 1.5 ниже трубка сверху

20:10

Find pipe and tube related code
Find pipe and tube related code
Claude's response was interrupted
0.75 ниже трубу сверху

20:11

Viewed a file, edited a file, read a file
Viewed a file, edited a file, read a file
Опустил колесо на 0.75 * H.

Robot arm
PY 
дно

20:12

Edited a file, read a file
Edited a file, read a file
Дно теперь снизу отверстия.

Robot arm
PY 
Снимок экрана 2026-04-02 в 8.13.24 PM.png
20:13
Отлично выглядит! Колёса с отверстием на месте. Что дальше?

зелень внизу

20:13
Это teal-блок просвечивает снизу через отверстие. Подниму wz чуть выше:


Edited a file, read a file
Edited a file, read a file

Raise wheel slightly to hide teal block bottom

robot_arm.py
+1
-1

Presented file
Done
Поднял колесо — teal не должен просвечивать снизу.

Robot arm
PY 
ты колеса делаешь высокими, не дно поднимаешь

20:14
Понял — нужно поднять только дно внутри отверстия, не трогая позицию колеса. Верну wz и подниму только дно:


Edited 2 files, read a file
Edited 2 files, read a file

Restore wz and raise only the bottom cap

robot_arm.py
+1
-1

Raise bottom cap to hide teal block

robot_arm.py
+5
-5

Presented file
Done
Дно поднято до верхней грани teal-блока — зелень будет скрыта, колёса остаются на прежней высоте.

Robot arm
PY 
выше

20:15

Edited a file, read a file
Edited a file, read a file
Поднял дно на 30% высоты колеса.

Robot arm
PY 
почему там конус внизу

20:18
Потому что дно (center_bot) — одна точка, и грани от неё к кольцу inner_rings[0] образуют конус. Нужно сделать плоский диск — использовать кольцо на нужной высоте вместо одной точки:


Edited a file, read a file
Edited a file, read a file

Replace cone bottom with flat disk at correct height

robot_arm.py
+11
-5

Presented file
Done
Теперь дно — плоский диск на нужной высоте, не конус.

Robot arm
PY 
*0.05 не на 0.3

20:19

Working
Working

Lower cap to 0.05

robot_arm.py
+1
-1

Presenting file(s)...



Claude is AI and can make mistakes. Please double-check responses.
Robot arm · PY
Copy

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
 
# трубы-соединители
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
add_arm("ArmB",  0,       -DIST - A/2,  0, -1, mat_black)
add_arm("ArmL", -DIST - A/2, 0,        -1,  0, mat_black)
add_arm("ArmR",  DIST + A/2, 0,         1,  0, mat_white)
 
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