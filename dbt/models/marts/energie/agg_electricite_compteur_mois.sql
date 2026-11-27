{#
  Grain : une ligne = un compteur électrique × un mois.

  Pour suivre chaque poste mois par mois (éclairage, compresseur, séchoir…).
  Les jours sans mesure valide (collecte arrêtée, valeur aberrante) ne sont
  pas comptés comme 0 : on donne les kWh MESURÉS, le nombre de jours mesurés
  et la moyenne par jour mesuré, pour comparer des mois inégalement relevés.

      kwh_mesures        = somme des kWh valides du mois
      jours_mesures      = jours avec un kWh valide
      couverture         = jours_mesures / jours du mois (jours écoulés pour le mois en cours)
      kwh_par_jour       = kwh_mesures / jours_mesures
      kwh_mois_estime    = kwh_par_jour × jours du mois, seulement si la couverture
                           atteint 80 % (sinon vide : trop peu de jours pour estimer)
#}

with jours as (

    select
        compteur,
        max(niveau)                                                         as niveau,
        cast(date_trunc('month', jour) as date)                             as mois,
        sum(kwh)                                                            as kwh_mesures,
        count(kwh)                                                          as jours_mesures
    from {{ ref('fct_electricite_jour') }}
    group by compteur, cast(date_trunc('month', jour) as date)

),

calendrier as (

    select
        j.*,
        -- Jours du mois ; pour le mois en cours, jours écoulés
        case
            when j.mois = cast(date_trunc('month', current_date) as date)
                then extract(day from current_date)::integer
            else extract(day from (j.mois + interval '1 month' - interval '1 day'))::integer
        end                                                                 as jours_mois
    from jours as j

)

select
    cast(compteur as text)                                                  as compteur,
    cast(niveau as text)                                                    as niveau,
    cast(mois as date)                                                      as mois,
    cast(kwh_mesures as numeric(18, 3))                                     as kwh_mesures,
    cast(jours_mesures as integer)                                          as jours_mesures,
    cast(jours_mois as integer)                                             as jours_mois,
    cast(jours_mesures::numeric / nullif(jours_mois, 0) as numeric(6, 4))   as couverture,
    cast(kwh_mesures / nullif(jours_mesures, 0) as numeric(18, 3))          as kwh_par_jour,
    cast(case when jours_mesures::numeric / nullif(jours_mois, 0) >= 0.8
              then kwh_mesures / jours_mesures * jours_mois end as numeric(18, 3))
                                                                            as kwh_mois_estime
from calendrier
