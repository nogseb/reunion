# La Réunion et Maurice, mai-juin 2027

Carnet de voyage en une page, pensé d'abord pour le téléphone : programme en tableau, programme jour par jour avec carte en relief, suivi des réservations, infos pratiques sourcées et dossiers de fond (« Pour aller + loin »).

Séjour du mercredi 19 mai au vendredi 4 juin 2027 : environ 10 jours à Maurice (ouest puis nord), le reste à La Réunion.

## Consulter le site

| Version | Où | Statuts de réservation |
|---|---|---|
| Artefact Claude (version de référence) | lien privé, partagé depuis Claude | partagés entre les personnes qui ont accès |
| GitHub Pages (optionnel) | dossier `docs/` | enregistrés dans le navigateur de chaque personne, non partagés |

Pour activer GitHub Pages : Settings → Pages → Source « Deploy from a branch » → branche `main`, dossier `/docs`.
Sur un compte GitHub gratuit, Pages n'est disponible que pour un dépôt public (voir la section Confidentialité).

## Structure

```
docs/                  site prêt à servir (GitHub Pages)
  index.html           page autonome générée
  terrain/             141 tuiles d'altitude (PNG terrarium, z5 à z12)
src/                   sources et générateur
  content.py           programme : 17 jours, activités, statuts, sources
  tab.py               vue tableau (accueil)
  articles.py          dossiers de la page « Pour aller + loin »
  template.html        gabarit, styles, navigation
  app.js               navigation, carte MapLibre, relief 3D, statuts
  site.py              assemble la page
  geo_build.py         traits de côte, lignes d'eau, lever et coucher du soleil
  terrain_build.py     tuiles de relief depuis Copernicus DEM
  *.json               données géographiques et lieux
  vendor/              feuille de style MapLibre GL 4.7.1
contenus/              articles en Markdown
```

## Mettre à jour le site

Prérequis : Python 3.10 ou plus.

```bash
pip install markdown shapely astral rasterio numpy pillow
cd src
python3 site.py          # régénère docs/index.html (et le fragment publié comme artefact)
```

Pour modifier le programme, éditer `src/content.py` (jours, horaires, statuts, sources) puis relancer `site.py`.
Pour ajouter un dossier, déposer le Markdown dans `contenus/` et le déclarer dans `src/articles.py`.

### Régénérer le relief (rarement utile)

1. Télécharger les 4 dalles Copernicus DEM GLO-90 dans `src/dem/` :
   - `Copernicus_DSM_COG_30_S21_00_E055_00_DEM.tif` et `Copernicus_DSM_COG_30_S22_00_E055_00_DEM.tif` (La Réunion)
   - `Copernicus_DSM_COG_30_S20_00_E057_00_DEM.tif` et `Copernicus_DSM_COG_30_S21_00_E057_00_DEM.tif` (Maurice)
   - source : `https://copernicus-dem-90m.s3.amazonaws.com/<nom sans .tif>/<nom>.tif`
2. `python3 terrain_build.py` (écrit `docs/terrain/` et `src/terrain_index.json`), puis `python3 site.py`.

### Régénérer les traits de côte

`python3 geo_build.py` relit `reunion_rings.json`, `maurice_rings.json` (extraits du GSHHG pleine résolution) et `places.json`, puis écrit `geo.json`. Le trait de côte GSHHG de La Réunion est recalé d'environ 1,2 km (voir `OFFSETS`).

## Statuts de réservation

Chaque activité porte un statut : réservé, à réserver, optionnel ou à arbitrer. La valeur par défaut est dans `content.py`.
Dans l'artefact Claude, une modification faite depuis la page est partagée avec les autres personnes ayant accès.
Dans la version GitHub Pages, elle reste dans le navigateur de la personne qui l'a faite.

## Confidentialité

La page contient des prénoms, des numéros de vol et les dates d'absence du domicile. Aucune adresse de logement n'y figure (commune uniquement).

Le site est conçu pour circuler **par lien partagé**, pas pour être trouvé sur un moteur de recherche :

| Mesure | Où | Effet |
|---|---|---|
| `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">` | `<head>` de `docs/index.html`, en tête du fragment artefact | pas d'indexation, ni cache, ni extrait, ni images indexées |
| En-tête HTTP `X-Robots-Tag` (mêmes valeurs) | `docs/.htaccess` | couvre aussi les tuiles PNG ; actif sur un hébergement Apache (OVHcloud mutualisé), ignoré par GitHub Pages |
| Aucun sitemap, aucun lien vers le site depuis ce dépôt | — | le site n'est pas signalé aux moteurs |

Points d'attention :

- Ne pas bloquer le site dans un `robots.txt` (`Disallow`) : un robot qui ne peut pas lire la page ne voit pas la consigne `noindex`, et l'adresse peut alors apparaître dans les résultats sans description.
- `noindex` est une consigne respectée par les grands moteurs (Google, Bing), pas une protection : toute personne qui a le lien peut ouvrir la page.
- Ces balises ne s'appliquent qu'au site. **Le dépôt GitHub lui-même, s'il est public, reste indexable** (README, `src/content.py`, etc.). Seul un dépôt privé l'évite ; GitHub Pages demande alors un abonnement payant.

### Héberger sur un domaine personnel (Apache, OVHcloud)

Copier le **contenu** du dossier `docs/` (y compris `.htaccess`, fichier caché) dans le sous-dossier choisi, par exemple `/rm/`, via FTP ou le gestionnaire de fichiers.

## Crédits et licences

- Relief : Copernicus DEM GLO-90, © DLR e.V. 2010-2014 et © Airbus Defence and Space GmbH 2014-2018, fourni dans le cadre de COPERNICUS par l'Union européenne et l'ESA.
- Traits de côte : GSHHG (Wessel et Smith), licence LGPL.
- Carte : MapLibre GL JS 4.7.1, licence BSD-3-Clause, chargée depuis jsDelivr (repli unpkg).
- Polices : Spectral, Atkinson Hyperlegible, IBM Plex Mono (Google Fonts, licence SIL OFL).
- Informations pratiques : sources et dates de vérification listées dans la page (Infos → Sources).
