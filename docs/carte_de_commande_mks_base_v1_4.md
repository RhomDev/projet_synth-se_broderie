---
tags:
  - projet_broderie
  - electronique
  - CNC
  - arduino
  - moteurs_pas_a_pas
statut: en cours
---
S
# Carte MKS Base V1.4

## 📌 Présentation Générale
La **MKS Base V1.4** est la carte électronique principale (cerveau) du projet de transformation de la machine à coudre en brodeuse numérique. Il s'agit d'une carte "tout-en-un" très utilisée dans les projets d'impression 3D et de petites CNC.

## ⚙️ Caractéristiques Techniques
* **Architecture :** Basée sur l'environnement **Arduino** (généralement un microcontrôleur ATmega2560). Elle se programme facilement via l'IDE Arduino.
* **Drivers intégrés :** Contrairement à un montage Arduino standard + Shield, cette carte intègre directement les contrôleurs de puissance (drivers) sur le circuit imprimé.
* **Connectique :** Permet de brancher directement :
	* Les moteurs pas à pas (X, Y, Z, extrudeurs - bien que seuls X et Y soient utilisés ici).
	* Les capteurs de fin de course (Endstops).
	* L'alimentation.
	* Connexion USB pour la communication avec un ordinateur.

## 🎯 Rôle dans le Projet Broderie
Dans le cadre de notre module de broderie, la carte MKS remplit plusieurs fonctions cruciales :

1. **Pilotage des Axes (X/Y) :** Elle envoie les impulsions électriques aux moteurs pas à pas pour déplacer le plateau mécanique (cadre de broderie) de manière ultra-précise via les courroies crantées.
2. **Acquisition de données :** Elle sera chargée de lire les informations envoyées par le futur capteur de position de l'aiguille (installé sur l'équerre violette imprimée en 3D).
3. **Synchronisation :** C'est dans le code téléversé sur cette carte que se fera la synchronisation critique : s'assurer que le plateau de tissu ne se déplace **que** lorsque l'aiguille est ressortie du tissu.

## 🚀 Prochaines Étapes liées à la carte
- [ ] Câbler les moteurs pas à pas des axes X et Y sur les ports correspondants de la MKS.
- [ ] Câbler le capteur de position de l'aiguille (temps de réponse rapide) sur l'une des entrées capteur (ex: pins Endstop).
- [ ] Rédiger et téléverser le code Arduino pour tester les déplacements de base.
- [ ] Programmer la boucle de synchronisation Mouvement/Aiguille.

---
**Liens & Références internes :**
* [[Projet broderie (machine CN)]] - Note principale du projet
* [[Mécanique Plateau XY]] - Note sur la structure mécanique