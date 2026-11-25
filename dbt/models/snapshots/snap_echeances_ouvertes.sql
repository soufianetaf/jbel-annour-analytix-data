{#
  Photo quotidienne des échéances ouvertes.
  Grain : une ligne = une échéance ouverte × un jour de photo.

  Pourquoi : Sage X3 ne garde que l'état actuel. Une facture réglée
  aujourd'hui n'apparaît plus comme ouverte hier. Sans cette photo, la
  balance âgée de la fin du mois dernier, le DSO ou l'évolution des
  créances sont impossibles à reconstituer. Chaque jour sans photo est
  perdu pour toujours (cahier des charges, 8.4 d).

  Fonctionnement : à chaque « dbt build », la photo DU JOUR est
  (re)calculée et remplace celle du même jour ; les photos des jours
  précédents ne sont jamais modifiées.
#}

{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='date_photo',
        on_schema_change='fail',
        full_refresh=false
    )
}}
{#
  full_refresh=false : même « dbt build --full-refresh » ne reconstruit
  JAMAIS cette table. Sans cette protection, la commande effacerait toutes
  les photos passées, qui ne peuvent pas être recalculées.
#}
{{
    config(tags=['photo'])
}}

select
    cast({{ date_du_jour() }} as date)                    as date_photo,
    type_piece,
    numero_piece,
    ligne_piece,
    numero_echeance,
    type_tiers,
    code_tiers,
    cle_client,
    compte_collectif,
    date_echeance,
    mode_paiement,
    reste_a_payer,
    jours_retard,
    tranche_retard,
    est_lettree
from {{ ref('fct_echeances') }}
where est_ouverte
