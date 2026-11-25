{#
  Grain : une ligne = une échéance (client ou fournisseur), état ACTUEL.

  Définitions : docs/indicateurs/finance_creances.md
      reste_a_payer = (montant - payé) × signe          en MAD
      positif : le tiers nous doit ; négatif : nous lui devons
      créances clients = somme des restes à payer des échéances clients ouvertes

  Le retard et la tranche de la balance âgée sont calculés à la date de
  construction de la table (colonne date_calcul). Pour l'historique, voir
  snapshots.snap_echeances_ouvertes (une photo par jour).
#}

with echeances as (

    select * from {{ ref('stg_x3__echeances') }}

),

calcul as (

    select
        *,
        (montant - paye) * signe                            as reste,
        abs(montant - paye) >= 0.01                         as ouverte,
        {{ date_du_jour() }}                                 as aujourd_hui
    from echeances

)

select
    -- Identifiant
    cast(type_piece as text)                                as type_piece,
    cast(numero_piece as text)                              as numero_piece,
    cast(ligne_piece as integer)                            as ligne_piece,
    cast(numero_echeance as integer)                        as numero_echeance,

    -- Tiers
    cast(case code_type_tiers when 1 then 'client' when 2 then 'fournisseur' end as text)
                                                            as type_tiers,
    cast(tiers as text)                                     as code_tiers,
    -- Clé vers dim_client, seulement pour les clients
    cast(case when code_type_tiers = 1 then {{ cle_x3('tiers') }} end as text)
                                                            as cle_client,
    cast(compte_collectif as text)                          as compte_collectif,
    cast(numero_document_origine as text)                   as numero_document_origine,
    cast(societe as text)                                   as societe,
    cast(site as text)                                      as site,

    -- Échéance
    cast(date_echeance as date)                             as date_echeance,
    cast(mode_paiement as text)                             as mode_paiement,
    cast(devise as text)                                    as devise,

    -- Montants signés en MAD
    cast(montant * signe as numeric(28, 10))                as montant_signe,
    cast(paye * signe as numeric(28, 10))                   as paye_signe,
    cast(reste as numeric(28, 10))                          as reste_a_payer,
    cast(en_cours_paiement as numeric(28, 10))              as en_cours_paiement,

    -- État
    cast(ouverte as boolean)                                as est_ouverte,
    cast(code_lettrage = 2 as boolean)                      as est_lettree,
    cast(niveau_relance as integer)                         as niveau_relance,
    cast(date_paiement as date)                             as date_paiement,

    -- Balance âgée, à la date de calcul
    cast(aujourd_hui as date)                               as date_calcul,
    cast(case when ouverte then greatest(aujourd_hui - date_echeance, 0) end as integer)
                                                            as jours_retard,
    cast({{ tranche_balance_agee('aujourd_hui - date_echeance', 'ouverte') }} as text)
                                                            as tranche_retard,

    cast(_charge_le as timestamp with time zone)            as charge_le

from calcul
