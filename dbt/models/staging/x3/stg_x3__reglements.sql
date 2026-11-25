{#
  Grain : une ligne = un règlement (encaissement ou décaissement).
  Source : raw_x3.paymenth (Sage X3, PAYMENTH), copiée en liste fermée :
  ni RIB, ni banque du tiers, ni numéro de chèque, ni adresse.

  Nettoyage seulement : montants positifs, sens séparé (comme dans X3).
#}

with source as (

    select * from {{ source('x3', 'paymenth') }}

)

select
    {{ texte_x3('num_0') }}                 as numero_reglement,
    {{ texte_x3('paytyp_0') }}              as type_reglement,      -- CESP, FEFF…
    {{ texte_x3('pam_0') }}                 as mode_paiement,
    bprtyp_0                                as code_type_tiers,     -- 1 client, 2 fournisseur
    {{ texte_x3('bpr_0') }}                 as tiers,
    {{ texte_x3('bprsac_0') }}              as compte_collectif,
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcy_0') }}                 as site,
    {{ texte_x3('ban_0') }}                 as banque_entreprise,   -- B01, CAISS…
    sns_0                                   as code_sens,           -- 2 encaissement, 1 décaissement
    {{ texte_x3('cur_0') }}                 as devise,
    amtcur_0                                as montant_devise,
    amtban_0                                as montant_banque,
    sta_0                                   as code_statut,
    {{ date_x3('accdat_0') }}               as date_comptable,
    {{ date_x3('duddat_0') }}               as date_echeance,
    {{ date_x3('valdat_0') }}               as date_valeur,
    {{ date_x3('bandat_0') }}               as date_remise_banque,
    fiy_0                                   as numero_exercice,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
