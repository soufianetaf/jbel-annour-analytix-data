{#
  Grain : une ligne = un client (fiche client de Sage X3).
  Source : raw_x3.bpcustomer, copiée en liste fermée (sans CIN ni banque).

  Nettoyage seulement. Les doublons de raison sociale (244 noms présents
  plusieurs fois, cahier des charges 5.1) ne sont PAS fusionnés : ce sont
  des codes clients différents dans X3, la fusion est une décision métier.
#}

with source as (

    select * from {{ source('x3', 'bpcustomer') }}

)

select
    {{ texte_x3('bpcnum_0') }}              as code_client,
    {{ texte_x3('bpcnam_0') }}              as nom_client,
    {{ texte_x3('bpcsho_0') }}              as intitule_court,
    {{ texte_x3('bcgcod_0') }}              as categorie_client,
    bpctyp_0                                as code_type_client,
    -- Menu local X3 « Non / Oui » : 1 = non, 2 = oui
    (bpcsta_0 = 2)                          as est_actif,
    {{ texte_x3('cur_0') }}                 as devise,
    {{ texte_x3('rep_0') }}                 as representant,
    {{ texte_x3('rep_1') }}                 as representant_2,
    {{ texte_x3('pte_0') }}                 as condition_paiement,
    {{ texte_x3('tsccod_0') }}              as famille_statistique_1,
    {{ texte_x3('tsccod_1') }}              as famille_statistique_2,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
