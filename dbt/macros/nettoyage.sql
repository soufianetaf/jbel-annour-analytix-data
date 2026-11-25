{#
  Nettoyage commun aux applications de l'usine (et à toute source autre
  que Sage X3). Mêmes règles que nettoyage_x3, nom générique.
#}

{# Texte : espaces autour retirés ; texte vide → NULL #}
{% macro texte(colonne) -%}
    nullif(trim({{ colonne }}), '')
{%- endmacro %}


{# Date et heure → date (les applications de l'usine stockent des datetime) #}
{% macro date_seule(colonne) -%}
    cast({{ colonne }} as date)
{%- endmacro %}
