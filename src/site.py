# -*- coding: utf-8 -*-
import json, os, re, datetime as dt
from html import escape as e
from content import DAYS, SOURCES, LABELS, LOGEMENTS, LG_ST, LG_ORDER, LG_GROUPS
from tab import TAB, GROUPS
from articles import ARTICLES
from quiz import QUIZ
import random
import markdown

GEO = json.load(open("geo.json"))
PLACES = json.load(open("places_final.json"))
HUBS = {"run": "air", "mru": "air", "baseouest": "home", "basenord": "home"}

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JABR = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

def fr(s):
    """Espaces insécables avant les signes doubles et l'euro."""
    s = re.sub(r" ([:;!?€])", "\u00a0\\1", s)
    s = re.sub(r"(\d) (MUR|km|min|h|m|kg|l)\b", "\\1\u00a0\\2", s)
    return s

def t(s):
    return fr(e(s, quote=False))

def date_long(iso):
    d = dt.date.fromisoformat(iso)
    j = "1er" if d.day == 1 else str(d.day)
    return f"{JOURS[d.weekday()].capitalize()} {j} {MOIS[d.month-1]}"

def date_short(iso):
    d = dt.date.fromisoformat(iso)
    j = "1er" if d.day == 1 else str(d.day)
    return f"{JABR[d.weekday()]} {j} {MOIS[d.month-1]}"

def hfmt(hm):
    h, m = hm.split(":")
    return f"{int(h)}\u00a0h\u00a0{m}"

def dms(lat, lon):
    def one(v, pos, neg):
        h = pos if v >= 0 else neg
        v = abs(v); d = int(v); m = round((v - d) * 60)
        if m == 60: d += 1; m = 0
        return f"{d}°{m:02d}′\u00a0{h}"
    return f"{one(lat,'N','S')} · {one(lon,'E','O')}"

ST = {"reserve": "Réservé", "areserver": "À réserver", "optionnel": "Optionnel", "arbitrer": "À arbitrer"}
ORDER = ["areserver", "arbitrer", "optionnel", "reserve"]
EFF = {"facile": 1, "modéré": 2, "soutenu": 3}
ISL = {"reunion": "La Réunion", "maurice": "Maurice", "both": "Maurice → La Réunion", "transit": "Trajet"}

def st_control(aid, s, label):
    opts = "".join(f'<option value="{k}"{" selected" if k == s else ""}>{ST[k]}</option>' for k in ORDER)
    return (f'<label class="st" data-act="{aid}" data-s="{s}"><span class="ico" aria-hidden="true"></span>'
            f'<span class="st-txt">{ST[s]}</span><span class="st-caret" aria-hidden="true"></span>'
            f'<select aria-label="Statut : {e(label)}">{opts}</select></label>')

# ---------- Lieux : jours associés ----------
places = {}
for pid, p in PLACES.items():
    places[pid] = dict(lon=p["lon"], lat=p["lat"], name=p["name"], isl=p["isl"], hub=HUBS.get(pid), days=[])
for d in DAYS:
    for pid in d["pts"]:
        did = f"j{d['n']}"
        if did not in places[pid]["days"]:
            places[pid]["days"].append(did)
used = {pid for d in DAYS for pid in d["pts"]}
places = {k: v for k, v in places.items() if k in used}

def src_name(key):
    title = SOURCES[key][0]
    name = title.split(" — ")[-1]
    return re.sub(r"\s*\(.*\)$", "", name)

