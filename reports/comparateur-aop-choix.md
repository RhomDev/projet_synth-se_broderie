# Comparateur capteur H21A1 : choix de l'AOP

Note de conception : pourquoi le LM318N et le TL081CN ne conviennent pas à une alimentation 5 V, et quel composant utiliser à la place.

## 1. Objectif

Un capteur à fente (H21A1) fournit une tension A. La sortie du montage doit être à 5 V (ou 3,3 V selon le contrôleur) si A dépasse 2,5 V, et à 0 V sinon. Cette sortie est lue par une broche d'entrée du microcontrôleur.

Seul le +5 V de la carte est disponible. La carte ne fournit aucune tension négative.

## 2. Pourquoi le LM318N et le TL081CN ne conviennent pas

### Ce qu'est un AOP « rail-to-rail »

Un « rail » est une ligne d'alimentation (le +V, et le 0 V ou le −V). Un AOP rail-to-rail peut amener sa sortie presque jusqu'à ces deux tensions, et certains acceptent aussi des entrées proches des rails. Alimenté en 0/5 V, il sort donc environ 0 V et 5 V.

Le LM318N et le TL081CN ne sont pas rail-to-rail.

### Caractéristiques du LM318-N (fiche produit TI)

| Paramètre | Valeur |
|---|---|
| Rail-to-rail | Non |
| Alimentation totale | 10 V min (±5 V) à 40 V max |
| Marge de sortie par rapport aux alimentations (typ.) | environ 2 V de chaque côté |
| Marge des entrées par rapport aux alimentations (typ.) | environ 3,5 V de chaque côté |
| Courant d'entrée (max) | 500 nA |
| Vitesse de variation (typ.) | 70 V/µs |
| Produit gain-bande (typ.) | 15 MHz |

Source : https://www.ti.com/product/LM318-N

### Conséquences pour ce montage

| Alimentation | Plage d'entrée utilisable | Sortie possible | Verdict |
|---|---|---|---|
| 5 V simple (0/5 V) | impossible : sous le minimum de 10 V | non garantie | à éviter |
| ±5 V | environ ±1,5 V | environ ±3 V | A (≈ 5 V) et la référence (2,5 V) sont hors plage |
| ±12 V | environ ±8,5 V | environ ±10 V | entrées OK, sortie à écrêter |

Pour le TL081CN, la même logique s'applique : on a relevé sur la courbe « maximum peak-to-peak output voltage versus supply voltage » de sa datasheet environ 6 V crête-à-crête de sortie pour une alimentation de ±4 V, soit environ 1 V de perte de chaque côté. Les autres valeurs du TL081 n'ont pas été revérifiées dans cette note.

## 3. Observations faites sur le montage

Montage testé : LM318N, V+ (broche 7) à 5 V, V− (broche 4) à la masse, référence 2,5 V sur la broche 3, capteur sur la broche 2.

- Sortie du capteur seule : 5 V.
- Sortie du capteur branchée sur la broche 2 : environ 2,6 à 2,7 V.
- Entrée laissée en l'air : 1,6 V (normal, une entrée non reliée n'a pas de tension définie).
- Capteur chargé par 750 Ω vers la masse : 1 V. Ce résultat est cohérent avec un phototransistor qui se comporte comme une source de courant d'environ 1,3 mA.

La chute à 2,6 V quand le capteur est branché sur l'AOP n'est pas expliquée de façon certaine. La cause la plus probable est l'alimentation hors spécification du LM318N (voir le tableau ci-dessus), mais cela n'a pas été confirmé par un test.

Remarque : avec la référence sur « + » et le capteur sur « − », la logique est inversée (sortie haute quand la fente est obstruée). Pour obtenir « haut quand A > 2,5 V », le capteur doit aller sur « + » et la référence sur « − ».

## 4. Solution recommandée : un comparateur LM393

Le LM393 est un vrai comparateur conçu pour fonctionner en alimentation simple (5 V). Sa sortie est à collecteur ouvert : il ne sait que tirer la sortie vers 0 V, et une résistance de rappel R6 la remonte à 5 V le reste du temps. Il n'a besoin ni de tension négative, ni de diodes d'écrêtage.

