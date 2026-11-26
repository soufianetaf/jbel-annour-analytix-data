# Fiche indicateur : trésorerie et règlements

> **Statut : proposition, à valider par le directeur financier.**

| Élément | Valeur |
|---|---|
| Domaine | Finance / trésorerie |
| Responsable métier | Directeur financier (à confirmer) |
| Sources qui font foi | Sage X3, dossier BASE1 : lignes d'écritures des comptes de trésorerie (`GACCENTRYD`), règlements (`PAYMENTH`) |
| Tables | `marts.agg_tresorerie_jour` (soldes), `marts.fct_reglements` (règlements) |

## Définitions

**Comptes de trésorerie** (plan comptable marocain, classe 5) :

| Préfixe | Contenu |
|---|---|
| 511 | Chèques et valeurs à encaisser |
| 514 | Banques |
| 516 | Caisses |
| 552 | Crédits de trésorerie (passif) |
| 554 | Banques, soldes créditeurs (passif) |

**Solde d'un compte au jour J** : somme des soldes (débit - crédit) de ses écritures de l'exercice de J, **à-nouveaux compris**, jusqu'à J inclus.

Pourquoi « de l'exercice » : au 1er janvier, Sage X3 reporte le solde de chaque compte de bilan par une écriture d'à-nouveaux (pièces `RANX1`). Additionner toutes les années depuis 2021 compterait ce report une fois par an.

**Trésorerie nette** = somme des soldes des comptes 51 moins les crédits de trésorerie (55).

**Règlement** : un encaissement (client) ou un décaissement (fournisseur, impôt, salaire global…), saisi dans Sage X3. Montant positif pour un encaissement, négatif pour un décaissement.

## Données sensibles

Les règlements contiennent des RIB (`XRIB_0`, `YRIBENDO_0`), la banque du tiers (`CHQBAN_0`), des numéros de chèque et l'adresse du tiers. **Copie en liste fermée : rien de tout cela n'est copié.** Le code banque copié (`BAN_0` : `B01`, `CAISS`…) est le compte bancaire **de l'entreprise**, pas celui du tiers.

## Rapprochement avec la source

Solde de fin d'exercice de **chaque** compte de trésorerie, contre la `BALANCE` de Sage X3. Trois précautions, toutes vérifiées sur les données :

- la `BALANCE` a une ligne par site et par tiers **et** une ligne de total : on ne lit que le total (sinon les comptes de chèques et d'effets, suivis par client, comptent double) ;
- l'exercice suivant (2027) y contient déjà le report automatique des soldes : on ne compare que les exercices commencés ;
- l'exercice d'une écriture est déduit de sa **date** : une pièce datée du 04/04/2025 était saisie sur l'exercice 2024.

```powershell
uv run python -m ingestion.rapprochement --tresorerie
```

## Points à valider

1. La liste des comptes de trésorerie est-elle complète (comptes 5115, 5541…) ?
2. Les valeurs à encaisser (511) font-elles partie de la trésorerie présentée à la direction ?
3. Le budget de l'entreprise existe-t-il hors de Sage X3 (fichier Excel) ? La table `BUD` de Sage X3 ne contient que 70 lignes.

## Premiers constats (25/11/2026, à présenter au directeur financier)

Position à ce jour, exercice 2026 (M MAD) :

| Famille | Solde |
|---|---|
| Caisses (516) | **21,88** |
| Valeurs à encaisser (511) | 16,80 |
| Banques (514) | -2,82 |
| Crédits de trésorerie (552) | 1,58 |

- Les soldes de fin d'exercice des comptes 51 et 55 retrouvent la `BALANCE` de Sage X3 au centime, compte par compte, de 2021 à 2026.
- **21,88 M MAD en caisse** : montant très peu plausible pour des espèces. Probablement des encaissements en espèces enregistrés en caisse mais jamais versés en banque dans Sage X3 (ou versés sans écriture de transfert). À rapprocher de l'inventaire physique des caisses.
- **Banque à -2,82 M MAD** alors que la caisse est très positive : à rapprocher des relevés bancaires (`XRELBANK`).
- Un crédit de trésorerie (passif) en solde **débiteur** (+1,58 M MAD) : à vérifier.
- **Au 31/12, `agg_tresorerie_jour` vaut 0** : la pièce de clôture (CLOS1) solde les comptes de trésorerie, les à-nouveaux du 1er janvier les rouvrent. C'est exactement la `BALANCE` de Sage X3 (le rapprochement passe), mais pour une position de fin d'année il faut lire le 30/12 ou `agg_direction_mois`, qui calcule la trésorerie de fin de mois sans la clôture (constaté le 26/11/2026).
- **16 lignes d'écritures datées de janvier 2027** et **1 pièce saisie sur l'exercice 2024 mais datée du 04/04/2025** (`1010409DECAI000911`) : signalées par deux tests dbt en avertissement.
