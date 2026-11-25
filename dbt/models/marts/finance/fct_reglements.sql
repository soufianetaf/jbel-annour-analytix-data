{#
  Grain : une ligne = un règlement saisi dans Sage X3.

  Règle (docs/indicateurs/finance_tresorerie.md) :
      encaissement (sens 2) : montant positif
      décaissement (sens 1) : montant négatif
#}

with reglements as (

    select * from {{ ref('stg_x3__reglements') }}

)

select
    cast(numero_reglement as text)                              as numero_reglement,
    cast(type_reglement as text)                                as type_reglement,
    cast(mode_paiement as text)                                 as mode_paiement,
    cast(case code_sens when 2 then 'encaissement' when 1 then 'décaissement' end as text)
                                                                as sens,
    cast(case code_type_tiers when 1 then 'client' when 2 then 'fournisseur' end as text)
                                                                as type_tiers,
    cast(tiers as text)                                         as code_tiers,
    cast(case when code_type_tiers = 1 then {{ cle_x3('tiers') }} end as text)
                                                                as cle_client,
    cast(banque_entreprise as text)                             as banque_entreprise,
    cast(societe as text)                                       as societe,
    cast(site as text)                                          as site,
    cast(date_comptable as date)                                as date_comptable,
    cast(date_echeance as date)                                 as date_echeance,
    cast(date_valeur as date)                                   as date_valeur,
    cast(code_statut as integer)                                as code_statut,
    cast(devise as text)                                        as devise,
    cast(montant_devise * case code_sens when 2 then 1 else -1 end as numeric(28, 10))
                                                                as montant_devise_signe,
    cast(montant_banque * case code_sens when 2 then 1 else -1 end as numeric(28, 10))
                                                                as montant_banque_signe,
    cast(_charge_le as timestamp with time zone)                as charge_le
from reglements
