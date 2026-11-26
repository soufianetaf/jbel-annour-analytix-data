{#
  Grain : une ligne = un point de contrôle d'un équipement dans une tournée
  préventive retenue (une par zone, poste et jour).
  Définitions : docs/indicateurs/maintenance.md
#}

select
    cast(r.id_resultat as bigint)                   as id_resultat,
    cast(t.id_tournee as bigint)                    as id_tournee,
    cast(t.jour as date)                            as jour,
    cast(t.zone as text)                            as zone,
    cast(t.poste as text)                           as poste,
    cast(t.equipe as text)                          as equipe,
    cast(e.id_equipement as bigint)                 as id_equipement,
    cast(e.equipement as text)                      as equipement,
    cast(e.code_sage as text)                       as code_sage,
    cast(e.code_machine as text)                    as code_machine,
    cast(a.action as text)                          as point_controle,
    cast(r.statut as text)                          as statut,
    cast(r.priorite as integer)                     as priorite,
    cast(r.nature as text)                          as nature,
    cast(r.suite_donnee as text)                    as suite_donnee,
    cast(r.numero_ot as text)                       as numero_ot
from {{ ref('stg_maintenance__resultats') }} as r
inner join {{ ref('int_maintenance__tournees_retenues') }} as t
    on t.id_tournee = r.id_tournee
   and t.est_retenue
left join {{ ref('stg_maintenance__points_controle') }} as p
    on p.id_point = r.id_point
left join {{ ref('stg_maintenance__equipements') }} as e
    on e.id_equipement = p.id_equipement
left join {{ ref('stg_maintenance__actions') }} as a
    on a.id_action = p.id_action
