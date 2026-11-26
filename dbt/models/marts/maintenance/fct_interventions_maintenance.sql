{#
  Grain : une ligne = une ligne d'intervention (un équipement, une plage horaire).
  Définitions : docs/indicateurs/maintenance.md

  minutes_arret = durée de l'intervention quand la machine était à l'arrêt
  (état « ARR ») : c'est le temps d'arrêt dû à la panne vu par la maintenance.
#}

with pieces as (

    select id_ligne, count(*) as pieces, sum(quantite) as quantite_pieces
    from {{ ref('stg_maintenance__pieces_intervention') }}
    group by id_ligne

)

select
    cast(l.id_ligne as bigint)                                      as id_ligne,
    cast(l.id_intervention as bigint)                               as id_intervention,
    cast(i.numero_fiche as text)                                    as numero_fiche,
    cast(coalesce(l.jour, i.jour) as date)                          as jour,
    cast(i.zone as text)                                            as zone,
    cast(i.service as text)                                         as service,
    cast(i.equipe as text)                                          as equipe,
    cast(i.poste as text)                                           as poste,
    cast(l.equipement as text)                                      as equipement,
    cast(l.etat_machine as text)                                    as etat_machine,
    cast(l.type_panne as text)                                      as type_panne,
    cast(l.type_intervention as text)                               as type_intervention,
    cast(l.debut as time)                                           as debut,
    cast(l.fin as time)                                             as fin,
    cast(l.duree_minutes as integer)                                as duree_minutes,
    cast(case when l.etat_machine = 'arrêt' then l.duree_minutes end as integer)
                                                                    as minutes_arret,
    cast(l.duree_saisie as text)                                    as duree_saisie,
    cast(coalesce(p.pieces, 0) as integer)                          as pieces,
    cast(p.quantite_pieces as numeric(12, 2))                       as quantite_pieces,
    cast(l.numero_ot as text)                                       as numero_ot
from {{ ref('stg_maintenance__lignes_intervention') }} as l
inner join {{ ref('stg_maintenance__interventions') }} as i
    on i.id_intervention = l.id_intervention
left join pieces as p
    on p.id_ligne = l.id_ligne
