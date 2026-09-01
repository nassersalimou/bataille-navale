# ============================================================
#  client/ecrans/ecran_creer.py  —  Création d'une nouvelle partie
# ============================================================
import pygame
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.ui.widgets import (Bouton, ChampTexte, dessiner_fond,
                                 dessiner_titre, dessiner_message)
from constantes import BLANC


class EcranCreerPartie:
    """Écran pour créer une partie : saisie du nom."""

    def __init__(self, fenetre, client):
        self.fenetre = fenetre
        self.client  = client
        self.message = ""
        w, h         = fenetre.get_size()
        cx           = w // 2

        self.champ_nom = ChampTexte(cx - 200, 340, 400, 48,
                                     placeholder="Nom de la partie", max_chars=30)
        self.btn_creer  = Bouton(cx - 140, 420, 280, 52, "Créer", style="vert")
        self.btn_retour = Bouton(cx - 100, 500, 200, 44, "← Retour", style="gris",
                                  taille_police=18)

    def gerer_evenements(self, events):
        """Retourne 'cree' | 'retour' | None."""
        for event in events:
            self.champ_nom.gerer_evenement(event)

            if self.btn_creer.gerer_evenement(event):
                nom = self.champ_nom.texte.strip()
                if not nom:
                    self.message = "Donnez un nom à la partie."
                    continue
                self.client.envoyer("creer_partie", nom=nom)
                return "attente_creation"

            if self.btn_retour.gerer_evenement(event):
                return "retour"

        return None

    def afficher(self):
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "Créer une partie", 160, taille=40)
        dessiner_message(self.fenetre, "Entrez un nom pour votre partie", 230, taille=20)

        w = self.fenetre.get_width()
        police_label = pygame.font.SysFont("segoeui", 18)
        s = police_label.render("Nom de la partie :", True, (180, 200, 240))
        self.fenetre.blit(s, (w // 2 - 200, 318))

        self.champ_nom.afficher(self.fenetre)
        self.btn_creer.afficher(self.fenetre)
        self.btn_retour.afficher(self.fenetre)

        if self.message:
            dessiner_message(self.fenetre, self.message, 570,
                             couleur=(255, 100, 100), taille=18)
