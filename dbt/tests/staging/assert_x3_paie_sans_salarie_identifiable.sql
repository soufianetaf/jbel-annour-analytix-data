{#
  Aucune ligne d'écriture sur un compte de personnel ne porte de tiers.

  Pourquoi : règle d'or n° 2, aucun salaire individuel dans l'entrepôt.
  Aujourd'hui la paie est comptabilisée PAR COMPTE (contrôle du 25/11/2026) :
  les écritures ne contiennent pas de salaire individuel. Si un jour la paie
  était comptabilisée salarié par salarié (un tiers par salarié), ce test
  échouerait et bloquerait la chaîne, avant que les données ne soient
  exposées.

  Comptes contrôlés (plan comptable marocain) :
    617  charges de personnel
    443  rémunérations dues au personnel
    3431 avances et acomptes au personnel

  Le test échoue s'il renvoie au moins une ligne (seuls les comptages
  sont renvoyés, jamais un montant).
#}

select compte, count(*) as lignes_avec_tiers
from {{ ref('stg_x3__lignes_ecriture') }}
where (compte like '617%' or compte like '443%' or compte like '3431%')
  and tiers is not null
group by compte
