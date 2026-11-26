{#
  Grain : une ligne = une zone de l'usine × un mois.
  Définitions : docs/indicateurs/fiabilite.md

      panne            = ligne d'intervention faite machine à l'ARRÊT
      MTTR (minutes)   = minutes d'arrêt / nombre de pannes        (temps moyen de réparation)
      MTBF (heures)    = heures de marche / nombre de pannes        (temps moyen entre deux pannes)

  Les heures de marche viennent des automates : seulement pour le moulage,
  l'empileuse et la dépileuse (le four cuit en continu, la préparation et
  le séchoir n'ont pas de compteur d'heures ; MTBF vide). Les interventions
  ne sont saisies que depuis septembre 2026.
#}

{% set machine_de_zone = {'moulage': 'moulage', 'empileuse': 'empileuse', 'dépileuse': 'depileuse'} %}

with pannes as (

    select
        zone,
        cast(date_trunc('month', jour) as date)                             as mois,
        count(*) filter (where etat_machine = 'arrêt')                      as pannes,
        sum(minutes_arret)                                                  as minutes_arret,
        count(*) filter (where type_intervention = 'curatif')               as interventions_curatives,
        count(*) filter (where type_intervention = 'palliatif')             as interventions_palliatives,
        count(*)                                                            as interventions
    from {{ ref('fct_interventions_maintenance') }}
    where zone is not null
    group by 1, 2

),

marche as (

    select
        case machine
            {% for zone, machine in machine_de_zone.items() %}
            when '{{ machine }}' then '{{ zone }}'
            {% endfor %}
        end                                                                 as zone,
        cast(date_trunc('month', jour) as date)                             as mois,
        sum(heures_marche)                                                  as heures_marche
    from {{ ref('fct_machines_jour') }}
    group by 1, 2

)

select
    cast(p.zone as text)                                                    as zone,
    cast(p.mois as date)                                                    as mois,
    cast(p.interventions as integer)                                        as interventions,
    cast(p.interventions_curatives as integer)                              as interventions_curatives,
    cast(p.interventions_palliatives as integer)                            as interventions_palliatives,
    cast(p.pannes as integer)                                               as pannes,
    cast(coalesce(p.minutes_arret, 0) as integer)                           as minutes_arret,
    -- 0 heure de marche sur un mois entier : l'automate n'a pas compté
    -- (dépileuse depuis octobre 2026), pas une machine arrêtée un mois
    cast(nullif(m.heures_marche, 0) as numeric(12, 2))                      as heures_marche,
    cast(p.minutes_arret::numeric / nullif(p.pannes, 0) as numeric(10, 1))  as mttr_minutes,
    cast(nullif(m.heures_marche, 0) / nullif(p.pannes, 0) as numeric(10, 1)) as mtbf_heures
from pannes as p
left join marche as m
    on m.zone = p.zone
   and m.mois = p.mois
