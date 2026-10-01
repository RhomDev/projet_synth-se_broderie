---
titre: Module Variateur AC (RobotDyn 1 Canal) — Contrôle de Vitesse Moteur
date: 2026-09-30
projet: Module Broderie
tags:
  - electronique
  - variateur_ac
  - triac
  - zero_crossing
  - moteur
  - mks_base
  - arduino
  - cnc
statut: termine
aliases:
  - Module variateur AC
  - Variateur AC
  - RobotDyn AC Dimmer
---

# Module Variateur AC (RobotDyn 1 Canal) : Étude et Intégration

## 1. Contexte et Problématique dans le Projet Broderie

Dans le projet de transformation de la machine à coudre mécanique en **brodeuse numérique CNC**, le mouvement de l'aiguille est entraîné par le moteur principal d'origine de la machine (moteur universel alimenté sur le secteur alternatif $230\text{ V AC}$).

Dans la configuration manuelle initiale, ce moteur est commandé par une pédale mécanique servant de rhéostat ou de gradateur à pied. Pour automatiser la broderie, la carte de commande principale (**MKS Base V1.4**, animée par un microcontrôleur **ATmega2560**) doit prendre le contrôle total de cette motorisation.

### Pourquoi un simple relais ON/OFF est insuffisant ?
Initialement, l'utilisation d'un relais électromécanique classique avait été envisagée (`[[Suivi_des_Taches|Tache sur machine]]`). Cependant, cette solution présente des limites rédhibitoires :
* **Vitesse incontrôlée :** Le relais n'offre qu'un fonctionnement en « tout ou rien » (0% ou 100%). À pleine vitesse (~1000 tours/minute), les accélérations sont trop brutales, entraînant un risque élevé de casse de fil, de saut de points ou de déchirement du textile.
* **Absence de rampe et de mode d'approche :** Il est impossible de faire tourner la machine au ralenti lors de phases délicates (prise d'origine / *homing*, calibration, points de couture complexes).
* **Usure mécanique et arcs électriques :** Les commutations répétées sous forte charge inductive détériorent rapidement les contacts du relais.

### La solution : Le variateur AC à découpe de phase
Pour obtenir une régulation fine et continue de la vitesse de couture, nous intégrons le **Module Variateur AC RobotDyn 1 Canal** (logique $3.3\text{ V} / 5\text{ V}$, $110\text{ V} / 230\text{ V AC}$, $50/60\text{ Hz}$).

---

## 2. Principe Fondamental : Découpe de Phase vs PWM Classique

Une incompréhension fréquente consiste à vouloir piloter une charge alternative en lui appliquant directement un signal PWM continu haute fréquence (tel que le PWM $25\text{ kHz}$ étudié dans `[[Configuration_PWM_Arduino|Configuration du PWM sur Arduino]]`). Cela est physiquement impossible avec un composant à déclenchement de type **TRIAC**.

```
                   Tension AC sinusoïdale (50 Hz, demi-période = 10 ms)
       +V_max ^        _--_                _--_
              |      /      \            /      \
              |     /  ON    \          /  ON    \
          0 V +----+----------+--------+----------+------> Temps (t)
              |     |<-délai->|        |<-délai->|
              |                \  ON  /            \  ON  /
       -V_max v                 ^----^              ^----^
              ^                ^
              Passage à zéro   Passage à zéro
              (Pulse ZC)       (Pulse ZC)
```

### Le comportement intrinsèque du TRIAC
Le composant de puissance au cœur du variateur est un **TRIAC** (*Triode for Alternating Current*), un semi-conducteur bidirectionnel équivalent à deux thyristors montés en tête-bêche :
1. **Amorçage :** Le TRIAC s'amorce lorsqu'une impulsion brève de courant est envoyée sur sa gâchette (*Gate* via la broche `PSM`).
2. **Auto-maintien (Latching) :** Une fois amorcé, le TRIAC **reste conducteur**, même si le signal sur la gâchette est coupé.
3. **Désamorçage naturel :** Le TRIAC ne peut se bloquer que lorsque le courant alternatif qui le traverse retombe sous un seuil minimal appelé **courant de maintien** ($I_H$ - *Holding Current*). Dans une onde sinusoïdale alternative à $50\text{ Hz}$, cette extinction a lieu naturellement à chaque **passage par zéro** de la tension (toutes les $10\text{ ms}$).

