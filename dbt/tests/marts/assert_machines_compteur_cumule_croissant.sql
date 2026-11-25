{#
  AVERTISSEMENT (ne bloque pas) : jours où un relevé de machine est plus
  grand que le dernier relevé de la journée.

  Pourquoi : fct_machines_jour prend le DERNIER relevé du jour comme total,
  parce que les compteurs sont cumulés depuis le début de la journée. Si un
  compteur était remis à zéro en cours de journée, le dernier relevé
  sous-estimerait la production : ce test le détecterait.
#}

{{ config(severity='warn') }}

with releves as (

    select
        machine,
        cast(releve_le as date) as jour,
        production,
        first_value(production) over (
            partition by machine, cast(releve_le as date)
            order by releve_le desc
        ) as dernier
    from {{ ref('stg_machines__releves') }}

)

select machine, jour, max(production) as releve_max, max(dernier) as dernier_releve
from releves
group by machine, jour
having max(production) > max(dernier) + 0.001
