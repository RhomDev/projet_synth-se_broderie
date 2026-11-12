---
titre: Protocole série PC ↔ carte MKS Base (v1 actuel et v2 proposé)
date: 2026-11-12
projet: Module Broderie
tags:
  - logiciel
  - firmware
  - protocole
  - serie
statut: v1 en service ; v2 validé, écrit dans src/arduino/controle_moteur_v2, pas encore flashé
aliases:
  - Protocole Série
  - Protocole v2
---

# Protocole série PC ↔ carte MKS Base

Référence commune au firmware (`src/arduino/controle_moteur_step/main_controle_motor/`) et à l'application PC (`src/python/communication/protocol.py`).

- **v1** : ce que fait le firmware actuellement flashé.
- **v2** : évolution validée le 12/11/2026, écrite dans `src/arduino/controle_moteur_v2/` (compilée, **pas encore flashée ni testée**). Tant qu'elle n'est pas flashée, l'application la sert par un simulateur étiqueté « SIMULATION ».

---

## 1. Liaison

| Paramètre | Valeur |
| :--- | :--- |
| Débit | 1 000 000 bauds, 8N1 (UBRR0 = 1, U2X0 = 1, erreur 0 %) |
| Puce USB | FTDI FT232R, VID:PID `0403:6001` |
| Ouverture du port | **redémarre l'ATmega** (DTR) : vitesses à 0, origine perdue |

---

## 2. Protocole v1 (firmware actuel)

Analyse caractère par caractère dans l'interruption de réception :
- `M`, `X`, `Y` (majuscules) ouvrent une commande ; `-` donne le signe ; les chiffres forment la valeur ;
- espace, `\r` ou `\n` **exécutent** la commande en cours ;
- tout autre caractère est ignoré. Plusieurs commandes par ligne sont possibles : `X100 Y-200\n`.

| Commande | Effet | Réponse |
| :--- | :--- | :--- |
| `M100` | durée de la dernière fenêtre d'autorisation (µs, 16 bits) | 2 octets binaires, little-endian. Vaut 70 au démarrage (pas une mesure) |
| `M101` | état des fins de course | 1 octet : bit 0 X_min, bit 1 X_max, bit 2 Y_min, bit 3 Y_max (1 = appuyé) |
| `M102` | fenêtre d'autorisation (aiguille hors du tissu) | 1 octet : 0 ou 1 |
| `X<n>` / `X-<n>` | DIR X selon le signe, vitesse X = n | aucune |
| `Y<n>` / `Y-<n>` | idem axe Y | aucune |

Unité de vitesse : cadence = n × 25 000 / 32 768 micropas/s. Plage valide 0 à 32 768. Avec 80 micropas/mm : 1 mm/s ≈ 104,9 unités.

---

## 3. Protocole v2

### 3.1 Principes

1. **Compatibilité** : `M100`, `M101`, `M102`, `X…` et `Y…` gardent exactement leur comportement v1.
2. **Démarrage** : mode broderie, chien de garde coupé, aucune alarme, aucune origine. Sans nouvelle commande, la carte se comporte comme en v1.
3. **Une commande v2 par ligne** : `M<code>` puis des paramètres `<lettre><entier signé>` séparés par des espaces. Fin de ligne `\n` ; `\r` ignoré ; 64 caractères au maximum.
4. **Une réponse ASCII par commande v2**, une seule ligne :
   - `ok M<code> <valeurs appliquées>`
   - `err M<code> <n>`
5. **Aucun message spontané** : le PC interroge (`M111`).
6. Toute ligne valide (v1 ou v2) réarme le chien de garde.

Unités : positions en micropas (int32) ; vitesses dans l'unité v1 (−32 768 à 32 768) ; accélération en micropas/s².

### 3.2 Commandes

| Commande | Paramètres | Effet | Réponse si acceptée |
| :--- | :--- | :--- | :--- |
| `M110` | — | arrêt immédiat de X et Y ; annule mouvements et prise d'origine | `ok M110` |
| `M111` | — | état complet (§ 3.3) | `ok M111 t=… x=… …` |
| `M112` | `S0` ou `S1` | mode : 0 = broderie (pas émis seulement fenêtre ouverte), 1 = manuel (pas émis à tout moment) | `ok M112 S<m>` |
| `M113` | `T0` ou `T100`…`T5000` | chien de garde : sans ligne valide pendant T ms alors qu'un axe a une consigne non nulle → arrêt comme `M110`, alarme bit 0. `T0` = coupé | `ok M113 T<ms>` |
| `M114` | — | acquitte toutes les alarmes | `ok M114` |
| `M120` | `X<v>` et/ou `Y<v>` | consigne de vitesse avec rampe (jog continu) | `ok M120 X<vx> Y<vy>` (consignes des deux axes) |
| `M121` | `A<a>` et/ou `V<v>` | accélération (1 à 16 000 000 µpas/s²) et vitesse max (1 à 32 768) des mouvements | `ok M121 A<a> V<v>` |
| `M122` | `X<dx>` et/ou `Y<dy>` | déplacement relatif (µpas), profil trapèze | `ok M122 X<dx> Y<dy>` (accepté, pas terminé) |
| `M123` | `X<x>` et/ou `Y<y>` | déplacement absolu (µpas) ; refusé si l'origine de l'axe n'est pas faite | `ok M123 X<x> Y<y>` |
| `M130` | `X1` et/ou `Y1`, `F<v>` optionnel | prise d'origine : vers Xmin/Ymin à la vitesse F, recul lent jusqu'au relâchement, position = 0 | `ok M130 X<0/1> Y<0/1> F<v>` (démarrée) |

