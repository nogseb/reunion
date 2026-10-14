"""Prépare les données géographiques embarquées dans la page.

- Traits de côte GSHHG pleine résolution (via basemap-data-hires), simplifiés.
- Lignes d'eau décoratives (style carte marine) autour des côtes.
- Chemins SVG de repli si la carte WebGL ne peut pas s'afficher.
- Lever et coucher du soleil par jour.
- Contrôle : chaque lieu tombe sur l'île (ou près de la côte s'il est en mer).
"""
import json, math, datetime as dt
from shapely.geometry import Polygon, Point, mapping, MultiPolygon
from shapely.ops import unary_union, transform
from astral import LocationInfo
from astral.sun import sun
from zoneinfo import ZoneInfo

LAT0 = -20.7
K = math.cos(math.radians(LAT0))  # échelle des longitudes

def to_eq(x, y, z=None):
    return (x * K, y)

def from_eq(x, y, z=None):
    return (x / K, y)

# Le trait de côte GSHHG de La Réunion est décalé d'environ 1,2 km vers le nord
# par rapport aux coordonnées WGS84 (contrôlé sur les extrémités de l'île et
# sur des points côtiers connus) : on le recale.
OFFSETS = {"reunion": (-0.001, -0.011), "maurice": (0.0, 0.0)}

def load_land(name, min_pts=4):
    rings = json.load(open(f"{name}_rings.json"))
    ox, oy = OFFSETS[name]
    rings = [[[x + ox, y + oy] for x, y in r] for r in rings]
    polys = [Polygon(r) for r in rings if len(r) >= min_pts]
    return unary_union([p.buffer(0) for p in polys])

def rnd(coords, n=4):
    return [[round(x, n), round(y, n)] for x, y in coords]

def geom_rings(g):
    gs = [g] if g.geom_type == "Polygon" else list(g.geoms)
    return gs

out = {"islands": {}}
land_all = {}
for name in ("reunion", "maurice"):
    land = load_land(name)
    land_all[name] = land
    eq = transform(to_eq, land)
    simp = transform(from_eq, eq.simplify(0.00025, preserve_topology=True))
    polys = []
    for p in geom_rings(simp):
        if p.area < 1e-6:  # îlots minuscules
            continue
        polys.append([rnd(p.exterior.coords)])
    # Lignes d'eau : décalages vers le large
    lines = []
    for d in (0.0045, 0.010, 0.018):
        b = transform(from_eq, eq.buffer(d, quad_segs=6).simplify(0.0012))
        for p in geom_rings(b):
            lines.append({"d": d, "c": rnd(p.exterior.coords)})
    minx, miny, maxx, maxy = land.bounds
    out["islands"][name] = {
        "land": polys,
        "waterlines": lines,
        "bounds": [round(minx, 4), round(miny, 4), round(maxx, 4), round(maxy, 4)],
        "npts": sum(len(r[0]) for r in polys),
    }

# Repli SVG : projection équirectangulaire locale
def svg_for(name, width=600, pad=0.06):
    land = land_all[name]
    eq = transform(to_eq, land).simplify(0.0006, preserve_topology=True)
    minx, miny, maxx, maxy = eq.bounds
    dx, dy = maxx - minx, maxy - miny
    minx -= dx * pad; maxx += dx * pad; miny -= dy * pad; maxy += dy * pad
    scale = width / (maxx - minx)
    height = (maxy - miny) * scale
    def P(x, y):
        return ((x - minx) * scale, (maxy - y) * scale)
    parts = []
    for p in geom_rings(eq):
        if p.area < 1e-7:
            continue
        pts = [P(x, y) for x, y in p.exterior.coords]
        parts.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return {"w": width, "h": round(height, 1), "d": "".join(parts),
            "proj": {"minx": minx, "maxy": maxy, "scale": scale, "k": K}}

out["svg"] = {n: svg_for(n) for n in ("reunion", "maurice")}

# Contrôle des lieux : sur terre, ou à moins de X km de la côte s'ils sont en mer
places = json.load(open("places.json"))
report = []
for pid, p in places.items():
    isl = p["isl"]
    land = land_all[isl]
    pt = Point(p["lon"], p["lat"])
    inside = land.contains(pt)
    dist_km = land.exterior.distance(pt) * 111 if land.geom_type == "Polygon" else min(g.exterior.distance(pt) for g in land.geoms) * 111
    kind = "sea" if p.get("sea") else ("coast" if p.get("coast") else "land")
    report.append((pid, isl, "terre" if inside else "MER", round(dist_km, 2), kind))
def is_bad(r):
    pid, isl, where, d, kind = r
    if kind == "land":
        return where == "MER" or d < 0.15
    if kind == "coast":
        return d > 0.8
    return where == "terre" or d > 15
bad = [r for r in report if is_bad(r)]
for r in report:
    print(*r)
print("A VERIFIER:", bad)

# Lever / coucher du soleil
sunrows = {}
d0 = dt.date(2027, 5, 19)
locs = {
    "reunion": LocationInfo("Saint-Denis", "Réunion", "Indian/Reunion", -20.879, 55.448),
    "maurice": LocationInfo("Port-Louis", "Maurice", "Indian/Mauritius", -20.161, 57.501),
}
for i in range(17):
    day = d0 + dt.timedelta(days=i)
    row = {}
    for k, loc in locs.items():
        s = sun(loc.observer, date=day, tzinfo=ZoneInfo(loc.timezone))
        row[k] = [s["sunrise"].strftime("%H:%M"), s["sunset"].strftime("%H:%M")]
    sunrows[day.isoformat()] = row
out["sun"] = sunrows
json.dump(out, open("geo.json", "w"), separators=(",", ":"), ensure_ascii=False)
print({n: v["npts"] for n, v in out["islands"].items()}, "taille geo.json :", round(len(json.dumps(out, separators=(",", ":"))) / 1024), "Ko")
print(sunrows["2027-05-20"], sunrows["2027-06-03"])
