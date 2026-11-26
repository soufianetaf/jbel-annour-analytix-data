{#
  Grain : une ligne = une ligne de livraison client.
  Source : raw_x3.sdeliveryd.
#}

with source as (

    select * from {{ source('x3', 'sdeliveryd') }}

)

select
    {{ texte_x3('sdhnum_0') }}                  as numero_livraison,
    sddlin_0                                    as ligne,
    {{ texte_x3('sohnum_0') }}                  as numero_commande,
    soplin_0                                    as ligne_commande,
    soqseq_0                                    as sequence_commande,
    {{ texte_x3('itmref_0') }}                  as article,
    {{ date_x3('shidat_0') }}                   as date_expedition,
    qty_0                                       as quantite_livree,
    rtnqty_0                                    as quantite_retournee,
    netprinot_0                                 as prix_net_ht,
    {{ texte_x3('sau_0') }}                     as unite_vente,
    _source,
    _charge_le
from source
where {{ texte_x3('sdhnum_0') }} is not null
