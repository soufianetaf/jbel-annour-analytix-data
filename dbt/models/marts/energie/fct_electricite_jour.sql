{#
  Grain : une ligne = un compteur électrique × un jour.

  Consommation du jour J (kWh) : la « consommation de la veille » que le
  compteur affiche le jour J+1 (cons_P_total_j_1). Elle est constante toute
  la journée J+1 (vérifié le 26/11/2026) ; à défaut, la dernière valeur.
  On n'utilise PAS l'index d'énergie : il recule plusieurs fois par jour
  (plus de 700 fois par compteur en un an) et fait des sauts aberrants
  (jusqu'à 10^14) ; la somme de ses écarts donne la moitié de la valeur
  du compteur. Le dernier jour n'a pas encore de consommation (connue le
  lendemain).

  Valeur plausible : entre 0 et puissance maximale du jour × 24 h (+10 %
  pour le pic tombé entre deux relevés). Une vingtaine de jours par compteur
  sont négatifs ou en millions, les mêmes jours sur tous les compteurs
  (pannes de la collecte) : kwh est alors vide, kwh_brut garde la valeur lue.

  cos φ : moyenne des relevés valides du jour (entre 0 et 1) ; part des
  relevés sous 0,8 (seuil des pénalités) ; nombre de relevés invalides.
  Puissance maximale du jour : pic de puissance active.
#}

with releves as (

    select *, cast(releve_le as date) as jour
    from {{ ref('stg_electricite__releves') }}

),

consommation as (

    -- La valeur lue le jour J+1 est celle du jour J
    select distinct on (compteur, jour)
        compteur,
        jour - 1                                as jour,
        consommation_veille                     as kwh,
        consommation_veille_pleine              as kwh_heures_pleines,
        consommation_veille_pointe              as kwh_heures_pointe,
        consommation_veille_creuse              as kwh_heures_creuses
    from releves
    where consommation_veille is not null
    order by compteur, jour, releve_le desc

),

mesures as (

    select
        compteur,
        max(niveau)                                             as niveau,
        jour,
        count(*)                                                as releves,
        avg(cos_phi)                                            as cos_phi_moyen,
        avg(case when cos_phi < 0.8 then 1.0 when cos_phi is not null then 0.0 end)
                                                                as part_cos_phi_sous_0_8,
        count(*) filter (where not cos_phi_valide)              as releves_cos_phi_invalides,
        max(puissance_active)                                   as puissance_max
    from releves
    group by compteur, jour

),

controle as (

    select
        m.*,
        c.kwh                                                   as kwh_brut,
        c.kwh_heures_pleines,
        c.kwh_heures_pointe,
        c.kwh_heures_creuses,
        c.kwh is not null
            and c.kwh >= 0
            and c.kwh <= m.puissance_max * 24 * 1.1
            and c.kwh <= 100000                                 as kwh_valide
    from mesures as m
    left join consommation as c
        on c.compteur = m.compteur
       and c.jour = m.jour

)

select
    cast(controle.compteur as text)                             as compteur,
    cast(niveau as text)                                        as niveau,
    cast(controle.jour as date)                                 as jour,
    cast(case when kwh_valide then kwh_brut end as numeric(18, 3))
                                                                as kwh,
    cast(coalesce(kwh_valide, false) as boolean)                as kwh_valide,
    cast(kwh_brut as numeric(24, 3))                            as kwh_brut,
    cast(case when kwh_valide then kwh_heures_pleines end as numeric(18, 3))
                                                                as kwh_heures_pleines,
    cast(case when kwh_valide then kwh_heures_pointe end as numeric(18, 3))
                                                                as kwh_heures_pointe,
    cast(case when kwh_valide then kwh_heures_creuses end as numeric(18, 3))
                                                                as kwh_heures_creuses,
    cast(cos_phi_moyen as numeric(6, 4))                        as cos_phi_moyen,
    cast(part_cos_phi_sous_0_8 as numeric(6, 4))                as part_cos_phi_sous_0_8,
    cast(releves_cos_phi_invalides as integer)                  as releves_cos_phi_invalides,
    cast(puissance_max as numeric(18, 3))                       as puissance_max,
    cast(releves as integer)                                    as releves,
    -- Énergie réactive : les relevés valides ne couvrent que quelques heures
    -- par jour (collecte par à-coups) ; le rapport réactif / actif mesuré sur
    -- ces relevés (int_electricite__reactif_jour) est appliqué aux kWh du jour
    cast(r.energie_reactive_kvarh / nullif(r.energie_active_kwh, 0) as numeric(8, 4))
                                                                as tan_phi_moyen,
    cast(case when kwh_valide
              then kwh_brut * r.energie_reactive_kvarh / nullif(r.energie_active_kwh, 0) end as numeric(18, 3))
                                                                as energie_reactive_kvarh,
    cast(case when kwh_valide
              then kwh_brut * r.energie_reactive_excedentaire_kvarh / nullif(r.energie_active_kwh, 0) end as numeric(18, 3))
                                                                as energie_reactive_excedentaire_kvarh,
    cast(r.heures_mesurees as numeric(10, 4))                   as heures_cos_phi_mesurees
from controle
left join {{ ref('int_electricite__reactif_jour') }} as r
    on r.compteur = controle.compteur
   and r.jour = controle.jour
