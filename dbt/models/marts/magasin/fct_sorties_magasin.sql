{#
  Grain : une ligne = une demande de sortie d'un article du magasin.

  Une sortie est VALIDÉE quand elle est traitée (DONE) et approuvée
  (APPROVED) : docs/indicateurs/magasin_sorties_da.md. Les sorties
  rejetées ou en attente restent dans la table, marquées.
  Les articles sont les codes de Sage X3 : la clé article est la même que
  dans les ventes, les achats et le stock.
#}

with sorties as (

    select * from {{ ref('stg_magasin__sorties') }}

)

select
    cast(id_sortie as integer)                                  as id_sortie,
    cast(cree_le as date)                                       as date_demande,
    cast({{ cle_x3('article') }} as text)                       as cle_article,
    cast(article as text)                                       as code_article,
    cast(designation as text)                                   as designation,
    cast(service as text)                                       as service,
    cast(service_concerne as text)                              as service_concerne,
    cast(affectation_1 as text)                                 as affectation_1,
    cast(affectation_2 as text)                                 as affectation_2,
    cast(quantite as numeric(28, 10))                           as quantite,
    cast(decision as text)                                      as decision,
    cast(statut as text)                                        as statut,
    cast(statut = 'DONE' and decision = 'APPROVED' as boolean)  as est_validee,
    cast(valide_le as timestamp)                                as valide_le,
    cast(extract(epoch from valide_le - cree_le) / 3600 as numeric(18, 2))
                                                                as heures_validation,
    cast(_charge_le as timestamp with time zone)                as charge_le
from sorties
