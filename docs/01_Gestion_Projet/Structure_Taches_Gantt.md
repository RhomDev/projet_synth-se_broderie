---
titre: Structure des Tâches & Planification Gantt (WBS)
date: 2026-11-03
projet: Module Broderie
tags:
  - gestion_projet
  - gantt
  - wbs
  - roadmap
  - taches
statut: actif
aliases:
  - Planning Gantt
  - Structure Taches Gantt
  - WBS Projet Broderie
---

# 📊 Structure des Tâches pour Diagramme de Gantt (WBS)

Ce document fournit la décomposition arborescente complète des lots de travail (**Work Breakdown Structure - WBS**) du projet de brodeuse CNC. Il distingue clairement les **tâches terminées (FAIT)** et les **tâches restantes (À FAIRE)**, avec leurs durées, dépendances (prédécesseurs) et jalons, prête à être saisie ou synchronisée dans **GanttProject** (`[[Planning_Gantt.gan]]`).

---

## 🎯 Jalons Majeurs du Projet (Milestones)

* **Jalon M1 (26/09/2026) :** Lancement officiel & validation du cahier des charges initial.
* **Jalon M2 (02/11/2026) :** Validation de la couture manuelle (carré piqué) & validation de l'architecture capteurs (Fin de course galet + Encodeur SEN0230).
* **Jalon M3 (Mi-Novembre 2026) :** Réception des composants (BOM) & assemblage banc d'essai mécanique/électronique.
* **Jalon M4 (Début Décembre 2026) :** Premier mouvement XY synchronisé sur l'aiguille levée (boucle fermée).
* **Jalon M5 (18/12/2026) :** Première broderie réelle complète validée avant le départ en vacances.
* **Trêve Hivernale (19/12/2026 au 03/01/2027) :** Vacances de Noël (activité réduite / pause technique).
* **Jalon M6 (28/01/2027) :** 🎓 **SOUTENANCE ORALE FINALE DU PROJET (DEADLINE IMPÉRATIVE)**.

---

## 📋 Tableau Synthétique des Tâches (Format Gantt)

