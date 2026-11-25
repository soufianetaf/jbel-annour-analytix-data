{#
  Grain : une ligne = une ligne de demande d'achat de l'application
  espace_magasin, avec le département et la décision de son entête.

  Depuis 2025, les demandes d'achat ne sont plus saisies dans Sage X3
  (docs/indicateurs/achats_circuit.md) : c'est ici que se lisent le
  département demandeur et le délai de validation.
  numero_da_x3 relie la demande à Sage X3 quand elle y a été reprise.
#}

with lignes as (

    select * from {{ ref('stg_espace_magasin__lignes_demande_achat') }}

),

entetes as (

    select * from {{ ref('stg_espace_magasin__demandes_achat') }}

)

select
    cast(l.id_ligne as bigint)                                  as id_ligne,
    cast(l.id_demande as bigint)                                as id_demande,
    cast(e.numero as text)                                      as numero_demande,
    cast(coalesce(l.numero_da_x3, e.numero_da_x3) as text)      as numero_da_x3,
    cast(e.date_demande as date)                                as date_demande,
    cast(e.departement as text)                                 as departement,
    cast(e.service as text)                                     as service,
    cast(coalesce(l.famille, e.famille) as text)                as famille,
    cast({{ cle_x3('coalesce(l.article_valide, l.article)') }} as text)
                                                                as cle_article,
    cast(coalesce(l.article_valide, l.article) as text)         as code_article,
    cast(l.designation as text)                                 as designation,
    cast(l.quantite as numeric(28, 10))                         as quantite_demandee,
    cast(l.quantite_validee as numeric(28, 10))                 as quantite_validee,
    cast(l.decision as text)                                    as decision_ligne,
    cast(e.decision as text)                                    as decision_demande,
    cast(e.code_depassement_budget = 1 as boolean)              as a_depassement_budget,
    cast(e.cree_le as timestamp)                                as cree_le,
    cast(e.valide_le as timestamp)                              as valide_le,
    cast(extract(epoch from e.valide_le - e.cree_le) / 86400 as numeric(18, 2))
                                                                as jours_validation,
    cast(l._charge_le as timestamp with time zone)              as charge_le
from lignes as l
left join entetes as e
    on e.id_demande = l.id_demande
