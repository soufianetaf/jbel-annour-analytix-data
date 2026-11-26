{#
  AVERTISSEMENT (ne bloque pas) : articles qui pèsent à eux seuls plus de
  5 % du stock valorisé de leur site.

  Pourquoi : au 25/11/2026, 10 articles font 535 M MAD sur 599 M MAD de
  stock valorisé au CMUP, presque tous des en-cours de fabrication dont le
  CMUP est aberrant (1,55 M MAD par étagère en séchage, 7,07 M MAD par
  wagon de biscuit). Le stock valorisé n'est présentable qu'une fois ces
  CMUP corrigés dans Sage X3 ; ce test les liste.
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'Contrôle de gestion', 'correction': "Revoir le coût moyen (CMUP) de l'article dans Sage X3."},
) }}

with stock as (

    select site, code_article, valeur_stock,
           sum(valeur_stock) over (partition by site) as valeur_site
    from {{ ref('fct_stock_article') }}
    where valeur_stock > 0

)

select site, code_article, valeur_stock, valeur_site,
       round(100 * valeur_stock / nullif(valeur_site, 0), 1) as part_pct
from stock
where valeur_stock > 0.05 * valeur_site
