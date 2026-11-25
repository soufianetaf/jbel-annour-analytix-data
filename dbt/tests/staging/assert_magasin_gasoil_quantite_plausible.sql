{#
  AVERTISSEMENT (ne bloque pas) : bons de gasoil d'une quantité négative
  ou supérieure à 2 000 litres.

  Pourquoi : la quantité saisie normale est positive (médiane 75 L, 99 %
  des bons sous 600 L au 25/11/2026). 7 bons sont négatifs, dont un à
  -449 595 L, et 2 dépassent 38 000 L : ce sont des erreurs de saisie
  (probablement un relevé de compteur saisi à la place des litres). Elles
  fausseraient la consommation : ce test les liste pour le magasin.
#}

{{ config(severity='warn') }}

select id_bon, numero_bon, quantite_saisie, compteur_km, cree_le
from {{ ref('stg_magasin__gasoil') }}
where quantite_saisie < 0
   or quantite_saisie > 2000
