{#
  Grain : une ligne = une ligne de réception fournisseur.
  Source : raw_x3.preceiptd (Sage X3, PRECEIPTD). Nettoyage seulement.
#}

with source as (

    select * from {{ source('x3', 'preceiptd') }}

)

select
    {{ texte_x3('pthnum_0') }}              as numero_reception,
    ptdlin_0                                as ligne,
    {{ texte_x3('prhfcy_0') }}              as site,
    {{ date_x3('rcpdat_0') }}               as date_reception,
    {{ texte_x3('pohnum_0') }}              as numero_commande,
    poplin_0                                as ligne_commande,
    poqseq_0                                as sequence_commande,
    {{ texte_x3('bpsnum_0') }}              as fournisseur,
    {{ texte_x3('itmref_0') }}              as article,
    qtystu_0                                as quantite,
    rtnqtystu_0                             as quantite_retournee,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    netpri_0                                as prix_net,
    linamt_0                                as montant_ht,
    {{ texte_x3('netcur_0') }}              as devise,
    _source,
    _charge_le

from source
where {{ texte_x3('pthnum_0') }} is not null
