{#
  Grain : une ligne = une fiche d'intervention de maintenance.
  Source : raw_maintenance_interventions.interventions, sans l'utilisateur.
#}

select
    cast(id as bigint)                          as id_intervention,
    {{ texte('numero_fiche') }}                 as numero_fiche,
    date_fiche                                  as jour,
    {{ zone_usine('zone') }}                    as zone,
    lower({{ texte('service_maintenance') }})   as service,
    upper({{ texte('equipe') }})                as equipe,
    {{ poste_maintenance('shift') }}            as poste,
    created_at                                  as cree_le,
    _charge_le
from {{ source('maintenance_interventions', 'interventions') }}
