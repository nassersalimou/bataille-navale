# ============================================================
#  case.py  —  Une case individuelle de la grille
# ============================================================
import pygame
from constantes import (
    COULEUR_EAU, COULEUR_SURVOL, COULEUR_RATE,
    COULEUR_TOUCHE, COULEUR_COULE, COULEURS_NAVIRES,
    COULEUR_PREVIEW_OK, COULEUR_PREVIEW_KO, NOIR
)


class Case:
    """Représente une case de la grille de bataille navale."""

    # États possibles d'une case
    ETAT_EAU      = "eau"       # vide, non visée
    ETAT_NAVIRE   = "navire"    # contient un navire (visible seulement sur grille joueur)
    ETAT_RATE     = "rate"      # tir raté
    ETAT_TOUCHE   = "touche"    # tir touché
    ETAT_COULE    = "coule"     # navire coulé (toutes ses cases)

    def __init__(self, ligne, colonne, x, y, taille):
        self.ligne   = ligne
        self.colonne = colonne
        self.x       = x
        self.y       = y
        self.taille  = taille

        self.etat          = Case.ETAT_EAU
        self.nom_navire    = None    # nom du navire posé dessus (si applicable)
        self.en_survol     = False
        self.preview       = None    # None | "ok" | "ko"

    # ----------------------------------------------------------
    #  Couleur à afficher selon l'état
    # ----------------------------------------------------------
    def _couleur_affichage(self):
        if self.preview == "ok":
            return COULEUR_PREVIEW_OK
        if self.preview == "ko":
            return COULEUR_PREVIEW_KO
        if self.en_survol and self.etat == Case.ETAT_EAU:
            return COULEUR_SURVOL
        if self.etat == Case.ETAT_NAVIRE and self.nom_navire:
            return COULEURS_NAVIRES.get(self.nom_navire, (150, 150, 150))
        if self.etat == Case.ETAT_RATE:
            return COULEUR_RATE
        if self.etat == Case.ETAT_TOUCHE:
            return COULEUR_TOUCHE
        if self.etat == Case.ETAT_COULE:
            return COULEUR_COULE
        return COULEUR_EAU

    # ----------------------------------------------------------
    #  Affichage
    # ----------------------------------------------------------
    def afficher(self, fenetre):
        couleur = self._couleur_affichage()
        rect = pygame.Rect(self.x, self.y, self.taille, self.taille)
        pygame.draw.rect(fenetre, couleur, rect)
        pygame.draw.rect(fenetre, NOIR, rect, 1)

    # ----------------------------------------------------------
    #  Utilitaires
    # ----------------------------------------------------------
    def contient_point(self, mx, my):
        return self.x <= mx < self.x + self.taille and self.y <= my < self.y + self.taille

    def reinitialiser_preview(self):
        self.preview  = None
        self.en_survol = False

    def __repr__(self):
        return f"Case({self.ligne},{self.colonne},{self.etat})"
