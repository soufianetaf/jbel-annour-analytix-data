{#
  Grain : une ligne = un article sur un site de stockage, état ACTUEL.

  Définitions : docs/indicateurs/stock_valorise.md
      valeur_stock = stock_physique × CMUP        en MAD
      article dormant = en stock, sans sortie depuis 365 jours (ou jamais)

  Pour l'historique : snapshots.snap_stock_jour (une photo par jour).
#}

with stock as (

    select * from {{ ref('stg_x3__stock_articles') }}

)

select
    cast({{ cle_x3('article') }} as text)                       as cle_article,
    cast(article as text)                                       as code_article,
    cast(site as text)                                          as site,
    cast(stock_physique as numeric(28, 10))                     as stock_physique,
    cast(stock_controle as numeric(28, 10))                     as stock_controle,
    cast(stock_rejete as numeric(28, 10))                       as stock_rejete,
    cast(quantite_allouee as numeric(28, 10))                   as quantite_allouee,
    cast(quantite_commandee as numeric(28, 10))                 as quantite_commandee,
    cast(cmup as numeric(28, 10))                               as cmup,
    cast(stock_physique * cmup as numeric(28, 10))              as valeur_stock,
    cast(dernier_prix_achat as numeric(28, 10))                 as dernier_prix_achat,
    cast(date_dernier_achat as date)                            as date_dernier_achat,
    cast(date_derniere_reception as date)                       as date_derniere_reception,
    cast(date_derniere_sortie as date)                          as date_derniere_sortie,
    cast(stock_physique > 0
         and (date_derniere_sortie is null
              or date_derniere_sortie < {{ date_du_jour() }} - 365) as boolean)
                                                                as est_dormant,
    cast({{ date_du_jour() }} as date)                          as date_calcul,
    cast(_charge_le as timestamp with time zone)                as charge_le
from stock
