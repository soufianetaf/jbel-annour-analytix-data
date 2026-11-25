{#
  Grain : une ligne = une ligne de demande d'achat de l'usine.
  Source : raw_espace_magasin.demandes_achats_lignes. Ni motif, ni
  observation, ni commentaire (texte libre, non copié).
#}

with source as (

    select * from {{ source('espace_magasin', 'demandes_achats_lignes') }}

)

select
    id                                      as id_ligne,
    demande_achat_id                        as id_demande,
    {{ texte('da_no') }}                    as numero_da_x3,
    {{ texte('code_article') }}             as article,
    {{ texte('code_article_valide') }}      as article_valide,
    {{ texte('designation') }}              as designation,
    {{ texte('reference') }}                as reference,
    {{ texte('marque') }}                   as marque,
    {{ texte('famille') }}                  as famille,
    {{ texte('affectation') }}              as affectation,
    quantite,
    quantite_val                            as quantite_validee,
    status                                  as code_statut,
    {{ texte('decision') }}                 as decision,
    validated_at                            as valide_le,
    created_at                              as cree_le,
    _source,
    _charge_le

from source
