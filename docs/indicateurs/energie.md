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

## Constats sur les données (26/11/2026)

1. **Environ 35 kWh par tonne cuite** (médiane 34,8 ; 9 jours sur 10 entre 31 et 41), stable d'un mois à l'autre (32 à 40).
2. **Pannes de la collecte** : 20 à 30 jours par compteur ont une valeur négative ou en millions, **les mêmes jours sur tous les compteurs** (par exemple 21-22/12/2025, 8-9/02/2026, fin février 2026). S'y ajoutent des jours à 0 kWh sur les transformateurs alors que le four produit (octobre 2026 entier, décembre 2025). Seuls 214 jours sur 369 ont un kWh par tonne.
3. **cos φ bas** : moyenne sous 0,8 sur le transformateur 1 (0,75) et la plupart des machines (extrudeuse 0,56, prepa2 0,57) ; le transformateur 2 est à 0,82. À vérifier avec la facture : risque de pénalités.
4. **Mesures de cos φ invalides** nombreuses : dépileuse 17 432 relevés, entrée 13 881, extrudeuse 7 844.
5. Les consommations saisies dans l'application de production (`stg_production__consommations`, en texte) couvrent mars 2025 à octobre 2026 ; 360 rapports sur 389 ont une électricité lisible, 73 un coke lisible. Elles ne servent pas au calcul : les compteurs font foi.

## Points à valider

1. Le total du site est-il bien transformateur 1 + transformateur 2 (et que mesure `entree`) ?
2. Unité des valeurs (kWh et kW, ou Wh et W) ? Les ordres de grandeur (35 kWh par tonne) indiquent kWh.
3. Seuil de pénalité du cos φ dans le contrat (0,8 retenu) ?
4. Les jours de panne de collecte peuvent-ils être repris (relevé manuel, facture du distributeur) ?
