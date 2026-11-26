{#
  Grain : une ligne = un département (libellé harmonisé), effectif des pointeuses.
  Source : raw_rh.effectifs_pointeuse (agrégat, petits départements déjà fusionnés).
#}

select
    {{ service_rh('service') }}                 as service,
    cast(sum(personnes) as integer)             as effectif,
    max(_charge_le)                             as _charge_le
from {{ source('rh', 'effectifs_pointeuse') }}
group by 1
