---
titre: Analyse et Intégration du Capteur Optique H21A1
date: 2026-09-29
projet: Module Broderie
tags:
  - electronique
  - capteur
  - mks_base
  - datasheet
  - arduino
  - cnc
statut: abandonne
aliases:
  - rapport_capteur_h21a1
  - Fourche Optique H21A1
  - H21A1
---

# Capteur de Position Aiguille : Fourche Optique H21A1

> [!WARNING] Solution Abandonnée (02/11/2026)
> Cette solution a été **officiellement abandonnée** en raison d'une complexité de conditionnement excessive (tension flottante) et d'exigences d'alignement mécanique trop contraignantes en atelier textile.
> Le projet adopte désormais un **[[Capteur_Fin_de_Course_Aiguille|fin de course mécanique standard]]** pour la détection du point mort haut et le homing, couplé à un **[[Encodeur_Rotatif_SEN0230|encodeur rotatif SEN0230]]**.
> Consulter la note d'arbitrage complète : `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision]]`.

## 1. Rôle dans le Projet Broderie
Dans le cadre de la transformation de la machine à coudre en brodeuse CNC, il est impératif de synchroniser les mouvements du plateau $X/Y$ avec la position de l'aiguille. Le but est d'interdire tout déplacement du tissu pendant que l'aiguille le traverse.

Le capteur **H21A1** (photo-interrupteur à fente infrarouge / fourche optique) a été sélectionné pour détecter le passage de l'aiguille en position haute sur l'arbre principal.

```
       Émetteur LED IR                       Récepteur Phototransistor
       +---------------+                   +-------------------------+
       |   Anode (+)   |                   |  Collecteur (5V via RL) |
       |       |       |  Faisceau IR      |            |            |
       |     [LED] ====|==================>|=====> [Phototransistor] |
       |       |       |   (Coupé par le   |            |            |
       |  Cathode (-)  |     drapeau)      |     Émetteur (GND)      |
       +---------------+                   +-------------------------+
```

---

## 2. Analyse de la Datasheet (Vitesse de Commutation vs Résistance $R_L$)
La lecture de la documentation constructeur met en évidence la sensibilité de la vitesse de commutation en fonction de la résistance de charge ($R_L$).

* **Comportement :** Plus la résistance $R_L$ placée entre l'alimentation ($V_{CC}$) et le collecteur du phototransistor est élevée, plus les temps de montée et de descente ($t_{\text{on}}$ et $t_{\text{off}}$) s'allongent.
* **Enjeu pour la broderie :** L'arbre principal pouvant tourner jusqu'à $\sim 1000\text{ tours/minute}$ ($16{,}6\text{ tours/seconde}$, soit un tour complet en $60\text{ ms}$), le capteur doit commuter en une fraction de milliseconde pour que la fenêtre de tir de déplacement du cadre soit exploitable.
* **Choix optimal :** Privilégier une résistance $R_L$ faible (entre $1\text{ k}\Omega$ et $2{,}5\text{ k}\Omega$) pour obtenir un front raide et limiter le temps de retard.

![Courbe de commutation H21A1](Screenshot%20From%202026-09-29%2014-12-44.png)

---

## 3. Comportement sous Charge & Nécessité du Conditionnement
Bien que le capteur réagisse rapidement, son impédance de sortie élevée pose un problème direct lorsqu'il est raccordé aux entrées numériques du microcontrôleur ATmega2560 :
* La tension basse remonte à $2{,}0\text{ V} - 2{,}5\text{ V}$ au lieu de descendre sous $0{,}8\text{ V}$.
<<<<<<< HEAD
* Ce signal flottant stagne dans la zone d'indécision logique du microcontrôleur ATmega2560 ($1{,}5\text{ V} < V < 3{,}0\text{ V}$).
* L'idée initiale d'utiliser un encodeur rotatif pour contourner ce problème a été rejetée pour éviter de surcharger le processeur avec 6000 interruptions/s (voir la `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision]]`).
* La solution retenue consiste à insérer un comparateur de tension dédié **LM393** (alimenté en 5V simple, sortie collecteur ouvert avec pull-up), délivrant un signal numérique franc 0V/5V pour déclencher de manière infaillible l'interruption sur front descendant (`FALLING`).

---
**Voir aussi :**
* `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision : Maintien du H21A1 vs Encodeur]]`
* `[[Conditionnement_AOP_H21A1|Carte Comparateur LM393 & PCB]]`
* `[[comparateur-aop-choix|Choix des composants AOP/Comparateur]]`
* `[[Carte_MKS_Base_V1_4|Raccordement Carte MKS Base]]`
* `[[capteur_position_H21A1.pdf|Datasheet officielle H21A1]]`
=======
* Cela nécessite l'insertion de l'étage de mise en forme par AOP décrit dans [[Conditionnement_AOP_H21A1|Conditionnement du signal H21A1]]`.

---
**Voir aussi :**
* [[Conditionnement_AOP_H21A1|Carte Comparateur AOP LM741 & PCB]]`
* [[Carte_MKS_Base_V1_4|Raccordement Carte MKS Base]]`
* [[capteur_position_H21A1.pdf|Datasheet officielle H21A1]]`
>>>>>>> ce25f4e (Fix: résolution conflit workspace.json)
* Code de test : `src/arduino/test_H21A1/test_H21A1.ino`
