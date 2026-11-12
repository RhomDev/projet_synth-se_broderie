# Firmware v2 de la brodeuse

Sketch Arduino pour la MKS Base V1.4 (ATmega2560). Protocole : `docs/05_Logiciel_et_Firmware/Protocole_Serie.md`.

**État : écrit et compilé, jamais téléversé ni testé sur la carte.**

## Rapport au firmware v1

Le firmware v1 (`../controle_moteur_step/main_controle_motor/`) n'est pas modifié : c'est la version de retour arrière.

| Inchangé | Nouveau |
| :--- | :--- |
| Broches, micropas 1/16, drivers toujours actifs | Compteur de position par axe (micropas émis) |
| Timer 2 à 25 kHz, accumulateurs 16 bits | Mode manuel (`M112 S1`) : pas émis même fenêtre fermée |
| Fins de course : bloquent seulement le sens qui y mène | Rampes, déplacements comptés avec arrêt exact, prise d'origine |
| Fenêtre aiguille D53 / D51, voyants D31 / D33 | Chien de garde (`M113`), alarmes (`M114`) |
| `M100`, `M101`, `M102`, lignes `X…` / `Y…` | Ligne d'état `M111`, réponses `ok` / `err` |

Différences volontaires avec la v1 :
- une valeur `X…`/`Y…` au-delà de 32 768 est bornée à 32 768 (la v1 devenait erratique) ;
- les commandes sont exécutées à la fin de ligne (`\n`), plus à l'espace : `serial_bridge.py` envoie déjà `\n` ;
- un mot illisible dans une ligne `X…`/`Y…` est ignoré en entier.

## Points à relire en priorité

1. `ISR(TIMER2_COMPA_vect)` : condition d'émission d'un pas, comptage de position, arrêt exact sur la cible.
2. `gerer_axe()` : profil trapèze de `M122`/`M123` (freinage quand `reste ≤ v²/2a`), prise d'origine.
3. `ISR(PCINT0_vect)` : mesure de la fenêtre (`M100` inchangé, `va` sur 32 bits).
4. Le passage en mode broderie (`M112 S0`) arrête les mouvements v2 en cours (`M120` à `M130`).

## Compiler et téléverser

Arduino IDE : carte « Arduino Mega or Mega 2560 », processeur ATmega2560. Ou en ligne de commande :

```bash
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 src/arduino/controle_moteur_v2
arduino-cli upload  --fqbn arduino:avr:mega:cpu=atmega2560 -p /dev/ttyUSB0 src/arduino/controle_moteur_v2
```

Compilation vérifiée le 12/11/2026 (core arduino:avr 1.8.8) : 9 442 octets de flash, 687 octets de RAM, aucun avertissement.

## Premier essai (dans cet ordre)

Prévoir de couper l'alimentation 12 V à tout moment. Commencer à basse vitesse.

1. **Sans 12 V** (USB seul) : connecter l'application. Elle doit détecter la v2 (`M111` répond). Vérifier la ligne d'état.
2. **Fins de course** : appuyer à la main sur chacune ; le voyant correspondant doit s'allumer dans l'onglet capteurs.
3. **Fenêtre aiguille** : tourner le volant à la main ; « Fenêtre aiguille » doit s'ouvrir et se fermer, et `va` donner une durée.
4. **Avec 12 V**, mode manuel : jog lent en X+ puis X−. Vérifier le sens et que le compteur suit.
5. **Sens et fins de course** : en jog lent vers Xmax, appuyer à la main sur Xmax : l'axe doit s'arrêter, et l'alarme d'information « fin de course X » apparaître. Idem pour Xmin, Ymin, Ymax.
6. **Chien de garde** : lancer un jog lent, puis débrancher le câble USB. L'axe doit s'arrêter en moins de 0,5 s.
7. **Prise d'origine** à vitesse réduite, puis mesure des courses.
8. **Charge série** : pendant un déplacement rapide, vérifier que `al` reste à 0 (aucune erreur de réception).

## Retour à la v1

Téléverser `src/arduino/controle_moteur_step/main_controle_motor/`. L'application détecte alors le firmware v1 et passe en mode diagnostic (capteurs seulement).
