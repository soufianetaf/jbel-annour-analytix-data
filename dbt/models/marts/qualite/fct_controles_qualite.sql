{#
  Grain : une ligne = un défaut contrôlé sur un chariot en sortie du four.
  Définitions : docs/indicateurs/qualite.md

  Chaque chariot est contrôlé sur une liste fixe de 11 défauts ; le
  contrôleur donne une couleur par défaut (statut) et, s'il y a défaut,
  des quantités. Les quantités sont parfois aberrantes (8 668, 356 226) :
  elles sont gardées telles quelles, les indicateurs comptent les statuts.
#}

select
    cast(c.id_controle as bigint)                   as id_controle,
    cast(c.id_chariot as bigint)                    as id_chariot,
    cast(ch.id_rapport as bigint)                   as id_rapport,
    cast(r.jour as date)                            as jour,
    cast(r.poste as text)                           as poste,
    cast(ch.type_brique as text)                    as type_brique,
    cast(ch.numero_chariot as text)                 as numero_chariot,
    cast(c.code_defaut as text)                     as code_defaut,
    cast(c.defaut as text)                          as defaut,
    cast(c.famille_defaut as text)                  as famille_defaut,
    cast(c.statut as text)                          as statut,
    cast(c.quantite_non_acceptable as integer)      as quantite_non_acceptable,
    cast(c.quantite_endommagee as integer)          as quantite_endommagee,
    cast(c.defaut_acceptable as boolean)            as defaut_acceptable,
    cast(c.separable as boolean)                    as separable
from {{ ref('stg_qualite__controles') }} as c
inner join {{ ref('stg_qualite__chariots') }} as ch
    on ch.id_chariot = c.id_chariot
inner join {{ ref('int_qualite__rapports_dates') }} as r
    on r.id_rapport = ch.id_rapport
