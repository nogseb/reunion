# -*- coding: utf-8 -*-
"""Comparatif de location de voiture à l'aéroport de Maurice (page Suivi, onglet « Location de voiture »).
Prix « à partir de » publiés en 2026, convertis au taux du 19/10/2026 (1 € = 53,04 MUR ; 1 $ ≈ 0,89 €).
Ce ne sont pas des devis pour mai 2027."""

RELEVE = "19 octobre 2026"

HYPOTHESES = [
    "Prise à l'aéroport le vendredi 21 mai vers 11 h 30, retour le dimanche 30 mai vers 16 h 30 : 9 jours et 5 heures, donc 10 jours facturés chez presque tous les loueurs.",
    "Quatre adultes avec des sacs souples, les grosses valises restant à La Réunion : une berline ou un SUV compact suffit. Les minis (i10, Picanto) sont trop justes.",
    "Mai est un mois creux : DiscoverCars l'affiche autour de 27 $ par jour pour une économique.",
]

CHIFFRES = [
    ("Loueur local, 10 jours", "300 à 450 €"),
    ("Soit par personne", "75 à 115 €"),
    ("Loueur international", "600 à 1 000 €"),
    ("Essence, environ 45 l", "≈ 60 €"),
]

# loueur, type, véhicule, prix par jour, total 10 jours, par personne, note, recommandé
OFFRES = [
    ("Maki", "Local", "Nissan Almera, berline", "≈ 29 €", "≈ 290 €", "≈ 73 €",
     "Assurance tous risques, kilométrage illimité, 2ᵉ conducteur, GPS et livraison inclus. Franchise et caution non publiées.", True),
    ("Maki", "Local", "Suzuki Fronx ou Vitara Brezza, SUV compact", "≈ 37 €", "≈ 375 €", "≈ 94 €",
     "Mêmes inclusions. Trustpilot 4 sur 5 (230 avis), quelques litiges sur la caution ou un modèle différent.", True),
    ("Liberta", "Local", "VW Virtus, berline", "2 000 Rs (≈ 38 €)", "≈ 380 €", "≈ 94 €",
     "Conditions d'assurance et caution non publiées.", False),
    ("Liberta", "Local", "Toyota Corolla Touring, break", "2 400 Rs (≈ 45 €)", "≈ 450 €", "≈ 113 €",
     "Très grand coffre. Conditions non publiées.", False),
    ("RosCar", "Local", "Suzuki Ertiga, 7 places", "49 $ (≈ 44 €)", "≈ 435 €", "≈ 109 €",
     "Assurance en option, prépaiement demandé.", False),
    ("First Choice", "Local, via comparateur", "Suzuki Dzire, berline", "≈ 24 €", "≈ 240 €", "≈ 60 €",
     "Le moins cher, avec une assurance de base.", False),
    ("DiscoverCars", "Comparateur", "SUV, prix d'appel", "≈ 55 €", "≈ 550 €", "≈ 138 €",
     "Moyenne du marché, tous loueurs confondus.", False),
    ("Sixt, aéroport", "International", "Suzuki Ertiga, 7 places", "≈ 98 €", "≈ 980 €", "≈ 245 €",
     "Comptoir à l'aéroport, procédures standard.", False),
]

ASSURANCE = [
    "Franchise : chez Avis, même l'assurance collision optionnelle laisse 20 000 à 30 000 roupies à votre charge (environ 380 à 570 €). Pneus, jantes et dessous de caisse ne sont jamais couverts.",
    "Caution : environ 400 € bloqués sur une carte de crédit pour une petite voiture, 700 à 800 € pour un SUV. Les cartes de débit posent souvent problème.",
    "Certaines cartes bancaires haut de gamme couvrent la franchise d'une location payée avec elles : à vérifier avant de racheter la franchise chez le loueur.",
]

RECO = ("Un loueur local qui inclut l'assurance tous risques et le second conducteur, avec remise des clés à l'aéroport, "
        "en berline ou SUV compact. Maki est le mieux documenté ; Liberta est l'alternative pour le break Corolla et son grand coffre.")

A_CONFIRMER = [
    "Montant de la franchise et exclusions (pneus, vitres, dessous de caisse)",
    "Montant de la caution et type de carte accepté",
    "Remise des clés à l'aéroport et son éventuel coût",
    "Second conducteur inclus",
    "Carburant : plein rendu plein",
    "Tolérance sur l'heure de retour",
]

VOLS = ("Horaires Air Mauritius relevés en octobre 2026, à revérifier pour mai 2027 : de La Réunion vers Maurice à 7 h 00, 10 h 10 et 18 h 00 ; "
        "de Maurice vers La Réunion à 8 h 40 et 15 h 25. Avec le retour de 15 h 25, la voiture serait rendue vers 13 h : on perd le dimanche après-midi, "
        "mais avec une petite tolérance du loueur, la location peut passer à 9 jours au lieu de 10. Le vol de 10 h 10 à l'aller garde le programme du 21 mai intact.")

SOURCES = [
    ("Location de voiture à Maurice — DiscoverCars", "https://www.discovercars.com/en/mauritius"),
    ("Tarifs Maki Car Rental — Holidays-Mauritius.com", "https://www.holidays-mauritius.com/car-rental.html"),
    ("Flotte et tarifs — Liberta Car Hire", "https://carhire.liberta.mu/fleet/"),
    ("RosCar Mauritius", "https://roscarmauritius.com/"),
    ("First Choice, aéroport de Maurice — EconomyBookings", "https://www.economybookings.com/en/suppliers/first-choice-car-rental/mru"),
    ("Sixt, aéroport de Maurice — EconomyBookings", "https://www.economybookings.com/en/suppliers/sixt/mru"),
    ("Avis, aéroport de Maurice", "https://www.avis.com/fr/locations/af/mu/plaisance/mru"),
    ("Mauritius airport car rental guide — The Traveler (août 2026)", "https://www.thetraveler.org/mauritius-airport-car-rental-guide-insurance-deposits/"),
    ("Avis clients Maki Car Rental — Trustpilot", "https://pt.trustpilot.com/review/www.maki-car-rental.com"),
    ("Vols MK249, MK209, MK208 — FlightStats", "https://www.flightstats.com/v2/flight-tracker/MK/209"),
    ("Taux EUR/MUR — CurrencyConvert", "https://currencyconvert.online/eur/mur"),
]
