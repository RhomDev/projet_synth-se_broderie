---
titre: Encodeur Rotatif Incrémental SEN0230 (GoTronic)
date: 2026-11-02
projet: Module Broderie
tags:
  - capteur
  - encodeur
  - cinematique
  - vitesse
  - mks_base
statut: actif
aliases:
  - Encodeur SEN0230
  - SEN0230
  - Encodeur Rotatif
---

# 🔄 Encodeur Rotatif Incrémental SEN0230 (GoTronic)

## 1. Rôle dans le Projet

L'encodeur rotatif **SEN0230** est dédié au suivi cinématique en continu de l'arbre de la machine à coudre :
* Mesure de la vitesse de rotation réelle du moteur secteur 230V pour l'asservissement en boucle fermée via le `[[Module_Variateur_AC|variateur AC RobotDyn]]`.
* Suivi de la position angulaire relative entre les passages au point mort haut recalés par le `[[Capteur_Fin_de_Course_Aiguille|fin de course aiguille]]`.

---

## 2. Caractéristiques Techniques (Datasheet)

| Paramètre | Valeur Spécifiée | Remarques |
| :--- | :--- | :--- |
| **Modèle** | SEN0230 (DFRobot / GoTronic) | Encodeur optique incrémental 2 canaux |
| **Résolution native** | $400\text{ impulsions / tour}$ | Canaux A et B en quadrature de phase |
| **Vitesse maximale admissible** | **$5000\text{ tours / minute}$** | Compatible haute vitesse |
| **Diamètre d'arbre** | $\varnothing 6\text{ mm}$ | Fixation poulie par vis pointeau sur méplat |
| **Tension d'alimentation** | $5\text{ V} - 24\text{ V DC}$ | Alimenté directement en $+5\text{ V}$ par la MKS Base |
| **Sorties logiques** | NPN collecteur ouvert | Requiert résistances de pull-up vers $+5\text{ V}$ |
| **Accessoire fourni** | Équerre de fixation rigide en aluminium | Montage simplifié sur le châssis |

---

## 3. Validation Mécanique & Dimensionnement de la Poulie

L'encodeur est entraîné par la courroie motrice reliant le moteur de la machine à la grosse poulie de l'arbre principal.

### Données de la cinématique de la machine :
* Poulie moteur : $9\text{ dents}$
* Grosse poulie arbre : $83\text{ dents}$ (rapport $83/9 \approx 9{,}22$)
* Vitesse de rotation maximale estimée de la machine : $\approx 860\text{ tr/min}$ (sur la grosse poulie)

### Calcul de la vitesse de l'arbre d'encodeur ($n$ dents) :
* Nombre de dents défilant par minute :
  $$D = 860\text{ tr/min} \times 83\text{ dents} = 71\,380\text{ dents/min}$$
* Vitesse de rotation de l'encodeur $N$ pour une poulie à $n$ dents :
  $$N = \frac{71\,380}{n}$$
* **Critère de sécurité constructeur :** $N \le 5000\text{ tr/min}$, ce qui impose :
  $$n \ge \frac{71\,380}{5000} \approx 14{,}28\text{ dents}$$

| Nombre de dents $n$ poulie encodeur | Vitesse résultante $N$ (à 860 tr/min machine) | Marge par rapport aux 5000 tr/min max |
| :---: | :---: | :---: |
| **16 dents** | $\approx 4461\text{ tr/min}$ | **$+10{,}8\%$ de marge de sécurité** |
| **18 dents** | $\approx 3965\text{ tr/min}$ | **$+20{,}7\%$ de marge de sécurité** |
| **20 dents** | $\approx 3569\text{ tr/min}$ | **$+28{,}6\%$ de marge de sécurité** |

> [!TIP]
> Le dimensionnement retenu est une poulie crantée de **16 à 18 dents** imprimée en 3D (matériau PETG ou Nylon pour la résistance à l'usure, avec flasques de guidage et vis pointeau avec insert écrou sur méplat $\varnothing 6\text{ mm}$). Les contraintes de vitesse de l'encodeur sont ainsi scrupuleusement respectées.

---

## 4. Câblage sur Carte MKS Base V1.4

* **Fil Rouge :** VCC ($+5\text{ V}$)
* **Fil Noir :** GND (Masse commune)
* **Fil Blanc :** Phase A (Entrée numérique / interruption microcontrôleur)
* **Fil Vert :** Phase B (Entrée numérique direction/quadrature)

---
**Voir aussi :**
* `[[fiche_technique_encodeur_sen0230.pdf|Datasheet officielle SEN0230]]`
* `[[Note_Decision_Capteur_Fourche_H21A1|Note de Décision : Choix Capteurs]]`
* `[[Capteur_Fin_de_Course_Aiguille|Fin de Course Aiguille & Homing]]`
* `[[Module_Variateur_AC|Variateur AC RobotDyn]]`
* `[[Carte_MKS_Base_V1_4|Brochage MKS Base V1.4]]`
