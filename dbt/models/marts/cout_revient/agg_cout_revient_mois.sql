{#
  Grain : une ligne = un mois.

  Coût de revient par tonne cuite (docs/indicateurs/cout_revient.md) :

      charges de production = charges d'exploitation (61) hors marchandises revendues
      coût par tonne du mois     = charges du mois / tonnes cuites du mois
      coût par tonne sur 12 mois = charges des 12 derniers mois / tonnes des 12 derniers mois

  Le coût sur 12 mois glissants est l'indicateur à lire : les amortissements
  ne sont passés qu'en décembre (24 M MAD en 2025) et certaines charges sont
  régularisées d'un mois sur l'autre. Il n'est calculé que si les 12 mois
  ont des tonnes cuites (automate du four, depuis le 26/11/2025).
#}

with mois as (

    select cast(date_trunc('month', d) as date) as mois
    from generate_series(date '2025-01-01', current_date, interval '1 month') as d

),

charges as (

    select
        mois,
        sum(charge) filter (where famille_cout <> 'hors coût de revient')       as charges_production,
        sum(charge) filter (where famille_cout in ('combustibles', 'électricité')) as charges_energie,
        sum(charge) filter (where famille_cout = 'amortissements et provisions') as amortissements
    from {{ ref('fct_charges_production_mois') }}
    group by mois

),

tonnes as (

    select cast(date_trunc('month', jour) as date) as mois, sum(production) as tonnes_cuites
    from {{ ref('fct_machines_jour') }}
    where machine = 'four'
    group by 1

),

mensuel as (

    select
        m.mois,
        coalesce(c.charges_production, 0)                                       as charges_production,
        coalesce(c.charges_energie, 0)                                          as charges_energie,
        coalesce(c.amortissements, 0)                                           as amortissements,
        t.tonnes_cuites
    from mois as m
    left join charges as c on c.mois = m.mois
    left join tonnes as t on t.mois = m.mois

),

glissant as (

    select
        *,
        sum(charges_production) over douze                                      as charges_12_mois,
        sum(charges_energie) over douze                                         as charges_energie_12_mois,
        sum(tonnes_cuites) over douze                                           as tonnes_12_mois,
        count(tonnes_cuites) over douze                                         as mois_avec_tonnes
    from mensuel
    window douze as (order by mois rows between 11 preceding and current row)

)

select
    cast(mois as date)                                                          as mois,
    cast(charges_production as numeric(28, 2))                                  as charges_production,
    cast(charges_energie as numeric(28, 2))                                     as charges_energie,
    cast(amortissements as numeric(28, 2))                                      as amortissements,
    cast(tonnes_cuites as numeric(18, 3))                                       as tonnes_cuites,
    cast(charges_production / nullif(tonnes_cuites, 0) as numeric(18, 2))       as cout_par_tonne_mois,
    cast(charges_energie / nullif(tonnes_cuites, 0) as numeric(18, 2))          as cout_energie_par_tonne_mois,
    cast(charges_12_mois as numeric(28, 2))                                     as charges_12_mois,
    cast(tonnes_12_mois as numeric(18, 3))                                      as tonnes_12_mois,
    cast(case when mois_avec_tonnes = 12
              then charges_12_mois / nullif(tonnes_12_mois, 0) end as numeric(18, 2))
                                                                                as cout_par_tonne_12_mois,
    cast(case when mois_avec_tonnes = 12
              then charges_energie_12_mois / nullif(tonnes_12_mois, 0) end as numeric(18, 2))
                                                                                as cout_energie_par_tonne_12_mois,
    cast(mois_avec_tonnes as integer)                                           as mois_avec_tonnes
from glissant
