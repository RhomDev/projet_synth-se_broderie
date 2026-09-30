## Configuration du PWM (25 kHz) sur Arduino

Le registre **ICR1** du Timer 1 définit le plafond (la valeur "TOP") que le chronomètre interne doit atteindre avant de repartir à zéro. Le temps mis pour accomplir ce cycle détermine la fréquence finale du signal.

## Formule de calcul

Pour déterminer la valeur à injecter dans le registre en mode _Fast PWM_, on utilise la formule suivante :

$$TOP = \frac{f_{CPU}}{N \times f_{PWM}} - 1$$

**Détail des paramètres :**

- **$f_{CPU}$ (16 000 000) :** La vitesse de l'horloge principale de l'Arduino (16 MHz).
    
- **$N$ (1) :** Le prédiviseur (_prescaler_). Ici, l'horloge n'est pas ralentie.
    
- **$f_{PWM}$ (25 000) :** La fréquence cible souhaitée (25 kHz).
    
- **- 1 :** L'ajustement nécessaire car le compteur électronique démarre toujours à 0.
    

## Résultat de l'opération

L'opération $(16 000 000 / 25 000)$ donne 640 étapes de comptage. Puisque l'on commence à 0, la valeur maximale à atteindre est 639.

L'instruction `ICR1 = 639;` commande donc au microcontrôleur de boucler de 0 à 639 à sa vitesse maximale, ce qui génère une impulsion exactement 25 000 fois par seconde.