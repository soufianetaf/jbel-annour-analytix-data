{#
  Grain : une ligne = une pièce de rechange utilisée sur une ligne d'intervention.

  Les codes sont ceux de Sage X3 quand ils existent : la clé article est la
  même que dans le stock, les achats et le magasin. Un code inconnu de X3
  (« 3260 », saisie libre) pointe vers l'article « Inconnu » et garde son
  code dans code_article.
#}

select
    cast(p.id_ligne as bigint)                                          as id_ligne,
    cast(p.position as integer)                                         as position,
    cast(i.jour as date)                                                as jour,
    cast(i.zone as text)                                                as zone,
    cast(i.equipement as text)                                          as equipement,
    cast(coalesce(a.cle_article, {{ cle_inconnue() }}) as text)         as cle_article,
    cast(p.code_article as text)                                        as code_article,
    cast(a.cle_article is not null as boolean)                          as article_x3,
    cast(p.quantite as numeric(12, 2))                                  as quantite
from {{ ref('stg_maintenance__pieces_intervention') }} as p
inner join {{ ref('fct_interventions_maintenance') }} as i
    on i.id_ligne = p.id_ligne
left join {{ ref('dim_article') }} as a
    on a.code_article = p.code_article
