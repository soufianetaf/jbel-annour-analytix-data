{#
  Grain : une ligne = une tournée préventive saisie, avec la décision de la
  retenir ou non.

  Une même tournée (zone, poste, jour) est souvent saisie plusieurs fois :
  jusqu'à 36 saisies, en brouillon (statut 1) ou validées (statut 2), parfois
  sans aucun résultat. Compter toutes les saisies multiplierait les points
  contrôlés. Règle (docs/indicateurs/maintenance.md, à valider) : pour une
  zone, un poste et un jour, une seule tournée est retenue :
  1. celle qui a des résultats,
  2. de préférence validée (statut 2),
  3. puis la plus récemment modifiée (à égalité, l'identifiant le plus grand).
#}

with resultats as (

    select id_tournee, count(*) as resultats
    from {{ ref('stg_maintenance__resultats') }}
    group by id_tournee

),

tournees as (

    select
        t.*,
        r.zone,
        r.poste,
        coalesce(x.resultats, 0)                                as resultats
    from {{ ref('stg_maintenance__tournees') }} as t
    inner join {{ ref('stg_maintenance__rapports') }} as r
        on r.id_rapport = t.id_rapport
    left join resultats as x
        on x.id_tournee = t.id_tournee

),

classees as (

    select
        *,
        row_number() over (
            partition by zone, poste, jour
            order by (resultats > 0) desc, (statut = 2) desc,
                     coalesce(modifie_le, cree_le) desc, id_tournee desc
        )                                                       as rang,
        count(*) over (partition by zone, poste, jour)          as saisies
    from tournees

)

select
    id_tournee,
    zone,
    poste,
    jour,
    equipe,
    statut,
    resultats,
    saisies                                                     as saisies_de_la_tournee,
    rang = 1 and resultats > 0                                  as est_retenue
from classees
