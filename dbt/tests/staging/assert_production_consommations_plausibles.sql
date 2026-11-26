{#
  AVERTISSEMENT (ne bloque pas) : rapports de consommations saisis avec une
  valeur impossible (quantité négative, production hors de 1 à 3 000 t par
  jour). fct_combustibles_jour les écarte ; ils sont à corriger dans
  l'application de production.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Production', 'correction': "Corriger le rapport de consommations dans l'application de production."},
) }}

select id_rapport, jour, production_tonnes, fuel_four, coke_micronise, propane
from {{ ref('stg_production__consommations') }}
where production_tonnes not between 1 and 3000
   or fuel_four < 0
   or coke_micronise < 0
   or propane < 0
   or electricite < 0
