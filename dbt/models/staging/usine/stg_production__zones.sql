{#
  Grain : une ligne = une zone de production (monobloc, empileuse,
  dépileuse, dépileuse vrac, four), avec son objectif par poste.
  Source : raw_production.objectifzones.
#}

with source as (

    select * from {{ source('production', 'objectifzones') }}

)

select
    cast(id as bigint)                      as id_zone,
    {{ texte('libelle') }}                  as zone,
    objectif                                as objectif_par_poste,
    _source,
    _charge_le

from source
