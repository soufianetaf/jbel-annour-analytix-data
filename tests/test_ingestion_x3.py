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
