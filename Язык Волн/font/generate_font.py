#!/usr/bin/env python3
"""
Генератор шрифта — Язык Волн
Русская буква/цифра → волновой символ (∩, ∪, Ω)
Заглавные = те же символы, но выше на UPPER_SHIFT единиц
"""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

UPM         = 1000
ASC         = 800
DESC        = -350
H           = 260
D           = 260
SW          = 52
EW          = 200
OHW         = 160
OGAP        = 20
OW          = OHW * 2 + OGAP
PAD         = 30
K           = 1.12
UPPER_SHIFT = 180   # насколько выше заглавные

ALPHABET = {
    'а': '._.',   'б': '._..', 'в': '._._.', 'г': '._...', 'д': '.__',
    'е': '.._',   'ё': '..__', 'ж': '._._',  'з': '.__.', 'и': '.._.',
    'й': '__.',   'к': '__..', 'л': '+.',     'м': '+..',  'н': '+...',
    'о': '+_.',   'п': '+._',  'р': '+__',    'с': '_+_',  'т': '++',
    'у': '.+_',   'ф': '.+.',  'х': '..+',   'ц': '.+',   'ч': '_+',
    'ш': '_+.',   'щ': '_+..', 'ъ': '+_+',   'ы': '+.+',  'ь': '_.+',
    'э': '+..+',  'ю': '+++',  'я': '___',
}

DIGITS = {
    '1': '.',    '2': '..',   '3': '...',  '4': '_.',   '5': '_..',
    '6': '_...', '7': '__',   '8': '_._',  '9': '_.._', '0': '_..._',
}

# строчные
LOWER_MAP = {
    'uni0430': (0x0430, 'а'), 'uni0431': (0x0431, 'б'), 'uni0432': (0x0432, 'в'),
    'uni0433': (0x0433, 'г'), 'uni0434': (0x0434, 'д'), 'uni0435': (0x0435, 'е'),
    'uni0451': (0x0451, 'ё'), 'uni0436': (0x0436, 'ж'), 'uni0437': (0x0437, 'з'),
    'uni0438': (0x0438, 'и'), 'uni0439': (0x0439, 'й'), 'uni043A': (0x043A, 'к'),
    'uni043B': (0x043B, 'л'), 'uni043C': (0x043C, 'м'), 'uni043D': (0x043D, 'н'),
    'uni043E': (0x043E, 'о'), 'uni043F': (0x043F, 'п'), 'uni0440': (0x0440, 'р'),
    'uni0441': (0x0441, 'с'), 'uni0442': (0x0442, 'т'), 'uni0443': (0x0443, 'у'),
    'uni0444': (0x0444, 'ф'), 'uni0445': (0x0445, 'х'), 'uni0446': (0x0446, 'ц'),
    'uni0447': (0x0447, 'ч'), 'uni0448': (0x0448, 'ш'), 'uni0449': (0x0449, 'щ'),
    'uni044A': (0x044A, 'ъ'), 'uni044B': (0x044B, 'ы'), 'uni044C': (0x044C, 'ь'),
    'uni044D': (0x044D, 'э'), 'uni044E': (0x044E, 'ю'), 'uni044F': (0x044F, 'я'),
}

# заглавные → тот же код буквы что и строчная
UPPER_MAP = {
    'uni0410': (0x0410, 'а'), 'uni0411': (0x0411, 'б'), 'uni0412': (0x0412, 'в'),
    'uni0413': (0x0413, 'г'), 'uni0414': (0x0414, 'д'), 'uni0415': (0x0415, 'е'),
    'uni0401': (0x0401, 'ё'), 'uni0416': (0x0416, 'ж'), 'uni0417': (0x0417, 'з'),
    'uni0418': (0x0418, 'и'), 'uni0419': (0x0419, 'й'), 'uni041A': (0x041A, 'к'),
    'uni041B': (0x041B, 'л'), 'uni041C': (0x041C, 'м'), 'uni041D': (0x041D, 'н'),
    'uni041E': (0x041E, 'о'), 'uni041F': (0x041F, 'п'), 'uni0420': (0x0420, 'р'),
    'uni0421': (0x0421, 'с'), 'uni0422': (0x0422, 'т'), 'uni0423': (0x0423, 'у'),
    'uni0424': (0x0424, 'ф'), 'uni0425': (0x0425, 'х'), 'uni0426': (0x0426, 'ц'),
    'uni0427': (0x0427, 'ч'), 'uni0428': (0x0428, 'ш'), 'uni0429': (0x0429, 'щ'),
    'uni042A': (0x042A, 'ъ'), 'uni042B': (0x042B, 'ы'), 'uni042C': (0x042C, 'ь'),
    'uni042D': (0x042D, 'э'), 'uni042E': (0x042E, 'ю'), 'uni042F': (0x042F, 'я'),
}

DIGIT_MAP = {
    'zero':  (0x0030, '0'), 'one':   (0x0031, '1'), 'two':   (0x0032, '2'),
    'three': (0x0033, '3'), 'four':  (0x0034, '4'), 'five':  (0x0035, '5'),
    'six':   (0x0036, '6'), 'seven': (0x0037, '7'), 'eight': (0x0038, '8'),
    'nine':  (0x0039, '9'),
}

ALL_CODES = {**ALPHABET, **DIGITS}

def elem_w(ch):
    return OW if ch == '+' else EW

def glyph_advance(code):
    return PAD * 2 + sum(elem_w(c) for c in code)

