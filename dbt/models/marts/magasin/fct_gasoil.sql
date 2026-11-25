{#
  Grain : une ligne = un bon de gasoil.

  litres = quantité saisie (positive ; médiane 75 L au 25/11/2026).
  Les bons négatifs ou de plus de 2 000 L sont des erreurs de saisie,
  listées par le test assert_magasin_gasoil_quantite_plausible.
  Un bon compte quand il est traité (DONE) et approuvé (APPROVED).

  Véhicule : l'immatriculation (colonne « matricule » de la source).
  compteur_km est le RELEVÉ du compteur. La distance est l'écart avec le
  relevé du bon valide précédent du même véhicule ; elle est vide si elle
  est négative ou supérieure à 5 000 km (compteur mal saisi, test
  assert_magasin_gasoil_compteur_plausible).

  Litres aux 100 km d'un véhicule sur une période :
      somme(litres) / somme(km_depuis_bon_precedent) × 100
  (sur les bons valides qui ont une distance).
#}

with bons as (

    select
        *,
        statut = 'DONE' and decision = 'APPROVED' as valide
    from {{ ref('stg_magasin__gasoil') }}

),

avec_precedent as (

    select
        *,
        lag(compteur_km) over (
            partition by vehicule, valide
            order by cree_le, id_bon
        ) as compteur_precedent
    from bons

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
    cast(case
            when valide
             and compteur_km - compteur_precedent between 0 and 5000
            then compteur_km - compteur_precedent
         end as integer)                                        as km_depuis_bon_precedent,
    cast(decision as text)                                      as decision,
    cast(valide as boolean)                                     as est_valide,
    cast(_charge_le as timestamp with time zone)                as charge_le
from avec_precedent
