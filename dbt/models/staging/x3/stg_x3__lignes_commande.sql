{#
  Grain : une ligne = une ligne de commande client (ligne × séquence).
  Source : raw_x3.sorderq (quantités).
#}

with source as (

    select * from {{ source('x3', 'sorderq') }}

)

select
    {{ texte_x3('sohnum_0') }}                  as numero_commande,
    soplin_0                                    as ligne,
    soqseq_0                                    as sequence,
    {{ texte_x3('itmref_0') }}                  as article,
    {{ texte_x3('stofcy_0') }}                  as site_stock,
    {{ date_x3('orddat_0') }}                   as date_commande,
    {{ date_x3('demdlvdat_0') }}                as date_livraison_demandee,
    soqsta_0                                    as code_statut,
    qty_0                                       as quantite_commandee,
    dlvqty_0                                    as quantite_livree,
    invqty_0                                    as quantite_facturee,
    odlqty_0                                    as quantite_en_livraison,
    allqty_0                                    as quantite_allouee,
    _source,
    _charge_le
from source
where {{ texte_x3('sohnum_0') }} is not null
