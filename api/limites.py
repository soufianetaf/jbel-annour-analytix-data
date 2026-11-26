"""Limite des tentatives de connexion (essais de mots de passe en série).

Deux compteurs, sur une fenêtre glissante :
- par compte : API_TENTATIVES_PAR_COMPTE échecs (5 par défaut) ;
- par adresse : API_TENTATIVES_PAR_ADRESSE échecs (20), pour qu'un même
  poste n'essaie pas un mot de passe sur tous les comptes.
Au-delà, la connexion est refusée (429) jusqu'à ce que les échecs les plus
anciens sortent de la fenêtre (15 minutes). Une connexion réussie remet le
compteur du compte à zéro.

Le compte n'est jamais verrouillé définitivement : sinon n'importe qui
pourrait bloquer le compte d'un autre en se trompant exprès.

Les compteurs sont en mémoire : ils valent pour un processus de l'API.
Avec plusieurs processus, chacun a les siens (limite multipliée d'autant) ;
un stockage partagé sera nécessaire si l'API tourne sur plusieurs serveurs.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class LimiteurTentatives:
    def __init__(
        self,
        par_compte: int,
        par_adresse: int,
        fenetre_secondes: float,
        horloge=time.monotonic,
    ) -> None:
        self.par_compte = par_compte
        self.par_adresse = par_adresse
        self.fenetre = fenetre_secondes
        self._horloge = horloge
        self._verrou = threading.Lock()
        self._echecs: dict[str, deque[float]] = defaultdict(deque)

    def _nettoyer(self, cle: str, maintenant: float) -> deque[float]:
        echecs = self._echecs[cle]
        while echecs and maintenant - echecs[0] >= self.fenetre:
            echecs.popleft()
        return echecs

    def attente(self, identifiant: str, adresse: str) -> int:
        """Secondes à attendre avant un nouvel essai (0 : l'essai est permis)."""
        maintenant = self._horloge()
        with self._verrou:
            attente = 0.0
            for cle, limite in (
                (f"compte:{identifiant}", self.par_compte),
                (f"adresse:{adresse}", self.par_adresse),
            ):
                echecs = self._nettoyer(cle, maintenant)
                if len(echecs) >= limite:
                    attente = max(attente, self.fenetre - (maintenant - echecs[0]))
            return int(attente) + (1 if attente else 0)

    def echec(self, identifiant: str, adresse: str) -> None:
        maintenant = self._horloge()
        with self._verrou:
            self._echecs[f"compte:{identifiant}"].append(maintenant)
            self._echecs[f"adresse:{adresse}"].append(maintenant)

    def reussite(self, identifiant: str) -> None:
        with self._verrou:
            self._echecs.pop(f"compte:{identifiant}", None)
