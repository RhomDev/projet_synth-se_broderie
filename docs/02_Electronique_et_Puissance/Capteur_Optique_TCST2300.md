---
titre: Fiche Technique - Capteur Optique Vishay TCST2300
date: 2026-11-05
projet: Module Broderie
tags:
  - electronique
  - capteur
  - fourche_optique
  - synchronisation
  - mks_base
  - datasheet
statut: valide
aliases:
  - TCST2300
  - Fiche Technique TCST2300
  - Capteur Optique TCST2300
---

# Fiche Technique : Capteur Optique à Fourche Vishay TCST2300

---

## 1. Rôle du Composant

Le **Vishay TCST2300** est un photo-interrupteur à transmission (fourche optique) haute précision. Dans le cadre de la brodeuse numérique, son rôle est d'assurer la **détection de position angulaire de l'arbre principal** (notamment le repérage du **Point Mort Haut - PMH** de l'aiguille).

Un drapeau obturateur mécanique solidaire de l'arbre vient couper le faisceau infrarouge lorsque l'aiguille est complètement dégagée du tissu. Ce signal informe le microcontrôleur (ATmega2560 de la carte MKS Base V1.4) qu'il dispose de la fenêtre temporelle sécurisée pour autoriser le déplacement pas-à-pas du cadre $X/Y$, éliminant tout risque de flexion ou bris d'aiguille.

Grâce à son ouverture de fente de seulement **$0{,}25\text{ mm}$**, le TCST2300 offre une résolution spatiale remarquable de **$0{,}2\text{ mm}$**, garantissant une répétabilité de commutation nettement supérieure aux fourches optiques génériques.

---

## 2. Brochage (Pinout)

Le TCST2300 comporte 4 broches traversantes disposées de part et d'autre de la fente optique (écartement inter-axes de $7{,}62\text{ mm}$ / $0{,}3''$, et pas de $2{,}54\text{ mm}$ / $0{,}1''$ entre broches d'un même côté).

Les repères sont **gravés en relief directement sur le sommet du boîtier en plastique noir** :

```
                  VUE DE DESSUS (TOP VIEW)
                     Fente optique (3,1 mm)
                             | |
              +--------------| |--------------+
              |    [ + ]     | |     [ D ]    |
  ÉMETTEUR    |   (Anode)    | |   (Émetteur) |    RÉCEPTEUR
  (LED IR)    |     LED      | |  Phototrans. | (Phototransistor)
              |    [ E ]     | |     [ + ]    |
              |  (Cathode)   | |  (Collecteur)|
              +--------------| |--------------+
                             | |
              <-------- 7,62 mm (0.3") ------->
```

### Identification des Broches

| Côté Composant | Repère Boîtier | Broche Fonctionnelle | Description Électrique |
| :--- | :---: | :--- | :--- |
| **Émetteur (LED IR)** | **`+`** | **Anode ($A$)** | Pôle positif de la diode infrarouge (à relier à $V_{CC}$ via résistance $R_{LED}$) |
| **Émetteur (LED IR)** | **`E`** | **Cathode ($K$)** | Pôle négatif de la diode infrarouge (à relier à la masse $GND$) |
| **Récepteur (Phototransistor)** | **`+`** | **Collecteur ($C$)** | Collecteur du transistor NPN (à relier à $V_{CC}$ via résistance $R_{pull-up}$ et vers entrée microcontrôleur) |
| **Récepteur (Phototransistor)** | **`D`** | **Émetteur ($E_{trans}$)** | Émetteur du transistor NPN (à relier à la masse $GND$) |

