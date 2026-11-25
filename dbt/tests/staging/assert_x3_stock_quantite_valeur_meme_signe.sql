{#
  La valeur d'un mouvement de stock a le même signe que sa quantité
  (ou l'une des deux est nulle).

  Pourquoi : les sorties valorisées (consommations par service, coût des
  ventes) additionnent les valeurs. Une sortie de valeur positive serait
  comptée comme une entrée. Vérifié sur 1,2 million de mouvements le
  25/11/2026 : aucune exception.

  Le test échoue s'il renvoie au moins une ligne.
#}

select site, article, date_mouvement, quantite, valeur
from {{ ref('stg_x3__mouvements_stock') }}
where sign(quantite) * sign(valeur) = -1
