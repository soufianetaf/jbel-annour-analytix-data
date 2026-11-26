{#
  Grain : une ligne = une machine × un jour (moulage, empileuse, dépileuse).
  Définitions : docs/indicateurs/fiabilite.md

  TRS (taux de rendement synthétique), HORS QUALITÉ :

      disponibilité    = heures de marche / (heures de marche + heures d'arrêt)
                         (le temps où l'automate était sous tension)
      cadence du jour  = production / heures de marche
      cadence de référence = meilleure cadence démontrée : 95e centile des
                         cadences du jour de la machine, sur tout l'historique
                         (la cadence nominale du constructeur n'est pas connue)
      performance      = cadence du jour / cadence de référence (au plus 1)
      TRS              = disponibilité × performance

  La qualité (part de briques bonnes) n'est pas mesurée par machine : le TRS
  est donc calculé sans elle, et l'écrit (trs_hors_qualite).

  Impact des pannes sur la production :

      production perdue estimée = minutes d'arrêt saisies par la maintenance
                                  / 60 × cadence de référence
#}

{% set zone_de_machine = {'moulage': 'moulage', 'empileuse': 'empileuse', 'depileuse': 'dépileuse'} %}

with jours as (

    select
        machine,
        jour,
        production,
        unite_production,
        heures_marche,
        heures_arret,
        disponibilite,
        production / nullif(heures_marche, 0)                               as cadence
    from {{ ref('fct_machines_jour') }}
    where machine in ({% for m in zone_de_machine %}'{{ m }}'{% if not loop.last %}, {% endif %}{% endfor %})

),

reference as (

    select
        machine,
        percentile_cont(0.95) within group (order by cadence)              as cadence_reference
    from jours
    where cadence > 0
    group by machine

),

arrets_maintenance as (

    select
        case zone
            {% for machine, zone in zone_de_machine.items() %}
            when '{{ zone }}' then '{{ machine }}'
            {% endfor %}
        end                                                                 as machine,
        jour,
        sum(minutes_arret)                                                  as minutes_arret,
        count(*) filter (where etat_machine = 'arrêt')                      as pannes
    from {{ ref('fct_interventions_maintenance') }}
    group by 1, 2

),

calcul as (

    select
        j.*,
        r.cadence_reference,
        -- least() ignore les vides en PostgreSQL : sans cadence (aucune heure
        -- de marche), la performance doit rester vide, pas valoir 1
        case
            when j.cadence is not null
            then least(j.cadence / nullif(r.cadence_reference, 0), 1)
        end                                                                 as performance,
        -- Sans aucune heure enregistrée, l'automate n'a pas compté : vide, pas 0
        case when j.heures_marche + j.heures_arret > 0 then j.disponibilite end
                                                                            as disponibilite_mesuree,
        a.minutes_arret                                                     as minutes_arret_maintenance,
        a.pannes
    from jours as j
    inner join reference as r
        on r.machine = j.machine
    left join arrets_maintenance as a
        on a.machine = j.machine
       and a.jour = j.jour

)

select
    cast(machine as text)                                                   as machine,
    cast(jour as date)                                                      as jour,
    cast(production as numeric(18, 3))                                      as production,
    cast(unite_production as text)                                          as unite_production,
    cast(heures_marche as numeric(8, 3))                                    as heures_marche,
    cast(heures_arret as numeric(8, 3))                                     as heures_arret,
    cast(cadence as numeric(12, 3))                                         as cadence_par_heure,
    cast(cadence_reference as numeric(12, 3))                               as cadence_reference,
    cast(disponibilite_mesuree as numeric(6, 4))                            as disponibilite,
    cast(performance as numeric(6, 4))                                      as performance,
    cast(disponibilite_mesuree * performance as numeric(6, 4))              as trs_hors_qualite,
    cast(coalesce(pannes, 0) as integer)                                    as pannes,
    cast(coalesce(minutes_arret_maintenance, 0) as integer)                 as minutes_arret_maintenance,
    cast(coalesce(minutes_arret_maintenance, 0) / 60.0 * cadence_reference as numeric(18, 3))
                                                                            as production_perdue_estimee
from calcul
