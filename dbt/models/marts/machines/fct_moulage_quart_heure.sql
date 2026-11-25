{#
  Grain : une ligne = un quart d'heure de mesures du moulage.

  Les mesures (une toutes les 11 secondes environ) sont agrégées par
  quart d'heure : moyenne, minimum, maximum et nombre de mesures. Un quart
  d'heure sans aucune mesure n'a pas de ligne : voir agg_moulage_coupures.
#}

select
    cast(date_bin('15 minutes', mesure_le, timestamp '2000-01-01') as timestamp) as quart_heure,
    cast(count(*) as integer)                                   as mesures,
    cast(avg(vitesse_coupe) as numeric(12, 3))                  as vitesse_coupe_moy,
    cast(avg(vitesse_doseur) as numeric(12, 3))                 as vitesse_doseur_moy,
    cast(avg(pression_monobloc) as numeric(12, 3))              as pression_monobloc_moy,
    cast(max(pression_monobloc) as numeric(12, 3))              as pression_monobloc_max,
    cast(avg(courant_extrudeuse) as numeric(12, 3))             as courant_extrudeuse_moy,
    cast(max(courant_extrudeuse) as numeric(12, 3))             as courant_extrudeuse_max,
    cast(count(*) filter (where courant_extrudeuse is null) as integer)
                                                                as mesures_courant_vides
from {{ ref('stg_moulage__mesures') }}
group by 1
