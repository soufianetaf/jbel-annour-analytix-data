{#
  Pour chaque document, le total HT de ses lignes est égal au HT de l'entête
  (à moins d'un centime près).

  Pourquoi : les analyses par article ou par représentant partent des
  lignes, celles par client ou par échéance partent des entêtes. Les deux
  doivent donner le même chiffre d'affaires.

  Le test échoue s'il renvoie au moins une ligne : chaque ligne renvoyée
  est un document dont les lignes ne retrouvent pas l'entête.
#}

with total_lignes as (

    select numero_facture, sum(montant_ht) as montant_ht_lignes
    from {{ ref('stg_x3__lignes_facture') }}
    group by numero_facture

)

select
    f.numero_facture,
    f.montant_ht                         as montant_ht_entete,
    coalesce(l.montant_ht_lignes, 0)     as montant_ht_lignes
from {{ ref('stg_x3__factures') }} as f
left join total_lignes as l using (numero_facture)
where abs(f.montant_ht - coalesce(l.montant_ht_lignes, 0)) >= 0.01
