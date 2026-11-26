{#
  Grain : une ligne = un chariot (wagon) contrôlé en sortie du four.
  Source : raw_qualite.rapport_composantes, sans observations ni photos.
#}

select
    cast(id as bigint)                          as id_chariot,
    cast(rapport_id as bigint)                  as id_rapport,
    upper({{ texte('type_brique') }})           as type_brique,
    {{ texte('numero_chariot') }}               as numero_chariot,
    temps_sortie_four                           as heure_sortie_four,
    controle_time                               as heure_controle,
    created_at                                  as cree_le,
    _charge_le
from {{ source('qualite', 'rapport_composantes') }}
