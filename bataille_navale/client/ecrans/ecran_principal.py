# ============================================================
#  client/ecrans/ecran_principal.py  —  Menu d'accueil
# ============================================================
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.ui.widgets import Bouton, dessiner_fond, dessiner_titre, dessiner_message
from constantes import BLANC, GRIS_CLAIR


class EcranPrincipal:
    """
    Menu d'accueil.
    Propose : Créer une partie | Rejoindre une partie | Reprendre une partie.
    """

    def __init__(self, fenetre, client):
        self.fenetre = fenetre
        self.client  = client
        w, h         = fenetre.get_size()
        cx           = w // 2

        self.btn_creer    = Bouton(cx - 160, 290, 320, 55, "➕  Créer une partie",   style="vert")
        self.btn_rejoindre= Bouton(cx - 160, 365, 320, 55, "🔗  Rejoindre une partie", style="bleu")
        self.btn_reprendre= Bouton(cx - 160, 440, 320, 55, "🔄  Reprendre une partie", style="orange")
        self.btn_quitter  = Bouton(cx - 160, 530, 320, 45, "Quitter",                style="gris",
                                   taille_police=18)

        self.boutons = [self.btn_creer, self.btn_rejoindre,
                        self.btn_reprendre, self.btn_quitter]

    def gerer_evenements(self, events):
        """
        Retourne : 'creer' | 'rejoindre' | 'reprendre' | 'quitter' | None
        """
        for event in events:
            if self.btn_creer.gerer_evenement(event):
                return "creer"
            if self.btn_rejoindre.gerer_evenement(event):
                return "rejoindre"
            if self.btn_reprendre.gerer_evenement(event):
                return "reprendre"
            if self.btn_quitter.gerer_evenement(event):
                return "quitter"
        return None

    def afficher(self):
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "⚓  BATAILLE NAVALE", 120, taille=52)
        dessiner_message(self.fenetre, "Choisissez une action", 200, taille=22)
        dessiner_message(self.fenetre, f"Connecté en tant que : {self.client._pseudo}",
                         235, couleur=(150, 200, 255), taille=18)
        for b in self.boutons:
            b.afficher(self.fenetre)
