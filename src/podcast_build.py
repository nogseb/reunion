"""Versions podcast des dossiers « Pour aller + loin ».

Chaque script (contenus/podcasts/<slug>.txt) alterne deux voix :
  A: voix féminine (Piper fr_FR-siwis-medium)
  B: voix masculine (Piper fr_FR-tom-medium)
Synthèse hors ligne avec sherpa-onnx, assemblage avec pauses, normalisation du volume
et export MP3 mono 64 kbit/s dans docs/podcasts/. Les durées sont écrites dans podcasts.json.

Voix : modèles Piper empaquetés par le projet sherpa-onnx (versions GitHub « tts-models »).
Usage : python3 podcast_build.py [slug ...]   (sans argument : tous les scripts)
"""
import glob, json, os, re, subprocess, sys, tempfile
import numpy as np
import sherpa_onnx

VOICES_DIR = os.environ.get("VOICES_DIR", "/tmp/claude-0/tts/sherpa")
VOICES = {"A": "fr_FR-siwis-medium", "B": "fr_FR-tom-medium"}
SPEED = 0.95            # un peu plus lent que la vitesse par défaut, pour l'écoute en voiture
SR = 44100
PAUSE_SAME = 0.35       # secondes entre deux phrases d'un même tour
PAUSE_TURN = 0.55       # secondes entre deux interlocuteurs
SCRIPTS = "../contenus/podcasts"
OUT = "../docs/podcasts"
TITLES = {}             # rempli depuis articles.py

def load_voice(name):
    d = os.path.join(VOICES_DIR, f"vits-piper-{name}")
    onnx = glob.glob(os.path.join(d, "*.onnx"))[0]
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=onnx, tokens=os.path.join(d, "tokens.txt"),
                                                   data_dir=os.path.join(d, "espeak-ng-data")),
        num_threads=2))
    return sherpa_onnx.OfflineTts(cfg)

def resample(x, sr):
    if sr == SR:
        return x
    n = int(round(len(x) * SR / sr))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)

def parse(path):
    turns = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([AB]):\s*(.+)$", line)
        if not m:
            raise ValueError(f"{path}: ligne sans locuteur : {line[:60]}")
        turns.append((m.group(1), m.group(2)))
    return turns

def build(slug, tts):
    turns = parse(os.path.join(SCRIPTS, f"{slug}.txt"))
    parts = []
    for i, (who, text) in enumerate(turns):
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s]
        for j, s in enumerate(sentences):
            a = tts[who].generate(s, sid=0, speed=SPEED)
            parts.append(resample(np.array(a.samples, dtype=np.float32), a.sample_rate))
            parts.append(np.zeros(int(SR * (PAUSE_SAME if j < len(sentences) - 1 else PAUSE_TURN)), np.float32))
    audio = np.concatenate([np.zeros(int(SR * 0.4), np.float32)] + parts)
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as f:
        audio.tofile(f.name)
        raw = f.name
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{slug}.mp3")
    title = TITLES.get(slug, slug)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", raw,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1",
                    "-c:a", "libmp3lame", "-b:a", "64k",
                    "-metadata", f"title={title}", "-metadata", "artist=Carnet de voyage, La Réunion et Maurice",
                    "-metadata", "album=Pour aller + loin", "-metadata", "comment=Voix de synthèse",
                    out], check=True)
    os.unlink(raw)
    return round(len(audio) / SR), os.path.getsize(out)

if __name__ == "__main__":
    from articles import ARTICLES
    for a in ARTICLES:
        src = open(a["file"], encoding="utf-8").read()
        TITLES[a["slug"]] = re.match(r"#\s+(.+?)\n", src).group(1).strip()
    slugs = sys.argv[1:] or [os.path.basename(p)[:-4] for p in sorted(glob.glob(os.path.join(SCRIPTS, "*.txt")))]
    tts = {k: load_voice(v) for k, v in VOICES.items()}
    meta_path = "podcasts.json"
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for slug in slugs:
        secs, size = build(slug, tts)
        meta[slug] = {"secs": secs, "bytes": size}
        print(f"{slug}: {secs // 60} min {secs % 60:02d} s, {size / 1e6:.1f} Mo")
    json.dump(meta, open(meta_path, "w"), indent=1, ensure_ascii=False)
