{#
  Un exercice clôturé (qui a une pièce de clôture) a ses comptes 6 et 7
  soldés à zéro, clôture comprise, au centime.

  Pourquoi : la pièce de clôture transfère le résultat de l'exercice au
  bilan. Si la somme ne revient pas à zéro, soit une pièce de clôture
  manque, soit une écriture a été copiée deux fois ou perdue. C'est aussi
  ce qui garantit que « résultat hors clôture » = résultat de l'exercice.

  Le test échoue s'il renvoie au moins une ligne.
#}

with exercices_clotures as (

    select distinct numero_exercice
    from {{ ref('fct_ecritures') }}
    where est_cloture

)

select e.numero_exercice, sum(e.solde) as solde_classes_6_7
from {{ ref('fct_ecritures') }} as e
inner join exercices_clotures using (numero_exercice)
where e.classe in ('6', '7')
group by e.numero_exercice
having abs(sum(e.solde)) >= 0.01