### La méthode du contrôle par angle de phase (Phase Cutting)
Pour faire varier la tension efficace $V_{RMS}$ (et donc la puissance injectée dans le moteur), on synchronise l'allumage du TRIAC avec la sinusoïde du secteur :
1. Le secteur alternatif à $50\text{ Hz}$ présente une période de $T = 20\text{ ms}$, soit **deux passages par zéro par période** (un toutes les demi-ondes de $t_{\text{demi}} = 10\text{ ms} = 10\,000\ \mu\text{s}$).
2. À chaque passage par zéro, le module génère un signal d'interruption sur sa broche **ZC** (*Zero-Crossing*).
3. Le microcontrôleur reçoit ce signal et déclenche un compte à rebours logiciel (délai $t_{\text{delay}}$ compris entre $0$ et $10\,000\ \mu\text{s}$).
4. Une fois ce délai écoulé, le microcontrôleur envoie une brève impulsion d'allumage ($10\ \mu\text{s}$) sur la broche **PSM** (*Pulse Skip Modulation / Gate*).
5. Le TRIAC conduit pour le reste de la demi-onde, puis s'éteint automatiquement au passage à zéro suivant.

### Formule de relation entre délai et puissance
Pour une fréquence secteur $f = 50\text{ Hz}$ ($t_{\text{demi}} = 10\,000\ \mu\text{s}$) :
$$\alpha = \frac{t_{\text{delay}}}{t_{\text{demi}}} \times 180^\circ$$

| Puissance souhaitée | Délai $t_{\text{delay}}$ | Angle de phase $\alpha$ | Comportement de la sinusoïde |
| :--- | :--- | :--- | :--- |
| **$100\%$ (Plein régime)** | $\approx 0\ \mu\text{s}$ | $0^\circ$ | Sinusoïde complète transmise |
| **$75\%$** | $\approx 2\,500\ \mu\text{s}$ | $45^\circ$ | Les 3/4 de la demi-onde sont transmis |
| **$50\%$ (Mi-puissance)** | $\approx 5\,000\ \mu\text{s}$ | $90^\circ$ | La moitié de la demi-onde est transmise |
| **$25\%$** | $\approx 7\,500\ \mu\text{s}$ | $135^\circ$ | Seule la fin de la demi-onde est transmise |
| **$0\%$ (Arrêt)** | Pas d'impulsion ($> 9\,800\ \mu\text{s}$) | $180^\circ$ | Le TRIAC reste bloqué |

---

## 3. Architecture Électrique et Isolation Galvanique

La présence du secteur $230\text{ V AC}$ impose des règles de sécurité drastiques. Le module RobotDyn garantit une **isolation galvanique totale** entre le côté secteur haute tension et le côté microcontrôleur basse tension grâce à deux optocoupleurs distincts.

```
       CÔTÉ COMMANDE (5V / MKS Base)            CÔTÉ PUISSANCE (230V AC)
      +-----------------------------+          +------------------------+
      |                             |          |                        |
      |   [Pin Interruption ZC] <---|--[Opto]--|-- Pont redresseur      |
      |                             |   ZC     |    + Détection 0V      |
      |                             |          |           ^            |
      |                             |          |           |            |
      |                             |          |   Secteur 230V AC      |
      |                             |          |           |            |
      |                             |          |           v            |
      |   [Sortie Numérique PSM]--->|--[Opto]--|-- Gâchette TRIAC       |
      |                             |  TRIAC   |        |               |
      |                             | (MOC3021)|     [MOTEUR]           |
      |                             |          |     + Snubber RC       |
      +-----------------------------+          +------------------------+
                     <==== Isolation Optique (3750V RMS) ====>
```

### 1. Étage Détection de Passage à Zéro (`ZC`)
* La tension alternative $230\text{ V}$ passe à travers des résistances de forte valeur puis un pont redresseur double alternance alimentant la diode d'un optocoupleur (ex: EL817 ou 4N35).
* Lorsque la tension sinusoïdale s'approche de $0\text{ V}$, le courant devient insuffisant pour allumer la diode de l'optocoupleur. Le phototransistor interne se bloque, faisant remonter la ligne `ZC` à l'état haut ($5\text{ V}$) via une résistance de tirage (*pull-up*).
* Cela génère un front logique franc à chaque passage par zéro, soit **100 impulsions par seconde** à $50\text{ Hz}$.

### 2. Étage Commande de Puissance (`PSM`)
* La broche `PSM` attaque la diode d'un **opto-TRIAC à amorçage aléatoire** (*random-phase optocoupler*, type MOC3021 / MOC3052).
* **Point technique crucial :** Il est impératif d'utiliser un opto-TRIAC *sans* détection de zéro intégrée (ne surtout pas utiliser un MOC3041). En effet, un composant *Zero-Cross* refuserait de s'amorcer au milieu d'une demi-onde, rendant la découpe de phase impossible.
* Le phototriac de l'opto-coupleur pilote directement la gâchette du TRIAC de puissance principal (souvent un BTA16-600B ou BTA24-600B, supportant jusqu'à $600\text{ V}$ et $16\text{ A}$ / $24\text{ A}$).

