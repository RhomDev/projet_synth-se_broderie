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

| Sous-système | Statut | Responsable | Prochaine Étape |
| :--- | :--- | :--- | :--- |
| **Capteur Aiguille (H21A1)** | 🟢 Étudié / PCB conçu | RhomDev & matazzo | Fabrication PCB & validation banc |
| **Carte MKS Base V1.4** | 🟡 En cours de câblage | RhomDev | Raccordement moteurs X/Y & alimentation |
| **Variateur Moteur AC** | 🟢 Modélisé & Documenté | RhomDev | Câblage module RobotDyn & tests sécurisés |
| **Mécanique Plateau XY** | 🟡 Contrôle à faire | matazzo | Vérification tension courroies & guidages |
| **Firmware Arduino** | 🟡 Tests partiels (INT2) | RhomDev | Intégration boucle temps réel X/Y/Aiguille |
| **Suite Logicielle Python** | ⚪ À démarrer | matazzo & RhomDev | Script de parsing G-code & envoi série |

---

## 📌 Tâches Immédiates (Sprint Actuel)

### Électronique & Câblage
- [ ] Câbler les moteurs pas à pas des axes X et Y sur les connecteurs dédiés de la `[[Carte_MKS_Base_V1_4|MKS Base V1.4]]`.
- [ ] Réaliser le montage sur platine ou graver le circuit imprimé du conditionneur AOP (`[[Conditionnement_AOP_H21A1|carte acquisition capteur]]`).
- [ ] Câbler le capteur de position d'aiguille `[[Fourche_Optique_H21A1|H21A1]]` via la carte comparatrice sur la pin d'interruption `PD2` (Pin 19 / `INT2`).
- [ ] Câbler le `[[Module_Variateur_AC|Module Variateur AC RobotDyn]]` sur le secteur 230V avec boîte de protection isolante et brancher les broches logiques `ZC` et `PSM` sur la MKS Base.

### Firmware & Logiciel
- [ ] Tester le mouvement élémentaire des axes X et Y (script test pas-à-pas sur microcontrôleur).
- [ ] Valider le déclenchement de l'interruption aiguille en rotation réelle moteur avec le code `src/arduino/test_H21A1/test_H21A1.ino`.
- [ ] Écrire le sketch de test du variateur AC avec rampe de démarrage doux.

---

## 🔮 Tâches Futures (Améliorations & Finition)
- [ ] Monter les butées mécaniques ou optiques de fin de course (*Endstops*) pour les axes X et Y.
- [ ] Installer un encodeur rotatif optique ou magnétique au niveau de la roue d'entraînement pour asservir la vitesse en boucle fermée.
- [ ] Intégrer un écran LCD / interface graphique autonome sur la machine.
- [ ] Évaluer l'installation d'un capteur laser de distance pour un homing automatique et la détection d'épaisseur de tissu.
- [ ] Finaliser le convertisseur de fichiers de broderie vectoriels en G-code optimisé (`src/python/algorithms/`).

---
**Liens utiles :**
* `[[00_Tableau_de_Bord|Tableau de Bord Principal]]`
* `[[Cahier_des_Charges|Cahier des Charges]]`
* Planning prévisionnel : `[[Planning_Gantt.gan]]`
