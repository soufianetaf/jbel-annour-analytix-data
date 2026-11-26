{#
  AVERTISSEMENT (ne bloque pas) : articles briques dont le poids dans Sage X3
  est absent, invraisemblable (hors 1 à 20 kg) ou à plus de 30 % du poids
  pesé à la sortie du four pour le même type. Ces poids sont à corriger dans
  Sage X3 : ils servent à passer des unités vendues aux tonnes.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Gestion des articles', 'correction': "Corriger le poids de l'article brique dans Sage X3 (fiche article, poids unitaire en kg)."},
) }}

select code_article, designation, type_brique, poids_x3_kg, poids_pese_kg, origine_poids
from {{ ref('int_cout_revient__poids_briques') }}
where poids_x3_kg is null
   or poids_x3_kg not between 1 and 20
   or (poids_pese_kg is not null and abs(poids_x3_kg / poids_pese_kg - 1) > 0.3)
