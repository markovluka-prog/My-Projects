#!/usr/bin/env python3
# Генератор поля Vocabulary Race — КРУГОВАЯ трасса в стиле Формулы-1 (Монако/гавань).
# Замкнутая петля, дома стоят в воде, яхты, трибуны, пит-лейн, поребрики.
# Старт + 49 клеток (всего 50). Гонка: круг от старта (0) до финиша (49).
# Источник правды для assets/board.svg И для ROUTE/SPECIAL в index.html.
import math, random

W, H = 1000, 1500
N = 50

# ── анкеры замкнутого контура трассы (по часовой), сглаживаются Catmull-Rom ──
ANCHORS = [
  (225,1320),(470,1332),(760,1320),       # стартовая прямая (низ)
  (862,1245),(888,1075),(820,975),(890,815),(876,600),  # правая сторона + кинк
  (798,470),(688,442),(636,512),(520,470),              # шикана (S) сверху
  (360,452),(250,470),(162,562),(256,664),              # шпилька (hairpin) слева
  (322,820),(218,980),(304,1135),(180,1252),            # левая сторона вниз
]

def catmull_closed(pts, seg=46):
    n=len(pts); out=[]
    for i in range(n):
        p0,p1,p2,p3 = pts[(i-1)%n],pts[i],pts[(i+1)%n],pts[(i+2)%n]
        for t in range(seg):
            s=t/seg; s2=s*s; s3=s2*s
            x=0.5*(2*p1[0]+(-p0[0]+p2[0])*s+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*s2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*s3)
            y=0.5*(2*p1[1]+(-p0[1]+p2[1])*s+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*s2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*s3)
            out.append((x,y))
    out.append(out[0])
    return out

path = catmull_closed(ANCHORS)

# кумулятивная длина (замкнутая)
cum=[0.0]
for i in range(1,len(path)):
    cum.append(cum[-1]+math.hypot(path[i][0]-path[i-1][0], path[i][1]-path[i-1][1]))
total=cum[-1]

def at(s):
    s%=total
    lo,hi=0,len(cum)-1
    while lo<hi:
        m=(lo+hi)//2
        if cum[m]<s: lo=m+1
        else: hi=m
    i=max(1,lo); seg=cum[i]-cum[i-1]; f=0 if seg==0 else (s-cum[i-1])/seg
    return (path[i-1][0]+(path[i][0]-path[i-1][0])*f, path[i-1][1]+(path[i][1]-path[i-1][1])*f)

# 50 клеток равномерно по кругу (cell 49 рядом с cell 0 — это линия старт/финиш)
cells=[at(i*total/N) for i in range(N)]

ROUTE=[(round(x/W*100,2), round(y/H*100,2)) for (x,y) in cells]

# ── спецклетки: стрелки вперёд/назад ──
SPECIAL = {
  8:  {"type":"fwd",  "to":12, "n":4},
  17: {"type":"fwd",  "to":20, "n":3},
  26: {"type":"back", "to":22, "n":4},
  35: {"type":"fwd",  "to":39, "n":4},
  44: {"type":"back", "to":40, "n":4},
}
SP_STYLE = {
  "fwd":  ("#14331a", "#4caf50", "#7be08a"),
  "back": ("#331414", "#e0524a", "#ff9a92"),
}

def dist_to_track(px,py):
    return min(math.hypot(px-ax,py-ay) for ax,ay in path)

def inside_loop(px,py):
    # точка внутри замкнутого контура (ray casting) — это «гавань»
    c=False; n=len(path)
    for i in range(n-1):
        x1,y1=path[i]; x2,y2=path[i+1]
        if ((y1>py)!=(y2>py)) and (px < (x2-x1)*(py-y1)/(y2-y1)+x1): c=not c
    return c

def P(pts): return " ".join(f"{x:.1f},{y:.1f}" for x,y in pts)

