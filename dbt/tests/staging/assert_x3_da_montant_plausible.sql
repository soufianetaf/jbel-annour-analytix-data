{#
  AVERTISSEMENT (ne bloque pas) : lignes de demande d'achat d'un montant
  supérieur à 100 M MAD.

  Pourquoi : au 25/11/2026, 85 lignes (article A13457, prix fictif de
  500 000 MAD) totalisent 6 171 milliards MAD. Les montants des DA ne
  sont donc pas utilisables en l'état : ce test liste les lignes à
  corriger dans Sage X3.
#}

{{ config(severity='warn') }}

select numero_demande, ligne, article, quantite, prix_net, montant_ht
from {{ ref('stg_x3__lignes_demande_achat') }}
where montant_ht > 100000000