Le LM393 contient deux comparateurs. Brochage à vérifier sur la datasheet : 1 = sortie A, 2 = entrée − A, 3 = entrée + A, 4 = masse, 5 = entrée + B, 6 = entrée − B, 7 = sortie B, 8 = alimentation.

### Bloc 1 : capteur

Brochage H21A1 à vérifier sur la datasheet (1 = anode, 2 = cathode, 3 = collecteur, 4 = émetteur).

```
+5 V ── R1 (220 Ω) ── broche 1 (anode)
broche 2 (cathode) ── GND
broche 3 (collecteur) ── +5 V
broche 4 (émetteur) ──┬── R2 (10 kΩ) ── GND
                      └── point A
```

### Bloc 2 : référence 2,5 V

```
+5 V ── R3 (10 kΩ) ──┬── R4 (10 kΩ) ── GND
                     └── point « 2,5 V »
```

### Bloc 3 : comparateur LM393

```
broche 8 ── +5 V
broche 4 ── GND
broche 3 (+) ── point A
broche 2 (−) ── point « 2,5 V »
broche 1 (sortie) ──┬── vers le microcontrôleur
                    └── R6 (10 kΩ) ── +5 V (ou 3,3 V)
broche 5 ── GND
broche 6 ── point « 2,5 V »
broche 7 ── laissée en l'air
```

Un condensateur de 100 nF entre les broches 8 et 4, près du boîtier, évite les oscillations. Les masses du capteur, du LM393 et de la carte doivent être reliées.

### Résultat

| Capteur | A | Sortie |
|---|---|---|
| Fente dégagée | > 2,5 V | haute (tension de R6) |
| Fente obstruée | ≈ 0 V | 0 V |

### Tension de R6

R6 doit être reliée à la tension logique du microcontrôleur : 5 V pour une carte 5 V, 3,3 V pour une carte 3,3 V. Une broche ne doit pas dépasser son alimentation d'environ 0,3 V, sauf si elle est indiquée « tolérante 5 V ».

### Point à confirmer sur la datasheet du LM393

Le signal A peut monter vers 5 V, ce qui dépasse la plage d'entrée en mode commun du LM393 en 5 V. La datasheet indique en principe que la sortie reste correcte tant que l'autre entrée est dans la plage, ce qui est le cas pour la référence de 2,5 V. À vérifier dans la datasheet du fabricant avant de figer le montage.

## 5. Alternative : garder le LM318N en ±12 V

Possible seulement si une alimentation ±12 V est disponible.

```
broche 7 ── +12 V
broche 4 ── −12 V
broche 3 (+) ── point A
broche 2 (−) ── point « 2,5 V »
broche 6 ── R5 (1 kΩ) ──┬── sortie (0/5 V)
                        ├── Zener 5,1 V (cathode côté sortie, anode GND)
                        └── Schottky BAT85 (cathode côté sortie, anode GND)
```

Pour une carte 3,3 V, remplacer la zener par un modèle 3,3 V. Les broches de compensation du LM318N (1, 5, 8) sont à vérifier dans la datasheet « LM118/LM218/LM318 » de TI avant utilisation.

Pour fabriquer un −5 V à partir du +5 V, un ICL7660 avec deux condensateurs de 10 µF existe, mais il ne résout pas le problème de plage d'entrée (voir section 2, ligne ±5 V).

## 6. Autres options rail-to-rail

Pour une alimentation 5 V simple, un AOP rail-to-rail (par exemple MCP6002 ou LMV321) est une alternative au LM393. Le câblage est celui du bloc 3, sans R6 ni diodes : la sortie est directement à environ 0 V et 5 V. Caractéristiques à confirmer sur les datasheets avant achat.

## 7. À vérifier avant de figer le montage

- Brochage du H21A1 et du LM393 sur leurs datasheets.
- Plage d'entrée en mode commun du LM393 (section 4).
- Tension logique du microcontrôleur, pour choisir la tension de R6.
- Tension de A capteur dégagé : si elle est inférieure à 3 V, passer R2 à 22 kΩ.
