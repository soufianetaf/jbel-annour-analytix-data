# Fiche indicateur : sorties magasin par service, gasoil, demandes d'achat et dépassements de budget

> **Statut : proposition, à valider par le responsable magasin et le responsable achats.**

| Élément | Valeur |
|---|---|
| Domaine | Magasin / achats |
| Responsable métier | Responsable magasin (à confirmer) |
| Sources qui font foi | Serveur de l'usine : base `Magasin` (demandes de sortie, bons de gasoil), base `espace_magasin` (demandes d'achat, dépassements de budget, entrées magasin, silos de coke et de fuel) |
| Tables | `marts.fct_sorties_magasin`, `marts.fct_gasoil`, `marts.fct_demandes_achat_usine`, `marts.fct_depassements_budget` |

## Pourquoi ces bases

Sage X3 ne dit pas **quel service** consomme les pièces (aucune section analytique sur les mouvements de stock), et les demandes d'achat n'y sont plus saisies depuis 2025. Ces deux informations sont dans les applications du magasin.

## Définitions

**Sortie magasin** : une demande de sortie d'un article par un service, pour une affectation (machine, zone…). Une sortie compte quand elle est **validée**.

**Bon de gasoil** : une sortie de gasoil pour un véhicule, avec le kilométrage. **Consommation d'un véhicule** sur une période = somme des quantités validées ; **litres aux 100 km** = quantité / kilomètres parcourus × 100.

**Demande d'achat (DA)** : demande d'un département, avec son circuit de visas (demandeur, responsable magasin) et sa décision.

**Dépassement de budget** : une DA dont la quantité dépasse la quantité budgétée de l'article. Il passe par un circuit d'avis (magasin, méthodes, DGA, gestion, amélioration, logistique, PDG).

## Données personnelles

Ces bases contiennent des données que **l'analyse par service n'utilise pas** et qui ne sont jamais copiées :

| Base | Jamais copié |
|---|---|
| `Magasin` | table `users` (**mots de passe**), CIN du chauffeur (`requests_gazoil`), nom du demandeur, identifiants des valideurs, commentaires. Le `matricule` des bons de gasoil est copié : c'est l'immatriculation du **véhicule** (confirmé le 25/11/2026), pas un matricule de salarié |
| `espace_magasin` | table `approval_tokens` (**jetons**), table `utilisateurs_badges` (**codes PIN**), noms des demandeurs et des personnes concernées, signatures, commentaires et motifs en texte libre |

## Lecture de la source

Le serveur de l'usine est lu avec le compte `sa` (dérogation du 25/11/2026, cahier des charges 5.4). Analytix n'y exécute que des lectures, sans verrou.

## Points à valider

1. Quels statuts signifient « sortie validée » (`status`, `approval`) ?
2. Les quantités de gasoil saisies comme texte (cahier des charges 5.2) : sont-elles dans `quantity` ou `qte_saisie` ?
3. Le champ `service` est-il le service demandeur ou le service consommateur (`service_concerne`) ?
4. Un dépassement est-il accepté quand le PDG l'approuve, ou quand tous les avis sont favorables ?

## Premiers constats (25/11/2026, à présenter au responsable magasin)

- Copie conforme : 7 tables de `Magasin` et `espace_magasin`, identiques à la source. Aucune donnée sensible dans l'entrepôt (contrôlé colonne par colonne).
- **Sorties magasin** (depuis le 14/02/2026) : 17 085 demandes, dont 15 541 validées (91 %), validées en 28 minutes en médiane.
  - Le champ « service » vaut `PRODTF001` pour 96 % des demandes, et « service concerné » vaut `MAG` pour 86 % : ils ne disent pas qui consomme.
  - **L'affectation dit quelle machine consomme** : dépileuse (3 169 sorties validées), pince (1 303), préparation (803), empileuse (763), monobloc (678), étagères du séchoir (661). C'est la base du coût de maintenance par machine.
  - Tous les articles sont des codes de Sage X3 : la clé article est commune avec le stock, les achats et les ventes.
- **Gasoil** : la quantité est dans `qte_saisie` (positive, médiane 75 L par bon), pas dans `quantity` (vide sur 98 % des bons). 350 194 L validés sur les bons plausibles.
  - **9 bons aberrants** : 7 négatifs (dont -449 595 L) et 2 de plus de 38 000 L. Probablement un relevé de compteur saisi à la place des litres (test `assert_magasin_gasoil_quantite_plausible`).
  - `km_parcouru` est le **relevé du compteur**, pas une distance : la distance est l'écart avec le bon valide précédent du même véhicule (`km_depuis_bon_precedent`). 2 relevés incohérents (compteur qui recule ou saute de plus de 5 000 km) sont listés par `assert_magasin_gasoil_compteur_plausible`.
  - **Le véhicule est dans `matricule`** (immatriculation, confirmé le 25/11/2026 ; la colonne `vehicule` est vide) : 35 véhicules. Les camions consomment **42 à 47 L aux 100 km**.
  - Un engin affiche 1 498 L « aux 100 km » pour 1 780 « km » : son compteur compte vraisemblablement des **heures** de fonctionnement (chargeuse, engin de manutention). Pour ces engins, l'indicateur est en litres par heure : liste des engins à fournir par le magasin.
- **Demandes d'achat de l'usine** : 639 demandes, 919 lignes ; seules 64 portent un numéro de DA Sage X3. Validation très rapide (médiane 3,6 heures).
- **Dépassements de budget** (depuis le 17/07/2026) : 602 demandes, dont 122 approuvées par le PDG.
- Une colonne vide sur tous les bons (`solde_j_1`) n'est pas créée par dlt : l'outil `verifier_types_staging` signale désormais ces colonnes absentes.
