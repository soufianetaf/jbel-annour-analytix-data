{#
  Grain : une ligne = un compteur électrique × un jour.

  Énergie réactive, base des pénalités de cos φ (docs/indicateurs/energie.md).
  La puissance réactive relevée (Q_Tot) est inutilisable (valeurs jusqu'à
  10 millions, moyenne négative) : elle est recalculée à partir de la
  puissance active et du cos φ valide :

      Q = P × tan φ,   tan φ = √(1 - cos²φ) / cos φ
      réactive excédentaire = P × (tan φ - 0,75) quand tan φ > 0,75 (cos φ < 0,8)

  Chaque relevé vaut le temps jusqu'au relevé suivant (5 minutes en
  général), au plus 15 minutes : un trou de collecte n'est pas compté.
  Relevés retenus : cos φ entre 0,05 et 1, puissance active entre 0 et 5 000 kW.
#}

with releves as (

    select
        compteur,
        releve_le,
        cast(releve_le as date)                                         as jour,
        puissance_active,
        cos_phi,
        -- least() ignore les vides en PostgreSQL : le dernier relevé (sans
        -- suivant) doit rester vide, pas valoir 15 minutes
        extract(epoch from (lead(releve_le) over (partition by compteur order by releve_le) - releve_le)) / 3600
                                                                        as heures_brutes
    from {{ ref('stg_electricite__releves') }}

),

valides as (

    select
        *,
        least(heures_brutes, 0.25)                                      as heures,
        sqrt(1 - cos_phi * cos_phi) / cos_phi                           as tan_phi
    from releves
    where cos_phi between 0.05 and 1
      and puissance_active between 0 and 5000
      and heures_brutes > 0

)

select
    compteur,
    jour,
    cast(sum(puissance_active * heures) as numeric(18, 3))              as energie_active_kwh,
    cast(sum(puissance_active * tan_phi * heures) as numeric(18, 3))    as energie_reactive_kvarh,
    cast(sum(puissance_active * greatest(tan_phi - 0.75, 0) * heures) as numeric(18, 3))
                                                                        as energie_reactive_excedentaire_kvarh,
    cast(sum(heures) as numeric(10, 4))                                 as heures_mesurees
from valides
group by compteur, jour
