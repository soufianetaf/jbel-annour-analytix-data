{#
  Grain : une ligne = un compteur par machine × un jour.
  Définitions : docs/indicateurs/energie.md

      kwh_par_tonne = kWh de la machine / tonnes cuites du site ce jour
                      (même dénominateur pour toutes : les machines se comparent)
      kwh_par_unite = kWh de la machine / sa propre production, quand son
                      automate en donne une (extrudeuse → étagères moulées,
                      four → tonnes, empileuse → wagons, dépileuse → paquets)
#}

{% set production_machine = {
    'extrudeuse': 'moulage', 'four': 'four', 'empileuse': 'empileuse', 'depileuse': 'depileuse'
} %}

with electricite as (

    select compteur, jour, kwh, cos_phi_moyen, energie_reactive_excedentaire_kvarh
    from {{ ref('fct_electricite_jour') }}
    where niveau = 'machine'

),

production as (

    select
        case machine
            {% for compteur, machine in production_machine.items() %}
            when '{{ machine }}' then '{{ compteur }}'
            {% endfor %}
        end                                     as compteur,
        jour,
        production,
        unite_production
    from {{ ref('fct_machines_jour') }}

)

select
    cast(e.compteur as text)                                            as compteur,
    cast(e.jour as date)                                                as jour,
    cast(e.kwh as numeric(18, 3))                                       as kwh,
    cast(s.tonnes_cuites as numeric(18, 3))                             as tonnes_cuites_site,
    cast(e.kwh / nullif(s.tonnes_cuites, 0) as numeric(12, 3))          as kwh_par_tonne,
    cast(p.production as numeric(18, 3))                                as production_machine,
    cast(p.unite_production as text)                                    as unite_production,
    cast(e.kwh / nullif(p.production, 0) as numeric(12, 3))             as kwh_par_unite,
    cast(e.cos_phi_moyen as numeric(6, 4))                              as cos_phi_moyen,
    cast(e.energie_reactive_excedentaire_kvarh as numeric(18, 3))       as energie_reactive_excedentaire_kvarh
from electricite as e
left join {{ ref('agg_energie_jour') }} as s
    on s.jour = e.jour
left join production as p
    on p.compteur = e.compteur
   and p.jour = e.jour
