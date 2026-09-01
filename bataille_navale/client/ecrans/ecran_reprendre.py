# ============================================================
#  client/ecrans/ecran_reprendre.py  —  Reprise par token
# ============================================================
import pygame, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from client.ui.widgets import (Bouton, ChampTexte, dessiner_fond,
                                 dessiner_titre, dessiner_message)


class EcranReprendrePartie:
    """Écran de reprise : saisie du token reçu lors de la déconnexion."""

    def __init__(self, fenetre, client):
        self.fenetre = fenetre
        self.client  = client
        self.message = ""
        w, h         = fenetre.get_size()
        cx           = w // 2

        self.champ_token = ChampTexte(cx - 160, 340, 320, 48,
                                       placeholder="Ex: A7F3-92BC", max_chars=16)
        self.btn_reprendre = Bouton(cx - 140, 420, 280, 50, "Reprendre", style="orange")
        self.btn_retour    = Bouton(cx - 100, 500, 200, 44, "← Retour",  style="gris",
                                    taille_police=18)

    def gerer_evenements(self, events):
        """Retourne 'attente_reprise' | 'retour' | None."""
        for event in events:
            self.champ_token.gerer_evenement(event)

            if self.btn_reprendre.gerer_evenement(event):
                token = self.champ_token.texte.strip().upper()
                if not token:
                    self.message = "Entrez votre token de reprise."
                    continue
                self.client.envoyer("reprendre_partie", token=token)
                return "attente_reprise"

            if self.btn_retour.gerer_evenement(event):
                return "retour"

        return None

    def afficher(self):
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "Reprendre une partie", 160, taille=40)
        dessiner_message(self.fenetre,
                         "Entrez le token reçu lors de votre déconnexion.",
                         230, taille=20)
        dessiner_message(self.fenetre,
                         "Le token vous a été fourni par le serveur.",
                         260, couleur=(150, 180, 220), taille=16)

        w = self.fenetre.get_width()
        police = pygame.font.SysFont("segoeui", 18)
        s = police.render("Token de reprise :", True, (180, 200, 240))
        self.fenetre.blit(s, (w // 2 - 160, 318))

        self.champ_token.afficher(self.fenetre)
        self.btn_reprendre.afficher(self.fenetre)
        self.btn_retour.afficher(self.fenetre)

        if self.message:
            dessiner_message(self.fenetre, self.message, 560,
                             couleur=(255, 100, 100), taille=18)
