{#
  Grain : une ligne = une ligne d'intervention (un équipement, une plage horaire).
  Source : raw_maintenance_interventions.lignes_intervention, sans
  intervenant ni texte libre (anomalie, cause, action réalisée).

  État de la machine : ARR = à l'arrêt, EM = en marche, TM (à valider).
  Durée : calculée sur les heures de début et de fin (macro
  duree_intervention_minutes) ; la durée saisie en texte est gardée pour
  contrôle. Pièces : liste JSON [{"code": …, "qte": …}], lue dans
  stg_maintenance__pieces_intervention.
#}

select
    cast(id as bigint)                                  as id_ligne,
    cast(intervention_id as bigint)                     as id_intervention,
    date_ligne                                          as jour,
    {{ texte('equipement_ensemble') }}                  as equipement,
    case upper({{ texte('etat_machine') }})
        when 'ARR' then 'arrêt'
        when 'EM' then 'en marche'
        when 'TM' then 'TM'
    end                                                 as etat_machine,
    {{ type_panne('type_panne') }}                      as type_panne,
    case lower({{ texte('type_intervention') }})
        when 'curatif' then 'curatif'
        when 'curative' then 'curatif'
        when 'palliatif' then 'palliatif'
    end                                                 as type_intervention,
    debut,
    fin,
    cast({{ duree_intervention_minutes('debut', 'fin') }} as integer)
                                                        as duree_minutes,
    {{ texte('duree') }}                                as duree_saisie,
    {{ texte('code_article_pdr') }}                     as pieces_json,
    cast(qte as integer)                                as quantite,
    {{ texte('numero_ot') }}                            as numero_ot,
    _charge_le
from {{ source('maintenance_interventions', 'lignes_intervention') }}
