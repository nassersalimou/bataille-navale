# ============================================================
#  client/ecrans/ecran_placement.py  —  Phase de placement des navires
# ============================================================
import pygame, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from grille import Grille
from navire import Navire, normaliser_forme, pivoter_forme
from client.ui.widgets import Bouton, dessiner_fond, dessiner_titre, dessiner_message
from constantes import (NAVIRES_DISPONIBLES, COULEURS_NAVIRES, BLANC, GRIS_CLAIR,
                         GRIS_MOYEN, GRIS_FONCE, NOIR, NB_LIGNES, NB_COLONNES,
                         COULEUR_PREVIEW_OK, COULEUR_PREVIEW_KO)


class EcranPlacement:
    """
    Le joueur sélectionne un navire dans la liste de droite,
    voit un aperçu sur la grille, clique pour le poser.
    R = rotation, Entrée = valider quand tout est placé.
    """

    def __init__(self, fenetre, client):
        self.fenetre = fenetre
        self.client  = client
        self.message = ""

        # Grille d'affichage (côté gauche)
        self.grille = Grille(x=60, y=100)

        # Navires à placer (copie de la liste)
        self.navires_a_placer = [dict(n) for n in NAVIRES_DISPONIBLES]
        self.navires_places   = {}   # nom → positions
        self.navire_selectionne = None   # dict du navire en cours
        self.rotation           = 0

        # Boutons
        w, h = fenetre.get_size()
        self.btn_valider = Bouton(w - 230, h - 100, 200, 50,
                                   "Valider ↵", style="vert")
        self.btn_valider.actif = False

        # Police pour la liste des navires
        self._police_nav  = pygame.font.SysFont("segoeui", 18, bold=True)
        self._police_info = pygame.font.SysFont("segoeui", 15)

    # ----------------------------------------------------------
    #  Calcul des positions du navire en cours de placement
    # ----------------------------------------------------------
    def _positions_preview(self, case_ancre):
        if not self.navire_selectionne or not case_ancre:
            return []
        forme = normaliser_forme(pivoter_forme(
            self.navire_selectionne["forme"], self.rotation))
        return [(case_ancre.ligne + dl, case_ancre.colonne + dc) for dl, dc in forme]

    def _placement_valide(self, positions):
        for (l, c) in positions:
            if not (0 <= l < NB_LIGNES and 0 <= c < NB_COLONNES):
                return False
            case = self.grille.case(l, c)
            if case and case.etat == "navire":
                return False
        return True

    # ----------------------------------------------------------
    #  Événements
    # ----------------------------------------------------------
    def gerer_evenements(self, events):
        """Retourne 'valide' | None."""
        mx, my = pygame.mouse.get_pos()
        case_survol = self.grille.clic_vers_case(mx, my)

        # Mise à jour de la preview
        self.grille.effacer_preview()
        if self.navire_selectionne and case_survol:
            positions = self._positions_preview(case_survol)
            valide    = self._placement_valide(positions)
            self.grille.afficher_preview(positions, valide)

        for event in events:
            # Rotation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.rotation = (self.rotation + 1) % 4
                if event.key == pygame.K_RETURN:
                    if len(self.navires_places) == len(NAVIRES_DISPONIBLES):
                        return self._envoyer_placement()

            # Clic sur la grille → poser le navire
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.navire_selectionne and case_survol:
                    positions = self._positions_preview(case_survol)
                    if self._placement_valide(positions):
                        self._poser_navire(positions)
                    else:
                        self.message = "Placement invalide !"
                else:
                    # Clic sur la liste des navires ?
                    self._clic_liste_navires(event.pos)

            if self.btn_valider.gerer_evenement(event):
                return self._envoyer_placement()

        return None

    def _clic_liste_navires(self, pos):
        w = self.fenetre.get_width()
        x_liste = w - 270
        for i, nav in enumerate(self.navires_a_placer):
            rect = pygame.Rect(x_liste, 130 + i * 80, 240, 68)
            if rect.collidepoint(pos):
                if nav["nom"] not in self.navires_places:
                    self.navire_selectionne = nav
                    self.rotation = 0
                    self.message  = f"Navire sélectionné : {nav['nom']}  (R = tourner)"
                return

    def _poser_navire(self, positions):
        nom = self.navire_selectionne["nom"]
        self.navires_places[nom] = positions
        # Colorer les cases
        for (l, c) in positions:
            case = self.grille.case(l, c)
            if case:
                case.etat       = "navire"
                case.nom_navire = nom
        self.navire_selectionne = None
        self.grille.effacer_preview()
        self.message = f"{nom} placé !"
        if len(self.navires_places) == len(NAVIRES_DISPONIBLES):
            self.btn_valider.actif = True
            self.message = "Tous les navires placés ! Appuyez sur Valider."

    def _envoyer_placement(self):
        if len(self.navires_places) < len(NAVIRES_DISPONIBLES):
            self.message = "Placez tous vos navires avant de valider."
            return None
        for nom, positions in self.navires_places.items():
            self.client.envoyer("placer_navire", nom_navire=nom,
                                 positions=[[l, c] for l, c in positions])
        self.client.envoyer("placement_termine")
        return "valide"

    # ----------------------------------------------------------
    #  Affichage
    # ----------------------------------------------------------
    def afficher(self):
        dessiner_fond(self.fenetre)
        w, h = self.fenetre.get_size()

        dessiner_titre(self.fenetre, "Placez vos navires", 30, taille=32)
        dessiner_message(self.fenetre,
                         "Cliquez sur un navire → cliquez sur la grille  |  R = rotation",
                         68, taille=16)

        # Étiquettes de grille
        police_etiq = pygame.font.SysFont("segoeui", 14)
        self.grille.afficher_etiquettes(self.fenetre, police_etiq)
        self.grille.afficher(self.fenetre)

        # Liste des navires (droite)
        x_liste = w - 270
        dessiner_message(self.fenetre, "Navires à placer", x_liste + 120, taille=18)
        # réutilisation de dessiner_message pour le titre de colonne
        s = self._police_nav.render("Navires à placer :", True, (200, 220, 255))
        self.fenetre.blit(s, (x_liste, 105))

        for i, nav in enumerate(self.navires_a_placer):
            nom    = nav["nom"]
            place  = nom in self.navires_places
            selec  = (self.navire_selectionne and
                      self.navire_selectionne["nom"] == nom)
            rect   = pygame.Rect(x_liste, 130 + i * 80, 240, 68)

            if place:
                couleur_fond = (30, 70, 30)
                couleur_texte = (100, 200, 100)
            elif selec:
                couleur_fond = (60, 80, 140)
                couleur_texte = BLANC
            else:
                couleur_fond = GRIS_FONCE
                couleur_texte = BLANC

            pygame.draw.rect(self.fenetre, couleur_fond, rect, border_radius=7)
            pygame.draw.rect(self.fenetre, COULEURS_NAVIRES.get(nom, (150,150,150)),
                             rect, 3, border_radius=7)

            s1 = self._police_nav.render(nom, True, couleur_texte)
            taille = nav["taille"]
            s2 = self._police_info.render(
                f"Taille : {taille}  {'✓ Placé' if place else ''}", True,
                (100, 200, 100) if place else GRIS_CLAIR)
            self.fenetre.blit(s1, (rect.x + 8, rect.y + 8))
            self.fenetre.blit(s2, (rect.x + 8, rect.y + 36))

            # Mini-aperçu de la forme
            self._dessiner_forme_mini(nav["forme"], rect.x + 170, rect.y + 8,
                                       COULEURS_NAVIRES.get(nom, (150,150,150)))

        self.btn_valider.afficher(self.fenetre)

        if self.message:
            dessiner_message(self.fenetre, self.message, h - 50,
                             couleur=(255, 220, 100), taille=17)

    def _dessiner_forme_mini(self, forme, x, y, couleur):
        """Dessine un mini-aperçu de la forme du navire."""
        taille = 9
        for (dl, dc) in forme:
            px = x + dc * (taille + 1)
            py = y + dl * (taille + 1)
            pygame.draw.rect(self.fenetre, couleur,
                             pygame.Rect(px, py, taille, taille))
