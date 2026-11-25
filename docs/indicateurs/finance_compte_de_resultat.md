# Fiche indicateur : compte de résultat (CPC) mensuel

> **Statut : proposition, à valider par le directeur financier et le contrôle de gestion.**

| Élément | Valeur |
|---|---|
| Domaine | Finance / contrôle de gestion |
| Responsable métier | Directeur financier (à confirmer) |
| Source qui fait foi | Sage X3, dossier BASE1 : `GACCENTRYD` (lignes d'écritures), `GACCENTRY` (entêtes), `GACCOUNT` (plan comptable) |
| Table | `marts.fct_ecritures` (lignes), `marts.agg_compte_de_resultat_mois` (CPC mensuel) |
| Grain | `fct_ecritures` : une ligne d'écriture de la comptabilité générale. `agg_…` : compte × mois |
| Plan comptable | Plan comptable marocain (`MAR`) |

## Définitions

**Solde d'une ligne d'écriture**, en MAD :

```
solde = montant × sens        sens = +1 au débit, -1 au crédit
```

**Charges** : comptes de la classe 6. **Produits** : comptes de la classe 7.

**Résultat** = produits − charges = − (somme des soldes des classes 6 et 7)

Le CPC (compte de produits et charges) regroupe les comptes par rubrique, selon les deux premiers chiffres du compte :

| Rubrique | Produits | Charges |
|---|---|---|
| Exploitation | 71 | 61 |
| Financier | 73 | 63 |
| Non courant | 75 | 65 |
| Impôt sur les résultats | | 67 |

## Règles proposées

| Règle | Choix proposé | Pourquoi |
|---|---|---|
| Registre | **Comptabilité générale** (`LEDTYP_0 = 1`) | Le registre 2 (analytique) reprend les mêmes montants ventilés autrement : les additionner compterait deux fois |
| Catégorie de pièce | **Catégories 1 et 2** ; la catégorie 3 est exclue | Vérifié contre la `BALANCE` de Sage X3 : elle compte une pièce `IMS12` de catégorie 2 (16,65 M en 2024) et ignore une pièce `SMDIV` de catégorie 3 (simulation) |
| Statut | Provisoires **et** définitives (`STA_0` 1 et 2) | Une pièce non encore validée est déjà comptabilisée ; à confirmer |
| Clôture | **Pièces de type `CLOS1` exclues** du compte de résultat | La pièce de clôture (une par exercice, au 31/12) solde les comptes 6 et 7 : sans l'exclure, chaque exercice clôturé vaudrait 0. **Ce n'est pas le journal J42**, qui contient aussi des opérations diverses et des amortissements toute l'année |
| Date | Date comptable (`ACCDAT_0`) | |
| Mois | Mois civil de la date comptable | À confirmer : l'exercice comptable peut ne pas commencer en janvier |
| Libellés des lignes | **Non copiés** (`DES_0`) | Un libellé peut contenir un nom de personne (ex. avance au personnel) |

## Données sensibles

La paie est comptabilisée **par compte, pas par salarié** : aucune des 829 lignes des comptes de personnel (617, 443) ne porte de tiers (contrôle du 25/11/2026). Les écritures ne contiennent donc pas de salaire individuel. Ce contrôle est refait à chaque chargement par un test dbt.

## Rapprochement avec la source

Les classes 6 et 7, clôture comprise, sont comparées par exercice à la table **`BALANCE`** que Sage X3 tient à jour lui-même (lignes de total société seulement : la `BALANCE` a aussi une ligne par site). Deux chemins indépendants. Écart toléré : moins de 0,01 MAD par exercice. Le résultat hors clôture est affiché à côté.

```powershell
uv run python -m ingestion.rapprochement --resultat
```

## Points à valider

1. Que sont les pièces de catégorie 2 (`IMS12`, 12 par an) ? Amortissements mensuels ? Elles sont gardées, comme dans la `BALANCE`.
2. Les pièces provisoires (statut 1) entrent-elles dans le résultat présenté à la direction ?
3. L'exercice comptable commence-t-il le 1er janvier ?
4. Le regroupement en rubriques du CPC convient-il, ou faut-il un découpage plus fin (achats consommés, autres charges externes, charges de personnel…) ?

## Premiers constats (25/11/2026, à présenter à la comptabilité)

| Exercice | Résultat hors clôture |
|---|---|
| 2021 | 32,16 M MAD |
| 2022 | 201,62 M MAD |
| 2023 | 1,16 M MAD |
| 2024 | 1,07 M MAD |
| 2025 | 1,69 M MAD |
| 2026 (au 25/11) | 50,54 M MAD |

- Les classes 6 et 7 retrouvent la `BALANCE` de Sage X3 au centime sur les 6 exercices.
- **Ventes comptabilisées (comptes 711 et 712) contre CA net facturé (`fct_ventes`)**, en M MAD : identiques en 2022 (158,18) et proches en 2021 (56,14 / 56,19), mais écarts de -1,3 en 2025, +4,7 en 2024 et **-23,8 en 2023** (133,20 / 157,01). Les deux sont rapprochés de Sage X3 au centime : l'écart est dans Sage X3 (ventes comptabilisées sur d'autres comptes, écritures de vente manuelles, décalages de dates). À analyser avec la comptabilité ; ce contrôle croisé deviendra un test du domaine Direction.
- **Un avoir fournisseur de 164,95 M MAD** (`FR140830`, 20/12/2022) suivi d'une **facture fournisseur du même montant** (`FF161935`, 23/01/2023) : le résultat 2022 est gonflé d'autant, celui de 2023 diminué d'autant. Probable régularisation à cheval sur deux exercices : à expliquer.
- Les résultats 2023 à 2025 (1 à 2 M MAD) sont très inférieurs à celui de 2026 en cours (50,5 M MAD) : à rapprocher des opérations diverses de fin d'année (pièces `ODDIV`).
