# Fiche indicateur : production par poste, réalisé contre objectif

> **Statut : proposition, à valider par le responsable production.**

| Élément | Valeur |
|---|---|
| Domaine | Production |
| Responsable métier | Responsable production (à confirmer) |
| Source qui fait foi | Serveur de l'usine, base **`production_2026`** (schéma `production`) |
| Tables | `marts.fct_production_poste` (zone × poste), `marts.fct_fiches_poste` |
| Grain | `fct_production_poste` : une zone × un poste (date, shift, équipe) |

## La base qui fait foi

Deux bases existent : `production` (ancienne, jusqu'au 02/03/2026) et `production_2026`. **Seule `production_2026` est lue** : vérifié le 25/11/2026, elle contient déjà 1 122 des 1 123 fiches de l'ancienne base et 4 343 des 4 348 lignes de production, avec les mêmes valeurs. Lire les deux compterait ces postes deux fois.

## Définitions

**Poste** : une période de travail d'une équipe, identifiée par la date, le shift (07h-15h, 15h-23h, 23h-07h) et l'équipe (A, B, C, D). Une **fiche de fin de poste** est saisie par poste.

**Zones** : monobloc, empileuse, dépileuse, dépileuse vrac, four. Chaque zone a un objectif par poste.

**Réalisé** d'une zone sur un poste : la quantité saisie (`saisie`). **Objectif** : l'objectif saisi pour ce poste (`objectif`), à défaut l'objectif de la zone.

**Taux de réalisation** = réalisé / objectif.

## Règles proposées

| Règle | Choix proposé | Pourquoi |
|---|---|---|
| Fiches supprimées | Exclues (`deleted_at` renseigné) | 24 fiches supprimées dans l'application |
| Poste saisi plusieurs fois | **Une seule fiche par (date, shift, équipe) : la plus récemment modifiée** ; les autres sont marquées doublon et exclues des totaux | 33 postes saisis plusieurs fois (148 fiches) : sans règle, leur production est comptée plusieurs fois. Règle à valider avec la production |
| Objectif vide ou nul | Taux de réalisation vide | 20 % des lignes sans objectif (cahier des charges, 5.2) |

## Points à valider

1. Unité du réalisé et de l'objectif par zone (étagères, wagons, paquets ?).
2. La règle de dédoublonnage (fiche la plus récente) convient-elle ?
3. **L'application de production n'est plus utilisée depuis le 25/04/2026** (fiches et lignes de production s'arrêtent ensemble) : où la production par poste est-elle saisie depuis mai (cahier des charges, 5.2) ?

## Premiers constats (25/11/2026, à présenter au responsable production)

- Copie conforme : 8 tables de `production_2026`, identiques à la source. Seule cette base est lue : elle contient l'historique de l'ancienne base `production` (1 122 fiches sur 1 123, 4 343 lignes sur 4 348, mêmes valeurs).
- **L'application de production n'est plus utilisée depuis fin avril 2026.** Les fiches vont du 11/03/2025 au 25/04/2026 ; les rares lignes créées après (juillet, octobre) sont rattachées à des fiches de mars. Il n'y a donc **aucune donnée de production par poste depuis mai 2026** : où est-elle saisie ?
- **Dédoublonnage** : 1 152 fiches, dont **1 006 retenues**, 87 doublons, 35 incomplètes (sans date, shift ou équipe) et 24 supprimées. Un même poste (29/12/2025, 07h-15h, équipe B) a été saisi 20 fois.
  - Sans dédoublonnage, le réalisé du monobloc serait **surévalué de 15 %** (73 375 au lieu de 64 016).
  - Après dédoublonnage : au plus 93 postes par mois, soit 3 postes par jour (cohérent).
- **Monobloc, réalisé contre objectif** : 100 à 124 % de mai à décembre 2025, puis 81 % en janvier 2026, 67 % en février, 39 % en avril.
- **Unités à confirmer** : pour l'empileuse (réalisé moyen 93 pour un objectif de 17) et le four (35 pour 15), réalisé et objectif ne semblent pas dans la même unité : le taux de réalisation de ces zones n'est pas fiable.
- **Principales raisons d'écart** : mécanique (450), gestion de production (398), électrique (342), manque de wagons vides (218), retard de déplacement des wagons (191), manque d'étagères vides (140).
- 20 lignes de production sans fiche (test en avertissement).
- Les noms de colonnes accentués des consommations ont été abîmés par dlt (`Consommation_Électrique` devient `consommation_lectrique`) : à traiter à l'étape énergie.
