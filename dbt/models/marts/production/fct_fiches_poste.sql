{#
  Grain : une ligne = une fiche de fin de poste, retenue ou non.

  Sert à la page « Qualité des données » : combien de fiches supprimées,
  incomplètes ou en doublon, par mois et par équipe. Les totaux de
  production, eux, viennent de fct_production_poste (fiches retenues).
#}

select
    cast(id_fiche as bigint)                    as id_fiche,
    cast(date_poste as date)                    as date_poste,
    cast(shift as text)                         as shift,
    cast(equipe as text)                        as equipe,
    cast(est_retenue as boolean)                as est_retenue,
    cast(motif_exclusion as text)               as motif_exclusion,
    cast(saisies_du_poste as integer)           as saisies_du_poste,
    cast(cree_le as timestamp)                  as cree_le
from {{ ref('int_production__fiches_dedoublonnees') }}
