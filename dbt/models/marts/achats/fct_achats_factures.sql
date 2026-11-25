{#
  Grain : une ligne = une ligne de facture ou d'avoir fournisseur.

  Dépense d'achat (docs/indicateurs/achats_circuit.md) :
  - montant signé : un avoir (signe -1 de l'entête) est négatif ;
  - en MAD : le montant de la ligne est converti avec le taux de la
    facture (montant HT en MAD / montant HT en devise de l'entête), pour
    les 191 factures en EUR.
#}

with lignes as (

    select * from {{ ref('stg_x3__lignes_facture_fournisseur') }}

),

entetes as (

    select
        *,
        case when montant_ht <> 0 then montant_ht_mad / montant_ht else 1 end as taux_mad
    from {{ ref('stg_x3__factures_fournisseurs') }}

)

select
    -- Identifiant
    cast(l.numero_facture as text)                                  as numero_facture,
    cast(l.ligne as integer)                                        as ligne,

    -- Nature
    cast(case when e.signe = -1 then 'avoir' else 'facture' end as text) as type_document,
    cast(e.type_facture as text)                                    as type_facture,
    cast(e.signe as integer)                                        as signe,

    -- Rattachement
    cast(l.date_comptable as date)                                  as date_comptable,
    cast(l.site as text)                                            as site,
    cast({{ cle_x3('l.fournisseur') }} as text)                     as cle_fournisseur,
    cast({{ cle_x3('l.article') }} as text)                         as cle_article,
    cast(l.fournisseur as text)                                     as code_fournisseur,
    cast(l.article as text)                                         as code_article,
    cast(l.numero_commande as text)                                 as numero_commande,
    cast(l.numero_reception as text)                                as numero_reception,

    -- Quantité, prix et montants
    cast(l.quantite * e.signe as numeric(28, 10))                   as quantite_signee,
    cast(l.unite_stock as text)                                     as unite_stock,
    cast(l.prix_net as numeric(28, 10))                             as prix_net,
    cast(l.devise as text)                                          as devise,
    cast(l.montant_ht * e.signe as numeric(28, 10))                 as montant_ht_signe,
    cast(l.montant_ht * e.taux_mad * e.signe as numeric(28, 10))    as montant_ht_mad_signe,
    cast(l._charge_le as timestamp with time zone)                  as charge_le

from lignes as l
inner join entetes as e
    on e.numero_facture = l.numero_facture
