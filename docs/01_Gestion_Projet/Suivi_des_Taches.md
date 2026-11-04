---
titre: Suivi des Tâches & Feuille de Route
date: 2026-11-03
projet: Module Broderie
tags:
  - gestion_projet
  - taches
  - roadmap
  - wbs
statut: en cours
aliases:
  - Tache sur machine
  - Suivi des Taches
  - Roadmap
---

# Suivi des Tâches & Feuille de Route

> [!IMPORTANT]
> Ce fichier est synchronisé avec la [[Structure_Taches_Gantt|WBS Gantt]] en date du **2026-11-03**.
> Prochaine deadline critique : 🎓 **Soutenance orale le 28/01/2027**.

---

## 🚦 Tableau d'Avancement Général

| Phase | Description | Avancement | Responsable(s) |
| :---: | :--- | :---: | :--- |
| 1.0 | Cadrage & Spécifications | ✅ 100% | Tous |
| 2.0 | Études Préliminaires & Choix Techniques | ✅ 100% | RhomDev & matazzo |
| 3.0 | Expérimentation, Tests Manuels & Pivot | ✅ 100% | Tous |
| 4.0 | Conception Mécanique & Approvisionnement | 🟡 ~20% | matazzo & Tous |
| 5.0 | Électronique, Câblage & Puissance | ⚪ 0% | RhomDev & Tous |
| 6.0 | Développement Firmware Arduino (C++) | ⚪ 0% | RhomDev |
| 7.0 | Suite Logicielle Python Hôte | ⚪ 0% | matazzo |
| 8.0 | Intégration Globale & Tests sur Tissu | ⚪ 0% | Tous |
| 9.0 | Rapport, Diaporama & Soutenance | ⚪ 0% | Tous |

---

## PHASE 1 : CADRAGE & SPÉCIFICATIONS ✅

- [x] **1.1 — Prise en main du sujet & définition du besoin** [Tous]
  - Responsable : Tous — Fait le 26/09 → 28/09/2026
- [x] **1.2 — Analyse de la machine Janome Facility 21** [RhomDev]
  - Responsable : RhomDev — Fait le 28/09 → 29/09/2026
- [x] **1.3 — Rédaction du Cahier des Charges fonctionnel** [Tous]
  - Responsable : Tous — Fait le 29/09 → 01/10/2026
- [x] **1.4 — Déploiement du coffre Obsidian & arborescence Git** [RhomDev]
  - Responsable : RhomDev — Fait le 01/10 → 02/10/2026

---

## PHASE 2 : ÉTUDES PRÉLIMINAIRES & CHOIX TECHNIQUES ✅

- [x] **2.1 — Analyse de la carte MKS Base V1.4 (ATmega2560)** [RhomDev]
  - Responsable : RhomDev — Fait le 29/09 → 02/10/2026
- [x] **2.2 — Étude du variateur AC RobotDyn (découpe de phase)** [RhomDev]
  - Responsable : RhomDev — Fait le 30/09 → 05/10/2026
- [x] **2.3 — Étude théorique Fast PWM vs découpe de phase** [RhomDev]
  - Responsable : RhomDev — Fait le 30/09 → 02/10/2026
- [x] **2.4 — Étude initiale de la fourche optique H21A1** [matazzo]
  - Responsable : matazzo — Fait le 29/09 → 03/10/2026
- [x] **2.5 — Conception PCB comparateur AOP pour H21A1** [RhomDev]
  - Responsable : RhomDev — Fait le 30/09 → 07/10/2026
- [x] **2.6 — Essais comparateur (LM318, TL081, LM393)** [matazzo]
  - Responsable : matazzo — Fait le 20/10 → 23/10/2026
- [x] **2.7 — Dimensionnement cinématique poulie encodeur** [matazzo]
  - Responsable : matazzo — Fait le 21/10 → 23/10/2026

---

## PHASE 3 : EXPÉRIMENTATION, TESTS MANUELS & PIVOT ✅

- [x] **3.1 — Test manuel de couture machine (Janome)** [Tous]
  - Responsable : Tous — Fait le 02/11/2026
- [x] **3.2 — Décision : abandon H21A1 au profit du fin de course** [Tous]
  - Responsable : Tous — Fait le 02/11/2026
- [x] **3.3 — Choix du fin de course à galet (PMH & homing)** [Tous]
  - Responsable : Tous — Fait le 02/11 → 03/11/2026
