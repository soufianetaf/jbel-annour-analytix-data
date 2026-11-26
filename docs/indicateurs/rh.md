# Fiche indicateur : effectifs, présence et recrutement (agrégés)

> **Statut : proposition, à valider par le responsable RH et la direction.**

| Élément | Valeur |
|---|---|
| Domaine | Ressources humaines |
| Responsable métier | Responsable RH |
| Sources qui font foi | Serveur de l'usine : base `RH` (application RH, candidatures) ; base `pointage` (pointeuses) |
| Tables | `marts.fct_effectifs_service` (service), `marts.agg_presence_service_jour` (département × jour), `marts.agg_presence_jour` (jour), `marts.agg_embauches_annee` (année), `marts.agg_recrutement` (poste × mois) |
| Copie | `uv run python -m ingestion.usine_rh` (5 agrégats, totaux rapprochés) |
| Accès | Rôle RH ; la direction voit les agrégats. Jamais le contrôle de gestion ni les autres rôles |

## Règle d'or : aucune donnée individuelle

Les autres copies prennent des tables. **La copie RH, non** : elle exécute sur le serveur source des requêtes d'agrégation (comptages et sommes par service, par jour, par mois). Aucune ligne de salarié ne quitte le serveur : pas de nom, de matricule, d'identifiant, de date de naissance, de téléphone, de taux horaire ni de donnée de candidat.

**Petits groupes** : un groupe de moins de **5 personnes** permettrait de retrouver quelqu'un (« le seul salarié du juridique a pointé 4 h »). Il est fusionné dans « autres (moins de 5 personnes) » avant d'être écrit dans l'entrepôt, et son temps sur site est vidé si le groupe fusionné reste sous 5 personnes. Les totaux sont conservés, et le rapprochement les compare à la source.

Trois contrôles :
- `tests/test_usine_rh.py` : la fusion des petits groupes, et aucune requête ne lit une colonne personnelle (nom, téléphone, CIN, taux horaire, RIB…) ;
- le rapprochement des totaux à chaque copie ;
- le test dbt **bloquant** `assert_rh_aucun_petit_groupe_nomme` : aucune table RH ne nomme un groupe de moins de 5 personnes.

**Pas copiés** : le dossier Sage X3 **JBELRH** (paie, primes, livre de paie avec salaires et RIB). Même agrégée par service, la masse salariale demande l'accord écrit de la direction et des RH (cahier des charges). Pas copiées non plus : les bases `pointage_1`, `pointage_2`, `wdms` (installations de pointeuses presque vides, en double) et le résumé calculé par le logiciel de pointage (`att_day_summary`, seulement 127 salariés).

## Définitions

**Service** : libellé harmonisé (accents retirés ; « DIRECTION GENERAL » → « DIRECTION GENERALE », « ACHAT » → « ACHATS »…). Les deux applications ne découpent pas l'entreprise de la même façon : « USINE » n'existe que dans la pointeuse ; les deux effectifs sont mis côte à côte, jamais additionnés.

**Effectif RH** : salariés non supprimés de l'application RH, sans date de sortie (la source écrit 1753 pour « pas de sortie »).

**Présence** (d'après les pointages bruts) :

```
présent                = au moins un pointage ce jour-là
temps sur site         = dernier pointage - premier pointage du jour (au moins deux pointages)
taux de présence       = personnes présentes / effectif enregistré dans la pointeuse
heures moyennes sur site = temps sur site / personnes avec une entrée et une sortie
part de pointage unique  = personnes avec un seul pointage / personnes présentes
```

Le jour est le jour calendaire : un poste de nuit (23h-7h) compte sur deux jours. Le temps sur site comprend les pauses.

## Constats (26/11/2026)

1. **615 salariés actifs** dans l'application RH, **558** dans la pointeuse. **191 salariés sans service** dans l'application RH (31 %).
2. **La pointeuse n'est déployée que depuis septembre 2026** : 1 % à 3 % des inscrits pointent d'avril à juillet, 21 % en septembre, **47 % en octobre** (262 personnes par jour ouvré). Le taux de présence mesure donc encore le **déploiement des pointeuses**, pas l'absentéisme. À ne pas présenter comme un taux d'absence.
3. Octobre, jours ouvrés : de 34 % (direction) à 85 % (amélioration continue) de présence mesurée ; **10 h sur site en moyenne**, 11 h à la production, à la logistique et à la TPM. 13 % à 32 % des présents n'ont qu'un pointage (entrée ou sortie oubliée).
4. **Embauches** : 207 en 2025, 124 en 2023 ; 44 sur les 12 derniers mois. Les dates d'embauche de la pointeuse sont inutilisables (555 sur 558 en 1970) : celles de l'application RH sont retenues.
5. **Recrutement** : 292 candidatures, presque toutes en novembre 2026 (142 chauffeurs de camion, 127 consultants RPA).

## Points à valider

1. Le seuil de 5 personnes et les agrégats autorisés (cahier des charges, question 8).
2. L'accord écrit pour une masse salariale par service, depuis JBELRH.
3. Quand le pointage sera généralisé : quel effectif de référence pour l'absentéisme (pointeuse ou application RH) ? Les congés et absences justifiées sont-ils saisis quelque part ?
4. Compléter le service des 191 salariés qui n'en ont pas.
