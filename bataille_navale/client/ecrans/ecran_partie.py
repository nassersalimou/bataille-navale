# ============================================================
#  client/ecrans/ecran_partie.py  —  Déroulement de la partie
# ============================================================
import pygame, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from grille import Grille
from case  import Case
from client.ui.widgets import Bouton, dessiner_fond, dessiner_message
from constantes import BLANC, GRIS_CLAIR, GRIS_FONCE, NOIR, TAILLE_CASE


class PopupQuitter:
    """
    Fenêtre modale affichée quand le joueur clique sur Quitter en cours de partie.
    Propose deux options :
      - Sauvegarder et quitter  → la partie est sauvegardée, token affiché
      - Quitter sans sauvegarder → on part, la partie est perdue
    """

    def __init__(self, fenetre):
        self.fenetre = fenetre
        w, h = fenetre.get_size()
        cx, cy = w // 2, h // 2

        # Fond de la popup
        self.rect_fond = pygame.Rect(cx - 280, cy - 160, 560, 320)

        self.btn_sauvegarder = Bouton(cx - 240, cy - 20,  230, 52,
                                       "💾  Sauvegarder et quitter", style="orange", taille_police=17)
        self.btn_quitter     = Bouton(cx +  10, cy - 20,  230, 52,
                                       "🚪  Quitter sans sauvegarder", style="rouge",  taille_police=17)
        self.btn_annuler     = Bouton(cx - 90,  cy + 60,  180, 42,
                                       "Annuler", style="gris", taille_police=16)

        self._police_titre = pygame.font.SysFont("segoeui", 24, bold=True)
        self._police_info  = pygame.font.SysFont("segoeui", 16)

        # Token affiché après sauvegarde
        self.token_affiche  = None
        self.btn_ok_token   = Bouton(cx - 70, cy + 100, 140, 42,
                                      "OK", style="vert", taille_police=18)

    def gerer_evenements(self, events):
        """
        Retourne :
          'annuler'           → fermer la popup, reprendre la partie
          'quitter_seul'      → quitter sans sauvegarder
          'sauvegarder'       → demander sauvegarde au serveur
          'fermer_apres_save' → après affichage du token, quitter
          None                → rien
        """
        for event in events:
            # Phase token : seul le bouton OK est actif
            if self.token_affiche is not None:
                if self.btn_ok_token.gerer_evenement(event):
                    return "fermer_apres_save"
                continue

            if self.btn_annuler.gerer_evenement(event):
                return "annuler"
            if self.btn_quitter.gerer_evenement(event):
                return "quitter_seul"
            if self.btn_sauvegarder.gerer_evenement(event):
                return "sauvegarder"
        return None

    def afficher_token(self, token):
        """Appelé par l'écran partie quand le serveur confirme la sauvegarde."""
        self.token_affiche = token

    def afficher(self):
        w, h = self.fenetre.get_size()
        cx   = w // 2

        # Fond semi-transparent
        voile = pygame.Surface((w, h), pygame.SRCALPHA)
        voile.fill((0, 0, 0, 160))
        self.fenetre.blit(voile, (0, 0))

        # Boîte
        pygame.draw.rect(self.fenetre, (25, 35, 60), self.rect_fond, border_radius=14)
        pygame.draw.rect(self.fenetre, (80, 120, 200), self.rect_fond, 3, border_radius=14)

        cy = self.rect_fond.centery

        if self.token_affiche is None:
            # Affichage normal : choix quitter
            s = self._police_titre.render("Que souhaitez-vous faire ?", True, BLANC)
            self.fenetre.blit(s, s.get_rect(centerx=cx, y=self.rect_fond.y + 24))

            lignes = [
                "Sauvegarder : la partie sera mise en attente.",
                "Un token unique vous sera donné pour la reprendre.",
                "N'importe qui pourra rejoindre avec ce token.",
            ]
            for i, ligne in enumerate(lignes):
                s = self._police_info.render(ligne, True, (180, 200, 230))
                self.fenetre.blit(s, s.get_rect(centerx=cx, y=self.rect_fond.y + 75 + i * 22))

            self.btn_sauvegarder.afficher(self.fenetre)
            self.btn_quitter.afficher(self.fenetre)
            self.btn_annuler.afficher(self.fenetre)
        else:
            # Affichage du token après sauvegarde
            s = self._police_titre.render("Partie sauvegardée !", True, (100, 255, 150))
            self.fenetre.blit(s, s.get_rect(centerx=cx, y=self.rect_fond.y + 24))

            s2 = self._police_info.render("Votre token de reprise :", True, GRIS_CLAIR)
            self.fenetre.blit(s2, s2.get_rect(centerx=cx, y=self.rect_fond.y + 80))

            police_token = pygame.font.SysFont("couriernew", 30, bold=True)
            s3 = police_token.render(self.token_affiche, True, (255, 220, 50))
            self.fenetre.blit(s3, s3.get_rect(centerx=cx, y=self.rect_fond.y + 115))

            s4 = self._police_info.render(
                "Notez ce token. Allez dans 'Reprendre une partie' pour continuer.",
                True, (180, 200, 230))
            self.fenetre.blit(s4, s4.get_rect(centerx=cx, y=self.rect_fond.y + 170))

            self.btn_ok_token.afficher(self.fenetre)


