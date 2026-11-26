{#
  Grain : une ligne = une pièce de rechange utilisée sur une ligne d'intervention.
  Source : raw_maintenance_interventions.lignes_intervention, colonne
  code_article_pdr, une liste JSON : [{"code": "A02930", "qte": 2}, …].

  « RAS », « Ras », « - », « Aucun » veulent dire « pas de pièce » : pas de
  ligne. Une liste qui n'est pas de la forme [{…}] (« ["RAS"] ») est ignorée.
#}

with lignes as (

    select
        id,
        {{ texte('code_article_pdr') }} as pieces_json,
        _charge_le
    from {{ source('maintenance_interventions', 'lignes_intervention') }}

),

pieces as (

    select
        lignes.id,
        piece.position,
        upper(trim(piece.valeur ->> 'code'))    as code_article,
        piece.valeur ->> 'qte'                  as quantite_saisie,
        lignes._charge_le
    from lignes
    cross join lateral jsonb_array_elements(
        case when pieces_json ~ '^\[\s*\{' then pieces_json::jsonb else '[]'::jsonb end
    ) with ordinality as piece (valeur, position)

)

select
    cast(id as bigint)                                  as id_ligne,
    cast(position as integer)                           as position,
    code_article,
    case when quantite_saisie ~ '^\d+(\.\d+)?$' then cast(quantite_saisie as numeric) end
                                                        as quantite,
    _charge_le
from pieces
where coalesce(code_article, '') not in ('', 'RAS', '-', 'AUCUN', 'R.A.S')
