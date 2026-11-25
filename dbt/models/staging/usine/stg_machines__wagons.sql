{#
  Grain : une ligne = le passage d'un wagon à l'empileuse (chargement) ou
  à la dépileuse (déchargement), enregistré par l'automate.
  Sources : raw_empileuse.chargement_wagons, raw_depileuse.dechargement_wagons
  (sans nom d'opérateur).
#}

with chargements as (

    select
        'empileuse'                     as machine,
        'chargement'                    as operation,
        cast("id" as bigint)            as id_passage,
        date_heure_entree               as entree_le,
        date_heure_sortie               as sortie_le,
        ordre_wagon,
        numero_reel_wagon               as numero_wagon,
        temps_decharge,
        _charge_le
    from {{ source('empileuse', 'chargement_wagons') }}

),

dechargements as (

    select
        'depileuse',
        'déchargement',
        cast("id" as bigint),
        date_heure_entree,
        date_heure_sortie,
        ordre_wagon,
        numero_reel_wagon,
        temps_decharge,
        _charge_le
    from {{ source('depileuse', 'dechargement_wagons') }}

)

select * from chargements
union all
select * from dechargements
