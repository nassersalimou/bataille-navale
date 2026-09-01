# ============================================================
#  constantes.py  —  Toutes les valeurs fixes du projet
# ============================================================

# --- Réseau ---
IP_DEFAUT   = "127.0.0.1"
PORT_DEFAUT = 5050

# --- Fenêtre ---
LARGEUR  = 1200
HAUTEUR  = 750
FPS      = 60
TITRE    = "Bataille Navale"

# --- Grille ---
NB_LIGNES   = 10
NB_COLONNES = 10
TAILLE_CASE = 38

# --- Couleurs des cases ---
COULEUR_EAU        = (30,  100, 160)   # bleu mer normal
COULEUR_SURVOL     = (255, 255, 100)   # jaune au survol
COULEUR_RATE       = (10,  40,  90)    # bleu très foncé
COULEUR_TOUCHE     = (220, 60,  60)    # rouge clair
COULEUR_COULE      = (120, 10,  10)    # rouge sombre
COULEUR_PREVIEW_OK = (100, 220, 100)   # vert prévisualisation valide
COULEUR_PREVIEW_KO = (220, 80,  80)    # rouge prévisualisation invalide

# --- Couleurs interface ---
NOIR          = (0,   0,   0)
BLANC         = (255, 255, 255)
GRIS_FONCE    = (30,  30,  30)
GRIS_MOYEN    = (70,  70,  70)
GRIS_CLAIR    = (180, 180, 180)
BLEU_MARINE   = (10,  20,  50)
BLEU_BOUTON   = (30,  80,  160)
VERT_BOUTON   = (40,  140, 60)
ROUGE_BOUTON  = (160, 40,  40)
ORANGE_BOUTON = (180, 100, 20)

# --- Couleurs par type de navire ---
COULEURS_NAVIRES = {
    "Patrouilleur":  (100, 200, 120),  # vert clair
    "Sous-marin":    (160, 100, 200),  # violet
    "Croiseur":      (200, 170, 60),   # or
    "Destroyer":     (80,  160, 200),  # bleu ciel
    "Porte-avions":  (200, 100, 60),   # orange
}

# --- Définition des navires (nom, forme en coordonnées relatives, couleur) ---
# Chaque forme est une liste de (dl, dc) par rapport à la case d'ancrage
NAVIRES_DISPONIBLES = [
    {
        "nom":   "Patrouilleur",
        "forme": [(0, 0), (0, 1)],          # droit 2 cases
        "taille": 2,
    },
    {
        "nom":   "Sous-marin",
        "forme": [(0, 0), (0, 1), (0, 2)],  # droit 3 cases
        "taille": 3,
    },
    {
        "nom":   "Croiseur",
        "forme": [(0, 0), (0, 1), (0, 2), (0, 3)],  # droit 4 cases
        "taille": 4,
    },
    {
        "nom":   "Destroyer",
        # Forme en L : 3 cases droites + 1 en bas à droite
        "forme": [(0, 0), (0, 1), (0, 2), (1, 2)],
        "taille": 4,
    },
    {
        "nom":   "Porte-avions",
        # Forme en T : 3 cases droites + 1 en haut au centre + 1 en bas au centre
        "forme": [(0, 0), (0, 1), (0, 2), (1, 1), (-1, 1)],
        "taille": 5,
    },
]

# --- Rotations possibles (multiples de 90°) ---
NB_ROTATIONS = 4

# --- Touches clavier ---
TOUCHE_ROTATION  = "r"      # rotate navire
TOUCHE_VALIDER   = "return" # valider placement complet
TOUCHE_RETOUR    = "escape" # retour écran précédent
