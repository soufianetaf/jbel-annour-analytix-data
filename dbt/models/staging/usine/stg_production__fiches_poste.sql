{#
  Grain : une ligne = une fiche de fin de poste, telle que saisie.
  Source : raw_production.finposts (base production_2026).
  Nettoyage seulement : les doublons et les fiches supprimées sont traités
  dans intermediate (int_production__fiches_dedoublonnees).
#}

with source as (

    select * from {{ source('production', 'finposts') }}

)

select
    cast(id as bigint)                      as id_fiche,
    {{ date_seule('selected_date') }}       as date_poste,
    {{ texte('shift') }}                    as shift,
    {{ texte('equipe') }}                   as equipe,
    status                                  as code_statut,
    {{ texte('nombre_palette') }}           as nombre_palettes_saisi,
    {{ texte('nombre_etageres') }}          as nombre_etageres_saisi,
    created_at                              as cree_le,
    updated_at                              as modifie_le,
    deleted_at                              as supprime_le,
    _source,
    _charge_le

from source
