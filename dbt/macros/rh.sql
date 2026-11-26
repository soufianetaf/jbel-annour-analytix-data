{#
  Données RH agrégées (docs/indicateurs/rh.md). Le groupe des petits services,
  fusionné à la copie (ingestion.usine_rh), garde son libellé.
#}

{% macro groupe_rh_masque() -%}
    'autres (moins de 5 personnes)'
{%- endmacro %}


{#
  Service écrit de plusieurs façons (accents, singulier ou pluriel, fautes)
  dans les applications RH et pointage → un seul libellé, sans accent.
#}
{% macro service_rh(colonne) -%}
    case
        when {{ colonne }} = {{ groupe_rh_masque() }} then {{ colonne }}
        else
            case translate(upper(trim({{ colonne }})), 'ÉÈÊËÀÂÄÔÖÛÙÜÎÏÇ', 'EEEEAAAOOUUUIIC')
                when 'DIRECTION GENERAL' then 'DIRECTION GENERALE'
                when 'MOYENS GENEREAUX' then 'MOYENS GENERAUX'
                when 'ARCHIVES' then 'ARCHIVE'
                when 'ACHAT' then 'ACHATS'
                when 'METHODE' then 'METHODES'
                else translate(upper(trim({{ colonne }})), 'ÉÈÊËÀÂÄÔÖÛÙÜÎÏÇ', 'EEEEAAAOOUUUIIC')
            end
    end
{%- endmacro %}
