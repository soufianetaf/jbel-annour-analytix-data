{#
  Les charges rangées par famille de coût redonnent, mois par mois, toutes
  les charges d'exploitation (61) du compte de résultat : aucun compte n'est
  perdu ni compté deux fois par la macro famille_cout.
#}

with familles as (

    select mois, sum(charge) as charges
    from {{ ref('fct_charges_production_mois') }}
    group by mois

),

cpc as (

    select mois, -sum(montant_resultat) as charges
    from {{ ref('agg_compte_de_resultat_mois') }}
    where compte like '61%'
    group by mois

)

select coalesce(f.mois, c.mois) as mois, f.charges as familles, c.charges as cpc
from familles as f
full outer join cpc as c
    on c.mois = f.mois
where abs(coalesce(f.charges, 0) - coalesce(c.charges, 0)) > 0.01
