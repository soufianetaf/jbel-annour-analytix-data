{#
  Grain : une ligne = une coupure des mesures du moulage de plus d'une heure.

  Une coupure peut être un arrêt de la machine ou une panne de la collecte
  (cahier des charges, 5.2). Le relevé de fin de poste du monobloc aide à
  trancher : s'il indique des heures de marche le même jour, la coupure
  est plus probablement une panne de collecte (colonne heures_marche_du_jour).
#}

with mesures as (

    select
        mesure_le as debut,
        lead(mesure_le) over (order by mesure_le, id_mesure) as fin
    from {{ ref('stg_moulage__mesures') }}

)

select
    cast(m.debut as timestamp)                                          as debut,
    cast(m.fin as timestamp)                                            as fin,
    cast(extract(epoch from m.fin - m.debut) / 3600 as numeric(10, 2))  as duree_heures,
    cast(j.heures_marche as numeric(10, 3))                             as heures_marche_du_jour
from mesures as m
left join {{ ref('fct_machines_jour') }} as j
    on j.machine = 'moulage'
   and j.jour = cast(m.debut as date)
where m.fin - m.debut > interval '1 hour'