---

## 4. Particularités de la Charge Inductive (Moteur de Machine à Coudre)

Un moteur électrique n'est pas une simple résistance chauffante : c'est une **charge inductive** ($R + L$). Cela implique deux phénomènes physiques majeurs à maîtriser :

### 1. Déphasage tension-courant
Le courant traversant la bobine est déphasé en retard par rapport à la tension ($I$ en retard sur $U$, facteur de puissance $\cos \phi < 1$). Par conséquent, lorsque la tension passe par zéro, le courant n'est pas encore nul. Le TRIAC ne se bloque que lorsque le **courant** passe par zéro, ce qui déplace légèrement le point d'extinction effectif.

### 2. Surtensions de commutation et protection par Snubber
Lors du blocage du TRIAC, la coupure du courant inductif génère une surtension brutale :
$$e_L = -L \frac{di}{dt}$$
Une montée en tension trop rapide ($\frac{dv}{dt}$) aux bornes du TRIAC peut provoquer un auto-amorçage parasite (*dv/dt triggering*) ou la destruction du semi-conducteur.
* **Le circuit Snubber (RC) :** Le module RobotDyn comprend un réseau amortisseur constitué d'une résistance ($39\ \Omega$ à $100\ \Omega$) en série avec un condensateur haute tension ($10\text{ nF}$ à $100\text{ nF}$ classe X2 / $400\text{ V}$), monté en parallèle sur le TRIAC. Ce réseau absorbe l'énergie résiduelle de la bobine et limite la pente $\frac{dv}{dt}$.
* **Varistance (MOV) :** En environnement bruité, l'adjonction d'une varistance $275\text{ V}$ aux bornes du moteur protège le circuit contre les pics de tension transitoires.

### 3. Durée de l'impulsion de gâchette
Pour une charge inductive, le courant met un certain temps à s'établir en raison de l'inductance ($L/R$). L'impulsion sur la broche `PSM` doit être maintenue suffisamment longtemps (typiquement entre $10\ \mu\text{s}$ et $50\ \mu\text{s}$) pour que le courant atteigne le seuil d'accrochage (*Latching Current* $I_L$) du TRIAC.

---

## 5. Brochage et Raccordement à la MKS Base V1.4

### Côté Basse Tension (Logique 5V)

| Broche Module | Signal | Raccordement sur MKS Base V1.4 (ATmega2560) | Description |
| :--- | :--- | :--- | :--- |
| **VCC** | Alimentation logique | Broche $5\text{ V}$ (connecteur Aux ou Endstop) | Alimente les optocoupleurs côté logique |
| **GND** | Masse | Broche $\text{GND}$ de la carte MKS | Référence commune logique |
| **ZC** | *Zero Crossing* (Sortie) | Broche d'interruption externe (ex: `D2` / `INT4` ou `D19` / `INT2`) | Envoie les tops de synchronisation $100\text{ Hz}$ |
| **PSM** | *Gate Trigger* (Entrée) | N'importe quelle sortie numérique (ex: `D3` ou `D11`) | Reçoit l'impulsion d'allumage du TRIAC |

### Côté Haute Tension (Secteur 230V)

| Bornier Module | Connexion | Description |
| :--- | :--- | :--- |
| **AC-IN (L)** | Phase secteur ($230\text{ V}$) | Alimentation électrique principale |
| **AC-IN (N)** | Neutre secteur | Retour d'alimentation secteur |
| **LOAD (L)** | Borne Phase du moteur | Sortie régulée en tension hachée |
| **LOAD (N)** | Borne Neutre du moteur | Raccordé en commun au neutre |

> [!WARNING]
> Le châssis métallique de la machine à coudre doit obligatoirement être relié à la **Terre de protection (PE)** de l'installation électrique. Les masses logiques ($5\text{ V}$) de la MKS Base ne doivent en aucun cas être en contact avec la phase ou le neutre du secteur.

---

## 6. Implémentation Logicielle sur Arduino (ATmega2560)

Deux approches logicielles sont envisageables :

### Méthode A : Utilisation de la bibliothèque `RBDdimmer`
La bibliothèque officielle de RobotDyn encapsule les timers matériels et la gestion de l'interruption ZC :

