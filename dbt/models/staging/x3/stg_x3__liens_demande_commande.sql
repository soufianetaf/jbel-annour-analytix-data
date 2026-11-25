{#
  Grain : une ligne = un lien entre une ligne de demande d'achat et une
  ligne de commande. Source : raw_x3.prequiso (Sage X3, PREQUISO).
  C'est le SEUL lien DA → commande dans Sage X3 : les lignes de commande
  n'ont pas de référence à la DA (champs d'origine vides).
#}

with source as (

    select * from {{ source('x3', 'prequiso') }}

)

select
    {{ texte_x3('pshnum_0') }}              as numero_demande,
    psdlin_0                                as ligne_demande,
    {{ texte_x3('pohnum_0') }}              as numero_commande,
    poplin_0                                as ligne_commande,
    poqseq_0                                as sequence_commande,
    qtystu_0                                as quantite,
    _source,
    _charge_le

from source
