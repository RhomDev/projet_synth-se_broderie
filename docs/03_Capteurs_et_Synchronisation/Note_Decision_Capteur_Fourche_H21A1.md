---
titre: Note de Décision — Abandon de la Fourche Optique H21A1 et Choix Fin de Course + Encodeur SEN0230
date: 2026-11-02
projet: Module Broderie
tags:
  - decision
  - electronique
  - capteur
  - mecanique
  - homing
  - encodeur
  - fin_de_course
  - synchronisation
statut: valide
aliases:
  - Note de Décision Capteur Fourche
  - Decision Fourche H21A1 vs Encodeur
  - Arbitrage Capteur Aiguille
  - Abandon Fourche H21A1
---

# 📌 Note de Décision — Abandon de la Fourche Optique H21A1 & Nouvelle Stratégie de Synchronisation (Fin de Course + Encodeur SEN0230)

## 1. Contexte et Motif de l'Arbitrage

Dans le système de broderie numérique, la synchronisation du déplacement du plateau $X/Y$ avec la cinématique de l'aiguille est essentielle : le tissu doit être strictement immobile lorsque l'aiguille est engagée dans la matière, et le déplacement n'est autorisé que lorsque l'aiguille est en position haute (Point Mort Haut - PMH).

Initialement, une **fourche optique infrarouge H21A1** associée à un drapeau mécanique d'obturation avait été retenue et étudiée en détail (avec conception d'un module comparateur LM393 pour corriger une tension basse flottante à $2{,}0\text{ V} - 2{,}5\text{ V}$).

> [!IMPORTANT]
> **Décision prise le 02 novembre 2026 :**
> L'équipe a acté l'**abandon définitif de la fourche optique H21A1**. Ce capteur s'est avéré trop contraignant, trop complexe à fiabiliser mécaniquement et électroniquement, et inadapté aux réalités de l'atelier textile.
> Le système bascule sur une **architecture hybride éprouvée et robuste** :
> 1. Un **capteur fin de course standard (contact sec mécanique / switch)** pour détecter l'état haut de la machine et gérer le **homing (prise d'origine)** de l'aiguille.
> 2. Un **encodeur rotatif incrémental optique SEN0230** (GoTronic) conforme aux contraintes de vitesse de la machine pour le suivi de rotation.

---

## 2. Pourquoi la Fourche Optique H21A1 a été Abandonnée

Bien que théoriquement séduisante, la fourche H21A1 accumule des contraintes rédhibitoires pour le projet :
1. **Complexité électronique excessive :** En raison de l'impédance de sortie et des tirages internes de l'ATmega2560, le capteur nécessitait une carte de conditionnement analogique intermédiaire (comparateur LM393, pont diviseur de référence, potentiomètre de réglage, résistances de pull-up), multipliant les sources potentielles de panne.
2. **Sensibilité environnementale critique :** Une fourche optique en environnement textile est très vulnérable à l'accumulation de peluches, poussières de fil et projections d'huile de graissage machine, risquant d'obstruer le faisceau IR de façon intempestive.
3. **Tolérance mécanique contraignante :** L'alignement du drapeau mécanique dans la fente étroite de quelques millimètres impose des tolérances d'usinage et de fixation très serrées sur le châssis de la machine, difficiles à maintenir sous les vibrations continues du moteur 230V.

---

## 3. Nouvelle Architecture Validée : Fin de Course + Encodeur SEN0230

```
                      +------------------------------------------+
                      |         Machine Janome Facility 21       |
                      +------------------------------------------+
                                     |                    |
                 (Arbre Principal)   |                    | (Courroie motrice)
                                     v                    v
                  +--------------------+        +--------------------+
                  | Fin de Course PMH  |        | Encodeur SEN0230   |
                  | Contact Sec / 5V   |        | 400 impulsions/tr  |
                  +--------------------+        +--------------------+
                             |                            |
                 Signal Tout-ou-Rien            Trains d'impulsions A/B
                 Homing & Sécurité PMH          Vitesse & Position angulaire
                             |                            |
                             +------------+   +-----------+
                                          |   |
                                          v   v
                               +---------------------+
                               | MKS Base V1.4       |
                               | (ATmega2560 / 16MHz)|
                               +---------------------+
```

