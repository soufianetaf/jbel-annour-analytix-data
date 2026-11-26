{#
  Grain : une ligne = un contrôle de poids des briques (date, poste).
  Source : raw_production.poidsbriques (application de production).
  Les contrôles supprimés dans l'application sont écartés.
#}

select
    cast(id as bigint)                          as id_controle_poids,
    date                                        as jour,
    {{ texte('heure') }}                        as heure,
    {{ poste_usine('shift') }}                  as poste,
    cast(etat as integer)                       as etat,
    created_at                                  as cree_le,
    _charge_le
from {{ source('production', 'poidsbriques') }}
where deleted_at is null
