{#
  Photo quotidienne du stock.
  Grain : une ligne = un article × un site × un jour de photo
  (seulement les articles qui ont du stock, en contrôle ou rejeté).

  Pourquoi : Sage X3 ne garde que le stock actuel. Le stock à la fin du
  mois dernier, la rotation ou la couverture ne se recalculent pas de
  façon fiable après coup (cahier des charges, 8.4 d). Chaque jour sans
  photo est perdu pour toujours.

  Même fonctionnement que snap_echeances_ouvertes : la photo du jour est
  (re)calculée à chaque « dbt build », les jours passés ne sont jamais
  modifiés, et la table n'est jamais reconstruite (full_refresh=false).
#}

{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='date_photo',
        on_schema_change='fail',
        full_refresh=false,
        tags=['photo']
    )
}}

select
    cast({{ date_du_jour() }} as date)      as date_photo,
    cle_article,
    code_article,
    site,
    stock_physique,
    stock_controle,
    stock_rejete,
    cmup,
    valeur_stock,
    est_dormant
from {{ ref('fct_stock_article') }}
where stock_physique <> 0
   or stock_controle <> 0
   or stock_rejete <> 0
