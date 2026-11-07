"""Builds the profile README images in ../assets, styled after diegorezm.github.io.

Usage: pip install fonttools brotli && python tools/build.py
"""

import base64
import io
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
OUT = ROOT / "assets"

W = 880
PAD = 32

THEMES = {
    "light": dict(paper="#e9e3d4", ink="#1c1b18", muted="#6c675b", rule="#1c1b182e", accent="#5b6a2c", grain=0.09),
    "dark": dict(paper="#14130f", ink="#e7e0cf", muted="#9a937f", rule="#e7e0cf24", accent="#b3bf73", grain=0.05),
}

FONT_FILES = {
    "serif": ("Instrument Serif", "instrument-serif.woff2", 400),
    "sans": ("IBM Plex Sans", "plex-sans.woff2", 400),
    "mono": ("IBM Plex Mono", "plex-mono-400.woff2", 400),
    "mono5": ("IBM Plex Mono", "plex-mono-500.woff2", 500),
}
_fonts = {k: TTFont(FONTS / f) for k, (_, f, _) in FONT_FILES.items()}


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


class Svg:
    def __init__(self, h, theme, label):
        self.h, self.t, self.label = h, THEMES[theme], label
        self.body, self.css, self.used = [], [], {}

    def text(self, x, y, s, font, size, fill, ls=0.0, anchor="start", upper=False, cls=""):
        if upper:
            s = s.upper()
        self.used.setdefault(font, set()).update(s)
        fam, _, weight = FONT_FILES[font]
        attrs = f'x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}"'
        if ls:
            attrs += f' letter-spacing="{ls}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if cls:
            attrs += f' class="{cls}"'
        self.body.append(f"<text {attrs}>{escape(s)}</text>")
        return measure(s, font, size, ls)

    def rule(self, y, color=None, x1=PAD, x2=W - PAD):
        self.body.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color or self.t["rule"]}" stroke-width="1"/>')

    def arrow(self, x, y, color, size=18):
        # lucide arrow-up-right, 24x24 viewbox
        s = size / 24
        self.body.append(
            f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></g>'
        )

    def font_css(self):
        out = []
        for font, chars in self.used.items():
            fam, file, weight = FONT_FILES[font]
            tt = TTFont(FONTS / file)
            opts = Options()
            opts.flavor = "woff2"
            opts.layout_features = ["*"]
            sub = Subsetter(opts)
            sub.populate(text="".join(chars) + " ")
            sub.subset(tt)
            buf = io.BytesIO()
            tt.flavor = "woff2"
            tt.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        return "".join(out)

    def render(self):
        t = self.t
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}" role="img" aria-label="{escape(self.label)}">'
            f"<title>{escape(self.label)}</title>"
            f"<style>{self.font_css()}{''.join(self.css)}</style>"
            f'<defs><clipPath id="card"><rect width="{W}" height="{self.h}" rx="6"/></clipPath>'
            f'<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter></defs>'
            f'<g clip-path="url(#card)"><rect width="{W}" height="{self.h}" fill="{t["paper"]}"/>'
            f"{''.join(self.body)}"
            f'<rect width="{W}" height="{self.h}" filter="url(#grain)" opacity="{t["grain"]}" style="mix-blend-mode:multiply"/></g>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{self.h - 1}" rx="6" fill="none" stroke="{t["rule"]}"/>'
            "</svg>"
        )


def save(name, theme, svg):
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}-{theme}.svg").write_text(svg.render(), encoding="utf-8")


# ---------------------------------------------------------------- content

LEAD = (
    "I build web apps with TypeScript, Next.js and PostgreSQL, ship them to Linux "
    "servers with Docker, and keep them running. Currently full-stack at Morzen "
    "and open to new opportunities."
)

PROJECTS = [
    ("grimo", True, "A social network for readers: shelves, reviews and a monthly reading recap. Web + mobile.", "TypeScript · Cloudflare"),
    ("meu-edital", True, "A study planner for public exams, with AI-imported notices.", "TypeScript · Kotlin · AI"),
]

