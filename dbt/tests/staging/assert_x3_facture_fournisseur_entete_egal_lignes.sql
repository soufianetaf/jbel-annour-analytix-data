{#
  AVERTISSEMENT (ne bloque pas) : factures fournisseurs dont le montant HT
  de l'entête ne correspond pas au total de leurs lignes, dans Sage X3.

  Pourquoi : au 25/11/2026, 22 factures sont concernées, par exemple
  FF171119 (600 000 MAD en entête, 3 000 MAD de lignes) ou FF174477
  (515 311 MAD / 3 346 MAD). La comptabilité est passée sur l'entête, les
  analyses par article partent des lignes : les deux divergent pour ces
  factures. Ce test les liste pour la comptabilité.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Comptabilité fournisseurs', 'correction': "Faire concorder le total de l'en-tête et les lignes de la facture dans Sage X3."},
) }}

with lignes as (

    select numero_facture, sum(montant_ht) as montant_ht_lignes
    from {{ ref('stg_x3__lignes_facture_fournisseur') }}
    group by numero_facture

)

select
    f.numero_facture,
    f.type_facture,
    f.date_comptable,
    f.montant_ht                        as montant_ht_entete,
    coalesce(l.montant_ht_lignes, 0)    as montant_ht_lignes
from {{ ref('stg_x3__factures_fournisseurs') }} as f
left join lignes as l using (numero_facture)
where abs(f.montant_ht - coalesce(l.montant_ht_lignes, 0)) >= 0.01
