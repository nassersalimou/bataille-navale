# ============================================================
#  protocole.py  —  Messages réseau JSON entre client et serveur
# ============================================================
import json


# ---------- Types de messages ----------
# Client → Serveur
MSG_PSEUDO          = "pseudo"
MSG_LISTE_PARTIES   = "liste_parties"
MSG_CREER_PARTIE    = "creer_partie"
MSG_REJOINDRE       = "rejoindre_partie"
MSG_REPRENDRE       = "reprendre_partie"
MSG_PLACER_NAVIRE   = "placer_navire"
MSG_PLACEMENT_OK    = "placement_termine"
MSG_TIR             = "tir"
MSG_QUITTER         = "quitter"
MSG_SAUVEGARDER_ET_QUITTER = "sauvegarder_et_quitter"

# Serveur → Client
MSG_ACK             = "ack"
MSG_ERREUR          = "erreur"
MSG_PARTIES         = "parties"
MSG_PARTIE_CREE     = "partie_cree"
MSG_PARTIE_REJOINTE = "partie_rejointe"
MSG_DEBUT_PARTIE    = "debut_partie"
MSG_RESULTAT_TIR    = "resultat_tir"
MSG_TOUR            = "tour"
MSG_FIN_PARTIE      = "fin_partie"
MSG_ETAT_GRILLE     = "etat_grille"
MSG_REPRISE_OK      = "reprise_ok"
MSG_SAUVEGARDE_OK   = "sauvegarde_ok"
MSG_ADVERSAIRE_DECONNECTE = "adversaire_deconnecte"


# ---------- Construction des paquets ----------

def construire(type_msg, **champs):
    """Crée un dict-message prêt à être sérialisé."""
    paquet = {"type": type_msg}
    paquet.update(champs)
    return paquet


# ---------- Envoi / réception sur socket TCP ----------

def envoyer(sock, type_msg, **champs):
    """Sérialise et envoie un message JSON sur le socket."""
    paquet = construire(type_msg, **champs)
    data   = json.dumps(paquet, ensure_ascii=False) + "\n"
    try:
        sock.sendall(data.encode("utf-8"))
        return True
    except OSError:
        return False


def recevoir(sock, buffer_restant=""):
    """
    Lit des données depuis le socket et retourne (messages, buffer_restant).
    Gère la fragmentation TCP : accumule jusqu'à trouver un '\n'.
    Retourne une liste de dicts décodés.
    """
    messages = []
    try:
        data = sock.recv(4096)
        if not data:
            return None, buffer_restant   # connexion fermée
        buffer_restant += data.decode("utf-8", errors="replace")
    except OSError:
        return None, buffer_restant

    while "\n" in buffer_restant:
        ligne, buffer_restant = buffer_restant.split("\n", 1)
        ligne = ligne.strip()
        if ligne:
            try:
                messages.append(json.loads(ligne))
            except json.JSONDecodeError:
                pass   # paquet corrompu, on l'ignore

    return messages, buffer_restant
