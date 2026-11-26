{#
  AVERTISSEMENT (ne bloque pas) : quantités de briques non acceptables
  invraisemblables pour un chariot (plus de 5 000 : 8 668 saisi 14 fois,
  356 226, 65 626). fct_controles_qualite les garde telles quelles ; les
  indicateurs comptent les statuts, pas les quantités.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Qualité', 'correction': "Corriger la quantité de briques non acceptables dans l'application qualité."},
) }}

select id_controle, jour, defaut, quantite_non_acceptable
from {{ ref('fct_controles_qualite') }}
where quantite_non_acceptable > 5000
