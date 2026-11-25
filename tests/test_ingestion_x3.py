"""Tests de l'ingestion Sage X3 : colonnes copiées, tables, rapprochement."""

from decimal import Decimal

import pytest

from ingestion.colonnes import ColonneSensibleNonDecidee, colonnes_a_copier
from ingestion.rapprochement import Mesure, Resultat
from ingestion.x3_ventes import TABLES

# ─── Colonnes sensibles ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "colonne",
    ["PAYBAN_0", "USRPASS_0", "PWD_0", "TOKEN", "NUMCIN_0", "RIB_0", "IBAN", "SALAIRE"],
)
def test_colonne_sensible_non_decidee_arrete_le_chargement(colonne: str) -> None:
    # En cas de doute, on ne copie rien : il faut décider explicitement
    with pytest.raises(ColonneSensibleNonDecidee, match=colonne):
        colonnes_a_copier(["NUM_0", colonne])


def test_colonne_exclue_n_est_pas_copiee() -> None:
    colonnes = colonnes_a_copier(["NUM_0", "PAYBAN_0", "AMTATI_0"], exclues={"PAYBAN_0"})

    assert colonnes == ["NUM_0", "AMTATI_0"]


def test_colonne_autorisee_apres_verification_est_copiee() -> None:
    colonnes = colonnes_a_copier(["NUM_0", "XTOKENTYP_0"], autorisees={"XTOKENTYP_0"})

    assert colonnes == ["NUM_0", "XTOKENTYP_0"]


def test_colonnes_ordinaires_copiees_dans_l_ordre_de_la_source() -> None:
    colonnes = ["NUM_0", "BPR_0", "ACCDAT_0", "AMTATI_0", "SALFCY_0"]

    assert colonnes_a_copier(colonnes) == colonnes


def test_colonne_decidee_disparue_de_la_source_signalee() -> None:
    # La source a changé de structure : on le signale au lieu de l'ignorer
    with pytest.raises(ValueError, match="absentes"):
        colonnes_a_copier(["NUM_0"], exclues={"PAYBAN_0"})


# ─── Définition des tables ──────────────────────────────────────────


@pytest.mark.parametrize("table", TABLES, ids=lambda t: t.nom)
def test_chaque_table_a_une_cle(table) -> None:
    assert table.cle, "la clé sert au contrôle des doublons"
    assert table.destination == table.nom.lower()


@pytest.mark.parametrize("nom", ["SINVOICE", "SINVOICED"])
def test_chaque_table_de_mouvements_a_un_montant(nom: str) -> None:
    # Les factures sont rapprochées en montant ; les référentiels, en lignes
    assert next(t for t in TABLES if t.nom == nom).montant


def test_banque_de_paiement_jamais_copiee() -> None:
    entetes = next(t for t in TABLES if t.nom == "SINVOICE")

    assert "PAYBAN_0" in entetes.exclues


# ─── Rapprochement ──────────────────────────────────────────────────


def _resultat(source: Mesure, entrepot: Mesure) -> Resultat:
    return Resultat(table="SINVOICE", source=source, entrepot=entrepot)


def test_copie_identique_conforme() -> None:
    mesure = Mesure(lignes=7988, montant=Decimal("123456789.12"))

    assert _resultat(mesure, mesure).conforme


def test_ligne_manquante_detectee() -> None:
    r = _resultat(Mesure(10, Decimal(100)), Mesure(9, Decimal(100)))

    assert not r.conforme
    assert r.problemes == ["-1 ligne(s)"]


def test_ecart_de_montant_sous_le_centime_tolere() -> None:
    # Critère d'acceptation n° 1 : écart inférieur à 0,01 MAD
    r = _resultat(Mesure(10, Decimal("100.000")), Mesure(10, Decimal("100.009")))

    assert r.conforme


def test_ecart_de_montant_d_un_centime_detecte() -> None:
    r = _resultat(Mesure(10, Decimal("100.00")), Mesure(10, Decimal("100.01")))

    assert not r.conforme
    assert "écart de montant" in r.problemes[0]


def test_doublon_de_cle_detecte() -> None:
    r = _resultat(Mesure(10, Decimal(100)), Mesure(10, Decimal(100), doublons=1))

    assert r.problemes == ["1 doublon(s) sur la clé"]


# ─── Listes fermées et CA annuel ────────────────────────────────────


def test_liste_fermee_ne_copie_que_les_colonnes_choisies() -> None:
    # Une colonne ajoutée plus tard dans la source n'entre jamais sans décision
    source = ["BPCNUM_0", "BPCNAM_0", "XCINGER_0", "PAYBAN_0", "NOUVELLE_0"]

    assert colonnes_a_copier(source, seulement=("BPCNUM_0", "BPCNAM_0")) == [
        "BPCNUM_0",
        "BPCNAM_0",
    ]


def test_liste_fermee_avec_colonne_disparue_signalee() -> None:
    with pytest.raises(ValueError, match="absentes"):
        colonnes_a_copier(["BPCNUM_0"], seulement=("BPCNUM_0", "BPCNAM_0"))


def test_liste_fermee_soumise_au_controle_des_colonnes_sensibles() -> None:
    # Mettre par erreur le CIN du gérant dans la liste fermée est bloqué
    with pytest.raises(ColonneSensibleNonDecidee, match="XCINGER_0"):
        colonnes_a_copier(["BPCNUM_0", "XCINGER_0"], seulement=("BPCNUM_0", "XCINGER_0"))


