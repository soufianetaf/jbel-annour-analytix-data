{#
  Grain : une ligne = un jour. Définitions : docs/indicateurs/energie.md

  Deux sources, mises côte à côte :
  - les AUTOMATES (font foi quand ils existent, depuis le 26/11/2025) :
    tonnes cuites (four), coke consommé et ratio de cuisson (four),
    électricité du site (transformateurs) ;
  - le RAPPORT SAISI dans l'application de production (mars 2025 - octobre
    2026) : électricité, fuel du four, coke micronisé, propane, charbon,
    grignons, production. Saisi en texte, parfois deux fois par jour : le
    dernier rapport du jour est retenu (le plus grand identifiant).

  Les ratios par tonne d'une source utilisent les tonnes de la même source.
  Unités saisies à confirmer (fuel et coke en tonnes, propane en bouteilles ?).
#}

with rapports as (

    select
        *,
        count(*) over (partition by jour)                               as rapports_du_jour
    from {{ ref('stg_production__consommations') }}
    where jour is not null

),

dernier as (

    select distinct on (jour) *
    from rapports
    order by jour, id_rapport desc

),

rapport_du_jour as (

    -- Saisies impossibles écartées (production à 956 297 t, fuel négatif…) :
    -- une quantité négative ; une production hors de 1 à 3 000 t par jour ;
    -- plus de 100 kg de coke, 0,1 t de fuel ou 0,1 de propane par tonne
    select
        jour,
        rapports_du_jour,
        case when production_tonnes between 1 and 3000 then production_tonnes end  as production_tonnes,
        case when electricite >= 0 then electricite end                             as electricite,
        case when fuel_four >= 0 then fuel_four end                                 as fuel_four,
        case when coke_micronise >= 0 then coke_micronise end                       as coke_micronise,
        case when coke_four >= 0 then coke_four end                                 as coke_four,
        case when propane >= 0 then propane end                                     as propane,
        case when charbon >= 0 then charbon end                                     as charbon,
        case when grignons >= 0 then grignons end                                   as grignons
    from dernier

),

ratios as (

    select
        *,
        fuel_four / nullif(production_tonnes, 0)                                    as fuel_par_tonne,
        coke_micronise * 1000 / nullif(production_tonnes, 0)                        as coke_kg_par_tonne,
        propane / nullif(production_tonnes, 0)                                      as propane_par_tonne
    from rapport_du_jour

),

jours as (

    select jour from dernier
    union
    select jour from {{ ref('agg_energie_jour') }}

)

select
    cast(j.jour as date)                                                as jour,

    -- Automates
    cast(e.tonnes_cuites as numeric(18, 3))                             as tonnes_cuites,
    cast(e.kwh_site as numeric(18, 3))                                  as kwh_site,
    cast(e.coke_consomme_tonnes as numeric(12, 3))                      as coke_automate_tonnes,
    cast(e.coke_kg_par_tonne as numeric(12, 3))                         as coke_automate_kg_par_tonne,

    -- Rapport saisi
    cast(r.production_tonnes as numeric(18, 3))                         as production_saisie_tonnes,
    cast(r.electricite as numeric(18, 3))                               as electricite_saisie_kwh,
    cast(r.fuel_four as numeric(12, 3))                                 as fuel_four_saisi,
    cast(r.coke_micronise as numeric(12, 3))                            as coke_micronise_saisi,
    cast(r.coke_four as numeric(12, 3))                                 as coke_four_saisi,
    cast(r.propane as numeric(12, 3))                                   as propane_saisi,
    cast(r.charbon as numeric(12, 3))                                   as charbon_saisi,
    cast(r.grignons as numeric(12, 3))                                  as grignons_saisis,
    cast(r.rapports_du_jour as integer)                                 as rapports_du_jour,

    -- Par tonne, chaque source avec ses propres tonnes
    cast(case when r.fuel_par_tonne <= 0.1 then r.fuel_par_tonne end as numeric(12, 5))
                                                                        as fuel_four_par_tonne,
    cast(case when r.coke_kg_par_tonne <= 100 then r.coke_kg_par_tonne end as numeric(12, 3))
                                                                        as coke_micronise_kg_par_tonne,
    cast(case when r.propane_par_tonne <= 0.1 then r.propane_par_tonne end as numeric(12, 5))
                                                                        as propane_par_tonne,

    -- Contrôle : rapport saisi / automate (1 = identiques)
    cast(r.electricite / nullif(e.kwh_site, 0) as numeric(8, 4))        as ratio_electricite_saisie_compteur,
    cast(r.production_tonnes / nullif(e.tonnes_cuites, 0) as numeric(8, 4))
                                                                        as ratio_production_saisie_four
from jours as j
left join ratios as r
    on r.jour = j.jour
left join {{ ref('agg_energie_jour') }} as e
    on e.jour = j.jour