# ── Рисование форм с y_off ──────────────────────────────────────────────────
def draw_arch(pen, x, w, h, y_off=0):
    ho = h + SW // 2
    hi = max(h - SW // 2, SW + 10)
    pen.moveTo((x, y_off))
    pen.curveTo((x, y_off + ho * K), (x + w, y_off + ho * K), (x + w, y_off))
    pen.lineTo((x + w - SW, y_off))
    pen.curveTo((x + w - SW, y_off + hi * K), (x + SW, y_off + hi * K), (x + SW, y_off))
    pen.lineTo((x, y_off))
    pen.closePath()

def draw_cup(pen, x, w, d, y_off=0):
    do_ = d + SW // 2
    di  = max(d - SW // 2, SW + 10)
    pen.moveTo((x, y_off))
    pen.curveTo((x, y_off - do_ * K), (x + w, y_off - do_ * K), (x + w, y_off))
    pen.lineTo((x + w - SW, y_off))
    pen.curveTo((x + w - SW, y_off - di * K), (x + SW, y_off - di * K), (x + SW, y_off))
    pen.lineTo((x, y_off))
    pen.closePath()

def draw_glyph(pen, code, y_off=0):
    x = PAD
    for ch in code:
        if ch == '.':
            draw_arch(pen, x, EW, H, y_off)
            x += EW
        elif ch == '_':
            draw_cup(pen, x, EW, D, y_off)
            x += EW
        elif ch == '+':
            draw_arch(pen, x, OHW, H, y_off)
            draw_arch(pen, x + OHW + OGAP, OHW, H, y_off)
            x += OW

# ── Сборка ──────────────────────────────────────────────────────────────────
def build():
    ALL_GLYPH_MAP = {**LOWER_MAP, **UPPER_MAP, **DIGIT_MAP}

    glyph_names = ['.notdef', 'space', 'hyphen'] + list(ALL_GLYPH_MAP.keys())
    char_map = {
        0x0020: 'space',
        0x002D: 'hyphen',
        **{cp: name for name, (cp, _) in ALL_GLYPH_MAP.items()}
    }

    def adv(name):
        _, char = ALL_GLYPH_MAP[name]
        code = ALL_CODES.get(char, '')
        return glyph_advance(code) if code else 500

    metrics = {
        '.notdef': (500, 0),
        'space':   (260, 0),
        'hyphen':  (120, 0),
        **{name: (adv(name), 0) for name in ALL_GLYPH_MAP}
    }

    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(char_map)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
    fb.setupNameTable({'familyName': 'YazykVoln', 'styleName': 'Regular'})
    fb.setupOS2(
        sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=0,
        usWinAscent=ASC, usWinDescent=abs(DESC),
        fsType=0, achVendID='VOLN',
    )
    fb.setupPost()
    fb.setupHead(unitsPerEm=UPM)

    charStrings = {}

    # .notdef
    p = T2CharStringPen(500, {})
    charStrings['.notdef'] = p.getCharString()

    # space
    p = T2CharStringPen(260, {})
    charStrings['space'] = p.getCharString()

    # hyphen — тонкая черта с закруглёнными концами
    hw = 60   # ширина черты
    hh = 18   # полувысота
    hpad = 30
    r = hh    # радиус закругления = полувысота (капсула)
    c = r * 0.552
    p = T2CharStringPen(120, {})
    p.moveTo((hpad + r, -hh))
    p.lineTo((hpad + hw - r, -hh))
    p.curveTo((hpad + hw - r + c, -hh), (hpad + hw, -hh + c), (hpad + hw, 0))
    p.curveTo((hpad + hw, hh - c), (hpad + hw - r + c, hh), (hpad + hw - r, hh))
    p.lineTo((hpad + r, hh))
    p.curveTo((hpad + r - c, hh), (hpad, hh - c), (hpad, 0))
    p.curveTo((hpad, -hh + c), (hpad + r - c, -hh), (hpad + r, -hh))
    p.closePath()
    charStrings['hyphen'] = p.getCharString()

    # строчные
    for name, (_, char) in LOWER_MAP.items():
        code = ALL_CODES.get(char, '')
        p = T2CharStringPen(metrics[name][0], {})
        if code:
            draw_glyph(p, code, y_off=0)
        charStrings[name] = p.getCharString()

    # заглавные — те же коды, y_off = UPPER_SHIFT
    for name, (_, char) in UPPER_MAP.items():
        code = ALL_CODES.get(char, '')
        p = T2CharStringPen(metrics[name][0], {})
        if code:
            draw_glyph(p, code, y_off=UPPER_SHIFT)
        charStrings[name] = p.getCharString()

    # цифры
    for name, (_, char) in DIGIT_MAP.items():
        code = ALL_CODES.get(char, '')
        p = T2CharStringPen(metrics[name][0], {})
        if code:
            draw_glyph(p, code, y_off=0)
        charStrings[name] = p.getCharString()

    fb.setupCFF(
        psName='YazykVoln-Regular',
        fontInfo={'version': '1.000', 'FullName': 'Yazyk Voln Regular',
                  'FamilyName': 'YazykVoln', 'Weight': 'Regular'},
        charStringsDict=charStrings,
        privateDict={'defaultWidthX': 0, 'nominalWidthX': 0},
    )

    out = '/workspaces/My-Projects/Язык Волн/font/YazykVoln.otf'
    fb.font.save(out)
    print(f'Готово: {out}')

if __name__ == '__main__':
    build()
