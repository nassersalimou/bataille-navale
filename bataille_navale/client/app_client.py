# ============================================================
#  client/app_client.py  —  Orchestre les écrans et les messages réseau
# ============================================================
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client_reseau import ClientReseau
from client.ecrans.ecran_connexion  import EcranConnexion
from client.ecrans.ecran_principal  import EcranPrincipal
from client.ecrans.ecran_creer      import EcranCreerPartie
from client.ecrans.ecran_attente    import EcranAttente
from client.ecrans.ecran_rejoindre  import EcranRejoindrePartie
from client.ecrans.ecran_reprendre  import EcranReprendrePartie
from client.ecrans.ecran_placement  import EcranPlacement
from client.ecrans.ecran_partie     import EcranPartie
from constantes import LARGEUR, HAUTEUR, FPS, TITRE, PORT_DEFAUT
import protocole as proto


class AppClient:
    """
    Boucle principale Pygame.
    Gère le changement d'écrans et les messages reçus du serveur.
    """

    def __init__(self, pseudo_arg=None):
        pygame.init()
        self.fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
        pygame.display.set_caption(TITRE)
        self.clock   = pygame.time.Clock()

        self.reseau  = ClientReseau()
        self._pseudo = pseudo_arg or ""
        self._derniere_ip   = "127.0.0.1"
        self._dernier_port  = PORT_DEFAUT
        self._reinitialiser_etat_partie()

        # Écrans
        self.ecran_actuel = None
        self._aller_connexion()

    def _reinitialiser_etat_partie(self):
        """Remet à zéro tous les infos liés à une partie en cours.
        Appelé à chaque retour au menu principal."""
        self._partie_id  = None
        self._nom_partie = None
        self._mon_id     = None
        self._pseudo_adv = "Adversaire"

    # ----------------------------------------------------------
    #  Transitions d'écrans
    # ----------------------------------------------------------
    def _aller_connexion(self):
        ec = EcranConnexion(self.fenetre)
        if self._pseudo:
            ec.champ_pseudo.texte = self._pseudo
        self.ecran_actuel = ("connexion", ec)

    def _aller_principal(self):
        self._reinitialiser_etat_partie()
        # Vider la file de messages résiduels pour éviter les fantômes
        self.reseau.lire_messages()
        # Si le socket a été fermé côté serveur (ex: après sauvegarder_et_quitter),
        # on se reconnecte automatiquement avec le même pseudo et la même IP/port
        if not self.reseau.connecte:
            ok = self.reseau.connecter(self._derniere_ip, self._dernier_port)
            if ok:
                self.reseau.envoyer("pseudo", pseudo=self._pseudo)
        self.ecran_actuel = ("principal", EcranPrincipal(self.fenetre, self))

    def _aller_creer(self):
        self.ecran_actuel = ("creer", EcranCreerPartie(self.fenetre, self))

    def _aller_attente(self, nom_partie, partie_id):
        self._nom_partie = nom_partie
        self._partie_id  = partie_id
        self.ecran_actuel = ("attente", EcranAttente(self.fenetre, self,
                                                      nom_partie, partie_id))

    def _aller_rejoindre(self):
        self.ecran_actuel = ("rejoindre", EcranRejoindrePartie(self.fenetre, self))

    def _aller_reprendre(self):
        self.ecran_actuel = ("reprendre", EcranReprendrePartie(self.fenetre, self))

    def _aller_placement(self):
        self.ecran_actuel = ("placement", EcranPlacement(self.fenetre, self))

    def _aller_partie(self, pseudo_adv):
        self._pseudo_adv  = pseudo_adv
        ec = EcranPartie(self.fenetre, self, self._pseudo, pseudo_adv)
        self.ecran_actuel = ("partie", ec)
        return ec

    # ----------------------------------------------------------
    #  Envoi vers le serveur (proxy pratique)
    # ----------------------------------------------------------
    def envoyer(self, type_msg, **champs):
        self.reseau.envoyer(type_msg, **champs)

    # ----------------------------------------------------------
    #  Traitement des messages reçus du serveur
    # ----------------------------------------------------------
    def _traiter_messages_serveur(self):
        for msg in self.reseau.lire_messages():
            t = msg.get("type")
            nom_ecran, ecran = self.ecran_actuel

            # --- Déconnexion réseau ---
            if t == "deconnexion_serveur":
                if hasattr(ecran, "message"):
                    ecran.message = "Connexion perdue avec le serveur."

            # --- Accusé de réception simple ---
            elif t == proto.MSG_ACK:
                pass

            # --- Erreur serveur ---
            elif t == proto.MSG_ERREUR:
                if hasattr(ecran, "message"):
                    ecran.message = msg.get("message", "Erreur inconnue")

            # --- Liste des parties ---
            elif t == proto.MSG_PARTIES:
                if nom_ecran == "rejoindre":
                    ecran.mettre_a_jour_liste(msg.get("parties", []))
                    ecran.message = ""

            # --- Partie créée (créateur attend) ---
            elif t == proto.MSG_PARTIE_CREE:
                self._aller_attente(msg.get("nom", "?"), msg.get("partie_id", "?"))

            # --- Deux joueurs présents → phase placement ---
            elif t == proto.MSG_DEBUT_PARTIE:
                self._mon_id    = msg.get("votre_id")
                pseudos         = msg.get("pseudos", [])
                self._pseudo_adv = next(
                    (p for p in pseudos if p != self._pseudo), "Adversaire")
                self._partie_id  = msg.get("partie_id")
                self._aller_placement()

            # --- Mise à jour des grilles ---
            elif t == proto.MSG_ETAT_GRILLE:
                if nom_ecran == "partie":
                    ecran.appliquer_etat_grille(
                        msg.get("type_grille", "propre"),
                        msg.get("cases", []))

            # --- Changement de tour ---
            elif t == proto.MSG_TOUR:
                if nom_ecran == "placement":
                    # Les deux placements sont terminés → lancer la partie
                    ec_partie = self._aller_partie(self._pseudo_adv)
                    ec_partie.set_tour(msg.get("votre_tour", False))
                    nom_ecran, ecran = self.ecran_actuel
                elif nom_ecran == "partie":
                    ecran.set_tour(msg.get("votre_tour", False))

            # --- Résultat d'un tir ---
            elif t == proto.MSG_RESULTAT_TIR:
                if nom_ecran == "partie":
                    tireur     = msg.get("tireur_id")
                    l, c       = msg.get("ligne"), msg.get("colonne")
                    res        = msg.get("resultat", "")
                    coule      = msg.get("nom_coule")
                    lettres    = "ABCDEFGHIJ"
                    col_lettre = lettres[c] if 0 <= c < 10 else str(c)
                    if tireur == self._mon_id:
                        texte_log = f"Vous → {col_lettre}{l+1} : {res.upper()}"
                    else:
                        texte_log = f"Ennemi → {col_lettre}{l+1} : {res.upper()}"
                    if coule:
                        texte_log += f" ({coule} coulé !)"
                    ecran.ajouter_log(texte_log)

            # --- Fin de partie ---
            elif t == proto.MSG_FIN_PARTIE:
                if nom_ecran == "partie":
                    ecran.fin_partie(msg.get("gagne", False))

            # --- Reprise confirmée par le serveur ---
            elif t == proto.MSG_REPRISE_OK:
                self._mon_id     = msg.get("votre_id")
                self._partie_id  = msg.get("partie_id")
                self._pseudo_adv = msg.get("pseudo_adverse", "Adversaire") or "Adversaire"
                etat = msg.get("etat", "")
                if etat == "en_cours":
                    ec_partie = self._aller_partie(self._pseudo_adv)
                    # Les grilles et le tour arrivent juste après dans d'autres messages
                else:
                    # Attendre le 2e joueur avec son token
                    self._aller_attente("Reprise en attente…", self._partie_id)

            # --- Sauvegarde confirmée (token à afficher dans la popup) ---
            elif t == proto.MSG_SAUVEGARDE_OK:
                if nom_ecran == "partie":
                    token = msg.get("token", "?")
                    ecran.recevoir_token_sauvegarde(token)

            # --- Adversaire déconnecté ---
            elif t == proto.MSG_ADVERSAIRE_DECONNECTE:
                token = msg.get("token", "?")
                if hasattr(ecran, "message"):
                    ecran.message = (f"Adversaire déconnecté — "
                                     f"Votre token de reprise : {token}")

    # ----------------------------------------------------------
    #  Boucle principale
    # ----------------------------------------------------------
    def lancer(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    if self.reseau.connecte:
                        self.reseau.envoyer(proto.MSG_QUITTER)
                    pygame.quit()
                    sys.exit()

            # Messages réseau
            self._traiter_messages_serveur()

            nom_ecran, ecran = self.ecran_actuel

            # --- Connexion ---
            if nom_ecran == "connexion":
                res = ecran.gerer_evenements(events)
                if res:
                    if res[0] == "quitter":
                        pygame.quit(); sys.exit()
                    elif res[0] == "connecter":
                        _, pseudo, ip, port = res
                        self._pseudo        = pseudo
                        self._derniere_ip   = ip
                        self._dernier_port  = port
                        ok = self.reseau.connecter(ip, port)
                        if ok:
                            self.reseau.envoyer(proto.MSG_PSEUDO, pseudo=pseudo)
                            self._aller_principal()
                        else:
                            ecran.message = f"Impossible de se connecter à {ip}:{port}"

            # --- Menu principal ---
            elif nom_ecran == "principal":
                res = ecran.gerer_evenements(events)
                if res == "creer":
                    self._aller_creer()
                elif res == "rejoindre":
                    self._aller_rejoindre()
                elif res == "reprendre":
                    self._aller_reprendre()
                elif res == "quitter":
                    pygame.quit(); sys.exit()

            # --- Créer une partie ---
            elif nom_ecran == "creer":
                res = ecran.gerer_evenements(events)
                if res == "retour":
                    self._aller_principal()

            # --- Attente adversaire ---
            elif nom_ecran == "attente":
                res = ecran.gerer_evenements(events)
                if res == "quitter":
                    self.reseau.envoyer(proto.MSG_QUITTER)
                    self._aller_principal()

            # --- Rejoindre ---
            elif nom_ecran == "rejoindre":
                res = ecran.gerer_evenements(events)
                if res == "retour":
                    self._aller_principal()

            # --- Reprendre ---
            elif nom_ecran == "reprendre":
                res = ecran.gerer_evenements(events)
                if res == "retour":
                    self._aller_principal()

            # --- Placement ---
            elif nom_ecran == "placement":
                ecran.gerer_evenements(events)

            # --- Partie ---
            elif nom_ecran == "partie":
                res = ecran.gerer_evenements(events)
                if res == "quitter":
                    # Quitter sans sauvegarde (ou partie déjà terminée)
                    self.reseau.envoyer(proto.MSG_QUITTER)
                    self._aller_principal()
                elif res == "quitter_save":
                    # La sauvegarde a déjà été traitée côté serveur
                    # (MSG_SAUVEGARDER_ET_QUITTER a fermé le socket serveur)
                    # On se reconnecte si le socket est fermé, sinon on passe
                    self._aller_principal()

            # Rendu
            ecran.afficher()
            pygame.display.flip()
            self.clock.tick(FPS)
