{#
  Grain : une ligne = un fournisseur de Sage X3, plus une ligne « Inconnu ».
  Dimension partagée : achats, dettes fournisseurs, maintenance (pièces).
#}

with fournisseurs as (

    select * from {{ ref('stg_x3__fournisseurs') }}

)

select
    cast({{ cle_x3('code_fournisseur') }} as text)                      as cle_fournisseur,
    cast(code_fournisseur as text)                                      as code_fournisseur,
    cast(coalesce(nom_fournisseur, '(sans nom) ' || code_fournisseur) as text)
                                                                        as nom_fournisseur,
    cast(intitule_court as text)                                        as intitule_court,
    cast(code_type_fournisseur as integer)                              as code_type_fournisseur,
    cast(groupe as text)                                                as groupe,
    cast(devise as text)                                                as devise,
    cast(est_actif as boolean)                                          as est_actif
from fournisseurs

union all

select
    cast({{ cle_inconnue() }} as text),
    cast(null as text),
    cast('Inconnu' as text),
    cast(null as text),
    cast(null as integer),
    cast(null as text),
    cast(null as text),
    cast(null as boolean)
