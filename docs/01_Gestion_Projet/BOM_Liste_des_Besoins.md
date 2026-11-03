---
titre: Liste des Besoins & Nomenclature Matériel (BOM)
date: 2026-11-02
projet: Module Broderie
tags:
  - gestion_projet
  - bom
  - approvisionnement
  - achats
  - electronique
  - mecanique
statut: valide
aliases:
  - BOM
  - Liste des Besoins
  - Produits a acheter
---

# 🛒 Nomenclature des Besoins & Approvisionnement (BOM)

Ce document formalise la liste des matériels et composants à commander pour la brodeuse numérique CNC, issue des spécifications validées et du fichier de suivi [`reports/Produits_a_acheter.xlsx`](file:///home/rhomdev/Documents/Ecole/2026-27/projet_synth-se_broderie/reports/Produits_a_acheter.xlsx).

---

## 📋 Tableau Récapitulatif des Produits à Commander

| Désignation | Référence / Spécification | Qté | Prix Unitaire | Total HT/TTC | Fournisseur / Lien | Rôle dans le Projet |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Encodeur Rotatif** | SEN0230 (arbre $\varnothing 6\text{ mm}$, 400 imp/tr, 5000 tr/min max) | 1 | 29,90 € | 29,90 € | [GoTronic SEN0230](https://www.gotronic.fr/art-encodeur-rotatif-6-mm-sen0230-26819.htm) | Suivi cinématique & asservissement vitesse |
| **Fin de Course Aiguille** | Microrupteur à levier avec galet (contact flexible) | 1 | 2,80 € | 2,80 € | GoTronic / Makerbot standard | Détection Point Mort Haut (PMH) & Homing aiguille |
| **Variateur AC 230V** | Module variateur RobotDyn (TRIAC, logique 3.3V/5V, opto-isolé) | 1 | 29,04 € | 29,04 € | RobotDyn EB0046830 | Découpe de phase & régulation moteur machine |
| **Fins de Course Plateau** | Butées mécaniques Endstops (axes X et Y) | 4 | 2,80 € | 11,20 € | Standard imprimante 3D / CNC | Homing X/Y et butées de sécurité physiques |
| **Optocoupleur ZC** *(Secours)* | H11AA1 (U2) — Détection passage à zéro | 1 | 1,40 € | 1,40 € | [GoTronic H11AA1](https://www.gotronic.fr/art-optocoupleur-h11aa1-31848.htm) | Composant de réserve pour variateur alternatif |
| **Opto-TRIAC** *(Secours)* | MOC3021M (U1) — Commande gâchette sans détection zéro | 1 | 1,04 € | 1,04 € | [GoTronic MOC3021](https://www.gotronic.fr/art-optotriac-moc3021-4202.htm) | Commande isolée du TRIAC de rechange |
| **TRIAC Puissance** *(Secours)*| BTA16-600C (Q1) — 16A, 600V | 1 | 1,60 € | 1,60 € | [GoTronic BTA16](https://www.gotronic.fr/art-triac-bta16-600c-22671.htm) | Étage de puissance alternatif de rechange |
| **Poulie Crantée Encodeur** | Poulie 16 à 18 dents (alésage $\varnothing 6\text{ mm}$ + méplat) | 1 | 0,00 € | *Interne* | Impression 3D (PETG / Nylon) | Entraînement de l'encodeur sur la courroie motrice |

---

## 💰 Synthèse Budgétaire

* **Budget total estimé :** **76,98 €**
* **Répartition :**
  * Section Capteurs (Encodeur + Endstops aiguille et plateau) : **43,90 €**
  * Section Puissance & Commande Moteur AC : **33,08 €**
  * Pièces d'adaptation mécanique : **0,00 €** (fabrication interne en impression 3D FDM).

---
**Voir aussi :**
* `[[Capteur_Fin_de_Course_Aiguille|Fiche Fin de Course Aiguille]]`
* `[[Encodeur_Rotatif_SEN0230|Fiche Encodeur SEN0230]]`
* `[[Module_Variateur_AC|Fiche Variateur AC RobotDyn]]`
* `[[Structure_Taches_Gantt|Planification Gantt (Tâche 4.1)]]`
* Fichier Excel source : [`reports/Produits_a_acheter.xlsx`](file:///home/rhomdev/Documents/Ecole/2026-27/projet_synth-se_broderie/reports/Produits_a_acheter.xlsx)
