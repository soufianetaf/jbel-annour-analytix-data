{#
  Grain : une ligne = une demande de sortie d'un article du magasin.
  Source : raw_magasin.requests (application Magasin de l'usine).
  Nettoyage seulement. Le nom du demandeur n'est pas copié.
#}

with source as (

    select * from {{ source('magasin', 'requests') }}

)

select
    id                                      as id_sortie,
    {{ texte('article') }}                  as article,
    {{ texte('designation') }}              as designation,
    quantity                                as quantite,
    quantite_stock,
    quantite_credit,
    qte_robot_saisie                        as quantite_saisie_x3,
    {{ texte('service') }}                  as service,
    {{ texte('service_concerne') }}         as service_concerne,
    {{ texte('affectation1') }}             as affectation_1,
    {{ texte('affectation2') }}             as affectation_2,
    {{ texte('affectation3') }}             as affectation_3,
    {{ texte('affectation4') }}             as affectation_4,
    {{ texte('intitule') }}                 as intitule,
    {{ texte('ms') }}                       as ms,
    {{ texte('retour') }}                   as retour,
    {{ texte('approval') }}                 as decision,       -- APPROVED, REJECTED
    {{ texte('status') }}                   as statut,         -- DONE, SUBMITTED
    created_at                              as cree_le,
    validated_at                            as valide_le,
    _source,
    _charge_le

from source
