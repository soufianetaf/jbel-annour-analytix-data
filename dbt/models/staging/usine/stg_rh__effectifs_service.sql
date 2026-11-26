{#
  Grain : une ligne = un service (libellé harmonisé), effectif de l'application RH.
  Source : raw_rh.effectifs_service (agrégat, petits services déjà fusionnés).
  Deux écritures d'un même service sont additionnées.
#}

select
    {{ service_rh('service') }}                 as service,
    cast(sum(personnes) as integer)             as effectif,
    cast(sum(embauches_12_mois) as integer)     as embauches_12_mois,
    max(_charge_le)                             as _charge_le
from {{ source('rh', 'effectifs_service') }}
group by 1
