from PIL import Image, ImageDraw, ImageFont

SQ = 92
BOARD = SQ * 8
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

LIGHT = (235, 219, 191)
DARK  = (176, 137, 104)
LINE  = (90, 66, 48)
WHITEP = (252, 250, 246)
BLACKP = (38, 34, 30)
OUT   = (28, 25, 22)

GLYPH = {'K':'\u265A','Q':'\u265B','R':'\u265C','B':'\u265D','N':'\u265E','P':'\u265F'}

f_piece = ImageFont.truetype(FONT, int(SQ*0.74))
f_coord = ImageFont.truetype(FONT_B, 28)
f_title = ImageFont.truetype(FONT_B, 44)


def draw_piece(d, cx, cy, color, ptype):
    g = GLYPH[ptype]
    fill = WHITEP if color == 'w' else BLACKP
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2):
            if dx*dx+dy*dy <= 5:
                d.text((cx+dx, cy+dy), g, font=f_piece, fill=OUT, anchor="mm")
    d.text((cx, cy), g, font=f_piece, fill=fill, anchor="mm")


def draw_board(d, ox, oy, pieces, col_labels, row_labels):
    for r in range(8):
        for c in range(8):
            x0 = ox + c*SQ; y0 = oy + r*SQ
            col = LIGHT if (r+c) % 2 == 0 else DARK
            d.rectangle([x0, y0, x0+SQ, y0+SQ], fill=col)
    d.rectangle([ox, oy, ox+BOARD, oy+BOARD], outline=LINE, width=4)
    for i in range(1, 8):
        d.line([ox+i*SQ, oy, ox+i*SQ, oy+BOARD], fill=LINE, width=1)
        d.line([ox, oy+i*SQ, ox+BOARD, oy+i*SQ], fill=LINE, width=1)
    for (cidx, ridx, color, ptype) in pieces:
        draw_piece(d, ox+cidx*SQ+SQ//2, oy+ridx*SQ+SQ//2, color, ptype)
    for c, lab in enumerate(col_labels):
        d.text((ox+c*SQ+SQ//2, oy+BOARD+28), lab, font=f_coord, fill=LINE, anchor="mm")
    for r, lab in enumerate(row_labels):
        d.text((ox-28, oy+r*SQ+SQ//2), lab, font=f_coord, fill=LINE, anchor="mm")


def C(letter): return "abcdefgh".index(letter)

# ===== Board 1 (his coords: rows 1..8 top->bottom, cols a..h) =====
p1 = [
    (C('e'),0,'b','N'),
    (C('e'),1,'b','P'), (C('f'),1,'b','Q'),
    (C('e'),2,'w','P'), (C('f'),2,'b','P'), (C('g'),2,'w','N'),
    (C('b'),3,'b','R'), (C('c'),3,'w','B'), (C('f'),3,'w','K'), (C('h'),3,'w','B'),
    (C('b'),4,'b','P'), (C('g'),4,'w','N'),
    (C('c'),5,'b','N'), (C('d'),5,'b','K'), (C('g'),5,'b','B'),
    (C('a'),6,'w','Q'), (C('b'),6,'b','P'), (C('c'),6,'b','B'), (C('d'),6,'b','P'),
]
p1_cols = list("abcdefgh")
p1_rows = list("12345678")

# ===== Board 2 (standard coords: cols a-h, ranks 8..1 top->bottom) =====
# helper: rank -> visual row idx
def RK(rank): return 8 - rank
p2 = [
    (C('b'),RK(8),'b','Q'), (C('d'),RK(8),'w','Q'),
    (C('e'),RK(6),'w','N'), (C('h'),RK(6),'w','R'),
    (C('b'),RK(5),'b','P'), (C('c'),RK(5),'w','B'), (C('f'),RK(5),'b','R'), (C('h'),RK(5),'w','B'),
    (C('a'),RK(4),'b','K'), (C('b'),RK(4),'b','P'), (C('h'),RK(4),'w','K'),
    (C('b'),RK(2),'b','R'), (C('d'),RK(2),'b','N'), (C('e'),RK(2),'b','N'),
    (C('b'),RK(1),'w','N'), (C('h'),RK(1),'w','B'),
]
p2_cols = list("abcdefgh")
p2_rows = list("87654321")

# ===== compose =====
M = 70
W = M + BOARD + M
H = M + 60 + BOARD + 110 + 60 + BOARD + M
img = Image.new("RGB", (W, H), (250, 247, 241))
d = ImageDraw.Draw(img)

y = M
d.text((M+30, y), "Задача 1", font=f_title, fill=(40,32,26))
y += 70
draw_board(d, M+34, y, p1, p1_cols, p1_rows)

y += BOARD + 110
d.text((M+30, y), "Задача 2", font=f_title, fill=(40,32,26))
y += 70
draw_board(d, M+34, y, p2, p2_cols, p2_rows)

img.save("/mnt/user-data/outputs/chess_boards.png")
print("saved", img.size)