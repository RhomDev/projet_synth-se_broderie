---
titre: Carte de Commande MKS Base V1.4
date: 2026-09-29
projet: Module Broderie
tags:
  - electronique
  - mks_base
  - microcontroleur
  - arduino
  - moteurs_pas_a_pas
  - cnc
statut: valide
aliases:
  - carte_de_commande_mks_base_v1_4
  - MKS Base V1.4
  - MKS Base
---

# Carte de Commande MKS Base V1.4

## 📌 Présentation Générale
La **MKS Base V1.4** constitue le centre névralgique (carte mère) de la brodeuse numérique. Cette carte intègre sur un même circuit imprimé un microcontrôleur équivalent à un **Arduino Mega 2560** et 5 contrôleurs de puissance (drivers) pour moteurs pas-à-pas (compatibles A4982/A4988).

```
                            +--------------------------+
                            |  Alimentation 12V / 24V  |
                            +--------------------------+
                                          |
                                          v
+-----------------------+     +--------------------------+     +--------------------------+
|  PC Hôte (Python)     | ==> |    MKS BASE V1.4         | ==> |  Moteurs Pas-à-Pas X/Y   |
|  G-code via USB Série |     |    (ATmega2560)          |     |  Cadre de broderie       |
+-----------------------+     +--------------------------+     +--------------------------+
                                     ^            |
                                     |            v
                     +-------------------+    +--------------------------+
                     | Capteur H21A1     |    | Variateur AC RobotDyn    |
                     | Synchro Aiguille  |    | Moteur 230V Couture      |
                     +-------------------+    +--------------------------+
```

---

## ⚙️ Caractéristiques Techniques Principales

* **Microcontrôleur :** ATmega2560 cadencé à $16\text{ MHz}$ (mémoire Flash $256\text{ ko}$, SRAM $8\text{ ko}$).
* **Pilotes Moteurs Intégrés :** Drivers A4982 configurables en $1/16$ de pas, avec dissipateurs thermiques intégrés.
* **Tension d'Alimentation :** $12\text{ V} - 24\text{ V DC}$ pour la section puissance moteurs.
* **Sorties MOSFET :** Présentes pour les sorties de chauffe (non utilisées pour la broderie, mais réassignables pour des actionneurs annexes).
* **Connecteurs Endstops :** 6 entrées fin de course protégées avec résistances de pull-up (utilisées pour les butées X/Y et les entrées capteurs).
* **Port Série USB :** Puce FTDI / CH340 pour la communication série avec le script Python streamer.

---

## 🎯 Rôle et Affectation des Ports dans le Projet

1. **Axes Pas-à-Pas X et Y :**
   * Connecteur moteur **X** : Translation gauche/droite du cadre.
   * Connecteur moteur **Y** : Translation avant/arrière du chariot.
2. **Synchronisation Aiguille (Fourche Optique H21A1) :**
   * Raccordement sur une broche d'interruption externe (ex: broche `PD2` / Pin 19 `INT2` ou `D2` / Pin 4 `INT4`).
   * Déclenchement matériel instantané pour sécuriser le déplacement du cadre uniquement aiguille levée.
3. **Pilotage du Variateur AC RobotDyn :**
   * Broche `ZC` (Zero Cross) : Raccordée sur une entrée d'interruption pour synchroniser la découpe de phase ($100\text{ Hz}$).
   * Broche `PSM` (Gate) : Raccordée sur une broche de sortie numérique pour déclencher le TRIAC.

---

## 🚀 Prochaines Étapes
- [ ] Raccorder les connecteurs 4 broches des moteurs pas-à-pas X et Y.
- [ ] Alimenter la carte via une alimentation stabilisée $12\text{ V} / 5\text{ A}$.
- [ ] Connecter le câble USB et valider la communication série avec `src/python/communication/serial_bridge.py`.

---
**Ressources & Schémas Associés :**
* `[[MKS_BASE_PINS.pdf]]` — Brochage officiel MKS Base
* `[[MKS_BASE_V1_4_Schematic_Alimentation_P1.pdf]]` — Schéma Alimentation
* `[[MKS_BASE_V1_4_Schematic_MOSFETs_P2.pdf]]` — Schéma Étage de puissance
* `[[MKS_BASE_V1_4_Schematic_Drivers_P3.pdf]]` — Schéma Drivers Moteurs A4982
* `[[ATMEGA640.PDF]]` — Datasheet Famille Microcontrôleur ATmega
* `[[Cahier_des_Charges|Cahier des Charges Broderie]]`
* `[[Plateau_XY_et_Mecanique|Mécanique Plateau XY]]`