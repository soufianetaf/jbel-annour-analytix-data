{#
  Grain : une ligne = un bon de gasoil.
  Source : raw_magasin.requests_gazoil. Ni CIN, ni nom du demandeur (non
  copiés). « matricule » est l'immatriculation du véhicule.

  La quantité réellement saisie est « qte_saisie » (positive, médiane 75 L) ;
  « quantity » est presque toujours vide (38 bons sur 2 346 au 25/11/2026).
  « km_parcouru » est le relevé du compteur, pas une distance.
#}

with source as (

    select * from {{ source('magasin', 'requests_gazoil') }}

)

select
    id                                      as id_bon,
    {{ texte('num_br') }}                   as numero_bon,
    {{ texte('article') }}                  as article,
    -- Le véhicule est dans « matricule » (immatriculation, confirmé le
    -- 25/11/2026) ; la colonne « vehicule » de la source est vide
    coalesce({{ texte('vehicule') }}, upper({{ texte('matricule') }}))
                                            as vehicule,
    {{ texte('service') }}                  as service,
    {{ texte('affectation_1') }}            as affectation_1,
    {{ texte('affectation_2') }}            as affectation_2,
    {{ texte('intitule') }}                 as intitule,
    nature                                  as code_nature,
    quantity                                as quantite_demandee,
    qte_saisie                              as quantite_saisie,
    km_parcouru                             as compteur_km,
    -- solde_j_1 (solde de la veille) n'est pas repris : vide sur tous les
    -- bons, dlt ne crée pas la colonne dans raw (25/11/2026)
    {{ texte('approval') }}                 as decision,
    {{ texte('status') }}                   as statut,
    created_at                              as cree_le,
    validated_at                            as valide_le,
    _source,
    _charge_le

from source
