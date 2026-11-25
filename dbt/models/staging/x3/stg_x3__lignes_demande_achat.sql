{#
  Grain : une ligne = une ligne de demande d'achat.
  Source : raw_x3.prequisd (Sage X3, PREQUISD). Nettoyage seulement.
  Attention : des montants sont fictifs (prix de 500 000 MAD sur l'article
  A13457) ; voir le test assert_x3_da_montant_plausible.
#}

with source as (

    select * from {{ source('x3', 'prequisd') }}

)

select
    {{ texte_x3('pshnum_0') }}              as numero_demande,
    psdlin_0                                as ligne,
    {{ texte_x3('pshfcy_0') }}              as site,
    {{ texte_x3('itmref_0') }}              as article,
    {{ texte_x3('bpsnum_0') }}              as fournisseur_propose,
    qtystu_0                                as quantite,
    ordqtystu_0                             as quantite_commandee,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    {{ texte_x3('cur_0') }}                 as devise,
    netpri_0                                as prix_net,
    linamt_0                                as montant_ht,
    {{ date_x3('extrcpdat_0') }}            as date_reception_souhaitee,
    linordflg_0                             as code_commande,
    lincleflg_0                             as code_solde,
    _source,
    _charge_le

from source
where {{ texte_x3('pshnum_0') }} is not null
