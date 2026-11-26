{#
  Qualité des données : historique des contrôles (docs/indicateurs/qualite_donnees.md).

  À chaque dbt build / dbt test, on-run-end enregistre dans
  qualite_donnees.resultats_tests le résultat :
  - de chaque test qui a un service responsable (meta.service : les
    avertissements à corriger dans les sources), même s'il passe, pour
    suivre les corrections ;
  - de tout test en échec ou en avertissement, même sans service.
  Les lignes en erreur elles-mêmes sont gardées par dbt (store_failures)
  dans une table par test du même schéma.
  Aucune donnée n'est écrite dans les sources : seulement dans l'entrepôt.
#}

{% macro creer_historique_qualite() %}
    create schema if not exists qualite_donnees;
    create table if not exists qualite_donnees.resultats_tests (
        controle_le         timestamp with time zone not null,
        invocation_id       text not null,
        test                text not null,
        modele              text,
        severite            text,
        statut              text not null,
        lignes_en_erreur    bigint,
        service             text,
        correction          text,
        table_lignes        text,
        primary key (invocation_id, test)
    );
{% endmacro %}


{% macro _texte_sql(valeur) -%}
    {%- if valeur is none -%}null{%- else -%}'{{ (valeur | string) | replace("'", "''") }}'{%- endif -%}
{%- endmacro %}


{% macro enregistrer_resultats_tests(results) %}
    {% if not execute %}{{ return('') }}{% endif %}
    {% set lignes = [] %}
    {% for r in results %}
        {% if r.node.resource_type == 'test' %}
            {% set meta = r.node.config.meta or {} %}
            {% set statut = r.status | string %}
            {% if meta.get('service') or statut in ['fail', 'warn', 'error'] %}
                {% set modele = r.node.attached_node or (r.node.depends_on.nodes | first) %}
                {% set table_lignes = r.node.relation_name if r.node.config.store_failures else none %}
                {% do lignes.append(
                    "(" ~ _texte_sql(run_started_at.isoformat()) ~ ", "
                    ~ _texte_sql(invocation_id) ~ ", "
                    ~ _texte_sql(r.node.name) ~ ", "
                    ~ _texte_sql(modele.split('.')[-1] if modele else none) ~ ", "
                    ~ _texte_sql(r.node.config.severity) ~ ", "
                    ~ _texte_sql(statut) ~ ", "
                    ~ (r.failures if r.failures is not none else 'null') ~ ", "
                    ~ _texte_sql(meta.get('service')) ~ ", "
                    ~ _texte_sql(meta.get('correction')) ~ ", "
                    ~ _texte_sql(table_lignes) ~ ")"
                ) %}
            {% endif %}
        {% endif %}
    {% endfor %}
    {% if lignes %}
        {% do run_query(
            "insert into qualite_donnees.resultats_tests "
            ~ "(controle_le, invocation_id, test, modele, severite, statut, lignes_en_erreur, service, correction, table_lignes) values "
            ~ (lignes | join(", "))
            ~ " on conflict (invocation_id, test) do nothing"
        ) %}
        {{ log("Qualité des données : " ~ (lignes | length) ~ " résultats de tests enregistrés", info=true) }}
    {% endif %}
    {{ return('') }}
{% endmacro %}
