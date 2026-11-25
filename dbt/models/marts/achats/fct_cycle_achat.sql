{#
  Grain : une ligne = une ligne de commande fournisseur (× échéance de
  livraison), avec la date de chaque étape du circuit d'achat.

  Définitions : docs/indicateurs/achats_circuit.md
  - demande d'achat : par la table de lien PREQUISO (la plus ancienne si
    plusieurs DA alimentent la même ligne) ; vide pour un achat direct ;
  - réception et facture : la PREMIÈRE réception et la PREMIÈRE facture
    rattachées à la ligne de commande.
#}

with lignes as (

    select * from {{ ref('stg_x3__lignes_commande_achat') }}

),

commandes as (

    select * from {{ ref('stg_x3__commandes_achat') }}

),

demandes as (

    select
        lien.numero_commande,
        lien.ligne_commande,
        lien.sequence_commande,
        min(da.date_demande)                as date_demande,
        min(lien.numero_demande)            as numero_demande,
        count(distinct lien.numero_demande) as nombre_demandes
    from {{ ref('stg_x3__liens_demande_commande') }} as lien
    inner join {{ ref('stg_x3__demandes_achat') }} as da
        on da.numero_demande = lien.numero_demande
    group by 1, 2, 3

),

receptions as (

    select
        numero_commande,
        ligne_commande,
        sequence_commande,
        min(date_reception)     as date_premiere_reception,
        sum(quantite)           as quantite_recue_lignes,
        count(*)                as nombre_receptions
    from {{ ref('stg_x3__lignes_reception') }}
    where numero_commande is not null
    group by 1, 2, 3

),

factures as (

    select
        numero_commande,
        ligne_commande,
        sequence_commande,
        min(date_comptable)     as date_premiere_facture
    from {{ ref('stg_x3__lignes_facture_fournisseur') }}
    where numero_commande is not null
    group by 1, 2, 3

)

select
    -- Identifiant
    cast(l.numero_commande as text)                                 as numero_commande,
    cast(l.ligne as integer)                                        as ligne,
    cast(l.sequence as integer)                                     as sequence,

    -- Rattachement
    cast(l.site as text)                                            as site,
    cast({{ cle_x3('l.fournisseur') }} as text)                     as cle_fournisseur,
    cast({{ cle_x3('l.article') }} as text)                         as cle_article,
    cast(l.fournisseur as text)                                     as code_fournisseur,
    cast(l.article as text)                                         as code_article,
    cast(c.acheteur as text)                                        as acheteur,
    cast(d.numero_demande as text)                                  as numero_demande,
    cast(coalesce(d.nombre_demandes, 0) as integer)                 as nombre_demandes,
    cast(d.numero_demande is null as boolean)                       as est_achat_direct,

    -- Dates des étapes
    cast(d.date_demande as date)                                    as date_demande,
    cast(l.date_commande as date)                                   as date_commande,
    cast(l.date_reception_prevue as date)                           as date_reception_prevue,
    cast(r.date_premiere_reception as date)                         as date_premiere_reception,
    cast(f.date_premiere_facture as date)                           as date_premiere_facture,

    -- Délais en jours
    cast(l.date_commande - d.date_demande as integer)               as jours_demande_commande,
    cast(r.date_premiere_reception - l.date_commande as integer)    as jours_commande_reception,
    cast(f.date_premiere_facture - r.date_premiere_reception as integer)
                                                                    as jours_reception_facture,
    cast(greatest(r.date_premiere_reception - l.date_reception_prevue, 0) as integer)
                                                                    as jours_retard_livraison,

    -- Quantités (unité de stock) et montant
    cast(l.quantite_commandee as numeric(28, 10))                   as quantite_commandee,
    cast(l.quantite_recue as numeric(28, 10))                       as quantite_recue,
    cast(l.quantite_facturee as numeric(28, 10))                    as quantite_facturee,
    cast(l.unite_stock as text)                                     as unite_stock,
    cast(case when l.quantite_commandee > 0
              then l.quantite_recue / l.quantite_commandee end as numeric(28, 10))
                                                                    as taux_service,
    cast(l.montant_ht as numeric(28, 10))                           as montant_ht,
    cast(l.devise as text)                                          as devise,
    cast(l.code_solde = 2 as boolean)                               as est_soldee,
    cast(l._charge_le as timestamp with time zone)                  as charge_le

from lignes as l
left join commandes as c
    on c.numero_commande = l.numero_commande
left join demandes as d
    on (d.numero_commande, d.ligne_commande, d.sequence_commande)
     = (l.numero_commande, l.ligne, l.sequence)
left join receptions as r
    on (r.numero_commande, r.ligne_commande, r.sequence_commande)
     = (l.numero_commande, l.ligne, l.sequence)
left join factures as f
    on (f.numero_commande, f.ligne_commande, f.sequence_commande)
     = (l.numero_commande, l.ligne, l.sequence)
