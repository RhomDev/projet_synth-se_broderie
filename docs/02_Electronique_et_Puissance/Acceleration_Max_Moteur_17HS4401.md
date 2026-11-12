---
titre: Accélération et vitesse maximales du moteur 17HS4401 — Démonstration et modèle de calcul
date: 2026-11-12
projet: Module Broderie
tags:
  - mecanique
  - cinematique
  - moteurs_pas_a_pas
  - modele
  - python
statut: en cours
aliases:
  - Accélération max moteur
  - Modèle de mouvement 17HS4401
  - motion_model
---

# Accélération et vitesse maximales du moteur 17HS4401

Cette fiche démontre la formule de l'accélération maximale que le moteur pas à pas **17HS4401** peut donner au plateau XY en fonction de la masse déplacée. Elle donne aussi la vitesse maximale, le choix du profil de vitesse et les valeurs numériques retenues. Elle s'appuie sur le tableur `calcul_stepper_moteur.xlsx` (`docs/02_Electronique_et_Puissance/`) et sur le module Python `src/python/algorithms/motion_model.py`.

Résultat de la démonstration (frottements négligés) :

$$a_{max} = \frac{C_{dispo}}{\dfrac{J_{rotor}}{r} + m\,r}$$

---

## 1. Objectif et notations

On cherche l'accélération maximale $a_{max}$ du plateau, la vitesse maximale $v_{max}$ et la plus grande distance $x_{max}$ parcourue pendant la fenêtre d'avance de l'aiguille, pour une masse déplacée $m$.

| Symbole | Signification | Unité |
| :--- | :--- | :--- |
| $m$ | masse déplacée (cadre, chariot, tissu) | kg |
| $a$, $v$ | accélération et vitesse linéaires du plateau | m/s², m/s |
| $\alpha$, $\omega$ | accélération et vitesse angulaires de l'arbre moteur | rad/s², rad/s |
| $r$ | rayon primitif de la poulie | m |
| $J_{rotor}$ | inertie du rotor du moteur | kg·m² |
| $C_{dispo}$ | couple moteur utilisable (avec marge de sécurité) | N·m |
| $\mu$ | coefficient de frottement équivalent (rails, courroie) | sans unité |
| $V$ | tension d'alimentation du driver | V |
| $L$, $R$, $I$ | inductance, résistance de phase, courant nominal | H, Ω, A |
| $t$ | durée de la fenêtre d'avance | s |

---

## 2. Valeurs retenues

| Paramètre | Valeur | Origine |
| :--- | :--- | :--- |
| Moteur | 17HS4401 : 40 N·cm, 1,7 A, 1,5 Ω, 2,8 mH, 54 g·cm², 200 pas/tour | `docs/datasheets/moteur_step/17HS4401.pdf` |
| Tension $V$ | 12 V | tableur (`N3`) ; 24 V étudié en comparaison |
| Poulie | GT2 de 20 dents, pas 2 mm, soit 40 mm/tour et $r = 6{,}37$ mm | confirmée le 12 novembre 2026 |
| Masse déplacée $m$ | 0 g (rotor seul), en attendant la mesure | choix du 12 novembre 2026 |
| Frottements $\mu$ | 0 (négligés) | choix du 12 novembre 2026 |
| Coefficient de sécurité | 0,5 sur le couple | marge anti-décrochage |
| Micropas | 1/16 (A4982 : MS1 = MS2 = HIGH), soit 12,5 µm par micropas | firmware `main_controle_motor.ino` |
| Fenêtre d'avance $t$ | 40 ms (hypothèse de travail) | tableur (`E14`) |

> [!NOTE]
> La fenêtre d'avance ne sera plus calculée à partir d'un angle : le microcontrôleur la mesurera entre les deux capteurs optiques de l'aiguille (début du mouvement quand l'aiguille remonte, fin au point haut). Les 40 ms sont une valeur de travail.

---

## 3. Formules de mécanique générale

