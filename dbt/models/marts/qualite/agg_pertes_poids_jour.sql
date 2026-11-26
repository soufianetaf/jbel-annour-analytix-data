{#
  Grain : une ligne = un jour × un type de brique.

  Une brique perd de l'eau au séchoir puis à la cuisson. En comparant le
  poids moyen du jour aux trois étapes (pesées plausibles seulement) :

      perte au séchage  = 1 - poids après séchoir / poids en sortie de mouleuse
      perte à la cuisson = 1 - poids après four   / poids après séchoir

  Ce ne sont pas les mêmes briques aux trois étapes (elles ne sont pas
  suivies une à une) : c'est une moyenne du jour, vide si une étape manque.
#}

with poids as (

    select
        jour,
        type_brique,
        sum(poids_moyen_kg * (briques_pesees - pesees_aberrantes)) filter (where zone = 'mouleuse')
            / nullif(sum(briques_pesees - pesees_aberrantes) filter (where zone = 'mouleuse' and poids_moyen_kg is not null), 0)
                                                                        as poids_mouleuse,
        sum(poids_moyen_kg * (briques_pesees - pesees_aberrantes)) filter (where zone = 'séchoir')
            / nullif(sum(briques_pesees - pesees_aberrantes) filter (where zone = 'séchoir' and poids_moyen_kg is not null), 0)
                                                                        as poids_sechoir,
        sum(poids_moyen_kg * (briques_pesees - pesees_aberrantes)) filter (where zone = 'four')
            / nullif(sum(briques_pesees - pesees_aberrantes) filter (where zone = 'four' and poids_moyen_kg is not null), 0)
                                                                        as poids_four,
        sum(briques_pesees)                                             as briques_pesees
    from {{ ref('fct_pesees_briques') }}
    group by jour, type_brique

)

select
    cast(jour as date)                                                  as jour,
    cast(type_brique as text)                                           as type_brique,
    cast(poids_mouleuse as numeric(12, 3))                              as poids_mouleuse_kg,
    cast(poids_sechoir as numeric(12, 3))                               as poids_sechoir_kg,
    cast(poids_four as numeric(12, 3))                                  as poids_four_kg,
    cast(1 - poids_sechoir / nullif(poids_mouleuse, 0) as numeric(8, 4)) as perte_sechage,
    cast(1 - poids_four / nullif(poids_sechoir, 0) as numeric(8, 4))    as perte_cuisson,
    cast(briques_pesees as integer)                                     as briques_pesees
from poids
