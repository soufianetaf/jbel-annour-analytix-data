{#
  Grain : une ligne = un bon de gasoil.

  litres = quantité saisie (positive ; médiane 75 L au 25/11/2026).
  Les bons négatifs ou de plus de 2 000 L sont des erreurs de saisie,
  listées par le test assert_magasin_gasoil_quantite_plausible.
  Un bon compte quand il est traité (DONE) et approuvé (APPROVED).
  compteur_km est le RELEVÉ du compteur (pas une distance) : la distance
  d'un véhicule entre deux bons = écart entre deux relevés.
  Le véhicule (colonne « matricule » de la source) n'est pas encore copié :
  sa nature est à confirmer (véhicule ou personne).
#}

with bons as (

    select * from {{ ref('stg_magasin__gasoil') }}

)

select
    cast(id_bon as integer)                                     as id_bon,
    cast(numero_bon as text)                                    as numero_bon,
    cast(cree_le as date)                                       as date_bon,
    cast(vehicule as text)                                      as vehicule,
    cast(service as text)                                       as service,
    cast(affectation_1 as text)                                 as affectation_1,
    cast({{ cle_x3('article') }} as text)                       as cle_article,
    cast(article as text)                                       as code_article,
    cast(quantite_saisie as numeric(18, 3))                     as litres,
    cast(compteur_km as integer)                                as compteur_km,
    cast(decision as text)                                      as decision,
    cast(statut = 'DONE' and decision = 'APPROVED' as boolean)  as est_valide,
    cast(_charge_le as timestamp with time zone)                as charge_le
from bons
