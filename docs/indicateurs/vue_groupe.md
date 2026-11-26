# Fiche : vue groupe (toutes les sociétés)

> **Statut : bloquée, décision de la direction nécessaire.**

Le cahier des charges prévoit une vue groupe pour la direction générale : CA, résultat, trésorerie de toutes les sociétés du groupe. L'exploration du 26/11/2026 (lecture seule, comptages seulement, aucune donnée de paie ni de personne) montre que **les données des autres sociétés ne sont dans aucune source accessible**.

## Ce que contiennent les dossiers Sage X3

| Serveur, dossier | Sociétés déclarées | Activité trouvée | Conclusion |
|---|---|---|---|
| Sage X3, **BASE1** | 100 Jbel Annour (+ deux groupes de sites, DEC et NDEC) | Jbel Annour : 310 971 lignes d'écritures et 7 997 factures, de 2021 à aujourd'hui | Source en service, déjà copiée |
| Sage X3, **BASE2** | Mêmes que BASE1 | Jbel Annour : 306 465 lignes d'écritures, 7 872 factures, **arrêtées au 30/10/2026** | Copie de BASE1 (essai ou sauvegarde). **Ne jamais la lire en plus de BASE1** : tout serait compté deux fois |
| Sage X3, **SAV**, **SAV2** | Mêmes que BASE1 | Jbel Annour, partiel (SAV : août-septembre 2021) | Sauvegardes, à ignorer |
| JBELRH (second serveur), **JBELRH** | 8 sociétés : 100, JBEL (Jbel Annour), AKEG (Al Kenz El Ghali), AMG0 (Amana Multiservices Group), AMS0 (Agence Marocaine Multiservices), CBDL (Conseil en Business Développement et Logistique), IMC0 (Industrial Maintenance Company), MSG0 (Marocaine de Support et de Gestion) | Comptabilité et factures de la **seule société 100**, de 2021 à janvier 2023 (152 208 lignes d'écritures, 1 423 factures). Aucune écriture ni facture pour les 7 autres sociétés | Ancienne copie de Jbel Annour, plus la paie et le pointage du groupe |

**Les 7 autres sociétés n'ont donc ni comptabilité ni ventes dans Sage X3.** Elles apparaissent seulement comme employeurs, dans la paie et le pointage de JBELRH.

## Ce qui est déjà fait côté groupe

- Les tables issues de Sage X3 (ventes, finance, achats, stock, commandes) portent la société (`societe`) : quand les données d'une autre société arriveront, elles s'ajouteront sans changer les définitions. Les tables de l'usine concernent la seule usine de Jbel Annour.
- Les fournisseurs du groupe sont repérés dans les achats de Jbel Annour (fiche achats : fournisseurs intra-groupe), et la refacturation probable du personnel par une société du groupe est signalée dans la fiche coût de revient (« prestations de services », 59 M MAD sur 12 mois).

## Décisions à prendre (direction générale)

1. **Où est tenue la comptabilité des 7 autres sociétés ?** Un autre logiciel, un cabinet comptable, des fichiers Excel ? Si une source existe, elle se copie comme les autres, en lecture seule.
2. **La paie agrégée par société** (masse salariale, effectif payé), seule donnée du groupe présente dans JBELRH : elle demande l'accord écrit de la direction et des RH (cahier des charges). Avec cet accord, elle se copie sur le modèle de la RH (agrégats calculés sur le serveur source, aucune ligne individuelle, groupes de moins de 5 personnes fusionnés).
3. **BASE2** : est-ce un dossier d'essai ? Confirmer qu'il ne doit jamais être lu.
4. **Groupes de sites DEC et NDEC** de BASE1 (« Sites déclarées », « Sites non déclarées ») : à quoi servent-ils ? Aucune écriture ne leur est rattachée aujourd'hui.
