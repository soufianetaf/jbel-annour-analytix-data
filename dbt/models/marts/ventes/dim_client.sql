{#
  Grain : une ligne = un client de Sage X3, plus une ligne « Inconnu ».

  Dimension partagée : ventes, livraisons, créances clients.
  Historique : non (type 1, valeurs actuelles). Le changement de
  représentant d'un client sera historisé plus tard (snapshot), car il
  change l'analyse des ventes passées (cahier des charges, 8.4 c).
#}

with clients as (

    select * from {{ ref('stg_x3__clients') }}

)

select
    cast({{ cle_x3('code_client') }} as text)       as cle_client,
    cast('x3' as text)                              as source,
    cast(code_client as text)                       as code_client,
    -- Fiche sans raison sociale dans X3 : on affiche le code plutôt qu'un vide
    cast(coalesce(nom_client, '(sans nom) ' || code_client) as text)
                                                    as nom_client,
    cast(intitule_court as text)                    as intitule_court,
    cast(categorie_client as text)                  as categorie_client,
    cast(est_actif as boolean)                      as est_actif,
    cast(representant as text)                      as representant,
    cast(representant_2 as text)                    as representant_2,
    cast(condition_paiement as text)                as condition_paiement,
    cast(famille_statistique_1 as text)             as famille_statistique_1,
    cast(devise as text)                            as devise
from clients

union all

-- Ligne « Inconnu » : une vente sans client reste comptée dans les totaux
select
    cast({{ cle_inconnue() }} as text),
    cast('x3' as text),
    cast(null as text),
    cast('Inconnu' as text),
    cast('Inconnu' as text),
    cast(null as text),
    cast(null as boolean),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as text),
    cast(null as text)
