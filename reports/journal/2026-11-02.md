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
  - planning
  - gantt
  - bom
statut: valide
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

### Pôle Machine & Prise en Main Manuelle
* **Auto-formation & enfilage :** Visionnage et application du tutoriel vidéo sur la machine Janome Facility 21 (`[[Tutoriel_Machine_a_Coudre]]`), maîtrise de la préparation de la canette et du réglage des tensions de fil.
* **Validation mécanique en direct :** 
  * Réalisation des premiers points de couture manuels réguliers.
  * Piquage complet d'une figure géométrique de test : **un carré complet piqué avec succès**.
  * Validation du bon fonctionnement cinématique de la machine (arbre supérieur, bielle, barre à aiguille, crochet rotatif et synchronisation de canette).

### Pôle Électronique & Capteurs — Réorientation Stratégique
* **Abandon définitif de la fourche optique H21A1 :**
  * Décision formalisée dans la `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision]]` : la fourche à fente accumule trop d'exigences et de contraintes (tension basse flottante à 2,0 V–2,5 V imposant un comparateur LM393 sur mesure, vulnérabilité critique aux poussières et peluches textiles, tolérances d'alignement mécanique trop étroites).
* **Validation du binôme Fin de Course + Encodeur SEN0230 :**
  1. **Capteur Fin de Course à Galet (PMH Aiguille) :** Microrupteur mécanique à roulette (type Endstop d'imprimante 3D) actionné par une came d'arbre. Permet d'éliminer les frottements à haute cadence (860 tr/min) et assure la détection franche de l'état haut ainsi que la procédure de **Homing (prise d'origine de l'aiguille)** au démarrage (`[[Capteur_Fin_de_Course_Aiguille]]`).
  2. **Encodeur Rotatif SEN0230 :** Validation du dimensionnement cinématique (poulie 16 à 18 dents en prise sur courroie motrice, maintenant la rotation entre 3965 et 4460 tr/min, sous le plafond constructeur de 5000 tr/min) pour l'asservissement en vitesse (`[[Encodeur_Rotatif_SEN0230]]`).

### Pôle Approvisionnement & Nomenclature (BOM)
* **Établissement du devis et de la liste des composants :**
  * Création du fichier source Excel `reports/Produits_a_acheter.xlsx` et de la note de synthèse `[[BOM_Liste_des_Besoins]]`.
  * **Budget total chiffré :** **76,98 €** comprenant :
    * 1 Encodeur rotatif SEN0230 GoTronic (29,90 €)
    * 1 Capteur fin de course flexible à galet pour l'aiguille (2,80 €)
    * 4 Butées mécaniques fin de course pour le plateau XY (11,20 €)
    * 1 Module variateur AC RobotDyn 230V avec découpe de phase (29,04 €)
    * Composants semi-conducteurs de rechange pour variateur AC discret (H11AA1, MOC3021, BTA16-600C : 4,04 €)
    * Poulie crantée encodeur 16-18 dents (fabrication interne en impression 3D FDM).

### Pôle Planification & Diagramme de Gantt
* **Intégration des contraintes calendaires majeures :**
  * **Jalon final impératif :** Soutenance orale finale fixée au **28 janvier 2027**.
  * **Trêve hivernale :** Vacances de Noël du **19 décembre 2026 au 03 janvier 2027** (période déclarée à faible activité).
  * **Rétro-planning validé :**
    * Novembre 2026 : Achats (BOM), redesign du plateau XY, impression 3D poulie/supports, montage mécanique, câblage complet MKS Base et sécurisation du variateur AC.
    * Décembre 2026 : Firmware de synchronisation (interruption AC ZC, homing aiguille, lecture encodeur) et première broderie réelle sur tissu **avant le départ en vacances (18 décembre)**.
    * Janvier 2027 : Rédaction intensive du rapport en LaTeX (`reports/rapport.tex`), diaporama, vidéo de démo et répétitions orales.
* **Mise à jour du planning :**
  * Synchronisation du fichier natif XML [`Planning_Gantt.gan`](file:///home/rhomdev/Documents/Ecole/2026-27/projet_synth-se_broderie/docs/01_Gestion_Projet/Planning_Gantt.gan) (9 phases WBS, 47 sous-tâches, 100% sur phases 1 à 3, affectation des ressources RhomDev et matazzo).
  * Publication de la fiche de décomposition arborescente `[[Structure_Taches_Gantt]]`.

### Pôle Infrastructure & Dépôt
* **Standardisation Git & Obsidian :**
  * Renforcement du `.gitignore` (filtrage des builds Arduino, environnements virtuels Python, fichiers KiCad et exclusion de `.obsidian/workspace.json`).
  * Reclassement des datasheets constructeurs dans `docs/datasheets/` (`fiche technique - janome facility 21.pdf`, `LM118-218-318.pdf`, `LM193-293-393.pdf`).
  * Création des dossiers manquants avec `.gitkeep` (`data/gcode/`, `data/mesures/`, `src/python/algorithms/`, `src/python/utils/`).
  * Mise à jour du Tableau de Bord Obsidian `[[00_Tableau_de_Bord]]` et du schéma d'architecture Mermaid.

---

## 2. Difficultés Rencontrées & Arbitrages

| Problème Rencontré | Impact sur le Projet | Décision & Solution Validée |
| :--- | :--- | :--- |
| **Complexité de la fourche optique H21A1** | Tension basse flottante (2V-2.5V), sensibilité extrême aux poussières textiles, besoin d'un comparateur LM393 sur mesure. | **Abandon définitif de la fourche optique**. Remplacement par un fin de course mécanique robuste. |
| **Frottement potentiel sur l'arbre à 860 tr/min** | Un levier métallique plat classique risquait de s'user prématurément par abrasion. | Choix d'un **microrupteur à galet (roulette)** assurant un roulement fluide et silencieux sur la came. |
| **Surcharge processeur de l'encodeur seul** | L'encodeur rotatif SEN0230 seul sans calage absolu risquait d'induire une dérive ou une surcharge d'interruption. | **Architecture hybride :** Fin de course pour le Homing / Point Mort Haut + Encodeur pour le suivi de vitesse. |
| **Fenêtre temporelle avant soutenance** | Trêve de Noël (19/12 au 03/01) et soutenance le 28/01. | Rétro-conception du planning pour **valider la première broderie avant Noël (18/12)** et réserver janvier aux livrables. |

---

## 3. Feuille de Route & Prochaines Actions Immédiates

- [ ] **Approvisionnement :** Lancer la commande des matériels selon la nomenclature `[[BOM_Liste_des_Besoins]]` (budget ~77 €).
- [ ] **Mécanique Plateau XY :** Revoir la conception CAO du plateau de travail (guidage linéaire, rigidité, fixation rapide du cadre de broderie).
- [ ] **Encodeur SEN0230 :** Modéliser et imprimer en 3D la poulie crantée (16 à 18 dents, alésage $\varnothing 6\text{ mm}$ avec méplat) en PETG/Nylon et concevoir son support châssis.
- [ ] **Fin de course Aiguille :** Modéliser la came d'arbre à pente douce et fixer le microrupteur à galet pour la détection du Point Mort Haut.
- [ ] **Fins de course Plateau :** Implanter les butées mécaniques de fin de course pour les axes $X$ et $Y$.
- [ ] **Variateur AC RobotDyn :** Réaliser le boîtier isolant sécurisé pour le 230V et câbler les signaux `ZC` et `PSM` sur la carte MKS Base V1.4.

---

## ⏱ Historique des Commits de la Journée
* **01:01:02** (`872c46f` - *RhomDev*) : `mj du projet grant, plus redesign de l'arborécence`
* **16:19:42** (`ab40df9` - *matazzo*) : `Add files via upload` (ajout de `reports/Produits_a_acheter.xlsx`)
* **15:20:35** (`56774a5` - *matazzo*) : `Create tuto machine à coudre`
* **13:17:25** (`defb284` - *RhomDev*) : `add datashet comparator`
