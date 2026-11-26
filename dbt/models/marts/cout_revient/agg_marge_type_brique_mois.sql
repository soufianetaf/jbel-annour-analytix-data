{#
  Grain : une ligne = un type de brique (B8, B10, B12…) × un mois.

      tonnes vendues  = unités vendues × poids de l'article / 1 000
      prix par tonne  = CA HT net / tonnes vendues
      marge par tonne = prix par tonne - coût de revient par tonne (12 mois glissants)

  Le coût de revient est celui du SITE, le même pour tous les types : sans
  comptabilité analytique, rien ne permet de répartir les charges par type
  de brique (à valider avec le contrôle de gestion). La marge compare donc
  le prix de chaque type au coût moyen d'une tonne.
#}

with ventes as (

    select
        cast(date_trunc('month', v.date_comptable) as date)     as mois,
        p.type_brique,
        sum(v.quantite_signee)                                  as unites_vendues,
        sum(v.quantite_signee * p.poids_kg) / 1000              as tonnes_vendues,
        sum(v.montant_ht_signe)                                 as ca_ht,
        count(*) filter (where p.poids_kg is null)              as lignes_sans_poids
    from {{ ref('fct_ventes') }} as v
    inner join {{ ref('int_cout_revient__poids_briques') }} as p
        on p.cle_article = v.cle_article
    where v.unite_vente = 'UN'
    group by 1, 2

)

select
    cast(v.mois as date)                                                    as mois,
    cast(v.type_brique as text)                                             as type_brique,
    cast(v.unites_vendues as numeric(18, 2))                                as unites_vendues,
    cast(v.tonnes_vendues as numeric(18, 3))                                as tonnes_vendues,
    cast(v.ca_ht as numeric(28, 2))                                         as ca_ht,
    cast(v.ca_ht / nullif(v.tonnes_vendues, 0) as numeric(18, 2))           as prix_par_tonne,
    cast(c.cout_par_tonne_12_mois as numeric(18, 2))                        as cout_par_tonne,
    cast(v.ca_ht / nullif(v.tonnes_vendues, 0) - c.cout_par_tonne_12_mois as numeric(18, 2))
                                                                            as marge_par_tonne,
    cast(v.ca_ht - v.tonnes_vendues * c.cout_par_tonne_12_mois as numeric(28, 2))
                                                                            as marge,
    cast(v.lignes_sans_poids as integer)                                    as lignes_sans_poids
from ventes as v
left join {{ ref('agg_cout_revient_mois') }} as c
    on c.mois = v.mois
