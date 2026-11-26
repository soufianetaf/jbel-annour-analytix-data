{#
  Grain : une ligne = une année d'embauche (ou le groupe des années à moins de 5 embauches).
  Source : raw_rh.embauches_annee.
#}

select
    {{ texte('annee') }}                as annee,
    cast(personnes as integer)          as embauches,
    _charge_le
from {{ source('rh', 'embauches_annee') }}
