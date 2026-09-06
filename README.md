# Bataille Navale — jeu réseau en Python (Pygame)

Jeu de bataille navale multijoueur en Python avec interface Pygame et communication client–serveur via sockets TCP. Ce dépôt contient le code source du serveur et du client pour jouer en local ou sur un réseau local.

## Résumé
- Langage : Python 3
- UI : Pygame
- Réseau : sockets TCP

## Prérequis
- Python 3.8+
- pip

## Installation (Windows)
1. git clone https://github.com/nassersalimou/bataille-navale
2. cd bataille-navale
3. python -m venv .venv
4. .\.venv\Scripts\Activate.ps1  (PowerShell) ou .\.venv\Scripts\activate.bat (CMD)
5. pip install -r requirements.txt

## Installation (Linux / macOS)
1. git clone https://github.com/nassersalimou/bataille-navale
2. cd bataille-navale
3. python3 -m venv .venv
4. source .venv/bin/activate
5. pip install -r requirements.txt

## Lancer une partie locale
- Démarrez le serveur (voir la structure du projet pour la commande exacte).
- Lancez deux instances du client (même machine ou machines du LAN) et suivez l'interface Pygame pour placer les navires et jouer.

## Résultat attendu
- Fenêtres clients affichant les grilles, connexions établies, attaques et états visibles.

## Sécurité
- Les fichiers de sauvegarde sont stockés localement en JSON : ne publiez pas ces fichiers si vous ne voulez pas exposer des données locales.
- Le serveur écoute par défaut sur localhost. Ne l'exposez pas sur Internet sans audit.

## Licence
- Licence MIT — voir LICENSE
