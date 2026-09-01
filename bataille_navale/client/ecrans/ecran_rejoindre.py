# ============================================================
#  client/ecrans/ecran_rejoindre.py  —  Liste des parties disponibles
# ============================================================
import pygame, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from client.ui.widgets import (Bouton, ListeParties, dessiner_fond,
                                 dessiner_titre, dessiner_message)


class EcranRejoindrePartie:
    """Liste les parties en attente reçues du serveur."""

    def __init__(self, fenetre, client):
        self.fenetre   = fenetre
        self.client    = client
        self.message   = ""
        self.selection = None
        w, h = fenetre.get_size()
        cx   = w // 2

        self.liste  = ListeParties(cx - 320, 200, 640, 380)
        self.btn_rejoindre = Bouton(cx - 200, 600, 180, 48, "Rejoindre", style="vert")
        self.btn_refresh   = Bouton(cx +  20, 600, 180, 48, "🔄 Actualiser", style="bleu")
        self.btn_retour    = Bouton(cx - 80,  665, 160, 40, "← Retour",    style="gris",
                                    taille_police=18)
        # Demander la liste dès l'ouverture
        self.client.envoyer("liste_parties")

    def mettre_a_jour_liste(self, parties):
        self.liste.mettre_a_jour(parties)

    def gerer_evenements(self, events):
        """Retourne 'rejoint' | 'retour' | None."""
        for event in events:
            partie = self.liste.gerer_evenement(event)
            if partie:
                self.selection = partie

            if self.btn_rejoindre.gerer_evenement(event):
                if self.selection:
                    self.client.envoyer("rejoindre_partie",
                                        partie_id=self.selection["id"])
                    return "attente_rejoindre"
                else:
                    self.message = "Sélectionnez une partie d'abord."

            if self.btn_refresh.gerer_evenement(event):
                self.client.envoyer("liste_parties")
                self.message = "Actualisation…"

            if self.btn_retour.gerer_evenement(event):
                return "retour"

        return None

    def afficher(self):
        dessiner_fond(self.fenetre)
        dessiner_titre(self.fenetre, "Rejoindre une partie", 120, taille=40)
        dessiner_message(self.fenetre, "Cliquez sur une partie puis sur Rejoindre",
                         170, taille=18)

        if not self.liste.parties:
            dessiner_message(self.fenetre,
                             "Aucune partie disponible pour le moment.",
                             390, couleur=(180, 180, 180), taille=20)

        self.liste.afficher(self.fenetre)
        self.btn_rejoindre.afficher(self.fenetre)
        self.btn_refresh.afficher(self.fenetre)
        self.btn_retour.afficher(self.fenetre)

        if self.message:
            dessiner_message(self.fenetre, self.message, 716,
                             couleur=(255, 200, 100), taille=18)
