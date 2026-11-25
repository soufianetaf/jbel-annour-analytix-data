{#
  Grain : une ligne = une mesure du process du moulage (environ toutes les
  11 secondes). Source : raw_moulage.remplissage_process_data, copiée en
  incrémental.
#}

select
    cast("id" as bigint)            as id_mesure,
    remplissage_id                  as id_remplissage,
    date_insert                     as mesure_le,
    vitesse_coupe,
    vitesse_doseur,
    pression_mono                   as pression_monobloc,
    courant_extrudeuse,
    _charge_le
from {{ source('moulage', 'remplissage_process_data') }}
