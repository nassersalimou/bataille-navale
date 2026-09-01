# ============================================================
#  navire.py  —  Un navire avec forme personnalisée
# ============================================================
import math


def pivoter_forme(forme, nb_rotations):
    """
    Pivote une forme de 90° × nb_rotations dans le sens horaire.
    Chaque élément est (dl, dc).
    """
    f = list(forme)
    for _ in range(nb_rotations % 4):
        # Rotation 90° horaire : (dl, dc) → (dc, -dl)
        f = [(dc, -dl) for (dl, dc) in f]
    return f


def normaliser_forme(forme):
    """
    Décale la forme pour que le coin supérieur-gauche soit en (0, 0).
    """
    min_l = min(dl for dl, dc in forme)
    min_c = min(dc for dl, dc in forme)
    return [(dl - min_l, dc - min_c) for (dl, dc) in forme]


class Navire:
    """
    Représente un navire avec une forme et une rotation.
    Les positions sont des tuples (ligne, colonne) sur la grille.
    """

    def __init__(self, nom, forme_base):
        self.nom        = nom
        self.forme_base = list(forme_base)  # liste de (dl, dc)
        self.rotation   = 0                 # 0, 1, 2 ou 3 (× 90°)
        self.positions  = []                # cases occupées sur la grille
        self.touches    = set()             # indices dans positions touchés

    # ----------------------------------------------------------
    #  Forme courante (selon rotation)
    # ----------------------------------------------------------
    def forme_courante(self):
        forme = pivoter_forme(self.forme_base, self.rotation)
        return normaliser_forme(forme)

    # ----------------------------------------------------------
    #  Rotation
    # ----------------------------------------------------------
    def pivoter(self):
        self.rotation = (self.rotation + 1) % 4

    # ----------------------------------------------------------
    #  Placement
    # ----------------------------------------------------------
    def calculer_positions(self, ligne_ancre, colonne_ancre):
        """Retourne les positions absolues si ancré en (ligne_ancre, colonne_ancre)."""
        return [
            (ligne_ancre + dl, colonne_ancre + dc)
            for (dl, dc) in self.forme_courante()
        ]

    def placer(self, ligne_ancre, colonne_ancre):
        """Pose le navire : mémorise les positions absolues."""
        self.positions = self.calculer_positions(ligne_ancre, colonne_ancre)

    # ----------------------------------------------------------
    #  Logique touché / coulé
    # ----------------------------------------------------------
    def recevoir_tir(self, ligne, colonne):
        """
        Enregistre un tir sur la case (ligne, colonne).
        Retourne True si touché.
        """
        if (ligne, colonne) in self.positions:
            self.touches.add((ligne, colonne))
            return True
        return False

    def est_coule(self):
        return set(self.positions) == self.touches

    # ----------------------------------------------------------
    #  Sérialisation pour sauvegarde JSON
    # ----------------------------------------------------------
    def vers_dict(self):
        return {
            "nom":       self.nom,
            "forme_base": self.forme_base,
            "rotation":  self.rotation,
            "positions": self.positions,
            "touches":   list(self.touches),
        }

    @staticmethod
    def depuis_dict(data):
        n = Navire(data["nom"], data["forme_base"])
        n.rotation  = data["rotation"]
        n.positions = [tuple(p) for p in data["positions"]]
        n.touches   = {tuple(t) for t in data["touches"]}
        return n

    def __repr__(self):
        return f"Navire({self.nom}, pos={self.positions}, touches={self.touches})"
