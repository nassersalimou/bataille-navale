# ============================================================
#  client/ui/widgets.py  —  Composants graphiques Pygame
# ============================================================
import pygame
from constantes import (
    BLANC, NOIR, GRIS_FONCE, GRIS_MOYEN, GRIS_CLAIR,
    BLEU_BOUTON, VERT_BOUTON, ROUGE_BOUTON, ORANGE_BOUTON
)

COULEURS_STYLE = {
    "bleu":   (BLEU_BOUTON,   (60, 120, 200), BLANC),
    "vert":   (VERT_BOUTON,   (70, 180,  90), BLANC),
    "rouge":  (ROUGE_BOUTON,  (200, 60,  60), BLANC),
    "orange": (ORANGE_BOUTON, (220, 140, 40), BLANC),
    "gris":   (GRIS_MOYEN,    (100, 100, 100), BLANC),
}


class Bouton:
    """Bouton cliquable avec texte."""

    def __init__(self, x, y, largeur, hauteur, texte,
                 style="bleu", taille_police=22):
        self.rect         = pygame.Rect(x, y, largeur, hauteur)
        self.texte        = texte
        self.style        = style
        self.taille_police = taille_police
        self._police      = None
        self.survol       = False
        self.actif        = True

    def _get_police(self):
        if self._police is None:
            self._police = pygame.font.SysFont("segoeui", self.taille_police, bold=True)
        return self._police

    def gerer_evenement(self, event):
        """Retourne True si le bouton est cliqué."""
        if not self.actif:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.survol = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def afficher(self, fenetre):
        couleur_base, couleur_survol, couleur_texte = COULEURS_STYLE.get(
            self.style, COULEURS_STYLE["bleu"])
        couleur = couleur_survol if self.survol else couleur_base
        if not self.actif:
            couleur = (60, 60, 60)

        pygame.draw.rect(fenetre, couleur, self.rect, border_radius=8)
        pygame.draw.rect(fenetre, BLANC, self.rect, 2, border_radius=8)

        police = self._get_police()
        surf   = police.render(self.texte, True, couleur_texte if self.actif else GRIS_CLAIR)
        fenetre.blit(surf, surf.get_rect(center=self.rect.center))