- [x] **3.5 — Établissement de la liste des besoins (BOM)** [Tous]
  - Responsable : Tous — Fait le 02/11 → 03/11/2026
- [x] **3.6 — Etude du fonction de la machine a coudre** [Tous
 - Responsable : Tous — Fait le 02/11 → 03/11/2026
---

## PHASE 4 : CONCEPTION MÉCANIQUE & APPROVISIONNEMENT 🟡

- [ ] **4.1 — Commande des composants et fournitures (BOM)** [Tous]
  - Responsable : Tous — Prévu : 04/11 → 10/11/2026
  - Livrable : Bons de commande validés
- [ ] **4.2 — Revoir le design CAO du plateau de travail XY** [matazzo]
  - Responsable : matazzo — Prévu : 04/11 → 11/11/2026
  - Livrable : Modèle 3D plateau (optimisation dimensions, rigidification, fixation)
- [ ] **4.3 — Supports et butées des fins de course plateau X/Y** [matazzo]
  - Responsable : matazzo — Prévu : 09/11 → 12/11/2026
  - Livrable : Butées X/Y installées
  - Prédécesseur : 4.2
- [ ] **4.4 — Fabrication / usinage du nouveau plateau de travail** [matazzo]
  - Responsable : matazzo — Prévu : 11/11 → 16/11/2026
  - Livrable : Plateau assemblé
  - Prédécesseur : 4.2
- [ ] **4.5 — Conception support détection aiguille** [matazzo]

---

## PHASE 5 : ÉLECTRONIQUE, CÂBLAGE & PUISSANCE ⚪

- [ ] **5.1 — Réception & vérification des composants commandés** [Tous]
  - Responsable : Tous — Prévu : 11/11 → 12/11/2026
  - Livrable : Matériel réceptionné et conforme
  - Prédécesseur : 4.1
- [ ] **5.2 — Intégration sous boîtier sécurisé du variateur AC** [RhomDev]
  - Responsable : RhomDev — Prévu : 12/11 → 16/11/2026
  - Livrable : Boîtier 230V isolé et sécurisé
  - Prédécesseur : 5.1
- [ ] **5.3 — Câblage des moteurs pas-à-pas X/Y sur MKS Base** [RhomDev]
  - Responsable : RhomDev — Prévu : 12/11 → 14/11/2026
  - Livrable : Moteurs NEMA 17 raccordés
  - Prédécesseur : 2.1, 4.4
- [ ] **5.4 — Câblage des fins de course (Aiguille PMH, X-Min, Y-Min)** [RhomDev]
  - Responsable : RhomDev — Prévu : 13/11 → 16/11/2026
  - Livrable : Faisceau endstops complet
  - Prédécesseur : 4.3
- [ ] **5.5 — Validation électrique globale sous tension (12V & 230V)** [Tous]
  - Responsable : Tous — Prévu : 17/11 → 19/11/2026
  - Livrable : Banc électrique validé sans défaut
  - Prédécesseur : 5.2, 5.3, 5.4
- [ ] **5.6 — Conception et Teste du module de détection partie élect** [RhomDev]

---

## PHASE 6 : DÉVELOPPEMENT FIRMWARE ARDUINO (C++) ⚪

- [ ] **6.1 — Firmware : Routine d'interruption ZC & commande TRIAC** [RhomDev]
  - Responsable : RhomDev — Prévu : 16/11 → 20/11/2026
  - Livrable : Contrôle moteur AC fonctionnel
  - Prédécesseur : 5.2
- [ ] **6.2 — Firmware : Séquence de Homing aiguille (PMH galet)** [matazzo]
  - Responsable : RhomDev — Prévu : 20/11 → 23/11/2026
  - Livrable : Homing aiguille validé
  - Prédécesseur : 5.4, 6.1
- [ ] **6.3 — Firmware : Séquence de Homing plateau X/Y** [matazzo]
  - Responsable : RhomDev — Prévu : 21/11 → 24/11/2026
  - Livrable : Homing axes X/Y validé
  - Prédécesseur : 5.3, 5.4
- [ ] **6.4 — Firmware : Machine à états de synchronisation aiguille** [RhomDev]
  - Responsable : RhomDev — Prévu : 24/11 → 30/11/2026
  - Livrable : Fenêtre d'avance sûre déterminée
  - Prédécesseur : 6.2, 6.3, 6.4
- [ ] **6.5 — Firmware : Interpréteur G-code (mouvements X/Y)** [RhomDev]
  - Responsable : RhomDev — Prévu : 27/11 → 02/12/2026
  - Livrable : Décodage G0/G1 opérationnel
  - Prédécesseur : 6.5
- [ ] **6.6 — Firmware : Machine à états de synchronisation aiguille** [RhomDev]

---

## PHASE 7 : SUITE LOGICIELLE PYTHON HÔTE ⚪

- [ ] **7.1 — Streamer USB série robuste (serial_bridge.py)** [RhomDev]
  - Responsable : matazzo — Prévu : 20/11 → 24/11/2026
  - Livrable : Pont série avec acquittement 'ok'
  - Prédécesseur : 2.1
- [ ] **7.2 — Module de vectorisation & extraction des points (SVG)** [RhomDev]
  - Responsable : matazzo — Prévu : 24/11 → 30/11/2026
  - Livrable : Script vectorisation fonctionnel
  - Prédécesseur : 7.1
- [ ] **7.3 — Générateur de G-code spécialisé broderie** [RhomDev]
  - Responsable : matazzo — Prévu : 30/11 → 04/12/2026
  - Livrable : Fichier G-code généré depuis SVG
  - Prédécesseur : 7.2
- [ ] **7.4 — Visualiseur 2D de trajectoires avant broderie** [RhomDev]
  - Responsable : matazzo — Prévu : 03/12 → 07/12/2026
  - Livrable : IHM ou plot matplotlib
  - Prédécesseur : 7.3

---

## PHASE 8 : INTÉGRATION GLOBALE & TESTS SUR TISSU (AVANT NOËL) ⚪

- [ ] **8.1 — Essais à vide : synchronisation mouvement sans fil** [Tous]
  - Responsable : Tous — Prévu : 04/12 → 08/12/2026
  - Livrable : Cycle synchronisé validé
  - Prédécesseur : 6.6, 7.1
- [ ] **8.2 — Première broderie réelle : ligne droite & carré auto** [Tous]
  - Responsable : Tous — Prévu : 08/12 → 11/12/2026
  - Livrable : Premier échantillon textile
  - Prédécesseur : 8.1, 7.3
- [ ] **8.3 — Optimisation de vitesse & réglage de la découpe AC** [Tous]
  - Responsable : Tous — Prévu : 11/12 → 15/12/2026
  - Livrable : Cadence maximale atteinte
  - Prédécesseur : 8.2
- [ ] **8.4 — Broderie d'un motif complexe complet avant Noël** [Tous]
  - Responsable : Tous — Prévu : 15/12 → 18/12/2026
  - Livrable : Démonstrateur textile complet
  - Prédécesseur : 8.3, 7.4

---

> [!WARNING]
> **TRÊVE HIVERNALE — Vacances de Noël : 19/12/2026 → 03/01/2027**
> Activité allégée / pause technique (10 jours).

---

## PHASE 9 : RAPPORT ÉCRIT, DIAPORAMA & SOUTENANCE (JANVIER) ⚪

- [ ] **9.1 — Rédaction intensive du rapport de synthèse (LaTeX)** [Tous]
  - Responsable : Tous — Prévu : 04/01 → 15/01/2027
  - Livrable : `reports/rapport.tex`
  - Prédécesseur : 8.4
- [ ] **9.2 — Préparation du diaporama & vidéo de démonstration** [Tous]
  - Responsable : Tous — Prévu : 15/01 → 22/01/2027
  - Livrable : Présentation soutenance + vidéo démo
  - Prédécesseur : 9.1
- [ ] **9.3 — Répétitions orales & calage du timing (20-30 min)** [Tous]
  - Responsable : Tous — Prévu : 22/01 → 27/01/2027
  - Livrable : Équipe prête et calée
  - Prédécesseur : 9.2
- [ ] **9.4 — 🎓 SOUTENANCE ORALE FINALE (DEADLINE OFFICIELLE)** [Tous]
  - Responsable : Tous — **28/01/2027**
  - Jalon impératif : Présentation devant le jury

---

**Liens utiles :**
*  [[Structure_Taches_Gantt|Décomposition des Tâches & WBS Gantt]] 
*  [[Planning_Gantt.gan|Fichier GanttProject]] 
*  [[00_Tableau_de_Bord|Tableau de Bord Principal]] 
*  [[Cahier_des_Charges|Cahier des Charges]] 