**Théorème du moment dynamique** (solide en rotation autour d'un axe fixe) :

$$\sum C_{ext} = J\,\frac{d\omega}{dt} = J\,\alpha$$

**Principe fondamental de la dynamique**, projeté sur l'axe de déplacement (translation) :

$$\sum F_{ext} = m\,a \qquad \left(a = \frac{dv}{dt}\right)$$

**Énergie cinétique** en rotation, puis en translation :

$$E_c = \tfrac{1}{2}\,J\,\omega^2 \qquad\qquad E_c = \tfrac{1}{2}\,m\,v^2$$

**Conservation de l'énergie cinétique à travers une transmission** sans pertes. Avec $k = \omega_c/\omega_m$, l'inertie de la charge ramenée à l'arbre moteur est :

$$\tfrac{1}{2}J_m\,\omega_m^2 = \tfrac{1}{2}J_c\,\omega_c^2 \;\Rightarrow\; J_{ramené} = J_c\left(\frac{\omega_c}{\omega_m}\right)^2 = k^2\,J_c$$

**Puissance mécanique** en rotation, puis en translation :

$$P = C\,\omega \qquad\qquad P = F\,v$$

Une transmission sans pertes conserve la puissance : $C\,\omega = F\,v$.

---

## 4. Cinématique poulie-courroie

Sans glissement, tout point de la courroie se déplace à la vitesse de la jante de la poulie. Un tour de poulie fait avancer la courroie de 40 mm.

$$v = \omega\,r \qquad\Rightarrow\qquad a = \frac{dv}{dt} = \alpha\,r \qquad\Rightarrow\qquad \alpha = \frac{a}{r}$$

La courroie exerce sur le plateau une force $F$ tangente à la poulie, qui crée un couple sur l'arbre avec le rayon $r$ comme bras de levier :

$$C = F\,r \qquad\Rightarrow\qquad F = \frac{C}{r}$$

Vérification par la puissance : $C\,\omega = (F\,r)\,\dfrac{v}{r} = F\,v$. La poulie joue le rôle d'un réducteur de rapport $k = r$.

---

## 5. Masse ramenée à l'arbre moteur

Vue de l'arbre, la masse $m$ se comporte comme un volant d'inertie $J_{eq} = m\,r^2$. Deux démonstrations indépendantes le confirment.

**Par l'énergie cinétique.** On remplace $v$ par $\omega\,r$ :

$$E_c = \tfrac{1}{2}\,m\,v^2 = \tfrac{1}{2}\,m\,(\omega\,r)^2 = \tfrac{1}{2}\,\underbrace{(m\,r^2)}_{J_{eq}}\,\omega^2$$

**Par la dynamique.** Le P.F.D. donne $F = m\,a$ et $a = \alpha\,r$, donc le couple opposé à l'arbre est :

$$C = F\,r = m\,a\,r = m\,(\alpha\,r)\,r = (m\,r^2)\,\alpha = J_{eq}\,\alpha$$

Avec $r = 6{,}37$ mm, une masse de 1 kg a une inertie ramenée de $4{,}05\times10^{-5}$ kg·m², soit 7,5 fois l'inertie du rotor ($5{,}4\times10^{-6}$ kg·m²). La charge domine dès que $m$ dépasse quelques centaines de grammes.

---

## 6. Bilan dynamique sur l'arbre moteur

On applique le théorème du moment dynamique à l'ensemble qui tourne avec l'arbre : le rotor et la masse ramenée. Le frottement oppose une force $\mu\,m\,g$ à la courroie, soit un couple $C_{frottement} = \mu\,m\,g\,r$ sur l'arbre.

$$C_{moteur} - \mu\,m\,g\,r = (J_{rotor} + m\,r^2)\,\alpha$$

Le terme $(J_{rotor} + m\,r^2)\,\alpha$ est le **couple d'accélération**. Avec $\alpha = a/r$ :

$$C_{moteur} - \mu\,m\,g\,r = \left(\frac{J_{rotor}}{r} + m\,r\right) a$$

L'accélération est maximale quand le moteur fournit son couple utilisable maximal, $C_{moteur} = C_{dispo}$ :

$$a_{max} = \frac{C_{dispo} - \mu\,m\,g\,r}{\dfrac{J_{rotor}}{r} + m\,r}$$

---

## 7. Simplification : frottements négligés

Pour $m = 1$ kg et $\mu = 0{,}03$, le couple de frottement vaut $\mu\,m\,g\,r \approx 1{,}9$ mN·m, soit 0,9 % de $C_{dispo} = 200$ mN·m. Il change $a_{max}$ de moins de 1 % (27,5 m/s² avec, 27,7 m/s² sans), un écart couvert par le coefficient de sécurité. On pose donc $\mu = 0$ :

$$\boxed{a_{max} = \frac{C_{dispo}}{\dfrac{J_{rotor}}{r} + m\,r} = \frac{C_{dispo}}{r\left(m + \dfrac{J_{rotor}}{r^2}\right)}}$$

Lecture physique : le couple disponible accélère l'inertie totale, vue du plateau comme une masse équivalente $m + J_{rotor}/r^2$. Ici $J_{rotor}/r^2 = 133$ g.

---

## 8. Couple disponible du 17HS4401

On retient $C_{dispo} = 0{,}20$ N·m, soit la moitié du couple de maintien (40 N·cm), pour des vitesses jusqu'au coude de la courbe couple-vitesse (section 9). Le datasheet ne donne pas de courbe couple-vitesse, le chiffre vient d'un modèle électrique simple.

À vitesse élevée, l'inductance empêche le courant d'atteindre sa valeur nominale dans le temps d'un pas, et la force électromotrice s'oppose à la tension. Le courant disponible est borné par :

$$I(\omega) = \min\left(I_{nom},\; \frac{V - K_e\,\omega}{Z}\right) \qquad Z = \sqrt{R^2 + (\omega_e\,L)^2} \qquad \omega_e = 50\,\omega$$

où $\omega_e$ est la pulsation électrique (50 paires de pôles) et $K_e \approx 0{,}13$ V·s/rad un ordre de grandeur déduit du couple de maintien. Le couple maximal vaut $C_{max}(\omega) = C_{maintien}\,I(\omega)/I_{nom}$.

Un moteur pas à pas qui dépasse son couple maximal décroche et perd des pas sans que rien ne le signale. On limite donc le couple utilisé à la moitié du maximum :

$$C_{dispo} = 0{,}5 \times C_{max} = 0{,}5 \times 0{,}40 = 0{,}20\ \text{N·m}$$

| Vitesse du plateau | $C_{max}$ à 24 V (modèle) | $C_{max}$ à 12 V (modèle) |
| :--- | :--- | :--- |
| jusqu'à 150 mm/s | 40 N·cm | 40 N·cm |
| 200 mm/s | 40 N·cm | 39,6 N·cm |
| 300 mm/s | 40 N·cm | 19,9 N·cm |

Le modèle est optimiste, surtout à 12 V : les courbes réelles chutent plus tôt.

---

## 9. Vitesse maximale : le coude de la courbe couple-vitesse

Le courant monte dans une bobine à la vitesse $V/L$. Il atteint $I$ en un temps $L\,I/V$. Le temps minimal entre deux pas entiers est donc $t_{pas} = 2\,L\,I/V$ (le facteur 2 varie selon les calculateurs). La vitesse du coude, au-delà de laquelle le couple baisse, s'en déduit :

$$f_{pas} = \frac{V}{2\,L\,I} \qquad\Rightarrow\qquad n = \frac{V}{2\,L\,I\,spr} \ \text{(tr/s)} \qquad\Rightarrow\qquad v_{max} = n \times 2\pi\,r$$

avec $spr = 200$ pas entiers par tour. **Il ne faut pas prendre 3 200 (micropas)** : la valeur serait 16 fois trop basse.

| Tension | Vitesse du coude | Plateau | Pas entiers/s | Micropas/s (1/16) |
| :--- | :--- | :--- | :--- | :--- |
| 12 V | 6,3 tr/s (378 tr/min) | 252 mm/s | 1 260 | 20 170 |
| 24 V | 12,6 tr/s (756 tr/min) | 504 mm/s | 2 521 | 40 340 |

Jusqu'au coude, le couple est plein : c'est la vitesse retenue pour planifier les profils. Au-delà, le couple décroît à peu près en 1/vitesse. La valeur est approximative (la résistance, la force électromotrice et le hacheur du A4982 l'abaissent) : elle doit être validée par un essai, en gardant 70 à 80 % de la vitesse sans perte de pas.

À 24 V, la cadence de 40 000 micropas/s devient lourde pour l'ATmega2560 avec deux axes. Passer à 1/8 de micropas la diviserait par deux, au prix d'une résolution de 25 µm.

---

## 10. Profil de vitesse : trapèze (qui devient triangle)

Le plateau part de l'arrêt et s'arrête en fin de pas. Deux profils sont possibles :

- **Triangle** : accélération pendant $t/2$ puis décélération pendant $t/2$. Distance $\Delta = a\,t^2/4$, vitesse de pointe $2\,\Delta/t$.
- **Trapèze** : accélération jusqu'à $v_{max}$, palier, décélération. Il n'apparaît que si $\Delta > v_{max}^2/a$.

**Choix : le trapèze.** Le triangle en est le cas limite, donc un seul algorithme couvre tous les pas. Le plafond $v_{max}$ protège le moteur : un triangle sur un grand pas monte à une vitesse de pointe où le couple a chuté. Une courbe en S (accélération progressive) réduit les vibrations à l'arrêt mais allonge la durée ; elle n'est à envisager que si des vibrations gênent après essai.

Avec $t_1 = v_{max}/a_{max}$ la durée de l'accélération, la plus grande distance dans la fenêtre $t$ est :

$$x_{max} = \begin{cases} a_{max}\,t^2/4 & \text{si } t_1 \ge t/2 \quad \text{(triangle)} \\[4pt] a_{max}\,t_1^2 + v_{max}\,(t - 2\,t_1) & \text{si } t_1 < t/2 \quad \text{(trapèze)} \end{cases}$$

**Planifier à partir de la durée.** La fenêtre est imposée par la machine. Pour un pas $\Delta$, on calcule le profil le plus doux qui finit pile à la fin de la fenêtre (fonction `plan_in_window`) : pour un triangle $a = 4\,\Delta/t^2$. Si même le profil le plus rapide dépasse la fenêtre, le pas est infaisable : il faut ralentir la couture ou découper le pas.

---

## 11. Application numérique

Valeurs du chapitre 2, $V = 12$ V, fenêtre de 40 ms. Exemple pour $m = 1$ kg ($r = 6{,}37 \times 10^{-3}$ m, $J_{rotor} = 5{,}4\times10^{-6}$ kg·m²) :

$$a_{max} = \frac{0{,}20}{\dfrac{5{,}4\times10^{-6}}{6{,}37\times10^{-3}} + 1\times 6{,}37\times10^{-3}} = \frac{0{,}20}{0{,}85\times10^{-3} + 6{,}37\times10^{-3}} \approx 27{,}7\ \text{m/s}^2$$

**Accélération maximale et distance maximale selon la masse** ($v_{max} = 252$ mm/s) :

| Masse $m$ (kg) | $a_{max}$ (m/s²) | Profil | $x_{max}$ en 40 ms (mm) |
| :--- | :--- | :--- | :--- |
| 0 (rotor seul) | 235,8 | trapèze | 9,8 |
| 0,25 | 82,0 | trapèze | 9,3 |
| 0,5 | 49,6 | trapèze | 8,8 |
| 1 | 27,7 | trapèze | 7,8 |
| 2 | 14,7 | trapèze | 5,8 |
| 3 | 10,0 | triangle | 4,0 |

À vide, la vitesse limite la distance ($x_{max} \approx v_{max} \times t$), pas l'accélération. Pour dépasser 10 mm en 40 ms, il faudrait passer à 24 V.

**Accélération nécessaire** pour un pas $\Delta$ en un temps $t$ (profil triangle, $a = 4\,\Delta/t^2$) :

| Déplacement $\Delta$ | Durée $t$ | $a$ nécessaire (m/s²) | Vitesse de pointe (mm/s) |
| :--- | :--- | :--- | :--- |
| 1 mm | 25 ms | 6,4 | 80 |
| 3 mm | 35 ms | 9,8 | 171 |
| 5 mm | 40 ms | 12,5 | 250 |
| 5 mm | 35 ms | 16,3 | 286 |
| 3 mm | 25 ms | 19,2 | 240 |

Les lignes à 286 mm/s dépassent la vitesse du coude à 12 V (252 mm/s) : à 12 V, le pas de 5 mm n'est tenable qu'avec une fenêtre d'au moins 40 ms.

**Conversion pour le firmware.** Avec 1/16 de micropas, un micropas vaut 12,5 µm :

$$a_{micropas/s^2} = \frac{a_{max}}{12{,}5\times10^{-6}} \qquad \text{ex. : } 27{,}7\ \text{m/s}^2 \Rightarrow 2{,}2\times10^{6}\ \text{micropas/s}^2$$

---

## 12. Lien avec le tableur et le module Python

| Tableur `calcul_stepper_moteur.xlsx` | Module `motion_model.py` |
| :--- | :--- |
| `E10` : rayon $r$ | `Axis.pulley_radius` (défaut GT2 20 dents) |
| `E11` : `spr` = 360 / angle du pas | `Motor.steps_per_rev` |
| `E12` : `V_max` | `Axis.corner_speed` et `Axis.v_max` |
| `E13` : `a_max` (saisi à la main) | `Axis.a_max` (calculé à partir de la masse) |
| `E14` : `t_max` | argument `window` des fonctions |
| `G14` : `t1` | `MovePlan.t_accel` |
| `E15` : `x_max` | `max_distance(window, a_max, v_max)` |

Fonctions principales : `plan_fastest` (profil le plus rapide), `plan_in_window` (profil le plus doux dans la fenêtre), `max_distance`, `capability_table`. Tests : `src/python/tests/test_motion_model.py` (21 tests, valeurs de référence de cette fiche). En ligne de commande : `python motion_model.py --masse 1 --tension 12`.

**Corrections à reporter dans le tableur :**
- **Formule de `E15`** : les phases d'accélération et de décélération parcourent ensemble $a\,t_1^2$, pas $2\,a\,t_1^2$. Avec les valeurs du tableur ($r = 10$ mm, $a = 100$ m/s²), `x_max` passe de 15,84 mm à 14,27 mm.
- **Rayon `E10`** : 0,01 m doit devenir 0,00637 m (poulie GT2 de 20 dents). `V_max` passe alors de 396 à 252 mm/s.
- **`a_max` (`E13`)** : 100 m/s² est une valeur saisie, sans lien avec la charge. Avec $r = 10$ mm, le couple ne le permet que pour $m \lesssim 0{,}15$ kg.
- **Cas du triangle** : si $t_1 \ge t/2$, la distance vaut $a\,t^2/4$ (non traité dans le tableur).

---

## 13. Limites et points à vérifier

- **Masse déplacée** : pas encore mesurée. Elle doit inclure le cadre, le chariot et le tissu. Sur l'axe Y, il faut y ajouter l'axe X avec son moteur.
- **Courant du driver A4982** : le calcul suppose un réglage de Vref pour 1,7 A. À 1,2 A, le couple baisse d'environ 30 %, donc $a_{max}$ aussi.
- **Frottements** : négligés. Une mesure au dynamomètre ($\mu = F/(m\,g)$, plateau tiré à vitesse constante) confirmera qu'ils restent de l'ordre de quelques pourcents du couple.
- **Firmware** : dans `main_controle_motor.ino`, `_acceleration` est un `uint16_t` (maximum 65 535 pas/s²). Si l'unité est le micropas de 12,5 µm, cela plafonne à 0,8 m/s², bien en dessous des 10 à 20 m/s² nécessaires. À passer en `uint32_t` ; la logique de rampe reste à relire.
- **Modèle** : il ne couvre ni l'élasticité de la courroie, ni les résonances du moteur, ni l'échauffement. Le test réel reste décisif : augmenter l'accélération par paliers avec la vraie charge et garder la valeur où aucun pas n'est perdu, avec une marge.

---
**Voir aussi :**
* [[Plateau_XY_et_Mecanique|Mécanique du Plateau XY]]
* [[Carte_MKS_Base_V1_4|Carte MKS Base V1.4]]
* [[Suivi_des_Taches|Feuille de route et tâches]]
