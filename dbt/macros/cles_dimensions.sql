{#
  Clés techniques des dimensions (cahier des charges, 8.3).

  Une clé est calculée à partir de la SOURCE et du CODE d'origine, pour
  que deux codes identiques venant de deux dossiers X3 (BASE1 et JBELRH)
  ne se mélangent jamais : md5('x3|BASE1|C001') ≠ md5('x3|JBELRH|C001').

  Un code absent (vide) pointe vers la ligne « Inconnu » de la dimension :
  la vente reste comptée dans les totaux, au lieu de disparaître d'une
  jointure.
#}

{# Clé de la ligne « Inconnu », la même dans toutes les dimensions #}
{% macro cle_inconnue() -%}
    '{{ local_md5("inconnu") }}'
{%- endmacro %}


{# Clé d'un code venant de Sage X3, dossier BASE1 #}
{% macro cle_x3(colonne, dossier='BASE1') -%}
    case
        when {{ colonne }} is null then {{ cle_inconnue() }}
        else md5('x3|{{ dossier }}|' || {{ colonne }})
    end
{%- endmacro %}
