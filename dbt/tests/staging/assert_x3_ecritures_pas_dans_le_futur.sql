{#
  AVERTISSEMENT (ne bloque pas) : écritures datées après le jour du
  chargement (cahier des charges, 5.2 « dates dans le futur »).

  Au 25/11/2026 : 16 lignes datées de janvier 2027. Erreur de saisie
  probable, à faire vérifier par la comptabilité.
#}

{{ config(severity='warn') }}

select type_piece, numero_piece, date_comptable, count(*) as lignes
from {{ ref('stg_x3__lignes_ecriture') }}
where registre = 1
  and date_comptable > {{ date_du_jour() }}
group by 1, 2, 3
