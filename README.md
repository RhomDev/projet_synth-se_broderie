# 🧵 Projet de Synthèse — Brodeuse Numérique CNC

Transformation et rétrofit d'une machine à coudre mécanique en **brodeuse numérique à commande numérique (CNC)** 2 axes ($X/Y$), synchronisée électroniquement sur la cinématique de l'aiguille.

---

## 🎯 Vue d'Ensemble

Ce projet multidisciplinaire associe mécanique, électronique de puissance, microcontrôleur temps réel et traitement vectoriel :
* **Mécanique :** Plateau 2 axes ($X/Y$) guidé sur rails linéaires et entraîné par courroies crantées GT2 supportant le cadre de broderie textile.
* **Électronique de Commande :** Carte mère **MKS Base V1.4** (microcontrôleur ATmega2560 cadencé à $16\text{ MHz}$ + drivers pas-à-pas A4982 intégrés).
* **Synchronisation Critique :** Détection optique ultra-rapide de l'aiguille en position haute via une **fourche infrarouge H21A1**, conditionnée par une carte comparatrice AOP (LM741) conçue sur mesure.
* **Puissance Moteur :** Régulation continue de la vitesse du moteur secteur $230\text{ V AC}$ de la machine par découpe de phase avec un **Module Variateur AC RobotDyn** (TRIAC isolé optiquement).
* **Chaîne Logicielle :** Pipeline Python pour la vectorisation de motifs, génération de G-code spécialisé et streamer série temps réel vers le firmware Arduino.

---

## 📂 Architecture du Projet

Le dépôt est organisé selon une hiérarchie modulaire et pérenne :

```
projet_synth-se_broderie/
├── docs/                                # 📚 Base de connaissances & Coffre Obsidian
│   ├── 00_Tableau_de_Bord.md            # Hub central et carte de navigation (MOC)
│   ├── Projet_Broderie.canvas           # Schéma visuel interactif sous Obsidian
│   ├── 01_Gestion_Projet/               # Cahier des charges, tâches et planning Gantt
│   ├── 02_Electronique_et_Puissance/    # Fiches techniques MKS Base, Variateur AC, Fast PWM
│   ├── 03_Capteurs_et_Synchronisation/  # Fiches capteur optique H21A1 et conditionnement AOP
│   ├── 04_Mecanique_et_Cinematique/     # Cinématique plateau XY et calculs de pas
│   ├── 05_Logiciel_et_Firmware/         # Architecture logicielle et protocoles
│   ├── assets/                          # Images, schémas de principe et graphiques
│   ├── datasheets/                      # Fiches constructeurs et schémas PDF
│   └── templates/                       # Modèles Obsidian (Fiche technique, Journal, Tâche)
│
├── hardware/                            # 🛠️ Conception Matérielle (CAO / EDA)
│   ├── elect/                           # Schémas et PCB KiCad (carte acquisition capteur)
│   ├── cad/                             # Modèles 3D (STEP, STL des pièces mécaniques)
│   └── exports/                         # Fichiers de fabrication (Gerbers, plans)
│
├── src/                                 # 💻 Code Source Exécutable
│   ├── arduino/                         # Firmware microcontrôleur ATmega2560 (C / C++)
│   │   ├── test_H21A1/                  # Test interruption INT2 capteur aiguille
│   │   └── lib/                         # Bibliothèques embarquées
│   └── python/                          # Traitement hôte & streaming G-code
│       ├── communication/               # Pont série USB (serial_bridge.py)
│       ├── algorithms/                  # Vectorisation & calcul de trajectoires
│       ├── utils/                       # Outils d'aide & prévisualisation
│       └── requirements.txt             # Dépendances Python
│
├── data/                                # 📊 Données d'Exécution & Mesures
│   ├── gcode/                           # Motifs de broderie vectorisés et fichiers G-code
│   └── mesures/                         # Relevés multimètre/oscilloscope et logs de test
│
└── reports/                             # 📝 Rapports & Livrables Académiques
    ├── journal/                         # Journaux de bord quotidiens datés
    ├── manuscript/                      # Rapport académique rédigé (LaTeX)
    ├── presentations/                   # Diaporamas et supports de soutenance
    └── figures/                         # Schémas haute résolution pour publications
```

---

## 🔮 Utilisation avec Obsidian

Le répertoire racine est configuré comme coffre (**Obsidian Vault**) prêt à l'emploi :
1. **Ouvrir le dossier :** Ouvrez simplement le dossier `projet_synth-se_broderie` dans Obsidian.
2. **Tableau de Bord :** La note [[00_Tableau_de_Bord|Tableau de Bord]] s'ouvre par défaut et offre une navigation immédiate vers chaque composant du projet.
3. **Canvas Visuel :** Explorez [[Projet_Broderie.canvas]] pour visualiser les liens dynamiques entre modules logiciels et cartes électroniques.
4. **Nouveaux Documents :** Utilisez la commande *Insert Template* (`Ctrl+T` / `Cmd+T`) pour générer instantanément des fiches techniques ou des journaux de bord formatés.

---

## 👥 Intervenants
* **Romaric Pradeau** (RhomDev)
* **Maé Tazzioli** (matazzo)