# ═══════════════ декор ═══════════════
def building(x,baseY,w,h,wall,roof=None,s=1.0):
    g=[f'<g transform="translate({x:.0f},{baseY:.0f}) scale({s})">']
    # тень на земле
    g.append(f'<ellipse cx="0" cy="3" rx="{w*0.6:.0f}" ry="5" fill="#000000" opacity="0.18"/>')
    g.append(f'<rect x="{-w/2:.0f}" y="{-h:.0f}" width="{w:.0f}" height="{h:.0f}" rx="2" fill="{wall}"/>')
    # окна
    cols=max(1,int(w//14)); rows=max(1,int(h//18))
    for r in range(rows):
        for c in range(cols):
            wx=-w/2+7+c*(w/cols); wy=-h+10+r*(h/rows)
            lit='#ffe89a' if random.random()<0.5 else '#9fc6e8'
            g.append(f'<rect x="{wx:.0f}" y="{wy:.0f}" width="6" height="8" fill="{lit}" opacity="0.9"/>')
    if roof:
        g.append(f'<path d="M{-w/2-3:.0f},{-h:.0f} L0,{-h-w*0.45:.0f} L{w/2+3:.0f},{-h:.0f} Z" fill="{roof}"/>')
    g.append('</g>')
    return "".join(g)

def yacht(x,y,s=1.0):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s})">'
            '<ellipse cx="0" cy="20" rx="60" ry="7" fill="#ffffff" opacity="0.35"/>'
            '<path d="M-52,2 L52,2 L40,20 L-40,20 Z" fill="#f4f4f4"/>'
            '<rect x="-30" y="-14" width="56" height="18" rx="3" fill="#dfe6ee"/>'
            '<rect x="-26" y="-10" width="10" height="9" fill="#7fb8e0"/>'
            '<rect x="-10" y="-10" width="10" height="9" fill="#7fb8e0"/>'
            '<rect x="6" y="-10" width="10" height="9" fill="#7fb8e0"/>'
            '<rect x="-3" y="-40" width="3" height="26" fill="#888"/>'
            '<path d="M2,-40 L24,-16 L2,-16 Z" fill="#e9534a"/></g>')

def grandstand(x,y,w,h):
    g=[f'<g transform="translate({x:.0f},{y:.0f})">']
    g.append(f'<path d="{-w/2},{0} L{w/2},0 L{w/2-8},{-h} L{-w/2+8},{-h} Z" fill="#cfd6df"/>')
    cols=int(w//12)
    for r in range(int(h//12)):
        for c in range(cols):
            cx=-w/2+12+c*((w-24)/max(1,cols-1)); cy=-6-r*12
            col=random.choice(['#e9534a','#ffd24a','#37a0d6','#4caf50','#ffffff','#c77dff'])
            g.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="2.6" fill="{col}"/>')
    g.append(f'<rect x="{-w/2-2}" y="{-h-8}" width="{w+4}" height="8" rx="2" fill="#e9534a"/>')
    g.append('</g>')
    return "".join(g)

def palm(x,y,s=1.0,flip=1):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s*flip},{s})">'
            '<ellipse cx="0" cy="4" rx="18" ry="5" fill="#00000022"/>'
            '<path d="M-4,2 Q-9,-24 -2,-52 L4,-52 Q-2,-24 5,2 Z" fill="#9c6b35"/>'
            '<path d="M0,-52 Q-30,-68 -60,-58 Q-32,-52 0,-47 Z" fill="#2f9d44"/>'
            '<path d="M0,-52 Q30,-68 60,-58 Q32,-52 0,-47 Z" fill="#2f9d44"/>'
            '<path d="M0,-52 Q-22,-84 -46,-90 Q-20,-68 0,-49 Z" fill="#38b552"/>'
            '<path d="M0,-52 Q22,-84 46,-90 Q20,-68 0,-49 Z" fill="#38b552"/>'
            '<path d="M0,-52 Q-5,-90 2,-100 Q7,-80 6,-52 Z" fill="#2f9d44"/>'
            '<circle cx="0" cy="-52" r="5" fill="#7a4a1f"/></g>')

def cone(x,y):
    return (f'<g transform="translate({x:.0f},{y:.0f})"><path d="M-6,7 L0,-11 L6,7 Z" fill="#ff7a1a"/>'
            '<rect x="-4" y="-1" width="8" height="3" fill="#fff"/></g>')

def flag(x,y,c):
    return (f'<g transform="translate({x:.0f},{y:.0f})"><rect x="-1" y="-30" width="2.5" height="30" fill="#888"/>'
            f'<path d="M1,-30 L18,-25 L1,-20 Z" fill="{c}"/></g>')

