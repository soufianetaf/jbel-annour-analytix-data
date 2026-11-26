{#
  Grain : une ligne = un rapport de contrôle qualité, avec SA date et SON poste.

  Les premiers rapports ont la date et le poste dans l'en-tête
  (rapport_infos) ; ensuite l'application les écrit dans le rapport, et
  108 rapports n'ont plus d'en-tête. Règle : l'en-tête, sinon le rapport,
  sinon la date de création.
#}

select
    r.id_rapport,
    r.statut,
    r.liste_controle,
    coalesce(e.jour, r.jour, cast(r.cree_le as date))   as jour,
    coalesce(e.poste, r.poste)                          as poste
from {{ ref('stg_qualite__rapports') }} as r
left join {{ ref('stg_qualite__entetes') }} as e
    on e.id_entete = r.id_entete
