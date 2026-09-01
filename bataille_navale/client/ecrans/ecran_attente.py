# ============================================================
#  client/ecrans/ecran_attente.py  —  Attente d'un adversaire
# ============================================================
import pygame, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from client.ui.widgets import Bouton, dessiner_fond, dessiner_titre, dessiner_message
from constantes import BLANC, GRIS_CLAIR


class EcranAttente:
    """Affiché quand le joueur a créé une partie et attend un adversaire."""

    def __init__(self, fenetre, client, nom_partie, partie_id):
        self.fenetre    = fenetre
        self.client     = client
        self.nom_partie = nom_partie
        self.partie_id  = partie_id
        self._tick      = 0
        w, h = fenetre.get_size()
        self.btn_quitter = Bouton(w // 2 - 100, h - 130, 200, 44,
                                   "Annuler", style="rouge", taille_police=18)

    def gerer_evenements(self, events):
        """Retourne 'quitter' | None."""
        for event in events:
            if self.btn_quitter.gerer_evenement(event):
                return "quitter"
        return None

    def afficher(self):
        self._tick += 1
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "En attente d'un adversaire…", 180, taille=36)
        dessiner_message(self.fenetre, f"Partie : {self.nom_partie}", 260, taille=22)
        dessiner_message(self.fenetre, f"ID : {self.partie_id}", 296,
                         couleur=(150, 200, 255), taille=18)

        # Animation points
        pts = "." * ((self._tick // 20) % 4)
        dessiner_message(self.fenetre, f"Recherche d'un joueur{pts}", 360,
                         couleur=(180, 220, 180), taille=20)
        self.btn_quitter.afficher(self.fenetre)
