{#
  AVERTISSEMENT (ne bloque pas) : commandes soldées (fermées) sans aucune
  livraison, de moins d'un an. Annulées, ou saisies en double : l'ADV dit
  laquelle, et supprime les doublons dans Sage X3 (cahier des charges :
  commandes clients jamais livrées).
#}

{{ config(
    severity='warn',
    store_failures=true,
    meta={'service': 'ADV', 'correction': "Vérifier la commande soldée sans livraison dans Sage X3 : annulation ou doublon."},
) }}

select numero_commande, code_client, date_commande, montant_ht
from {{ ref('fct_commandes') }}
where soldee_sans_livraison
  and date_commande >= current_date - 365
