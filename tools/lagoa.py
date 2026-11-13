"""Lagoa design system primitives for the README header and the LinkedIn banner.

Tokens, fonts and mascot come from the Lagoa design system. Everything here draws
flat SVG: a sky gradient, layered hills, trees, a pond, the mascot and text with
subsetted fonts embedded, so the images render the same on GitHub and LinkedIn.
"""

import base64
import io
import math
import random
import re
import tomllib
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
FONTS = TOOLS / "fonts"
MASCOT = TOOLS / "mascot"


def load_profile():
    with open(ROOT / "profile.toml", "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------- tokens

THEMES = {
    "light": dict(
        paper="#f4f0e4", raised="#fbf9f2", ink="#1f3329", muted="#56685c", rule="rgba(31,51,41,0.16)",
        pink="#e9788f", available="#5f9b6e", sky_top="#b9d8cf", sky_bottom="#e6eedc", sun="#f6e7b8",
        hill_far="#b7cfb0", hill_mid="#8fb491", hill_near="#6f9a76", tree="#3f6b52", tree_dark="#2c5240",
        trunk="#6b4f3a", water="#9fcfca", water_hi="#d6ece7", grass="#4f7d5b", flower="#fbf8ef",
        grain=0.10, blend="multiply", shadow="rgba(20,40,30,0.12)", ghost="rgba(31,51,41,0.07)",
    ),
    "dark": dict(
        paper="#13231d", raised="#1a2d25", ink="#e7eedf", muted="#a6b6a8", rule="rgba(231,238,223,0.14)",
        pink="#f29aac", available="#7fbf8e", sky_top="#0d2226", sky_bottom="#1b3a35", sun="#e9efd9",
        hill_far="#24443d", hill_mid="#1c3a31", hill_near="#163027", tree="#12291f", tree_dark="#0d2018",
        trunk="#2a2119", water="#2d5e63", water_hi="#5d9a98", grass="#2b4f3b", flower="#cfd8c7",
        grain=0.06, blend="screen", shadow="rgba(0,0,0,0.35)", ghost="rgba(231,238,223,0.06)",
    ),
}

# key: (family, file, weight, style)
FONT_FILES = {
    "serif": ("Cormorant Garamond", "cormorant-500.woff2", 500, "normal"),
    "serif-i": ("Cormorant Garamond", "cormorant-italic-400.woff2", 400, "italic"),
    "sans": ("DM Sans", "dm-sans.woff2", 400, "normal"),
    "mono": ("DM Mono", "dm-mono-400.woff2", 400, "normal"),
    "mono5": ("DM Mono", "dm-mono-500.woff2", 500, "normal"),
}
_fonts = {k: TTFont(FONTS / v[1]) for k, v in FONT_FILES.items()}


def measure(s, font, size, ls=0.0):
    f = _fonts[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap.get(ord(c), cmap[32])][0] for c in s)
    return adv * size / upm + ls * len(s)


def wrap(s, font, size, width):
    lines, cur = [], ""
    for word in s.split():
        test = f"{cur} {word}".strip()
        if cur and measure(test, font, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = test
    return lines + [cur]


_ids = iter(range(1, 1000))


def mascot(pose, x, y, height):
    """Mascot pose with its viewBox top-left at (x, y), scaled to `height` px tall."""
    src = (MASCOT / f"axo-{pose}.svg").read_text(encoding="utf-8").replace("ax-head", f"ax-head-{next(_ids)}")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', src).group(1).split()]
    inner = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", src.strip())
    s = height / vb[3]
    return f'<g transform="translate({x - vb[0] * s:.1f} {y - vb[1] * s:.1f}) scale({s:.4f})">{inner}</g>', vb[2] * s


MASCOT_CSS = (
    ".gills{transform-origin:0 0;animation:gills 3s ease-in-out infinite alternate}"
    ".eyes{transform-origin:0 4px;animation:blink 6s infinite}"
    ".wave{transform-origin:33px 46px;animation:wave 1.6s ease-in-out infinite}"
    ".bird{animation:drift 40s linear infinite}"
    "@keyframes gills{to{transform:scale(1.04)}}"
    "@keyframes blink{0%,95%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}"
    "@keyframes wave{0%,100%{transform:rotate(0)}50%{transform:rotate(-16deg)}}"
    "@keyframes drift{from{transform:translateX(0)}to{transform:translateX(60px)}}"
    "@media (prefers-reduced-motion:reduce){.gills,.eyes,.wave,.bird{animation:none}}"
)


# ---------------------------------------------------------------- svg

class Svg:
    def __init__(self, w, h, theme, label, radius=0):
        self.w, self.h, self.radius = w, h, radius
        self.t = THEMES[theme]
        self.label = label
        self.body, self.css, self.defs, self.used = [], [MASCOT_CSS], [], {}

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, font, size, fill, ls=0.0, anchor="start", upper=False):
        if upper:
            s = s.upper()
        self.used.setdefault(font, set()).update(s)
        fam, _, weight, style = FONT_FILES[font]
        a = f'x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}"'
        if style != "normal":
            a += f' font-style="{style}"'
        if ls:
            a += f' letter-spacing="{ls}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        self.add(f"<text {a}>{escape(s)}</text>")
        return measure(s, font, size, ls)

    def arrow(self, x, y, color, size=12):
        """↗ drawn as a path (DM Mono has no arrow glyphs)."""
        k = size / 24
        self.add(
            f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" fill="none" stroke="{color}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></g>'
        )

    def font_css(self):
        out = []
        for font, chars in self.used.items():
            fam, file, weight, style = FONT_FILES[font]
            tt = TTFont(FONTS / file, recalcTimestamp=False)
            opts = Options()
            opts.flavor = "woff2"
            opts.layout_features = ["*"]
            sub = Subsetter(opts)
            sub.populate(text="".join(sorted(chars)) + " ")
            sub.subset(tt)
            buf = io.BytesIO()
            tt.flavor = "woff2"
            tt.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:{style};"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
            )
        return "".join(out)

    def render(self):
        t, w, h, r = self.t, self.w, self.h, self.radius
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(self.label)}">'
            f"<title>{escape(self.label)}</title>"
            f"<style>{self.font_css()}{''.join(self.css)}</style>"
            f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="{r}"/></clipPath>'
            f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["sky_top"]}"/>'
            f'<stop offset=".7" stop-color="{t["sky_bottom"]}"/></linearGradient>'
            f'<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter>'
            f'<filter id="float" x="-10%" y="-40%" width="120%" height="200%">'
            f'<feDropShadow dx="0" dy="10" stdDeviation="15" flood-color="{t["shadow"]}" flood-opacity="1"/></filter>'
            f"{''.join(self.defs)}</defs>"
            f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="url(#sky)"/>'
            f"{''.join(self.body)}"
            f'<rect width="{w}" height="{h}" filter="url(#grain)" opacity="{t["grain"]}" style="mix-blend-mode:{t["blend"]}"/></g>'
            "</svg>"
        )


