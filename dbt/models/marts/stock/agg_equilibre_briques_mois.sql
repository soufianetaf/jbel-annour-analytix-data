{#
  Grain : une ligne = un mois. Définitions : docs/indicateurs/equilibre_briques.md

  Ce qui est produit, stocké et vendu, en tonnes de briques :

      tonnes cuites          automate du four (depuis le 26/11/2025)
      production déclarée    entrées de production dans Sage X3 (mouvements de type 5)
      livraisons             sorties de livraison dans Sage X3 (type 4)
      ventes facturées       factures et avoirs des articles briques
      stock de fin de mois   stock d'aujourd'hui moins les mouvements postérieurs
                             à la fin du mois (reconstitué : Sage X3 ne garde
                             pas le stock passé)

  Les transferts entre dépôts (types 1 et 2) s'annulent : ils ne changent
  pas le stock total. Les quantités X3 sont en unités, passées en tonnes
  avec le poids de chaque article (int_cout_revient__poids_briques).
#}

with poids as (

    select cle_article, poids_kg from {{ ref('int_cout_revient__poids_briques') }}

),

mouvements as (

    select
        cast(date_trunc('month', m.date_mouvement) as date)                         as mois,
        sum(m.quantite * p.poids_kg) filter (where m.code_type_mouvement = 5) / 1000 as production_declaree,
        -sum(m.quantite * p.poids_kg) filter (where m.code_type_mouvement = 4) / 1000 as livraisons,
        sum(m.quantite * p.poids_kg) / 1000                                         as variation_stock
    from {{ ref('fct_mouvements_stock') }} as m
    inner join poids as p
        on p.cle_article = m.cle_article
    group by 1

),

stock_actuel as (

    select sum(s.stock_physique * p.poids_kg) / 1000 as tonnes
    from {{ ref('fct_stock_article') }} as s
    inner join poids as p
        on p.cle_article = s.cle_article

),

mois as (

    select cast(date_trunc('month', d) as date) as mois
    from generate_series(date '2025-01-01', current_date, interval '1 month') as d

),

cuites as (

    select cast(date_trunc('month', jour) as date) as mois, sum(production) as tonnes_cuites
    from {{ ref('fct_machines_jour') }}
    where machine = 'four'
    group by 1

),

ventes as (

    select mois, sum(tonnes_vendues) as tonnes_vendues
    from {{ ref('agg_marge_type_brique_mois') }}
    group by mois

),

assemble as (

    select
        m.mois,
        c.tonnes_cuites,
        coalesce(mv.production_declaree, 0)                                         as production_declaree,
        coalesce(mv.livraisons, 0)                                                  as livraisons,
        v.tonnes_vendues,
        coalesce(mv.variation_stock, 0)                                             as variation_stock,
        -- Mouvements des mois suivants, à retirer du stock d'aujourd'hui
        coalesce(sum(mv.variation_stock) over (
            order by m.mois rows between 1 following and unbounded following
        ), 0)                                                                       as mouvements_apres
    from mois as m
    left join mouvements as mv on mv.mois = m.mois
    left join cuites as c on c.mois = m.mois
    left join ventes as v on v.mois = m.mois

)

select
    cast(a.mois as date)                                                            as mois,
    cast(a.tonnes_cuites as numeric(18, 3))                                         as tonnes_cuites,
    cast(a.production_declaree as numeric(18, 3))                                   as production_declaree,
    cast(a.livraisons as numeric(18, 3))                                            as livraisons,
    cast(a.tonnes_vendues as numeric(18, 3))                                        as tonnes_vendues,
    cast(a.variation_stock as numeric(18, 3))                                       as variation_stock,
    cast(s.tonnes - a.mouvements_apres as numeric(18, 3))                           as stock_fin_mois,
    cast(a.production_declaree / nullif(a.tonnes_cuites, 0) as numeric(8, 4))       as ratio_declaree_cuite
from assemble as a
cross join stock_actuel as s
