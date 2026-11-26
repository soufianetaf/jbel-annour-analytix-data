{#
  BLOQUANT : aucune table RH de l'entrepôt ne nomme un groupe de moins de
  5 personnes (cahier des charges : aucune donnée RH individuelle).

  La copie (ingestion.usine_rh) fusionne déjà ces groupes ; ce test vérifie
  qu'aucun modèle ne les recrée, par exemple en découpant plus finement.
  Seuls des comptages sont renvoyés.
#}

select 'effectifs_rh' as table_rh, service as groupe, effectif_rh as personnes
from {{ ref('fct_effectifs_service') }}
where effectif_rh < 5 and service <> {{ groupe_rh_masque() }}

union all

select 'effectifs_pointeuse', service, effectif_pointeuse
from {{ ref('fct_effectifs_service') }}
where effectif_pointeuse < 5 and service <> {{ groupe_rh_masque() }}

union all

select 'presence', service || ' ' || jour, personnes_presentes
from {{ ref('agg_presence_service_jour') }}
where personnes_presentes < 5 and service <> {{ groupe_rh_masque() }}

union all

select 'embauches', annee, embauches
from {{ ref('agg_embauches_annee') }}
where embauches < 5 and annee <> {{ groupe_rh_masque() }}
