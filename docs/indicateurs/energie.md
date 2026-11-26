# Fiche indicateur : électricité, cos φ et énergie par tonne

> **Statut : proposition, à valider par le responsable électrique / méthodes et le contrôle de gestion.**

| Élément | Valeur |
|---|---|
| Domaine | Énergie |
| Responsable métier | Responsable électrique ou méthodes (à confirmer) |
| Sources qui font foi | Serveur de l'usine : base `electrique_data` (13 compteurs, un relevé toutes les 5 minutes depuis le 26/11/2025) ; base `Four_prod` (tonnes cuites, coke) |
| Tables | `marts.fct_electricite_jour` (compteur × jour), `marts.agg_energie_jour` (site × jour, par tonne) |
| Copie | `uv run python -m ingestion.usine_electricite` (13 tables rapprochées : nombre de lignes et somme de la puissance) |

## Les compteurs

| Niveau | Compteurs | Consommation moyenne par jour |
|---|---|---|
| Général | `transfo2`, `transfo1` | 15 900 et 9 600 kWh |
| Général | `entree` | 210 kWh : **ce n'est pas le total du site** |
| Par machine | `argile`, `sechoir`, `four`, `compresseur`, `prepa2`, `extrudeuse`, `prepa1`, `empileuse`, `depileuse`, `eclairage` (nommé `eclirage` dans la source) | de 9 000 (argile) à 175 kWh (éclairage) |

**Électricité du site = transformateur 1 + transformateur 2.** Ne jamais additionner tous les compteurs : la somme des compteurs par machine dépasse déjà celle des transformateurs (médiane : 108 %), ils se recouvrent.

## Définitions

**Consommation d'un compteur sur le jour J** = la « consommation de la veille » (`cons_P_total_j_1`) que le compteur affiche **le jour J+1**. Elle ne change pas de la journée (une seule valeur par jour pour 99 % des compteurs-jours). Le jour en cours n'a pas encore de consommation : elle est connue le lendemain.

On n'utilise **pas** l'index d'énergie (`cons_P_total`) : il se remet à zéro chaque jour vers minuit, recule 600 à 760 fois par compteur en un an, et fait des sauts aberrants (jusqu'à 10^14 sur le four et le compresseur). La somme de ses écarts positifs donne la moitié de la valeur du compteur.

**Valeur plausible** : entre 0 et puissance maximale du jour × 24 h (+10 % pour le pic tombé entre deux relevés), et au plus 100 000 kWh. Sinon `kwh` est vide, `kwh_valide` est faux et `kwh_brut` garde la valeur lue. Un transformateur à 0 kWh sur une journée entière est aussi une panne : le jour n'a pas d'électricité du site.

**Tranches tarifaires** (`cons_P_*_j_1`) : heures pleines, de pointe, creuses, données par le compteur, mêmes règles.

**cos φ** (facteur de puissance) : entre 0 et 1. En dessous de 0,8, le distributeur facture des pénalités. Par jour : moyenne des relevés valides, part des relevés sous 0,8, nombre de relevés hors de 0 à 1 (erreurs de mesure, exclues des moyennes).

**Énergie par tonne** (site, par jour) :

```
kWh par tonne  = (transformateur 1 + transformateur 2) / tonnes cuites par le four ce jour
coke par tonne = ratio de cuisson (kg de coke par tonne), dernier relevé du jour de l'automate du four
```

Les tonnes cuites viennent du bilan du jour du four (`fct_machines_jour`, fiche machines).

### Électricité par machine (`agg_electricite_machine_jour`)

```
kWh par tonne = kWh de la machine / tonnes cuites du site (même dénominateur : les machines se comparent)
kWh par unité = kWh de la machine / sa propre production
```

| Compteur | Production de l'automate |
|---|---|
| extrudeuse | étagères moulées (moulage) |
| four | tonnes cuites |
| empileuse | wagons |
| dépileuse | paquets |

### Prix du kWh (`agg_electricite_prix_mois`)

```
prix du kWh sur 12 mois = factures d'électricité (comptes 61251) des 12 mois / kWh estimés des 12 mois
kWh estimés             = kWh moyen d'un jour complet × nombre de jours
```

Deux précautions : les kWh manquent les jours de panne de collecte (d'où l'estimation), et **les factures sont comptabilisées irrégulièrement** (aucune en janvier, février et avril 2026, deux en décembre 2025 et mars 2026) : un prix mensuel ne voudrait rien dire. Le prix est calculé dès que les 12 mois ont 180 jours complets de compteurs.

### Énergie réactive et pénalités de cos φ

Le distributeur facture l'énergie réactive au-delà de **tan φ = 0,75** (cos φ = 0,8). La puissance réactive relevée par les compteurs (`Q_Tot`) est inutilisable : valeurs jusqu'à 10 millions, moyenne négative. Elle est recalculée :

```
tan φ = √(1 - cos²φ) / cos φ            (relevés au cos φ valide, puissance de 0 à 5 000 kW)
tan φ moyen du jour = Σ P × tan φ × durée / Σ P × durée
énergie réactive excédentaire = kWh du jour × Σ P × (tan φ - 0,75)⁺ × durée / Σ P × durée
```

