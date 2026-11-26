{#
  AVERTISSEMENT (ne bloque pas) : bons de gasoil valides dont le relevé de
  compteur recule, ou avance de plus de 5 000 km, par rapport au bon
  valide précédent du même véhicule.

  Pourquoi : la distance sert au calcul des litres aux 100 km. Un relevé
  mal saisi donnerait une distance absurde : fct_gasoil la laisse vide, et
  ce test liste les bons concernés pour le magasin.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Magasin', 'correction': "Corriger le kilométrage saisi sur le bon de gasoil dans l'application Magasin."},
) }}

with bons as (

    select
        id_bon,
        vehicule,
        date_bon,
        compteur_km,
        lag(compteur_km) over (partition by vehicule order by date_bon, id_bon) as precedent
    from {{ ref('fct_gasoil') }}
    where est_valide

)

select id_bon, vehicule, date_bon, precedent, compteur_km
from bons
where precedent is not null
  and (compteur_km < precedent or compteur_km - precedent > 5000)
