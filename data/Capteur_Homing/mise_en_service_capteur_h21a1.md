---
titre: Mise en Service_capteur
date: 2026-09-30
Projet: Capteur homing
tags:
  - electronique
  - capteur
  - mks_base
  - datasheet
  - arduino
  - cnc
statut: en cours
---
# Module de correction du signal (Comparateur de tension)

## 1. Contexte et Problématique
La partie réceptrice du capteur optique à fente (H21A1) se comporte comme une résistance variable. Selon la présence ou l'absence d'obstacle dans la fente, sa résistance passe de moins de 1 Mohm à une valeur comprise entre 3 et 6 Mohm. Par rapport à la tension de sortie, cela donne l'impression d'un court-circuit lorsque le capteur atteint son taux résistif le plus élevé.

* **À vide (mesure au multimètre) :** La tension varie parfaitement entre 5V et environ 0.8V. Cette plage est théoriquement idéale pour le microcontrôleur de la carte MKS Base V1.4([[MKS_BASE_PINS.pdf]]), car toute tension inférieure à 1.5V est considérée comme un état bas (LOW) stable. Cela permet d'y insérer une instruction pour détecter les fronts descendants (FALLING).
* **En charge (connecté à la carte) :** Lorsque la sortie du capteur est reliée à l'entrée digitale du microcontrôleur, la tension basse remonte à cause des résistances internes de tirage de la carte. La tension stagne alors autour de 2V - 2.5V, ce qui représente une zone d'incertitude instable pour l'entrée digitale du processeur ATmega2560([[ATMEGA640.PDF]]).

## 2. Principe de la solution : L'Amplificateur Opérationnel (AOP)
Pour isoler le capteur de l'influence de la carte et garantir une détection fiable, la solution consiste à créer un module de correction intermédiaire. Son rôle est de convertir la tension analogique instable du capteur en un signal digital parfaitement propre (0V ou 5V purs).

Ce conditionnement est réalisé en utilisant un Amplificateur Opérationnel (AOP) monté en **comparateur de tension**. Il va comparer la tension fluctuante issue du capteur avec une tension de référence fixe, que l'on pourra ajuster manuellement.

## 3. Analyse du schéma de câblage 
Le circuit s'articule autour de trois blocs fonctionnels reliés à la puce AOP (modélisée par un composant type LM741) :

* **Le signal du capteur (Entrée Non-Inverseuse V+) :** Le phototransistor (représentant le récepteur H21A1) forme un pont diviseur avec sa résistance de tirage reliée au 5V. La tension mesurée à ce point de jonction est injectée directement sur la broche V+ de l'AOP.
* **Le seuil de référence (Entrée Inverseuse V-) :** Une résistance variable (potentiomètre) couplée à une résistance fixe vers la masse (GND) crée un diviseur de tension réglable. Il permet de définir une tension de référence constante injectée sur la broche V- de l'AOP.
* **L'étage de sortie (Sortie D) :** L'AOP compare en temps réel les deux entrées.
  * Si la tension du capteur est supérieure à la tension de référence, la sortie bascule au maximum (5V).
  * Si la tension du capteur passe sous la tension de référence (même si elle ne chute qu'à 2.5V), la sortie sature vers le minimum (0V).

![[montage_correction.png]]

## 4. Mise en service et Calibration sur la machine
L'atout de ce module est sa flexibilité lors de la mise en route du système de broderie:
1. Une fois le montage en place, on relève la tension haute et la tension basse réelles délivrées par le capteur.
2. On ajuste la résistance variable pour fixer la tension de référence exactement à mi-chemin de ces deux valeurs.
3. Dès que le signal franchit ce seuil, l'AOP génère un front descendant net et immédiat vers 0V. Le microcontrôleur peut alors traiter l'interruption matérielle sans aucune erreur d'interprétation logique, assurant une synchronisation parfaite de l'aiguille.