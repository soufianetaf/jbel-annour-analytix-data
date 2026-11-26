{#
  Grain : une ligne = un point de contrôle d'un équipement.
  Source : raw_maintenance.equipement_actions.
#}

select
    cast(id as bigint)              as id_point,
    cast(equipement_id as bigint)   as id_equipement,
    cast(action_id as bigint)       as id_action,
    cast(ordre as integer)          as ordre,
    _charge_le
from {{ source('maintenance', 'equipement_actions') }}
