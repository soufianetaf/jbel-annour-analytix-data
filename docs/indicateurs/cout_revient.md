# Fiche indicateur : coût de revient, marge par type de brique, tableau de bord direction

> **Statut : proposition, à valider par le contrôle de gestion et le directeur financier.**

| Élément | Valeur |
|---|---|
| Domaine | Coût de revient, direction |
| Responsable métier | Contrôle de gestion (à confirmer) |
| Sources qui font foi | Tables déjà rapprochées : compte de résultat (Sage X3), ventes (Sage X3), tonnes cuites (automate du four), pesées des briques (application de production) |
| Tables | `marts.fct_charges_production_mois` (compte × mois), `marts.agg_cout_revient_mois` (mois), `marts.agg_marge_type_brique_mois` (type × mois), `marts.agg_direction_mois` (mois) |

Aucune nouvelle copie : tout est construit à partir des tables des étapes précédentes.

## Pourquoi pas le coût de Sage X3

Le coût de revient des lignes de facture (`CPRPRI`) est faux : 2 487 lignes ont un coût supérieur à 5 fois le prix de vente (cahier des charges). Il n'y a pas non plus de comptabilité analytique par section dans ce qui est copié. Le coût est donc calculé à partir de la **comptabilité générale**, rapprochée de Sage X3 au centime.

## Définitions

**Charges de production** = charges d'exploitation (comptes 61) du compte de résultat, clôtures exclues, **sauf les achats de marchandises revendues** (611 : camions, terrains…), qui ne servent pas à fabriquer des briques. Elles sont rangées en familles (macro `famille_cout`) :

| Famille | Comptes |
|---|---|
| combustibles | 61223 |
| électricité | 61251 |
| argile et matières premières | 6121, 61241 |
| emballages | 6123, 61243 |
| entretien et pièces de rechange | 61220001, 6133, 61252 |
| autres consommables | reste de 6122, 6124, 6125 (dont les variations de stock) |
| prestations de services | 6126 |
| locations et crédit-bail | 6131, 6132 |
| personnel | 617 |
| amortissements et provisions | 619 |
| autres charges | reste de 61 |
| hors coût de revient | 611 |

Un test vérifie chaque mois que les familles redonnent toutes les charges 61 du compte de résultat.

```
coût par tonne sur 12 mois = charges de production des 12 derniers mois / tonnes cuites des 12 derniers mois
coût énergie par tonne     = (combustibles + électricité) / tonnes cuites
```

**L'indicateur à lire est celui des 12 mois glissants.** Le coût d'un mois seul ne veut rien dire : les amortissements ne sont passés qu'en décembre (24 M MAD en 2025), et certaines charges sont régularisées d'un mois à l'autre (combustibles négatifs en octobre 2025). Il n'est calculé que si les 12 mois ont des tonnes cuites (automate du four, depuis le 26/11/2025) : premier mois disponible, octobre 2026.

**Marge par type de brique** :

```
type de brique  = lu dans la désignation de l'article (« BRIQUE BLCH8 » → B8, « (B10) » → B10)
tonnes vendues  = unités vendues × poids de l'article / 1 000
prix par tonne  = CA HT net / tonnes vendues
marge par tonne = prix par tonne - coût par tonne sur 12 mois
```

**Poids d'un article** : celui de Sage X3 s'il est plausible (1 à 20 kg), sinon le poids médian pesé à la sortie du four pour ce type. Contrôle : sur janvier à octobre 2026, **232 564 t vendues pour 235 653 t cuites** (1,3 % d'écart, l'écart de stock compris). Les poids sont donc cohérents.

**Le coût est celui du site, le même pour tous les types** : sans comptabilité analytique, rien ne permet de dire qu'une tonne de B12 coûte plus qu'une tonne de B8. La marge compare le prix de chaque type au coût moyen d'une tonne.

## Tableau de bord direction (`agg_direction_mois`)

Une ligne par mois : CA net, résultat comptable, trésorerie de fin de mois, tonnes cuites et vendues, coût et marge, kWh par tonne, heures d'arrêt maintenance. Rien n'est recalculé : chaque chiffre vient d'une table déjà rapprochée de sa source.

**Trésorerie de fin de mois** : comptes 51 et 55, cumul de l'exercice, **sans la pièce de clôture**. Au 31/12, la clôture remet ces comptes à zéro (comme dans la `BALANCE` de Sage X3) ; sans cette précaution, la trésorerie de décembre vaudrait 0. Fin décembre 2025 : -3,20 M MAD, exactement le montant rouvert au 1er janvier 2026.

## Constats (26/11/2026)

1. **Coût de revient : 617 MAD par tonne** sur décembre 2025 - novembre 2026 (646 MAD sur novembre 2025 - octobre 2026), dont **195 MAD d'énergie** (combustibles et électricité).
2. Charges des 12 derniers mois (M MAD) : prestations de services 59,2 ; combustibles 44,3 ; amortissements 24,1 ; locations et crédit-bail 12,3 ; électricité 10,6 ; entretien et pièces 10,0 ; emballages 6,6 ; argile 2,7 ; **personnel 2,2**.
3. **Les salaires disparaissent de Jbel Annour à partir d'avril 2026** (617 à zéro ou presque). Le personnel est probablement porté par une société du groupe et refacturé en prestations de services (6126, la première charge). À confirmer : sinon le coût de main-d'œuvre est sous-estimé.
4. Prix moyen de 2026 : **B8 665 MAD la tonne, B10 872, B12 652**. Avec un coût de 631 MAD la tonne, la marge est mince sur la B8 (environ 34 MAD la tonne) et la B12, plus large sur la B10.
5. Poids à corriger dans Sage X3 (test `assert_cout_poids_article_coherent`, 31 articles) : BLCH12 (50 cm) à 0,01 kg, B12 PBP à 2,5 kg contre 3,9 kg pesés, B10 PBP à 3,5 kg contre 2,8 kg, des articles sans poids.
6. Vue groupe : seule la société 100 (Jbel Annour) est dans Sage X3 BASE1. Les autres sociétés du groupe sont dans le dossier JBELRH (étape RH).

## Points à valider

1. Les familles de coût et l'exclusion des marchandises revendues (611).
2. Où est le coût du personnel depuis avril 2026 ?
3. Faut-il répartir les charges par type de brique (au poids, au temps de four) ou garder un coût moyen ?
4. Les amortissements : lisser l'annuel sur 12 mois, ou garder les 12 mois glissants ?
