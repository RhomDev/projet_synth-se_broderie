# Brodeuse numérique : consignes pour Claude Code

Projet de master (Automatique-Robotique) : rétrofit d'une machine à coudre Janome Facility 21 en brodeuse à patch. Un plateau XY à moteurs pas à pas bouge le cadre sous l'aiguille. Le firmware (Arduino Mega, carte MKS Base V1.4) fait le temps réel ; l'application PC (Python, PySide6) pilote la carte par liaison série.

Langue : tout est en français (commentaires, docstrings, messages de l'interface, documents). Garde-le.

## Organisation

- `src/python/communication/` : `protocol.py` (trames, sans entrée-sortie), `link.py` (thread de liaison, une seule requête en vol), `simulator.py` (carte simulée), `serial_transport.py`, `ports.py`. `serial_bridge.py` est un ancien module, non utilisé.
- `src/python/machine/` : `state.py` (état déduit de la liaison), `safety.py` (règles pures), `motion.py` (intentions de mouvement), `sewing_motor.py` (moteur de couture 230 V), `line_test.py` (ligne de test), `config.py` et `units.py`.
- `src/python/ui/` : fenêtre principale et panneaux. `src/python/main.py` lance l'application (`--simulation` pour la machine simulée).
- `src/python/tests/` : tests `unittest` (pas de pytest requis).
- `src/arduino/controle_moteur_v2/` : firmware v2. `docs/05_Logiciel_et_Firmware/Protocole_Serie.md` est la référence du protocole.
- `reports/journal/` : journal de bord du projet, un fichier par jour.

`docs/05_Logiciel_et_Firmware/Architecture_Logicielle.md` est en partie périmé (il parle de 115 200 bauds et d'accusés `OK`/`BUFFER_FREE` ; la liaison réelle est à 1 000 000 bauds avec des réponses `ok M<code>` / `err M<code> <n>`). Fais confiance au code et au protocole.

## Lancer les tests

```
cd src/python
pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -t .
```

Sous Windows (PowerShell) : `$env:QT_QPA_PLATFORM="offscreen"` avant la commande. La suite complète doit rester verte avant tout commit.

## Sécurité (non négociable)

Le moteur de couture est branché au 230 V.
- Au moindre doute ou perte de communication, l'application arrête le moteur. L'arrêt (`M140 S0`) n'est jamais soumis à une condition et part même liaison perdue ; seul le démarrage est contrôlé (`safety.can_run_motor`).
- Le démarrage exige un chien de garde (`M113`) confirmé actif par la carte. Tant que le moteur tourne, le bail du thread UI (`link.require_lease`) fait couper le moteur par la carte si l'interface se fige.
- Une donnée trop ancienne s'affiche « inconnue », jamais comme une mesure actuelle.
- Tout ce que renvoie le simulateur est étiqueté SIMULATION et ne vaut pas mesure.
- Le bouton ARRÊT est un arrêt logiciel (`M110`, qui coupe aussi le moteur). Il ne remplace pas un arrêt d'urgence matériel.

## Conventions

- Ne change pas le comportement des commandes existantes (`M100` à `M130`, lignes `X…`/`Y…`). Toute évolution du protocole met à jour `Protocole_Serie.md` dans le même commit.
- Style : `from __future__ import annotations`, dataclasses, fonctions pures pour les règles de sécurité, modules documentés par une docstring qui explique le principe. Respecte l'organisation existante.
- Chaque nouveau comportement a un test, avec le simulateur (`tests/test_simulator.py` fournit `FakeClock` et `send`) ou des doublures simples (`tests/test_motor.py`).
- Un firmware v2 sans `M140`/`M141` doit continuer de fonctionner : l'application sonde `M141` à la connexion et désactive le moteur si besoin.

## Avancement de l'application

Les étapes 1 à 3 ne sont pas documentées dans le dépôt ; d'après le code : liaison série et protocole v2, simulateur, état et sécurité, interface de pilotage manuel.
- Étape 4 : détection du firmware (v1 ou v2), simulateur v1, machine à coudre simulée, ligne de test (`tests/test_step4.py`).
- Étape 5 : moteur de couture AC (`M140`/`M141`, erreur 8, bit d'alarme `0x10`) : `sewing_motor.py`, `ui/motor_panel.py`, intégration dans la ligne de test, simulateur et tests (`tests/test_motor.py`).

Reste à faire pour l'étape 5, à valider sur la machine :
- Flasher le firmware à jour, puis vérifier `M141` et un démarrage à faible vitesse, moteur non couplé à l'aiguille.
- Vérifier le délai `SETTLE_S` (1 s) de mesure de la fenêtre aiguille dans `line_test.py`, trop court à très basse vitesse.
- Confirmer l'ordre des contrôles de `M140` côté firmware (paramètre, puis alarme, puis secteur : hypothèse du simulateur).
- Les valeurs de rampe, `dl`, `w` et le lien vitesse moteur / cadence du simulateur sont fictifs.

Pas de pause dans la ligne de test, et pas de lecteur de G-code complet dans l'application.

## Git

L'application Claude n'a pas accès en écriture à ce dépôt : c'est l'utilisateur qui pousse. Travaille sur une branche, fais des commits clairs, ne pousse pas sans demande.
