{#
  Grain : une ligne = une raison d'écart rattachée à une ligne de production.
  Sources : raw_production.productionpost_raison et raw_production.raisons.
  La raison libre saisie (colonne « raison ») complète la raison de la liste.
#}

with liens as (

    select * from {{ source('production', 'productionpost_raison') }}

),

raisons as (

    select * from {{ source('production', 'raisons') }}

)

select
    cast(l.id as bigint)                    as id_lien,
    cast(l.productionpost_id as bigint)     as id_ligne,
    cast(l.raison_id as bigint)             as id_raison,
    coalesce({{ texte('r.libelle') }}, {{ texte('l.raison') }})
                                            as raison,
    l._charge_le
from liens as l
left join raisons as r
    on r.id = l.raison_id
