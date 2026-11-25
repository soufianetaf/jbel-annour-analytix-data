"""Contrôles de sécurité du dépôt, exécutés par la CI et en local.

Ce script vérifie que Git ne contient rien qui ne doit pas en sortir :
secrets, documents confidentiels, extractions de données, adresses des
serveurs internes, fichiers trop lourds.

Il ne lit que les fichiers suivis par Git (``git ls-files``), comme le
ferait quelqu'un qui clone le dépôt.

Utilisation, depuis la racine du dépôt :

    python infra/ci/verifier_depot.py

Code de sortie 0 si tout est conforme, 1 sinon (la CI échoue alors).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

# Taille maximale d'un fichier versionné. Au-delà, c'est presque toujours
# une extraction de données ou un fichier généré qui n'a rien à faire ici.
TAILLE_MAX_OCTETS = 5 * 1024 * 1024

# Dossiers qui ne doivent jamais apparaître dans Git.
DOSSIERS_INTERDITS = ("docs/confidentiel/", "exploration/")

# Extensions de fichiers de données : une extraction posée par erreur dans
# le dossier ne doit jamais partir dans Git. Seules les petites tables de
# référence dbt (dbt/seeds/) sont autorisées.
EXTENSIONS_DONNEES = {".csv", ".xlsx", ".xls", ".parquet", ".bak", ".mdf", ".ldf"}
DOSSIER_SEEDS = "dbt/seeds/"

# Adresses IP de réseaux privés (192.168.x.x, 10.x.x.x, 172.16-31.x.x).
# Les adresses des serveurs vont dans .env, jamais dans le code.
MOTIF_IP_PRIVEE = re.compile(
    r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"
)

# Fichiers que ce contrôle d'adresse ignore (binaires, sons, images).
EXTENSIONS_BINAIRES = {".png", ".jpg", ".jpeg", ".gif", ".mp3", ".mp4", ".wav", ".pbix", ".ico"}


def fichiers_suivis() -> list[str]:
    """Liste des fichiers suivis par Git, chemins au format POSIX."""
    resultat = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    return [chemin for chemin in resultat.stdout.decode("utf-8").split("\0") if chemin]


def est_fichier_env(chemin: str) -> bool:
    """Vrai pour .env, .env.prod, etc. ; faux pour le modèle .env.example."""
    nom = PurePosixPath(chemin).name
    return (nom == ".env" or nom.startswith(".env.")) and nom != ".env.example"


def verifier(chemins: list[str]) -> list[str]:
    """Retourne la liste des problèmes trouvés (vide si tout est conforme)."""
    problemes: list[str] = []

    for chemin in chemins:
        extension = PurePosixPath(chemin).suffix.lower()

        # 1. Fichiers de secrets
        if est_fichier_env(chemin):
            problemes.append(f"[secret] fichier d'environnement versionné : {chemin}")

        # 2. Dossiers confidentiels
        for dossier in DOSSIERS_INTERDITS:
            if chemin.startswith(dossier):
                problemes.append(f"[confidentiel] fichier d'un dossier interdit : {chemin}")

        # 3. Fichiers de données
        if extension in EXTENSIONS_DONNEES and not chemin.startswith(DOSSIER_SEEDS):
            problemes.append(f"[donnees] fichier de données hors de {DOSSIER_SEEDS} : {chemin}")

        fichier = Path(chemin)
        if not fichier.is_file():
            continue  # supprimé localement mais encore suivi : rien à lire

        # 4. Taille
        taille = fichier.stat().st_size
        if taille > TAILLE_MAX_OCTETS:
            problemes.append(
                f"[taille] {chemin} fait {taille / 1024 / 1024:.1f} Mo "
                f"(maximum {TAILLE_MAX_OCTETS // 1024 // 1024} Mo)"
            )

        # 5. Adresses IP internes dans les fichiers texte
        if extension in EXTENSIONS_BINAIRES:
            continue
        try:
            contenu = fichier.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # fichier binaire non listé : ignoré
        for numero, ligne in enumerate(contenu.splitlines(), start=1):
            if MOTIF_IP_PRIVEE.search(ligne):
                # On n'affiche pas l'adresse elle-même dans les journaux de la CI.
                problemes.append(f"[adresse] adresse IP interne dans {chemin}, ligne {numero}")

    return problemes


def main() -> int:
    chemins = fichiers_suivis()
    problemes = verifier(chemins)

    if problemes:
        print(f"ÉCHEC : {len(problemes)} problème(s) dans le dépôt.\n")
        for probleme in problemes:
            print(f"  - {probleme}")
        print("\nRetirez ces fichiers de Git (git rm --cached <fichier>) ou corrigez-les.")
        return 1

    print(f"OK : {len(chemins)} fichiers vérifiés, aucun problème.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
