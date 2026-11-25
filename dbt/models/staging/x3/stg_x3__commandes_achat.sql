{#
  Grain : une ligne = une commande fournisseur (entête).
  Source : raw_x3.porder (Sage X3, PORDER), sans nom ni adresse du tiers.
#}

with source as (

    select * from {{ source('x3', 'porder') }}

)

select
    {{ texte_x3('pohnum_0') }}              as numero_commande,
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('pohfcy_0') }}              as site,
    pohtyp_0                                as code_type_commande,
    purtyp_0                                as code_type_achat,
    {{ date_x3('orddat_0') }}               as date_commande,
    {{ texte_x3('bpsnum_0') }}              as fournisseur,
    {{ texte_x3('buy_0') }}                 as acheteur,
    {{ texte_x3('cce_0') }}                 as section,
    {{ texte_x3('cur_0') }}                 as devise,
    appflg_0                                as code_signature,
    rcpflg_0                                as code_reception,
    invflg_0                                as code_facturation,
    cleflg_0                                as code_solde,
    totlinamt_0                             as montant_ht,
    _source,
    _charge_le

from source
where {{ texte_x3('pohnum_0') }} is not null