> [!NOTE]
> Le repère **`E`** sur le boîtier désigne le côté **Émetteur** (côté diode, correspondant à la cathode), tandis que le repère **`D`** désigne le côté **Détecteur** (côté récepteur, correspondant à l'émetteur du transistor NPN).

---

## 3. Schéma de Montage Électronique

### Montage Recommandé : Émetteur Commun avec Résistance de Pull-up

Ce montage fournit un niveau logique franc directement compatible avec les entrées logiques du microcontrôleur (ATmega2560 sur carte MKS Base V1.4, Arduino, ou tout MCU 5V / 3,3V).

```
          +5V (VCC)                             +5V (VCC)
             |                                     |
             |                                     |
            [R1] (R_LED = 180 Ω)                  [R2] (R_pullup = 33 kΩ)
             |                                     |
             |                                     +------> Signal vers GPIO / INT
             |                                     |        (ex: D2 / D18 / Endstop MKS)
             v                                     |
           +---+                                 +---+
           | A |                                 | C |
           | + |                                 | + |
           |   |                                 |   |
   LED IR  |   | = = = Faisceau IR = = = >       |   | Phototransistor NPN
  (950 nm) |   |    (Aperture 0.25 mm)           |   |
           | E |                                 | D |
           | K |                                 | E |
           +---+                                 +---+
             |                                     |
             |                                     |
            GND                                   GND
```

### Description Textuelle du Câblage

1. **Section Émetteur (LED IR) :**
   * Relier l'alimentation **$V_{CC}$** (+5V) à l'une des bornes de la résistance de limitation $R_1$ ($180\ \Omega$).
   * Relier l'autre borne de $R_1$ à l'**Anode** (broche marquée **`+`** côté émetteur).
   * Relier la **Cathode** (broche marquée **`E`** côté émetteur) à la masse commune (**$GND$**).

2. **Section Récepteur (Phototransistor) :**
   * Relier l'alimentation **$V_{CC}$** (+5V) à l'une des bornes de la résistance de tirage $R_2$ ($33\text{ k}\Omega$).
   * Relier l'autre borne de $R_2$ au **Collecteur** (broche marquée **`+`** côté détecteur).
   * Relier le point milieu entre $R_2$ et le Collecteur à la **broche d'entrée numérique** du microcontrôleur (entrée Fin de Course / Endstop ou broche d'interruption externe).
   * Relier l'**Émetteur** (broche marquée **`D`** côté détecteur) à la masse commune (**$GND$**).

3. **Découplage Local :**
   * Souder un condensateur céramique multicouche $C_1 = 100\text{ nF}$ au plus près des broches d'alimentation du module ($V_{CC}$ et $GND$).

### Table de Vérité & Logique du Signal

| État Mécanique | Faisceau Optique | État Phototransistor | Tension de Sortie ($V_{signal}$) | Niveau Logique Microcontrôleur |
| :--- | :--- | :--- | :--- | :---: |
| **Repos (Aiguille basse / Fente libre)** | Non occulté (reçu) | **Saturé** (conducteur) | $\approx V_{CEsat} \le 0{,}4\text{ V}$ | **`LOW` (0)** |
| **Détection PMH (Drapeau dans la fente)** | **Coupé** (occulté) | **Bloqué** (isolant) | $\approx V_{CC} = 5{,}0\text{ V}$ | **`HIGH` (1)** |

*L'interruption de synchronisation dans le firmware sera configurée sur front montant (`RISING`) à l'arrivée au PMH, ou sur front descendant (`FALLING`) lors de la sortie du drapeau.*

---

## 4. Dimensionnement des Composants

### 4.1. Résistance de Limitation de la LED IR ($R_{LED}$)

D'après la datasheet Vishay du TCST2300 :
* Tension directe typique : $V_F \approx 1{,}25\text{ V}$ (à $I_F = 20\text{ mA}$).
* Courant nominal recommandé : $I_F = 20\text{ mA}$ (le constructeur garantit le rapport de transfert CTR pour cette valeur de test).
* Courant maximal continu admissible : $I_{F,\max} = 60\text{ mA}$.

#### Formule de Calcul :
$$R_{LED} = \frac{V_{CC} - V_F}{I_F}$$

#### Calcul pour une Alimentation $V_{CC} = 5{,}0\text{ V}$ :
$$R_{LED} = \frac{5{,}0\text{ V} - 1{,}25\text{ V}}{0{,}020\text{ A}} = \frac{3{,}75\text{ V}}{0{,}020\text{ A}} = 187{,}5\ \Omega$$

