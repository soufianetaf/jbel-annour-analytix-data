# Fiche indicateur : créances clients et balance âgée

> **Statut : proposition, à valider par le directeur financier et la comptabilité.**

| Élément | Valeur |
|---|---|
| Domaine | Finance |
| Responsable métier | Directeur financier / comptabilité (à confirmer) |
| Source qui fait foi | Sage X3, dossier BASE1 : `GACCDUDATE` (échéances) |
| Tables | `marts.fct_echeances` (état actuel), `snapshots.snap_echeances_ouvertes` (photo quotidienne) |
| Grain | Une ligne = une échéance d'une pièce comptable |
| Fréquence | Copie incrémentale à chaque passage ; photo une fois par jour |

## Définitions

**Échéance** : date à laquelle une partie d'une facture (ou d'un avoir) doit être payée. Une facture payée en trois fois a trois échéances.

**Reste à payer** d'une échéance, en MAD (monnaie de la société) :

```
reste_a_payer = (montant - montant_payé) × signe
```

Positif : le client nous doit de l'argent. Négatif : nous lui devons (avoir, trop-perçu).

**Créances clients** : somme des restes à payer des échéances **clients** non soldées.

**Retard** d'une échéance ouverte, à la date du jour : `date du jour - date d'échéance`, en jours. Une échéance pas encore arrivée n'est pas en retard.

**Balance âgée** : les créances classées selon leur retard.

| Tranche | Retard |
|---|---|
| Non échu | échéance pas encore atteinte |
| 1 à 30 jours | |
| 31 à 60 jours | |
| 61 à 90 jours | |
| 91 à 180 jours | |
| 181 à 365 jours | |
| Plus de 365 jours | |

## Règles proposées

| Règle | Choix proposé | Pourquoi |
|---|---|---|
| Montant | En monnaie de la société (`AMTLOC_0`, `PAYLOC_0`), MAD | Les montants en devise ne s'additionnent pas |
| Signe | `SNS_0` | Comme pour les ventes, le signe est séparé du montant dans X3 |
| Échéance « soldée » | Reste à payer nul (au centime) | À rapprocher de l'indicateur de lettrage `FLGCLE_0` |
| Clients ou fournisseurs | Type de tiers (`BPRTYP_0`) et compte collectif (`SAC_0`) | La même table contient aussi les dettes fournisseurs |
| Échéances de plus d'un an | **Gardées et montrées à part** | 13 879 échéances échues depuis plus d'un an (cahier des charges, 5.1) : elles gonflent la balance âgée. C'est à la comptabilité de les lettrer, passer en pertes ou relancer, pas à Analytix de les cacher |

## Pourquoi une photo quotidienne

Sage X3 ne garde que l'état **actuel** des échéances : quand une facture est réglée, on ne sait plus qu'elle était ouverte hier. Pour suivre l'évolution des créances (le DSO, la balance âgée de la fin du mois dernier), il faut photographier chaque jour les échéances ouvertes. **Un jour sans photo est perdu pour toujours.**

## Rapprochement avec la source

- Copie : nombre d'échéances et total des montants, contre Sage X3.
- Indicateur : total des restes à payer clients, calculé dans Sage X3 avec la même règle, contre `marts.fct_echeances`.

## Points à valider

1. Quels comptes collectifs (`SAC_0`) sont des créances clients ?
2. Une échéance est-elle soldée quand le reste est nul, ou quand elle est lettrée (`FLGCLE_0`) ?
3. Les effets à l'encaissement (montants « en cours », `TMPLOC_0`) sont-ils considérés comme payés ?
4. Les tranches de la balance âgée conviennent-elles ?

## Premiers constats (25/11/2026, à présenter à la comptabilité)

| Tranche (clients) | Échéances | Reste à payer |
|---|---|---|
| Non échu | 403 | 53,40 M MAD |
| 1 à 90 jours | 160 | 3,31 M MAD |
| 91 à 365 jours | 2 102 | -19,72 M MAD |
| Plus de 365 jours | 9 698 | 20,92 M MAD |
| **Total** | **12 363** | **57,91 M MAD** |

- **9 698 échéances clients ouvertes depuis plus d'un an** : elles représentent 78 % des échéances ouvertes.
- **La tranche 181 à 365 jours est négative (-19,82 M MAD)** : ce sont vraisemblablement des encaissements non lettrés (règlements reçus mais pas rapprochés de leurs factures). Tant qu'ils ne sont pas lettrés, la facture d'un côté et le règlement de l'autre restent « ouverts » : la balance âgée par tranche est faussée, même si le total est juste.
- Le total des créances clients est identique à Sage X3, au centime (`ingestion.rapprochement --creances`).
