{#
  Grain : une ligne = un contrôle de poids × une zone × un type de brique
  (jusqu'à 8 briques pesées). Source : application de production.

  Pesée plausible : à moins de 40 % du poids médian de la même zone et du
  même type de brique sur toute la période. Les autres (3 382 au lieu de
  3,382 kg, 96 kg, 0,8 kg…) sont des erreurs de saisie : comptées, mais
  exclues des moyennes.
#}

with pesees as (

    select
        p.*,
        c.jour,
        c.poste
    from {{ ref('stg_production__pesees_briques') }} as p
    inner join {{ ref('stg_production__controles_poids') }} as c
        on c.id_controle_poids = p.id_controle_poids
    where p.zone is not null

),

medianes as (

    select
        zone,
        type_brique,
        percentile_cont(0.5) within group (order by poids_kg)   as poids_median
    from pesees
    group by zone, type_brique

),

controlees as (

    select
        p.*,
        p.poids_kg between m.poids_median * 0.6 and m.poids_median * 1.4    as plausible
    from pesees as p
    inner join medianes as m
        on m.zone = p.zone
       and m.type_brique is not distinct from p.type_brique

)

select
    cast(id_controle_poids as bigint)                                   as id_controle_poids,
    cast(jour as date)                                                  as jour,
    cast(poste as text)                                                 as poste,
    cast(zone as text)                                                  as zone,
    cast(coalesce(type_brique, 'inconnu') as text)                      as type_brique,
    cast(count(*) as integer)                                           as briques_pesees,
    cast(count(*) filter (where not plausible) as integer)              as pesees_aberrantes,
    cast(avg(poids_kg) filter (where plausible) as numeric(12, 3))      as poids_moyen_kg,
    cast(min(poids_kg) filter (where plausible) as numeric(12, 3))      as poids_min_kg,
    cast(max(poids_kg) filter (where plausible) as numeric(12, 3))      as poids_max_kg,
    cast(stddev_samp(poids_kg) filter (where plausible) as numeric(12, 4))
                                                                        as ecart_type_kg
from controlees
group by id_controle_poids, jour, poste, zone, coalesce(type_brique, 'inconnu')
