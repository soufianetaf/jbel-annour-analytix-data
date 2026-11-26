{#
  Grain : une ligne = une livraison client (bon de livraison).
  Définitions : docs/indicateurs/commandes_livraisons.md

      jours_expedition_facture = date comptable de la facture - date d'expédition
                                 (vide si la facture est datée AVANT l'expédition :
                                 erreur de date, comptée par un test)
      jours_sans_facture       = aujourd'hui - date d'expédition, pour une
                                 livraison validée pas encore facturée
#}

with livraisons as (

    select * from {{ ref('stg_x3__livraisons') }}

),

factures as (

    select numero_facture, date_comptable from {{ ref('stg_x3__factures') }}

)

select
    cast(l.numero_livraison as text)                                    as numero_livraison,
    cast(l.numero_commande as text)                                     as numero_commande,
    cast(l.societe as text)                                             as societe,
    cast(l.site as text)                                                as site,
    cast({{ cle_x3('l.client') }} as text)                              as cle_client,
    cast(l.client as text)                                              as code_client,
    cast(l.representant as text)                                        as representant,
    cast(l.date_expedition as date)                                     as date_expedition,
    cast(l.est_validee as boolean)                                      as est_validee,
    cast(l.est_facturee as boolean)                                     as est_facturee,
    cast(l.numero_facture as text)                                      as numero_facture,
    cast(f.date_comptable as date)                                      as date_facture,
    cast(case when f.date_comptable >= l.date_expedition
              then f.date_comptable - l.date_expedition end as integer) as jours_expedition_facture,
    cast(case when l.est_validee and not l.est_facturee
              then current_date - l.date_expedition end as integer)     as jours_sans_facture,
    cast(l.montant_ht as numeric(28, 2))                                as montant_ht,
    cast(l.poids_net as numeric(18, 3))                                 as poids_net,
    cast(l.unite_poids as text)                                         as unite_poids
from livraisons as l
left join factures as f
    on f.numero_facture = l.numero_facture
