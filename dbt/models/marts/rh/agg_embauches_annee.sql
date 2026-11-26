{#
  Grain : une ligne = une année d'embauche, pour toute l'entreprise (les
  années à moins de 5 embauches sont regroupées à la copie).
#}

select
    cast(annee as text)         as annee,
    cast(embauches as integer)  as embauches
from {{ ref('stg_rh__embauches_annee') }}