# ---------- Jours ----------
MAP_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14"/></svg>'
days_html = []
acts_json = []
for d in DAYS:
    did = f"j{d['n']}"
    isl = d["isl"]
    tags = []
    if d.get("calm"):
        tags.append('<span class="tag tag-calm">Journée calme</span>')
    meta = []
    eff = EFF[d["effort"]]
    bars = "".join(f'<i class="{"on" if i < eff else ""}"></i>' for i in range(3))
    meta.append(f'<li><span class="k">Effort</span><span class="effort" aria-hidden="true">{bars}</span>{t(d["effort"])}</li>')
    if isl in ("reunion", "maurice", "both"):
        k = "maurice" if isl == "both" else isl
        sr, ss = GEO["sun"][d["date"]][k]
        meta.append(f'<li><span class="k">Soleil</span><span>{hfmt(sr)} – {hfmt(ss)}</span></li>')
    if d.get("main"):
        p = PLACES[d["main"]]
        meta.append(f'<li><span class="mono">{dms(p["lat"], p["lon"])}</span></li>')
    acts = []
    for i, a in enumerate(d["acts"]):
        tm = f'<time>{hfmt(a["t"])}</time>' if a.get("t") else '<time aria-hidden="true">·</time>'
        note = f'<p class="act-n">{t(a["note"])}</p>' if a.get("note") else ""
        stc = ""
        if a.get("s"):
            stc = st_control(a["id"], a["s"], a["txt"])
            acts_json.append(dict(id=a["id"], day=did, txt=a["txt"], s=a["s"]))
        if a.get("link"):
            note += f'<a class="act-l" href="{a["link"][0]}">{t(a["link"][1])}</a>'
        acts.append(f'<li class="act">{tm}<div class="act-body"><p class="act-t">{t(a["txt"])}</p>{note}</div>{stc}</li>')
    tip = f'<p class="note"><b>Conseil pratique</b>{t(d["tip"])}</p>' if d.get("tip") else ""
    planb = f'<p class="note note-b"><b>Si la météo est défavorable</b>{t(d["planb"])}</p>' if d.get("planb") else ""
    src = ""
    if d["src"]:
        dates = sorted({SOURCES[k][3] for k in d["src"]})
        links = ", ".join(f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{e(src_name(k))}</a>' for k in d["src"])
        src = f'<p class="src">Vérifié le {" et ".join(dates)} : {links}</p>'
    mapbtn = f'<button type="button" class="btn-map" data-fly="{did}">{MAP_ICON}Voir sur la carte</button>' if d["pts"] else ""
    days_html.append(f'''<article class="day isl-{isl}" id="d-{did}" aria-labelledby="{did}-t">
  <div class="day-head">
    <div class="day-no"><small>Jour</small>{d["n"]}</div>
    <p class="day-date"><span>{date_long(d["date"])}</span><span class="tag">{ISL[isl]}</span>{"".join(tags)}</p>
    <div><h3 id="{did}-t">{t(d["title"])}</h3><p class="day-place">{t(d["place"])}</p></div>
  </div>
  <ul class="meta">{"".join(meta)}</ul>
  <p class="travel"><b>Trajets</b> · {t(d["travel"])}</p>
  <ol class="acts">{"".join(acts)}</ol>
  {tip}{planb}{src}{mapbtn}
</article>''')

# ---------- Frise ----------
cells, leg = [], []
for d in DAYS:
    did = f"j{d['n']}"
    cells.append(f'<button type="button" class="tl-cell isl-{d["isl"]}" data-day="{did}" data-goto="{did}" aria-label="Jour {d["n"]}, {date_long(d["date"])}, {e(d["title"])}">{d["n"]}</button>')
blocks = [(1, 2, ""), (3, 7, "Maurice ouest"), (8, 12, "Maurice nord"), (13, 16, "La Réunion"), (17, 17, "")]
for a, b, lab in blocks:
    leg.append(f'<span style="grid-column:{a} / {b + 1}">{e(lab)}</span>')

# ---------- Réservations (état initial, recalculé en direct par la page) ----------
resa = []
for k in ORDER:
    items = [a for a in acts_json if a["s"] == k]
    h = f'<div class="resa-group" data-s="{k}"><h3><span class="ico" aria-hidden="true"></span>{ST[k]} <span class="n">{len(items)}</span></h3>'
    if items:
        lis = []
        for a in items:
            dd = next(x for x in DAYS if f"j{x['n']}" == a["day"])
            lis.append(f'<li><button type="button" class="resa-day" data-goto="{a["day"]}"><span class="d">J{dd["n"]} · {date_short(dd["date"])}</span><span class="t">{t(a["txt"])}</span></button>{st_control(a["id"], a["s"], a["txt"])}</li>')
        h += f'<ul class="resa-list">{"".join(lis)}</ul>'
    else:
        h += '<p class="resa-empty">Rien encore. Passez un élément à « Réservé » une fois la réservation confirmée.</p>'
    resa.append(h + "</div>")


# ---------- Logements à Maurice (page Suivi) ----------
def lg_control(lid, s, label):
    opts = "".join(f'<option value="{k}"{" selected" if k == s else ""}>{LG_ST[k]}</option>' for k in LG_ORDER)
    return (f'<label class="st" data-lg="{lid}" data-s="{s}"><span class="ico" aria-hidden="true"></span>'
            f'<span class="st-txt">{LG_ST[s]}</span><span class="st-caret" aria-hidden="true"></span>'
            f'<select aria-label="Demande : {e(label)}">{opts}</select></label>')

def gallery(x):
    """Bandeau de vignettes ; chaque vignette ouvre la photo (visionneuse en JS, lien simple sinon)."""
    if not x.get("photos"):
        return ""
    items = json.load(open(x["photos"]))
    d = x["photos_dir"]
    lis = "".join(
        f'<li><a href="{d}{ph["f"]}" data-i="{i}" data-cap="{e(ph["cap"])}" data-w="{ph["w"]}" data-h="{ph["h"]}">'
        f'<img src="{d}t/{ph["f"]}" alt="{e(ph["cap"])}" width="{ph["tw"] // 2}" height="{ph["th"] // 2}" loading="lazy" decoding="async"></a></li>'
        for i, ph in enumerate(items))
    return (f'<div class="gal" data-gal="{x["id"]}"><p class="gal-h">Photos de la maison <span class="mono">{len(items)}</span></p>'
            f'<ul class="gal-strip" aria-label="Photos de la maison, {e(x["lieu"])}">{lis}</ul></div>')

lg_html = []
for g, glabel, gnote in LG_GROUPS:
    items = [x for x in LOGEMENTS if x["g"] == g]
    lis = []
    for x in items:
        if x["debut"]:
            n = (dt.date.fromisoformat(x["fin"]) - dt.date.fromisoformat(x["debut"])).days
            dates = f'{date_short(x["debut"])} → {date_short(x["fin"])} · {n} nuits'
        else:
            dates = "Sans demande"
        lis.append(
            f'<li class="lg-item" id="{x["id"]}" data-lg-item="{x["id"]}" data-s="{x["s"]}">'
            f'<div class="lg-body"><p class="lg-h"><b>{t(x["hote"])}</b><span>{t(x["lieu"])}</span></p>'
            f'<p class="lg-d mono">{dates}</p><p class="lg-n">{t(x["note"])}</p>'
            f'<a class="lg-a" href="{x["url"]}" target="_blank" rel="noopener noreferrer">Voir l\'annonce HomeExchange</a>{gallery(x)}</div>'
            f'{lg_control(x["id"], x["s"], x["hote"] + ", " + x["lieu"])}</li>')
    lg_html.append(f'<div class="resa-group lg-group"><h3>{t(glabel)} <span class="n">{len([x for x in items if x["s"] != "ecartee"])}</span></h3>'
                   f'<p class="lg-gn">{t(gnote)}</p><ul class="resa-list lg-list">{"".join(lis)}</ul></div>')
logements_html = "".join(lg_html)

# ---------- Vue tableau ----------
act_s = {a["id"]: a["s"] for a in acts_json}
tab_rows = ['<thead><tr><th scope="col">Jour</th><th scope="col">Programme</th><th scope="col" class="c-eff">Effort</th></tr></thead>']
for (glabel, gisl, ga, gb) in GROUPS:
    tab_rows.append(f'<tbody><tr class="grp grp-{gisl}"><th colspan="3" scope="colgroup">{t(glabel)}</th></tr>')
    for d in DAYS[ga - 1:gb]:
        did = f"j{d['n']}"
        items = []
        for lab, aid in TAB[d["n"]]:
            if aid:
                st = act_s[aid]
                items.append(f'<li data-tact="{aid}" data-s="{st}"><span class="ico" aria-hidden="true"></span>{t(lab)}<span class="sr"> ({ST[st]})</span></li>')
            else:
                items.append(f'<li>{t(lab)}</li>')
        eff = EFF[d["effort"]]
        bars = "".join(f'<i class="{"on" if i < eff else ""}"></i>' for i in range(3))
        calm = '<span class="tag tag-calm">calme</span>' if d.get("calm") else ""
        tab_rows.append(
            f'<tr class="row isl-{d["isl"]}" data-day="{did}">'
            f'<td class="c-day"><span class="n">{d["n"]}</span><span class="d">{date_short(d["date"])}</span></td>'
            f'<td class="c-prog"><a class="t" href="#{did}">{t(d["title"])}</a>{calm}<span class="pl">{t(d["place"])}</span>'
            f'<ul class="tab-acts">{"".join(items)}</ul></td>'
            f'<td class="c-eff"><span class="effort" role="img" aria-label="Effort {d["effort"]}">{bars}</span></td></tr>')
    tab_rows.append('</tbody>')

# ---------- Pratique ----------
def srcline(keys, date=None):
    links = ", ".join(f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{e(src_name(k))}</a>' for k in keys)
    dates = sorted({SOURCES[k][3] for k in keys})
    return f'<p class="src">Vérifié le {" et ".join(dates)} : {links}</p>'

def phone(label, num):
    return f'<li><span>{t(label)}</span><span class="num">{num}</span><button type="button" class="copy" data-copy="{num}">Copier</button></li>'

prat = []
prat.append(f'''<article class="card"><p class="eyebrow">Heure</p><h3>Décalage horaire</h3>
<p class="big">+2 h</p>
<p>{t("La Réunion et Maurice sont à UTC+4 toute l'année, sans heure d'été. En mai et juin, quand il est midi à Toulouse, il est 14 h à Saint-Denis comme à Port-Louis.")}</p>
<p>{t("Journées courtes en début d'hiver austral : lever vers 6 h 40, coucher vers 17 h 45. Les activités en plein air se calent tôt.")}</p></article>''')
prat.append(f'''<article class="card"><p class="eyebrow">Papiers</p><h3>Formalités pour Maurice</h3>
<ul>
<li>{t("Pas de visa pour un séjour de moins de 3 mois : un tampon est apposé à l'arrivée.")}</li>
<li>{t("Passeport valide pour toute la durée du séjour. Pour La Réunion, la carte d'identité suffit.")}</li>
<li>{t("Billet retour exigé. Justificatifs d'hébergement et de ressources pouvant être demandés : gardez les confirmations HomeExchange à portée de main.")}</li>
<li>{t("Formulaire en ligne « Mauritius All in One Travel Form » recommandé avant le départ, et questionnaire sanitaire remis à l'arrivée.")}</li>
<li>{t("Une autorisation de voyage électronique a été annoncée fin 2025, sans date d'entrée en vigueur : à revérifier au printemps 2027.")}</li>
</ul>{srcline(["diplo", "eta"])}</article>''')
prat.append(f'''<article class="card"><p class="eyebrow">Argent</p><h3>Monnaie à Maurice</h3>
<p class="big">1 € ≈ 53,1 MUR</p>
<p>{t("Roupie mauricienne (MUR, notée Rs). Repères : 100 MUR ≈ 1,90 € ; 1 000 MUR ≈ 19 €. Taux indicatif du 13 octobre 2026, hors frais bancaires.")}</p>
<p>{t("Prévoir des espèces pour les marchés, la cuisine de rue et les petits sites. La Réunion est en euros.")}</p>{srcline(["fx"])}</article>''')
prat.append(f'''<article class="card"><p class="eyebrow">Route</p><h3>Conduire à Maurice</h3>
<ul>
<li><strong>{t("On roule à gauche")}</strong>{t(" ; les ronds-points se prennent dans le sens des aiguilles d'une montre.")}</li>
<li>{t("40 km/h en ville, 80 km/h hors agglomération, 110 km/h sur certaines portions de l'autoroute.")}</li>
<li>{t("Permis français accepté pour un séjour touristique ; permis international recommandé, à demander avant le départ. Les loueurs demandent en général plus d'un an de permis.")}</li>
<li>{t("Pas de péage. Beaucoup de stations-service ferment la nuit.")}</li>
<li>{t("Stationnement payant à Port-Louis, Rose-Hill, Curepipe et Quatre-Bornes : disques vendus en station-service.")}</li>
</ul>{srcline(["diplo", "auto"])}</article>''')
prat.append(f'''<article class="card"><p class="eyebrow">Saison</p><h3>Météo de fin mai</h3>
<ul>
<li>{t("Début de l'hiver austral, hors saison cyclonique. Les alizés de sud-est arrosent les côtes est et laissent l'ouest abrité.")}</li>
<li>{t("La Réunion : 21 à 28 °C à Saint-Denis en mai, 19 à 26 °C en juin. Côte ouest très sèche (20 mm et 3 jours de pluie en mai au Port). Cilaos : 11 à 22 °C. Mer à 27 °C en mai, 26 °C en juin.")}</li>
<li>{t("Maurice en mai : 21 à 27 °C sur la côte, mer autour de 27 °C, environ 7 h de soleil par jour, averses souvent brèves.")}</li>
<li>{t("Prévisions : Météo-France La Réunion et Mauritius Meteorological Services, à consulter la veille de chaque sortie.")} <a href="https://meteofrance.re/" target="_blank" rel="noopener">Météo-France</a> · <a href="http://metservice.intnet.mu/" target="_blank" rel="noopener">MMS</a></li>
</ul>{srcline(["clire", "climu"])}</article>''')
prat.append(f'''<article class="card"><p class="eyebrow">Urgences</p><h3>Contacts utiles</h3>
<p class="sublabel">La Réunion</p>
<ul class="phones">{phone("SAMU", "15")}{phone("Police et gendarmerie", "17")}{phone("Pompiers", "18")}{phone("Numéro d'urgence européen", "112")}</ul>
<p class="sublabel">Maurice</p>
<ul class="phones">{phone("Police", "999")}{phone("Urgences médicales (SAMU)", "114")}{phone("Pompiers", "115")}{phone("Garde-côtes", "177")}{phone("Alertes cyclone depuis un mobile", "171")}</ul>
<p>{t("Ambassade de France à Maurice, installée à Telfair (Moka) : contact via son site. France Consulaire répond du lundi au vendredi, de 8 h à 16 h heure de Paris, soit de 10 h à 18 h à Maurice.")} <a href="https://mu.diplomatie.gouv.fr/" target="_blank" rel="noopener">mu.diplomatie.gouv.fr</a></p>
{srcline(["urgre", "urgmu", "diplo", "amb"])}</article>''')


# ---------- Pour aller + loin ----------
DAYN = {f"j{d['n']}": d for d in DAYS}
PODS = json.load(open("podcasts.json")) if os.path.exists("podcasts.json") else {}
def pod_block(slug):
    p = PODS.get(slug)
    if not p:
        return ""
    mins = max(1, round(p["secs"] / 60))
    size = f'{p["bytes"] / 1e6:.1f}'.replace(".", ",")
    return (f'<div class="pod"><p class="pod-h"><b>Version podcast</b> · {mins} min · deux voix de synthèse</p>'
            f'<audio controls preload="none" src="podcasts/{slug}.mp3"></audio>'
            f'<a class="pod-dl" href="podcasts/{slug}.mp3" download>Télécharger le MP3 ({size} Mo)</a></div>')
LETTERS = "ABCD"
def quiz_block(slug):
    qs = QUIZ.get(slug)
    if not qs:
        return ""
    items = []
    for i, x in enumerate(qs):
        opts = [x["r"]] + x["f"]
        random.Random(f"{slug}-{i}-13").shuffle(opts)  # graine choisie pour répartir les bonnes réponses entre A, B, C et D
        ok = opts.index(x["r"])
        btns = "".join(f'<button type="button" class="qz-o" data-i="{k}"><span class="qz-l" aria-hidden="true">{LETTERS[k]}</span><span>{t(o)}</span></button>' for k, o in enumerate(opts))
        items.append(f'<li class="qz" data-ok="{ok}"><p class="qz-q" id="qz-{slug}-{i}">{t(x["q"])}</p>'
                     f'<div class="qz-opts" role="group" aria-labelledby="qz-{slug}-{i}">{btns}</div>'
                     f'<p class="qz-why" aria-live="polite" hidden><b class="qz-v"></b> {t(x["why"])}</p></li>')
    return (f'<section class="quiz" id="quiz-{slug}" data-quiz="{slug}" aria-labelledby="quiz-{slug}-t">'
            f'<p class="eyebrow">Avez-vous bien retenu ?</p><h3 id="quiz-{slug}-t">Le quiz du dossier <span class="qz-n">{len(qs)} questions</span></h3>'
            f'<ol class="qz-list">{"".join(items)}</ol>'
            f'<div class="qz-end" hidden><p class="qz-score" aria-live="polite"></p>'
            f'<button type="button" class="btn-ghost qz-reset">Recommencer le quiz</button></div></section>')
cards, essays = [], []
for a in ARTICLES:
    src = open(a["file"], encoding="utf-8").read()
    m = re.match(r"#\s+(.+?)\n+\*(.+?)\*\s*\n", src)
    title, stand = m.group(1).strip(), m.group(2).strip()
    body = src[m.end():].lstrip()
    body = re.sub(r"^---\s*\n", "", body)
    body = re.sub(r"<small>\s*\n", '<div class="fine" markdown="1">\n', body).replace("</small>", "</div>")
    html_body = markdown.markdown(body, extensions=["tables", "extra", "sane_lists", "md_in_html"])
    html_body = html_body.replace("<table>", '<div class="essay-table"><table>').replace("</table>", "</table></div>")
    html_body = fr(html_body)
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html_body)))
    mins = max(1, round(words / 220))
    slug = a["slug"]
    links = "".join(
        f'<li><button type="button" data-goto="{did}"><span class="dn {"mru" if DAYN[did]["isl"] == "maurice" else "run"}">{DAYN[did]["n"]}</span>'
        f'<span>{t(lab)}<small>{date_long(DAYN[did]["date"])}</small></span></button></li>' for did, lab in a["links"])
    note = f'<p class="essay-note">{t(a["note"])}</p>' if a.get("note") else ""
    cards.append(f'''<a class="essay-card" href="#lire-{slug}">
  <p class="meta-line">{t(a["theme"])} · {t(a["dest"])} · {mins} min de lecture{(" · podcast " + str(max(1, round(PODS[slug]["secs"] / 60))) + " min") if slug in PODS else ""}</p>
  <h3>{t(title)}</h3>
  <p>{t(stand)}</p>
  <span class="go">Lire le dossier</span>
</a>''')
    essays.append(f'''<article class="essay" id="a-{slug}" aria-labelledby="a-{slug}-t" hidden>
  <a class="btn-ghost essay-back" href="#loin">Tous les dossiers</a>
  <header class="essay-head">
    <p class="eyebrow">{t(a["theme"])} · {t(a["dest"])}</p>
    <h2 class="essay-title" id="a-{slug}-t">{t(title)}</h2>
    <p class="standfirst">{t(stand)}</p>
    <p class="essay-meta">{mins} min de lecture{(' · <a href="#quiz-' + slug + '" class="qz-jump">quiz de ' + str(len(QUIZ[slug])) + ' questions en fin de dossier</a>') if slug in QUIZ else ""}</p>
    {pod_block(slug)}
  </header>
  <aside class="field" aria-label="Sur le terrain">
    <h3>Sur le terrain pendant le séjour</h3>
    <ul>{links}</ul>
  </aside>
  <div class="essay-body">{html_body}</div>
  {note}
  {quiz_block(slug)}
  <a class="btn-ghost essay-back" href="#loin">Tous les dossiers</a>
</article>''')
loin_html = ('<div id="essays-list"><div class="essays">' + "".join(cards) + '</div>'
             '<p class="loin-note">D\u2019autres dossiers sur La Réunion et Maurice pourront s\u2019ajouter ici au fil de la préparation.</p></div>'
             + "".join(essays))

