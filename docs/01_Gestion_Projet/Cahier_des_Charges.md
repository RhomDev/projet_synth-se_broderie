---
titre: Cahier des Charges & Spécifications — Module Broderie
date: 2026-09-26
projet: Module Broderie
tags:
  - gestion_projet
  - cahier_des_charges
  - cnc
  - broderie
statut: valide
aliases:
  - Projet broderie (machine CN)
  - Module Broderie
  - Cahier des Charges
---

# Cahier des Charges — Module Broderie Numérique

## 🎯 Objectif Général du Projet
Le projet vise à transformer une machine à coudre mécanique traditionnelle en une **brodeuse numérique à commande numérique (CNC)** autonome, capable d'exécuter des motifs de broderie vectoriels prédéfinis.

Un plateau mécanique 2 axes ($X$ et $Y$) entraîné par des moteurs pas-à-pas a été pré-installé sur la machine. Le cœur de commande est une carte **MKS Base V1.4** (microcontrôleur ATmega2560 + drivers pas-à-pas intégrés).

---

## 📌 Missions Principales

```
             +-----------------------------------------------+
             |       Machine à Coudre + Cadre Broderie       |
             +-----------------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+-------------------------------+               +-------------------------------+
|  1. Remise en État Mécanique  |               |  2. Synchronisation Aiguille  |
|  - Tension des courroies X/Y  |               |  - Détection optique (H21A1)  |
|  - Butées et guidages         |               |  - Déplacement cadre HORS     |
|  - Rigidité du cadre          |               |    tissu uniquement           |
+-------------------------------+               +-------------------------------+
                                 |
                                 v
                +-------------------------------+
                |  3. Pilotage & Vitesse Moteur |
                |  - Variateur AC RobotDyn      |
                |  - Régulation par découpe     |
                |    de phase (TRIAC)           |
                +-------------------------------+
                                 |
                                 v
                +-------------------------------+
                |  4. Chaîne Numérique (Python) |
                |  - Vectorisation / G-code     |
                |  - Streamer série MKS Base    |
                +-------------------------------+
```

### 1. Remise en état et validation de la cinématique mécanique
* Contrôle du guidage linéaire des axes $X$ et $Y$.
* Ajustement de la tension des courroies crantées pour éliminer tout jeu (*backlash*).
* Définition de l'aire utile de broderie et mise en place de la procédure de prise d'origine (*Homing*).

### 2. Détection de position d'aiguille & Synchronisation critique
* Choix et intégration d'un capteur de position ultra-rapide (**Fourche optique H21A1**).
* Conditionnement du signal par comparateur AOP pour éliminer l'effet de charge de la carte MKS Base.
* **Règle absolue de sécurité :** Le cadre textile ne doit **JAMAIS** se déplacer tant que l'aiguille est engagée dans le tissu. Les moteurs pas-à-pas $X/Y$ ne peuvent translater le tissu que lorsque l'aiguille est en position haute (fenêtre temporelle d'environ $15\text{ ms}$ à $30\text{ ms}$ par cycle à $500-1000\text{ tr/min}$).

### 3. Contrôle de puissance et vitesse du moteur principal
* Abandon de la pédale mécanique manuelle et du relais tout-ou-rien.
* Intégration du **Module Variateur AC RobotDyn** pour réguler la vitesse de piquage via découpe de phase asservie sur le zéro secteur ($50\text{ Hz}$).
* Possibilité d'asservir la vitesse selon la complexité du point ou lors des phases délicates.

### 4. Chaîne logicielle de broderie (Software Pipeline)
* Développement d'outils Python pour convertir des motifs graphiques (SVG, DST, PES ou images) en commandes de trajectoire (G-code broderie).
* Pont de communication série (`serial_bridge.py`) pour transmettre les commandes à l'Arduino de la carte MKS Base.

---
**Documents associés :**
* `[[Carte_MKS_Base_V1_4|Architecture Carte MKS Base]]`
* `[[Plateau_XY_et_Mecanique|Mécanique Plateau XY]]`
* `[[Fourche_Optique_H21A1|Capteur H21A1]]`
* `[[Module_Variateur_AC|Variateur AC]]`
* `[[Suivi_des_Taches|Feuille de Route & Tâches]]`
