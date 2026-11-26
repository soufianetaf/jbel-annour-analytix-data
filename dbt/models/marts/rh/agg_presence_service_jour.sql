{#
  Grain : une ligne = un département × un jour. Définitions : docs/indicateurs/rh.md

      taux_presence          = personnes qui ont pointé / effectif du département dans la pointeuse
      heures_moyennes_site   = temps sur site / personnes avec une entrée et une sortie
      part_pointage_unique   = personnes avec un seul pointage / personnes qui ont pointé

  Le taux n'est pas calculé pour le groupe fusionné « autres » : ses membres
  ne sont pas les mêmes d'un jour à l'autre ni dans l'effectif.
#}

select
    cast(j.service as text)                                             as service,
    cast(j.jour as date)                                                as jour,
    cast(j.personnes as integer)                                        as personnes_presentes,
    cast(j.pointages as integer)                                        as pointages,
    cast(e.effectif as integer)                                         as effectif_pointeuse,
    cast(case when j.service <> {{ groupe_rh_masque() }}
              then j.personnes::numeric / nullif(e.effectif, 0) end as numeric(6, 4))
                                                                        as taux_presence,
    cast(j.minutes_sur_site / 60.0 / nullif(j.personnes_entree_sortie, 0) as numeric(6, 2))
                                                                        as heures_moyennes_site,
    cast(1 - j.personnes_entree_sortie::numeric / nullif(j.personnes, 0) as numeric(6, 4))
                                                                        as part_pointage_unique
from {{ ref('stg_rh__pointage_service_jour') }} as j
left join {{ ref('stg_rh__effectifs_pointeuse') }} as e
    on e.service = j.service
