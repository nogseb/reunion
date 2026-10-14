"""Tuiles de relief « terrarium » (256 px) pour les deux îles, d'après Copernicus DEM GLO-90.

- Mosaïque par île, reprojection en Web Mercator tuile par tuile.
- Mer et valeurs négatives ramenées à 0 m (sinon la mer s'enfoncerait sous la carte).
- Seules les tuiles contenant de la terre sont écrites ; les autres seront servies plates par la page.
"""
import glob, io, json, math, os, shutil
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds
from PIL import Image

OUT = "../docs/terrain"
ZMIN, ZMAX = 5, 12
R = 6378137.0
ORIGIN = math.pi * R

def tile_xy(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    lr = math.radians(lat)
    y = int((1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n)
    return x, y

def tile_bounds_merc(x, y, z):
    size = 2 * ORIGIN / 2 ** z
    minx = -ORIGIN + x * size
    maxy = ORIGIN - y * size
    return minx, maxy - size, minx + size, maxy

def encode(h):
    h = np.clip(np.round(h), 0, 9000).astype(np.int32)
    v = h + 32768
    rgb = np.zeros(h.shape + (3,), np.uint8)
    rgb[..., 0] = v // 256
    rgb[..., 1] = v % 256
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()

files = sorted(glob.glob("dem/*.tif"))
groups = {
    "reunion": [f for f in files if "E055" in f],
    "maurice": [f for f in files if "E057" in f],
}
boxes = {"reunion": (55.19, -21.41, 55.87, -20.84), "maurice": (57.28, -20.55, 57.82, -19.81)}
mosaics = {}
for k, fl in groups.items():
    srcs = [rasterio.open(f) for f in fl]
    arr, tr = merge(srcs)
    crs = srcs[0].crs
    for s in srcs:
        s.close()
    a = arr[0].astype(np.float32)
    a[~np.isfinite(a)] = 0
    a[a < 0] = 0
    mosaics[k] = (a, tr, crs)
    print(k, a.shape, "max", round(float(a.max()), 1))

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
keys, total = [], 0
for z in range(ZMIN, ZMAX + 1):
    tiles = set()
    for k, (w, s, e, n) in boxes.items():
        x0, y0 = tile_xy(w, n, z)
        x1, y1 = tile_xy(e, s, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                tiles.add((x, y))
    nz = 0
    for (x, y) in sorted(tiles):
        b = tile_bounds_merc(x, y, z)
        dst_tr = from_bounds(*b, 256, 256)
        out = np.zeros((256, 256), np.float32)
        for k, (a, tr, crs) in mosaics.items():
            tmp = np.zeros((256, 256), np.float32)
            reproject(a, tmp, src_transform=tr, src_crs=crs, dst_transform=dst_tr, dst_crs="EPSG:3857",
                      resampling=Resampling.bilinear if z >= 11 else Resampling.average, src_nodata=None, dst_nodata=0)
            out = np.maximum(out, tmp)
        if out.max() < 1:
            continue
        data = encode(out)
        p = f"{OUT}/{z}/{x}"
        os.makedirs(p, exist_ok=True)
        open(f"{p}/{y}.png", "wb").write(data)
        keys.append(f"{z}/{x}/{y}")
        total += len(data)
        nz += 1
    print(f"z{z}: {nz} tuiles")
flat = np.zeros((256, 256), np.float32)
flat_png = encode(flat)
json.dump({"keys": keys, "flat": __import__("base64").b64encode(flat_png).decode()}, open("terrain_index.json", "w"))
print("total", len(keys), "tuiles,", round(total / 1024 / 1024, 2), "Mo ; tuile plate", len(flat_png), "octets")
