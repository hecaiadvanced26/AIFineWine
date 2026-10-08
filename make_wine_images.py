"""Generate one demo SVG bottle per wine from data/catalog.json.

Usage (from the repo root):
    python make_wine_images.py                      # reads data/catalog.json
    python make_wine_images.py path/to/catalog.json static/wines

Output: <out_dir>/<wine_id>.svg plus <out_dir>/placeholder.svg
No dependencies. Illustrations only, not real product photos.
"""
import json
import sys
from html import escape
from pathlib import Path

# (glass, wine, label, accent) per style
PALETTE = {
    "red":       ("#2a1a1f", "#6b1f33", "#f6efe4", "#742c40"),
    "white":     ("#6f7a45", "#e8d98a", "#fbf8ee", "#8a7a2c"),
    "rose":      ("#7a5a5c", "#e9a3a8", "#fdf4f2", "#b4575f"),
    "sparkling": ("#3b4a3a", "#f1e3a4", "#fbf8ee", "#a58a2e"),
    "other":     ("#3a3a3a", "#b9a27a", "#f6f1e7", "#6b5a3a"),
}


def style_of(wine_type):
    t = (wine_type or "").lower()
    if any(k in t for k in ("spark", "champ", "mouss", "cava", "prosecco", "cr\u00e9m", "crem", "p\u00e9til")):
        return "sparkling"
    if any(k in t for k in ("ros\u00e9", "rose", "rosado")):
        return "rose"
    if any(k in t for k in ("red", "rouge", "rosso", "tinto")):
        return "red"
    if any(k in t for k in ("white", "blanc", "bianco", "blanco")):
        return "white"
    return "other"


def wrap(text, width=12, max_lines=4):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1] + "\u2026"
    return lines


def bottle_svg(name, winery, vintage, wine_type):
    glass, wine, label, accent = PALETTE[style_of(wine_type)]
    name_lines = wrap(name)
    # Georgia 10px is about 5.6 px per character; squeeze lines that would leave the 66 px label area.
    tspans = "".join(
        f'<tspan x="100" dy="{0 if i == 0 else 12}"'
        + (' textLength="64" lengthAdjust="spacingAndGlyphs"' if len(l) * 5.6 > 64 else "")
        + f'>{escape(l)}</tspan>'
        for i, l in enumerate(name_lines))
    sub = escape(f"{winery or ''}".strip()[:16])
    year = escape(str(vintage)) if vintage else ""  # unknown or non-vintage: never claim "NV"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300" role="img" aria-label="Bottle illustration: {escape(name)}">
<defs>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{glass}"/><stop offset=".45" stop-color="{wine}"/><stop offset="1" stop-color="{glass}"/></linearGradient>
</defs>
<rect width="200" height="300" fill="#f0ece5"/>
<ellipse cx="100" cy="284" rx="46" ry="6" fill="#000" opacity=".12"/>
<path d="M88 14h24v8h-24z" fill="{accent}"/>
<path d="M90 22h20v62c0 14 30 24 30 52v138c0 6-4 10-10 10H70c-6 0-10-4-10-10V136c0-28 30-38 30-52z" fill="url(#g)"/>
<path d="M76 140v120" stroke="#fff" stroke-opacity=".18" stroke-width="5" stroke-linecap="round"/>
<rect x="64" y="150" width="72" height="96" rx="3" fill="{label}"/>
<rect x="64" y="150" width="72" height="5" fill="{accent}"/>
<text x="100" y="172" text-anchor="middle" font-family="Georgia,serif" font-size="10" fill="#302b28">{tspans}</text>
<text x="100" y="228" text-anchor="middle" font-family="system-ui,sans-serif" font-size="7" fill="#706963">{sub}</text>
<text x="100" y="240" text-anchor="middle" font-family="Georgia,serif" font-size="10" fill="{accent}">{year}</text>
</svg>
"""


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "data/catalog.json")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "static/wines")
    wines = json.loads(src.read_text(encoding="utf-8"))["wines"]
    out.mkdir(parents=True, exist_ok=True)
    for w in wines:
        (out / f"{w['wine_id']}.svg").write_text(
            bottle_svg(w.get("name", ""), w.get("winery"), w.get("vintage"), w.get("wine_type")),
            encoding="utf-8")
    (out / "placeholder.svg").write_text(bottle_svg("Wine", "", None, None), encoding="utf-8")
    print(f"{len(wines)} images written to {out}/")


if __name__ == "__main__":
    main()
