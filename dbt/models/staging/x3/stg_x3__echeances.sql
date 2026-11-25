{#
  Grain : une ligne = une échéance d'une pièce comptable (client ou fournisseur).
  Source : raw_x3.gaccdudate (Sage X3, GACCDUDATE), copiée en incrémental.

  Nettoyage seulement. Les montants restent POSITIFS comme dans X3 ; le
  sens est dans « signe ». Le reste à payer et la balance âgée sont
  calculés dans marts (docs/indicateurs/finance_creances.md).

  Ligne retirée : l'échéance technique vide (sans numéro de pièce).
#}

with source as (

    select * from {{ source('x3', 'gaccdudate') }}

)

select
    -- Identifiant : pièce, ligne, numéro d'échéance
    {{ texte_x3('typ_0') }}                 as type_piece,
    {{ texte_x3('num_0') }}                 as numero_piece,
    lig_0                                   as ligne_piece,
    dudlig_0                                as numero_echeance,
    accnum_0                                as numero_ecriture,

    -- Tiers
    bprtyp_0                                as code_type_tiers,    -- 1 client, 2 fournisseur
    {{ texte_x3('bpr_0') }}                 as tiers,
    {{ texte_x3('bprpay_0') }}              as tiers_payeur,
    {{ texte_x3('sac_0') }}                 as compte_collectif,   -- CT, FL, EFA…

    -- Rattachement
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcy_0') }}                 as site,
    {{ texte_x3('soinum_0') }}              as numero_document_origine,
    fiy_0                                   as exercice,
    per_0                                   as periode,

    -- Échéance
    {{ date_x3('duddat_0') }}               as date_echeance,
    {{ texte_x3('pam_0') }}                 as mode_paiement,      -- LCR, CHQ, VIR…
    sns_0                                   as signe,
    {{ texte_x3('cur_0') }}                 as devise,

    -- Montants positifs, en devise du document et en MAD (monnaie société)
    amtcur_0                                as montant_devise,
    amtloc_0                                as montant,
    paycur_0                                as paye_devise,
    payloc_0                                as paye,
    tmploc_0                                as en_cours_paiement,

    -- Suivi
    flgcle_0                                as code_lettrage,      -- 1 non lettrée, 2 lettrée
    dudsta_0                                as code_statut,
    {{ date_x3('paydat_0') }}               as date_paiement,
    levfup_0                                as niveau_relance,
    {{ date_x3('datfup_0') }}               as date_derniere_relance,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
