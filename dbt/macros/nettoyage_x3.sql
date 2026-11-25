{#
  Nettoyage des valeurs « vides déguisées » de Sage X3.

  Sage X3 ne stocke jamais de vide (NULL) :
  - un texte vide est un espace ' ' (ou plusieurs) ;
  - une date absente vaut 1753-01-01 (minimum de SQL Server) ou 1900-01-01.

  Ces macros les transforment en vrais vides, pour que les comptages,
  les jointures et les filtres « valeur absente » fonctionnent.
  Utilisées seulement dans la couche staging.
#}

{# Texte : espaces autour retirés ; texte vide → NULL #}
{% macro texte_x3(colonne) -%}
    nullif(trim({{ colonne }}), '')
{%- endmacro %}


{# Date : 1753, 1900 ou toute date avant 1901 → NULL ; sinon type date #}
{% macro date_x3(colonne) -%}
    case
        when {{ colonne }} < date '1901-01-01' then null
        else cast({{ colonne }} as date)
    end
{%- endmacro %}


{# Date et heure : mêmes règles, en gardant l'heure #}
{% macro horodatage_x3(colonne) -%}
    case
        when {{ colonne }} < timestamp '1901-01-01' then null
        else {{ colonne }}
    end
{%- endmacro %}
