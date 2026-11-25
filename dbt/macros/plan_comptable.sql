{#
  Lecture du plan comptable marocain d'après les premiers chiffres du compte.
  Écrite une seule fois : dim_compte et le rapprochement l'utilisent.
  Référence : docs/indicateurs/finance_compte_de_resultat.md
#}

{# Classe 6 = charge, classe 7 = produit, autres classes = bilan #}
{% macro nature_compte(compte) -%}
    case left({{ compte }}, 1)
        when '6' then 'charge'
        when '7' then 'produit'
        else 'bilan'
    end
{%- endmacro %}


{# Rubrique du CPC (compte de produits et charges) #}
{% macro rubrique_cpc(compte) -%}
    case left({{ compte }}, 2)
        when '71' then '1 - Produits d''exploitation'
        when '61' then '2 - Charges d''exploitation'
        when '73' then '3 - Produits financiers'
        when '63' then '4 - Charges financières'
        when '75' then '5 - Produits non courants'
        when '65' then '6 - Charges non courantes'
        when '67' then '7 - Impôt sur les résultats'
        else case when left({{ compte }}, 1) in ('6', '7') then '8 - Autres' end
    end
{%- endmacro %}
