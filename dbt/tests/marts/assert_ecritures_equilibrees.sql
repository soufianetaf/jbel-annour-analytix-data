{#
  Chaque pièce comptable est équilibrée : total des débits = total des
  crédits, au centime.

  Pourquoi : c'est la règle de base de la comptabilité en partie double.
  Une pièce déséquilibrée dans l'entrepôt signalerait une ligne perdue ou
  copiée deux fois (cahier des charges 5.1 : 0 écriture déséquilibrée
  dans Sage X3, l'entrepôt doit garder cette propriété).

  Le test échoue s'il renvoie au moins une ligne.
#}

select type_piece, numero_piece, sum(debit) as debit, sum(credit) as credit
from {{ ref('fct_ecritures') }}
group by type_piece, numero_piece
having abs(sum(debit) - sum(credit)) >= 0.01
