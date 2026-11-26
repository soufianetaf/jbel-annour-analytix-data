{#
  Grain : une ligne = un poste × un mois de réception des candidatures.
  Source : raw_rh.candidatures_mois (comptages seulement, aucune donnée de candidat).
#}

select
    {{ texte('poste') }}                        as poste,
    cast({{ texte('mois') }} || '-01' as date)  as mois,
    cast(personnes as integer)                  as candidatures,
    _charge_le
from {{ source('rh', 'candidatures_mois') }}
