{#
  Grain : une ligne = un relevé d'un compteur électrique.
  Sources : les 13 tables de raw_electrique_data, une par compteur, réunies.

  Nettoyage seulement :
  - le nom du compteur est ajouté (entree, transfo1… éclairage) ;
  - « Tansion » (orthographe de la source) devient « tension » ;
  - un cos φ hors de 0 à 1 est une erreur de mesure : il devient vide
    (colonne cos_phi_valide pour le compter).
#}

{% set compteurs = [
    ('entree', 'général'), ('transfo1', 'général'), ('transfo2', 'général'),
    ('argile', 'machine'), ('prepa1', 'machine'), ('prepa2', 'machine'),
    ('extrudeuse', 'machine'), ('sechoir', 'machine'), ('empileuse', 'machine'),
    ('four', 'machine'), ('depileuse', 'machine'), ('compresseur', 'machine'),
    ('eclirage', 'machine'),
] %}

{% for compteur, niveau in compteurs %}
select
    '{{ "eclairage" if compteur == "eclirage" else compteur }}' as compteur,
    '{{ niveau }}'                                  as niveau,
    cast("id" as bigint)                            as id_releve,
    date_insert                                     as releve_le,
    tansion_m                                       as tension_moyenne,
    courant_m                                       as courant_moyen,
    case when cos_phi_m between 0 and 1 then cos_phi_m end
                                                    as cos_phi,
    (cos_phi_m between 0 and 1)                     as cos_phi_valide,
    p_tot                                           as puissance_active,
    q_tot                                           as puissance_reactive,
    s_tot                                           as puissance_apparente,
    cons_p_total                                    as index_energie,
    cons_p_total_j_1                                as consommation_veille,
    cons_p_plein_j_1                                as consommation_veille_pleine,
    cons_p_pointe_j_1                               as consommation_veille_pointe,
    cons_p_creuse_j_1                               as consommation_veille_creuse,
    _charge_le
from {{ source('electricite', compteur ~ '_elect') }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
