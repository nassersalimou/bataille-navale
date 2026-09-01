# ============================================================
#  server/serveur.py  —  Serveur TCP autoritaire
# ============================================================
import socket
import threading
import sys
import os
import uuid

# Ajoute la racine du projet dans le path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import protocole as proto
from server.models.partie import Partie
from server.persistence.sauvegarde import (
    sauvegarder_partie, charger_partie,
    lister_parties_sauvegardees, supprimer_sauvegarde
)
from constantes import IP_DEFAUT, PORT_DEFAUT


class Serveur:
    """
    Serveur TCP multi-clients.
    Chaque client tourne dans son propre thread.
    Le serveur est le seul maître du jeu.
    """

    def __init__(self, ip=IP_DEFAUT, port=PORT_DEFAUT):
        self.ip      = ip
        self.port    = port
        self.parties = {}          # partie_id → Partie
        self.sessions = {}         # joueur_id → dict info
        self.verrou   = threading.Lock()
        self._charger_parties_sauvegardees()

    # ----------------------------------------------------------
    #  Démarrage
    # ----------------------------------------------------------
    def demarrer(self):
        srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv_sock.bind((self.ip, self.port))
        srv_sock.listen(10)
        print(f"[SERVEUR] En écoute sur {self.ip}:{self.port}")
        while True:
            try:
                conn, addr = srv_sock.accept()
                print(f"[SERVEUR] Nouveau client : {addr}")
                t = threading.Thread(target=self._gerer_client,
                                     args=(conn,), daemon=True)
                t.start()
            except KeyboardInterrupt:
                break
        srv_sock.close()

    # ----------------------------------------------------------
    #  Chargement des sauvegardes au démarrage
    # ----------------------------------------------------------
    def _charger_parties_sauvegardees(self):
        for pid in lister_parties_sauvegardees():
            partie = charger_partie(pid)
            if partie:
                self.parties[partie.id] = partie
                print(f"[SERVEUR] Partie sauvegardée chargée : {partie.id}")

    # ----------------------------------------------------------
    #  Boucle client dans son thread
    # ----------------------------------------------------------
    def _gerer_client(self, sock):
        joueur_id = str(uuid.uuid4())[:8]
        buffer    = ""

        with self.verrou:
            self.sessions[joueur_id] = {
                "socket":    sock,
                "pseudo":    None,
                "partie_id": None,
            }

        try:
            while True:
                messages, buffer = proto.recevoir(sock, buffer)
                if messages is None:
                    break
                for msg in messages:
                    self._traiter_message(joueur_id, sock, msg)
        except Exception as e:
            print(f"[SERVEUR] Erreur client {joueur_id} : {e}")
        finally:
            self._deconnecter(joueur_id, sock)

    # ----------------------------------------------------------
    #  Routeur de messages
    # ----------------------------------------------------------
    def _traiter_message(self, joueur_id, sock, msg):
        t = msg.get("type")

        if t == proto.MSG_PSEUDO:
            self._cmd_pseudo(joueur_id, sock, msg)
        elif t == proto.MSG_LISTE_PARTIES:
            self._cmd_liste_parties(joueur_id, sock)
        elif t == proto.MSG_CREER_PARTIE:
            self._cmd_creer_partie(joueur_id, sock, msg)
        elif t == proto.MSG_REJOINDRE:
            self._cmd_rejoindre(joueur_id, sock, msg)
        elif t == proto.MSG_REPRENDRE:
            self._cmd_reprendre(joueur_id, sock, msg)
        elif t == proto.MSG_PLACER_NAVIRE:
            self._cmd_placer_navire(joueur_id, sock, msg)
        elif t == proto.MSG_PLACEMENT_OK:
            self._cmd_placement_ok(joueur_id, sock)
        elif t == proto.MSG_TIR:
            self._cmd_tir(joueur_id, sock, msg)
        elif t == proto.MSG_SAUVEGARDER_ET_QUITTER:
            self._cmd_sauvegarder_et_quitter(joueur_id, sock)
        elif t == proto.MSG_QUITTER:
            self._cmd_quitter(joueur_id, sock)

    # ----------------------------------------------------------
    #  Commandes
    # ----------------------------------------------------------
    def _cmd_pseudo(self, joueur_id, sock, msg):
        pseudo = msg.get("pseudo", "Joueur")
        with self.verrou:
            self.sessions[joueur_id]["pseudo"] = pseudo
        proto.envoyer(sock, proto.MSG_ACK, message="Pseudo enregistré")

    def _cmd_liste_parties(self, joueur_id, sock):
        with self.verrou:
            liste = [p.infos_publiques() for p in self.parties.values()
                     if p.etat in ("attente", "sauvegardee")]
        proto.envoyer(sock, proto.MSG_PARTIES, parties=liste)

    def _cmd_creer_partie(self, joueur_id, sock, msg):
        nom    = msg.get("nom", "Partie sans nom")
        pseudo = self._pseudo(joueur_id)

        with self.verrou:
            partie = Partie(nom, pseudo, joueur_id)
            partie.ajouter_joueur   # déjà fait dans __init__
            partie.joueurs[0]["socket"] = sock
            self.parties[partie.id] = partie
            self.sessions[joueur_id]["partie_id"] = partie.id

        proto.envoyer(sock, proto.MSG_PARTIE_CREE,
                      partie_id=partie.id, nom=partie.nom)

    def _cmd_rejoindre(self, joueur_id, sock, msg):
        partie_id = msg.get("partie_id")
        pseudo    = self._pseudo(joueur_id)

        with self.verrou:
            partie = self.parties.get(partie_id)
            if not partie or partie.etat != "attente":
                proto.envoyer(sock, proto.MSG_ERREUR, message="Partie introuvable ou non disponible")
                return
            if not partie.ajouter_joueur(joueur_id, pseudo, sock):
                proto.envoyer(sock, proto.MSG_ERREUR, message="Partie complète")
                return
            self.sessions[joueur_id]["partie_id"] = partie_id
            partie.demarrer_placement()
            # Prévenir les deux joueurs
            for j in partie.joueurs:
                pseudos = [jj["pseudo"] for jj in partie.joueurs]
                proto.envoyer(j["socket"], proto.MSG_DEBUT_PARTIE,
                              partie_id=partie_id,
                              pseudos=pseudos,
                              votre_id=j["id"])

    def _cmd_reprendre(self, joueur_id, sock, msg):
        # Normaliser le token : majuscules, sans espaces
        token = msg.get("token", "").strip().upper()

        partie_trouvee   = None
        ancien_id_joueur = None
        etat_final       = None

        with self.verrou:
            for partie in self.parties.values():
                for old_jid, tok in partie.token_reprise.items():
                    if tok.upper() == token:
                        partie_trouvee   = partie
                        ancien_id_joueur = old_jid
                        break
                if partie_trouvee:
                    break

            if not partie_trouvee:
                proto.envoyer(sock, proto.MSG_ERREUR, message="Token invalide ou partie introuvable")
                return

            # Reconnecter ce joueur à la place de l'ancien slot
            partie_trouvee.reprendre(ancien_id_joueur, sock)
            self.sessions[joueur_id]["partie_id"] = partie_trouvee.id

            nb_connectes = sum(1 for j in partie_trouvee.joueurs if j["socket"] is not None)
            if nb_connectes == 2:
                partie_trouvee.etat = "en_cours"

            etat_final = partie_trouvee.etat

        # Hors du verrou : envoi réseau
        if etat_final == "en_cours":
            proto.envoyer(sock, proto.MSG_REPRISE_OK,
                          partie_id=partie_trouvee.id,
                          etat="en_cours",
                          votre_id=ancien_id_joueur,
                          pseudo_adverse=self._pseudo_adverse(partie_trouvee, ancien_id_joueur))
            # Envoyer grilles et tour aux deux joueurs
            for j in partie_trouvee.joueurs:
                if j["socket"]:
                    self._envoyer_etat_grilles(partie_trouvee, j["id"])
                    proto.envoyer(j["socket"], proto.MSG_TOUR,
                                  votre_tour=(partie_trouvee.tour_joueur == j["id"]))
        else:
            proto.envoyer(sock, proto.MSG_REPRISE_OK,
                          partie_id=partie_trouvee.id,
                          etat="sauvegardee",
                          votre_id=ancien_id_joueur,
                          pseudo_adverse="")

    def _cmd_placer_navire(self, joueur_id, sock, msg):
        with self.verrou:
            partie = self._partie_du_joueur(joueur_id)
            if not partie:
                return
            ok, message = partie.traiter_placement_navire(
                joueur_id,
                msg.get("nom_navire"),
                msg.get("positions", [])
            )
        if ok:
            proto.envoyer(sock, proto.MSG_ACK, message="Navire placé")
            # Envoyer la grille mise à jour
            with self.verrou:
                grille = partie.grilles[joueur_id]
            proto.envoyer(sock, proto.MSG_ETAT_GRILLE,
                          type_grille="propre",
                          cases=partie.grilles[joueur_id].etat_pour_proprietaire())
        else:
            proto.envoyer(sock, proto.MSG_ERREUR, message=message)

    def _cmd_placement_ok(self, joueur_id, sock):
        with self.verrou:
            partie = self._partie_du_joueur(joueur_id)
            if not partie:
                return
            ok, message = partie.confirmer_placement(joueur_id)
            jeu_demarre = partie.etat == "en_cours"

        if not ok:
            proto.envoyer(sock, proto.MSG_ERREUR, message=message)
            return

        proto.envoyer(sock, proto.MSG_ACK, message="Placement confirmé")
        if jeu_demarre:
            # Notifier les deux joueurs que le jeu commence
            with self.verrou:
                for j in partie.joueurs:
                    if j["socket"]:
                        c_est_votre_tour = (partie.tour_joueur == j["id"])
                        proto.envoyer(j["socket"], proto.MSG_TOUR,
                                      votre_tour=c_est_votre_tour)
                        self._envoyer_etat_grilles(partie, j["id"])

    def _cmd_tir(self, joueur_id, sock, msg):
        ligne   = msg.get("ligne")
        colonne = msg.get("colonne")

        with self.verrou:
            partie = self._partie_du_joueur(joueur_id)
            if not partie:
                return
            resultat, nom_coule, partie_finie = partie.traiter_tir(joueur_id, ligne, colonne)

        if resultat is None:
            proto.envoyer(sock, proto.MSG_ERREUR, message="Tir invalide ou pas votre tour")
            return

        adv_id = partie.adversaire_id(joueur_id)

        # Envoyer le résultat aux deux joueurs
        with self.verrou:
            for j in partie.joueurs:
                if j["socket"]:
                    proto.envoyer(j["socket"], proto.MSG_RESULTAT_TIR,
                                  tireur_id=joueur_id,
                                  ligne=ligne, colonne=colonne,
                                  resultat=resultat,
                                  nom_coule=nom_coule)

        if partie_finie:
            with self.verrou:
                for j in partie.joueurs:
                    if j["socket"]:
                        gagne = (partie.gagnant == j["id"])
                        proto.envoyer(j["socket"], proto.MSG_FIN_PARTIE, gagne=gagne)
            # Supprimer la sauvegarde si elle existait
            supprimer_sauvegarde(partie.id)
        else:
            # Notifier le changement de tour
            with self.verrou:
                for j in partie.joueurs:
                    if j["socket"]:
                        c_est_votre_tour = (partie.tour_joueur == j["id"])
                        proto.envoyer(j["socket"], proto.MSG_TOUR,
                                      votre_tour=c_est_votre_tour)
            # Envoyer grilles mises à jour
            with self.verrou:
                self._envoyer_etat_grilles(partie, joueur_id)
                self._envoyer_etat_grilles(partie, adv_id)

    def _cmd_sauvegarder_et_quitter(self, joueur_id, sock):
        """
        Sauvegarde explicite : sauvegarde la partie, envoie le token,
        puis ferme proprement la connexion de ce joueur.
        """
        with self.verrou:
            partie = self._partie_du_joueur(joueur_id)

        if partie and partie.etat in ("en_cours", "placement"):
            tokens    = partie.sauvegarder()          # génère les tokens une fois
            sauvegarder_partie(partie)
            print(f"[SERVEUR] Partie {partie.id} sauvegardée par {self._pseudo(joueur_id)}")

            pseudo    = self._pseudo(joueur_id)
            mon_token = tokens.get(pseudo, "?")

            # Envoyer le token à celui qui sauvegarde
            proto.envoyer(sock, proto.MSG_SAUVEGARDE_OK, token=mon_token)

            # Prévenir l'adversaire avec son token
            with self.verrou:
                for j in partie.joueurs:
                    if j["id"] != joueur_id and j["socket"]:
                        adv_token = tokens.get(j["pseudo"], "?")
                        proto.envoyer(j["socket"], proto.MSG_ADVERSAIRE_DECONNECTE,
                                      token=adv_token,
                                      message="Adversaire a sauvegardé et quitté.")
        else:
            # Rien à sauvegarder (partie déjà terminée ou pas de partie)
            proto.envoyer(sock, proto.MSG_ACK, message="OK")

        # Fermer proprement ce joueur
        with self.verrou:
            self.sessions.pop(joueur_id, None)
        try:
            sock.close()
        except OSError:
            pass

    def _cmd_quitter(self, joueur_id, sock):
        """Quitter sans sauvegarde explicite."""
        with self.verrou:
            partie = self._partie_du_joueur(joueur_id)

        # Sauvegarde automatique seulement si la partie n'est PAS déjà sauvegardée
        if partie and partie.etat in ("en_cours", "placement"):
            tokens = partie.sauvegarder()
            sauvegarder_partie(partie)
            with self.verrou:
                for j in partie.joueurs:
                    if j["id"] != joueur_id and j["socket"]:
                        adv_token = tokens.get(j["pseudo"], "?")
                        proto.envoyer(j["socket"], proto.MSG_ADVERSAIRE_DECONNECTE,
                                      token=adv_token,
                                      message="Adversaire déconnecté. Partie sauvegardée.")

        with self.verrou:
            self.sessions.pop(joueur_id, None)
        try:
            sock.close()
        except OSError:
            pass

    # ----------------------------------------------------------
    #  Déconnexion forcée (perte de socket)
    # ----------------------------------------------------------
    def _deconnecter(self, joueur_id, sock):
        """Appelé quand le socket se ferme de façon inattendue."""
        with self.verrou:
            session = self.sessions.pop(joueur_id, None)
            if session is None:
                return
            partie_id = session.get("partie_id")
            partie    = self.parties.get(partie_id)

        if partie and partie.etat in ("en_cours", "placement"):
            tokens = partie.sauvegarder()
            sauvegarder_partie(partie)
            print(f"[SERVEUR] Partie {partie.id} sauvegardée (déconnexion inattendue)")
            with self.verrou:
                for j in partie.joueurs:
                    if j["id"] != joueur_id and j["socket"]:
                        adv_token = tokens.get(j["pseudo"], "?")
                        proto.envoyer(j["socket"], proto.MSG_ADVERSAIRE_DECONNECTE,
                                      token=adv_token,
                                      message="Adversaire déconnecté. Partie sauvegardée.")
        try:
            sock.close()
        except OSError:
            pass

    # ----------------------------------------------------------
    #  Utilitaires
    # ----------------------------------------------------------
    def _pseudo(self, joueur_id):
        s = self.sessions.get(joueur_id, {})
        return s.get("pseudo") or "Joueur"

    def _pseudo_adverse(self, partie, joueur_id):
        for j in partie.joueurs:
            if j["id"] != joueur_id:
                return j["pseudo"]
        return "Adversaire"

    def _partie_du_joueur(self, joueur_id):
        session   = self.sessions.get(joueur_id)
        partie_id = session.get("partie_id") if session else None
        return self.parties.get(partie_id)

    def _envoyer_etat_grilles(self, partie, joueur_id):
        """Envoie à joueur_id l'état de sa grille ET de la grille ennemie."""
        j = partie.joueur_par_id(joueur_id)
        if not j or not j["socket"]:
            return
        adv_id = partie.adversaire_id(joueur_id)

        proto.envoyer(j["socket"], proto.MSG_ETAT_GRILLE,
                      type_grille="propre",
                      cases=partie.grilles[joueur_id].etat_pour_proprietaire())
        if adv_id and adv_id in partie.grilles:
            proto.envoyer(j["socket"], proto.MSG_ETAT_GRILLE,
                          type_grille="ennemie",
                          cases=partie.grilles[adv_id].etat_pour_ennemi())


# ----------------------------------------------------------
#  Point d'entrée autonome
# ----------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Serveur Bataille Navale")
    parser.add_argument("--ip",   default=IP_DEFAUT)
    parser.add_argument("--port", type=int, default=PORT_DEFAUT)
    args = parser.parse_args()
    Serveur(args.ip, args.port).demarrer()
