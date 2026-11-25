# Fiche indicateur : stock valorisé et mouvements de stock

> **Statut : proposition, à valider par le responsable magasin et le contrôle de gestion.**

| Élément | Valeur |
|---|---|
| Domaine | Stock / magasin |
| Responsable métier | Responsable magasin et contrôle de gestion (à confirmer) |
| Sources qui font foi | Sage X3, dossier BASE1 : `ITMMVT` (stock et coût moyen par article et site), `STOJOU` (journal des mouvements) |
| Tables | `marts.fct_stock_article` (état actuel), `snapshots.snap_stock_jour` (photo quotidienne), `marts.fct_mouvements_stock` (mouvements) |

## Définitions

**Stock physique** d'un article sur un site : quantité en unité de stock (`PHYSTO_0`), hors stock en contrôle et rejeté.

**CMUP** : coût moyen unitaire pondéré de l'article sur le site (`AVC_0`), recalculé par Sage X3 à chaque entrée.

**Stock valorisé** = stock physique × CMUP, en MAD.

**Mouvement de stock** : une entrée ou une sortie d'un article sur un site, avec sa quantité (positive à l'entrée, négative à la sortie) et sa valeur (`AMTVAL_0`).

**Rotation** d'un article sur une période = sorties valorisées / stock valorisé moyen. **Article dormant** : article en stock sans aucune sortie depuis 12 mois.

## Pourquoi une photo quotidienne

Sage X3 ne garde que le stock **actuel** (`ITMMVT`). Le stock d'un jour passé peut être recalculé à partir des mouvements, mais le calcul est fragile : mouvements corrigés après coup, CMUP qui change. La photo du stock de chaque jour est donc prise dès maintenant (cahier des charges, 8.4 d). **Un jour sans photo est perdu pour toujours.**

## Rapprochement avec la source

- Copies : nombre de lignes, quantités et valeurs, contre Sage X3.
- Indicateur : stock valorisé total par site, calculé dans Sage X3 avec la même règle, contre `marts.fct_stock_article`.

## Points à valider

1. Le stock valorisé inclut-il le stock en contrôle (`CTLSTO_0`) et le stock rejeté (`REJSTO_0`) ?
2. La valorisation au CMUP est-elle la méthode retenue par le contrôle de gestion (ou le dernier prix d'achat) ?
3. Signification des types de mouvement (`TRSTYP_0`, de 1 à 35) : réceptions, livraisons, sorties diverses, transferts…
4. Le stock valorisé du site 101 calculé ainsi atteint **598 M MAD** : est-ce plausible, ou des CMUP sont-ils aberrants (comme le coût de revient des factures, cahier des charges 5.1) ?

## Premiers constats (25/11/2026, à présenter au magasin et au contrôle de gestion)

- Copie conforme : 13 917 articles × sites et 1 195 601 mouvements, identiques à Sage X3 ; stock valorisé par site identique au centime.
- **La photo quotidienne du stock a démarré le 25/11/2026** (3 388 articles en stock).
- **Le stock valorisé au CMUP n'est pas présentable en l'état** : 599 M MAD, dont **535 M MAD pour 10 articles**, presque tous des **en-cours de fabrication** au CMUP aberrant :

| Article | Désignation | Unité | CMUP | Valeur |
|---|---|---|---|---|
| `ES_B12/50` | En cours de séchage B12/50 | étagère | 1 551 305 MAD | 248,2 M |
| `B12/50CUIT` | Semi-fini biscuit B12/50 | wagon | 7 066 867 MAD | 183,7 M |
| `EM_B12/25` | Semi-fini empilé B12/25 | wagon | 391 174 MAD | 24,3 M |
| `B12/25CUIT` | Semi-fini biscuit B12/25 | wagon | 876 395 MAD | 18,4 M |
| `A00146` | Brique 250/200/150 (B12) | unité | 193,61 MAD | 16,3 M |

  Hors en-cours, le stock vaut **70,1 M MAD**. Le test `assert_stock_cmup_plausible` liste à chaque chargement les articles qui pèsent plus de 5 % du stock de leur site.
- **1 403 articles dormants** (en stock, sans sortie depuis un an) : 32,2 M MAD.
- **Les mouvements de stock n'ont pas de section analytique** : les sorties par service ne peuvent pas venir de Sage X3. Elles viendront de l'application Magasin de l'usine (demandes de sortie par service et affectation).
- Les sorties valorisées de 2025 atteignent 6,4 milliards MAD, gonflées par les transferts internes d'en-cours au CMUP aberrant : à ne pas utiliser tant que les CMUP ne sont pas corrigés.