def cloud(x,y,s=1.0):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s})" fill="#ffffff" opacity="0.9">'
            '<ellipse cx="0" cy="0" rx="32" ry="18"/><ellipse cx="-26" cy="6" rx="22" ry="13"/>'
            '<ellipse cx="26" cy="6" rx="24" ry="14"/></g>')

def bird(x,y,s=1.0):
    return (f'<path d="M{x-9*s:.0f},{y:.0f} Q{x-3*s:.0f},{y-7*s:.0f} {x:.0f},{y:.0f} '
            f'Q{x+3*s:.0f},{y-7*s:.0f} {x+9*s:.0f},{y:.0f}" stroke="#3a4a5a" stroke-width="2.5" '
            f'fill="none" stroke-linecap="round" opacity="0.7"/>')

WALLS=['#f3e4c4','#efd9b0','#dfe7ee','#e8cfa6','#cdd7e0','#f6ead2']
ROOFS=['#c5562f','#b8472a','#cf6638',None,None]

# ═══════════════ SVG ═══════════════
random.seed(5)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append('<defs>'
  '<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">'
  '<stop offset="0" stop-color="#5fb4e0"/><stop offset="0.5" stop-color="#2f8fce"/><stop offset="1" stop-color="#1f6fb0"/></linearGradient>'
  '<linearGradient id="asph" x1="0" y1="0" x2="0" y2="1">'
  '<stop offset="0" stop-color="#5a5f6b"/><stop offset="1" stop-color="#3a3e47"/></linearGradient>'
  '<radialGradient id="sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff3b0"/><stop offset="1" stop-color="#ffd24a"/></radialGradient>'
  '<linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">'
  '<stop offset="0" stop-color="#7cc45a"/><stop offset="1" stop-color="#4e9e3e"/></linearGradient>'
  '<linearGradient id="sand" x1="0" y1="0" x2="0" y2="1">'
  '<stop offset="0" stop-color="#f3e2b3"/><stop offset="1" stop-color="#e6cf94"/></linearGradient>'
  '<pattern id="check" width="36" height="36" patternUnits="userSpaceOnUse">'
  '<rect width="36" height="36" fill="#fff"/><rect width="18" height="18" fill="#111"/><rect x="18" y="18" width="18" height="18" fill="#111"/></pattern>'
  '<filter id="soft"><feGaussianBlur stdDeviation="6"/></filter></defs>')

# море
svg.append(f'<rect width="{W}" height="{H}" fill="url(#sea)"/>')
# рябь
for _ in range(70):
    wx=random.uniform(20,980); wy=random.uniform(20,1480)
    svg.append(f'<path d="M{wx:.0f},{wy:.0f} q7,-5 14,0 q7,5 14,0" stroke="#ffffff" stroke-width="2.5" fill="none" opacity="0.28" stroke-linecap="round"/>')
# ── ЗЕМЛЯ: остров-кольцо вдоль трассы (песок → трава) ──
pp_land=P(path)
# песчаная кайма (шире) — пляжи у воды
svg.append(f'<polyline points="{pp_land}" fill="none" stroke="#ede0b8" stroke-width="330" stroke-linecap="round" stroke-linejoin="round" filter="url(#soft)"/>')
svg.append(f'<polyline points="{pp_land}" fill="none" stroke="url(#sand)" stroke-width="300" stroke-linecap="round" stroke-linejoin="round"/>')
# трава (уже песка) — основная суша
svg.append(f'<polyline points="{pp_land}" fill="none" stroke="url(#grass)" stroke-width="240" stroke-linecap="round" stroke-linejoin="round"/>')
# крапинки травы (тёмная зелень) для текстуры
random.seed(31)
for _ in range(140):
    gx=random.uniform(40,960); gy=random.uniform(360,1460)
    if 30<dist_to_track(gx,gy)<118:
        r=random.uniform(4,11)
        svg.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{r:.0f}" fill="#3f8b34" opacity="0.5"/>')

# солнце
svg.append('<g><circle cx="140" cy="135" r="78" fill="#ffe98a" opacity="0.3" filter="url(#soft)"/>')
for k in range(12):
    a=math.radians(k*30)
    svg.append(f'<line x1="{140+56*math.cos(a):.0f}" y1="{135+56*math.sin(a):.0f}" x2="{140+80*math.cos(a):.0f}" y2="{135+80*math.sin(a):.0f}" stroke="#ffe07a" stroke-width="6" stroke-linecap="round"/>')
