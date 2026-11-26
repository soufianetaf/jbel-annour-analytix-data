{#
  Grain : une ligne = une tournée préventive saisie.
  Source : raw_maintenance.rapports_quotidiens, sans l'utilisateur.
  Statut : 0, 1 (en cours, points pas tous remplis), 2 (validée).
#}

select
    cast(id as bigint)              as id_tournee,
    cast(rapport_id as bigint)      as id_rapport,
    upper({{ texte('equipe') }})    as equipe,
    date_controle                   as jour,
    cast(statut as integer)         as statut,
    created_at                      as cree_le,
    updated_at                      as modifie_le,
    _charge_le
from {{ source('maintenance', 'rapports_quotidiens') }}
