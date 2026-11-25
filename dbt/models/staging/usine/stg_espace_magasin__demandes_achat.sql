{#
  Grain : une ligne = une demande d'achat de l'usine (entête).
  Source : raw_espace_magasin.demandes_achats. Ni nom du demandeur, ni
  commentaires (non copiés).
#}

with source as (

    select * from {{ source('espace_magasin', 'demandes_achats') }}

)

select
    id                                      as id_demande,
    {{ texte('numero') }}                   as numero,
    {{ texte('da_no') }}                    as numero_da_x3,
    cast("date" as date)                    as date_demande,
    cast(echeance as date)                  as date_echeance,
    {{ texte('departement_demandeur') }}    as departement,
    {{ texte('service') }}                  as service,
    {{ texte('affectation2') }}             as affectation,
    {{ texte('famille') }}                  as famille,
    {{ texte('code_article') }}             as article,
    quantite_val                            as quantite_validee,
    {{ texte('fournisseur') }}              as fournisseur,
    visa_demandeur                          as a_visa_demandeur,
    visa_resp_magasin                       as a_visa_magasin,
    status                                  as code_statut,
    {{ texte('decision') }}                 as decision,
    depassement_buget                       as code_depassement_budget,
    validated_at                            as valide_le,
    created_at                              as cree_le,
    _source,
    _charge_le

from source
