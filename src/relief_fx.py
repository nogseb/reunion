"""Courbes de niveau des deux îles pour l'animation de fond « Relief des deux îles ».

Source : les tuiles d'altitude « terrarium » du site (docs/terrain/10, Copernicus DEM GLO-90).
Sortie : relief_fx.json, lu par site.py. À relancer seulement si les tuiles changent.
Dépendances : numpy, pillow, scikit-image, shapely.
"""
import json
import numpy as np
from PIL import Image
from skimage import measure
from shapely.geometry import LineString

TILES = "../docs/terrain/10/"
ISLANDS = {
    # tuiles x, tuiles y, niveaux (m) : côte puis courbes
    "reunion": dict(xs=[669, 670], ys=[572, 573, 574], levels=[5] + list(range(250, 3001, 250))),
    "maurice": dict(xs=[675, 676], ys=[569, 570, 571], levels=[5] + list(range(100, 801, 100))),
}


def mosaic(xs, ys):
    rows = []
    for y in ys:
        row = []
        for x in xs:
            try:
                a = np.asarray(Image.open(f"{TILES}{x}/{y}.png").convert("RGB")).astype(np.float64)
                row.append(a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768)
            except FileNotFoundError:
                row.append(np.full((256, 256), -50.0))
        rows.append(np.hstack(row))
    return np.vstack(rows)


out = {}
for k, d in ISLANDS.items():
    elev = mosaic(d["xs"], d["ys"])
    levels = []
    for lv in d["levels"]:
        paths = []
        for c in measure.find_contours(elev, lv):
            if len(c) < 12:
                continue
            pts = list(LineString([(p[1], p[0]) for p in c]).simplify(1.1).coords)
            if len(pts) >= 4:
                paths.append(pts)
        levels.append(paths)
    allp = [p for paths in levels for path in paths for p in path]
    x0, y0 = min(p[0] for p in allp), min(p[1] for p in allp)
    x1, y1 = max(p[0] for p in allp), max(p[1] for p in allp)

    def d_of(group):
        return "".join("M" + "L".join(f"{x - x0:.0f} {y - y0:.0f}" for x, y in path) for paths in group for path in paths)

    cut = 1 + (len(levels) - 1) // 2   # courbes basses / hautes
    out[k] = dict(w=round(x1 - x0), h=round(y1 - y0), coast=d_of(levels[:1]), low=d_of(levels[1:cut]), high=d_of(levels[cut:]))

json.dump(out, open("relief_fx.json", "w"), separators=(",", ":"))
print({k: (v["w"], v["h"]) for k, v in out.items()})