### 3.1. Capteur Fin de Course Standard (Position Haute & Homing Aiguille)
* **Principe :** Un microrupteur à levier ou galet (type fin de course d'imprimante 3D / CNC) activé mécaniquement par une came solidaire de l'arbre principal lorsque l'aiguille atteint sa position dégagée du tissu.
* **Avantages immédiats :**
  * **Robustesse absolue :** Signal binaire tout-ou-rien franc ($0\text{ V} / 5\text{ V}$), totalement insensible aux poussières et à la lumière ambiante.
  * **Câblage direct :** Raccordement direct sur un port fin de course de la carte MKS Base (ex. Pin `PD2` ou entrée Endstop dédiée) avec utilisation du pull-up interne ou externe, sans aucune carte AOP intermédiaire.
  * **Configuration du Homing :** Permet une séquence d'initialisation propre au démarrage (la machine tourne au ralenti jusqu'au déclenchement du switch, garantissant que l'aiguille démarre toujours en position haute avant le premier déplacement du cadre).

### 3.2. Encodeur Rotatif SEN0230 (Suivi de Vitesse & Synchronisation)
* **Spécifications :** Résolution de $400\text{ impulsions/tour}$, vitesse maximale admissible de $5000\text{ tr/min}$, arbre de $\varnothing 6\text{ mm}$, livré avec équerre de fixation rigide.
* **Compatibilité avec les vitesses machine :**
  * Vitesse maximale machine : $\le 860\text{ tr/min}$ (sur la grosse poulie 83 dents).
  * Avec une poulie d'entraînement de l'encodeur de $16$ à $18\text{ dents}$ imprimée en 3D en prise sur la courroie motrice :
    $$\text{Vitesse encodeur} = \frac{860 \times 83}{16} \approx 4460\text{ tr/min} \le 5000\text{ tr/min}$$
  * Les contraintes de vitesse constructeur sont donc **rigoureusement respectées**.

---

## 4. Synthèse Comparative des Approches

| Paramètre | Fourche Optique H21A1 (Abandonnée) | Fin de Course + Encodeur SEN0230 (Retenu) |
| :--- | :--- | :--- |
| **Complexité électronique** | Élevée (AOP LM393 + PCB requis) | **Minimale (contact direct + entrées logiques)** |
| **Sensibilité poussière / huile** | Élevée (faisceau IR obturable) | **Nulle (contact mécanique + encodeur industriel)** |
| **Procédure de Homing aiguille** | Difficile / imprécise | **Directe et standardisée** |
| **Mesure de vitesse continue** | Non (1 impulsion/tour seulement) | **Oui (400 imp/tour, asservissement fin)** |
| **Mise en œuvre mécanique** | Tolérance millimétrique critique | **Came sur arbre + poulie crantée standard** |

---

## 5. Plan d'Action & Déploiement

1. **Mécanique :**
   - Modéliser et imprimer en 3D la poulie crantée (16 ou 18 dents, alésage $6\text{ mm}$ avec méplat et vis pointeau) et son support pour l'encodeur SEN0230.
   - Concevoir la came mécanique sur l'arbre supérieur pour actionner le fin de course de l'aiguille.
   - Revoir le design du plateau de travail $X/Y$ et intégrer les supports pour les fins de course des axes $X$ et $Y$.
2. **Électronique & Puissance :**
   - Raccorder le fin de course aiguille sur un port Endstop de la MKS Base V1.4.
   - Câbler l'encodeur SEN0230 (alimenté en 5V) sur les entrées logiques du microcontrôleur.
   - Câbler le **Module Variateur AC RobotDyn** (TRIAC) pour réguler la vitesse du moteur secteur 230V.
   - Passer la commande des matériels manquants selon la liste des besoins établie.
3. **Firmware & Logiciel :**
   - Développer la routine de Homing aiguille basée sur le contact de fin de course.
   - Valider la lecture de l'encodeur SEN0230 et l'asservissement en vitesse via le variateur AC.

---
**Voir aussi :**
* `[[Capteur_Fin_de_Course_Aiguille|Fiche Technique : Fin de Course Point Mort Haut]]`
* `[[Encodeur_Rotatif_SEN0230|Fiche Technique : Encodeur Rotatif SEN0230]]`
* `[[Module_Variateur_AC|Fiche Module Variateur AC RobotDyn]]`
* `[[Plateau_XY_et_Mecanique|Mécanique & Redesign du Plateau XY]]`
* `[[00_Tableau_de_Bord|Tableau de Bord Général]]`
