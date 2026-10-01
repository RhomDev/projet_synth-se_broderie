---
titre: Configuration du Fast PWM (25 kHz) sur Arduino Mega
date: 2026-09-30
projet: Module Broderie
tags:
  - electronique
  - arduino
  - pwm
  - timers
  - microcontroleur
statut: termine
aliases:
  - Configuration du PWM sur Arduino
  - Fast PWM 25kHz
---

# Configuration du PWM (25 kHz) sur Arduino ATmega2560

## 1. Principe des Timers & Registre TOP
Le registre **ICR1** du Timer 1 définit le plafond (la valeur « TOP ») que le compteur interne doit atteindre avant de repartir à zéro. Le temps mis pour accomplir ce cycle détermine la fréquence finale du signal PWM généré.

```
       Valeur Compteur
   TOP ^      /|      /|      /|
 (639) |     / |     / |     / |
       |    /  |    /  |    /  |
     0 +---+---+---+---+---+---+---> Temps
       |<-- Période PWM (40 µs) -->|
```

---

## 2. Formule de Calcul en Mode Fast PWM

Pour déterminer la valeur à injecter dans le registre en mode *Fast PWM*, on applique la formule générale du constructeur Atmel :

$$TOP = \frac{f_{\text{CPU}}}{N \times f_{\text{PWM}}} - 1$$

### Détail des paramètres :
* **$f_{\text{CPU}} = 16\,000\,000\text{ Hz}$ :** Vitesse de l'horloge principale de l'ATmega2560 ($16\text{ MHz}$).
* **$N = 1$ :** Facteur du prédiviseur (*prescaler*). L'horloge du timer tourne à la fréquence native du quartz sans ralentissement.
* **$f_{\text{PWM}} = 25\,000\text{ Hz}$ :** Fréquence cible recherchée ($25\text{ kHz}$, au-delà du spectre audible humain pour éliminer les sifflements acoustiques).
* **$- 1$ :** Correction nécessaire car le comptage électronique commence à $0$.

---

## 3. Application Numérique

$$TOP = \frac{16\,000\,000}{1 \times 25\,000} - 1 = 640 - 1 = 639$$

L'instruction en C / registres :
```cpp
ICR1 = 639; // Fixe la période à exactement 40 µs (fréquence 25 kHz)
```

Le microcontrôleur boucle donc de 0 à 639 à chaque période, générant précisément 25 000 impulsions par seconde.

---

## 4. Nuance Critique : PWM Continu vs Découpe de Phase AC
Bien que cette méthode soit idéale pour commander des hacheurs continus (moteurs DC, ventilateurs, ponts en H), elle **ne peut pas** être appliquée telle quelle à un TRIAC sur le secteur $230\text{ V AC}$. 

Pour le pilotage du moteur alternatif de la machine à coudre, le système utilise la découpe de phase synchronisée sur le passage à zéro du réseau ($50\text{ Hz}$).

---
**Voir aussi :**
* `[[Module_Variateur_AC|Étude complète du Variateur AC RobotDyn]]`
* `[[Carte_MKS_Base_V1_4|Architecture Carte MKS Base]]`
* `[[ATMEGA640.PDF|Datasheet Atmel ATmega]]`