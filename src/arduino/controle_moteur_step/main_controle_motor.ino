
static uint32_t _Vmax;    // vitesse de croisière (pas/s)
static uint16_t _acceleration;   // Accélération (pas/s²)

volatile bool flag_MOSI_rising = false;
volatile bool flag_SS_rising = false;
static uint8_t last_PINB = 0;

void setup() {
       /*** Configuration des timers pour les délais précis ***/
       // Configuration du timer 1 pour les délais précis 
       TCCR1A = 0; // Mode normal sur les sorties
       TCCR1B = 0; // Réinitialisation
       TCNT1  = 0;
       // Configuration du Prescaler à 8 (CS11 = 1) || Configuration du Mode CTC (WGM12 = 1 dans TCCR1B)
       TCCR1B |= 0x0A;        

       // Valeur initiale pour un pas toutes les 500 µs
       OCR1A = 999;

       // Nettoyer les drapeaux résiduels dans TIFR1
       TIFR1 = 0x02;
       // Activation de l'interruption Compare Match A (OCIE1A)
       TIMSK1 |= 0x02;


       // Configuration du timer 1 pour les délais précis 
       TCCR2A = 0; // Mode normal sur les sorties
       TCCR2B = 0; // Réinitialisation
       TCNT2  = 0;
       // Configuration du Prescaler à 8 (CS11 = 1) || Configuration du Mode CTC (WGM12 = 1 dans TCCR1B)
       TCCR2B |= 0x0A;        

       // Valeur initiale pour un pas toutes les 500 µs
       OCR2A = 999;

       // Nettoyer les drapeaux résiduels dans TIFR1
       TIFR2 = 0x02;
       // Activation de l'interruption Compare Match A (OCIE1A)
       TIMSK2 |= 0x02;


       /*** Configuration des capteurs fin de course ***/
       // fin course X
       DDRE &= ~0x30; // Configure PE5 (Pin 7) pour le MIN et PE4 (Pin 6) pour le MAX en entrée
       DDRJ &= ~0x03; // Configure PJ1 (Pin 64) pour le MIN et PJ0 (Pin 63) pour le MAX en entrée


       /*** Configuration pin MS du Driver ***/
       // Configuration des broches MS1 et MS2 pour le mode de micro-pas Driver X
       DDRE |= 0x08; // Configure PE3 (Pin 5) en sortie pour MS1
       PORTE |= 0x08; // Met PE3 à HIGH pour MS1
       DDRH |= 0x08; // Configure PH8 (Pin 15) en sortie pour MS2
       PORTH |= 0x08; // Met PH8 à HIGH pour MS2

       // Configuration des broches MS1 et MS2 pour le mode de micro-pas Driver Y
       DDRF |= 0x20; // Configure PF5 (Pin 92) en sortie pour MS1
       PORTF |= 0x20; // Met PF5 à HIGH pour MS1 
       DDRF |= 0x10; // Configure PF4 (Pin 93) en sortie pour MS2
       PORTF |= 0x10; // Met PF4 à HIGH pour MS2


       /*** Configuration de la librairie controle_moteur_step ***/
       // Création d'une instance de StepperDriver pour le moteur X
       DDRF |= 0x03; // Configure PF0 (Pin 94) et PF1 (Pin 95) en sortie pour STEP et DIR
       DDRD |= 0x80; // Configure PD7 (Pin 13) en sortie pour ENABLE

        // États par défaut : LOW
       if((PINF & 0x01)==0x01) PINF |= 0x01;
       if((PINF & 0x02)==0x02) PINF |= 0x02;
       if((PIND & 0x80)==0x80) PIND |= 0x80; 

       // Création d'une instance de StepperDriver pour le moteur Y
       DDRF |= 0xC4; // Configure PF6 (Pin 91) et PF7 (Pin 90) en sortie pour STEP et DIR
       // Configure PF2 (Pin 95) en sortie pour ENABLE
       
        // États par défaut : LOW
       if((PINF & 0x40)==0x40) PINF |= 0x40;
       if((PINF & 0x80)==0x80) PINF |= 0x80;
       if((PINF & 0x04)==0x04) PINF |= 0x04;

}

void loop() {
  if (flag_MOSI_rising) {
    
    flag_MOSI_rising = false;  // Réinitialise le drapeau d'interruption
  }

  if (flag_SS_rising) {
    
    flag_SS_rising = false;    // Réinitialise le drapeau d'interruption
  }
}

// Routine d'interruption du groupe PCINT0 (Port B)
ISR(PCINT0_vect) {
  uint8_t current_PINB = PINB;
  uint8_t changed = current_PINB ^ last_PINB;

  // Détection du front montant sur PB2 (SD_MOSI) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB2)) && (current_PINB & (1 << PB2))) {
       PORTC |= (1 << PC4);       // Allume PC4 (Pin 33)
       delay(50);                // Maintient à 5V pendant 200 ms (ajustable)
        PORTC &= ~(1 << PC4);      // Éteint PC4 (retour à 0V)
        flag_MOSI_rising = true;
  }

  // Détection du front montant sur PB0 (SD_SS) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB0)) && (current_PINB & (1 << PB0))) {
       PORTC |= (1 << PC6);       // Allume PC6 (Pin 31)
        delay(50);                // Maintient à 5V pendant 200 ms (ajustable)
       PORTC &= ~(1 << PC6);      // Éteint PC6 (retour à 0V)
       flag_SS_rising = true;
  }

  last_PINB = current_PINB;
}

ISR(TIMER1_COMPA_vect) {
    // Code à exécuter à chaque interruption du timer 1
    // Par exemple, vous pouvez appeler une fonction pour gérer le moteur pas à pas X

}