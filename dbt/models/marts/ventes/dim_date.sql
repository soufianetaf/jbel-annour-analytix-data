{#
  Grain : une ligne = un jour, du 1er janvier 2020 au 31 décembre 2030.

  Dimension partagée par tous les domaines (ventes, achats, production…).
  Générée, sans source : aucun jour ne manque, même sans vente ce jour-là.
#}

with jours as (

    select cast(jour as date) as date_jour
    from generate_series(date '2020-01-01', date '2030-12-31', interval '1 day') as jour

)

select
    date_jour,
    cast(extract(year from date_jour) as integer)                   as annee,
    cast(extract(quarter from date_jour) as integer)                as trimestre,
    cast(extract(month from date_jour) as integer)                  as mois,
    cast(to_char(date_jour, 'YYYY-MM') as text)                     as annee_mois,
    cast(
        (array['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
               'août', 'septembre', 'octobre', 'novembre', 'décembre'])
        [extract(month from date_jour)] as text
    )                                                               as nom_mois,
    cast(extract(isoyear from date_jour) as integer)                as annee_iso,
    cast(extract(week from date_jour) as integer)                   as semaine_iso,
    -- 1 = lundi … 7 = dimanche
    cast(extract(isodow from date_jour) as integer)                 as jour_semaine,
    cast(
        (array['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'])
        [extract(isodow from date_jour)] as text
    )                                                               as nom_jour,
    (extract(isodow from date_jour) = 7)                            as est_dimanche

from jours
