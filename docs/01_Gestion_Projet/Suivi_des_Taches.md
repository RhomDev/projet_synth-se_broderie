---
titre: Suivi des Tâches & Feuille de Route
date: 2026-10-01
projet: Module Broderie
tags:
  - gestion_projet
  - taches
  - roadmap
statut: en cours
aliases:
  - Tache sur machine
  - Suivi des Taches
  - Roadmap
---

# Suivi des Tâches & Feuille de Route

## 🚦 Tableau d'Avancement Général

| Sous-système                    | Statut                                            | Responsable       | Prochaine Étape                                     |
| :------------------------------ | :------------------------------------------------ | :---------------- | :-------------------------------------------------- |
| **Capteur Aiguille (H21A1)**    | 🔴 Abandonné (trop contraignant)                  | RhomDev & matazzo | Remplacement par fin de course mécanique            |
| **Synchronisation Aiguille**    | 🟢 Solution validée (Fin de course PMH + SEN0230) | RhomDev & matazzo | Montage came PMH & impression poulie encodeur       |
| **Tests Machine Manuels**       | 🟢 Validés (02/11/2026)                           | RhomDev & matazzo | Réalisation de points manuels et d'un carré réussie |
| **Variateur Moteur AC**         | 🟡 En cours de mise en place                      | RhomDev           | Câblage module RobotDyn & régulation vitesse        |
| **Mécanique Plateau XY**        | 🟡 Redesign en cours                              | matazzo           | Revoir le design du plateau + fins de course X/Y    |
| **Carte MKS Base V1.4**         | 🟡 En cours de câblage                            | RhomDev           | Raccordement moteurs X/Y, endstops et variateur     |
| **Besoins & Approvisionnement** | 🟢 Liste établie                                  | matazzo & RhomDev | Passage des commandes des composants                |
| **Firmware Arduino**            | 🟡 En cours d'adaptation                          | RhomDev           | Routine de Homing aiguille + lecture encodeur       |
| **Suite Logicielle Python**     | ⚪ À démarrer                                      | matazzo & RhomDev | Script de parsing G-code & envoi série              |

---

## 📌 Tâches Immédiates (Sprint Actuel)

### Validation Fonctionnelle Machine
- [x] **Comprendre le fonctionnement d'une machine à coudre & valider la mécanique de piquage :**
  - Tests manuels effectués le 02/11/2026 : points réguliers obtenus et tracé complet d'une forme géométrique (carré) réussi.

### Approvisionnement & Besoins
- [x] Préparer la liste détaillée des composants et matériels à commander (BOM).
- [ ] Valider et passer la commande des pièces manquantes.

### Mécanique & Plateau de Travail
- [ ] **Revoir le design du plateau de travail :** optimisation des dimensions, rigidification et fixation du cadre.
- [ ] Concevoir et intégrer les supports pour les **fins de course des axes X et Y** (homing du cadre).
- [ ] Modéliser et imprimer en 3D la poulie crantée (16 à 18 dents) pour l' [[Encodeur_Rotatif_SEN0230|encodeur SEN0230]] .
- [ ] Installer le support et la came mécanique sur l'arbre pour le  [[Capteur_Fin_de_Course_Aiguille|fin de course aiguille]] .

### Électronique & Câblage
- [ ] Câbler le **capteur fin de course aiguille** sur l'entrée Endstop dédiée de la  [[Carte_MKS_Base_V1_4|MKS Base V1.4]] .
- [x] Câbler l'**encodeur rotatif SEN0230** (alimentation 5V et canaux A/B). (Abandonnée)
- [ ] Câbler les **fins de course du plateau X et Y**.
- [ ] Mettre en place et raccorder le  [[Module_Variateur_AC|Module Variateur AC RobotDyn]]  (230V AC et signaux  ZC  /  PSM ) pour le contrôle de la vitesse moteur.
- [ ] Raccorder les moteurs pas-à-pas NEMA 17 des axes X et Y.

### Firmware & Logiciel
- [ ] Développer la séquence de **Homing aiguille** au démarrage (recherche du contact haut et RAZ encodeur).
- [ ] Tester le contrôle de vitesse moteur via le variateur AC.
- [ ] Tester le déplacement élémentaire XY avec prise d'origine sur les fins de course du plateau.

---

## 🔮 Tâches Futures (Améliorations & Finition)
- [ ] Monter les butées mécaniques ou optiques de fin de course (*Endstops*) pour les axes X et Y.
- [ ] Installer un encodeur rotatif optique ou magnétique au niveau de la roue d'entraînement pour asservir la vitesse en boucle fermée.
- [ ] Intégrer un écran LCD / interface graphique autonome sur la machine.
- [ ] Évaluer l'installation d'un capteur laser de distance pour un homing automatique et la détection d'épaisseur de tissu.
- [ ] Finaliser le convertisseur de fichiers de broderie vectoriels en G-code optimisé ( src/python/algorithms/ ).

---
**Liens utiles :**
*  [[Structure_Taches_Gantt|Décomposition des Tâches & WBS Gantt]] 
*  [[Planning_Gantt.gan|Fichier GanttProject]] 
*  [[00_Tableau_de_Bord|Tableau de Bord Principal]] 
*  [[Cahier_des_Charges|Cahier des Charges]] 
