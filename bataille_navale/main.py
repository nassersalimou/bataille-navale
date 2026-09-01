#!/usr/bin/env python3
# ============================================================
#  main.py  —  Point d'entrée de la Bataille Navale
#
#  Usage :
#    python main.py                   → lance le client (serveur auto en local)
#    python main.py --pseudo Alice    → avec pseudo prédéfini
#    python main.py --ip 192.168.1.5 --port 5050   → serveur distant
#    python main.py --serveur-seul    → lance seulement le serveur
# ============================================================
import argparse
import sys
import os
import socket
import subprocess
import time

# Assure que la racine du projet est dans le path Python
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from constantes import IP_DEFAUT, PORT_DEFAUT


def serveur_disponible(ip, port):
    """Teste si un serveur écoute déjà sur ip:port."""
    try:
        s = socket.create_connection((ip, port), timeout=1)
        s.close()
        return True
    except OSError:
        return False


def lancer_serveur_en_arriere_plan(ip, port):
    """
    Lance server/serveur.py dans un sous-processus détaché.
    Retourne le processus.
    """
    chemin_serveur = os.path.join(ROOT, "server", "serveur.py")
    proc = subprocess.Popen(
        [sys.executable, chemin_serveur, "--ip", ip, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Attendre que le serveur soit prêt (max 3 secondes)
    for _ in range(30):
        time.sleep(0.1)
        if serveur_disponible(ip, port):
            return proc
    return proc


def main():
    parser = argparse.ArgumentParser(description="Bataille Navale")
    parser.add_argument("--pseudo",       default="",         help="Pseudo du joueur")
    parser.add_argument("--ip",           default=IP_DEFAUT,  help="IP du serveur")
    parser.add_argument("--port",  type=int, default=PORT_DEFAUT, help="Port du serveur")
    parser.add_argument("--serveur-seul", action="store_true",
                        help="Lance uniquement le serveur (sans interface)")
    args = parser.parse_args()

    # --- Mode serveur seul ---
    if args.serveur_seul:
        from server.serveur import Serveur
        print(f"Lancement du serveur sur {args.ip}:{args.port}")
        Serveur(args.ip, args.port).demarrer()
        return

    # --- Mode client (avec auto-lancement serveur local si besoin) ---
    if args.ip in (IP_DEFAUT, "localhost", "127.0.0.1"):
        if not serveur_disponible(args.ip, args.port):
            print(f"[MAIN] Serveur non détecté → lancement automatique sur {args.ip}:{args.port}")
            lancer_serveur_en_arriere_plan(args.ip, args.port)
        else:
            print(f"[MAIN] Serveur déjà actif sur {args.ip}:{args.port}")

    # --- Lancement de l'interface client ---
    from client.app_client import AppClient
    app = AppClient(pseudo_arg=args.pseudo)
    app.lancer()


if __name__ == "__main__":
    main()
