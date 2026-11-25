# Fiche indicateur : chiffre d'affaires net (CA net)

> **Statut : proposition, à valider par le directeur commercial et le contrôle de gestion.**
> Tant qu'elle n'est pas validée, le chiffre est calculé mais ne doit pas être présenté comme officiel.

| Élément | Valeur |
|---|---|
| Domaine | Commercial / Finance |
| Responsable métier | Directeur commercial (à confirmer) |
| Source qui fait foi | Sage X3, dossier BASE1 : `SINVOICE` (entêtes) et `SINVOICED` (lignes) |
| Table | `marts.fct_ventes` |
| Grain | Une ligne = une ligne de facture ou d'avoir |
| Fréquence de mise à jour | Toutes les 2 heures (cible), aujourd'hui au lancement de l'ingestion |

## Définition

**Le CA net est le total hors taxes des factures, moins le total hors taxes des avoirs, sur la période.**

```
CA net = Σ montant_ht_signe
       = Σ (montant HT de la ligne × signe du document)
```

| Règle | Choix proposé | Pourquoi |
|---|---|---|
| Hors taxes ou TTC | **Hors taxes** | La TVA n'est pas un revenu de l'entreprise |
| Avoirs | **Déduits** (signe -1, colonne `SNS_0`) | Dans Sage X3, le montant d'un avoir est positif : sans le signe, un avoir **augmenterait** le CA |
| Pro forma (`PRF`) | **Exclues** | Facture provisoire, sans valeur comptable |
| Date de rattachement | **Date comptable** de l'entête (`ACCDAT_0`) | C'est la date qui rattache le document à une période comptable, comme dans les états de Sage X3 |
| Société | Toutes celles de BASE1 (aujourd'hui uniquement `100`, Jbel Annour) | |
| Devise | MAD (tous les documents actuels) | Un test signale tout document dans une autre devise |
| Statut du document | Tous les statuts | À confirmer : 8 documents ont le statut 1 (non validé ?) |

## Rapprochement avec la source

Le CA net par année calculé dans l'entrepôt (à partir des **lignes**) est comparé au même calcul fait directement dans Sage X3 (à partir des **entêtes**). Écart toléré : **moins de 0,01 MAD** par année.

```powershell
uv run python -m ingestion.rapprochement --ca
```

## Points à valider

1. Date comptable ou date de facture ?
2. Les 8 documents au statut 1 doivent-ils être comptés ?
3. Les ventes du site 102 (négoce) sont-elles dans le CA présenté à la direction, ou séparées ?
4. Le CA est-il suivi par représentant **de la ligne** (`REP1_0`) ou **du client** (fiche client) ?
