{#
  Durée saisie par un automate en texte « h:mm:ss » → heures (décimal).

  Les automates écrivent des durées avec des espaces à la place des zéros
  (« 2: 1:53 » pour 2 h 01 min 53 s) et parfois un texte (« encours »).
  Tout ce qui n'a pas la forme h:m:s devient vide. Arrondi à 4 décimales
  d'heure (un tiers de seconde).
#}
{% macro duree_heures(colonne) -%}
    case
        when replace({{ colonne }}, ' ', '') ~ '^\d+:\d+:\d+$' then round(
              split_part(replace({{ colonne }}, ' ', ''), ':', 1)::numeric
            + split_part(replace({{ colonne }}, ' ', ''), ':', 2)::numeric / 60
            + split_part(replace({{ colonne }}, ' ', ''), ':', 3)::numeric / 3600, 4)
    end
{%- endmacro %}
