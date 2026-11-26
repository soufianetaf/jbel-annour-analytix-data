{#
  Grain : une ligne = un chariot contrôlé en sortie du four.

  Statut du chariot = le plus grave de ses défauts :
  défaut majeur > défaut mineur > conforme ; « non contrôlé » si aucun
  défaut n'a été contrôlé (tout en bleu ou sans couleur).
#}

with defauts as (

    select
        id_chariot,
        count(*)                                                    as defauts_listes,
        count(*) filter (where statut in ('conforme', 'défaut mineur', 'défaut majeur'))
                                                                    as defauts_controles,
        count(*) filter (where statut = 'défaut mineur')            as defauts_mineurs,
        count(*) filter (where statut = 'défaut majeur')            as defauts_majeurs,
        string_agg(defaut, ', ' order by defaut) filter (where statut = 'défaut majeur')
                                                                    as liste_defauts_majeurs
    from {{ ref('fct_controles_qualite') }}
    group by id_chariot

)

select
    cast(ch.id_chariot as bigint)                   as id_chariot,
    cast(ch.id_rapport as bigint)                   as id_rapport,
    cast(r.jour as date)                            as jour,
    cast(r.poste as text)                           as poste,
    cast(ch.type_brique as text)                    as type_brique,
    cast(ch.numero_chariot as text)                 as numero_chariot,
    cast(ch.heure_sortie_four as time)              as heure_sortie_four,
    cast(ch.heure_controle as time)                 as heure_controle,
    cast(case
        when d.defauts_majeurs > 0 then 'défaut majeur'
        when d.defauts_mineurs > 0 then 'défaut mineur'
        when d.defauts_controles > 0 then 'conforme'
        else 'non contrôlé'
    end as text)                                    as statut_chariot,
    cast(coalesce(d.defauts_listes, 0) as integer)  as defauts_listes,
    cast(coalesce(d.defauts_controles, 0) as integer) as defauts_controles,
    cast(coalesce(d.defauts_mineurs, 0) as integer) as defauts_mineurs,
    cast(coalesce(d.defauts_majeurs, 0) as integer) as defauts_majeurs,
    cast(d.liste_defauts_majeurs as text)           as liste_defauts_majeurs
from {{ ref('stg_qualite__chariots') }} as ch
inner join {{ ref('int_qualite__rapports_dates') }} as r
    on r.id_rapport = ch.id_rapport
left join defauts as d
    on d.id_chariot = ch.id_chariot
