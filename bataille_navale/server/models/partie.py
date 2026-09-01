# ============================================================
#  server/models/partie.py  —  Logique d'une partie (côté serveur)
# ============================================================
import uuid
from navire import Navire
from case   import Case
from constantes import NB_LIGNES, NB_COLONNES, NAVIRES_DISPONIBLES


class GrilleServeur:
    """
    Grille logique (pas d'affichage), utilisée côté serveur.
    Stocke l'état réel de toutes les cases.
    """
    def __init__(self):
        # tableau[l][c] = {'etat': ..., 'nom_navire': None}
        self.tableau = [
            [{"etat": Case.ETAT_EAU, "nom_navire": None} for _ in range(NB_COLONNES)]
            for _ in range(NB_LIGNES)
        ]
        self.navires = []

    def case_valide(self, l, c):
        return 0 <= l < NB_LIGNES and 0 <= c < NB_COLONNES

    def placement_possible(self, positions):
        """Vérifie que toutes les positions sont libres et dans la grille."""
        for (l, c) in positions:
            if not self.case_valide(l, c):
                return False
            if self.tableau[l][c]["etat"] == Case.ETAT_NAVIRE:
                return False
        return True

    def placer_navire(self, navire):
        """Pose un navire sur la grille logique."""
        for (l, c) in navire.positions:
            self.tableau[l][c]["etat"]       = Case.ETAT_NAVIRE
            self.tableau[l][c]["nom_navire"] = navire.nom
        self.navires.append(navire)

    def recevoir_tir(self, l, c):
        """
        Traite un tir en (l, c).
        Retourne : "rate" | "touche" | "coule"
        """
        case = self.tableau[l][c]
        if case["etat"] in (Case.ETAT_RATE, Case.ETAT_TOUCHE, Case.ETAT_COULE):
            return "deja_joue"

        # Cherche si un navire est là
        navire_touche = None
        for nav in self.navires:
            if (l, c) in nav.positions:
                navire_touche = nav
                break

        if navire_touche is None:
            case["etat"] = Case.ETAT_RATE
            return "rate"

        navire_touche.recevoir_tir(l, c)
        if navire_touche.est_coule():
            # Marquer toutes les cases du navire en coulé
            for (nl, nc) in navire_touche.positions:
                self.tableau[nl][nc]["etat"] = Case.ETAT_COULE
            return "coule"
        else:
            case["etat"] = Case.ETAT_TOUCHE
            return "touche"

    def tous_navires_coules(self):
        return all(n.est_coule() for n in self.navires)

    def etat_pour_proprietaire(self):
        """Retourne toutes les cases (navires visibles)."""
        cases = []
        for l in range(NB_LIGNES):
            for c in range(NB_COLONNES):
                info = self.tableau[l][c]
                cases.append({
                    "ligne": l, "colonne": c,
                    "etat": info["etat"],
                    "nom_navire": info["nom_navire"]
                })
        return cases

    def etat_pour_ennemi(self):
        """Retourne uniquement les tirs (pas les navires non touchés)."""
        cases = []
        for l in range(NB_LIGNES):
            for c in range(NB_COLONNES):
                info = self.tableau[l][c]
                etat = info["etat"]
                if etat == Case.ETAT_NAVIRE:
                    etat = Case.ETAT_EAU  # cache les navires non touchés
                cases.append({
                    "ligne": l, "colonne": c,
                    "etat": etat,
                    "nom_navire": info["nom_navire"] if etat != Case.ETAT_EAU else None
                })
        return cases

    def vers_dict(self):
        return {
            "tableau":  self.tableau,
            "navires":  [n.vers_dict() for n in self.navires],
        }

    @staticmethod
    def depuis_dict(data):
        g = GrilleServeur()
        g.tableau  = data["tableau"]
        g.navires  = [Navire.depuis_dict(nd) for nd in data["navires"]]
        return g


