{#
  Grain : une ligne = un point de contrôle préventif (libellé).
  Source : raw_maintenance.actions.
#}

select
    cast(id as bigint)              as id_action,
    {{ texte('description') }}      as action,
    _charge_le
from {{ source('maintenance', 'actions') }}
