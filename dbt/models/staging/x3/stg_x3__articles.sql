{#
  Grain : une ligne = un article (fiche article de Sage X3).
  Source : raw_x3.itmmaster, copiée en liste fermée.

  Nettoyage seulement. Les codes de catégorie et de famille statistique
  sont gardés tels quels ; leurs libellés viendront des tables de
  paramétrage de X3.
#}

with source as (

    select * from {{ source('x3', 'itmmaster') }}

)

select
    {{ texte_x3('itmref_0') }}              as code_article,
    {{ texte_x3('itmdes1_0') }}             as designation,
    {{ texte_x3('itmdes2_0') }}             as designation_2,
    {{ texte_x3('tclcod_0') }}              as categorie_article,
    {{ texte_x3('tsicod_0') }}              as famille_statistique_1,
    {{ texte_x3('tsicod_1') }}              as famille_statistique_2,
    {{ texte_x3('tsicod_2') }}              as famille_statistique_3,
    itmsta_0                                as code_statut,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    {{ texte_x3('sau_0') }}                 as unite_vente,
    saustucoe_0                             as coefficient_vente_stock,
    {{ texte_x3('weu_0') }}                 as unite_poids,
    -- 0 dans X3 = poids non renseigné
    nullif(itmwei_0, 0)                     as poids_unitaire,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
