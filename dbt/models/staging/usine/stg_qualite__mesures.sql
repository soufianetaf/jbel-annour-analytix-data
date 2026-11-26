{#
  Grain : une ligne = une brique mesurée (poids en kg, dimensions en cm, à confirmer).
  Source : raw_qualite.groups. Un 0 est une mesure non faite : vide.
#}

select
    cast(id as bigint)                                  as id_mesure,
    cast(info_id as bigint)                             as id_prelevement,
    cast(nullif(poids, 0) as numeric(12, 3))            as poids_kg,
    cast(nullif(haut, 0) as numeric(12, 2))             as hauteur_cm,
    cast(nullif(large, 0) as numeric(12, 2))            as largeur_cm,
    cast(nullif(long, 0) as numeric(12, 2))             as longueur_cm,
    created_at                                          as cree_le,
    _charge_le
from {{ source('qualite', 'groups') }}
