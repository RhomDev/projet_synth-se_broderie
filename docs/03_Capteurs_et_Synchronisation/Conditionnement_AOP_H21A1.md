---
titre: Module de Conditionnement du Signal Capteur (Comparateur AOP LM741)
date: 2026-09-30
projet: Module Broderie
tags:
  - electronique
  - capteur
  - aop
  - comparateur
  - mks_base
  - kicad
  - pcb
statut: valide
aliases:
  - mise_en_service_capteur_h21a1
  - Conditionnement AOP H21A1
  - Module de correction du signal
---

# Module de Conditionnement du Signal Capteur (Comparateur AOP)

## 1. Contexte et Problématique
La partie réceptrice du capteur optique à fente `[[Fourche_Optique_H21A1|H21A1]]` se comporte comme une résistance variable. Selon la présence ou l'absence d'obstacle dans la fente, sa résistance interne passe de moins de $1\text{ M}\Omega$ à une valeur comprise entre $3\text{ M}\Omega$ et $6\text{ M}\Omega$.

* **À vide (mesure au multimètre) :** La tension varie parfaitement entre $5\text{ V}$ et environ $0{,}8\text{ V}$. Cette plage est théoriquement idéale pour le microcontrôleur de la carte `[[Carte_MKS_Base_V1_4|MKS Base V1.4]]`, car toute tension inférieure à $1{,}5\text{ V}$ est considérée comme un niveau logique bas (`LOW`) stable, permettant la détection fiable d'un front descendant (`FALLING`).
* **En charge (connecté à la carte hôte) :** Lorsque la sortie du capteur est reliée à l'entrée numérique du microcontrôleur, la tension basse remonte à cause des résistances internes de tirage de la carte. La tension stagne alors autour de $2{,}0\text{ V} - 2{,}5\text{ V}$, ce qui représente une zone d'incertitude instable pour l'étage d'entrée logique du processeur ATmega2560.

---

## 2. Principe de la Solution : L'Amplificateur Opérationnel en Comparateur
Pour isoler le capteur de l'influence de la carte et garantir une détection sans faille, nous avons conçu un module intermédiaire de conditionnement.

Son rôle est de convertir la tension analogique instable issue du capteur en un signal tout-ou-rien digital parfaitement franc ($0\text{ V}$ ou $5\text{ V}$ purs) :

$$V_{out} = \begin{cases} 5\text{ V} & \text{si } V^+ > V^- \\ 0\text{ V} & \text{si } V^+ < V^- \end{cases}$$

```
                +5V
                 |
             [R_pullup]
                 |
      Capteur----+-----> (V+) Non-Inverseuse
      H21A1                |
                          |\
                          | \
                          |  \-----> Sortie Digitale D (vers MKS Pin 19)
                          |  /
    Potentiomètre -----> (V-) /
    (Seuil V_ref)         |/
```

---

## 3. Analyse du Montage Électrique
Le montage s'articule autour de trois blocs fonctionnels reliés à l'AOP (modélisé par un composant type LM741 / LM358) :

1. **Signal Capteur (Entrée Non-Inverseuse $V^+$) :** Le phototransistor forme un pont diviseur avec sa résistance de charge reliée au $5\text{ V}$. La tension à ce point est injectée sur la broche $V^+$.
2. **Seuil de Référence Ajustable (Entrée Inverseuse $V^-$) :** Un potentiomètre monté en pont diviseur entre $5\text{ V}$ et la masse permet d'ajuster manuellement la tension de seuil de référence $V_{\text{ref}}$ (fixée typiquement vers $1{,}5\text{ V} - 1{,}8\text{ V}$).
3. **Sortie Digitale Saturation :** L'AOP compare instantanément $V^+$ et $V^-$. Dès que le drapeau mécanique obture le faisceau, la tension chute sous $V_{\text{ref}}$, et la sortie bascule immédiatement à $0\text{ V}$ franc.

![Schéma de correction](montage_correction.png)

---

## 4. Réalisation Matérielle (KiCad PCB)
Le circuit complet a été saisi et routé sous KiCad dans le dossier [`hardware/elect/carte_acquisition_capteur/`](file:///home/rhomdev/Documents/Ecole/projet_synth-se_broderie/hardware/elect/carte_acquisition_capteur/) :
* Schéma électronique : `carte_acquisition_capteur.kicad_sch`
* Circuit imprimé : `carte_acquisition_capteur.kicad_pcb`
* Trous de fixation : 3 trous mécaniques prévus pour fixation rigide sur le châssis.

---

## 5. Procédure de Calibration & Validation
1. Mettre le circuit sous tension $5\text{ V}$.
2. Relever au multimètre la tension haute ($V_{\text{haut}} \approx 4{,}8\text{ V}$) et basse ($V_{\text{bas}} \approx 2{,}2\text{ V}$) délivrées par le capteur sous charge.
3. Régler le potentiomètre pour que $V^-$ se situe exactement à la valeur médiane :
   $$V_{\text{ref}} = \frac{V_{\text{haut}} + V_{\text{bas}}}{2} \approx \frac{4{,}8 + 2{,}2}{2} = 3{,}5\text{ V}$$
4. Vérifier que la sortie bascule de façon nette entre $0\text{ V}$ et $5\text{ V}$ lors de la rotation de l'arbre.
5. Valider la réception d'interruption avec le sketch Arduino : `src/arduino/test_H21A1/test_H21A1.ino`.

---
**Voir aussi :**
* `[[Fourche_Optique_H21A1|Fiche Capteur H21A1]]`
* `[[Carte_MKS_Base_V1_4|Connexion à la Carte MKS Base]]`
* `[[00_Tableau_de_Bord|Tableau de Bord]]`