# ---------- Sources ----------
srcs = []
for k, (title, url, what, date) in SOURCES.items():
    srcs.append(f'<li><a href="{url}" target="_blank" rel="noopener">{e(title)}</a><span>{t(what)} · vérifié le {date}</span></li>')

# ---------- Données pour la page ----------
labels = []
for k in ("reunion", "maurice", "sea"):
    for (txt, lon, lat, kind) in LABELS[k]:
        labels.append(dict(t=txt, lon=lon, lat=lat, k=kind))
trip = dict(
    days=[dict(id=f"j{d['n']}", n=d["n"], date=d["date"], short=date_short(d["date"]), title=d["title"], isl=d["isl"], pts=d["pts"]) for d in DAYS],
    acts=acts_json, places=places, labels=labels,
    logements=[dict(id=x["id"], s=x["s"], hote=x["hote"]) for x in LOGEMENTS], lgst=LG_ST,
)
geo_out = dict(islands={k: dict(land=v["land"], waterlines=v["waterlines"], bounds=v["bounds"]) for k, v in GEO["islands"].items()}, svg=GEO["svg"])
geo_out["terrain"] = json.load(open("terrain_index.json"))

# Animation de fond « Relief des deux îles » : courbes de niveau réelles (voir relief_fx.py)
FX = json.load(open("relief_fx.json"))
def fx_island(k):
    i = FX[k]
    vb = f'0 0 {i["w"]} {i["h"]}'
    return (f'<div class="fx-isl fx-{k}" style="aspect-ratio:{i["w"]}/{i["h"]}">'
            + "".join(f'<svg class="fx-l fx-{c}" viewBox="{vb}" preserveAspectRatio="xMidYMid meet"><path d="{i[c]}" pathLength="1"/></svg>'
                      for c in ("coast", "low", "high")) + '</div>')
