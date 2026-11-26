# Fiche indicateur : qualité des briques

> **Statut : proposition, à valider par le responsable qualité.**

| Élément | Valeur |
|---|---|
| Domaine | Qualité |
| Responsable métier | Responsable qualité (à confirmer) |
| Sources qui font foi | Serveur de l'usine : base `qualite` (contrôles en sortie du four, mesures) ; base `production_2026` (pesées des briques à trois étapes) |
| Tables | `marts.fct_controles_qualite` (défaut × chariot), `marts.fct_chariots_qualite` (chariot), `marts.fct_pesees_briques` (contrôle × zone × type), `marts.agg_pertes_poids_jour` (jour × type), `marts.fct_mesures_briques` (brique mesurée) |
| Copie | `uv run python -m ingestion.usine_qualite` (6 tables rapprochées) ; les pesées viennent de `ingestion.usine_production` |

Jamais copiés : le nom du freineur, l'identifiant de l'utilisateur, les observations, emplacements, corrections et notes en texte libre, les photos.

## 1. Défauts en sortie du four

Le contrôleur prend un chariot à la sortie du four et passe une **liste fixe de 11 défauts**. Pour chacun, il choisit une couleur et, s'il y a défaut, saisit des quantités.

| Couleur | Statut (interprétation à valider) |
|---|---|
| vert | conforme |
| jaune | défaut mineur |
| rouge | défaut majeur |
| bleu | non contrôlé (aucune quantité n'est jamais saisie en bleu) |
| vide | non renseigné |

Les libellés sont en arabe dans la source ; la traduction française (macro `defaut_qualite`) est à valider :

| Famille | Défauts |
|---|---|
| Cuisson | sous-cuit (MC), surcuit ou brûlé (BB), taches de coke ou coke non brûlé (TC) |
| Matière | nodules de chaux (CH), écaillage (EC) |
| Forme | déformation (D), retrait (R), affaissement (GF) |
| Fissures | sur la largeur (FL), sur les deux faces (FP), longitudinales (FH), transversales (FV) |
| Manutention | briques tombées (BR) |

Les codes de l'application ne suivent pas toujours le libellé (BB est « brûlé », BR est « tombé ») : **le libellé fait foi**.

**Statut d'un chariot** = son défaut le plus grave : défaut majeur > défaut mineur > conforme ; « non contrôlé » s'il n'a aucun défaut contrôlé.

```
part de chariots en défaut majeur = chariots « défaut majeur » / chariots contrôlés (hors « non contrôlé »)
```

Les **quantités** de briques non acceptables sont gardées telles quelles mais pas additionnées : 20 saisies dépassent 5 000 pour un chariot (8 668 saisi 14 fois, 356 226). Les indicateurs comptent les statuts.

## 2. Poids des briques à trois étapes

L'application de production pèse jusqu'à 8 briques par zone, à chaque poste : sortie de la mouleuse (« Monobloc », brique crue), sortie du séchoir, sortie du four. Les poids sont saisis en texte, en kg.

**Pesée plausible** : à moins de 40 % du poids médian de la même zone et du même type de brique. Les autres (« 3382 » au lieu de 3,382, « 96 »…) sont comptées dans `pesees_aberrantes` et exclues des moyennes : 0,3 % des pesées.

```
perte au séchage   = 1 - poids moyen après séchoir / poids moyen en sortie de mouleuse
perte à la cuisson = 1 - poids moyen après four    / poids moyen après séchoir
```

Moyennes du jour par type de brique : ce ne sont pas les mêmes briques aux trois étapes.

## 3. Mesures du service qualité

Poids et dimensions de briques prélevées en sortie de mouleuse et de séchoir (`fct_mesures_briques`). Unité des dimensions à confirmer (des cm d'après les ordres de grandeur).

## Constats sur les données (26/11/2026)

1. **Application qualité peu utilisée** : 154 chariots contrôlés en tout, surtout de juin à août 2025 (136), puis 6 en décembre 2025 et 11 en avril 2026. Dernière saisie le 17/04/2026, comme l'application de production.
2. Sur les chariots contrôlés : 22 conformes, 66 avec un défaut mineur, **43 avec un défaut majeur** ; 23 non contrôlés. Défauts majeurs les plus fréquents : fissures sur les deux faces (14), fissures sur la largeur (12), fissures transversales (11) ; défaut mineur le plus fréquent : sous-cuit (61).
3. **Pesées régulières** d'avril 2025 à février 2026 (50 à 100 contrôles par mois), puis presque plus rien (2 en mars, 1 en avril 2026).
4. **B8-25** (la brique principale) : 3,34 kg en sortie de mouleuse, 2,83 kg après le séchoir, 2,56 kg après le four. Perte médiane de **15,2 % au séchage** et de **9,9 % à la cuisson** (287 jours).
5. Beaucoup de saisies d'essai : zones « Yyt », « Gvv », emplacements « test », « ghg », références de moule écrites de plusieurs façons (G299-01, g-299-01, G.299.01, ramenées à G29901). Les zones non reconnues restent vides.
6. 108 rapports n'ont pas d'en-tête (date et poste) : on prend la date du rapport, sinon sa date de création.
7. Deux autres bases ne sont pas copiées : `qualite_check` (essais d'une journée, août 2025) et `qualite_prod` (nouvelle application, 40 inspections du 2 au 15 octobre 2026). À reprendre si `qualite_prod` remplace l'application actuelle.

## Points à valider

1. Sens des couleurs (en particulier le bleu) et traduction des 11 défauts.
2. Une quantité « non acceptable » compte-t-elle des briques ? Quel ordre de grandeur pour un chariot ?
3. Tolérance de poids par type de brique, à mettre à la place des 40 % autour de la médiane.
4. L'application `qualite_prod` remplace-t-elle `qualite` ? Les contrôles ont-ils repris ailleurs depuis avril 2026 ?
