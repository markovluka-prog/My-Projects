import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect('equal')
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.axis('off')
fig.patch.set_facecolor('#ececec')

TEAL      = '#2a9d8f'
TEAL_DARK = '#1b6b62'
BLACK     = '#111111'
CREAM     = '#ddd5b8'
CREAM_DK  = '#a09070'
DARK_GRAY = '#333333'

# Пропорции (1 unit ≈ ~1cm)
BW   = 2.0    # размер бирюзового блока
GAP  = 0.28   # зазор между блоками
h    = BW/2 + GAP/2   # смещение центров блоков от центра кластера

AW   = 0.55   # ширина рычага
LONG = 3.8    # длинное плечо (вдоль кластера)
SHORT = 5.5   # короткое плечо (наружу)
CONN_LW = 10  # толщина Г-коннектора

# Центры блоков
B = [(-h, h), (h, h), (-h, -h), (h, -h)]

# ─────────────────────────────────────────────
# Вспомогательная функция: рисует Г-рычаг
# corner_x, corner_y — угол Г (точка сгиба, = позиция шара)
# dir_long  — направление длинного плеча от угла: (dx, dy)
# dir_short — направление короткого плеча от угла: (dx, dy)
# ─────────────────────────────────────────────
def draw_L_arm(ax, cx, cy, dir_long, dir_short, color, edge, zorder=4):
    lx = cx + dir_long[0] * LONG
    ly = cy + dir_long[1] * LONG
    sx = cx + dir_short[0] * SHORT
    sy = cy + dir_short[1] * SHORT

    hw = AW / 2

    # Нормали к плечам
    def norm(dx, dy): return (-dy, dx)

    nl = norm(*dir_long)
    ns = norm(*dir_short)

    # Длинное плечо: прямоугольник от угла (cx,cy) до (lx,ly)
    pts_long = [
        (cx + nl[0]*hw, cy + nl[1]*hw),
        (lx + nl[0]*hw, ly + nl[1]*hw),
        (lx - nl[0]*hw, ly - nl[1]*hw),
        (cx - nl[0]*hw, cy - nl[1]*hw),
    ]
    ax.add_patch(plt.Polygon(pts_long, closed=True,
                              facecolor=color, edgecolor=edge,
                              linewidth=1.2, zorder=zorder,
                              joinstyle='round', capstyle='round'))

    # Короткое плечо: прямоугольник от угла (cx,cy) до (sx,sy)
    pts_short = [
        (cx + ns[0]*hw, cy + ns[1]*hw),
        (sx + ns[0]*hw, sy + ns[1]*hw),
        (sx - ns[0]*hw, sy - ns[1]*hw),
        (cx - ns[0]*hw, cy - ns[1]*hw),
    ]
    ax.add_patch(plt.Polygon(pts_short, closed=True,
                              facecolor=color, edgecolor=edge,
                              linewidth=1.2, zorder=zorder,
                              joinstyle='round', capstyle='round'))

    # Скруглённый угол
    ax.add_patch(plt.Circle((cx, cy), hw*1.05,
                              color=color, zorder=zorder+1))

# ─────────────────────────────────────────────
# 1. РЫЧАГИ (под блоками, zorder=4)
# ─────────────────────────────────────────────
# Черный рычаг ВВЕРХ — угол на верхнем ЛЕВОМ блоке
# Длинное плечо → вправо (вдоль верха кластера)
# Короткое плечо → вверх (рука/нога)
draw_L_arm(ax, -h, h,
           dir_long=(1, 0), dir_short=(0, 1),
           color=BLACK, edge=DARK_GRAY)

# Черный рычаг ВНИЗ — угол на нижнем ПРАВОМ блоке
# Длинное плечо → влево
# Короткое плечо → вниз
draw_L_arm(ax, h, -h,
           dir_long=(-1, 0), dir_short=(0, -1),
           color=BLACK, edge=DARK_GRAY)

# Белый рычаг ВЛЕВО — угол на верхнем ПРАВОМ блоке
# Длинное плечо → вниз (вдоль правой стороны кластера)
# Короткое плечо → влево (рука/нога)
draw_L_arm(ax, h, h,
           dir_long=(0, -1), dir_short=(-1, 0),
           color=CREAM, edge=CREAM_DK)

# Белый рычаг ВПРАВО — угол на нижнем ЛЕВОМ блоке
# Длинное плечо → вверх
# Короткое плечо → вправо
draw_L_arm(ax, -h, -h,
           dir_long=(0, 1), dir_short=(1, 0),
           color=CREAM, edge=CREAM_DK)

