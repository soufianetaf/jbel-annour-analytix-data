{#
  Grain : une ligne = une ligne de commande × une échéance de livraison.
  Source : raw_x3.porderq (Sage X3, PORDERQ). Nettoyage seulement.
#}

with source as (

    select * from {{ source('x3', 'porderq') }}

)

select
    {{ texte_x3('pohnum_0') }}              as numero_commande,
    poplin_0                                as ligne,
    poqseq_0                                as sequence,
    {{ texte_x3('pohfcy_0') }}              as site,
    {{ date_x3('orddat_0') }}               as date_commande,
    {{ texte_x3('bpsnum_0') }}              as fournisseur,
    {{ texte_x3('itmref_0') }}              as article,
    qtystu_0                                as quantite_commandee,
    rcpqtystu_0                             as quantite_recue,
    invqtystu_0                             as quantite_facturee,
    retqtystu_0                             as quantite_retournee,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    {{ date_x3('extrcpdat_0') }}            as date_reception_prevue,
    {{ date_x3('lasrcpdat_0') }}            as date_derniere_reception,
    {{ date_x3('lasinvdat_0') }}            as date_derniere_facture,
    linamt_0                                as montant_ht,
    {{ texte_x3('netcur_0') }}              as devise,
    linsta_0                                as code_statut,
    lincleflg_0                             as code_solde,
    _source,
    _charge_le

from source
where {{ texte_x3('pohnum_0') }} is not null
