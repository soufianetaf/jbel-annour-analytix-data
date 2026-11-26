# Fiche indicateur : équilibre production, stock et ventes des briques

> **Statut : proposition, à valider par le contrôle de gestion et la logistique.**

| Élément | Valeur |
|---|---|
| Domaine | Stock, production, ventes |
| Sources | Automate du four (`fct_machines_jour`), mouvements de stock Sage X3 (`fct_mouvements_stock`), stock actuel (`fct_stock_article`), ventes (`agg_marge_type_brique_mois`) |
| Table | `marts.agg_equilibre_briques_mois` (mois) |
| API | `/v1/stock/equilibre-briques` |

Indicateur croisé du cahier des charges : ce qui est produit, stocké et vendu chaque mois, en tonnes.

## Définitions

| Colonne | Définition |
|---|---|
| `tonnes_cuites` | Tonnes cuites par le four, d'après son automate (depuis le 26/11/2025) |
| `production_declaree` | Entrées de production dans Sage X3 (mouvements de type 5) |
| `livraisons` | Sorties de livraison dans Sage X3 (type 4) |
| `tonnes_vendues` | Factures et avoirs des articles briques |
| `stock_fin_mois` | Stock d'aujourd'hui moins les mouvements postérieurs à la fin du mois |
| `ratio_declaree_cuite` | Production déclarée / tonnes cuites (1 = identiques) |

- Les quantités Sage X3 sont en unités, passées en tonnes avec le poids de chaque article (fiche coût de revient).
- **Le stock passé est reconstitué** : Sage X3 ne garde que le stock d'aujourd'hui. Stock de fin de mois = stock actuel - mouvements des mois suivants. Les photos quotidiennes du stock (`snap_stock_jour`, depuis le 25/11/2026) le confirmeront.
- Les transferts entre dépôts (types 1 et 2) s'annulent : ils ne changent pas le stock total.

## Constats (26/11/2026)

1. **Livraisons et ventes facturées concordent** à moins de 0,1 % chaque mois (par exemple octobre 2026 : 37 658 t livrées, 37 590 t facturées). Les deux circuits de Sage X3 sont cohérents. Novembre est bas côté ventes (4 269 t) : la facturation du mois n'est pas encore passée.
2. **Production déclarée dans Sage X3 et tonnes cuites diffèrent** : de 87 % à 134 % selon le mois (octobre 2026 : 25 623 t déclarées pour 19 071 t cuites). La déclaration de production dans X3 n'est pas faite au jour le jour, ou pas sur les mêmes quantités que l'automate. À voir avec la production et la logistique.
3. Stock de briques à fin de mois : entre 7 000 et 19 500 t ; **8 983 t aujourd'hui** (6 043 t de B8, 1 843 t de B12, 1 064 t de B10).

## Points à valider

1. Sens des types de mouvement Sage X3 (5 = production, 4 = livraison, 1 et 2 = transferts) avec la logistique.
2. Quand et sur quelle base la production est-elle déclarée dans Sage X3 ?
3. Le stock de briques compte-t-il les briques en cours (dans le four, au séchoir) ?
