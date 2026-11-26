{#
  Grain : une ligne = le prix d'une ligne de commande client.
  Source : raw_x3.sorderp, sans le coût de revient (CPRPRI, faux).
#}

with source as (

    select * from {{ source('x3', 'sorderp') }}

)

select
    {{ texte_x3('sohnum_0') }}                  as numero_commande,
    soplin_0                                    as ligne,
    sopseq_0                                    as sequence,
    {{ texte_x3('itmref_0') }}                  as article,
    {{ texte_x3('rep1_0') }}                    as representant,
    gropri_0                                    as prix_brut,
    netprinot_0                                 as prix_net_ht,
    {{ texte_x3('sau_0') }}                     as unite_vente,
    focflg_0 = 2                                as est_gratuit,
    _source,
    _charge_le
from source
where {{ texte_x3('sohnum_0') }} is not null
