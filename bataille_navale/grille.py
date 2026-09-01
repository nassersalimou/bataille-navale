# ============================================================
#  grille.py  —  Grille de jeu composée de cases
# ============================================================
import pygame
from case import Case
from constantes import NB_LIGNES, NB_COLONNES, TAILLE_CASE


class Grille:
    """
    Grille de bataille navale.
    Peut représenter la grille du joueur (avec ses navires visibles)
    ou la grille ennemie (tirs uniquement).
    """

    def __init__(self, x, y, nb_lignes=NB_LIGNES, nb_colonnes=NB_COLONNES,
                 taille_case=TAILLE_CASE):
        self.x           = x
        self.y           = y
        self.nb_lignes   = nb_lignes
        self.nb_colonnes = nb_colonnes
        self.taille_case = taille_case
        self.tableau     = []
        self._creer_grille()

    # ----------------------------------------------------------
    #  Construction
    # ----------------------------------------------------------
    def _creer_grille(self):
        self.tableau = []
        for l in range(self.nb_lignes):
            ligne_cases = []
            for c in range(self.nb_colonnes):
                px = self.x + c * self.taille_case
                py = self.y + l * self.taille_case
                ligne_cases.append(Case(l, c, px, py, self.taille_case))
            self.tableau.append(ligne_cases)

    # ----------------------------------------------------------
    #  Accès
    # ----------------------------------------------------------
    def case(self, ligne, colonne):
        if 0 <= ligne < self.nb_lignes and 0 <= colonne < self.nb_colonnes:
            return self.tableau[ligne][colonne]
        return None

    def clic_vers_case(self, mx, my):
        if mx < self.x or my < self.y:
            return None
        c = (mx - self.x) // self.taille_case
        l = (my - self.y) // self.taille_case
        return self.case(int(l), int(c))

    # ----------------------------------------------------------
    #  Survol souris (pour la grille ennemie)
    # ----------------------------------------------------------
    def mettre_a_jour_survol(self, mx, my):
        for ligne in self.tableau:
            for case in ligne:
                case.en_survol = case.contient_point(mx, my) and case.etat == Case.ETAT_EAU

    # ----------------------------------------------------------
    #  Prévisualisation du placement
    # ----------------------------------------------------------
    def afficher_preview(self, positions, valide):
        """Colore les cases de preview selon validité."""
        etat = "ok" if valide else "ko"
        for (l, c) in positions:
            case = self.case(l, c)
            if case:
                case.preview = etat

    def effacer_preview(self):
        for ligne in self.tableau:
            for case in ligne:
                case.preview = None

    # ----------------------------------------------------------
    #  Affichage
    # ----------------------------------------------------------
    def afficher(self, fenetre):
        for ligne in self.tableau:
            for case in ligne:
                case.afficher(fenetre)

    def afficher_etiquettes(self, fenetre, police):
        """Affiche les lettres (colonnes) et chiffres (lignes) autour de la grille."""
        lettres = "ABCDEFGHIJ"
        couleur = (200, 220, 255)
        for c in range(self.nb_colonnes):
            texte = police.render(lettres[c], True, couleur)
            fx = self.x + c * self.taille_case + self.taille_case // 2 - texte.get_width() // 2
            fy = self.y - 20
            fenetre.blit(texte, (fx, fy))
        for l in range(self.nb_lignes):
            texte = police.render(str(l + 1), True, couleur)
            fx = self.x - 20
            fy = self.y + l * self.taille_case + self.taille_case // 2 - texte.get_height() // 2
            fenetre.blit(texte, (fx, fy))

    # ----------------------------------------------------------
    #  Mise à jour depuis les données serveur
    # ----------------------------------------------------------
    def appliquer_etat(self, cases_etat):
        """
        cases_etat : liste de dicts {'ligne', 'colonne', 'etat', 'nom_navire'}
        envoyée par le serveur.
        """
        for info in cases_etat:
            case = self.case(info["ligne"], info["colonne"])
            if case:
                case.etat       = info["etat"]
                case.nom_navire = info.get("nom_navire")

    # ----------------------------------------------------------
    #  Largeur / hauteur totale (utile pour le layout)
    # ----------------------------------------------------------
    @property
    def largeur(self):
        return self.nb_colonnes * self.taille_case

    @property
    def hauteur(self):
        return self.nb_lignes * self.taille_case
