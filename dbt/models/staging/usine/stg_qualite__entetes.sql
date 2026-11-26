{#
  Grain : une ligne = un en-tête de contrôle (date et poste).
  Source : raw_qualite.rapport_infos, sans le nom du freineur.
#}

select
    cast(id as bigint)                          as id_entete,
    date_controle                               as jour,
    {{ poste_usine('shift') }}                  as poste,
    _charge_le
from {{ source('qualite', 'rapport_infos') }}