# ─────────────────────────────────────────────
# 2. Г-КОННЕКТОРЫ (4 дуги, zorder=5)
# ─────────────────────────────────────────────
r_in  = (h + BW/2) * 0.92
r_out = (h + BW/2) * 1.38

for a0, a1 in [(90, 180), (0, 90), (180, 270), (270, 360)]:
    theta = np.linspace(np.radians(a0), np.radians(a1), 60)
    xo = r_out * np.cos(theta)
    yo = r_out * np.sin(theta)
    xi = r_in  * np.cos(theta[::-1])
    yi = r_in  * np.sin(theta[::-1])
    xs = np.concatenate([xo, xi])
    ys = np.concatenate([yo, yi])
    ax.add_patch(plt.Polygon(list(zip(xs, ys)), closed=True,
                              facecolor=BLACK, edgecolor='#222',
                              linewidth=0.5, zorder=5))

# ─────────────────────────────────────────────
# 3. БИРЮЗОВЫЕ БЛОКИ (zorder=6)
# ─────────────────────────────────────────────
for bx, by in B:
    ax.add_patch(patches.FancyBboxPatch(
        (bx - BW/2, by - BW/2), BW, BW,
        boxstyle="round,pad=0.15",
        facecolor=TEAL, edgecolor=TEAL_DARK,
        linewidth=2, zorder=6))
    # отверстия 2×2
    for di in [-0.45, 0.45]:
        for dj in [-0.45, 0.45]:
            ax.add_patch(plt.Circle((bx+di, by+dj), 0.2,
                                     color=TEAL_DARK, zorder=7))
            ax.add_patch(plt.Circle((bx+di, by+dj), 0.11,
                                     color='#0e3d38', zorder=8))

# ─────────────────────────────────────────────
# 4. ШАРЫ (zorder=9)
# ─────────────────────────────────────────────
for bx, by in B:
    ax.add_patch(plt.Circle((bx, by), 0.42, color=BLACK, zorder=9))
    ax.add_patch(plt.Circle((bx - 0.12, by + 0.12), 0.14,
                              color='#555', zorder=10))

# ─────────────────────────────────────────────
# 5. РАЗМЕРНЫЕ ЛИНИИ
# ─────────────────────────────────────────────
arr = dict(arrowstyle='<->', color='#777', lw=1.2, mutation_scale=11)
tk = dict(fontsize=9, color='#444', ha='center', va='center',
          fontfamily='monospace',
          bbox=dict(fc='#ececec', ec='none', pad=1.5))

# Полный размах
tip = h + SHORT
ax.annotate('', xy=(tip + 0.3, -8.8), xytext=(-tip - 0.3, -8.8),
            arrowprops=arr)
ax.text(0, -9.4, '17.5 см', **tk)

# Кластер
cl = h + BW/2
ax.annotate('', xy=(cl, -7.2), xytext=(-cl, -7.2),
            arrowprops=arr)
ax.text(0, -7.75, '~4.5 см', **tk)

# Короткое плечо (вверх)
tip_y = h + SHORT
ax.annotate('', xy=(cl + 1.0, tip_y), xytext=(cl + 1.0, h),
            arrowprops=arr)
ax.text(cl + 2.5, h + SHORT/2, '~3.5 см\n(рука)', **tk)

# ─────────────────────────────────────────────
# 6. ЗАГОЛОВОК И ЛЕГЕНДА
# ─────────────────────────────────────────────
ax.set_title('Звезда Луки — вид сверху, базовая позиция',
             fontsize=13, fontweight='bold', color='#222', pad=14)

lx, ly = -9.5, 9.2
for i, (col, txt) in enumerate([
    (TEAL,     'бирюзовый блок  (x4)'),
    ('#777',   'шар-шарнир      (x4)'),
    (BLACK,    'Г-коннектор     (x4)'),
    (BLACK,    'рычаг черный  вверх/вниз (x2)'),
    (CREAM_DK, 'рычаг белый  влево/вправо (x2)'),
]):
    ax.text(lx, ly - i*0.85, '■ ' + txt, fontsize=7.8,
            color=col, va='center', fontfamily='monospace')

out = "/Users/lukamarkov/Library/Mobile Documents/com~apple~CloudDocs/My projects/Звезда Луки/zvezda_luki.png"
plt.tight_layout()
plt.savefig(out, dpi=160, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("OK:", out)
