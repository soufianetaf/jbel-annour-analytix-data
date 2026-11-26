{#
  Grain : une ligne = un département (libellé harmonisé) × un jour.
  Source : raw_rh.pointage_service_jour (agrégat calculé sur la pointeuse).

  personnes                = salariés qui ont pointé au moins une fois ce jour-là
  personnes_entree_sortie  = salariés avec au moins deux pointages
  minutes_sur_site         = somme, pour ces derniers, de (dernier - premier pointage) ;
                             vide pour un petit groupe fusionné resté sous 5 personnes
#}

select
    {{ service_rh('service') }}                         as service,
    cast(jour as date)                                  as jour,
    cast(sum(personnes) as integer)                     as personnes,
    cast(sum(pointages) as integer)                     as pointages,
    cast(sum(personnes_entree_sortie) as integer)       as personnes_entree_sortie,
    cast(sum(minutes_sur_site) as bigint)               as minutes_sur_site,
    max(_charge_le)                                     as _charge_le
from {{ source('rh', 'pointage_service_jour') }}
group by 1, 2
