{#
  Grain : une ligne = une commande client (entête).
  Source : raw_x3.sorder (Sage X3, SORDER), en liste fermée.

  Codes de statut de Sage X3, traduits :
    statut de la commande     1 ouverte, 2 soldée
    statut de livraison       1 non livrée, 2 partiellement livrée, 3 livrée
    statut de facturation     1 non facturée, 2 partiellement facturée, 3 facturée
#}

with source as (

    select * from {{ source('x3', 'sorder') }}

)

select
    {{ texte_x3('sohnum_0') }}                  as numero_commande,
    {{ texte_x3('cpy_0') }}                     as societe,
    {{ texte_x3('salfcy_0') }}                  as site,
    {{ texte_x3('bpcord_0') }}                  as client,
    {{ texte_x3('bpcinv_0') }}                  as client_facture,
    {{ texte_x3('rep_0') }}                     as representant,
    {{ texte_x3('cur_0') }}                     as devise,
    {{ date_x3('orddat_0') }}                   as date_commande,
    {{ date_x3('demdlvdat_0') }}                as date_livraison_demandee,
    {{ date_x3('lasdlvdat_0') }}                as date_derniere_livraison,
    {{ date_x3('lasinvdat_0') }}                as date_derniere_facture,
    case ordsta_0 when 1 then 'ouverte' when 2 then 'soldée' end
                                                as statut_commande,
    case dlvsta_0 when 1 then 'non livrée' when 2 then 'partiellement livrée' when 3 then 'livrée' end
                                                as statut_livraison,
    case invsta_0 when 1 then 'non facturée' when 2 then 'partiellement facturée' when 3 then 'facturée' end
                                                as statut_facturation,
    hldsta_0 = 2                                as est_bloquee,
    ordnot_0                                    as montant_ht,
    ordati_0                                    as montant_ttc,
    linnbr_0                                    as lignes,
    clelinnbr_0                                 as lignes_soldees,
    dlvlinnbr_0                                 as lignes_livrees,
    invlinnbr_0                                 as lignes_facturees,
    {{ horodatage_x3('credattim_0') }}          as cree_le,
    {{ horodatage_x3('upddattim_0') }}          as modifie_le,
    _source,
    _charge_le
from source
where {{ texte_x3('sohnum_0') }} is not null
