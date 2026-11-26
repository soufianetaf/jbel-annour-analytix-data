{#
  Libellés des défauts de l'application qualité. La source les donne en
  arabe ; traduction proposée, à valider par le responsable qualité
  (docs/indicateurs/qualite.md). Les codes de l'application ne
  correspondent pas toujours au libellé (BB = brûlé, BR = tombé) : c'est
  le libellé qui fait foi.
#}
{% macro defaut_qualite(code) -%}
    case {{ code }}
        when 'MC'  then 'Sous-cuit'
        when 'BB'  then 'Surcuit (brûlé)'
        when 'TC'  then 'Taches de coke, coke non brûlé'
        when 'CH'  then 'Nodules de chaux'
        when 'EC'  then 'Écaillage'
        when 'D'   then 'Déformation'
        when 'R'   then 'Retrait'
        when 'GF'  then 'Affaissement'
        when 'BR'  then 'Briques tombées'
        when 'FL'  then 'Fissures sur la largeur'
        when 'FP'  then 'Fissures sur les deux faces'
        when 'FH'  then 'Fissures longitudinales'
        when 'FV'  then 'Fissures transversales'
        when 'AD'  then 'Gauchissement'
        when 'TD'  then 'Déchirure'
        when 'QA'  then 'Aspect'
        when 'PC'  then 'Masse conforme'
        when 'DIM' then 'Dimensions conformes'
    end
{%- endmacro %}


{% macro famille_defaut_qualite(code) -%}
    case
        when {{ code }} in ('MC', 'BB', 'TC') then 'cuisson'
        when {{ code }} in ('CH', 'EC') then 'matière'
        when {{ code }} in ('D', 'R', 'GF') then 'forme'
        when {{ code }} in ('FL', 'FP', 'FH', 'FV') then 'fissures'
        when {{ code }} = 'BR' then 'manutention'
        else 'autre contrôle'
    end
{%- endmacro %}


{#
  Couleur saisie par le contrôleur → statut. Interprétation à valider :
  vert = pas de défaut, jaune = défaut mineur, rouge = défaut majeur,
  bleu = non contrôlé (aucune quantité n'est jamais saisie en bleu).
#}
{% macro statut_controle_qualite(couleur) -%}
    case {{ couleur }}
        when 'green'  then 'conforme'
        when 'yellow' then 'défaut mineur'
        when 'red'    then 'défaut majeur'
        when 'blue'   then 'non contrôlé'
        else 'non renseigné'
    end
{%- endmacro %}


{# Poste écrit « 07h00-15h00 » ou « 07h00 - 15h00 » → « 07h00 - 15h00 » (comme la production) #}
{% macro poste_usine(colonne) -%}
    nullif(regexp_replace(trim({{ colonne }}), '\s*-\s*', ' - '), '')
{%- endmacro %}
