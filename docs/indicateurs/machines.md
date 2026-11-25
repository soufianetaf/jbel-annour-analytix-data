# Fiche indicateur : machines (moulage, séchoir, empileuse, four, dépileuse)

> **Statut : proposition, à valider par le responsable production et le responsable méthodes.**

| Élément | Valeur |
|---|---|
| Domaine | Production / machines |
| Responsable métier | Responsable production et méthodes (à confirmer) |
| Sources qui font foi | Serveur de l'usine : bases `moulage`, `sechoir`, `empileuse`, `Four_prod`, `depileuse`, alimentées par les automates |
| Tables | `marts.fct_machines_jour` (bilan journalier par machine), `marts.fct_moulage_quart_heure`, `marts.fct_wagons` |

## La chaîne de fabrication

```
Moulage (monobloc) → Séchoir → Empileuse → Four → Dépileuse
   étagères           étagères   wagons      wagons   paquets
```

## Définitions

**Relevé** : chaque automate enregistre un relevé à chaque fin de poste (7 h, 15 h, 23 h). Ses compteurs (production, heures de marche et d'arrêt, démarrages) sont **cumulés depuis le début de la journée**. Le **bilan du jour** est donc le dernier relevé de la journée ; la production d'un poste est l'écart entre deux relevés.

**Production du jour**, par machine :

| Machine | Production | Unité |
|---|---|---|
| Moulage | chariots (étagères) produits | étagère |
| Empileuse | wagons empilés | wagon |
| Four | briques cuites | tonne et unité |
| Dépileuse | wagons dépilés ; paquets emballés et en vrac | wagon, paquet |

**Disponibilité** d'une machine sur un jour = heures de marche / (heures de marche + heures d'arrêt).

**Mesures du moulage** : une mesure par minute environ (vitesse de coupe, vitesse du doseur, pression du monobloc, courant de l'extrudeuse), agrégée par **quart d'heure** (moyenne, minimum, maximum, nombre de mesures).

**Coupure de mesure** : un intervalle de plus d'une heure sans mesure. Elle peut être un **arrêt de la machine** ou une **panne de la collecte** : on ne peut pas les distinguer avec les seules mesures (cahier des charges, 5.2).

**Cycle d'un wagon** (empileuse, dépileuse) : temps entre l'entrée et la sortie du wagon.

## Données personnelles

Le **nom de l'opérateur** (remplissage des étagères, chargement et déchargement des wagons) n'est pas copié : l'analyse se fait par machine, pas par personne.

## Points à valider

1. Les compteurs repartent-ils bien de zéro à minuit (4 jours où un compteur redescend en cours de journée) ?
2. Le bilan journalier du four (`qte_brique_tonne`) fait-il foi pour la production en tonnes, à la place des fiches de poste arrêtées depuis fin avril 2026 ?
3. Une coupure de mesure du moulage pendant une période où le bilan journalier indique une marche est-elle une panne de la collecte ?

## Premiers constats (25/11/2026, à présenter au responsable production et aux méthodes)

- Copie conforme : 11 tables des automates, identiques à la source, dont **1 287 866 mesures du moulage** (copie incrémentale ; rapprochement arrêté à la dernière mesure copiée, une mesure arrivant toutes les 11 secondes).
- **Les relevés des machines sont pris en fin de poste (7 h, 15 h, 23 h) et les compteurs sont cumulés depuis le début de la journée** : four 267 t à 7 h, 583 t à 15 h, 935 t le soir. Le total du jour est le dernier relevé ; **additionner les relevés aurait compté la production deux à trois fois**. Règle protégée par un test unitaire.
- **Les automates couvrent sans interruption la période depuis novembre 2025**, y compris après l'arrêt des fiches de poste (fin avril 2026) : environ **23 000 tonnes cuites par mois** (four), 5 500 étagères moulées, 1 100 wagons empilés, 22 000 paquets emballés.
- **Contrôle croisé** : wagons de l'empileuse, 44,7 au compteur et 44 au journal wagon par wagon le 24/11/2026. Monobloc en janvier 2026 : 6 874 étagères selon les fiches de poste, 6 557 selon l'automate.
- **Le compteur de wagons de la dépileuse vaut toujours 0** : les wagons dépilés viennent du journal des déchargements.
- **Disponibilité du monobloc** (marche / (marche + arrêt)) : 71 à 78 % la plupart des mois, 45 % en mars 2026, 60 % en mai-juin.
- **267 coupures des mesures du moulage de plus d'une heure** (2 227 heures au total, la plus longue 446 heures, les 18 jours du cahier des charges). **219 tombent des jours où le monobloc a tourné plus de 8 heures** : ce sont très probablement des **pannes de la collecte**, pas des arrêts de la machine.
- Cycle médian d'un wagon : 26 minutes à l'empileuse, 29 minutes à la dépileuse ; 20 passages au cycle impossible (sortie avant l'entrée, ou plus de 24 h).
- 4 jours où un compteur redescend en cours de journée (remise à zéro ?) : signalés par `assert_machines_compteur_cumule_croissant`.
