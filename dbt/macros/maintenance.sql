{#
  Nettoyage commun aux applications de maintenance (et des autres zones
  de l'usine). Docs : docs/indicateurs/maintenance.md
#}

{# Zone de l'usine écrite de plusieurs façons → nom unique (Monobloc = moulage) #}
{% macro zone_usine(colonne) -%}
    case lower(trim({{ colonne }}))
        when 'monobloc' then 'moulage'
        when 'moulage' then 'moulage'
        when 'preparation' then 'préparation'
        when 'préparation' then 'préparation'
        when 'sechoir' then 'séchoir'
        when 'séchoir' then 'séchoir'
        when 'four' then 'four'
        when 'empileuse' then 'empileuse'
        when 'depileuse' then 'dépileuse'
        when 'dépileuse' then 'dépileuse'
    end
{%- endmacro %}


{# Poste écrit « matin », « apres-midi », « nuit » → même écriture que la production #}
{% macro poste_maintenance(colonne) -%}
    case lower(trim({{ colonne }}))
        when 'matin' then '07h00 - 15h00'
        when 'apres-midi' then '15h00 - 23h00'
        when 'après-midi' then '15h00 - 23h00'
        when 'nuit' then '23h00 - 07h00'
    end
{%- endmacro %}


{# Type de panne abrégé (Méc, Eléc, Chaud…) → libellé #}
{% macro type_panne(colonne) -%}
    case lower(trim({{ colonne }}))
        when 'méc' then 'mécanique'
        when 'mec' then 'mécanique'
        when 'eléc' then 'électrique'
        when 'éléc' then 'électrique'
        when 'chaud' then 'chaudronnerie'
        when 'hydr' then 'hydraulique'
        when 'pneu' then 'pneumatique'
        when 'plombie' then 'plomberie'
        when 'jonction' then 'jonction'
        when 'automatique' then 'automatisme'
    end
{%- endmacro %}


{#
  Durée d'une intervention en minutes, à partir des heures de début et de
  fin (la durée saisie en texte, « 0h10 », « 10 min », « 3h et 50 min »,
  ne sert que de contrôle). Une fin avant le début passe minuit : + 24 h.
  Au-delà de 12 h, c'est une erreur de saisie : vide.
#}
{% macro duree_intervention_minutes(debut, fin) -%}
    case
        when {{ debut }} is null or {{ fin }} is null then null
        when extract(epoch from ({{ fin }} - {{ debut }}
                 + case when {{ fin }} < {{ debut }} then interval '24 hours' else interval '0' end)) / 60 > 720
        then null
        else round(extract(epoch from ({{ fin }} - {{ debut }}
                 + case when {{ fin }} < {{ debut }} then interval '24 hours' else interval '0' end)) / 60)
    end
{%- endmacro %}