# ---------------------------------------------------------------- landscape

def hill(w, base, amp, seed, wl=(420, 260)):
    """y(x) for a soft rolling hill line."""
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in wl]
    return lambda x: base(x) + sum(amp * (0.65 if i else 1) * math.sin(x / l * 6.28 + p) for i, (l, p) in enumerate(zip(wl, ph)))


def hill_path(w, h, f, color, step=24):
    pts = [(x, f(x)) for x in range(-step, w + 2 * step, step)]
    d = f"M{pts[0][0]} {pts[0][1]:.1f}"
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]} {p2[1]:.1f}"
    d += f" L{pts[-2][0]} {h} L{pts[0][0]} {h}Z"
    return f'<path d="{d}" fill="{color}"/>'


def pine(x, y, size, t):
    """Tall triangle-stack pine standing on (x, y); `size` is its height."""
    w = size * 0.42
    out = [f'<rect x="{x - size * 0.035:.1f}" y="{y - size * 0.22:.1f}" width="{size * 0.07:.1f}" height="{size * 0.24:.1f}" fill="{t["trunk"]}"/>']
    for wf, top, bot in [(1.0, 0.62, 0.16), (0.82, 0.86, 0.42), (0.6, 1.0, 0.68)]:
        out.append(
            f'<path d="M{x - w * wf:.1f} {y - size * bot:.1f}L{x:.1f} {y - size * top:.1f}L{x + w * wf:.1f} {y - size * bot:.1f}Z" fill="{t["tree_dark"]}"/>'
        )
    return "".join(out)


def round_tree(x, y, size, t):
    """Circle-cluster tree on (x, y): trunk, canopy circles and one soft highlight."""
    trunk = f'<rect x="{x - size * 0.045:.1f}" y="{y - size * 0.62:.1f}" width="{size * 0.09:.1f}" height="{size * 0.63:.1f}" fill="{t["trunk"]}"/>'
    canopy = "".join(
        f'<circle cx="{x + dx * size:.1f}" cy="{y - dy * size:.1f}" r="{r * size:.1f}" fill="{t[c]}"/>'
        for dx, dy, r, c in [(0, 0.98, 0.36, "tree"), (0.22, 0.74, 0.3, "tree_dark"), (-0.24, 0.72, 0.28, "tree")]
    )
    hi = f'<circle cx="{x - size * 0.1:.1f}" cy="{y - size * 1.08:.1f}" r="{size * 0.11:.1f}" fill="{t["flower"]}" opacity=".1"/>'
    return trunk + canopy + hi


def ghost(svg, x, y, word, size, anchor="middle"):
    """Oversized ghost wordmark behind the landscape (Lagoa `ghost` token)."""
    return svg.text(x, y, word, "serif", size, svg.t["ghost"], anchor=anchor)


