{#
  Grain : une ligne = une machine × un jour.

  Les relevés des automates sont des compteurs cumulés depuis le début de
  la journée : le total du jour est le DERNIER relevé de la journée.
  Additionner les relevés compterait la production deux à trois fois.

  Wagons de la dépileuse : son compteur de wagons vaut toujours 0 ; ils
  viennent du journal des déchargements (un passage = un wagon). Pour
  l'empileuse, le journal des chargements est donné à côté du compteur,
  pour contrôle (44 wagons au journal, 44,7 au compteur le 24/11/2026).

  disponibilite = heures de marche / (heures de marche + heures d'arrêt).
#}

with releves as (

    select
        *,
        cast(releve_le as date) as jour,
        row_number() over (
            partition by machine, cast(releve_le as date)
            order by releve_le desc
        ) as rang,
        count(*) over (partition by machine, cast(releve_le as date)) as releves_du_jour
    from {{ ref('stg_machines__releves') }}

),

wagons as (

    select machine, cast(entree_le as date) as jour, count(*) as wagons
    from {{ ref('stg_machines__wagons') }}
    group by 1, 2

)

select
    cast(r.machine as text)                                     as machine,
    cast(r.jour as date)                                        as jour,
    cast(r.production as numeric(18, 3))                        as production,
    cast(r.unite_production as text)                            as unite_production,
    cast(r.production_calculee as numeric(18, 3))               as production_secondaire,
    cast(w.wagons as integer)                                   as wagons_journal,
    cast(r.heures_marche as numeric(10, 3))                     as heures_marche,
    cast(r.heures_arret as numeric(10, 3))                      as heures_arret,
    cast(r.heures_marche / nullif(r.heures_marche + r.heures_arret, 0) as numeric(8, 4))
                                                                as disponibilite,
    cast(r.demarrages as integer)                               as demarrages,
    cast(r.releve_le as timestamp)                              as dernier_releve_le,
    cast(r.releves_du_jour as integer)                          as releves_du_jour,
    cast(r._charge_le as timestamp with time zone)              as charge_le
from releves as r
left join wagons as w
    on w.machine = r.machine
   and w.jour = r.jour
where r.rang = 1
