{#
  Tranche de la balance âgée d'une échéance (docs/indicateurs/finance_creances.md).

  Écrite une seule fois, utilisée par l'état actuel (fct_echeances) ET par
  la photo quotidienne (snap_echeances_ouvertes) : la balance âgée d'hier
  et celle d'aujourd'hui sont calculées exactement de la même façon.

  retard : expression en jours (date de calcul - date d'échéance)
  ouverte : expression booléenne ; une échéance soldée n'a pas de tranche
#}
{% macro tranche_balance_agee(retard, ouverte) -%}
    case
        when not ({{ ouverte }}) then null
        when {{ retard }} <= 0   then '0 - non échu'
        when {{ retard }} <= 30  then '1 - 1 à 30 jours'
        when {{ retard }} <= 60  then '2 - 31 à 60 jours'
        when {{ retard }} <= 90  then '3 - 61 à 90 jours'
        when {{ retard }} <= 180 then '4 - 91 à 180 jours'
        when {{ retard }} <= 365 then '5 - 181 à 365 jours'
        else                          '6 - plus de 365 jours'
    end
{%- endmacro %}


{#
  Date à laquelle on calcule retards et photos : aujourd'hui.
  En macro pour que les tests unitaires puissent la figer
  (overrides: macros: date_du_jour: …).
#}
{% macro date_du_jour() -%}
    current_date
{%- endmacro %}
