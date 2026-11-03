---
titre: 🧵 Tableau de Bord — Projet Brodeuse Numérique CNC
date: 2026-10-01
projet: Module Broderie
tags:
  - dashboard
  - moc
  - projet_broderie
  - synthese
statut: actif
aliases:
  - Tableau de Bord
  - Accueil
  - Home
  - MOC
---

# 🧵 Tableau de Bord — Brodeuse Numérique CNC

> [!NOTE]
> **Projet de Synthèse :** Rétrofit et automatisation d'une machine à coudre conventionnelle en brodeuse numérique 2 axes ($X/Y$) pilotée par G-code, synchronisée sur la cinématique de l'aiguille.

---

## 🗺️ Navigation Rapide (Map of Content)

```
                              [ PROJET BRODERIE CNC ]
                                         |
     +---------------+---------------+---+---------------+---------------+
     |               |               |                   |               |
     v               v               v                   v               v
📋 Gestion &     ⚡ Électronique    👁️ Capteurs &       ⚙️ Mécanique &   💻 Logiciel &
   Feuille Route    & Puissance     Synchronisation      Cinématique     Firmware
```

### 📋 1. Gestion de Projet & Spécifications
* `[[Cahier_des_Charges|🎯 Cahier des Charges & Objectifs]]` — Spécifications issues du sujet initial, missions et jalons.
* `[[Suivi_des_Taches|📋 Feuille de Route & Suivi des Tâches]]` — Checklist active, priorités du moment et tâches futures.
* `[[BOM_Liste_des_Besoins|🛒 Nomenclature des Besoins (BOM)]]` — Devis et liste des composants à commander (~77 €).
* `[[Structure_Taches_Gantt|📊 Décomposition des Tâches WBS (Gantt)]]` — Liste structurée des tâches faites et à faire avec dépendances.
* `[[Planning_Gantt.gan|📅 Fichier GanttProject]]` — Fichier XML natif GanttProject (deadline 28/01/2027).
* `[[Tutoriel_Machine_a_Coudre|🧵 Tutoriel Vidéo Janome Facility 21]]` — Guide d'enfilage et de fonctionnement machine.

### ⚡ 2. Électronique & Puissance
* `[[Carte_MKS_Base_V1_4|🧠 Carte MKS Base V1.4]]` — Cerveau de commande (ATmega2560), drivers A4982, entrées capteurs.
* `[[Module_Variateur_AC|🔌 Module Variateur AC (RobotDyn)]]` — Découpe de phase par TRIAC pour régulation moteur 230V.
* `[[Configuration_PWM_Arduino|⏱️ Configuration Fast PWM (25 kHz)]]` — Calcul des registres Timer 1 sur microcontrôleur.

