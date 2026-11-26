{#
  Nettoyage commun aux applications de l'usine (et à toute source autre
  que Sage X3). Mêmes règles que nettoyage_x3, nom générique.
#}

{# Texte : espaces autour retirés ; texte vide → NULL #}
{% macro texte(colonne) -%}
    nullif(trim({{ colonne }}), '')
{%- endmacro %}


{#
  Nombre saisi en texte → nombre (cahier des charges 5.2 : quantités
  saisies comme du texte). Espaces retirés, virgule décimale acceptée.
  Tout ce qui n'est pas un nombre (« 12 t », « néant », vide) devient vide :
  rien n'est deviné.
#}
{% macro nombre_saisi(colonne) -%}
    case
        when replace(replace(trim({{ colonne }}), ' ', ''), ',', '.') ~ '^-?\d+(\.\d+)?$'
        then replace(replace(trim({{ colonne }}), ' ', ''), ',', '.')::numeric
    end
{%- endmacro %}


{# Date et heure → date (les applications de l'usine stockent des datetime) #}
{% macro date_seule(colonne) -%}
    cast({{ colonne }} as date)
{%- endmacro %}
