{#
  Grain : une ligne = un prélèvement de briques pour mesure (zone, type).
  Source : raw_qualite.infos.

  Zone : seules « Sortie Séchoir », « Sortie Mouleuse » et « Four » sont
  reconnues ; le reste (« Yyt », « Gvv »…) sont des essais de saisie,
  gardés avec zone vide. Référence du moule écrite de plusieurs façons
  (G299-01, g-299-01, G.299.01) : ramenée à lettres et chiffres.
#}

select
    cast(id as bigint)                                  as id_prelevement,
    cast(rapport_id as bigint)                          as id_rapport,
    case lower({{ texte('zone') }})
        when 'sortie séchoir' then 'séchoir'
        when 'sechoire' then 'séchoir'
        when 'sortie mouleuse' then 'mouleuse'
        when 'moulage' then 'mouleuse'
        when 'monobloc' then 'mouleuse'
        when 'four' then 'four'
    end                                                 as zone,
    {{ texte('zone') }}                                 as zone_saisie,
    upper({{ texte('type') }})                          as type_brique,
    nullif(regexp_replace(upper(referance), '[^A-Z0-9]', '', 'g'), '')
                                                        as reference_moule,
    created_at                                          as cree_le,
    _charge_le
from {{ source('qualite', 'infos') }}
