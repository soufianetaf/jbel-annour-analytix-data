{#
  Grain : une ligne = une pièce comptable (entête d'écriture).
  Source : raw_x3.gaccentry (Sage X3, GACCENTRY), copiée en incrémental.

  Nettoyage seulement. La catégorie (réelle / autre) et le statut
  (provisoire / définitive) servent à filtrer dans marts.
#}

with source as (

    select * from {{ source('x3', 'gaccentry') }}

)

select
    {{ texte_x3('typ_0') }}                 as type_piece,
    {{ texte_x3('num_0') }}                 as numero_piece,
    {{ texte_x3('cpy_0') }}                 as societe,
    {{ texte_x3('fcy_0') }}                 as site,
    {{ texte_x3('jou_0') }}                 as journal,
    fiy_0                                   as numero_exercice,
    per_0                                   as periode,
    {{ date_x3('accdat_0') }}               as date_comptable,
    cat_0                                   as code_categorie,     -- 1 réelle
    sta_0                                   as code_statut,        -- 1 provisoire, 2 définitive
    {{ texte_x3('cur_0') }}                 as devise,
    orimod_0                                as code_module_origine,
    rvs_0                                   as code_extourne,
    {{ texte_x3('bprvcr_0') }}              as reference_tiers,
    {{ horodatage_x3('credattim_0') }}      as cree_le,
    {{ horodatage_x3('upddattim_0') }}      as modifie_le,
    _source,
    _charge_le

from source
where {{ texte_x3('num_0') }} is not null
