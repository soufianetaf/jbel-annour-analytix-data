{#
  Grain : une ligne = un jour, pour le site.

  Définitions : docs/indicateurs/energie.md
  - électricité du site = transformateur 1 + transformateur 2 (le compteur
    « entree » ne mesure que 260 kWh par jour : ce n'est pas le total) ;
    les compteurs par machine sont en aval, on ne les additionne pas ;
  - tonnes cuites = bilan du jour du four (fct_machines_jour) ;
  - coke : dernier relevé du jour de l'automate du four (compteurs cumulés).

      kwh_par_tonne  = électricité du site / tonnes cuites
      coke_kg_tonne  = ratio de cuisson donné par l'automate du four
#}

with electricite as (

    select
        jour,
        sum(kwh) filter (where compteur in ('transfo1', 'transfo2'))    as kwh_site,
        -- Un transformateur à 0 kWh sur une journée entière est une panne
        -- de collecte (le site consomme toujours) : il ne compte pas.
        count(*) filter (where compteur in ('transfo1', 'transfo2') and kwh > 0)
                                                                        as transformateurs_mesures,
        sum(kwh) filter (where niveau = 'machine')                      as kwh_compteurs_machines,
        min(cos_phi_moyen) filter (where compteur in ('transfo1', 'transfo2'))
                                                                        as cos_phi_min_transformateurs
    from {{ ref('fct_electricite_jour') }}
    group by jour

),

four as (

    select * from {{ ref('fct_machines_jour') }}
    where machine = 'four'

),

coke as (

    select distinct on (cast(releve_le as date))
        cast(releve_le as date)     as jour,
        coke_kg_par_tonne,
        coke_consomme_tonnes,
        coke_livre_tonnes
    from {{ ref('stg_four__combustible') }}
    order by cast(releve_le as date), releve_le desc

)

select
    cast(coalesce(e.jour, f.jour) as date)                              as jour,
    cast(case when e.transformateurs_mesures = 2 then e.kwh_site end as numeric(18, 3))
                                                                        as kwh_site,
    cast(coalesce(e.transformateurs_mesures = 2, false) as boolean)     as electricite_complete,
    cast(e.kwh_compteurs_machines as numeric(18, 3))                    as kwh_compteurs_machines,
    cast(e.cos_phi_min_transformateurs as numeric(6, 4))                as cos_phi_min_transformateurs,
    cast(f.production as numeric(18, 3))                                as tonnes_cuites,
    cast(case when e.transformateurs_mesures = 2
              then e.kwh_site / nullif(f.production, 0) end as numeric(12, 3))
                                                                        as kwh_par_tonne,
    cast(c.coke_kg_par_tonne as numeric(12, 3))                         as coke_kg_par_tonne,
    cast(c.coke_consomme_tonnes as numeric(12, 3))                      as coke_consomme_tonnes,
    cast(c.coke_livre_tonnes as numeric(12, 3))                         as coke_livre_tonnes
from electricite as e
full outer join four as f
    on f.jour = e.jour
left join coke as c
    on c.jour = coalesce(e.jour, f.jour)
