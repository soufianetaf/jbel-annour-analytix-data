# Fiche indicateur : circuit d'achat, délais et dépenses fournisseurs

> **Statut : proposition, à valider par le responsable achats et le contrôle de gestion.**

| Élément | Valeur |
|---|---|
| Domaine | Achats |
| Responsable métier | Responsable achats (à confirmer) |
| Source qui fait foi | Sage X3, dossier BASE1 : demandes d'achat (`PREQUIS`, `PREQUISD`), commandes (`PORDER`, `PORDERQ`), réceptions (`PRECEIPTD`), factures fournisseurs (`PINVOICE`, `PINVOICED`), fournisseurs (`BPSUPPLIER`) |
| Tables | `marts.fct_cycle_achat`, `marts.fct_achats_factures`, `marts.dim_fournisseur` |

## Définitions

**Circuit d'achat** : demande d'achat (DA) → commande au fournisseur (BC) → réception → facture.

`fct_cycle_achat` a une ligne par **ligne de commande**. Chaque ligne porte la date de chaque étape, ce qui permet de mesurer les délais :

| Délai | Calcul |
|---|---|
| DA → commande | date de commande - date de la demande d'achat d'origine |
| Commande → réception | date de la première réception - date de commande |
| Réception → facture | date comptable de la première facture - date de la première réception |
| Retard de livraison | date de la première réception - date de réception prévue (si positif) |

**Taux de service** d'une ligne : quantité reçue / quantité commandée.

**Dépense d'achat** (`fct_achats_factures`) : montant HT des factures fournisseurs, avoirs déduits, à la date comptable.

**Prix d'achat** d'un article chez un fournisseur : prix net unitaire de la ligne de facture.

## Données sensibles

- Fiche fournisseur : la banque (`PAYBAN_0`) n'est pas copiée.
- Entêtes de commande, de réception et de facture : nom et adresse des tiers non copiés (le nom vient de la fiche fournisseur).
- Textes libres des lignes (`LINTEX_0`) non copiés.

## Rapprochement avec la source

- Copies : nombre de lignes et montants, table par table.
- Indicateur : dépense HT par année, calculée dans Sage X3 sur les entêtes de factures, contre `fct_achats_factures` (lignes).

## Points à valider

1. Une commande sans demande d'achat est-elle normale (achats directs) ?
2. Le délai commande → réception se mesure-t-il à la première réception ou à la réception complète ?
3. Le service demandeur est-il bien la section analytique `CCE_0` de la demande d'achat ?
4. La table `BUDPURAUD` (43 000 lignes) suit-elle les budgets d'achat ? Ses colonnes (pièce, compte, section, quantité) ressemblent à une trace d'engagements : à confirmer avant de l'utiliser pour les dépassements de budget.

## Premiers constats (25/11/2026, à présenter au responsable achats et à la comptabilité)

- Copie conforme : les 9 tables du circuit sont identiques à Sage X3. Dépense d'achat par année (lignes de factures, en MAD) identique au centime de 2021 à 2026.
- **Le lien DA → commande est dans la table `PREQUISO`**, pas dans les lignes de commande (champs d'origine vides sur les 52 790 lignes).
- **Les demandes d'achat ont quitté Sage X3** : part des lignes de commande sans DA dans X3, 41 % en 2023, 54 % en 2024, **98 % en 2025, 100 % en 2026**. Le circuit des DA (avec validation) est désormais dans l'application `espace_magasin` de l'usine : le délai DA → commande devra venir de là.
- **Aucune DA n'a de service demandeur** (section analytique vide) : le service viendra aussi d'`espace_magasin`.
- **Les montants des DA sont inutilisables** : 85 lignes de l'article `A13457` portent un prix fictif de 500 000 MAD, pour 6 171 milliards MAD au total (test `assert_x3_da_montant_plausible`).
- **22 factures fournisseurs ont un entête différent de leurs lignes** dans Sage X3, par exemple `FF171119` (600 000 MAD en entête, 3 000 MAD de lignes) et `FF174477` (515 311 / 3 346). Écart cumulé de 2023 à 2026 : environ 1,05 M MAD (test `assert_x3_facture_fournisseur_entete_egal_lignes`).
- **Les premiers fournisseurs sont des sociétés du groupe** (AMS, AKEG, Industrial Maintenance Company : 48,7 M MAD en 2025). À distinguer pour la vue groupe : ces achats s'annulent en consolidation.
- Délais médians 2025 : commande → réception 6 jours, réception → facture 20 jours ; 17 % des lignes livrées en retard sur la date prévue.
- **63 lignes de commande de 2026 reçues avant la date de commande** : commandes saisies après la livraison.
