{#
  Grain : une ligne = une brique mesurée par le service qualité (poids et
  dimensions). Source : application qualité (prélèvements en sortie de
  mouleuse et de séchoir).
#}

select
    cast(m.id_mesure as bigint)                     as id_mesure,
    cast(p.id_prelevement as bigint)                as id_prelevement,
    cast(r.jour as date)                            as jour,
    cast(r.poste as text)                           as poste,
    cast(p.zone as text)                            as zone,
    cast(p.type_brique as text)                     as type_brique,
    cast(p.reference_moule as text)                 as reference_moule,
    cast(m.poids_kg as numeric(12, 3))              as poids_kg,
    cast(m.hauteur_cm as numeric(12, 2))            as hauteur_cm,
    cast(m.largeur_cm as numeric(12, 2))            as largeur_cm,
    cast(m.longueur_cm as numeric(12, 2))           as longueur_cm
from {{ ref('stg_qualite__mesures') }} as m
inner join {{ ref('stg_qualite__prelevements') }} as p
    on p.id_prelevement = m.id_prelevement
left join {{ ref('int_qualite__rapports_dates') }} as r
    on r.id_rapport = p.id_rapport
