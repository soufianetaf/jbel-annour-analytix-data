{#
  Grain : une ligne = un rapport de contrôle qualité.
  Source : raw_qualite.rapports. La date et le poste sont dans l'en-tête
  (rapport_infos) pour les premiers rapports, dans le rapport lui-même
  ensuite : les deux sont gardés, le choix est fait dans les marts.
#}

select
    cast(id as bigint)                          as id_rapport,
    cast(rapport_info_id as bigint)             as id_entete,
    cast(status as integer)                     as statut,
    {{ texte('list') }}                         as liste_controle,
    date                                        as jour,
    {{ poste_usine('shift') }}                  as poste,
    created_at                                  as cree_le,
    _charge_le
from {{ source('qualite', 'rapports') }}
