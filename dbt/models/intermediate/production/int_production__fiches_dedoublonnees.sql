{#
  Grain : une ligne = une fiche de fin de poste, avec la décision de la
  retenir ou non.

  Règle de dédoublonnage (docs/indicateurs/production_postes.md, à valider
  avec la production) :
  1. une fiche supprimée dans l'application n'est pas retenue ;
  2. une fiche sans date, shift ou équipe n'est pas retenue (29 fiches
     vides au 25/11/2026) ;
  3. pour un même poste (date, shift, équipe), une seule fiche est retenue :
     la plus récemment modifiée (à égalité, l'identifiant le plus grand).
     Exemple : le poste du 29/12/2025, 07h-15h, équipe B, saisi 20 fois.

  C'est ici, en intermediate, que la règle est écrite une fois : toutes les
  tables de production en aval ne comptent que les fiches retenues.
#}

with fiches as (

    select * from {{ ref('stg_production__fiches_poste') }}

),

classees as (

    select
        *,
        row_number() over (
            partition by date_poste, shift, equipe
            order by coalesce(modifie_le, cree_le) desc, id_fiche desc
        ) as rang,
        count(*) over (partition by date_poste, shift, equipe) as saisies_du_poste
    from fiches
    where supprime_le is null
      and date_poste is not null
      and shift is not null
      and equipe is not null

)

select
    f.id_fiche,
    f.date_poste,
    f.shift,
    f.equipe,
    f.cree_le,
    f.modifie_le,
    coalesce(c.rang = 1, false)                         as est_retenue,
    case
        when f.supprime_le is not null then 'supprimée'
        when f.date_poste is null or f.shift is null or f.equipe is null then 'incomplète'
        when c.rang > 1 then 'doublon'
    end                                                 as motif_exclusion,
    coalesce(c.saisies_du_poste, 0)                     as saisies_du_poste
from fiches as f
left join classees as c
    on c.id_fiche = f.id_fiche
