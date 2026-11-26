{#
  Grain : une ligne = un ordre de travail ouvert sur un point non conforme.
  Source : raw_maintenance.ordre_travail, sans problème ni commentaire.
  Le nom de colonne accentué a été abîmé à la copie (« numéro_ot » → num_ro_ot).
  Temps prévu saisi en texte (« 120 », « 30 min », « 3h ») : seuls les
  nombres seuls sont gardés, en minutes.
#}

select
    cast(id as bigint)                                  as id_ordre_travail,
    cast(equipement_action_id as bigint)                as id_point,
    cast(rapport_quotidien_id as bigint)                as id_tournee,
    {{ texte('num_ro_ot') }}                            as numero_ot,
    {{ texte('statut') }}                               as statut,
    cast(priorite as integer)                           as priorite,
    {{ texte('type') }}                                 as type_action,
    {{ texte('nature') }}                               as nature,
    {{ nombre_saisi('temps') }}                         as temps_prevu_minutes,
    cast(code_article as text)                          as code_article,
    cast(quantite as integer)                           as quantite,
    created_at                                          as cree_le,
    _charge_le
from {{ source('maintenance', 'ordre_travail') }}
