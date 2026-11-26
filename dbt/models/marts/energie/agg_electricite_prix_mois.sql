{#
  Grain : une ligne = un mois. Définitions : docs/indicateurs/energie.md

  Prix du kWh = facture d'électricité (comptes 61251, compte de résultat) /
  kWh des transformateurs. Deux corrections :
  1. les kWh manquent les jours de panne de collecte : kWh estimés = kWh
     moyen d'un jour complet × nombre de jours (du mois, ou des 12 mois) ;
  2. les factures sont comptabilisées irrégulièrement (aucune certains mois,
     deux d'autres) : le prix se lit sur 12 mois glissants, calculé dès que
     les 12 mois ont 180 jours complets de compteurs.

  Pénalité de cos φ estimée = énergie réactive excédentaire des
  transformateurs (cos φ < 0,8) × tarif du contrat, à renseigner dans la
  variable dbt « tarif_energie_reactive_mad_kvarh » (vide tant qu'il n'est pas connu).
#}

{% set tarif_reactif = var('tarif_energie_reactive_mad_kvarh', none) %}

with mois as (

    select cast(date_trunc('month', d) as date) as mois
    from generate_series(date '2025-11-01', current_date, interval '1 month') as d

),

kwh as (

    select
        cast(date_trunc('month', jour) as date)                             as mois,
        avg(kwh_site) filter (where electricite_complete)                   as kwh_jour_complet,
        sum(kwh_site) filter (where electricite_complete)                   as kwh_mesures,
        count(*) filter (where electricite_complete)                        as jours_complets
    from {{ ref('agg_energie_jour') }}
    group by 1

),

reactif as (

    select
        cast(date_trunc('month', jour) as date)                             as mois,
        sum(energie_reactive_excedentaire_kvarh)                            as reactif_excedentaire
    from {{ ref('fct_electricite_jour') }}
    where compteur in ('transfo1', 'transfo2')
    group by 1

),

facture as (

    select mois, sum(charge) as facture
    from {{ ref('fct_charges_production_mois') }}
    where famille_cout = 'électricité'
    group by mois

),

mensuel as (

    select
        m.mois,
        coalesce(f.facture, 0)                                              as facture,
        k.kwh_mesures,
        k.jours_complets,
        k.kwh_jour_complet
            * extract(day from (m.mois + interval '1 month' - interval '1 day'))
                                                                            as kwh_estimes,
        r.reactif_excedentaire
    from mois as m
    left join kwh as k on k.mois = m.mois
    left join facture as f on f.mois = m.mois
    left join reactif as r on r.mois = m.mois

),

glissant as (

    -- Sur 12 mois : kWh moyen d'un jour complet de la période × jours de la période
    select
        *,
        sum(facture) over douze                                             as facture_12_mois,
        sum(kwh_mesures) over douze / nullif(sum(jours_complets) over douze, 0)
            * sum(extract(day from (mois + interval '1 month' - interval '1 day'))) over douze
                                                                            as kwh_estimes_12_mois,
        sum(jours_complets) over douze                                      as jours_complets_12_mois,
        count(*) over douze                                                 as mois_de_la_periode
    from mensuel
    window douze as (order by mois rows between 11 preceding and current row)

)

select
    cast(mois as date)                                                      as mois,
    cast(facture as numeric(18, 2))                                         as facture_electricite,
    cast(kwh_mesures as numeric(18, 3))                                     as kwh_mesures,
    cast(jours_complets as integer)                                         as jours_complets,
    cast(kwh_estimes as numeric(18, 3))                                     as kwh_estimes,
    cast(facture_12_mois as numeric(18, 2))                                 as facture_12_mois,
    cast(kwh_estimes_12_mois as numeric(18, 3))                             as kwh_estimes_12_mois,
    cast(jours_complets_12_mois as integer)                                 as jours_complets_12_mois,
    -- Au moins 12 mois de factures et 180 jours complets de compteurs
    cast(case when mois_de_la_periode = 12 and jours_complets_12_mois >= 180
              then facture_12_mois / nullif(kwh_estimes_12_mois, 0) end as numeric(10, 4))
                                                                            as prix_kwh_12_mois,
    cast(reactif_excedentaire as numeric(18, 3))                            as energie_reactive_excedentaire_kvarh,
    cast({{ 'reactif_excedentaire * ' ~ tarif_reactif if tarif_reactif is not none else 'null' }} as numeric(18, 2))
                                                                            as penalite_cos_phi_estimee
from glissant
