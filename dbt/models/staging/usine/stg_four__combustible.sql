{#
  Grain : une ligne = un relevé de l'automate du four (fin de poste).
  Source : raw_four_prod.donnes_prod_four.

  Colonnes de combustible et de cuisson. Comme les autres compteurs des
  automates, les quantités sont cumulées depuis le début de la journée :
  le total du jour est le dernier relevé (voir agg_energie_jour).
#}

select
    date_insert                         as releve_le,
    qte_brique_tonne                    as tonnes_cuites,
    ration_cuisson_cocke_kg_tonne       as coke_kg_par_tonne,
    consomm_coke_tonne                  as coke_consomme_tonnes,
    qte_coke_livre_tonne                as coke_livre_tonnes,
    cadence_consom_coke_tonne_hr        as coke_tonnes_par_heure,
    stock_coke_petrol_silo1             as stock_coke_silo1,
    stock_coke_petrol_silo2             as stock_coke_silo2,
    stock_fuel_reserv1                  as stock_fuel,
    nbr_brule_operationnel              as bruleurs_en_marche,
    _charge_le
from {{ source('four_prod', 'donnes_prod_four') }}