Chaque relevé vaut le temps jusqu'au suivant, au plus 15 minutes. Les relevés valides ne couvrent que quelques heures par jour (collecte par à-coups) : le rapport mesuré sur ces heures est appliqué aux kWh du jour (`heures_cos_phi_mesurees` dit sur combien d'heures).

**Pénalité estimée** = énergie réactive excédentaire des transformateurs × tarif du contrat. Le tarif n'est pas connu : il se renseigne dans la variable dbt `tarif_energie_reactive_mad_kvarh` (`dbt/dbt_project.yml`). Tant qu'il est vide, la pénalité reste vide.

### Combustibles (`fct_combustibles_jour`)

Deux sources côte à côte, chacune avec ses propres tonnes :

| Source | Contenu | Période |
|---|---|---|
| Automates (font foi) | tonnes cuites, coke consommé et ratio de cuisson du four, électricité des transformateurs | depuis le 26/11/2025 |
| Rapport saisi (application de production) | électricité, fuel du four, coke micronisé, propane, charbon, grignons, production | mars 2025 - juillet 2026 |

Rapport saisi : le **dernier rapport du jour** est retenu (69 jours en ont plusieurs). Les saisies impossibles sont écartées : quantité négative, production hors de 1 à 3 000 t par jour, plus de 100 kg de coke, 0,1 t de fuel ou 0,1 de propane par tonne (31 rapports, test `assert_production_consommations_plausibles`).

## Constats sur les données (26/11/2026)

1. **Environ 35 kWh par tonne cuite** (médiane 34,8 ; 9 jours sur 10 entre 31 et 41), stable d'un mois à l'autre (32 à 40).
2. **Pannes de la collecte** : 20 à 30 jours par compteur ont une valeur négative ou en millions, **les mêmes jours sur tous les compteurs** (par exemple 21-22/12/2025, 8-9/02/2026, fin février 2026). S'y ajoutent des jours à 0 kWh sur les transformateurs alors que le four produit (octobre 2026 entier, décembre 2025). Seuls 214 jours sur 369 ont un kWh par tonne.
3. **cos φ bas** : moyenne sous 0,8 sur le transformateur 1 (0,75) et la plupart des machines (extrudeuse 0,56, prepa2 0,57) ; le transformateur 2 est à 0,82. À vérifier avec la facture : risque de pénalités.
4. **Mesures de cos φ invalides** nombreuses : dépileuse 17 432 relevés, entrée 13 881, extrudeuse 7 844.
5. Les consommations saisies dans l'application de production (en texte) vont de mars 2025 à juillet 2026 en pratique (une saisie isolée en octobre). Comparées aux automates les mêmes jours : **électricité saisie = 89 % du compteur** (46 jours), **production saisie = 91 % des tonnes cuites** (86 jours), **coke micronisé saisi = 94 % du coke de l'automate** (84 jours : il est donc bien en tonnes). Les automates font foi.
6. **Prix de l'électricité : 0,94 MAD le kWh** sur 12 mois (10,6 M MAD de factures pour 11,3 M kWh estimés).
7. **Électricité par unité** (médianes) : four 6,9 kWh par tonne cuite ; extrudeuse 4,4 kWh par étagère moulée ; empileuse 6,5 kWh par wagon. Rapportés aux tonnes du site : argile 12,5 kWh par tonne, séchoir 10,5, four 6,9.
8. **cos φ pondéré par l'énergie** : transformateur 1 à 0,86 (tan φ 0,59), transformateur 2 à 0,92 (tan φ 0,43). L'énergie réactive excédentaire vient presque toute du **transformateur 1** (67 000 kvarh sur un an, contre 1 000). Les machines les plus en cause : prépa 2 (tan φ 1,27) et extrudeuse (1,38). Une batterie de condensateurs sur ces départs serait à étudier.
9. Combustibles saisis (médianes par tonne) : **coke micronisé 20 kg**, fuel du four 0,0045 par tonne (4,5 kg si le fuel est saisi en tonnes), propane 0,005 par tonne (unités à confirmer). Charbon et grignons presque jamais saisis (« . »).

## Points à valider

1. Le total du site est-il bien transformateur 1 + transformateur 2 (et que mesure `entree`) ?
2. Unité des valeurs (kWh et kW, ou Wh et W) ? Les ordres de grandeur (35 kWh par tonne) indiquent kWh.
3. Seuil de pénalité du cos φ dans le contrat (0,8 retenu) ?
4. Les jours de panne de collecte peuvent-ils être repris (relevé manuel, facture du distributeur) ?
5. Tarif de l'énergie réactive dans le contrat (MAD par kvarh), et seuil de tan φ (0,75 retenu).
6. Unités saisies : fuel du four (tonnes ?), propane (bouteilles, kg ?). Que sont les « grignons » (`Consommation_Faitour`) ?
7. Le rapport de consommations de l'application de production est-il encore tenu depuis juillet 2026 ?