```cpp
#include <RBDdimmer.h>

// Définition des broches sur la MKS Base V1.4
#define ZC_PIN     2    // Broche supportant une interruption matérielle (INT4 sur Mega2560)
#define DIMMER_PIN 3    // Broche numérique standard pour la gâchette

// Déclaration de l'objet gradateur (mode normal pour découpe de phase)
dimmerLamp moteurBroderie(DIMMER_PIN);

void setup() {
  Serial.begin(115200);
  
  // Initialisation du module (NORMAL_MODE = découpe de phase, ON = actif)
  moteurBroderie.begin(NORMAL_MODE, ON);
  
  // Vitesse initiale à l'arrêt
  moteurBroderie.setPower(0);
  Serial.println("Variateur AC initialisé - Moteur à l'arrêt.");
}

void loop() {
  // Exemple : Rampe d'accélération progressive (démarrage doux)
  for (int vitesse = 10; vitesse <= 60; vitesse += 5) {
    moteurBroderie.setPower(vitesse); // Réglage en pourcentage (0 à 100%)
    Serial.print("Vitesse moteur réglée à : ");
    Serial.print(vitesse);
    Serial.println("%");
    delay(500);
  }
  
  delay(3000);
  
  // Arrêt sécurisé
  moteurBroderie.setPower(0);
  delay(2000);
}
```

### Méthode B : Implémentation bas niveau sans bibliothèque (Interruption + Timer)
Pour s'intégrer directement dans le cœur temps réel de la brodeuse sans conflit de timer avec les moteurs pas-à-pas $X/Y$ :
1. **Interruption ZC :** L'interruption externe (ex: `INT2` sur front descendant, similaire au code développé dans `src/arduino/test_H21A1/test_H21A1.ino`) est déclenchée à chaque passage par zéro.
2. **Rechargement d'un Timer :** L'ISR calcule la valeur de comparaison selon la vitesse souhaitée.
3. **Interruption Timer :** Lorsque le timer expire, il génère une impulsion de $15\ \mu\text{s}$ sur la broche `PSM` pour réarmer le TRIAC.
```cpp


```
---

## 7. Synchronisation globale avec le cycle de broderie

L'introduction de ce variateur s'insère dans la cinématique globale de la machine :

```
         [ Fourche Optique H21A1 ]
         Détection Aiguille Haute
                    |
                    v
    +-------------------------------+
    |   MKS Base V1.4 (ATmega2560)  |
    +-------------------------------+
       |                         |
       v                         v
[ Variateur AC RobotDyn ]  [ Moteurs Pas-à-Pas X/Y ]
Régulation Vitesse Couture    Déplacement du Cadre
(Découpe de phase 50 Hz)    (Uniquement Aiguille HORS Tissu)
```

1. **Cycle de piquage :** Le variateur AC maintient le moteur à une cadence constante et stabilisée (ex: 300 à 500 points/minute).
2. **Synchronisation :** Lorsque l'aiguille remonte et franchit le capteur optique `[[rapport_capteur_h21a1|H21A1]]` (conditionné par la nouvelle carte comparatrice AOP `[[mise_en_service_capteur_h21a1|mise_en_service_capteur_h21a1.md]]`), le microcontrôleur autorise le déplacement des axes $X$ et $Y$.
3. **Arrêt d'urgence ou pause de changement de couleur :** La commande `moteurBroderie.setPower(0)` coupe instantanément la puissance moteur pour stopper la couture en fin de motif.

---

## 8. Règles de Sécurité et Bonnes Pratiques Atelier

1. **Danger d'électrocution ($230\text{ V}$) :** Tout réglage physique ou recâblage doit impérativement s'effectuer hors tension (prise débranchée).
2. **Boîtier d'isolation :** Le module variateur RobotDyn doit être enfermé dans un boîtier isolant dédié (imprimé en 3D en PETG ou PLA résistant), avec orifices de ventilation pour le dissipateur en aluminium du TRIAC.
3. **Ségrégation des câbles :** Séparer physiquement les torons de câbles secteur $230\text{ V}$ des nappes de signaux logiques $5\text{ V}$ (capteurs optiques, endstops, lignes SPI/I2C) pour éviter les rayonnements électromagnétiques parasites (CEM).

---
**Documents et Références Associés :**
* `[[Module Variateur AC, 1 Canal, Logique 3.3V_5V, AC 50_60Hz, 220V_110V _ RobotDyn.pdf]]` — Documentation constructeur RobotDyn
* `[[Configuration_PWM_Arduino|Configuration du PWM sur Arduino]]` — Étude des timers et PWM ATmega
* `[[mise_en_service_capteur_h21a1|mise_en_service_capteur_h21a1.md]]` — Conditionnement du capteur de synchronisation aiguille
* `[[carte_de_commande_mks_base_v1_4|carte_de_commande_mks_base_v1_4.md]]` — Architecture de la carte hôte MKS Base
