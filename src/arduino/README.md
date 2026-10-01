# Firmware Embarqué (Arduino / ATmega2560)

Ce dossier contient le code source destiné au microcontrôleur ATmega2560 de la carte **MKS Base V1.4**.

## Structure
* `test_H21A1/test_H21A1.ino` : Sketch de validation de l'interruption matérielle `INT2` (Pin 19 / `PD2`) pour la détection optique de la position haute de l'aiguille.
* `lib/` : Bibliothèques embarquées (gestion des moteurs pas-à-pas, timer pour découpe de phase du variateur AC).

## Compilation et Téléversement
* **Carte cible :** Arduino Mega 2560 (`ATmega2560`)
* **Vitesse de communication série :** `115200 bauds`
