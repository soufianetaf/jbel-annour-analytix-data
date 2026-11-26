{#
  Grain : une ligne = un mois. Définitions : docs/indicateurs/commandes_livraisons.md

  Le cycle commande → expédition → facture, par mois :
  - commandes du mois (date de commande) et celles soldées sans livraison ;
  - livraisons du mois (date d'expédition) et leur délai jusqu'à la facture.
#}

with commandes as (

    select
        cast(date_trunc('month', date_commande) as date)                    as mois,
        count(*)                                                            as commandes,
        sum(montant_ht)                                                     as montant_commande_ht,
        avg(jours_commande_expedition)                                      as jours_moyens_commande_expedition,
        count(*) filter (where soldee_sans_livraison)                       as soldees_sans_livraison,
        sum(montant_ht) filter (where soldee_sans_livraison)                as montant_soldees_sans_livraison
    from {{ ref('fct_commandes') }}
    where date_commande is not null
    group by 1

),

livraisons as (

    select
        cast(date_trunc('month', date_expedition) as date)                  as mois,
        count(*)                                                            as livraisons,
        sum(montant_ht)                                                     as montant_livre_ht,
        percentile_cont(0.5) within group (order by jours_expedition_facture) as jours_median_expedition_facture,
        count(*) filter (where est_facturee)                                as livraisons_facturees,
        sum(montant_ht) filter (where est_validee and not est_facturee)     as montant_livre_non_facture
    from {{ ref('fct_livraisons') }}
    where date_expedition is not null
    group by 1

)

select
    cast(coalesce(c.mois, l.mois) as date)                                  as mois,
    cast(coalesce(c.commandes, 0) as integer)                               as commandes,
    cast(c.montant_commande_ht as numeric(28, 2))                           as montant_commande_ht,
    cast(c.jours_moyens_commande_expedition as numeric(8, 2))               as jours_moyens_commande_expedition,
    cast(coalesce(c.soldees_sans_livraison, 0) as integer)                  as commandes_soldees_sans_livraison,
    cast(c.montant_soldees_sans_livraison as numeric(28, 2))                as montant_soldees_sans_livraison,
    cast(coalesce(l.livraisons, 0) as integer)                              as livraisons,
    cast(l.montant_livre_ht as numeric(28, 2))                              as montant_livre_ht,
    cast(l.jours_median_expedition_facture as numeric(8, 1))                as jours_median_expedition_facture,
    cast(coalesce(l.livraisons_facturees, 0) as integer)                    as livraisons_facturees,
    cast(l.montant_livre_non_facture as numeric(28, 2))                     as montant_livre_non_facture
from commandes as c
full outer join livraisons as l
    on l.mois = c.mois
