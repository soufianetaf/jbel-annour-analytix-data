# Fiche indicateur : commandes, livraisons et facturation

> **Statut : proposition, à valider par l'ADV et le directeur commercial.**

| Élément | Valeur |
|---|---|
| Domaine | Commercial, ADV |
| Sources | Sage X3 : SORDER, SORDERQ, SORDERP (commandes), SDELIVERY, SDELIVERYD (livraisons), SINVOICE (factures) |
| Tables | `marts.fct_commandes` (commande), `marts.fct_livraisons` (livraison), `marts.agg_commercial_mois` (mois) |
| Copie | `uv run python -m ingestion.x3_commandes` (5 tables, rapprochées au centime) |
| API | `/v1/ventes/cycle-mois`, `/v1/ventes/livre-non-facture` (le représentant ne voit que ses livraisons) |

Listes fermées : jamais les adresses, noms de contacts et de destinataires, le chauffeur, les plaques, les remarques, les utilisateurs X3, ni le coût de revient des lignes (`CPRPRI`, faux).

## Comment Jbel Annour travaille (d'après les données)

- **La commande est saisie au moment de la livraison** : 0 jour en médiane entre la commande et l'expédition, 69 955 commandes sur 70 719 ont exactement une livraison. Il n'y a presque pas de carnet de commandes en attente : 6 commandes ouvertes au 26/11/2026.
- **La facturation est mensuelle** : les livraisons d'un mois sont facturées en fin de mois ou au début du suivant (6 à 17 jours en médiane selon le mois).

Les indicateurs utiles sont donc le **livré non facturé**, les **délais** et les **commandes soldées sans livraison**, plus qu'un carnet de commandes.

## Définitions

| Indicateur | Définition |
|---|---|
| Délai commande → expédition | Première expédition - date de commande (jours) |
| Délai expédition → facture | Date comptable de la facture - date d'expédition ; vide si la facture est datée avant l'expédition (test en avertissement) |
| Livré non facturé | Livraisons validées pas encore facturées, avec leur ancienneté (jours depuis l'expédition) |
| Reste à livrer | Commandes ouvertes : quantité commandée - quantité livrée |
| Commande soldée sans livraison | Commande fermée sans aucune livraison : annulée, ou saisie en double |

Statuts de Sage X3 traduits : commande 1 ouverte, 2 soldée ; livraison 1 non livrée, 2 partiellement, 3 livrée ; facturation 1 non facturée, 2 partiellement, 3 facturée.

## Contrôles

- Les 5 tables sont rapprochées de Sage X3 à chaque copie (lignes et montants, au centime).
- **Livré et facturé concordent** : de janvier à octobre 2026, 168,6 M MAD livrés pour 167,1 M MAD de CA facturé (0,9 % d'écart, les livraisons de fin de mois facturées le mois suivant).
- Aucune facture datée avant son expédition au 26/11/2026 (test `assert_livraison_facturee_avant_expedition`).

## Constats (26/11/2026)

1. **Livré non facturé : 681 livraisons, 11,9 M MAD**, toutes de novembre 2026 (la plus ancienne a 25 jours) : la facturation mensuelle de novembre n'est pas encore passée.
2. **667 commandes soldées sans aucune livraison** depuis 2021 (18,9 M MAD), dont 174 sur les douze derniers mois et **100 en octobre 2026**. Annulations, ou doublons de saisie : à revoir par l'ADV (test `assert_commandes_soldees_sans_livraison`, sur la page « Qualité des données »).
3. Le délai médian entre expédition et facture va de 4 à 17 jours selon le mois : le jour de la facturation mensuelle varie.

## Points à valider

1. Une commande soldée sans livraison est-elle une annulation, ou un doublon à supprimer ?
2. La facturation est-elle bien mensuelle pour tous les clients ? Certains sont-ils facturés à la livraison ?
3. Le « carnet de commandes » a-t-il un sens pour la direction, vu que la commande est saisie à la livraison ? Les commandes des clients arrivent-elles ailleurs (téléphone, application adv) ?
