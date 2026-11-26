{#
  Grain : une ligne = un défaut contrôlé sur un chariot.
  Source : raw_qualite.controles, sans emplacement, correction ni note
  (texte libre, souvent des essais : « test », « ghg »).

  Le code MC sert aussi, dans un autre formulaire (2 lignes), au contrôle
  « dimensions conformes » : il est renommé DIM d'après le libellé.
  Le nom de colonne accentué de la source a été abîmé à la copie
  (« quantite_endomagé » → quantite_endomagx).
#}

with source as (

    select
        *,
        case
            when libelle = 'قياسات القطع مطابق للمعايير' then 'DIM'
            else upper({{ texte('code') }})
        end as code_corrige
    from {{ source('qualite', 'controles') }}

)

select
    cast(id as bigint)                                  as id_controle,
    cast(composante_id as bigint)                       as id_chariot,
    code_corrige                                        as code_defaut,
    {{ defaut_qualite('code_corrige') }}                as defaut,
    {{ famille_defaut_qualite('code_corrige') }}        as famille_defaut,
    {{ texte('libelle') }}                              as libelle_source,
    {{ texte('status') }}                               as couleur,
    {{ statut_controle_qualite(texte('status')) }}      as statut,
    cast(origine as integer)                            as origine,
    cast(quantite_endomagx as integer)                  as quantite_endommagee,
    cast(quantite_non_acceptable as integer)            as quantite_non_acceptable,
    case {{ texte('defect_acceptable') }}
        when '1' then true when '0' then false
    end                                                 as defaut_acceptable,
    case is_separable when 1 then true when 0 then false end
                                                        as separable,
    created_at                                          as cree_le,
    _charge_le
from source
