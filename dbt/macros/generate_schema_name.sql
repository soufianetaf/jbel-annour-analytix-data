{#
  Nom du schéma où dbt crée un modèle.

  Par défaut, dbt colle le schéma du profil et celui du modèle
  (« staging_marts »). Ici, chaque couche va dans SON schéma, tel qu'il
  est écrit dans dbt_project.yml : staging, intermediate, marts. Ce sont
  les schémas créés par infra.postgres.initialiser_entrepot, avec leurs
  droits (l'API ne lit que marts).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
