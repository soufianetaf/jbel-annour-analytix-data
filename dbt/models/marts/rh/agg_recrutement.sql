{#
  Grain : une ligne = un poste × un mois de réception des candidatures.
  Comptages seulement : aucune donnée de candidat n'est copiée.
#}

select
    cast(poste as text)             as poste,
    cast(mois as date)              as mois,
    cast(candidatures as integer)   as candidatures
from {{ ref('stg_rh__candidatures_mois') }}
