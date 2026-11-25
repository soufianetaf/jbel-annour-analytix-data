{#
  Grain : une ligne = un compte de charge ou de produit × un mois.

  CPC mensuel, construit à partir de fct_ecritures (jamais des sources),
  SANS les écritures de clôture (elles remettent les comptes 6 et 7 à zéro) :
      montant_resultat = - solde
      positif pour un produit, négatif pour une charge
      résultat du mois = somme de montant_resultat
#}

with ecritures as (

    select * from {{ ref('fct_ecritures') }}
    where classe in ('6', '7')
      and not est_cloture

)

select
    cast(date_trunc('month', e.date_comptable) as date)     as mois,
    cast(extract(year from e.date_comptable) as integer)    as annee,
    cast(e.numero_exercice as integer)                      as numero_exercice,
    cast(e.societe as text)                                 as societe,
    cast(e.cle_compte as text)                              as cle_compte,
    cast(e.compte as text)                                  as compte,
    cast(c.intitule as text)                                as intitule,
    cast(c.nature as text)                                  as nature,
    cast(c.rubrique_cpc as text)                            as rubrique_cpc,
    cast(sum(e.debit) as numeric(28, 10))                   as debit,
    cast(sum(e.credit) as numeric(28, 10))                  as credit,
    cast(-sum(e.solde) as numeric(28, 10))                  as montant_resultat,
    cast(count(*) as integer)                               as lignes

from ecritures as e
left join {{ ref('dim_compte') }} as c
    on c.cle_compte = e.cle_compte
group by 1, 2, 3, 4, 5, 6, 7, 8, 9
