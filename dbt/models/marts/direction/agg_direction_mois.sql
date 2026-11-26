{#
  Grain : une ligne = un mois. Tableau de bord de la direction.

  Chaque chiffre vient d'une table déjà rapprochée de sa source ; rien n'est
  recalculé ici, seulement réuni :
      ca_net                 fct_ventes (CA de Sage X3)
      resultat               agg_compte_de_resultat_mois (clôtures exclues)
      tresorerie_fin_mois    fct_ecritures, comptes 51 et 55 hors clôture (cumul de l'exercice)
      tonnes_cuites          fct_machines_jour (four)
      tonnes_briques_vendues agg_marge_type_brique_mois
      cout_par_tonne         agg_cout_revient_mois (12 mois glissants)
      kwh_par_tonne          agg_energie_jour (jours où l'électricité est complète)
      heures_arret_maintenance agg_maintenance_zone_jour
#}

with mois as (

    select cast(date_trunc('month', d) as date) as mois
    from generate_series(date '2025-01-01', current_date, interval '1 month') as d

),

ventes as (

    select cast(date_trunc('month', date_comptable) as date) as mois, sum(montant_ht_signe) as ca_net
    from {{ ref('fct_ventes') }}
    group by 1

),

resultat as (

    select mois, sum(montant_resultat) as resultat
    from {{ ref('agg_compte_de_resultat_mois') }}
    group by 1

),

tresorerie_mois as (

    -- Mouvements des comptes 51 et 55 par mois, SANS la pièce de clôture :
    -- au 31/12, la clôture remet ces comptes à zéro (les à-nouveaux du
    -- 1er janvier les rouvrent). Avec elle, la trésorerie de décembre vaudrait 0.
    select
        cast(date_trunc('month', date_comptable) as date)   as mois,
        numero_exercice,
        sum(solde)                                          as mouvement
    from {{ ref('fct_ecritures') }}
    where left(compte, 2) in ('51', '55')
      and not est_cloture
    group by 1, 2

),

tresorerie as (

    -- Cumul dans l'exercice, à-nouveaux compris
    select
        mois,
        sum(mouvement) over (partition by numero_exercice order by mois)    as tresorerie_fin_mois
    from tresorerie_mois

),

briques as (

    select mois, sum(tonnes_vendues) as tonnes_vendues, sum(marge) as marge_briques
    from {{ ref('agg_marge_type_brique_mois') }}
    group by 1

),

energie as (

    select
        cast(date_trunc('month', jour) as date)                         as mois,
        sum(kwh_site) filter (where electricite_complete)
            / nullif(sum(tonnes_cuites) filter (where electricite_complete), 0) as kwh_par_tonne
    from {{ ref('agg_energie_jour') }}
    group by 1

),

maintenance as (

    select cast(date_trunc('month', jour) as date) as mois, sum(minutes_arret) / 60.0 as heures_arret
    from {{ ref('agg_maintenance_zone_jour') }}
    group by 1

)

select
    cast(m.mois as date)                                        as mois,
    cast(v.ca_net as numeric(28, 2))                            as ca_net,
    cast(r.resultat as numeric(28, 2))                          as resultat,
    cast(t.tresorerie_fin_mois as numeric(28, 2))               as tresorerie_fin_mois,
    cast(c.tonnes_cuites as numeric(18, 3))                     as tonnes_cuites,
    cast(b.tonnes_vendues as numeric(18, 3))                    as tonnes_briques_vendues,
    cast(c.cout_par_tonne_12_mois as numeric(18, 2))            as cout_par_tonne,
    cast(c.cout_energie_par_tonne_12_mois as numeric(18, 2))    as cout_energie_par_tonne,
    cast(b.marge_briques as numeric(28, 2))                     as marge_briques,
    cast(e.kwh_par_tonne as numeric(12, 3))                     as kwh_par_tonne,
    cast(mt.heures_arret as numeric(12, 2))                     as heures_arret_maintenance
from mois as m
left join ventes as v on v.mois = m.mois
left join resultat as r on r.mois = m.mois
left join tresorerie as t on t.mois = m.mois
left join {{ ref('agg_cout_revient_mois') }} as c on c.mois = m.mois
left join briques as b on b.mois = m.mois
left join energie as e on e.mois = m.mois
left join maintenance as mt on mt.mois = m.mois