class ChampTexte:
    """Champ de saisie texte simple."""

    def __init__(self, x, y, largeur, hauteur, placeholder="", max_chars=30):
        self.rect        = pygame.Rect(x, y, largeur, hauteur)
        self.placeholder = placeholder
        self.max_chars   = max_chars
        self.texte       = ""
        self.actif       = False
        self._police     = None

    def _get_police(self):
        if self._police is None:
            self._police = pygame.font.SysFont("segoeui", 22)
        return self._police

    def gerer_evenement(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.actif = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.actif:
            if event.key == pygame.K_BACKSPACE:
                self.texte = self.texte[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                if len(self.texte) < self.max_chars:
                    self.texte += event.unicode

    def afficher(self, fenetre):
        couleur_bord = BLANC if self.actif else GRIS_MOYEN
        pygame.draw.rect(fenetre, GRIS_FONCE, self.rect, border_radius=6)
        pygame.draw.rect(fenetre, couleur_bord, self.rect, 2, border_radius=6)

        police = self._get_police()
        if self.texte:
            surf = police.render(self.texte, True, BLANC)
        else:
            surf = police.render(self.placeholder, True, GRIS_CLAIR)
        fenetre.blit(surf, (self.rect.x + 8, self.rect.y + self.rect.height // 2 - surf.get_height() // 2))

        # Curseur clignotant
        if self.actif and pygame.time.get_ticks() % 1000 < 500:
            cx = self.rect.x + 8 + police.size(self.texte)[0]
            cy = self.rect.y + 6
            pygame.draw.line(fenetre, BLANC, (cx, cy), (cx, cy + self.rect.height - 12), 2)


class ListeParties:
    """Affiche une liste scrollable de parties disponibles."""

    def __init__(self, x, y, largeur, hauteur):
        self.rect          = pygame.Rect(x, y, largeur, hauteur)
        self.parties       = []
        self.selection     = None
        self._police_titre = None
        self._police_info  = None
        self.scroll        = 0
        self.hauteur_ligne = 72

    def _get_polices(self):
        if self._police_titre is None:
            self._police_titre = pygame.font.SysFont("segoeui", 19, bold=True)
            self._police_info  = pygame.font.SysFont("segoeui", 15)

    def mettre_a_jour(self, parties):
        self.parties   = parties
        self.selection = None

    def gerer_evenement(self, event):
        """Retourne la partie sélectionnée ou None."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                idx = (event.pos[1] - self.rect.y + self.scroll) // self.hauteur_ligne
                if 0 <= idx < len(self.parties):
                    self.selection = idx
                    return self.parties[idx]
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll = max(0, self.scroll - event.y * 20)
        return None

    def afficher(self, fenetre):
        self._get_polices()
        pygame.draw.rect(fenetre, GRIS_FONCE, self.rect, border_radius=8)
        pygame.draw.rect(fenetre, GRIS_MOYEN, self.rect, 2, border_radius=8)

        clip = fenetre.get_clip()
        fenetre.set_clip(self.rect)

        for i, p in enumerate(self.parties):
            ry = self.rect.y + i * self.hauteur_ligne - self.scroll
            if ry + self.hauteur_ligne < self.rect.y:
                continue
            if ry > self.rect.bottom:
                break

            rect_ligne = pygame.Rect(self.rect.x + 4, ry + 2,
                                     self.rect.width - 8, self.hauteur_ligne - 4)
            couleur_fond = (50, 80, 120) if self.selection == i else (40, 55, 80)
            pygame.draw.rect(fenetre, couleur_fond, rect_ligne, border_radius=6)

            # Titre
            nom     = p.get("nom", "?")
            createur = p.get("createur", "?")
            etat    = p.get("etat", "?")
            nb_j    = p.get("nb_joueurs", 0)
            reprise = p.get("reprise", False)

            etiquette_etat = "🔄 À REPRENDRE" if reprise else ("⏳ EN ATTENTE" if etat == "attente" else etat.upper())
            couleur_etat   = (255, 200, 50) if reprise else (100, 220, 100)

            s1 = self._police_titre.render(f"{nom}", True, BLANC)
            s2 = self._police_info.render(f"Par {createur}  —  {nb_j}/2 joueur(s)", True, GRIS_CLAIR)
            s3 = self._police_info.render(etiquette_etat, True, couleur_etat)

            fenetre.blit(s1, (rect_ligne.x + 10, rect_ligne.y + 6))
            fenetre.blit(s2, (rect_ligne.x + 10, rect_ligne.y + 28))
            fenetre.blit(s3, (rect_ligne.x + 10, rect_ligne.y + 48))

        fenetre.set_clip(clip)


def dessiner_titre(fenetre, texte, y, couleur=BLANC, taille=42):
    police = pygame.font.SysFont("segoeui", taille, bold=True)
    surf   = police.render(texte, True, couleur)
    fenetre.blit(surf, surf.get_rect(centerx=fenetre.get_width() // 2, y=y))


def dessiner_message(fenetre, texte, y, couleur=GRIS_CLAIR, taille=20):
    police = pygame.font.SysFont("segoeui", taille)
    surf   = police.render(texte, True, couleur)
    fenetre.blit(surf, surf.get_rect(centerx=fenetre.get_width() // 2, y=y))


def dessiner_fond(fenetre):
    """Fond dégradé bleu marine."""
    w, h = fenetre.get_size()
    for y in range(h):
        t   = y / h
        r   = int(5  + t * 15)
        g   = int(10 + t * 25)
        b   = int(40 + t * 60)
        pygame.draw.line(fenetre, (r, g, b), (0, y), (w, y))