| ID | Phase / Tâche | Statut | Responsable | Durée | Début Prévu | Fin Prévue | Prédécesseur(s) | Livrable / Note |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1.0** | **PHASE 1 : CADRAGE & SPÉCIFICATIONS** | | | | | | | |
| 1.1 | Prise en main du sujet & définition du besoin | **[FAIT]** | Tous | 3j | 26/09/2026 | 28/09/2026 | - | `[[Cahier_des_Charges]]` |
| 1.2 | Analyse de la machine Janome Facility 21 | **[FAIT]** | RhomDev | 2j | 28/09/2026 | 29/09/2026 | 1.1 | Fiche technique Janome |
| 1.3 | Rédaction du Cahier des Charges fonctionnel | **[FAIT]** | Tous | 3j | 29/09/2026 | 01/10/2026 | 1.1, 1.2 | `[[Cahier_des_Charges]]` |
| 1.4 | Déploiement du coffre Obsidian & arborescence Git | **[FAIT]** | RhomDev | 2j | 01/10/2026 | 02/10/2026 | 1.3 | `[[00_Tableau_de_Bord]]` |
| **2.0** | **PHASE 2 : ÉTUDES PRÉLIMINAIRES & CHOIX TECHNIQUES** | | | | | | | |
| 2.1 | Analyse de la carte MKS Base V1.4 (ATmega2560) | **[FAIT]** | RhomDev | 3j | 29/09/2026 | 02/10/2026 | 1.3 | `[[Carte_MKS_Base_V1_4]]` |
| 2.2 | Étude du variateur AC RobotDyn (découpe de phase) | **[FAIT]** | RhomDev | 4j | 30/09/2026 | 05/10/2026 | 2.1 | `[[Module_Variateur_AC]]` |
| 2.3 | Étude théorique Fast PWM vs découpe de phase | **[FAIT]** | RhomDev | 2j | 30/09/2026 | 02/10/2026 | 2.2 | `[[Configuration_PWM_Arduino]]` |
| 2.4 | Étude initiale de la fourche optique H21A1 | **[FAIT]** | matazzo | 4j | 29/09/2026 | 03/10/2026 | 1.3 | `[[Fourche_Optique_H21A1]]` |
| 2.5 | Conception PCB comparateur AOP pour H21A1 | **[FAIT]** | RhomDev | 5j | 30/09/2026 | 07/10/2026 | 2.4 | `carte_acquisition_capteur` |
| 2.6 | Essais comparateur (LM318, TL081, LM393) | **[FAIT]** | matazzo | 3j | 20/10/2026 | 23/10/2026 | 2.5 | `[[comparateur-aop-choix]]` |
| 2.7 | Dimensionnement cinématique poulie encodeur | **[FAIT]** | matazzo | 2j | 21/10/2026 | 23/10/2026 | 1.2 | `[[2026-10-23]]` |
| **3.0** | **PHASE 3 : EXPÉRIMENTATION, TESTS MANUELS & PIVOT** | | | | | | | |
| 3.1 | Test manuel de couture machine (Janome) | **[FAIT]** | Tous | 1j | 02/11/2026 | 02/11/2026 | 1.2 | Réalisation d'un carré |
| 3.2 | Décision : abandon H21A1 au profit du fin de course | **[FAIT]** | Tous | 1j | 02/11/2026 | 02/11/2026 | 2.6, 3.1 | `[[Note_Decision_Capteur_Fourche_H21A1]]` |
| 3.3 | Choix du fin de course à galet (PMH & homing) | **[FAIT]** | Tous | 1j | 02/11/2026 | 03/11/2026 | 3.2 | `[[Capteur_Fin_de_Course_Aiguille]]` |
| 3.4 | Validation de l'encodeur rotatif SEN0230 | **[FAIT]** | matazzo | 1j | 02/11/2026 | 03/11/2026 | 2.7, 3.2 | `[[Encodeur_Rotatif_SEN0230]]` |
| 3.5 | Établissement de la liste des besoins (BOM) | **[FAIT]** | Tous | 1j | 02/11/2026 | 03/11/2026 | 3.3, 3.4 | Liste des composants |
| **4.0** | **PHASE 4 : CONCEPTION MÉCANIQUE & APPROVISIONNEMENT** | | | | | | | |
| 4.1 | Commande des composants et fournitures (BOM) | **[À FAIRE]** | Tous | 5j | 04/11/2026 | 10/11/2026 | 3.5 | Bons de commande |
| 4.2 | Revoir le design CAO du plateau de travail XY | **[À FAIRE]** | matazzo | 5j | 04/11/2026 | 11/11/2026 | 3.1 | Modèle 3D plateau |
| 4.3 | Modélisation 3D de la poulie encodeur (16-18 dents) | **[À FAIRE]** | matazzo | 2j | 04/11/2026 | 06/11/2026 | 3.4 | Fichier STL poulie |
| 4.4 | Impression 3D de la poulie crantée (PETG/Nylon) | **[À FAIRE]** | matazzo | 1j | 06/11/2026 | 07/11/2026 | 4.3 | Pièce mécanique imprimée |
| 4.5 | Conception et impression du support encodeur | **[À FAIRE]** | matazzo | 3j | 07/11/2026 | 11/11/2026 | 4.4 | Support rigide monté |
| 4.6 | Conception de la came d'arbre & support switch PMH | **[À FAIRE]** | RhomDev | 3j | 05/11/2026 | 09/11/2026 | 3.3 | Support + came PMH |
| 4.7 | Supports et butées des fins de course plateau X/Y | **[À FAIRE]** | matazzo | 3j | 09/11/2026 | 12/11/2026 | 4.2 | Butées X/Y installées |
| 4.8 | Fabrication / usinage du nouveau plateau de travail | **[À FAIRE]** | matazzo | 4j | 11/11/2026 | 16/11/2026 | 4.2 | Plateau assemblé |
| **5.0** | **PHASE 5 : ÉLECTRONIQUE, CÂBLAGE & PUISSANCE** | | | | | | | |
| 5.1 | Réception & vérification des composants commandés | **[À FAIRE]** | Tous | 1j | 11/11/2026 | 12/11/2026 | 4.1 | Matériel réceptionné |
| 5.2 | Intégration sous boîtier sécurisé du variateur AC | **[À FAIRE]** | RhomDev | 3j | 12/11/2026 | 16/11/2026 | 5.1 | Boîtier 230V isolé |
| 5.3 | Câblage des moteurs pas-à-pas X/Y sur MKS Base | **[À FAIRE]** | RhomDev | 2j | 12/11/2026 | 14/11/2026 | 2.1, 4.8 | Moteurs raccordés |
| 5.4 | Câblage des fins de course (Aiguille PMH, X-Min, Y-Min)| **[À FAIRE]** | RhomDev | 2j | 13/11/2026 | 16/11/2026 | 4.6, 4.7 | Faisceau endstops |
| 5.5 | Câblage de l'encodeur SEN0230 sur la carte MKS | **[À FAIRE]** | RhomDev | 1j | 16/11/2026 | 17/11/2026 | 4.5, 5.1 | Canaux A/B connectés |
| 5.6 | Validation électrique globale sous tension (12V & 230V)| **[À FAIRE]** | Tous | 2j | 17/11/2026 | 19/11/2026 | 5.2, 5.3, 5.4, 5.5 | Banc électrique validé |
| **6.0** | **PHASE 6 : DÉVELOPPEMENT FIRMWARE ARDUINO (C++)** | | | | | | | |
| 6.1 | Firmware : Routine d'interruption ZC & commande TRIAC| **[À FAIRE]** | RhomDev | 4j | 16/11/2026 | 20/11/2026 | 5.2 | Contrôle moteur AC |
| 6.2 | Firmware : Routine de décodage encodeur (vitesse) | **[À FAIRE]** | RhomDev | 3j | 18/11/2026 | 21/11/2026 | 5.5 | Mesure de rotation |
| 6.3 | Firmware : Séquence de Homing aiguille (PMH galet) | **[À FAIRE]** | RhomDev | 2j | 20/11/2026 | 23/11/2026 | 5.4, 6.1 | Homing aiguille validé |
| 6.4 | Firmware : Séquence de Homing plateau X/Y | **[À FAIRE]** | RhomDev | 2j | 21/11/2026 | 24/11/2026 | 5.3, 5.4 | Homing axes X/Y validé |
| 6.5 | Firmware : Machine à états de synchronisation aiguille | **[À FAIRE]** | RhomDev | 5j | 24/11/2026 | 30/11/2026 | 6.2, 6.3, 6.4 | Fenêtre d'avance sûre |
| 6.6 | Firmware : Interpréteur G-code (mouvements X/Y) | **[À FAIRE]** | RhomDev | 4j | 27/11/2026 | 02/12/2026 | 6.5 | Décodage G0/G1 |
| **7.0** | **PHASE 7 : SUITE LOGICIELLE PYTHON HÔTE** | | | | | | | |
| 7.1 | Streamer USB série robuste (`serial_bridge.py`) | **[À FAIRE]** | matazzo | 3j | 20/11/2026 | 24/11/2026 | 2.1 | Pont série avec ack 'ok' |
| 7.2 | Module de vectorisation & extraction des points (SVG) | **[À FAIRE]** | matazzo | 5j | 24/11/2026 | 30/11/2026 | 7.1 | Script vectorisation |
| 7.3 | Générateur de G-code spécialisé broderie | **[À FAIRE]** | matazzo | 4j | 30/11/2026 | 04/12/2026 | 7.2 | Fichier G-code généré |
| 7.4 | Visualiseur 2D de trajectoires avant broderie | **[À FAIRE]** | matazzo | 3j | 03/12/2026 | 07/12/2026 | 7.3 | IHM ou plot matplotlib |
| **8.0** | **PHASE 8 : INTÉGRATION GLOBALE & TESTS SUR TISSU (AVANT NOËL)** | | | | | | | |
| 8.1 | Essais à vide : synchronisation mouvement sans fil | **[À FAIRE]** | Tous | 3j | 04/12/2026 | 08/12/2026 | 6.6, 7.1 | Cycle synchronisé |
| 8.2 | Première broderie réelle : ligne droite & carré auto | **[À FAIRE]** | Tous | 3j | 08/12/2026 | 11/12/2026 | 8.1, 7.3 | Premier échantillon |
| 8.3 | Optimisation de vitesse & réglage de la découpe AC | **[À FAIRE]** | Tous | 3j | 11/12/2026 | 15/12/2026 | 8.2 | Cadence maximale |
| 8.4 | Broderie d'un motif complexe complet avant Noël | **[À FAIRE]** | Tous | 3j | 15/12/2026 | 18/12/2026 | 8.3, 7.4 | Démonstrateur textile |
| **-** | **TRÊVE HIVERNALE : VACANCES DE NOËL** | **[PAUSE]** | Tous | 10j | 19/12/2026 | 03/01/2027 | 8.4 | Activité allégée |
| **9.0** | **PHASE 9 : RAPPORT ÉCRIT, DIAPORAMA & SOUTENANCE (JANVIER)** | | | | | | | |
| 9.1 | Rédaction intensive du rapport de synthèse (LaTeX) | **[À FAIRE]** | Tous | 10j | 04/01/2027 | 15/01/2027 | 8.4 | `reports/rapport.tex` |
| 9.2 | Préparation du diaporama & vidéo de démonstration | **[À FAIRE]** | Tous | 5j | 15/01/2027 | 22/01/2027 | 9.1 | Présentation soutenance |
| 9.3 | Répétitions orales & calage du timing (20-30 min) | **[À FAIRE]** | Tous | 4j | 22/01/2027 | 27/01/2027 | 9.2 | Équipe prête |
| 9.4 | 🎓 **SOUTENANCE ORALE FINALE (DEADLINE OFFICIELLE)** | **[JALON]** | Tous | 0j | **28/01/2027**| **28/01/2027**| 9.3 | Présentation jury |

