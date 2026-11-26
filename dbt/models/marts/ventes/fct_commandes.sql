{#
  Grain : une ligne = une commande client.
  Définitions : docs/indicateurs/commandes_livraisons.md

      jours_commande_expedition = première expédition - date de commande
      reste_a_livrer            = quantité commandée - quantité livrée (lignes),
                                  pour une commande ouverte
      soldee_sans_livraison     = commande soldée (fermée) sans aucune livraison :
                                  annulée, ou saisie en double
#}

with livraisons as (

    select
        numero_commande,
        count(*)                                        as livraisons,
        min(date_expedition)                            as premiere_expedition,
        max(date_expedition)                            as derniere_expedition,
        sum(montant_ht)                                 as montant_livre_ht,
        sum(montant_ht) filter (where est_facturee)     as montant_facture_ht
    from {{ ref('fct_livraisons') }}
    group by numero_commande

),

lignes as (

    select
        numero_commande,
        sum(quantite_commandee)                         as quantite_commandee,
        sum(quantite_livree)                            as quantite_livree
    from {{ ref('stg_x3__lignes_commande') }}
    group by numero_commande

)

select
    cast(c.numero_commande as text)                                     as numero_commande,
    cast(c.societe as text)                                             as societe,
    cast(c.site as text)                                                as site,
    cast({{ cle_x3('c.client') }} as text)                              as cle_client,
    cast(c.client as text)                                              as code_client,
    cast(c.representant as text)                                        as representant,
    cast(c.date_commande as date)                                       as date_commande,
    cast(c.date_livraison_demandee as date)                             as date_livraison_demandee,
    cast(c.statut_commande as text)                                     as statut_commande,
    cast(c.statut_livraison as text)                                    as statut_livraison,
    cast(c.statut_facturation as text)                                  as statut_facturation,
    cast(c.est_bloquee as boolean)                                      as est_bloquee,
    cast(c.montant_ht as numeric(28, 2))                                as montant_ht,
    cast(coalesce(l.livraisons, 0) as integer)                          as livraisons,
    cast(l.premiere_expedition as date)                                 as premiere_expedition,
    cast(l.derniere_expedition as date)                                 as derniere_expedition,
    cast(case when l.premiere_expedition >= c.date_commande
              then l.premiere_expedition - c.date_commande end as integer)
                                                                        as jours_commande_expedition,
    cast(l.montant_livre_ht as numeric(28, 2))                          as montant_livre_ht,
    cast(l.montant_facture_ht as numeric(28, 2))                        as montant_facture_ht,
    cast(q.quantite_commandee as numeric(18, 3))                        as quantite_commandee,
    cast(q.quantite_livree as numeric(18, 3))                           as quantite_livree,
    cast(case when c.statut_commande = 'ouverte'
              then greatest(q.quantite_commandee - q.quantite_livree, 0) end as numeric(18, 3))
                                                                        as reste_a_livrer,
    cast(c.statut_commande = 'soldée' and c.statut_livraison = 'non livrée' as boolean)
                                                                        as soldee_sans_livraison
from {{ ref('stg_x3__commandes') }} as c
left join livraisons as l
    on l.numero_commande = c.numero_commande
left join lignes as q
    on q.numero_commande = c.numero_commande
