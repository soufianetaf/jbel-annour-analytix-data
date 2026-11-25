{#
  Grain : une ligne = une ligne d'écriture de la comptabilité GÉNÉRALE,
  simulations exclues.

  Règles (docs/indicateurs/finance_compte_de_resultat.md) :
  1. Registre 1 (comptabilité générale) : le registre analytique reprend
     les mêmes montants, les additionner compterait deux fois.
  2. Catégories 1 et 2 ; la catégorie 3 (simulation) est exclue. C'est
     exactement ce que retient la BALANCE de Sage X3 (vérifié le 25/11/2026 :
     une pièce de clôture IMS12 est en catégorie 2, une simulation SMDIV en 3).
  3. solde = montant × sens (débit positif, crédit négatif), en MAD.
  4. Les pièces de clôture (var « type_piece_cloture », CLOS1) sont gardées
     mais marquées : elles soldent les comptes 6 et 7 au 31/12 et doivent
     être exclues d'un compte de résultat. Ce n'est PAS le journal J42, qui
     contient aussi des opérations diverses toute l'année.
#}

with lignes as (

    select * from {{ ref('stg_x3__lignes_ecriture') }}
    where registre = 1  -- règle 1

),

pieces as (

    select * from {{ ref('stg_x3__ecritures') }}
    where code_categorie in (1, 2)  -- règle 2

)

select
    -- Identifiant
    cast(l.type_piece as text)                                      as type_piece,
    cast(l.numero_piece as text)                                    as numero_piece,
    cast(l.ligne as integer)                                        as ligne,

    -- Pièce
    cast(p.journal as text)                                         as journal,
    cast(p.code_statut = 2 as boolean)                              as est_definitive,
    cast(l.type_piece = '{{ var("type_piece_cloture") }}' as boolean) as est_cloture,  -- règle 4
    cast(l.date_comptable as date)                                  as date_comptable,
    cast(l.numero_exercice as integer)                              as numero_exercice,
    cast(l.periode as integer)                                      as periode,
    cast(l.societe as text)                                         as societe,
    cast(l.site as text)                                            as site,

    -- Compte et tiers
    cast({{ cle_x3("l.plan_comptable || '|' || l.compte") }} as text) as cle_compte,
    cast(l.compte as text)                                          as compte,
    cast(left(l.compte, 1) as text)                                 as classe,
    cast(l.tiers as text)                                           as code_tiers,

    -- Montants en MAD (règle 3)
    cast(case when l.sens = 1 then l.montant else 0 end as numeric(28, 10))  as debit,
    cast(case when l.sens = -1 then l.montant else 0 end as numeric(28, 10)) as credit,
    cast(l.montant * l.sens as numeric(28, 10))                     as solde,
    cast(l.devise as text)                                          as devise,

    cast(l._charge_le as timestamp with time zone)                  as charge_le

from lignes as l
inner join pieces as p
    on p.type_piece = l.type_piece
   and p.numero_piece = l.numero_piece
