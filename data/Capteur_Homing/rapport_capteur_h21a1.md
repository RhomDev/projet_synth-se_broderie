---
titre: Analyse et Intégration du Capteur Optique H21A1
date: 2026-09-29
projet: Capteur homing
tags:
  - electronique
  - capteur
  - mks_base
  - datasheet
  - arduino
  - cnc
statut: en cours
---

# Capteur de Position : Fourche Optique H21A1

## 1. Rôle dans le projet
Dans le cadre de la transformation de la machine à coudre en broderie CNC, il est impératif de synchroniser les mouvements du plateau X/Y avec la position de l'aiguille. Le but est d'éviter que le tissu ne se déplace pendant que l'aiguille le traverse. 
Le capteur **H21A1** (photo-interrupteur à fente ou fourche optique) a été sélectionné pour détecter la position haute de l'arbre principal.

## 2. Analyse de la Datasheet (Vitesse de commutation vs Résistance)
La lecture de la datasheet du H21A1 met en évidence le comportement de la vitesse de commutation du capteur en fonction de la résistance de charge ($R_L$).

*   **Comportement :** Plus la résistance $R_L$ placée entre l'alimentation ($V_{CC}$) et le capteur est élevée, plus les temps de réaction ($t_{on}$ et $t_{off}$) sont longs. 
*   **Enjeu pour la broderie :** L'arbre principal pouvant atteindre ~1000 tours/minute, le capteur doit réagir instantanément au passage du marqueur mécanique (drapeau ou disque à fente). 
*   **Conclusion :** Il faut privilégier une résistance $R_L$ relativement faible (entre $1 k\Omega$ et $2.5 k\Omega$) pour garantir un signal franc et extrêmement rapide.
*   *Note de test :* Les valeurs PW (300 µs) et PRR (100 pps) indiquées sur le graphique du constructeur sont uniquement les conditions de test en laboratoire (Pulse Width / Pulse Repetition Rate) et n'impactent pas notre montage final en tension continue.

![[Screenshot From 2026-09-29 14-12-44.png]]

## 3. Compatibilité avec la Carte MKS Base V1.4
Le H21A1 est parfaitement adapté à l'écosystème de la carte de commande MKS Base :
*   **Tension logique :** Fonctionne de manière optimale sous $V_{CC} = 5V$, ce qui correspond à la tension logique de la puce Arduino (ATmega2560) de la MKS.
*   **Connectique :** Agit comme un interrupteur binaire (HIGH/LOW). Il se branche directement sur les broches "Endstop" (Fin de course) de la carte.
*   **Traitement :** Le signal sera lu via les interruptions matérielles (Hardware Interrupts) de l'Arduino pour ne rater aucun cycle de l'aiguille à haute vitesse, sans ralentir le calcul des trajectoires des moteurs pas à pas.
