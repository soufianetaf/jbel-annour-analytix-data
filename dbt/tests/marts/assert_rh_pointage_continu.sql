{#
  AVERTISSEMENT (ne bloque pas) : jours ouvrés où moins de la moitié des
  personnes habituelles ont pointé.

  Pourquoi : depuis le 30/10/2026, une cinquantaine de personnes pointent par
  jour contre près de 300 avant (base pointage du serveur de l'usine, table
  att_punches). Le taux de présence affiché mesure alors la panne du pointage,
  pas la présence. Référence : médiane des jours ouvrés des 28 jours précédents.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'RH', 'correction': "Vérifier que les pointeuses envoient leurs pointages à la base pointage (terminaux, synchronisation)."},
) }}

with jours as (

    select jour, personnes_presentes
    from {{ ref('agg_presence_jour') }}
    where jour_semaine between 1 and 5

),

reference as (

    select
        j.jour,
        j.personnes_presentes,
        (
            select percentile_cont(0.5) within group (order by p.personnes_presentes)
            from jours as p
            where p.jour >= j.jour - 28 and p.jour < j.jour
        ) as mediane_28_jours
    from jours as j

)

select jour, personnes_presentes, mediane_28_jours
from reference
where mediane_28_jours >= 50
  and personnes_presentes < 0.5 * mediane_28_jours
