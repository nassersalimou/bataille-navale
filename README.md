# Bataille Navale en réseau

Jeu de bataille navale multijoueur développé en Python avec Pygame et une architecture client–serveur par sockets TCP.

## Fonctionnalités

- création et connexion à une partie ;
- placement interactif des navires ;
- jeu à deux en temps réel ;
- sauvegarde d'une partie ;
- reprise après déconnexion avec un code unique ;
- persistance locale au format JSON.

## Technologies

- Python 3
- Pygame
- sockets TCP
- JSON

## Installation

```bash
python -m venv .venv
```

Sous Windows :

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python bataille_navale/main.py
```

Sous Linux ou macOS :

```bash
source .venv/bin/activate
pip install -r requirements.txt
python bataille_navale/main.py
```

Le serveur écoute par défaut sur `127.0.0.1`. Lancez ensuite deux clients pour tester une partie locale.

## Structure

```text
bataille_navale/
├── client/       Interface Pygame et client réseau
├── server/       Serveur, parties et persistance
├── main.py       Point d'entrée
├── protocole.py  Protocole d'échange
├── grille.py     Gestion des grilles
└── navire.py     Modèle des navires
```

## Auteurs

Projet universitaire réalisé par Nasser Salimou et Safwan Msellek.
