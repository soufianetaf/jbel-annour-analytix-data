{#
  Grain : une ligne = une ligne d'écriture comptable, dans un registre
  (1 comptabilité générale, 2 analytique).
  Source : raw_x3.gaccentryd (Sage X3, GACCENTRYD), copiée en incrémental,
  sans libellé ni nom de tiers.

  Nettoyage seulement : montants positifs, sens séparé (comme dans X3).
#}

with source as (

    select * from {{ source('x3', 'gaccentryd') }}

)

select
    -- Identifiant
    {{ texte_x3('typ_0') }}                 as type_piece,
    {{ texte_x3('num_0') }}                 as numero_piece,
    lin_0                                   as ligne,
    ledtyp_0                                as registre,           -- 1 général, 2 analytique
    accnum_0                                as numero_ecriture,

    -- Rattachement
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcylin_0') }}              as site,
    {{ date_x3('accdat_0') }}               as date_comptable,
    fiy_0                                   as numero_exercice,
    per_0                                   as periode,

    -- Compte
    {{ texte_x3('coa_0') }}                 as plan_comptable,
    {{ texte_x3('acc_0') }}                 as compte,
    {{ texte_x3('sac_0') }}                 as compte_collectif,
    {{ texte_x3('bpr_0') }}                 as tiers,

    -- Montants positifs ; sens 1 = débit, -1 = crédit
    sns_0                                   as sens,
    {{ texte_x3('cur_0') }}                 as devise,
    amtcur_0                                as montant_devise,
    amtled_0                                as montant,
    qty_0                                   as quantite,
    {{ texte_x3('uom_0') }}                 as unite,
    flgmtc_0                                as code_lettrage,

    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
