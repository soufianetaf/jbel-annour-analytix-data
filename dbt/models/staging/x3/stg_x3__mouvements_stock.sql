{#
  Grain : une ligne = un mouvement de stock d'un article sur un site.
  Source : raw_x3.stojou (Sage X3, STOJOU), copiée en incrémental, sans
  libellé ni champs libres.

  Nettoyage seulement. La quantité est déjà signée dans X3 (+ entrée,
  - sortie) ; le sens de la valeur est vérifié par un test.
#}

with source as (

    select * from {{ source('x3', 'stojou') }}

)

select
    -- Identifiant
    {{ texte_x3('stofcy_0') }}              as site,
    updcod_0                                as code_mise_a_jour,
    {{ texte_x3('itmref_0') }}              as article,
    {{ date_x3('iptdat_0') }}               as date_mouvement,
    mvtseq_0                                as sequence,
    mvtind_0                                as indice,

    -- Nature
    trstyp_0                                as code_type_mouvement,
    {{ texte_x3('trsfam_0') }}              as famille_transaction,
    {{ texte_x3('wrh_0') }}                 as depot,
    {{ texte_x3('loc_0') }}                 as emplacement,
    {{ texte_x3('bprnum_0') }}              as tiers,
    vcrtyp_0                                as code_type_document,
    {{ texte_x3('vcrnum_0') }}              as numero_document,
    vcrlin_0                                as ligne_document,

    -- Quantité (signée dans X3) et valeur
    qtystu_0                                as quantite,
    {{ texte_x3('stu_0') }}                 as unite_stock,
    amtval_0                                as valeur,
    prival_0                                as prix_valorisation,
    {{ texte_x3('sta_0') }}                 as statut_stock,

    -- Sections analytiques (service, centre de coût…)
    {{ texte_x3('cce_0') }}                 as section_1,
    {{ texte_x3('cce_1') }}                 as section_2,
    {{ texte_x3('cce_2') }}                 as section_3,

    {{ date_x3('accdat_0') }}               as date_comptable,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
