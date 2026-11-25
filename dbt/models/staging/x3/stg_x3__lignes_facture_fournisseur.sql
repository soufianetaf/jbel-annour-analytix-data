{#
  Grain : une ligne = une ligne de facture ou d'avoir fournisseur.
  Source : raw_x3.pinvoiced (Sage X3, PINVOICED). Nettoyage seulement.
  Montants positifs, en devise de la facture.
#}

with source as (

    select * from {{ source('x3', 'pinvoiced') }}

)

select
    {{ texte_x3('num_0') }}                 as numero_facture,
    pidlin_0                                as ligne,
    invtyp_0                                as code_categorie,
    {{ texte_x3('fcylin_0') }}              as site,
    {{ date_x3('accdat_0') }}               as date_comptable,
    {{ texte_x3('bpr_0') }}                 as fournisseur,
    {{ texte_x3('itmref_0') }}              as article,
    qtystu_0                                as quantite,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    netpri_0                                as prix_net,
    amtnotlin_0                             as montant_ht,
    {{ texte_x3('netcur_0') }}              as devise,
    {{ texte_x3('pohnum_0') }}              as numero_commande,
    poplin_0                                as ligne_commande,
    poqseq_0                                as sequence_commande,
    {{ texte_x3('pthnum_0') }}              as numero_reception,
    ptdlin_0                                as ligne_reception,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
