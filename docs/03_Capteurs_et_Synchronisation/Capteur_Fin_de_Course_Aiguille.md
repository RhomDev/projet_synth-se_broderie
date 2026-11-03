---
titre: Capteur Fin de Course Aiguille (Point Mort Haut & Homing)
date: 2026-11-02
projet: Module Broderie
tags:
  - capteur
  - fin_de_course
  - homing
  - mks_base
  - mecanique
  - securite
statut: actif
aliases:
  - Capteur Fin de Course Aiguille
  - Endstop Aiguille
  - Homing Aiguille
---

# 🛑 Capteur Fin de Course Aiguille — Détection Point Mort Haut & Homing

## 1. Rôle et Fonction dans le Système

Dans la brodeuse numérique, le déplacement du cadre de broderie ($X/Y$) ne peut avoir lieu que lorsque l'aiguille est complètement sortie du textile.

Pour remplacer la fourche optique H21A1 (abandonnée pour complexité et contraintes d'alignement), un **capteur de fin de course mécanique standard à levier avec galet** (type Endstop mécanique pour imprimante 3D / CNC, standard RAMPS/Makerbot) est installé sur la machine.

Ses deux rôles fondamentaux sont :
1. **Détection du Point Mort Haut (PMH) :** Détecter de manière binaire et infaillible l'instant où l'aiguille atteint sa hauteur maximale (hors tissu).
2. **Initialisation et Homing Machine :** Permettre au firmware d'effectuer une prise d'origine mécanique de l'arbre de couture dès la mise sous tension.

---

## 2. Intégration Mécanique & Atouts du Modèle à Galet

* **Modèle retenu :** Microrupteur mécanique à levier équipé d'un **galet de roulement** (roulette).
* **Actionneur :** Une came profilée ou un ergot à pente douce solidaire de l'arbre supérieur de la machine.
* **Avantages majeurs du galet par rapport à un levier plat :**
  * **Suppression du frottement sec :** Le galet roule sur le profil de la came lors de la rotation de l'arbre (jusqu'à $860\text{ tr/min}$), évitant l'usure prématurée du plastique et le risque d'accrochage mécanique.
  * **Actionnement progressif et silencieux :** Transition mécanique fluide garantissant un déclenchement reproductible sans à-coups.
  * **Insensibilité environnementale :** Totalement insensible aux poussières textiles, peluches et micro-projections d'huile de graissage machine.

---

## 3. Schéma Électrique & Connexion MKS Base V1.4

Le fin de course se raccorde directement sur un connecteur Endstop de la carte `[[Carte_MKS_Base_V1_4|MKS Base V1.4]]` (ex: connecteur Z-Min ou broche d'interruption dédiée) :

```
                  +5V (Interne MKS Base)
                     |
                 [R_pullup 10k]
                     |
   Microcontrôleur --+
   Broche Entrée     |
                     o  Contact Normalement Ouvert (NO)
                      \
                       o  Masse (GND)
```

* **Configuration :** Câblage de type `Normalement Ouvert` (NO) ou `Normalement Fermé` (NC pour sécurité positive) tiré au $+5\text{ V}$ par la résistance de pull-up interne ou externe de la carte.
* **Niveaux logiques :**
  * Contact relâché : $5\text{ V}$ (Niveau logique `HIGH`)
  * Came active (PMH) : $0\text{ V}$ (Niveau logique `LOW`)
* Aucun circuit amplificateur ni comparateur AOP n'est nécessaire !

---

## 4. Algorithme de Homing de l'Aiguille

Au démarrage de la brodeuse (commande G-code `G28` ou séquence d'initialisation) :
1. Le firmware active le moteur principal à vitesse très réduite via le `[[Module_Variateur_AC|variateur AC RobotDyn]]`.
2. Le microcontrôleur lit l'état du fin de course aiguille.
3. Dès détection du front de fermeture du contact (passage à l'état bas), le moteur est coupé immédiatement.
4. L'aiguille est alors calée avec certitude en position haute, prête pour les déplacements de positionnement du cadre.
5. Les coordonnées relatives de l'encodeur `[[Encodeur_Rotatif_SEN0230|SEN0230]]` sont réinitialisées à $0^\circ$ (zéro machine).

---
**Voir aussi :**
* `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision : Choix Fin de Course]]`
* `[[Encodeur_Rotatif_SEN0230|Encodeur Rotatif SEN0230]]`
* `[[Carte_MKS_Base_V1_4|Brochage Carte MKS Base V1.4]]`
* `[[Plateau_XY_et_Mecanique|Mécanique du Plateau XY]]`
