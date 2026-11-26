{#
  Grain : une ligne = une demande d'intervention.

  Délai de remise en service = remise en service - panne, en heures ; vide
  tant que la demande n'est pas close (62 sur 69 au 26/11/2026).
#}

select
    cast(id_demande as bigint)                                          as id_demande,
    cast(coalesce(panne_le, cree_le) as date)                           as jour,
    cast(service as text)                                               as service,
    cast(machine as text)                                               as machine,
    cast(code_machine as text)                                          as code_machine,
    cast(etat_machine as text)                                          as etat_machine,
    cast(urgence as integer)                                            as urgence,
    cast(type_intervention as text)                                     as type_intervention,
    cast(statut as integer)                                             as statut,
    cast(action_efficace as boolean)                                    as action_efficace,
    cast(panne_le as timestamp)                                         as panne_le,
    cast(debut_le as timestamp)                                         as debut_le,
    cast(remise_service_le as timestamp)                                as remise_service_le,
    cast(round(extract(epoch from (debut_le - panne_le)) / 3600, 2) as numeric(10, 2))
                                                                        as heures_avant_intervention,
    cast(round(extract(epoch from (remise_service_le - panne_le)) / 3600, 2) as numeric(10, 2))
                                                                        as heures_remise_service
from {{ ref('stg_maintenance__demandes') }}
