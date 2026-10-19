# -*- coding: utf-8 -*-
"""Vue tableau : libellés courts par jour, reliés aux statuts quand ils en ont un."""

GROUPS = [
    ("Départ · 19 et 20 mai", "reunion", 1, 2),
    ("Maurice, côte ouest · 21 au 25 mai", "maurice", 3, 7),
    ("Maurice, côte nord · 26 au 30 mai", "maurice", 8, 12),
    ("La Réunion · 31 mai au 3 juin", "reunion", 13, 16),
    ("Retour · 4 juin", "transit", 17, 17),
]

TAB = {
    1: [("Vol AF7419 Toulouse → Paris", "j1-vol"), ("Vol AF0672 Paris → Saint-Denis", "j1-vol2")],
    2: [("Arrivée à 12 h 20", None), ("Repos", None), ("Barachois au coucher du soleil", "j2-barachois")],
    3: [("Vol vers Maurice", "j3-vol"), ("Voiture de location", "j3-voiture"), ("Biscuiterie Rault", "j3-rault"),
        ("Blue Bay en bateau à fond de verre", "j3-bluebay"), ("Installation à La Gaulette", "j3-baseouest")],
    4: [("Morne Brabant avec guide", "j4-guide"), ("Route de l'Esclave", None), ("Rhumerie de Chamarel", "j4-rhum"),
        ("Sept Couleurs et cascade", None), ("Ebony Forest", "j4-ebony")],
    5: [("Randonnée au choix", "j5-rando"), ("Grand Bassin", None), ("Plaine Champagne", None), ("Point de vue des Gorges", None)],
    6: [("Kayak vers l'île aux Bénitiers", "j6-kayak"), ("Plage publique du Morne", None)],
    7: [("Rhum et vanille à Saint-Aubin", "j7-staubin"), ("Rochester Falls", None), ("Gris-Gris et Roche qui pleure", None), ("Prairie Beach", None)],
    8: [("Maison Eurêka", "j8-eureka"), ("Aapravasi Ghat", "j8-aapravasi"), ("Marché central", None), ("Caudan", None),
        ("Coucher de soleil à Flic-en-Flac", "j8-flic")],
    9: [("Île aux Cerfs en navette lente", None), ("Kayak en bonus, si mer calme", "j9-kayak"), ("Belle Mare", None),
        ("Installation côte nord", "j8-basenord")],
    10: [("Île d'Ambre en kayak de mer", "j10-ambre"), ("Pereybère", None), ("Rooftop The Cloud au coucher du soleil", "j10-cloud"),
         ("Dîner à La Rougaille Créole", None), ("Variante : îlots du nord en bateau rapide", "j10-ilots")],
    11: [("Pamplemousses", None), ("L'Aventure du Sucre", None), ("La Table du Château", "j11-table"),
         ("Château de Labourdonnais", None), ("Dîner à Grand Baie", None)],
    12: [("Messe à Cap Malheureux", "j12-messe"), ("Poisson grillé et Mont-Choisy", None), ("Vol vers La Réunion", "j12-vol")],
    13: [("Pont de la Rivière de l'Est", None), ("Tunnel de lave 2004, visite découverte", "j13-tunnel"), ("Vanille au Tremblet", "j13-vanille"),
         ("Cap Méchant", None), ("Jardin des Parfums et des Épices", "j13-epices"), ("Cascade de Grand Galet", None)],
    14: [("Parapente", "j14-parapente"), ("Jardin de Mascarin", None), ("Gouffre de l'Étang-Salé", None),
         ("Plateforme de verre de Bois-Court", None), ("Skywalk", "j14-skywalk")],
    15: [("Temple du Colosse", None), ("Voile de la Mariée", None), ("Hell-Bourg", None), ("Maison Folio", "j15-folio"),
         ("Mare à Poule d'Eau", None)],
    16: [("Jardin de l'État", None), ("Musée Léon-Dierx", "j16-dierx"), ("Grand Marché", None), ("Lieux de culte", None),
         ("Street art", None), ("Vol AF0673", "j16-vol")],
    17: [("Vol AF7402 Paris → Toulouse", "j17-vol"), ("Arrivée à 8 h 50", None)],
}
