{#
  Grain : une ligne = un service (libellé harmonisé).
  Définitions : docs/indicateurs/rh.md

  Deux effectifs, de deux applications qui ne découpent pas l'entreprise de
  la même façon (« USINE » n'existe que dans la pointeuse ; 191 salariés sans
  service dans l'application RH) : ils sont mis côte à côte, pas additionnés.
#}

select
    cast(coalesce(r.service, p.service) as text)    as service,
    cast(r.effectif as integer)                     as effectif_rh,
    cast(r.embauches_12_mois as integer)            as embauches_12_mois,
    cast(p.effectif as integer)                     as effectif_pointeuse
from {{ ref('stg_rh__effectifs_service') }} as r
full outer join {{ ref('stg_rh__effectifs_pointeuse') }} as p
    on p.service = r.service
