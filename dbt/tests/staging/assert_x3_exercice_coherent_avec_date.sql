{#
  AVERTISSEMENT (ne bloque pas) : lignes d'écriture dont l'exercice saisi
  dans Sage X3 ne correspond pas à leur date comptable.

  Pourquoi : une pièce datée du 04/04/2025 était saisie sur l'exercice 2024.
  L'entrepôt se fie à la DATE (comme la BALANCE de Sage X3) ; ce test
  liste les pièces à faire vérifier par la comptabilité.
#}

{{ config(severity='warn') }}

select l.type_piece, l.numero_piece, l.date_comptable,
       l.numero_exercice as exercice_saisi, x.numero_exercice as exercice_de_la_date
from {{ ref('stg_x3__lignes_ecriture') }} as l
inner join {{ ref('stg_x3__exercices') }} as x
    on x.registre = 1
   and x.societe = l.societe
   and l.date_comptable between x.date_debut and x.date_fin
where l.registre = 1
  and l.numero_exercice <> x.numero_exercice
group by 1, 2, 3, 4, 5
