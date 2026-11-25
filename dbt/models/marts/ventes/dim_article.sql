{#
  Grain : une ligne = un article de Sage X3, plus une ligne « Inconnu ».

  Dimension partagée : ventes, achats, stock, maintenance (pièces).
  Le même article a la même clé partout : c'est ce qui permettra de
  croiser les ventes et les achats, puis de calculer le coût par tonne.
#}

with articles as (

    select * from {{ ref('stg_x3__articles') }}

)

select
    cast({{ cle_x3('code_article') }} as text)      as cle_article,
    cast('x3' as text)                              as source,
    cast(code_article as text)                      as code_article,
    cast(designation as text)                       as designation,
    cast(designation_2 as text)                     as designation_2,
    cast(categorie_article as text)                 as categorie_article,
    cast(famille_statistique_1 as text)             as famille_statistique_1,
    cast(famille_statistique_2 as text)             as famille_statistique_2,
    cast(famille_statistique_3 as text)             as famille_statistique_3,
    cast(code_statut as integer)                    as code_statut,
    cast(unite_stock as text)                       as unite_stock,
    cast(unite_vente as text)                       as unite_vente,
    cast(coefficient_vente_stock as numeric(28, 10)) as coefficient_vente_stock,
    cast(unite_poids as text)                       as unite_poids,
    cast(poids_unitaire as numeric(28, 10))         as poids_unitaire
from articles

union all

-- Ligne « Inconnu »
select
    cast({{ cle_inconnue() }} as text),
    cast('x3' as text),
    cast(null as text),
    cast('Inconnu' as text),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as integer),
    cast(null as text),
    cast(null as text),
    cast(null as numeric(28, 10)),
    cast(null as text),
    cast(null as numeric(28, 10))
