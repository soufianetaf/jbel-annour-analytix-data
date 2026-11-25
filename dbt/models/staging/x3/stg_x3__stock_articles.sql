{#
  Grain : une ligne = un article sur un site de stockage (état ACTUEL).
  Source : raw_x3.itmmvt (Sage X3, ITMMVT), copiée en liste fermée.

  Nettoyage seulement. La valorisation (stock × CMUP) est faite dans marts.
#}

with source as (

    select * from {{ source('x3', 'itmmvt') }}

)

select
    {{ texte_x3('itmref_0') }}              as article,
    {{ texte_x3('stofcy_0') }}              as site,
    physto_0                                as stock_physique,
    ctlsto_0                                as stock_controle,
    rejsto_0                                as stock_rejete,
    gloall_0                                as quantite_allouee,
    ordsto_0                                as quantite_commandee,
    avc_0                                   as cmup,
    laspurpri_0                             as dernier_prix_achat,
    {{ date_x3('laspurdat_0') }}            as date_dernier_achat,
    lasrcppri_0                             as dernier_prix_reception,
    {{ date_x3('lasrcpdat_0') }}            as date_derniere_reception,
    {{ date_x3('lasissdat_0') }}            as date_derniere_sortie,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
