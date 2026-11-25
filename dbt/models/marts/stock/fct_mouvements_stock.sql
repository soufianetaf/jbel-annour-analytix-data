{#
  Grain : une ligne = un mouvement de stock d'un article sur un site.

  Quantité et valeur sont signées dans Sage X3 : positives à l'entrée,
  négatives à la sortie (vérifié par assert_x3_stock_quantite_valeur_meme_signe).
  Les types de mouvement (code_type_mouvement) restent des codes X3, à
  libeller avec le magasin (docs/indicateurs/stock_valorise.md).
#}

with mouvements as (

    select * from {{ ref('stg_x3__mouvements_stock') }}

)

select
    -- Identifiant (clé naturelle de STOJOU)
    cast(site as text)                                          as site,
    cast(code_mise_a_jour as integer)                           as code_mise_a_jour,
    cast(article as text)                                       as code_article,
    cast(date_mouvement as date)                                as date_mouvement,
    cast(sequence as bigint)                                    as sequence,
    cast(indice as bigint)                                      as indice,

    cast({{ cle_x3('article') }} as text)                       as cle_article,
    cast(code_type_mouvement as integer)                        as code_type_mouvement,
    cast(case when quantite > 0 then 'entrée'
              when quantite < 0 then 'sortie'
              else 'sans quantité' end as text)                 as sens,
    cast(depot as text)                                         as depot,
    cast(tiers as text)                                         as code_tiers,
    cast(code_type_document as integer)                         as code_type_document,
    cast(numero_document as text)                               as numero_document,
    cast(ligne_document as integer)                             as ligne_document,
    cast(section_1 as text)                                     as section_1,
    cast(section_2 as text)                                     as section_2,

    cast(quantite as numeric(28, 10))                           as quantite,
    cast(unite_stock as text)                                   as unite_stock,
    cast(valeur as numeric(28, 10))                             as valeur,
    cast(date_comptable as date)                                as date_comptable,
    cast(_charge_le as timestamp with time zone)                as charge_le
from mouvements
