{#
  Grain : une ligne = un relevé d'une machine (moulage, empileuse, four,
  dépileuse), enregistré par l'automate en fin de poste.

  Les compteurs sont CUMULÉS depuis le début de la journée (vérifié le
  25/11/2026 : four 267 t à 7 h, 583 t à 15 h, 935 t le soir). Ne jamais
  additionner les relevés d'une journée : le total du jour est le dernier
  relevé (voir fct_machines_jour).

  Les durées « h:mm:ss » en texte sont converties en heures (macro
  duree_heures). Une même structure pour les quatre machines :
      production         quantité principale du jour à cet instant
      unite_production   étagère, wagon, tonne, paquet
#}

with moulage as (

    select
        'moulage'                               as machine,
        date_insert                             as releve_le,
        nbr_chariot_reel::numeric               as production,
        'étagère'                               as unite_production,
        nbr_chariot_calcul::numeric             as production_calculee,
        {{ duree_heures('heure_marche') }}      as heures_marche,
        {{ duree_heures('heure_arret_total') }} as heures_arret,
        nbr_demarrage                           as demarrages,
        _charge_le
    from {{ source('moulage', 'donnes_prod_mono') }}

),

empileuse as (

    select
        'empileuse',
        date_insert,
        wagons_empiles::numeric,
        'wagon',
        null::numeric,
        {{ duree_heures('heure_marche_empileuse') }},
        {{ duree_heures('heure_arret_empileuse') }},
        null::integer,
        _charge_le
    from {{ source('empileuse', 'donnes_prod_emp') }}

),

four as (

    select
        'four',
        date_insert,
        qte_brique_tonne::numeric,
        'tonne',
        qte_brique_unite::numeric,
        null::numeric,
        null::numeric,
        null::integer,
        _charge_le
    from {{ source('four_prod', 'donnes_prod_four') }}

),

depileuse as (

    select
        'depileuse',
        date_insert,
        paquet_embale::numeric,
        'paquet',
        paquet_vrac::numeric,
        {{ duree_heures('heure_marche') }},
        {{ duree_heures('heure_arret') }},
        null::integer,
        _charge_le
    from {{ source('depileuse', 'donnes_prod_dep') }}

)

select * from moulage
union all select * from empileuse
union all select * from four
union all select * from depileuse
