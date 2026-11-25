{#
  Grain : une ligne = un compte de trésorerie × un jour où il a bougé.

  Construit à partir de fct_ecritures (jamais des sources).
  Définitions : docs/indicateurs/finance_tresorerie.md

      solde_fin_jour = somme des soldes (débit - crédit) de l'EXERCICE,
                       à-nouveaux compris, jusqu'au jour inclus

  Le cumul repart à chaque exercice : au 1er janvier, les à-nouveaux
  (pièces RANX1) reportent déjà le solde de l'année précédente.
  Pour un jour sans mouvement, le solde est celui du dernier jour connu.
#}

with mouvements as (

    select
        date_comptable                          as date_jour,
        numero_exercice,
        cle_compte,
        compte,
        sum(solde)                              as mouvement,
        count(*)                                as lignes
    from {{ ref('fct_ecritures') }}
    where left(compte, 2) in ('51', '55')
    group by 1, 2, 3, 4

)

select
    cast(m.date_jour as date)                                   as date_jour,
    cast(m.numero_exercice as integer)                          as numero_exercice,
    cast(m.cle_compte as text)                                  as cle_compte,
    cast(m.compte as text)                                      as compte,
    cast(c.intitule as text)                                    as intitule,
    cast({{ famille_tresorerie('m.compte') }} as text)          as famille,
    cast(m.mouvement as numeric(28, 10))                        as mouvement,
    cast(sum(m.mouvement) over (
        partition by m.numero_exercice, m.cle_compte
        order by m.date_jour
        rows between unbounded preceding and current row
    ) as numeric(28, 10))                                       as solde_fin_jour,
    cast(m.lignes as integer)                                   as lignes
from mouvements as m
left join {{ ref('dim_compte') }} as c
    on c.cle_compte = m.cle_compte
