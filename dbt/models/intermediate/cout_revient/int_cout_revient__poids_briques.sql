{#
  Grain : une ligne = un article brique vendu, avec son poids pour passer
  des unités vendues aux tonnes.

  Poids retenu :
  1. le poids de l'article dans Sage X3, s'il est plausible (1 à 20 kg) ;
  2. sinon le poids médian pesé à la sortie du four pour ce type de brique
     (application de production, fct_pesees_briques, briques de 25 cm).
  Le poids de Sage X3 est parfois faux (BLCH12 à 0,01 kg, B12 PBP à 2,5 kg
  contre 3,9 kg pesés) : le test assert_cout_poids_article_coherent les liste.
#}

with articles as (

    select
        cle_article,
        code_article,
        designation,
        {{ type_brique_vente('designation') }}                      as type_brique,
        case when lower(unite_poids) = 'kg' then poids_unitaire end as poids_x3_kg
    from {{ ref('dim_article') }}

),

pesees as (

    -- B8-25 → B8 ; seules les briques de 25 cm sont pesées régulièrement
    select
        split_part(type_brique, '-', 1)                             as type_brique,
        percentile_cont(0.5) within group (order by poids_moyen_kg) as poids_pese_kg
    from {{ ref('fct_pesees_briques') }}
    where zone = 'four'
      and type_brique like '%-25'
    group by 1

)

select
    a.cle_article,
    a.code_article,
    a.designation,
    a.type_brique,
    a.poids_x3_kg,
    cast(p.poids_pese_kg as numeric(12, 3))                         as poids_pese_kg,
    case
        when a.poids_x3_kg between 1 and 20 then a.poids_x3_kg
        else p.poids_pese_kg
    end                                                             as poids_kg,
    case
        when a.poids_x3_kg between 1 and 20 then 'Sage X3'
        when p.poids_pese_kg is not null then 'pesées du four'
    end                                                             as origine_poids
from articles as a
left join pesees as p
    on p.type_brique = a.type_brique
where a.type_brique is not null