def test_fiche_client_sans_cin_ni_banque() -> None:
    clients = next(t for t in TABLES if t.nom == "BPCUSTOMER")

    assert clients.seulement is not None
    for interdite in ("XCINGER_0", "XCINASS_0", "PAYBAN_0", "XTRIB_0", "XPASSIFC_0"):
        assert interdite not in clients.seulement


def test_ca_identique_conforme() -> None:
    from ingestion.rapprochement import comparer_ca

    ca = {2025: Decimal("100.00"), 2026: Decimal("50.00")}

    assert all(ok for *_, ok in comparer_ca(ca, ca))


def test_annee_absente_de_l_entrepot_detectee() -> None:
    from ingestion.rapprochement import comparer_ca

    lignes = comparer_ca({2025: Decimal(100), 2026: Decimal(50)}, {2026: Decimal(50)})

    assert lignes[0] == (2025, Decimal(100), Decimal(0), False)


# ─── Moteur commun et finance ───────────────────────────────────────


def test_table_incrementale_sans_sa_date_de_modification_refusee() -> None:
    # Sans la colonne de date copiée, la copie incrémentale ne pourrait pas reprendre
    from ingestion.x3 import TableX3, verifier_tables

    table = TableX3(nom="T", cle=("NUM_0",), incremental="UPDDATTIM_0", seulement=("NUM_0",))

    with pytest.raises(ValueError, match="UPDDATTIM_0"):
        verifier_tables((table,), {"T": ["NUM_0", "UPDDATTIM_0"]})


def test_table_sans_sa_cle_refusee() -> None:
    # Sans la clé, la fusion incrémentale créerait des doublons
    from ingestion.x3 import TableX3, verifier_tables

    table = TableX3(nom="T", cle=("NUM_0", "LIG_0"), seulement=("NUM_0",))

    with pytest.raises(ValueError, match="LIG_0"):
        verifier_tables((table,), {"T": ["NUM_0", "LIG_0"]})


def test_echeances_copiees_en_incremental_avec_cle_complete() -> None:
    from ingestion.x3_finance import TABLES as TABLES_FINANCE

    echeances = TABLES_FINANCE[0]

    assert echeances.incremental == "UPDDATTIM_0"
    assert echeances.lag_jours >= 1
    assert echeances.cle == ("TYP_0", "NUM_0", "LIG_0", "DUDLIG_0")
    assert set(echeances.cle) <= set(echeances.seulement)


def test_requete_balance_additionne_toutes_les_periodes() -> None:
    # Les 28 colonnes de la BALANCE (à-nouveaux + périodes) sont toutes prises
    from ingestion.rapprochement import requete_resultat_x3

    sql = requete_resultat_x3("BASE1")

    assert "CAST(DEBLED_0 " in sql and "CAST(DEBLED_27 " in sql
    assert "CAST(CDTLED_0 " in sql and "CAST(CDTLED_27 " in sql
    assert "DEBLED_28" not in sql
    assert "LEDTYP_0 = 1" in sql  # comptabilité générale seulement


def test_comptabilite_sans_libelle_ni_nom_de_tiers() -> None:
    # Un libellé d'écriture peut contenir un nom de personne
    from ingestion.x3_finance import TABLES as TABLES_FINANCE

    lignes = next(t for t in TABLES_FINANCE if t.nom == "GACCENTRYD")

    assert "DES_0" not in lignes.seulement
    assert "XBPRNAM_0" not in lignes.seulement


def test_soldes_compares_compte_par_compte() -> None:
    # Deux écarts qui se compensent dans le total restent visibles par compte
    from ingestion.rapprochement import comparer_soldes

    source = {(6, "514A"): Decimal(100), (6, "514B"): Decimal(50)}
    entrepot = {(6, "514A"): Decimal(150), (6, "514B"): Decimal(0)}

    total_source, total_entrepot, ecarts = comparer_soldes(source, entrepot)[6]

    assert total_source == total_entrepot == Decimal(150)
    assert ecarts == ["514A", "514B"]


def test_balance_lue_sur_ses_lignes_de_total() -> None:
    # La BALANCE a une ligne par site et par tiers ET une ligne de total
    from ingestion.rapprochement import REQUETE_TRESORERIE_X3, requete_resultat_x3

    for sql in (requete_resultat_x3("BASE1"), REQUETE_TRESORERIE_X3):
        assert "LTRIM(RTRIM(FCY_0)) = ''" in sql
        assert "LTRIM(RTRIM(BPR_0)) = ''" in sql


def test_verification_des_types_detecte_une_macro_texte_sur_un_nombre() -> None:
    # stg_x3__mouvements_stock applique texte_x3 à stofcy_0 : si la colonne
    # était un nombre (comme UPDCOD_0 l'est réellement), l'outil doit le dire
    from infra.ci.verifier_types_staging import incoherences

    types = {("raw_x3", "stojou", "stofcy_0"): "bigint"}

    problemes = incoherences(types)

    assert any(
        "stg_x3__mouvements_stock" in p and "texte_x3(stofcy_0)" in p and "bigint" in p
        for p in problemes
    )
