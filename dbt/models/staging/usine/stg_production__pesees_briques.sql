{#
  Grain : une ligne = une brique pesée (jusqu'à 8 par zone et contrôle).
  Source : raw_production.poidsbriques_infos, colonnes poids1 à poids8
  remises en lignes.

  Les poids sont saisis en TEXTE (kg) : convertis par nombre_saisi ; un 0
  ou une case vide est une brique non pesée et n'a pas de ligne.
  Zone : Monobloc = sortie de la mouleuse (brique crue), séchoir, four.
#}

with pesees as (

    select
        source.id,
        source.poidsbrique_id,
        case lower({{ texte('zone') }})
            when 'monobloc' then 'mouleuse'
            when 'séchoir' then 'séchoir'
            when 'four' then 'four'
        end                                         as zone,
        upper({{ texte('type') }})                  as type_brique,
        position.numero,
        position.poids,
        source._charge_le
    from {{ source('production', 'poidsbriques_infos') }} as source
    cross join lateral (
        values
            (1, {{ nombre_saisi('poids1') }}),
            (2, {{ nombre_saisi('poids2') }}),
            (3, {{ nombre_saisi('poids3') }}),
            (4, {{ nombre_saisi('poids4') }}),
            (5, {{ nombre_saisi('poids5') }}),
            (6, {{ nombre_saisi('poids6') }}),
            (7, {{ nombre_saisi('poids7') }}),
            (8, {{ nombre_saisi('poids8') }})
    ) as position (numero, poids)

)

select
    cast(id as bigint)                                  as id_pesees,
    cast(poidsbrique_id as bigint)                      as id_controle_poids,
    zone,
    type_brique,
    numero                                              as numero_brique,
    cast(poids as numeric(12, 3))                       as poids_kg,
    _charge_le
from pesees
where poids > 0
