{{ config(materialized='view') }}

{#
  Grain : une ligne = un contrôle de qualité des données (un test dbt).
  Définitions : docs/indicateurs/qualite_donnees.md

  Page « Qualité des données » : pour chaque contrôle, son dernier résultat,
  le service qui doit corriger la source, la marche à suivre, et l'évolution
  depuis le contrôle précédent.

  Une VUE, et non une table : l'historique est rempli à la FIN de chaque
  construction (on-run-end), après les modèles ; une table aurait toujours
  un contrôle de retard.
#}

with historique as (

    select
        *,
        row_number() over (partition by test order by controle_le desc)     as rang
    from {{ source('qualite_donnees', 'resultats_tests') }}

),

premiere_erreur as (

    select test, min(controle_le) as premiere_erreur_le
    from historique
    where coalesce(lignes_en_erreur, 0) > 0
    group by test

)

select
    cast(d.test as text)                                                    as test,
    cast(d.service as text)                                                 as service,
    cast(d.correction as text)                                              as correction,
    cast(d.modele as text)                                                  as modele,
    cast(d.severite as text)                                                as severite,
    cast(d.statut as text)                                                  as statut,
    cast(d.controle_le as timestamp with time zone)                         as dernier_controle_le,
    cast(coalesce(d.lignes_en_erreur, 0) as bigint)                         as lignes_en_erreur,
    cast(p.lignes_en_erreur as bigint)                                      as lignes_controle_precedent,
    cast(coalesce(d.lignes_en_erreur, 0) - p.lignes_en_erreur as bigint)    as evolution,
    cast(e.premiere_erreur_le as timestamp with time zone)                  as premiere_erreur_le,
    cast(d.table_lignes as text)                                            as table_lignes
from historique as d
left join historique as p
    on p.test = d.test
   and p.rang = 2
left join premiere_erreur as e
    on e.test = d.test
where d.rang = 1
