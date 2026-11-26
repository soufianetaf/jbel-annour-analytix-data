{#
  AVERTISSEMENT (ne bloque pas) : passages de wagons sortis avant d'être
  entrés, jamais sortis, ou restés plus de 24 heures (cahier des charges, 5.2).
  fct_wagons laisse leur cycle vide ; ce test les liste.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Automatisme', 'correction': "Vérifier l'horloge et les capteurs d'entrée et de sortie des wagons."},
) }}

select machine, id_passage, entree_le, sortie_le
from {{ ref('fct_wagons') }}
where cycle_minutes is null
