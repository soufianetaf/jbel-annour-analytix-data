{#
  Grain : une ligne = une livraison client (bon de livraison).
  Source : raw_x3.sdelivery, sans chauffeur, plaque ni destinataire.

  Drapeaux de Sage X3 (1 = non, 2 = oui) traduits en vrai / faux.
#}

with source as (

    select * from {{ source('x3', 'sdelivery') }}

)

select
    {{ texte_x3('sdhnum_0') }}                  as numero_livraison,
    {{ texte_x3('sohnum_0') }}                  as numero_commande,
    {{ texte_x3('cpy_0') }}                     as societe,
    {{ texte_x3('salfcy_0') }}                  as site,
    {{ texte_x3('stofcy_0') }}                  as site_stock,
    {{ texte_x3('bpcord_0') }}                  as client,
    {{ texte_x3('rep_0') }}                     as representant,
    {{ date_x3('shidat_0') }}                   as date_expedition,
    {{ date_x3('dlvdat_0') }}                   as date_livraison,
    cfmflg_0 = 2                                as est_validee,
    invflg_0 = 2                                as est_facturee,
    {{ texte_x3('sihnum_0') }}                  as numero_facture,
    dlvnot_0                                    as montant_ht,
    netwei_0                                    as poids_net,
    {{ texte_x3('weu_0') }}                     as unite_poids,
    _source,
    _charge_le
from source
where {{ texte_x3('sdhnum_0') }} is not null
