#!/usr/bin/env python3
"""
Язык Волн — клавиатурный шрифт
. → ∩ (арка)   _ → ∪ (чаша)   + → Ω (омега)   - → черта-разделитель
"""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

UPM  = 1000
ASC  = 700
DESC = -350
H    = 280   # высота арки
D    = 280   # глубина чаши
SW   = 52    # толщина штриха
EW   = 220   # ширина . и _
OHW  = 150   # ширина каждой из двух арок Ω
OGAP = 24    # зазор между арками Ω
OW   = OHW * 2 + OGAP + 40  # ширина + (с отступами)
SEP  = 80    # ширина черты -
K    = 1.12  # коэффициент безье

def arch(pen, x, w, h):
    ho = h + SW // 2
    hi = max(h - SW // 2, SW + 8)
    pen.moveTo((x, 0))
    pen.curveTo((x, ho * K), (x + w, ho * K), (x + w, 0))
    pen.lineTo((x + w - SW, 0))
    pen.curveTo((x + w - SW, hi * K), (x + SW, hi * K), (x + SW, 0))
    pen.lineTo((x, 0))
    pen.closePath()

def cup(pen, x, w, d):
    do_ = d + SW // 2
    di  = max(d - SW // 2, SW + 8)
    pen.moveTo((x, 0))
    pen.curveTo((x, -(do_ * K)), (x + w, -(do_ * K)), (x + w, 0))
    pen.lineTo((x + w - SW, 0))
    pen.curveTo((x + w - SW, -(di * K)), (x + SW, -(di * K)), (x + SW, 0))
    pen.lineTo((x, 0))
    pen.closePath()

def build():
    pad = 10  # боковой отступ внутри глифа

    glyphOrder = ['.notdef', 'space', 'period', 'underscore', 'plus', 'hyphen']
    charMap = {
        0x0020: 'space',
        0x002E: 'period',      # .
        0x005F: 'underscore',  # _
        0x002B: 'plus',        # +
        0x002D: 'hyphen',      # -
    }
    metrics = {
        '.notdef':   (300, 0),
        'space':     (220, 0),
        'period':    (EW + pad * 2, 0),
        'underscore':(EW + pad * 2, 0),
        'plus':      (OW + pad * 2, 0),
        'hyphen':    (SEP + pad * 2, 0),
    }

    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(glyphOrder)
    fb.setupCharacterMap(charMap)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
    fb.setupNameTable({'familyName': 'YazykVolnKeys', 'styleName': 'Regular'})
    fb.setupOS2(
        sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=0,
        usWinAscent=ASC, usWinDescent=abs(DESC), fsType=0, achVendID='VOLN',
    )
    fb.setupPost()
    fb.setupHead(unitsPerEm=UPM)

    charStrings = {}

    # .notdef
    p = T2CharStringPen(300, {})
    charStrings['.notdef'] = p.getCharString()

    # space
    p = T2CharStringPen(220, {})
    charStrings['space'] = p.getCharString()

    # period → ∩ арка над линией
    p = T2CharStringPen(EW + pad * 2, {})
    arch(p, pad, EW, H)
    charStrings['period'] = p.getCharString()

    # underscore → ∪ чаша под линией
    p = T2CharStringPen(EW + pad * 2, {})
    cup(p, pad, EW, D)
    charStrings['underscore'] = p.getCharString()

    # plus → Ω две арки
    p = T2CharStringPen(OW + pad * 2, {})
    arch(p, pad, OHW, H)
    arch(p, pad + OHW + OGAP, OHW, H)
    charStrings['plus'] = p.getCharString()

    # hyphen → черта-разделитель на линии
    p = T2CharStringPen(SEP + pad * 2, {})
    half = SW // 2
    p.moveTo((pad, -half))
    p.lineTo((pad + SEP, -half))
    p.lineTo((pad + SEP, half))
    p.lineTo((pad, half))
    p.closePath()
    charStrings['hyphen'] = p.getCharString()

    fb.setupCFF(
        psName='YazykVolnKeys-Regular',
        fontInfo={
            'version':    '1.000',
            'FullName':   'Yazyk Voln Keys Regular',
            'FamilyName': 'YazykVolnKeys',
            'Weight':     'Regular',
        },
        charStringsDict=charStrings,
        privateDict={'defaultWidthX': 0, 'nominalWidthX': 0},
    )

    out = '/workspaces/My-Projects/Язык Волн/font/YazykVolnKeys.otf'
    fb.font.save(out)
    print(f'Готово: {out}')

if __name__ == '__main__':
    build()
