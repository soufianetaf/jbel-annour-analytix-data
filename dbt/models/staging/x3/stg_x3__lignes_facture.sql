{#
  Grain : une ligne = une ligne d'un document de vente (facture, avoir, pro forma).
  Source : raw_x3.sinvoiced (Sage X3, SINVOICED).

  Nettoyage seulement, aucune règle métier (voir stg_x3__factures).

  Colonne volontairement NON reprise : CPRPRI_0 (coût de revient de la
  ligne). Elle est fausse sur des milliers de lignes (cahier des charges,
  5.1) : jamais de marge calculée avec ce champ. Elle reste dans raw_x3.
#}

with source as (

    select * from {{ source('x3', 'sinvoiced') }}

)

select
    -- Identifiant
    {{ texte_x3('num_0') }}                 as numero_facture,
    sidlin_0                                as numero_ligne,

    -- Rattachement
    {{ texte_x3('bpcinv_0') }}              as client_facture,
    {{ texte_x3('rep1_0') }}                as representant,
    {{ texte_x3('rep2_0') }}                as representant_2,
    {{ texte_x3('salfcy_0') }}              as site_vente,
    {{ texte_x3('stofcy_0') }}              as site_stock,

    -- Origine : commande et livraison
    {{ texte_x3('sohnum_0') }}              as numero_commande,
    soplin_0                                as ligne_commande,
    {{ texte_x3('sdhnum_0') }}              as numero_livraison,
    sddlin_0                                as ligne_livraison,

    -- Article
    {{ texte_x3('itmref_0') }}              as article,
    {{ texte_x3('itmdes1_0') }}             as designation,

    -- Quantités
    qty_0                                   as quantite,
    {{ texte_x3('sau_0') }}                 as unite_vente,
    qtystu_0                                as quantite_stock,
    {{ texte_x3('stu_0') }}                 as unite_stock,

    -- Prix et montants (positifs, comme dans X3)
    gropri_0                                as prix_brut,
    netpri_0                                as prix_net,
    amtnotlin_0                             as montant_ht,
    amtatilin_0                             as montant_ttc,
    {{ texte_x3('vat_0') }}                 as code_tva,

    -- Date
    {{ date_x3('invdat_0') }}               as date_facture,

    -- Suivi dans Sage X3
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,

    -- Traçabilité du chargement
    _source,
    _charge_le

from source
