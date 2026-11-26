{#
  Grain : une ligne = un jour, pour tout le site.

      taux_presence        = personnes qui ont pointé / effectif total de la pointeuse
      heures_moyennes_site = temps sur site / personnes avec une entrée et une sortie
                             (sans les petits groupes dont le temps a été vidé)
#}

with jours as (

    select
        jour,
        sum(personnes)                                                      as personnes,
        sum(pointages)                                                      as pointages,
        sum(minutes_sur_site)                                               as minutes_sur_site,
        sum(personnes_entree_sortie) filter (where minutes_sur_site is not null)
                                                                            as personnes_avec_temps
    from {{ ref('stg_rh__pointage_service_jour') }}
    group by jour

),

effectif as (

    select sum(effectif) as effectif from {{ ref('stg_rh__effectifs_pointeuse') }}

)

select
    cast(j.jour as date)                                                    as jour,
    cast(extract(isodow from j.jour) as integer)                            as jour_semaine,
    cast(j.personnes as integer)                                            as personnes_presentes,
    cast(j.pointages as integer)                                            as pointages,
    cast(e.effectif as integer)                                             as effectif_pointeuse,
    cast(j.personnes::numeric / nullif(e.effectif, 0) as numeric(6, 4))     as taux_presence,
    cast(j.minutes_sur_site / 60.0 / nullif(j.personnes_avec_temps, 0) as numeric(6, 2))
                                                                            as heures_moyennes_site
from jours as j
cross join effectif as e
