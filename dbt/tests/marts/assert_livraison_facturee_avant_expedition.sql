{#
  AVERTISSEMENT (ne bloque pas) : livraisons dont la facture est datée AVANT
  l'expédition (erreur de date dans Sage X3). fct_livraisons leur laisse un
  délai vide ; ce test les liste pour l'ADV.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'ADV', 'correction': "Corriger la date d'expédition ou la date de la facture dans Sage X3."},
) }}

select numero_livraison, numero_facture, date_expedition, date_facture
from {{ ref('fct_livraisons') }}
where date_facture < date_expedition
