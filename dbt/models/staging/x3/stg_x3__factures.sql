{#
  Grain : une ligne = un document de vente (facture, avoir ou pro forma).
  Source : raw_x3.sinvoice (Sage X3, SINVOICE).

  Nettoyage seulement, aucune règle métier :
  - noms de colonnes en français ;
  - espaces → vide, dates 1753 / 1900 → vide (macros nettoyage_x3) ;
  - liste de colonnes explicite : une colonne ajoutée dans X3 n'apparaît
    pas ici sans décision.

  Les montants restent POSITIFS, comme dans X3 : le signe des avoirs est
  dans la colonne « signe ». Le chiffre d'affaires (factures moins avoirs,
  hors pro forma) est calculé dans les couches suivantes.

  Ligne retirée : l'entête technique sans numéro (vide, daté de 1753, sans
  aucune ligne de facture), signalée par le cahier des charges (5.1).
#}

with source as (

    select * from {{ source('x3', 'sinvoice') }}

)

select
    -- Identifiant
    {{ texte_x3('num_0') }}                 as numero_facture,

    -- Nature du document
    {{ texte_x3('sivtyp_0') }}              as type_facture,       -- FAC, AVF, AVR, PRF
    invtyp_0                                as code_categorie,     -- 1 facture, 2 avoir, 5 pro forma
    sns_0                                   as signe,              -- 1 ou -1 (avoir)
    sta_0                                   as code_statut,

    -- Rattachement
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcy_0') }}                 as site,
    {{ texte_x3('bpr_0') }}                 as client,
    {{ texte_x3('bprnam_0') }}              as nom_client,
    {{ texte_x3('bprpay_0') }}              as client_payeur,

    -- Dates
    {{ date_x3('accdat_0') }}               as date_comptable,
    {{ date_x3('strduddat_0') }}            as date_depart_echeance,
    {{ texte_x3('pte_0') }}                 as condition_paiement,

    -- Montants (positifs, en devise du document)
    {{ texte_x3('cur_0') }}                 as devise,
    amtnot_0                                as montant_ht,
    amtati_0                                as montant_ttc,

    -- Suivi dans Sage X3
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,

    -- Traçabilité du chargement
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
