{#
  Grain : une ligne = une zone × un poste (date, shift, équipe).

  Seules les fiches RETENUES sont comptées (int_production__fiches_dedoublonnees) :
  un poste saisi plusieurs fois n'est compté qu'une fois. Les lignes sans
  fiche ou rattachées à une fiche non retenue sont exclues.

  objectif = objectif saisi sur la ligne, à défaut objectif de la zone.
  taux_realisation = réalisé / objectif (vide si l'objectif est vide ou nul).
  Attention : pour certaines zones (empileuse, four), réalisé et objectif
  ne semblent pas dans la même unité (docs/indicateurs/production_postes.md).
#}

with lignes as (

    select * from {{ ref('stg_production__lignes_production') }}

),

fiches as (

    select * from {{ ref('int_production__fiches_dedoublonnees') }}
    where est_retenue

),

zones as (

    select * from {{ ref('stg_production__zones') }}

),

raisons as (

    select id_ligne, count(*) as nombre_raisons, string_agg(distinct raison, ' ; ') as raisons
    from {{ ref('stg_production__raisons_ecart') }}
    group by id_ligne

)

select
    cast(l.id_ligne as bigint)                                  as id_ligne,
    cast(f.id_fiche as bigint)                                  as id_fiche,
    cast(f.date_poste as date)                                  as date_poste,
    cast(f.shift as text)                                       as shift,
    cast(f.equipe as text)                                      as equipe,
    cast(coalesce(z.zone, l.zone) as text)                      as zone,
    cast(l.realise as numeric(18, 3))                           as realise,
    cast(coalesce(nullif(l.objectif, 0), z.objectif_par_poste) as numeric(18, 3))
                                                                as objectif,
    cast(l.realise / nullif(coalesce(nullif(l.objectif, 0), z.objectif_par_poste), 0)
         as numeric(18, 4))                                     as taux_realisation,
    cast(coalesce(r.nombre_raisons, 0) as integer)              as nombre_raisons_ecart,
    cast(r.raisons as text)                                     as raisons_ecart,
    cast(l._charge_le as timestamp with time zone)              as charge_le
from lignes as l
inner join fiches as f
    on f.id_fiche = l.id_fiche
left join zones as z
    on z.id_zone = l.id_zone
left join raisons as r
    on r.id_ligne = l.id_ligne
