{#
  Chaque dimension a UNE et UNE SEULE ligne « Inconnu », avec la clé
  inconnue (macro cle_inconnue).

  Pourquoi : une vente dont le client ou l'article est absent pointe vers
  cette ligne. S'il n'y en avait aucune, la vente disparaîtrait des
  totaux par client ; s'il y en avait deux, elle serait comptée deux fois.

  Le test échoue s'il renvoie au moins une ligne.
#}

with comptes as (

    select 'dim_client' as dimension, count(*) as lignes_inconnues
    from {{ ref('dim_client') }}
    where cle_client = {{ cle_inconnue() }}

    union all

    select 'dim_article', count(*)
    from {{ ref('dim_article') }}
    where cle_article = {{ cle_inconnue() }}

)

select dimension, lignes_inconnues
from comptes
where lignes_inconnues <> 1