* **Valeur normalisée recommandée :**
  * **$180\ \Omega$** (série E24) $\implies I_F = \frac{5{,}0 - 1{,}25}{180} \approx 20{,}8\text{ mA}$ (parfaitement calibré).
  * **$220\ \Omega$** (série E12 standard) $\implies I_F = \frac{5{,}0 - 1{,}25}{220} \approx 17{,}0\text{ mA}$ (très bon compromis réduisant l'échauffement).
* **Puissance dissipée :**
  $$P_{R_{LED}} = R \times I_F^2 = 180 \times (0{,}0208)^2 \approx 78\text{ mW}$$
  Une résistance standard de puissance **$1/4\text{ W}$ ($250\text{ mW}$)** offre une marge de sécurité de plus de $3\times$.

*(Si utilisé sous $V_{CC} = 3{,}3\text{ V}$ : $R_{LED} = \frac{3{,}3 - 1{,}25}{0{,}020} = 102{,}5\ \Omega \implies \mathbf{100\ \Omega}$ ou $\mathbf{120\ \Omega}$).*

---

### 4.2. Résistance de Tirage du Phototransistor ($R_{pull-up}$)

> [!IMPORTANT]
> **Particularité critique du modèle TCST2300 :**
> À la différence du TCST2103 (fente large de $1\text{ mm}$, $I_C = 4\text{ mA}$ typique), le **TCST2300 dispose d'une fente ultra-étroite de $0{,}25\text{ mm}$**. 
> Le flux optique reçu par le silicium est donc réduit, ce qui donne un taux de transfert de courant modeste :
> * $CTR_{\min} = 1{,}25\%$
> * $CTR_{typ} = 2{,}5\%$
> Pour $I_F = 20\text{ mA}$, le courant de collecteur passant est seulement de :
> $$I_{C,\min} = 20\text{ mA} \times 0{,}0125 = 0{,}25\text{ mA}\ (250\ \mu\text{A})$$
> $$I_{C,typ} = 20\text{ mA} \times 0{,}025 = 0{,}50\text{ mA}\ (500\ \mu\text{A})$$

Pour garantir que le phototransistor sature franchement lorsque la fente est libre et amène la broche sous la tension de déchet $V_{CEsat} \le 0{,}4\text{ V}$ (bien en-dessous du seuil bas logique de l'ATmega2560 $V_{IL} = 1{,}5\text{ V}$), le courant tiré par la résistance doit être inférieur au courant de saturation $I_{C,\min}$ :

$$I_{pull-up} = \frac{V_{CC} - V_{CEsat}}{R_{pull-up}} \le I_{C,\min}$$

D'où la condition sur la valeur minimale de $R_{pull-up}$ :
$$R_{pull-up} \ge \frac{V_{CC} - V_{CEsat}}{I_{C,\min}} = \frac{5{,}0\text{ V} - 0{,}4\text{ V}}{0{,}00025\text{ A}} = \frac{4{,}6\text{ V}}{0{,}00025\text{ A}} = 18{,}4\text{ k}\Omega$$

#### Analyse du Choix :
* Si l'on utilisait une résistance classique de $1\text{ k}\Omega$ ou $2{,}2\text{ k}\Omega$ (adaptée aux capteurs courants), le phototransistor ne parviendrait **pas** à saturer et la tension basse resterait bloquée vers $4\text{ V}$, empêchant toute détection par le microcontrôleur.
* Une valeur trop élevée ($> 100\text{ k}\Omega$) dégraderait le temps de montée à cause des capacités parasites de la ligne.
* **Valeur recommandée sous 5V :** **$33\text{ k}\Omega$** ou **$47\text{ k}\Omega$** (série E12/E24, $1/4\text{ W}$).
  * Avec $R_{pull-up} = 33\text{ k}\Omega$ :
    $$I_{pull-up} = \frac{4{,}6\text{ V}}{33\text{ k}\Omega} \approx 0{,}139\text{ mA}$$
    Le coefficient de sursaturation est de $k_{sat} = \frac{0{,}25\text{ mA}}{0{,}139\text{ mA}} \approx 1{,}8$, assurant un état bas franc ($V_{OL} \le 0{,}3\text{ V}$) même avec le vieillissement de la LED IR.
  * Constante de temps avec une capacité de ligne parasite $C_p \approx 25\text{ pF}$ : $\tau = R \cdot C = 33\text{ k}\Omega \times 25\text{ pF} \approx 0{,}8\ \mu\text{s}$. Cette durée est totalement négligeable devant la période de rotation de la brodeuse ($60\text{ ms}$ à $1000\text{ tr/min}$).

*(Si utilisé sous $V_{CC} = 3{,}3\text{ V}$ : $R_{pull-up} \ge \frac{3{,}3 - 0{,}4}{0{,}25\text{ mA}} = 11{,}6\text{ k}\Omega \implies \mathbf{22\text{ k}\Omega}$ ou $\mathbf{33\text{ k}\Omega}$).*

---

## 5. Précautions Matérielles & Recommandations d'Intégration

### 5.1. Limites Absolues à Ne Pas Dépasser (Absolute Maximum Ratings)

| Paramètre | Symbole | Valeur Limite Absolue | Conséquence en cas de Dépassement |
| :--- | :---: | :---: | :--- |
| **Courant direct max LED** | $I_F$ | **$60\text{ mA}$** | Destruction thermique de la jonction GaAs. Maintenir $I_F \le 20-25\text{ mA}$. |
| **Tension inverse max LED** | $V_R$ | **$6\text{ V}$** | Claquage irréversible de la diode IR si câblée à l'envers. |
| **Tension Collecteur-Émetteur** | $V_{CEO}$ | **$70\text{ V}$** | Claquage par avalanche du phototransistor. |
| **Tension inverse Émetteur-Collecteur**| $V_{ECO}$ | **$7\text{ V}$** | Destruction en cas de mauvaise polarisation du transistor. |
| **Puissance totale dissipée** | $P_{tot}$ | **$250\text{ mW}$** | À température ambiante $T_{amb} \le 25^\circ\text{C}$ (déclassement au-delà). |
| **Température de fonctionnement** | $T_{amb}$| **$-55^\circ\text{C}$ à $+85^\circ\text{C}$** | Tenir éloigné des points chauds moteurs. |

### 5.2. Recommandations CEM & Environnement Industriel

1. **Filtrage Électrique :**
   * Dans l'environnement d'une brodeuse, le hachage PWM des drivers pas-à-pas (A4982) et le variateur AC (moteur 230V) injectent des parasites haute fréquence sur le bus 5V.
   * Placer impérativement un condensateur de découplage de **$100\text{ nF}$ céramique** entre $V_{CC}$ et $GND$ au plus près du capteur.
   * Si la ligne de signal mesure plus de $30\text{ cm}$, utiliser un **câble blindé ou une paire torsadée** (Signal + GND), avec le blindage raccordé à la masse côté carte MKS Base uniquement.

2. **Sensibilité Optique & Ambiance Textile :**
   * Le TCST2300 intègre un filtre optique opaque à la lumière visible qui atténue l'éclairage ambiant. Cependant, éviter d'exposer la fente optique directement à une source infrarouge parasite (éclairage halogène puissant ou soleil direct).
   * **Poussières et bourres textiles :** La fente réceptrice mesurant seulement $0{,}25\text{ mm}$, l'accumulation de peluches de fil ou de poussières de tissu peut provoquer des faux déclenchements. Prévoir un capot de protection mécanique ou un dégagement suffisant pour permettre un nettoyage périodique à l'air sec.

3. **Guidage Mécanique de l'Obturateur :**
   * Largeur de fente mécanique : $3{,}1\text{ mm}$.
   * Utiliser une lame obturatrice rigide et totalement opaque (tôle aluminium noircie ou plastique opaque d'épaisseur $0{,}8\text{ mm}$ à $1{,}2\text{ mm}$).
   * Veiller à ce que l'obturateur passe au centre de la fente sans risque de frottement mécanique contre les parois internes du capteur en cas de vibration.

---

## 6. Références & Documents Associés

* **Datasheet Constructeur :** `[[TCST2300.pdf|Fiche Technique Vishay TCST2300]]` (Doc. Vishay n°81147)
* **Carte de Commande :** `[[Carte_MKS_Base_V1_4|Documentation Carte MKS Base V1.4]]`
* **Choix Comparateur / Conditionnement :** `[[comparateur-aop-choix|Note Technique Comparateur]]`
* **Précédente Étude :** `[[Fourche_Optique_H21A1|Retour d'expérience Fourche Optique H21A1]]`