---

## 🛠️ Instructions pour GanttProject

Pour importer ou mettre à jour ce planning dans `[[Planning_Gantt.gan]]` :
1. **Ouvrir GanttProject** et charger le fichier [`docs/01_Gestion_Projet/Planning_Gantt.gan`](file:///home/rhomdev/Documents/Ecole/2026-27/projet_synth-se_broderie/docs/01_Gestion_Projet/Planning_Gantt.gan).
2. **Créer les 9 groupes de tâches (Phases 1 à 9)** en définissant la propriété *Tâche récapitulative / Projet*.
3. **Affecter les prédécesseurs** pour établir le chemin critique (ex. : la commande 4.1 dépend de 3.5 ; le câblage 5.x précède le firmware 6.x).
4. **Mettre à jour les taux d'avancement :**
   * Phases 1.0, 2.0 et 3.0 : **100% terminées**.
   * Phase 4.0 : **20% (BOM prête)**.
   * Phases 5.0 à 9.0 : **0% à 10% (en attente des composants)**.

---
**Voir aussi :**
* `[[Planning_Gantt.gan|Fichier Source GanttProject]]`
* `[[Suivi_des_Taches|Feuille de Route Active]]`
* `[[Cahier_des_Charges|Cahier des Charges Fonctionnel]]`
* `[[00_Tableau_de_Bord|Tableau de Bord Général]]`
