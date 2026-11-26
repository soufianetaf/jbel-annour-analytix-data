{#
  Grain : une ligne = un modèle de tournée préventive (une zone × un poste).
  Source : raw_maintenance.rapports. Chaque zone × poste existe deux fois ;
  seul le premier jeu a des tournées.
#}

select
    cast(id as bigint)              as id_rapport,
    {{ zone_usine('type') }}        as zone,
    {{ poste_usine('shift') }}      as poste,
    _charge_le
from {{ source('maintenance', 'rapports') }}
