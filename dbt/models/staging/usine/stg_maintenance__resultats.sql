{#
  Grain : une ligne = le résultat d'un point de contrôle dans une tournée.
  Source : raw_maintenance.resultats_controle, sans commentaire, problème
  ni actions planifiées (texte libre).
#}

select
    cast(id as bigint)                                  as id_resultat,
    cast(rapport_quotidien_id as bigint)                as id_tournee,
    cast(equipement_action_id as bigint)                as id_point,
    case {{ texte('statut') }}
        when 'C' then 'conforme'
        when 'NC' then 'non conforme'
        when 'Empty' then 'non rempli'
    end                                                 as statut,
    cast(priorite as integer)                           as priorite,
    {{ texte('type') }}                                 as type_action,
    {{ texte('nature') }}                               as nature,
    {{ texte('nc_type') }}                              as suite_donnee,
    {{ texte('n_ot') }}                                 as numero_ot,
    upper({{ texte('code_article') }})                  as code_article,
    cast(quantite as integer)                           as quantite,
    _charge_le
from {{ source('maintenance', 'resultats_controle') }}
