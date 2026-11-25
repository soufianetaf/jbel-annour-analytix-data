{#
  Grain : une ligne = un compte du plan comptable.
  Source : raw_x3.gaccount (Sage X3, GACCOUNT).
#}

with source as (

    select * from {{ source('x3', 'gaccount') }}

)

select
    {{ texte_x3('coa_0') }}                 as plan_comptable,
    {{ texte_x3('acc_0') }}                 as compte,
    {{ texte_x3('des_0') }}                 as intitule,
    {{ texte_x3('dessho_0') }}              as intitule_court,
    sac_0                                   as code_collectif,     -- indicateur numérique dans GACCOUNT
    {{ texte_x3('clscod_0') }}              as code_classement,
    -- Menu local X3 « Non / Oui » : 1 = non, 2 = oui
    (enaflg_0 = 2)                          as est_actif,
    _source,
    _charge_le

from source
