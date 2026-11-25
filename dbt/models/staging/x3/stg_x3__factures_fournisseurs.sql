{#
  Grain : une ligne = une facture ou un avoir fournisseur (entête).
  Source : raw_x3.pinvoice (Sage X3, PINVOICE), sans nom ni adresse.
  Montants positifs ; le sens est dans « signe » (-1 pour un avoir).
#}

with source as (

    select * from {{ source('x3', 'pinvoice') }}

)

select
    {{ texte_x3('num_0') }}                 as numero_facture,
    invtyp_0                                as code_categorie,     -- 1 facture, 2 avoir
    {{ texte_x3('pivtyp_0') }}              as type_facture,       -- FAF, AVR, AVO…
    {{ texte_x3('bpr_0') }}                 as fournisseur,
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcy_0') }}                 as site,
    {{ date_x3('accdat_0') }}               as date_comptable,
    {{ date_x3('bprdat_0') }}               as date_facture_fournisseur,
    sta_0                                   as code_statut,
    sns_0                                   as signe,
    {{ texte_x3('cur_0') }}                 as devise,
    amtnot_0                                as montant_ht,
    amtati_0                                as montant_ttc,
    amtnotl_0                               as montant_ht_mad,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