class Partie:
    """
    Représente une partie côté serveur.
    États : attente | placement | en_cours | terminee | sauvegardee
    """

    ETATS = ("attente", "placement", "en_cours", "terminee", "sauvegardee")

    def __init__(self, nom, createur_pseudo, createur_id):
        self.id            = str(uuid.uuid4())[:8].upper()
        self.nom           = nom
        self.etat          = "attente"

        # Joueurs : liste de dicts {id, pseudo, socket, pret, buffer}
        self.joueurs       = []
        self.grilles       = {}    # joueur_id → GrilleServeur
        self.placement_ok  = {}    # joueur_id → bool

        self.tour_joueur   = None  # id du joueur dont c'est le tour
        self.gagnant       = None

        # Sauvegarde
        self.token_reprise = {}    # joueur_id → token

        # Ajouter le créateur
        self.ajouter_joueur(createur_id, createur_pseudo, None)

    # ----------------------------------------------------------
    #  Gestion des joueurs
    # ----------------------------------------------------------
    def ajouter_joueur(self, joueur_id, pseudo, sock):
        if len(self.joueurs) >= 2:
            return False
        self.joueurs.append({"id": joueur_id, "pseudo": pseudo,
                              "socket": sock, "buffer": ""})
        self.grilles[joueur_id]      = GrilleServeur()
        self.placement_ok[joueur_id] = False
        return True

    def joueur_par_id(self, joueur_id):
        for j in self.joueurs:
            if j["id"] == joueur_id:
                return j
        return None

    def adversaire_id(self, joueur_id):
        for j in self.joueurs:
            if j["id"] != joueur_id:
                return j["id"]
        return None

    def joueur_socket(self, joueur_id):
        j = self.joueur_par_id(joueur_id)
        return j["socket"] if j else None

    def mettre_a_jour_socket(self, joueur_id, sock):
        j = self.joueur_par_id(joueur_id)
        if j:
            j["socket"] = sock

    # ----------------------------------------------------------
    #  Phase placement
    # ----------------------------------------------------------
    def demarrer_placement(self):
        self.etat = "placement"

    def traiter_placement_navire(self, joueur_id, nom_navire, positions):
        """
        Tente de placer le navire.  Retourne (ok, message).
        """
        grille = self.grilles[joueur_id]

        # Trouver la définition du navire
        defn = next((n for n in NAVIRES_DISPONIBLES if n["nom"] == nom_navire), None)
        if defn is None:
            return False, "Navire inconnu"

        # Vérifier qu'il n'est pas déjà placé
        for nav in grille.navires:
            if nav.nom == nom_navire:
                return False, "Navire déjà placé"

        positions_tuples = [tuple(p) for p in positions]
        if not grille.placement_possible(positions_tuples):
            return False, "Placement invalide"

        navire = Navire(nom_navire, defn["forme"])
        navire.positions = positions_tuples
        grille.placer_navire(navire)
        return True, "OK"

    def confirmer_placement(self, joueur_id):
        """Le joueur déclare son placement terminé."""
        grille = self.grilles[joueur_id]
        noms_places = {n.nom for n in grille.navires}
        noms_requis = {n["nom"] for n in NAVIRES_DISPONIBLES}
        if noms_places != noms_requis:
            return False, "Tous les navires ne sont pas placés"
        self.placement_ok[joueur_id] = True
        if all(self.placement_ok.values()):
            self._demarrer_jeu()
        return True, "OK"

    def _demarrer_jeu(self):
        self.etat         = "en_cours"
        self.tour_joueur  = self.joueurs[0]["id"]

    # ----------------------------------------------------------
    #  Phase de jeu
    # ----------------------------------------------------------
    def traiter_tir(self, tireur_id, ligne, colonne):
        """
        Retourne (resultat, nom_navire_coule_ou_None, partie_finie).
        """
        if self.etat != "en_cours":
            return None, None, False
        if self.tour_joueur != tireur_id:
            return None, None, False

        cible_id = self.adversaire_id(tireur_id)
        if cible_id is None:
            return None, None, False

        grille_cible = self.grilles[cible_id]
        resultat     = grille_cible.recevoir_tir(ligne, colonne)
        if resultat == "deja_joue":
            return None, None, False

        nom_coule = None
        if resultat == "coule":
            # Retrouver le nom du navire coulé
            for nav in grille_cible.navires:
                if (ligne, colonne) in nav.positions and nav.est_coule():
                    nom_coule = nav.nom
                    break

        partie_finie = grille_cible.tous_navires_coules()
        if partie_finie:
            self.etat    = "terminee"
            self.gagnant = tireur_id
        else:
            # Changer de tour
            self.tour_joueur = cible_id

        return resultat, nom_coule, partie_finie

    # ----------------------------------------------------------
    #  Sauvegarde / reprise
    # ----------------------------------------------------------
    def sauvegarder(self):
        """
        Passe la partie en état sauvegardé et génère des tokens UNE SEULE FOIS.
        Si des tokens existent déjà, on les réutilise sans les régénérer.
        Retourne un dict {pseudo: token} pour les envoyer aux joueurs.
        """
        import secrets
        self.etat = "sauvegardee"

        # Générer les tokens seulement s'ils n'existent pas encore
        for j in self.joueurs:
            if j["id"] not in self.token_reprise:
                self.token_reprise[j["id"]] = secrets.token_hex(4).upper()

        # Retourner {pseudo: token} pour affichage
        return {j["pseudo"]: self.token_reprise[j["id"]] for j in self.joueurs}

    def reprendre(self, joueur_id, nouveau_sock):
        """Reconnecte un joueur après reprise par token."""
        self.mettre_a_jour_socket(joueur_id, nouveau_sock)

    # ----------------------------------------------------------
    #  Infos publiques (pour la liste des parties)
    # ----------------------------------------------------------
    def infos_publiques(self):
        pseudos = [j["pseudo"] for j in self.joueurs]
        return {
            "id":         self.id,
            "nom":        self.nom,
            "createur":   pseudos[0] if pseudos else "?",
            "etat":       self.etat,
            "nb_joueurs": len(self.joueurs),
            "reprise":    self.etat == "sauvegardee",
        }

    # ----------------------------------------------------------
    #  Sérialisation complète pour sauvegarde fichier
    # ----------------------------------------------------------
    def vers_dict(self):
        return {
            "id":            self.id,
            "nom":           self.nom,
            "etat":          self.etat,
            "joueurs":       [{"id": j["id"], "pseudo": j["pseudo"]} for j in self.joueurs],
            "grilles":       {k: v.vers_dict() for k, v in self.grilles.items()},
            "placement_ok":  self.placement_ok,
            "tour_joueur":   self.tour_joueur,
            "gagnant":       self.gagnant,
            "token_reprise": self.token_reprise,
        }

    @staticmethod
    def depuis_dict(data):
        p = Partie.__new__(Partie)
        p.id           = data["id"]
        p.nom          = data["nom"]
        p.etat         = data["etat"]
        p.joueurs      = [{"id": j["id"], "pseudo": j["pseudo"],
                           "socket": None, "buffer": ""}
                          for j in data["joueurs"]]
        p.grilles      = {k: GrilleServeur.depuis_dict(v) for k, v in data["grilles"].items()}
        p.placement_ok = data["placement_ok"]
        p.tour_joueur  = data["tour_joueur"]
        p.gagnant      = data["gagnant"]
        p.token_reprise = data.get("token_reprise", {})
        return p
