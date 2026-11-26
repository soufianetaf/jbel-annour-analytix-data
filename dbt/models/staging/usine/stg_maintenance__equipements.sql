{#
  Grain : une ligne = un équipement de l'usine.
  Source : raw_maintenance.equipements.

  Code Sage X3 : 2 lettres de zone + E + numéro de machine (ME03 =
  monobloc), puis SE + numéro de sous-ensemble (ME03SE02 = extrudeuse).
  Le secteur (S1, S2, S3) est à la fin du nom : un même code existe dans
  plusieurs secteurs.
#}

select
    cast(id as bigint)                                          as id_equipement,
    {{ texte('nom') }}                                          as equipement,
    upper({{ texte('code_e_sage') }})                           as code_sage,
    regexp_replace(upper({{ texte('code_e_sage') }}), 'SE\d+$', '')
                                                                as code_machine,
    substring(upper({{ texte('nom') }}) from '\s(S\d)$')        as secteur,
    _charge_le
from {{ source('maintenance', 'equipements') }}
