# Fiche indicateur : fiabilité des machines (MTTR, MTBF, TRS, impact des pannes)

> **Statut : proposition, à valider par le responsable maintenance et le responsable production.**

| Élément | Valeur |
|---|---|
| Domaine | Maintenance et production |
| Sources | Interventions de maintenance (`fct_interventions_maintenance`), bilans du jour des automates (`fct_machines_jour`) |
| Tables | `marts.agg_fiabilite_zone_mois` (zone × mois), `marts.agg_performance_machine_jour` (machine × jour) |
| API | `/v1/maintenance/fiabilite`, `/v1/machines/performance` |

Indicateurs croisés du cahier des charges : ils réunissent la maintenance (les pannes saisies) et les automates (les heures et la production). Aucune nouvelle copie.

## MTTR et MTBF (par zone et par mois)

```
panne            = ligne d'intervention faite machine à l'arrêt (état « ARR »)
MTTR (minutes)   = minutes d'arrêt / nombre de pannes        temps moyen de réparation
MTBF (heures)    = heures de marche / nombre de pannes        temps moyen entre deux pannes
```

Les heures de marche viennent des automates : **seulement pour le moulage, l'empileuse et la dépileuse**. Le four cuit en continu, la préparation et le séchoir n'ont pas de compteur d'heures : leur MTBF est vide, leur MTTR est calculé. Un mois à 0 heure de marche (l'automate n'a pas compté) donne aussi un MTBF vide, pas 0.

## TRS hors qualité (par machine et par jour)

```
disponibilité         = heures de marche / (heures de marche + heures d'arrêt)
cadence du jour       = production / heures de marche
cadence de référence  = 95e centile des cadences du jour de la machine (meilleure cadence démontrée)
performance           = cadence du jour / cadence de référence, au plus 1
TRS hors qualité      = disponibilité × performance
```

- **La cadence nominale des constructeurs n'est pas connue** : la référence est la meilleure cadence que la machine a réellement tenue (95e centile, pour écarter un jour exceptionnel). Elle se remplace par la cadence nominale dès qu'elle est connue.
- **La qualité n'est pas mesurée par machine** : le TRS est calculé sans elle, et la colonne le dit (`trs_hors_qualite`).
- Un jour sans aucune heure enregistrée : disponibilité, performance et TRS vides, pas 0 ni 1.

## Impact des pannes sur la production

```
production perdue estimée = minutes d'arrêt saisies par la maintenance / 60 × cadence de référence
```

Dans l'unité de la machine : étagères (moulage), wagons (empileuse), paquets (dépileuse).

## Constats (26/11/2026)

| Machine | Cadence de référence | Disponibilité | Performance | TRS hors qualité | Production perdue par les pannes depuis septembre |
|---|---|---|---|---|---|
| Moulage | 13,5 étagères/h | 69 % | 94 % | **69 %** | 382 étagères sur 15 198 (2,5 %) |
| Empileuse | 2,5 wagons/h | 77 % | 88 % | **72 %** | 75 wagons sur 2 959 (2,5 %) |
| Dépileuse | 46,7 paquets/h | 72 % | 88 % | **77 %** | 900 paquets sur 57 044 (1,6 %) |

1. **La disponibilité est la première perte** (69 % à 77 %) : c'est elle qu'il faut améliorer, plus que la cadence.
2. MTTR de septembre à novembre 2026 : de 19 à 45 minutes sur les machines de la chaîne, **52 à 64 minutes à la préparation**, la zone la plus lente à réparer.
3. MTBF du moulage : 39 h en septembre, **9 h en octobre** (38 pannes), 15 h en novembre.
4. **L'automate de la dépileuse ne compte plus ses heures depuis fin septembre 2026** : ni TRS ni MTBF depuis. À signaler à l'automatisme.
5. Les interventions ne sont saisies que depuis septembre 2026 : MTTR, MTBF et production perdue n'existent pas avant.

## Points à valider

1. La cadence nominale de chaque machine, pour remplacer la meilleure cadence démontrée.
2. Une panne = une intervention machine à l'arrêt : faut-il aussi compter les interventions curatives faites machine en marche ?
3. Le temps d'ouverture du TRS : le temps où l'automate était sous tension, ou les 24 heures du jour ?
4. Mesurer la qualité par machine (briques cassées au moulage, à l'empilage, au dépilage) pour un TRS complet.
