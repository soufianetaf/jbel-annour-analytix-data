{#
  Grain : une ligne = une demande d'intervention.
  Source : raw_maintenance_demandes.demandes_intervention, sans demandeur,
  intervenant ni texte libre. Les demandes d'essai (« test », « FFFF »)
  sont écartées.
  Urgence : « + », « ++ », « +++ » → 1, 2, 3.
#}

with source as (

    select * from {{ source('maintenance_demandes', 'demandes_intervention') }}

)

select
    cast(id as bigint)                                  as id_demande,
    lower({{ texte('service') }})                       as service,
    {{ texte('machine') }}                              as machine,
    {{ texte('code_machine') }}                         as code_machine,
    case
        when lower({{ texte('etat_machine') }}) ~ '^(en )?arr' then 'arrêt'
        when lower({{ texte('etat_machine') }}) ~ '^(en )?march|^em$' then 'en marche'
    end                                                 as etat_machine,
    cast(compteur_machine as integer)                   as compteur_machine,
    length({{ texte('urgence') }})                      as urgence,
    lower({{ texte('type_intervention') }})             as type_intervention,
    cast(statut as integer)                             as statut,
    action_efficace,
    date_heure_panne                                    as panne_le,
    date_heure_debut                                    as debut_le,
    date_heure_remise_service                           as remise_service_le,
    created_at                                          as cree_le,
    _charge_le
from source
where coalesce(lower({{ texte('service') }}), '') not in ('test', 'ffff')
  and coalesce(lower({{ texte('machine') }}), '') <> 'test'