def hero(theme):
    t = THEMES[theme]
    h = 432
    s = Svg(h, theme, "Diego Rezende. Development | Linux | Infra. " + LEAD + " Email: diegommrez12@gmail.com")
    cx, cy = 720, 216

    # radar: rings + spokes turning slowly, a sweep, and blips lighting up as it passes
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for r in range(10, 300, 9))
    spokes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{cx + 300 * math.cos(math.radians(a)):.1f}" y2="{cy + 300 * math.sin(math.radians(a)):.1f}"/>'
        for a in range(0, 360, 15)
    )
    s.body.append(f'<g class="spin" fill="none" stroke="{t["ink"]}" stroke-width=".8" opacity=".38">{rings}{spokes}</g>')

    wedges = []
    n, step, r = 24, 2.5, 290
    for k in range(n):
        a1, a2 = math.radians(-k * step), math.radians(-(k + 1) * step)
        wedges.append(
            f'<path d="M{cx} {cy} L{cx + r * math.cos(a1):.1f} {cy + r * math.sin(a1):.1f} '
            f'A{r} {r} 0 0 0 {cx + r * math.cos(a2):.1f} {cy + r * math.sin(a2):.1f}Z" '
            f'fill="{t["accent"]}" opacity="{0.32 * (1 - k / n) ** 1.6:.3f}"/>'
        )
    s.body.append(
        f'<g class="sweep">{"".join(wedges)}<line x1="{cx}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{t["accent"]}" stroke-width="1.4"/></g>'
    )
    sweep_secs = 7
    for i, (ang, dist) in enumerate([(25, 120), (70, 210), (140, 165), (205, 95), (250, 240), (310, 185), (345, 255)]):
        x = cx + dist * math.cos(math.radians(ang))
        y = cy + dist * math.sin(math.radians(ang))
        s.body.append(
            f'<g class="blip" style="animation-delay:{ang / 360 * sweep_secs:.2f}s">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{t["accent"]}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="none" stroke="{t["accent"]}" stroke-width="1"/></g>'
        )
    s.body.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{t["accent"]}"/>')
    s.css.append(
        f".spin{{transform-origin:{cx}px {cy}px;animation:spin 140s linear infinite}}"
        f".sweep{{transform-origin:{cx}px {cy}px;animation:spin {sweep_secs}s linear infinite}}"
        f".blip{{opacity:0;animation:blip {sweep_secs}s ease-out infinite}}"
        ".blink{animation:blink 1.1s steps(1) infinite}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
        "@keyframes blip{0%{opacity:1}55%{opacity:0}100%{opacity:0}}"
        "@keyframes blink{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.spin,.sweep,.blip,.blink{animation:none}}"
    )

    # top bar
    x = PAD
    w = s.text(x, 52, "Diego Rezende", "serif", 22, t["ink"])
    s.text(x + w, 52, ".", "serif", 22, t["accent"])
    s.text(W - PAD, 50, "BR · UTC−3", "mono", 11, t["muted"], ls=1.6, anchor="end")
    status = "open to work"
    sw = measure(status.upper(), "mono", 11, 1.6)
    sx = W - PAD - measure("BR · UTC−3", "mono", 11, 1.6) - 28 - sw
    s.body.append(f'<circle class="blink" cx="{sx - 10}" cy="46.5" r="3.5" fill="{t["accent"]}"/>')
    s.text(sx, 50, status, "mono", 11, t["accent"], ls=1.6, upper=True)

    # name
    w = s.text(x - 4, 192, "Diego Rezende", "serif", 104, t["ink"])
    s.body.append(f'<circle cx="{x - 4 + w + 9}" cy="184" r="7.5" fill="{t["accent"]}"/>')

    # tagline box
    parts, size, ls = ["DEVELOPMENT", "LINUX", "INFRA"], 13, 2.1
    bx, by, bh = x, 218, 38
    tx = bx + 16
    for i, p in enumerate(parts):
        if i:
            tx += 12
            tx += s.text(tx, by + 24, "|", "mono5", size, t["accent"], ls=ls) + 12
        tx += s.text(tx, by + 24, p, "mono5", size, t["ink"], ls=ls)
    s.body.append(f'<rect class="blink" x="{tx + 4:.1f}" y="{by + 12}" width="8" height="15" fill="{t["accent"]}"/>')
    bw = tx + 20 - bx
    s.body.append(f'<rect x="{bx}" y="{by}" width="{bw:.1f}" height="{bh}" fill="none" stroke="{t["ink"]}"/>')

    # lead
    for i, line in enumerate(wrap(LEAD, "sans", 15.5, 450)):
        s.text(x, 294 + i * 25, line, "sans", 15.5, t["muted"])

    cx2 = x
    for i, c in enumerate(["diegommrez12@gmail.com", "linkedin.com/in/diegorezm", "diegorezm.github.io"]):
        if i:
            cx2 += s.text(cx2 + 10, 394, "·", "mono", 11, t["accent"]) + 20
        cx2 += s.text(cx2, 394, c, "mono", 11, t["ink"] if i == 0 else t["muted"], ls=1.6, upper=True)
    return s


def section(theme, title, note):
    t = THEMES[theme]
    s = Svg(84, theme, title)
    s.text(PAD, 58, title, "serif", 44, t["ink"])
    s.rule(70, t["ink"], x1=PAD + measure(title, "serif", 44) + 20, x2=W - PAD - measure(note.upper(), "mono", 11, 1.6) - 20)
    s.text(W - PAD, 62, note, "mono", 11, t["muted"], ls=1.6, anchor="end", upper=True)
    return s


def project(theme, idx, name, building, blurb, stack):
    t = THEMES[theme]
    blurb_x, blurb_w = 272, 330
    lines = wrap(blurb, "sans", 14.5, blurb_w)
    h = max(84, 46 + 22 * len(lines))
    s = Svg(h, theme, f"{name}: {blurb} ({stack})")
    s.text(PAD, 44, f"{idx:02d}", "mono", 11, t["muted"], ls=1.2)
    s.text(PAD + 32, 46, name, "serif", 28, t["ink"])
    if building:
        s.body.append(f'<circle class="blink" cx="{PAD + 35}" cy="62" r="2.6" fill="{t["accent"]}"/>')
        s.text(PAD + 44, 66, "building", "mono", 10, t["accent"], ls=1.5, upper=True)
    for i, line in enumerate(lines):
        s.text(blurb_x, 45 + i * 22, line, "sans", 14.5, t["muted"])
    s.text(W - PAD - 34, 45, stack, "mono", 11.5, t["muted"], anchor="end")
    s.arrow(W - PAD - 18, 30, t["muted"])
    if building:
        s.css.append(".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
    return s


def main():
    for theme in THEMES:
        save("hero", theme, hero(theme))
        save("work", theme, section(theme, "Now building", "currently on"))
        for i, p in enumerate(PROJECTS, 1):
            save(f"project-{p[0].lower()}", theme, project(theme, i, *p))
    print(f"wrote {len(list(OUT.glob('*.svg')))} svgs to {OUT}")


if __name__ == "__main__":
    main()