def river(hx, hy, hw, bx, by, bw, t):
    """River from a narrow mouth at the horizon (hx, hy) widening to the bottom edge."""
    l0, r0, l1, r1 = hx - hw / 2, hx + hw / 2, bx - bw / 2, bx + bw / 2
    my = (hy + by) / 2
    left = f"M{l0:.1f} {hy:.1f}C{l0 - hw:.1f} {my:.1f} {l1 + bw * 0.1:.1f} {my:.1f} {l1:.1f} {by:.1f}"
    right = f"M{r0:.1f} {hy:.1f}C{r0 + hw * 0.6:.1f} {my:.1f} {r1 - bw * 0.05:.1f} {my:.1f} {r1:.1f} {by:.1f}"
    body = (
        f'<path d="{left}L{r1:.1f} {by:.1f}C{r1 - bw * 0.05:.1f} {my:.1f} {r0 + hw * 0.6:.1f} {my:.1f} {r0:.1f} {hy:.1f}Z" fill="{t["water"]}"/>'
    )
    banks = f'<g fill="none" stroke="{t["water_hi"]}" stroke-width="2" opacity=".55"><path d="{left}"/><path d="{right}"/></g>'
    return body + banks


def swimmer(svg, cx, cy, height):
    """The mascot's head poking out of the water at (cx, cy) = water line under the chin."""
    t = svg.t
    k = height / 118  # axo-head viewBox height
    m, w = mascot("head", cx - 100 * k, cy - (66 + 36) * k, height)
    svg.add(m)
    svg.add(f'<rect x="{cx - 64 * k:.1f}" y="{cy:.1f}" width="{128 * k:.1f}" height="{12 * k:.1f}" fill="{t["water"]}"/>')
    svg.add(
        f'<ellipse cx="{cx:.1f}" cy="{cy + 2 * k:.1f}" rx="{70 * k:.1f}" ry="{9 * k:.1f}" fill="none" stroke="{t["water_hi"]}" stroke-width="2" opacity=".7"/>'
        f'<path d="M{cx - 40 * k:.1f} {cy + 18 * k:.1f}h{80 * k:.1f}" stroke="{t["water_hi"]}" stroke-width="2" stroke-linecap="round" opacity=".5"/>'
    )


def tuft(x, y, t, s=1.0):
    return (
        f'<g stroke="{t["grass"]}" stroke-width="1.6" stroke-linecap="round" fill="none">'
        f'<path d="M{x} {y}q{-2 * s:.1f} {-6 * s:.1f} {-6 * s:.1f} {-10 * s:.1f}"/>'
        f'<path d="M{x} {y}q{0.5 * s:.1f} {-7 * s:.1f} 0 {-13 * s:.1f}"/>'
        f'<path d="M{x} {y}q{2 * s:.1f} {-6 * s:.1f} {6 * s:.1f} {-9 * s:.1f}"/></g>'
    )


def daisy(x, y, t, r=3):
    petals = "".join(
        f'<circle cx="{x + r * math.cos(a):.1f}" cy="{y + r * math.sin(a):.1f}" r="{r * 0.62:.1f}"/>' for a in [i * math.pi / 3 for i in range(6)]
    )
    return f'<g fill="{t["flower"]}">{petals}</g><circle cx="{x}" cy="{y}" r="{r * 0.55:.1f}" fill="{t["sun"]}"/>'


def meadow(x0, x1, y_of, t, seed=1, density=1.0):
    """Scatter grass tufts and daisies along the ground line between x0 and x1."""
    rnd = random.Random(seed)
    out, x = [], x0
    while x < x1:
        y = y_of(x) + rnd.uniform(4, 30)
        out.append(tuft(x, y, t, rnd.uniform(0.9, 1.3)) if rnd.random() < 0.6 else daisy(x, y, t, rnd.uniform(2.6, 3.4)))
        x += rnd.uniform(24, 60) / density
    return "".join(out)


def birds(x, y, t, s=1.6):
    out = []
    for dx, dy, k in [(0, 0, 1), (56, -10, 0.9), (70, 30, 0.7)]:
        k *= s
        out.append(
            f'<path d="M{x + dx} {y + dy}q{5 * k:.1f} {-6 * k:.1f} {10 * k:.1f} 0q{5 * k:.1f} {-6 * k:.1f} {10 * k:.1f} 0" '
            f'stroke="{t["ink"]}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    return f'<g class="bird">{"".join(out)}</g>'


def strip(svg, x, y, cells, cell_w=None, h=58):
    """Quick-links strip: paper-raised, radius-lg, shadow-float, hairlines between cells."""
    t = svg.t
    pad = 20
    widths = cell_w or [max(measure(lbl.upper(), "mono5", 10, 2), measure(val, "mono", 13)) + 2 * pad + 18 for lbl, val in cells]
    total = sum(widths)
    svg.add(f'<rect x="{x}" y="{y}" width="{total:.1f}" height="{h}" rx="16" fill="{t["raised"]}" filter="url(#float)"/>')
    cx = x
    for i, ((lbl, val), cw) in enumerate(zip(cells, widths)):
        if i:
            svg.add(f'<line x1="{cx:.1f}" y1="{y + 12}" x2="{cx:.1f}" y2="{y + h - 12}" stroke="{t["rule"]}"/>')
        svg.text(cx + pad, y + 23, lbl, "mono5", 10, t["muted"], ls=2, upper=True)
        svg.text(cx + pad, y + 43, val, "mono", 13, t["ink"])
        svg.arrow(cx + cw - pad - 10, y + 13, t["muted"], 12)
        cx += cw
    return total
