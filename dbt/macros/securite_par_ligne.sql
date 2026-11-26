{#
  Sécurité par ligne (cahier des charges : les droits sont appliqués aussi
  dans PostgreSQL, pas seulement dans l'écran ni seulement dans l'API).

  Appliquée en post-hook aux tables qui ont un représentant (ventes,
  livraisons, commandes), à chaque reconstruction par dbt.

  Pour le compte de l'API (var « role_api ») :
  - périmètre « * » : toutes les lignes (direction, commercial, finance) ;
  - périmètre = un code représentant : seulement ses lignes ;
  - périmètre NON DÉCLARÉ ou vide : AUCUNE ligne. Si l'API oubliait un jour
    de déclarer le périmètre, un représentant ne verrait rien plutôt que tout.
  L'API déclare le périmètre avant chaque lecture (api/base.py), pour la
  seule transaction.

  Les autres lecteurs (groupe de lecture de marts, pour Power BI) voient
  toutes les lignes : la sécurité par ligne de Power BI se règle dans Power
  BI (rôles), à l'étape Power BI. Le propriétaire (dbt) n'est jamais filtré.
#}

{% macro securite_par_ligne(colonne='representant') -%}
    alter table {{ this }} enable row level security;
    drop policy if exists perimetre_api on {{ this }};
    create policy perimetre_api on {{ this }} for select using (
        current_user <> '{{ var("role_api") }}'
        or current_setting('analytix.perimetre', true) = '*'
        or (
            {{ colonne }} is not null
            and {{ colonne }} = nullif(current_setting('analytix.perimetre', true), '')
        )
    )
{%- endmacro %}
