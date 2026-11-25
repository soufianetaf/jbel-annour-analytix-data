{#
  Le CA net de fct_ventes (calculé depuis les LIGNES) est égal, au
  centime près et pour chaque année, au CA net calculé depuis les
  ENTÊTES de staging, avec la même définition.

  Pourquoi : deux chemins indépendants vers le même chiffre. Une
  jointure qui perd ou duplique des lignes dans fct_ventes ferait
  diverger les deux.

  Le test échoue s'il renvoie au moins une ligne (une année en écart).
#}

with depuis_lignes as (

    select extract(year from date_comptable) as annee, sum(montant_ht_signe) as ca
    from {{ ref('fct_ventes') }}
    group by 1

),

depuis_entetes as (

    select extract(year from date_comptable) as annee, sum(montant_ht * signe) as ca
    from {{ ref('stg_x3__factures') }}
    where type_facture <> 'PRF'
    group by 1

)

select
    coalesce(l.annee, e.annee) as annee,
    l.ca                       as ca_depuis_lignes,
    e.ca                       as ca_depuis_entetes
from depuis_lignes as l
full outer join depuis_entetes as e using (annee)
where abs(coalesce(l.ca, 0) - coalesce(e.ca, 0)) >= 0.01
