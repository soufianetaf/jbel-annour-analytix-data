{#
  Grain : une ligne = un compte de charges d'exploitation (61) × un mois,
  rangé dans sa famille de coût. Définitions : docs/indicateurs/cout_revient.md

  Construit à partir du compte de résultat mensuel (clôtures exclues).
      charge = - montant_resultat  (positif pour une charge)
#}

select
    cast(mois as date)                                  as mois,
    cast(societe as text)                               as societe,
    cast(compte as text)                                as compte,
    cast(intitule as text)                              as intitule,
    cast({{ famille_cout('compte') }} as text)          as famille_cout,
    cast(-montant_resultat as numeric(28, 2))           as charge
from {{ ref('agg_compte_de_resultat_mois') }}
where compte like '61%'
