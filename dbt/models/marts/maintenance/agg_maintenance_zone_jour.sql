{#
  Grain : une ligne = une zone de l'usine × un jour.

      tournees_faites       = postes (sur 3) dont la tournée préventive a des résultats
      taux_realisation      = points remplis / points de la tournée
      taux_conformite       = points conformes / points remplis
      minutes_intervention  = durée des interventions sur panne
      minutes_arret         = durée des interventions machine à l'arrêt
#}

with preventif as (

    select
        zone,
        jour,
        count(distinct poste)                                           as tournees_faites,
        count(*)                                                        as points,
        count(*) filter (where statut <> 'non rempli')                  as points_remplis,
        count(*) filter (where statut = 'conforme')                     as points_conformes,
        count(*) filter (where statut = 'non conforme')                 as points_non_conformes
    from {{ ref('fct_controles_preventifs') }}
    group by zone, jour

),

interventions as (

    select
        zone,
        jour,
        count(*)                                                        as interventions,
        count(*) filter (where etat_machine = 'arrêt')                  as interventions_machine_arretee,
        sum(duree_minutes)                                              as minutes_intervention,
        sum(minutes_arret)                                              as minutes_arret
    from {{ ref('fct_interventions_maintenance') }}
    where zone is not null
    group by zone, jour

)

select
    cast(coalesce(p.zone, i.zone) as text)                              as zone,
    cast(coalesce(p.jour, i.jour) as date)                              as jour,
    cast(coalesce(p.tournees_faites, 0) as integer)                     as tournees_faites,
    cast(coalesce(p.points, 0) as integer)                              as points_controle,
    cast(coalesce(p.points_non_conformes, 0) as integer)                as points_non_conformes,
    cast(p.points_remplis::numeric / nullif(p.points, 0) as numeric(6, 4))
                                                                        as taux_realisation,
    cast(p.points_conformes::numeric / nullif(p.points_remplis, 0) as numeric(6, 4))
                                                                        as taux_conformite,
    cast(coalesce(i.interventions, 0) as integer)                       as interventions,
    cast(coalesce(i.interventions_machine_arretee, 0) as integer)       as interventions_machine_arretee,
    cast(coalesce(i.minutes_intervention, 0) as integer)                as minutes_intervention,
    cast(coalesce(i.minutes_arret, 0) as integer)                       as minutes_arret
from preventif as p
full outer join interventions as i
    on i.zone = p.zone
   and i.jour = p.jour
