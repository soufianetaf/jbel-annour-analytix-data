{#
  Grain : une ligne = une ligne de facture ou d'avoir (pro forma exclues).

  Définition du CA net : docs/indicateurs/ventes_ca_net.md
      CA net = somme de montant_ht_signe

  Règles métier appliquées ici (et seulement ici) :
  1. Les pro forma (PRF) sont exclues : sans valeur comptable.
  2. Les montants et quantités sont SIGNÉS : un avoir (signe -1) est
     négatif, il se déduit du CA quand on additionne.
  3. La date de rattachement est la date comptable de l'entête.

  Les codes (client, article) restent à côté des clés, pour qu'une ligne
  se lise sans jointure et se retrouve dans Sage X3.
#}

with lignes as (

    select * from {{ ref('stg_x3__lignes_facture') }}

),

entetes as (

    select * from {{ ref('stg_x3__factures') }}
    where type_facture <> 'PRF'  -- règle 1

)

select
    -- Identifiant de la ligne (clé naturelle)
    cast(l.numero_facture as text)                          as numero_facture,
    cast(l.numero_ligne as integer)                         as numero_ligne,

    -- Nature du document
    cast(case when e.signe = -1 then 'avoir' else 'facture' end as text)
                                                            as type_document,
    cast(e.type_facture as text)                            as type_facture,
    cast(e.signe as integer)                                as signe,

    -- Clés vers les dimensions
    cast(e.date_comptable as date)                          as date_comptable,  -- règle 3
    cast({{ cle_x3('e.client') }} as text)                  as cle_client,
    cast({{ cle_x3('l.article') }} as text)                 as cle_article,

    -- Codes lisibles (dimensions dégénérées)
    cast(e.client as text)                                  as code_client,
    cast(l.article as text)                                 as code_article,
    cast(l.representant as text)                            as representant,
    cast(e.societe as text)                                 as societe,
    cast(e.site as text)                                    as site,
    cast(l.numero_commande as text)                         as numero_commande,
    cast(l.numero_livraison as text)                        as numero_livraison,
    cast(l.date_facture as date)                            as date_facture,

    -- Mesures signées (règle 2)
    cast(l.quantite * e.signe as numeric(28, 10))           as quantite_signee,
    cast(l.unite_vente as text)                             as unite_vente,
    cast(l.prix_net as numeric(28, 10))                     as prix_net,
    cast(l.montant_ht * e.signe as numeric(28, 10))         as montant_ht_signe,
    cast(l.montant_ttc * e.signe as numeric(28, 10))        as montant_ttc_signe,

    -- Traçabilité
    cast(l._charge_le as timestamp with time zone)          as charge_le

from lignes as l
inner join entetes as e
    on e.numero_facture = l.numero_facture
