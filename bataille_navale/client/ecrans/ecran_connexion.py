# ============================================================
#  client/ecrans/ecran_connexion.py  —  Saisie pseudo et IP serveur
# ============================================================
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.ui.widgets import (Bouton, ChampTexte, dessiner_fond,
                                 dessiner_titre, dessiner_message)
from constantes import BLANC, ROUGE_BOUTON, IP_DEFAUT, PORT_DEFAUT


class EcranConnexion:
    """
    Premier écran : saisie du pseudo et de l'adresse IP du serveur.
    """

    def __init__(self, fenetre):
        self.fenetre  = fenetre
        self.message  = ""
        self.en_cours = False
        w, h          = fenetre.get_size()
        cx            = w // 2

        self.champ_pseudo = ChampTexte(cx - 180, 310, 360, 45,
                                        placeholder="Votre pseudo", max_chars=20)
        self.champ_ip     = ChampTexte(cx - 180, 390, 260, 45,
                                        placeholder=IP_DEFAUT, max_chars=40)
        self.champ_port   = ChampTexte(cx + 90,  390, 90,  45,
                                        placeholder=str(PORT_DEFAUT), max_chars=5)
        self.btn_connexion = Bouton(cx - 140, 470, 280, 50, "Se connecter", style="vert")
        self.btn_quitter   = Bouton(cx - 80,  545,  160, 40, "Quitter", style="gris", taille_police=18)

    def gerer_evenements(self, events):
        """Retourne ('connecter', pseudo, ip, port) ou ('quitter',) ou None."""
        for event in events:
            self.champ_pseudo.gerer_evenement(event)
            self.champ_ip.gerer_evenement(event)
            self.champ_port.gerer_evenement(event)

            if self.btn_connexion.gerer_evenement(event):
                pseudo = self.champ_pseudo.texte.strip()
                ip     = self.champ_ip.texte.strip()    or IP_DEFAUT
                port_s = self.champ_port.texte.strip()  or str(PORT_DEFAUT)
                if not pseudo:
                    self.message = "Veuillez entrer un pseudo."
                    continue
                try:
                    port = int(port_s)
                except ValueError:
                    self.message = "Port invalide."
                    continue
                return ("connecter", pseudo, ip, port)

            if self.btn_quitter.gerer_evenement(event):
                return ("quitter",)

        return None

    def afficher(self):
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "⚓  BATAILLE NAVALE", 120, taille=52)
        dessiner_message(self.fenetre, "Connexion au serveur", 210, taille=26)

        w = self.fenetre.get_width()
        police_label = pygame.font.SysFont("segoeui", 18)

        def label(texte, y):
            s = police_label.render(texte, True, (180, 200, 240))
            self.fenetre.blit(s, (w // 2 - 180, y))

        label("Pseudo :", 288)
        label("Adresse IP du serveur :", 368)
        label("Port :", 368)

        self.champ_pseudo.afficher(self.fenetre)
        self.champ_ip.afficher(self.fenetre)
        self.champ_port.afficher(self.fenetre)
        self.btn_connexion.afficher(self.fenetre)
        self.btn_quitter.afficher(self.fenetre)

        if self.message:
            dessiner_message(self.fenetre, self.message, 530,
                             couleur=(255, 100, 100), taille=18)

    def afficher_connexion_en_cours(self):
        dessiner_message(self.fenetre, "Connexion en cours...", 530,
                         couleur=(100, 255, 150), taille=18)