Règles :
- `M120`, `M122`, `M123` et `M130` ne sont acceptés **qu'en mode manuel** (première version).
- Un nouvel ordre sur un axe remplace le mouvement en cours, en passant par la rampe.
- Chaque axe suit son propre profil : pas d'interpolation linéaire.
- Fin de course atteinte pendant un mouvement (hors prise d'origine) : consigne de l'axe à 0, alarme bit 2 (X) ou 3 (Y).

### 3.3 Ligne d'état (`M111`)

```
ok M111 t=123456 x=1200 y=3400 vx=0 vy=-800 es=0 win=1 mode=1 home=3 mv=2 al=0 va=28500
```

| Champ | Type | Sens |
| :--- | :--- | :--- |
| `t` | uint32 | ms depuis le démarrage. S'il diminue, la carte a redémarré : origine perdue |
| `x`, `y` | int32 | position en micropas, depuis l'origine si elle est faite, sinon depuis la mise sous tension |
| `vx`, `vy` | int | vitesse instantanée signée (unité v1) |
| `es` | 0–15 | fins de course, codage de `M101` |
| `win` | 0/1 | fenêtre d'autorisation, comme `M102` |
| `mode` | 0/1 | 0 broderie, 1 manuel |
| `home` | 0–3 | bit 0 : origine X faite ; bit 1 : origine Y faite |
| `mv` | 0–3 | bit 0 : X en mouvement ; bit 1 : Y en mouvement |
| `al` | 0–15 | bit 0 chien de garde, bit 1 erreur de réception (**bloquants**) ; bit 2 / 3 : fin de course X / Y touchée pendant un mouvement (information) |
| `va` | uint32 | durée de la dernière fenêtre en µs (32 bits) ; **0 tant qu'aucune fenêtre complète n'a été mesurée** |

### 3.4 Codes d'erreur

| Code | Sens |
| :---: | :--- |
| 1 | commande inconnue |
| 2 | paramètre manquant, inconnu ou hors plage |
| 3 | origine non faite |
| 4 | prise d'origine en cours |
| 5 | commande réservée au mode manuel |
| 6 | alarme bloquante active (acquitter par `M114`) |
| 7 | ligne trop longue ou mal formée |

### 3.5 Valeurs au démarrage

| Réglage | Valeur |
| :--- | :--- |
| mode | 0 (broderie) |
| chien de garde | coupé (`T0`) |
| `A` | 80 000 µpas/s² (1 000 mm/s² à 80 µpas/mm) |
| `V` | 2 097 (≈ 20 mm/s) |
| `F` de `M130` | 1 049 (≈ 10 mm/s) |

### 3.6 Précisions ajoutées en rédigeant ce document (validées le 12/11/2026)

1. `err M0 7` quand la ligne ne commence ni par `M`, ni par `X`, ni par `Y`, ou dépasse 64 caractères (ex. `G1 X50` n'est plus exécuté).
2. `va` est sur 32 bits et vaut 0 avant la première mesure. `M100` garde son comportement v1 (16 bits, 70 au démarrage).
3. Le chien de garde ne se déclenche que si un axe a une consigne non nulle (pas d'alarme quand tout est à l'arrêt).
4. Valeurs au démarrage du § 3.5.
5. Tant qu'une alarme bloquante est active, les lignes `X…`/`Y…` (v1) sont ignorées, comme les mouvements v2.

Ajoutée en écrivant le firmware (à valider) :

6. `M112 S0` (retour en mode broderie) arrête les mouvements v2 en cours (`M120` à `M130`), qui sont réservés au mode manuel. Les lignes `X…`/`Y…` ne sont pas touchées.

---

## 4. Modifications nécessaires dans le firmware

1. **Réception** : l'interruption range seulement les caractères dans un tampon de ligne (64 octets) ; l'analyse passe dans `loop()`. Les lignes `X…`/`Y…` et `M100`–`M102` gardent leur effet v1.
2. **Émission** : file circulaire (128 octets) vidée par l'interruption UDRE, ou passage à `Serial`.
3. **Timer 2** : compteur de position int32 par axe (±1 à chaque pas selon DIR). Pas autorisé si la fin de course du sens est libre **et** (mode manuel **ou** fenêtre ouverte).
4. **Tâche à 1 kHz dans `loop()`** : rampes, profils `M122`/`M123`, automate de prise d'origine, chien de garde. Lecture des variables 32 bits partagées sous `cli()`/`sei()`.
5. **Fin de course pendant un mouvement** : consigne à 0, bit d'alarme.
6. **Entrées D51/D53 (TCST2300)** : ne pas activer les pull-ups internes. En parallèle des 33 kΩ externes, la résistance équivalente (~17 kΩ) passerait sous le minimum de 18,4 kΩ calculé dans `[[Capteur_Optique_TCST2300]]` pour saturer le phototransistor.

---

## 5. Correspondance côté Python

| Commande | Fonction (`communication/protocol.py`) |
| :--- | :--- |
| `M110` | `stop_all()` |
| `M111` | `read_status()` |
| `M112` | `set_mode(manual)` |
| `M113` | `set_watchdog(timeout_ms)` |
| `M114` | `clear_alarms()` |
| `M120` | `set_speeds(vx, vy)` |
| `M121` | `set_motion_limits(accel, vmax)` |
| `M122` | `move_relative(dx, dy)` |
| `M123` | `move_absolute(x, y)` |
| `M130` | `home(x, y, speed)` |
| `X…` / `Y…` (v1) | `LegacySpeeds(vx, vy)` : sans réponse, utilisée par la ligne de test |

---
**Voir aussi :**
* `[[Architecture_Logicielle|Architecture Logicielle]]`
* `[[Carte_MKS_Base_V1_4|Carte MKS Base V1.4]]`
* `[[Capteur_Optique_TCST2300|Capteur TCST2300]]`
