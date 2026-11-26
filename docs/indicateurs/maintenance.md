# Fiche indicateur : maintenance préventive et interventions

> **Statut : proposition, à valider par le responsable maintenance.**

| Élément | Valeur |
|---|---|
| Domaine | Maintenance |
| Responsable métier | Responsable maintenance (à confirmer) |
| Sources qui font foi | Serveur de l'usine : base `maintenance_2026` (préventif, interventions) ; base `maintenance` (demandes d'intervention seulement) |
| Tables | `marts.fct_controles_preventifs` (point × tournée), `marts.fct_interventions_maintenance` (ligne d'intervention), `marts.fct_pieces_maintenance` (pièce × ligne), `marts.fct_demandes_intervention` (demande), `marts.agg_maintenance_zone_jour` (zone × jour) |
| Copie | `uv run python -m ingestion.usine_maintenance` (10 tables, 3 copies, rapprochées) |

Jamais copiés : les noms d'intervenants et de contrôleurs, les identifiants des utilisateurs, les commentaires, anomalies, causes, constats et travaux en texte libre, les signatures.

## Zones

Six zones, écrites de plusieurs façons dans les applications et ramenées à un seul nom (macro `zone_usine`) : préparation, moulage (« Monobloc »), séchoir, four, empileuse, dépileuse.

## 1. Maintenance préventive

À chaque poste, une tournée par zone passe les points de contrôle de chaque équipement (« Contrôler le niveau d'huile des réducteurs », 1 840 points sur 535 équipements). Chaque point est **C** (conforme), **NC** (non conforme) ou vide (non rempli).

**Une seule tournée retenue par zone, poste et jour.** Une même tournée est souvent saisie plusieurs fois : jusqu'à 36 saisies, en brouillon ou validées, parfois sans aucun résultat. La tournée retenue est celle qui a des résultats, validée de préférence, puis la plus récemment modifiée. Sur 2 118 saisies, 928 sont retenues (86 125 points sur 92 589).

```
taux de réalisation = points remplis / points de la tournée
taux de conformité  = points conformes / points remplis
tournées faites     = postes (sur 3) dont la tournée a des résultats
```

## 2. Interventions sur panne

Une fiche par intervention, avec une ou plusieurs lignes : équipement, état de la machine, type de panne, type d'intervention, heures de début et de fin, pièces de rechange.

**Durée** = heure de fin - heure de début. Une fin avant le début passe minuit (+ 24 h). Au-delà de 12 h, c'est une erreur de saisie : la durée est vide. La durée saisie en texte (« 0h10 », « 10 min », « 3h et 50 min ») est gardée pour contrôle : elle correspond au calcul dans 602 cas sur 604 lisibles.

**Minutes d'arrêt** = durée des interventions faites machine à l'arrêt (état « ARR »).

| Code saisi | État de la machine |
|---|---|
| ARR | arrêt |
| EM | en marche |
| TM | à valider |

**Pièces de rechange** : lues dans la liste JSON de chaque ligne (`[{"code": "A02930", "qte": 2}]`). « RAS », « - », « Aucun » ne sont pas des pièces. Les codes sont ceux de Sage X3 quand ils existent : la clé article est la même que dans le stock et les achats.

## 3. Demandes d'intervention

Saisies dans l'ancienne base `maintenance`. Urgence « + » à « +++ » → 1 à 3.

```
heures avant intervention = début - panne
heures de remise en service = remise en service - panne
```

## Constats sur les données (26/11/2026)

1. **Préventif en service depuis août 2026** : quelques tournées en février et avril, puis 900 saisies en août. Taux de conformité moyen de 88 % à 97 % selon la zone ; les plus bas : **séchoir 83 %** (2 428 points non conformes) et **préparation 85 %** (1 655).
2. Les tournées ne couvrent pas tous les postes : en moyenne 1,2 poste sur 3 au four et à la dépileuse, 2,2 à l'empileuse.
3. **Interventions depuis septembre 2026** : 1 137 lignes, 412 heures d'intervention, dont **254 heures machine à l'arrêt**. Zone la plus touchée en arrêt : préparation (71 h), puis séchoir (56 h). Équipement le plus arrêté : broyeur 1 (14 h), en comptant aussi les broyeurs saisis « Broyeur N2 », « Broyeur 2 ».
4. Pannes surtout mécaniques (487 lignes), puis électriques (211). 57 % des interventions sont curatives, 13 % palliatives, 30 % sans type.
5. **L'équipement est saisi en texte libre** (« Broyeur 1 », « Broyeur N1 », « Broyeurs 1 et 2 ») et ne correspond jamais au nom de la liste des équipements : pas de lien avec le préventif ni avec le code Sage X3.
6. Pièces : 273 pièces sur 207 codes, dont 164 connus de Sage X3 ; les autres pointent vers l'article « Inconnu ».
7. Demandes d'intervention : 66 (hors essais), seulement 6 closes avec une date de remise en service (131 h en moyenne).
8. Non copiés : l'ancienne base `maintenance` pour le préventif (378 tournées, aucune en commun avec `maintenance_2026`), ses checklists électriques et ses contrôles d'étagères, les compteurs de durée de vie de la base `gmao` ; `suivi_interventions` (déjà dans les interventions).

## Points à valider

1. La règle de la tournée retenue (une par zone, poste et jour).
2. Sens de l'état « TM ».
3. Le temps d'arrêt doit-il venir de la maintenance (état ARR) ou des automates (coupures du moulage, fiche machines) ?
4. Peut-on imposer le choix de l'équipement dans une liste (celle du préventif, avec code Sage X3) au lieu du texte libre ?
5. L'ancienne base `maintenance` doit-elle encore être lue (demandes d'intervention, checklists) ?
