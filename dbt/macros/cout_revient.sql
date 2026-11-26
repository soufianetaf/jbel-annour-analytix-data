{#
  Coût de revient : docs/indicateurs/cout_revient.md (à valider avec le
  contrôle de gestion).
#}

{#
  Famille de coût d'un compte de charges d'exploitation (61), d'après le
  plan comptable marocain et les comptes utilisés par Jbel Annour.
  Les achats de marchandises revendues (611 : camions, terrains…) ne sont
  pas un coût de fabrication des briques : « hors coût de revient ».
  L'ordre compte : le préfixe le plus précis passe en premier.
#}
{% macro famille_cout(compte) -%}
    case
        when {{ compte }} like '611%' then 'hors coût de revient'
        when {{ compte }} like '61223%' then 'combustibles'
        when {{ compte }} like '61251%' then 'électricité'
        when {{ compte }} like '6121%' or {{ compte }} like '61241%' then 'argile et matières premières'
        when {{ compte }} like '6123%' or {{ compte }} like '61243%' then 'emballages'
        when {{ compte }} like '61220001%' or {{ compte }} like '6133%' or {{ compte }} like '61252%'
            then 'entretien et pièces de rechange'
        when {{ compte }} like '6122%' or {{ compte }} like '6124%' or {{ compte }} like '6125%'
            then 'autres consommables'
        when {{ compte }} like '6126%' then 'prestations de services'
        when {{ compte }} like '6131%' or {{ compte }} like '6132%' then 'locations et crédit-bail'
        when {{ compte }} like '617%' then 'personnel'
        when {{ compte }} like '619%' then 'amortissements et provisions'
        when {{ compte }} like '61%' then 'autres charges'
    end
{%- endmacro %}


{#
  Type de brique lu dans la désignation de l'article Sage X3 :
  « BRIQUE BLCH8 », « B8 PBP », « BRIQUE 250/200/100 PL (B10) »,
  « BRIQUE_12 », « A// BRIQUE B12 (50CM) » → B8, B10, B12…
  Vide pour ce qui n'est pas une brique vendue (réfractaire, casse, moule).
#}
{% macro type_brique_vente(designation) -%}
    case
        when upper({{ designation }}) ~ 'REFRACT|CASSE|MOULE|ANALYSE|CACHET' then null
        when upper({{ designation }}) !~ 'BRIQUE|^B\d' then null
        else 'B' || coalesce(
            substring(upper({{ designation }}) from 'B(?:LCH|F)?\s*(\d{1,2})(?!\d)'),
            substring(upper({{ designation }}) from 'BRIQUE[ _](\d{1,2})(?!\d)')
        )
    end
{%- endmacro %}
