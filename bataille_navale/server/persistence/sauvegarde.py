# ============================================================
#  server/persistence/sauvegarde.py  —  Sauvegarde JSON des parties
# ============================================================
import json
import os

DOSSIER_SAVES = os.path.join(os.path.dirname(__file__), "saves")


def _chemin_partie(partie_id):
    os.makedirs(DOSSIER_SAVES, exist_ok=True)
    return os.path.join(DOSSIER_SAVES, f"partie_{partie_id}.json")


def sauvegarder_partie(partie):
    """Écrit l'état complet d'une partie dans un fichier JSON."""
    chemin = _chemin_partie(partie.id)
    try:
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(partie.vers_dict(), f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        print(f"[SAVE] Erreur sauvegarde : {e}")
        return False


def charger_partie(partie_id):
    """Charge une partie depuis son fichier JSON. Retourne None si absent."""
    from server.models.partie import Partie
    chemin = _chemin_partie(partie_id)
    if not os.path.exists(chemin):
        return None
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Partie.depuis_dict(data)
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"[SAVE] Erreur chargement : {e}")
        return None


def lister_parties_sauvegardees():
    """Retourne les ids des parties sauvegardées sur disque."""
    os.makedirs(DOSSIER_SAVES, exist_ok=True)
    ids = []
    for nom in os.listdir(DOSSIER_SAVES):
        if nom.startswith("partie_") and nom.endswith(".json"):
            ids.append(nom[len("partie_"):-len(".json")])
    return ids


def supprimer_sauvegarde(partie_id):
    chemin = _chemin_partie(partie_id)
    if os.path.exists(chemin):
        os.remove(chemin)
