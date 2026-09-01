# ============================================================
#  client/client_reseau.py  —  Communication avec le serveur
# ============================================================
import socket
import threading
import queue
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocole as proto
from constantes import IP_DEFAUT, PORT_DEFAUT


class ClientReseau:
    """
    Gère la connexion TCP avec le serveur.
    Les messages reçus sont mis dans une queue thread-safe,
    consultée par la boucle principale Pygame.
    """

    def __init__(self):
        self.sock          = None
        self.connecte      = False
        self.messages_recus = queue.Queue()   # messages venant du serveur
        self.buffer         = ""
        self._thread_reception = None

    # ----------------------------------------------------------
    #  Connexion
    # ----------------------------------------------------------
    def connecter(self, ip=IP_DEFAUT, port=PORT_DEFAUT):
        """Retourne True si la connexion réussit."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((ip, port))
            self.sock.settimeout(None)
            self.connecte = True
            self._thread_reception = threading.Thread(
                target=self._boucle_reception, daemon=True)
            self._thread_reception.start()
            return True
        except OSError as e:
            print(f"[CLIENT] Connexion échouée : {e}")
            self.connecte = False
            return False

    def deconnecter(self):
        self.connecte = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass

    # ----------------------------------------------------------
    #  Réception (thread dédié)
    # ----------------------------------------------------------
    def _boucle_reception(self):
        while self.connecte:
            messages, self.buffer = proto.recevoir(self.sock, self.buffer)
            if messages is None:
                self.connecte = False
                self.messages_recus.put({"type": "deconnexion_serveur"})
                break
            for msg in messages:
                self.messages_recus.put(msg)

    # ----------------------------------------------------------
    #  Envoi (appelé depuis le thread principal)
    # ----------------------------------------------------------
    def envoyer(self, type_msg, **champs):
        if self.connecte and self.sock:
            return proto.envoyer(self.sock, type_msg, **champs)
        return False

    # ----------------------------------------------------------
    #  Lecture non bloquante des messages reçus
    # ----------------------------------------------------------
    def lire_messages(self):
        """Retourne tous les messages disponibles sans bloquer."""
        msgs = []
        while not self.messages_recus.empty():
            try:
                msgs.append(self.messages_recus.get_nowait())
            except queue.Empty:
                break
        return msgs