svg.append('<circle cx="140" cy="135" r="48" fill="url(#sun)"/></g>')
svg.append(cloud(430,90,0.9)+cloud(660,140,0.75)+cloud(840,80,0.8))
for bx,by in [(360,200),(520,150),(690,230),(800,180),(300,120)]:
    svg.append(bird(bx,by,1.1))

# дома НА ЗЕМЛЕ — вдоль трассы, на травяном кольце (внутри и снаружи)
random.seed(9)
houses=[]
for _ in range(900):
    x=random.uniform(60,940); y=random.uniform(360,1460)
    # на суше: близко к трассе (трава простирается до ~118)
    if 66<dist_to_track(x,y)<112:
        if all(math.hypot(x-hx,y-hy)>120 for hx,hy in houses):
            houses.append((x,y))
for hx,hy in sorted(houses,key=lambda p:p[1]):
    w=random.uniform(22,36); h=random.uniform(34,62)
    svg.append(building(hx,hy,w,h,random.choice(WALLS),random.choice(ROOFS)))
# яхты в открытой воде центра гавани
for yx,yy,ys in [(430,820,0.9),(560,880,1.0),(470,990,0.85),(610,1050,0.8),(520,740,0.75)]:
    if inside_loop(yx,yy) and dist_to_track(yx,yy)>150:
        svg.append(yacht(yx,yy,ys))

# пальмы вдоль трассы (на траве, у самой кромки дороги)
random.seed(21); pc=0
for _ in range(400):
    if pc>=22: break
    x=random.uniform(60,940); y=random.uniform(380,1440)
    if 58<dist_to_track(x,y)<74:
        if all(math.hypot(x-px,y-py)>70 for px,py in [(h[0],h[1]) for h in houses]):
            svg.append(palm(x,y,random.uniform(0.6,0.9),random.choice([1,-1]))); pc+=1

# ═══════════════ ТРАССА (замкнутый круг) ═══════════════
pp=P(path)
svg.append(f'<polyline points="{pp}" fill="none" stroke="#000" stroke-width="130" stroke-linecap="round" stroke-linejoin="round" opacity="0.30" filter="url(#soft)"/>')
# шины-барьеры красно-белые (внешняя кромка)
svg.append(f'<polyline points="{pp}" fill="none" stroke="#d23b2c" stroke-width="120" stroke-linecap="round" stroke-linejoin="round"/>')
svg.append(f'<polyline points="{pp}" fill="none" stroke="#ffffff" stroke-width="120" stroke-dasharray="26 26" stroke-linecap="butt" stroke-linejoin="round"/>')
# асфальт
svg.append(f'<polyline points="{pp}" fill="none" stroke="url(#asph)" stroke-width="104" stroke-linecap="round" stroke-linejoin="round"/>')
# осевая разметка
svg.append(f'<polyline points="{pp}" fill="none" stroke="#f5d34a" stroke-width="5" stroke-dasharray="24 28" stroke-linecap="round" opacity="0.75"/>')

# трибуны вдоль стартовой прямой (снаружи, у низа)
svg.append(grandstand(360,1438,240,52)+grandstand(640,1440,200,48))
# флажки на поребриках поворотов
for fi in (10,15,30,42):
    fx,fy=cells[fi]; svg.append(flag(fx, fy-44, random.choice(['#e9534a','#ffd24a','#37a0d6'])))

# Клетки/стрелки/старт/финиш рисует НЕ здесь, а слой #cells-layer в index.html
# (фон-иллюстрация отдельно, разметка поверх). Здесь только фон-арт трассы.
svg.append('</svg>')
open('assets/board.svg','w').write("\n".join(svg))

# ── вывод для index.html ──
print("ROUTE length:", len(ROUTE), " self-intersect check skipped")
print("const ROUTE = [")
for i in range(0,len(ROUTE),6):
    print("  "+",".join(f"[{a},{b}]" for a,b in ROUTE[i:i+6])+",")
print("];\n")
print("const SPECIAL = {")
for i,sp in SPECIAL.items():
    print(f"  {i}: {{ type:'{sp['type']}', to:{sp['to']}, n:{sp['n']} }},")
print("};")
