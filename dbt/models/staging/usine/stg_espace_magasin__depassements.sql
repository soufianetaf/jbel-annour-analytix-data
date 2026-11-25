{#
  Grain : une ligne = une demande de dépassement de budget sur un article.
  Source : raw_espace_magasin.depassement. Ni commentaires, ni nom du
  demandeur, ni identifiant du valideur (non copiés).
#}

with source as (

    select * from {{ source('espace_magasin', 'depassement') }}

)

select
    id                                      as id_depassement,
    {{ texte('numero_depassemnt') }}        as numero_depassement,
    {{ texte('numero_da') }}                as numero_da,
    {{ texte('numero_budget') }}            as numero_budget,
    type_da                                 as code_type_da,
    {{ texte('code_article') }}             as article,
    {{ texte('designation') }}              as designation,
    {{ texte('famille') }}                  as famille,
    qte_demande                             as quantite_demandee,
    qte_buget                               as quantite_budget,
    qte_recomande                           as quantite_recommandee,
    date_creation                           as cree_le,
    date_aprove                             as approuve_le,
    {{ texte('statut') }}                   as statut,
    {{ texte('statut_res_magasin') }}       as avis_magasin,
    {{ texte('statut_res_methode') }}       as avis_methodes,
    {{ texte('statut_res_dga') }}           as avis_dga,
    {{ texte('statut_res_gestion') }}       as avis_gestion,
    {{ texte('statut_res_amelioration') }}  as avis_amelioration,
    {{ texte('statut_res_logistique') }}    as avis_logistique,
    {{ texte('statut_pdg') }}               as avis_pdg,
    {{ texte('accept_partiel') }}           as acceptation_partielle,
    _source,
    _charge_le

from source
