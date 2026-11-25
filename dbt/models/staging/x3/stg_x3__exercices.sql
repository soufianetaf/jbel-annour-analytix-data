{#
  Grain : une ligne = un exercice comptable d'une société, dans un registre.
  Source : raw_x3.fiscalyear (Sage X3, FISCALYEAR).
#}

with source as (

    select * from {{ source('x3', 'fiscalyear') }}

)

select
    {{ texte_x3('cpy_0') }}                 as societe,
    ledtyp_0                                as registre,
    fiynum_0                                as numero_exercice,
    {{ texte_x3('des_0') }}                 as intitule,
    {{ date_x3('fiystr_0') }}               as date_debut,
    {{ date_x3('fiyend_0') }}               as date_fin,
    fiysta_0                                as code_statut,
    _source,
    _charge_le

from source
