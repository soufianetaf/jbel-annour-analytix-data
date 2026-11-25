{#
  Le signe d'un document doit correspondre à son type :
  un avoir (AVF, AVR) a le signe -1, une facture ou un pro forma le signe 1.

  Pourquoi : le chiffre d'affaires sera calculé avec « signe ». Un avoir
  avec le signe 1 serait ajouté au CA au lieu d'en être retiré.

  Le test échoue s'il renvoie au moins une ligne.
#}

select numero_facture, type_facture, signe
from {{ ref('stg_x3__factures') }}
where (type_facture in ('AVF', 'AVR') and signe <> -1)
   or (type_facture in ('FAC', 'PRF') and signe <> 1)
