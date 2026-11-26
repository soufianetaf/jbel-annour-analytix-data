{#
  Grain : une ligne = un rapport de consommations saisi dans l'application
  de production (base production_2026), de mars 2025 à octobre 2026.
  Source : raw_production.consomations.

  Les quantités sont saisies en TEXTE dans l'application : elles sont
  converties en nombres (macro nombre_saisi) ; ce qui n'est pas un nombre
  devient vide et se compte avec les colonnes *_saisi.
  Les noms de colonnes accentués de la source ont été abîmés à la copie
  (« Consommation_Électrique » → consommation_lectrique).
#}

with source as (

    select * from {{ source('production', 'consomations') }}
    where deleted_at is null

)

select
    cast(id as bigint)                                          as id_rapport,
    {{ date_seule('date') }}                                    as jour,
    {{ texte('heure_rapport') }}                                as heure_rapport,
    {{ nombre_saisi('consommation_lectrique') }}                as electricite,
    {{ nombre_saisi('consommation_coke_four') }}                as coke_four,
    {{ nombre_saisi('consommation_fuel_four') }}                as fuel_four,
    {{ nombre_saisi('consommation_charbon') }}                  as charbon,
    {{ nombre_saisi('consommation_propane') }}                  as propane,
    {{ nombre_saisi('total_production_en_tonne') }}             as production_tonnes,
    {{ texte('consommation_lectrique') }}                       as electricite_saisi,
    {{ texte('consommation_coke_four') }}                       as coke_four_saisi,
    {{ texte('total_production_en_tonne') }}                    as production_tonnes_saisi,
    _charge_le
from source