fx_html = ('<div id="fx" aria-hidden="true" data-page="accueil">'
           + fx_island("maurice") + fx_island("reunion") + '</div>')

css = open("vendor/maplibre-gl.css").read()
app = open("app.js").read()
tpl = open("template.html").read()

def safe_json(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

html = (tpl.replace("/*__MAPLIBRE_CSS__*/", css)
        .replace("__TIMELINE__", "".join(cells))
        .replace("__TL_LEGEND__", "".join(leg))
        .replace("__TABLE__", "".join(tab_rows))
        .replace("__LOIN__", loin_html)
        .replace("__DAYS__", "\n".join(days_html))
        .replace("__RESA__", "".join(resa))
        .replace("__LOGEMENTS__", logements_html)
        .replace("__PRATIQUE__", "".join(prat))
        .replace("__SOURCES__", "".join(srcs))
        .replace("__TRIP_JSON__", safe_json(trip))
        .replace("__GEO_JSON__", safe_json(geo_out))
        .replace("__FX__", fx_html)
        .replace("__APP_JS__", app))
# Site de voyage privé : accessible par lien, mais pas dans les moteurs de recherche.
# noindex : pas d'indexation ; nofollow : liens non suivis ; noarchive / nosnippet : ni cache ni extrait ;
# noimageindex : images de la page non indexées. Doublé côté serveur par docs/.htaccess (en-tête X-Robots-Tag).
ROBOTS = '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">'

# Fragment publié comme artefact Claude (le squelette HTML est ajouté à la publication).
# L'artefact Claude ne permet pas les téléchargements : lien MP3 retiré de cette version (lecture seule).
frag = re.sub(r'<a class="pod-dl"[^>]*>.*?</a>', '', html)
open("reunion-maurice-2027.html", "w").write(ROBOTS + "\n" + frag)

# Version autonome (dossier docs/, pour GitHub Pages ou un hébergement web) : document HTML complet,
# avec titre, balise robots, polices et styles dans <head>.
# Hors artefact, les statuts sont enregistrés dans le navigateur (localStorage) et ne sont pas partagés.
cut = html.index("</style>") + len("</style>")
head_part, body_part = html[:cut], html[cut:]
assert head_part.lstrip().startswith("<title>") and "<nav" not in head_part
doc = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       + ROBOTS + '\n<meta name="referrer" content="strict-origin-when-cross-origin">\n'
       + head_part
       + '\n<style>img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>'
       + body_part + '\n</body>\n</html>\n')
open("../docs/index.html", "w").write(doc)
print("OK", round(len(html.encode()) / 1024), "Ko,", len(acts_json), "statuts,", len(places), "lieux")
