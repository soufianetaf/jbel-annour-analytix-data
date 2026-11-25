{#
  Grain : une ligne = une demande de dépassement de budget sur un article.

  quantite_depassement = quantité demandée - quantité budgétée.
  Chaque avis du circuit (magasin, méthodes, DGA, gestion, amélioration,
  logistique, PDG) reste visible ; est_approuve_pdg indique la décision
  finale du PDG (à confirmer, docs/indicateurs/magasin_sorties_da.md).
#}

with depassements as (

    select * from {{ ref('stg_espace_magasin__depassements') }}

)

select
    cast(id_depassement as integer)                             as id_depassement,
    cast(numero_depassement as text)                            as numero_depassement,
    cast(numero_da as text)                                     as numero_da,
    cast(numero_budget as text)                                 as numero_budget,
    cast(cree_le as date)                                       as date_demande,
    cast({{ cle_x3('article') }} as text)                       as cle_article,
    cast(article as text)                                       as code_article,
    cast(designation as text)                                   as designation,
    cast(famille as text)                                       as famille,
    cast(quantite_demandee as numeric(28, 10))                  as quantite_demandee,
    cast(quantite_budget as numeric(28, 10))                    as quantite_budget,
    cast(quantite_demandee - quantite_budget as numeric(28, 10)) as quantite_depassement,
    cast(statut as text)                                        as statut,
    cast(avis_magasin as text)                                  as avis_magasin,
    cast(avis_methodes as text)                                 as avis_methodes,
    cast(avis_dga as text)                                      as avis_dga,
    cast(avis_gestion as text)                                  as avis_gestion,
    cast(avis_amelioration as text)                             as avis_amelioration,
    cast(avis_logistique as text)                               as avis_logistique,
    cast(avis_pdg as text)                                      as avis_pdg,
    cast(coalesce(avis_pdg = 'APPROUVE', false) as boolean)     as est_approuve_pdg,
    cast(approuve_le as timestamp)                              as approuve_le,
    cast(_charge_le as timestamp with time zone)                as charge_le
from depassements
