---
titre: Mécanique du Plateau XY & Cinématique de Broderie
date: 2026-09-29
projet: Module Broderie
tags:
  - mecanique
  - cinematique
  - moteurs_pas_a_pas
  - cnc
statut: en cours
aliases:
  - Mécanique Plateau XY
  - Plateau XY
---

# Plateau Mécanique XY et Cinématique de Broderie

## 1. Description du Dispositif
Le module de broderie est constitué d'un châssis mécanique rapporté sur la table de la machine à coudre. Il supporte le cadre à broder sur lequel le textile est tendu.

* **Axe X (Transversal) :** Déplacement gauche/droite du cadre de broderie, guidé par des rails linéaires et entraîné par courroie crantée (type GT2).
* **Axe Y (Longitudinal) :** Déplacement avant/arrière du chariot supportant l'axe X.
* **Motorisation :** Moteurs pas-à-pas bipolaires NEMA 17 alimentés par les drivers **A4982** intégrés à la carte `[[Carte_MKS_Base_V1_4|MKS Base V1.4]]`.

---

## 2. Contrainte Critique de Synchronisation Mécanique

La cinématique d'une brodeuse numérique se distingue fondamentalement d'une fraiseuse CNC ou d'une imprimante 3D :
* **Imprimante 3D / CNC :** Déplacement continu et régulier de l'outil pendant l'extrusion ou l'usinage.
* **Brodeuse CNC :** Mouvement **strictement discontinu**.
  * Pendant que l'aiguille perce le tissu (cycle inférieur, formation de la boucle avec la canette), le tissu doit être **parfaitement immobile**.
  * Dès que la pointe de l'aiguille quitte la surface du tissu (détecté par la `[[Fourche_Optique_H21A1|fourche optique H21A1]]`), une fenêtre de tir mécanique s'ouvre.
  * Le cadre doit alors exécuter l'incrément de déplacement $(\Delta X, \Delta Y)$ correspondant au point de broderie suivant, puis s'immobiliser avant la prochaine pénétration.

```
       Rotation Arbre Principal (360°)
  0°                  120°                240°                360°
  +--------------------+-------------------+--------------------+
  |    Aiguille en     |  Aiguille monte   |   Aiguille descend |
  |     bas (tissu)    |   (HORS TISSU)    |    (vers tissu)    |
  +--------------------+-------------------+--------------------+
  |<-- IMMOBILE ------>|<-- DÉPLACEMENT -->|<-- IMMOBILE ------>|
                        FENÊTRE D'AVANCE
                        (Env. 20 à 35 ms)
```

---

## 3. Précision et Résolution de Pas

Pour un moteur pas-à-pas à $200\text{ pas/tour}$ ($1{,}8^\circ/\text{pas}$) couplé à une poulie $GT2$ de $20\text{ dents}$ ($p = 2\text{ mm}$, soit $40\text{ mm/tour}$) et des drivers configurés en $1/16$ de micropas :

$$\text{Résolution} = \frac{40\text{ mm}}{200 \times 16} = \frac{40}{3200} = 0{,}0125\text{ mm/micropas} = 12{,}5\ \mu\text{m}$$

Cette finesse de pas garantit une excellente définition des contours de broderie et la fidélité des motifs denses (points de bourdon, remplissages tatami).

---

## 4. Tâches Mécaniques & Améliorations Prévues
- [ ] Vérifier la perpendicularité rigoureuse entre l'axe $X$ et l'axe $Y$.
- [ ] Mesurer et régler la tension des courroies crantées pour éliminer tout jeu d'inversion.
- [ ] Installer les butées de fin de course (*Endstops*) physiques ou optiques pour le zéro machine (*Homing*).
- [ ] Évaluer l'ajout d'un capteur de distance laser pour la calibration de planéité.

---
**Voir aussi :**
* `[[Cahier_des_Charges|Cahier des Charges du Module]]`
* `[[Carte_MKS_Base_V1_4|Carte MKS Base V1.4]]`
* `[[Fourche_Optique_H21A1|Capteur de Position Aiguille H21A1]]`
