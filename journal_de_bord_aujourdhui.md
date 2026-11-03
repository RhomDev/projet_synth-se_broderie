---
titre: Journal de bord - 2026-11-02
date: 2026-11-02
tags:
  - journal
  - projet_broderie
  - test_machine
  - decision
  - mecanique
  - electronique
  - capteurs
statut: en cours
aliases:
  - journal_de_bord_aujourdhui
  - Journal du 02 Novembre 2026
---

# Journal de bord — 02 novembre 2026

## 👥 Intervenants
* **RhomDev** (Romaric Pradeau)
* **matazzo** (Maé Tazzioli)

---

## 1. Travaux Réalisés

### Pôle Machine & Tests Manuels de Couture
* **Validation mécanique en direct :** Test manuel complet de la machine à coudre Janome Facility 21.
* **Réalisations :**
  * Formation propre et régulière de points de couture sans blocage ni casse de fil.
  * Réalisation réussie d'une figure géométrique de test complète : **piquage réussi d'un carré**.
  * Ce test confirme le bon état mécanique de la machine, de la cinématique aiguille/canette et de la tension du fil.

### Pôle Électronique & Capteurs — Réorientation Stratégique
* **Abandon définitif de la fourche optique H21A1 :**
  * Analyse des essais précédents : le capteur optique à fente s'est avéré beaucoup trop complexe à mettre en place (étage de conditionnement AOP/LM393 indispensable pour contrer la tension flottante de 2V–2,5V, vulnérabilité critique aux poussières textiles et alignement mécanique contraignant dans un espace restreint).
* **Validation de la nouvelle architecture de synchronisation :**
  1. **Capteur Fin de Course Mécanique (Switch PMH à galet) :** Choix d'un microrupteur standard à galet (type endstop d'imprimante 3D) pour détecter la position haute de l'aiguille (Point Mort Haut). Le galet permet à la came de rouler sans frottement ni usure à haute vitesse (jusqu'à 860 tr/min). Il servira directement à la procédure de **Homing (prise d'origine)** de l'aiguille au démarrage.
  2. **Encodeur Rotatif SEN0230 (GoTronic) :** Intégration confirmée sur la courroie motrice. L'étude cinématique prouve qu'avec une poulie de 16 à 18 dents, la vitesse de rotation reste largement sous la limite constructeur de $5000\text{ tr/min}$ (environ $4000\text{ à } 4460\text{ tr/min}$ pour 860 tr/min machine).
* **Rédaction de la documentation :**
  * Rédaction de la note d'arbitrage : `[[Note_Decision_Capteur_Fourche_H21A1]]`.
  * Création des fiches techniques : `[[Capteur_Fin_de_Course_Aiguille]]` et `[[Encodeur_Rotatif_SEN0230]]`.

### Pôle Approvisionnement & Gestion de Projet
* **Établissement de la BOM (Bill of Materials) :** Préparation et formalisation de la liste des besoins matériels et composants à commander pour l'ensemble du projet.
* **Planification Gantt & Contraintes de Calendrier :**
  * Intégration de la **deadline finale impérative du 28 janvier 2027** (soutenance orale).
  * Intégration de la trêve des vacances de Noël (du 19 décembre 2026 au 03 janvier 2027) comme période à faible activité.
  * Rétro-planning : l'ensemble des essais d'intégration machine et premiers motifs brodés doit être finalisé avant le 18 décembre 2026 pour consacrer le mois de janvier à la rédaction du rapport LaTeX et aux répétitions de soutenance.
  * Mise à jour du fichier natif `[[Planning_Gantt.gan]]` et de la note de référence `[[Structure_Taches_Gantt]]`.

---

## 2. Difficultés Rencontrées & Arbitrages

* **Complexité et contraintes du capteur H21A1 :**
  * *Difficulté :* Le H21A1 exigeait une électronique sur mesure sensible et un calibrage de seuil analogique pointilleux qui fragilisaient la fiabilité globale de la brodeuse.
  * *Arbitrage :* Abandon du capteur optique. Passage à un contact sec franc (fin de course) pour le zéro machine/PMH + encodeur SEN0230 pour la mesure dynamique de vitesse et d'angle.

---

## 3. Feuille de Route & Prochaines Étapes Immédiates

- [ ] **Mise en place de l'encodeur SEN0230 :**
  - Modéliser et imprimer en 3D la poulie crantée (16–18 dents, alésage $\varnothing 6\text{ mm}$ avec méplat).
  - Fabriquer et monter le support rigide sur le bâti machine.
- [ ] **Installation du fin de course pour l'aiguille :**
  - Concevoir la came mécanique d'arbre et positionner le microrupteur pour le déclenchement au Point Mort Haut (PMH) et la gestion du homing.
- [ ] **Fins de course du plateau de travail :**
  - Monter et câbler les butées de fin de course pour les axes $X$ et $Y$.
- [ ] **Redesign du plateau de travail :**
  - Revoir la conception CAO du plateau mécanique supportant le cadre de broderie pour améliorer la rigidité, la planéité et le guidage.
- [ ] **Contrôle de vitesse moteur :**
  - Câbler et mettre en service le **variateur AC RobotDyn** (TRIAC) pour piloter électroniquement la vitesse du moteur 230V via l'ATmega2560.
- [ ] **Commandes :**
  - Valider et passer la commande selon la liste des besoins préparée.

---

## ⏱ Historique des commits
- 13:17:25 (defb284 - RhomDev) : add datashet comparator
