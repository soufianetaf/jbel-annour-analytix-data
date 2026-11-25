{#
  Grain : une ligne = le passage d'un wagon à l'empileuse ou à la dépileuse.

  cycle_minutes = sortie - entrée. Les cycles négatifs ou de plus de 24 h
  sont des erreurs d'horodatage (cahier des charges, 5.2) : vides ici,
  listés par le test assert_machines_cycle_wagon_plausible.
#}

select
    cast(machine as text)                                       as machine,
    cast(id_passage as bigint)                                  as id_passage,
    cast(operation as text)                                     as operation,
    cast(entree_le as date)                                     as jour,
    cast(entree_le as timestamp)                                as entree_le,
    cast(sortie_le as timestamp)                                as sortie_le,
    cast(numero_wagon as integer)                               as numero_wagon,
    cast(case
            when sortie_le >= entree_le
             and sortie_le - entree_le <= interval '24 hours'
            then extract(epoch from sortie_le - entree_le) / 60
         end as numeric(10, 2))                                 as cycle_minutes,
    cast(_charge_le as timestamp with time zone)                as charge_le
from {{ ref('stg_machines__wagons') }}
