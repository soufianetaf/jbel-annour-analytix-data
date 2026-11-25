{#
  Grain : une ligne = le réalisé et l'objectif d'une zone sur une fiche de poste.
  Source : raw_production.productionposts (base production_2026).
#}

with source as (

    select * from {{ source('production', 'productionposts') }}

)

select
    cast(id as bigint)                      as id_ligne,
    cast(finpost_id as bigint)              as id_fiche,
    cast(objectifzone_id as bigint)         as id_zone,
    {{ texte('libelle') }}                  as zone,
    saisie                                  as realise,
    objectif,
    created_at                              as cree_le,
    _source,
    _charge_le

from source