class EcranPartie:
    """
    Affiche :
      - La grille du joueur (gauche) avec ses navires
      - La grille ennemie (droite) sur laquelle il tire
    Gère la popup de quitter avec ou sans sauvegarde.
    """

    def __init__(self, fenetre, client, pseudo_joueur, pseudo_adverse):
        self.fenetre         = fenetre
        self.client          = client
        self.pseudo_joueur   = pseudo_joueur
        self.pseudo_adverse  = pseudo_adverse
        self.message         = ""
        self.c_est_mon_tour  = False
        self.partie_finie    = False
        self.resultat_final  = ""

        w, h = fenetre.get_size()
        marge_haut = 110
        self.grille_propre  = Grille(x=40,                         y=marge_haut)
        self.grille_ennemie = Grille(x=w - 40 - TAILLE_CASE * 10, y=marge_haut)

        self.btn_quitter = Bouton(w // 2 - 80, h - 65, 160, 44,
                                   "Quitter", style="rouge", taille_police=18)
        self._police_label = pygame.font.SysFont("segoeui", 19, bold=True)
        self._police_info  = pygame.font.SysFont("segoeui", 16)
        self._log          = []

        # Popup (None = pas affichée)
        self._popup = None

    # ----------------------------------------------------------
    #  Mise à jour depuis les messages serveur
    # ----------------------------------------------------------
    def appliquer_etat_grille(self, type_grille, cases):
        if type_grille == "propre":
            self.grille_propre.appliquer_etat(cases)
        else:
            self.grille_ennemie.appliquer_etat(cases)

    def set_tour(self, c_est_mon_tour):
        self.c_est_mon_tour = c_est_mon_tour
        if c_est_mon_tour:
            self.message = "C'est votre tour — cliquez sur la grille adverse !"
        else:
            self.message = f"Tour de {self.pseudo_adverse}…"

    def ajouter_log(self, texte):
        self._log.append(texte)
        if len(self._log) > 6:
            self._log.pop(0)

    def fin_partie(self, gagne):
        self.partie_finie  = True
        self.resultat_final = "Victoire ! 🏆" if gagne else "Défaite… ⚓"
        self.message        = self.resultat_final
        self._popup         = None  # fermer popup si ouverte

    def recevoir_token_sauvegarde(self, token):
        """Appelé par app_client quand le serveur envoie le token après sauvegarde."""
        if self._popup:
            self._popup.afficher_token(token)

    # ----------------------------------------------------------
    #  Événements
    # ----------------------------------------------------------
    def gerer_evenements(self, events):
        """
        Retourne :
          'quitter'       → retour menu sans sauvegarde
          'quitter_save'  → retour menu après sauvegarde (token déjà affiché)
          None            → rien
        """
        mx, my = pygame.mouse.get_pos()

        # Si la popup est ouverte, on lui délègue tous les événements
        if self._popup is not None:
            res_popup = self._popup.gerer_evenements(events)
            if res_popup == "annuler":
                self._popup = None
            elif res_popup == "quitter_seul":
                # Partir sans sauvegarder — on envoie quitter au serveur
                self.client.envoyer("quitter")
                return "quitter"
            elif res_popup == "sauvegarder":
                # Demander la sauvegarde au serveur
                self.client.envoyer("sauvegarder_et_quitter")
                # La popup reste ouverte et attend le token
            elif res_popup == "fermer_apres_save":
                return "quitter_save"
            return None

        # Survol grille ennemie
        if self.c_est_mon_tour and not self.partie_finie:
            self.grille_ennemie.mettre_a_jour_survol(mx, my)

        for event in events:
            # Bouton quitter principal
            if self.btn_quitter.gerer_evenement(event):
                if self.partie_finie:
                    # Partie terminée : quitter directement, pas besoin de sauvegarder
                    return "quitter"
                else:
                    # Partie en cours : ouvrir la popup
                    self._popup = PopupQuitter(self.fenetre)
                    return None

            # Tir sur la grille ennemie
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self.c_est_mon_tour and not self.partie_finie):
                case = self.grille_ennemie.clic_vers_case(mx, my)
                if case and case.etat == Case.ETAT_EAU:
                    self.client.envoyer("tir", ligne=case.ligne, colonne=case.colonne)
                    self.c_est_mon_tour = False
                    self.message = "Tir envoyé…"

        return None

    # ----------------------------------------------------------
    #  Affichage
    # ----------------------------------------------------------
    def afficher(self):
        dessiner_fond(self.fenetre)
        w, h = self.fenetre.get_size()

        # Titres des grilles
        s1 = self._police_label.render(
            f"Votre flotte — {self.pseudo_joueur}", True, (150, 220, 255))
        s2 = self._police_label.render(
            f"Flotte ennemie — {self.pseudo_adverse}", True, (255, 160, 100))
        self.fenetre.blit(s1, (self.grille_propre.x, 80))
        self.fenetre.blit(s2, (self.grille_ennemie.x, 80))

        # Étiquettes
        police_etiq = pygame.font.SysFont("segoeui", 13)
        self.grille_propre.afficher_etiquettes(self.fenetre, police_etiq)
        self.grille_ennemie.afficher_etiquettes(self.fenetre, police_etiq)

        self.grille_propre.afficher(self.fenetre)
        self.grille_ennemie.afficher(self.fenetre)

        # Indicateur de tour (centre haut)
        cx = w // 2
        if not self.partie_finie:
            indicateur  = "▶ Votre tour" if self.c_est_mon_tour else "⏳ Tour adverse"
            couleur_ind = (100, 255, 100) if self.c_est_mon_tour else (255, 180, 60)
            s = self._police_label.render(indicateur, True, couleur_ind)
            self.fenetre.blit(s, s.get_rect(centerx=cx, y=30))
        else:
            couleur_fin = (255, 220, 50) if "Victoire" in self.resultat_final else (255, 80, 80)
            s = pygame.font.SysFont("segoeui", 34, bold=True).render(
                self.resultat_final, True, couleur_fin)
            self.fenetre.blit(s, s.get_rect(centerx=cx, y=22))
            # Inviter à quitter
            s2 = self._police_info.render("Cliquez sur Quitter pour revenir au menu.",
                                           True, GRIS_CLAIR)
            self.fenetre.blit(s2, s2.get_rect(centerx=cx, y=58))

        # Message bas
        if self.message and not self.partie_finie:
            s = self._police_info.render(self.message, True, (220, 220, 150))
            self.fenetre.blit(s, s.get_rect(centerx=cx, y=h - 105))

        # Log des tirs
        for i, ligne in enumerate(self._log):
            s = self._police_info.render(ligne, True, (170, 200, 170))
            self.fenetre.blit(s, (15, h - 180 + i * 20))

        self.btn_quitter.afficher(self.fenetre)
        self._afficher_legende()

        # Popup par-dessus tout
        if self._popup is not None:
            self._popup.afficher()

    def _afficher_legende(self):
        w, h = self.fenetre.get_size()
        items = [
            ((30,  100, 160), "Eau"),
            ((10,  40,  90),  "Raté"),
            ((220, 60,  60),  "Touché"),
            ((120, 10,  10),  "Coulé"),
        ]
        x, y = w - 130, h - 155
        s = self._police_info.render("Légende :", True, GRIS_CLAIR)
        self.fenetre.blit(s, (x, y - 20))
        for couleur, label in items:
            pygame.draw.rect(self.fenetre, couleur,
                             pygame.Rect(x, y, 18, 18), border_radius=3)
            s = self._police_info.render(label, True, GRIS_CLAIR)
            self.fenetre.blit(s, (x + 24, y + 1))
            y += 26