### 👁️ 3. Capteurs & Synchronisation Aiguille
* `[[Note_Decision_Capteur_Fourche_H21A1|📌 Note de Décision : Abandon Fourche H21A1 & Choix Fin de Course + Encodeur]]` — Justification du passage au contact sec pour le homing et à l'encodeur SEN0230.
* `[[Capteur_Fin_de_Course_Aiguille|🛑 Capteur Fin de Course Aiguille (Point Mort Haut & Homing)]]` — Détection binaire du PMH et prise d'origine machine.
* `[[Encodeur_Rotatif_SEN0230|🔄 Encodeur Rotatif SEN0230]]` — Suivi cinématique et mesure de vitesse de rotation (GoTronic).
* `[[Fourche_Optique_H21A1|⚠️ Fourche Optique H21A1 (Archivée)]]` — Étude initiale et raisons de son abandon.
* `[[Conditionnement_AOP_H21A1|🛠️ Conditionnement AOP LM393 (Archivé)]]` — Conception du module comparateur (obsolète suite à l'abandon du H21A1).
* `[[comparateur-aop-choix|🔬 Choix de l'AOP Comparateur (Archivé)]]` — Comparatif LM318/TL081 vs LM393.

### ⚙️ 4. Mécanique & Cinématique
* `[[Plateau_XY_et_Mecanique|📐 Plateau XY, Redesign & Butées de Fin de Course]]` — Cadre de broderie, redesign du plateau de travail, courroies GT2 et butées X/Y.

### 💻 5. Logiciel & Firmware
* `[[Architecture_Logicielle|💻 Architecture Logicielle & Pipeline Numérique]]` — Chaîne Python (vectorisation/G-code) + Cœur temps réel Arduino.
* **Firmware Arduino :** Routine de homing aiguille, lecture de l'encodeur SEN0230 et contrôle du variateur AC.
* **Communication :** [[serial_bridge.py]].

### 📅 6. Journaux de Bord Quotidiens
* `[[journal_de_bord_aujourdhui|📅 Journal du 02 Novembre 2026 (Aujourd'hui)]]` — Essais manuels réussis (points & carré), abandon de la fourche, choix du fin de course + encodeur SEN0230, liste des besoins et variateur AC.
* `[[2026-10-23|📅 Journal du 23 Octobre 2026]]` — Étude des AOP et dimensionnement poulie encodeur.
* `[[2026-10-01|📅 Journal du 01 Octobre 2026]]` — Restructuration complète de l'architecture projet & déploiement Obsidian.
* `[[2026-09-30|📅 Journal du 30 Septembre 2026]]` — Conception PCB comparateur AOP & étude du variateur AC RobotDyn.
* `[[2026-09-29|📅 Journal du 29 Septembre 2026]]` — Étude capteur H21A1, carte MKS Base et initialisation Gantt.

---

## 🧩 Architecture Système Visuelle

```mermaid
flowchart TD
    subgraph PC["🖥️ Ordinateur Hôte"]
        Motif["Motif Graphique<br>(SVG / DST / PES)"] --> Traitement["Générateur G-code<br>Python (`src/python/`)"]
        Traitement --> Streamer["Streamer Série USB<br>`serial_bridge.py`"]
    end

    subgraph MKS["🧠 Carte MKS Base V1.4 (ATmega2560)"]
        USB["Liaison Série USB<br>115200 bauds"] --> Parser["Interpréteur G-code<br>& Synchronisation"]
        Parser --> ControlStep["Contrôle Moteurs Pas-à-Pas<br>(Drivers A4982)"]
        Parser --> ControlAC["Commande Découpe de Phase<br>(Pulse Gate PSM)"]
        ZeroCross["Détection Zéro (ZC)<br>Interruption 100 Hz"] --> ControlAC
        EndstopAig["Entrée Fin de Course PMH<br>(Homing & Sécurité Aiguille)"] --> Parser
        EncoderIn["Entrées Encodeur SEN0230<br>(Vitesse & Position Angulaire)"] --> Parser
        EndstopsXY["Entrées Fins de Course X/Y<br>(Homing Plateau)"] --> Parser
    end

    subgraph Hardware["⚙️ Machine & Actionneurs"]
        ControlStep --> MotXY["Moteurs NEMA 17<br>Axes X & Y Plateau"]
        ControlAC --> Dimmer["Module Variateur AC<br>(RobotDyn TRIAC)"]
        Dimmer --> MotCouture["Moteur 230V AC<br>Entraînement Machine"]
        MotCouture --> Mecanisme["Cinématique Aiguille<br>& Canette"]
        Mecanisme --> EndstopSwitch["Fin de Course Mécanique<br>(Point Mort Haut Came)"]
        EndstopSwitch --> EndstopAig
        MotCouture --> EncoderDevice["Encodeur SEN0230<br>(Poulie sur courroie)"]
        EncoderDevice --> EncoderIn
        MotXY --> PlateauLimit["Butées Mécaniques<br>(Fins de course X & Y)"]
        PlateauLimit --> EndstopsXY
    end

    Streamer <== USB ==> USB
```

    Streamer <== USB ==> USB
```

---

## 🚀 Vue Interactive Canvas
> [!TIP]
> Ouvrez la vue visuelle interactive complète : **[[Projet_Broderie.canvas]]** pour explorer les blocs d'interconnexion matérielle et logicielle sous forme de schéma dynamique.

---

## 📚 Bibliothèque de Datasheets & Schémas PDF
* 📄 [[capteur_position_H21A1.pdf|Datasheet Fourche Optique H21A1]]
* 📄 [[Module_Variateur_AC_RobotDyn.pdf|Documentation Variateur AC RobotDyn]]
* 📄 [[MKS_BASE_PINS.pdf|Brochage Connecteurs MKS Base V1.4]]
* 📄 [[MKS_BASE_V1_4_Schematic_Alimentation_P1.pdf|Schéma MKS Base - Alimentation]]
* 📄 [[MKS_BASE_V1_4_Schematic_MOSFETs_P2.pdf|Schéma MKS Base - MOSFETs]]
* 📄 [[MKS_BASE_V1_4_Schematic_Drivers_P3.pdf|Schéma MKS Base - Drivers Pas-à-Pas]]
* 📄 [[ATMEGA640.PDF|Datasheet Microcontrôleur ATmega2560 / 640]]

---

## ⚙️ Outils & Modèles Obsidian
Pour créer une nouvelle note propre et standardisée, utilisez les modèles dans `docs/templates/` :
* [[Template_Fiche_Technique.md]] (pour un composant électronique ou mécanique)
* [[Template_Journal.md]] (pour le rapport quotidien de séance)
* [[Template_Tache.md]] (pour une nouvelle tâche ou réunion)
