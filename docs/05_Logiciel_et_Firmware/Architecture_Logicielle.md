---
titre: Architecture Logicielle & Pipeline Numérique
date: 2026-09-30
projet: Module Broderie
tags:
  - logiciel
  - firmware
  - python
  - arduino
  - gcode
statut: en cours
aliases:
  - Architecture Logicielle
  - Pipeline Numérique
---

# Architecture Logicielle & Pipeline Numérique

## 1. Vue d'Ensemble du Flux de Données

Le système de broderie repose sur une collaboration étroite entre un ordinateur hôte (traitement vectoriel en Python) et le microcontrôleur embarqué (carte MKS Base ATmega2560 gérant le temps réel).

```
   [ Motif Graphique ] (SVG / PES / DST / Image)
            |
            v
   [ Traitement Python : `src/python/algorithms/` ]
   - Vectorisation et génération des points de piqûre
   - Planification de trajectoire et ordre des points
   - Génération de G-code spécialisé broderie
            |
            v
   [ Streamer Série : `src/python/communication/serial_bridge.py` ]
            | (Liaison USB Série 115200 bauds)
            v
   [ Firmware Arduino / ATmega2560 : `src/arduino/` ]
   - Décodage des commandes de coordonnées (X, Y)
   - Synchronisation matérielle avec l'interruption aiguille (H21A1)
   - Pilotage des impulsions pas-à-pas (A4982)
   - Asservissement de vitesse moteur AC (TRIAC RobotDyn)
```

---

## 2. Rôle du Cœur Embarqué (Arduino / C++)
Situé dans [`src/arduino/`](file:///home/rhomdev/Documents/Ecole/projet_synth-se_broderie/src/arduino/), le firmware est soumis à de fortes contraintes temps réel :
* **Interruption Prioritaire (Aiguille) :** Gérée par interruption vectorielle matérielle (`INT2` ou similaire) pour réagir en moins de quelques microsecondes au front haut de l'aiguille.
* **Ordonnancement des moteurs pas-à-pas :** Génération des trains d'impulsions (STEP/DIR) sur les axes $X$ et $Y$ sans utiliser d'instructions bloquantes de type `delay()`.
* **Régulation du variateur AC :** Interruption de passage par zéro (`ZC`) et minuterie interne (Timer 1 ou 3) pour le déclenchement de la gâchette TRIAC.

---

## 3. Rôle de la Suite Python
Située dans [`src/python/`](file:///home/rhomdev/Documents/Ecole/projet_synth-se_broderie/src/python/) :
* **`serial_bridge.py` :** Assure le protocole de communication avec accusé de réception (`OK` / `BUFFER_FREE`) pour alimenter le tampon du microcontrôleur sans saturation ni sous-alimentation.
* **`algorithms/` :** Module de conversion de motifs vectoriels en chemins optimisés minimisant les sauts de fil et les croisements.
* **`utils/` :** Outils de visualisation 2D des trajectoires pour prévisualiser la broderie avant lancement physique sur la machine.

---
**Voir aussi :**
* `[[Carte_MKS_Base_V1_4|Carte MKS Base V1.4]]`
* `[[Conditionnement_AOP_H21A1|Capteur H21A1 & Interruption INT2]]`
* `[[Module_Variateur_AC|Variateur AC RobotDyn]]`
