{#
  Grain : une ligne = une demande d'achat (entête).
  Source : raw_x3.prequis (Sage X3, PREQUIS). Nettoyage seulement.
  La section analytique (service demandeur) est vide sur toutes les DA au
  25/11/2026 : le service viendra de l'application espace_magasin.
#}

with source as (

    select * from {{ source('x3', 'prequis') }}

)

select
    {{ texte_x3('pshnum_0') }}              as numero_demande,
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('pshfcy_0') }}              as site,
    {{ date_x3('prqdat_0') }}               as date_demande,
    {{ texte_x3('cce_0') }}                 as section,
    {{ texte_x3('requsr_0') }}              as code_demandeur,
    appflg_0                                as code_signature,
    ordflg_0                                as code_commande,
    cleflg_0                                as code_solde,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    _source,
    _charge_le

from source
where {{ texte_x3('pshnum_0') }} is not null
