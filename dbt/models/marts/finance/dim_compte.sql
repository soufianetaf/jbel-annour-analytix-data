{#
  Grain : une ligne = un compte du plan comptable, plus une ligne « Inconnu ».

  Ajoute au plan comptable de X3 la classe, la nature (charge, produit,
  bilan) et la rubrique du CPC (docs/indicateurs/finance_compte_de_resultat.md),
  d'après les premiers chiffres du compte (plan comptable marocain).
#}

with comptes as (

    select * from {{ ref('stg_x3__comptes') }}

)

select
    cast({{ cle_x3("plan_comptable || '|' || compte") }} as text)  as cle_compte,
    cast(plan_comptable as text)                                    as plan_comptable,
    cast(compte as text)                                            as compte,
    cast(intitule as text)                                          as intitule,
    cast(left(compte, 1) as text)                                   as classe,
    cast({{ nature_compte('compte') }} as text)                     as nature,
    cast({{ rubrique_cpc('compte') }} as text)                      as rubrique_cpc,
    cast(est_actif as boolean)                                      as est_actif
from comptes

union all

select
    cast({{ cle_inconnue() }} as text),
    cast(null as text),
    cast(null as text),
    cast('Inconnu' as text),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as boolean)
