{#
  Grain : une ligne = un fournisseur.
  Source : raw_x3.bpsupplier (Sage X3, BPSUPPLIER), sans banque.
#}

with source as (

    select * from {{ source('x3', 'bpsupplier') }}

)

select
    {{ texte_x3('bpsnum_0') }}              as code_fournisseur,
    {{ texte_x3('bpsnam_0') }}              as nom_fournisseur,
    {{ texte_x3('bpssho_0') }}              as intitule_court,
    bpstyp_0                                as code_type_fournisseur,
    {{ texte_x3('bpsgru_0') }}              as groupe,
    {{ texte_x3('cur_0') }}                 as devise,
    {{ texte_x3('acccod_0') }}              as code_comptable,
    (enaflg_0 = 2)                          as est_actif,
    _source,
    _charge_le

from source
