
static bool ARUX=true;
static bool ARUY=true;

static uint32_t _Vmax;    // vitesse de croisière (pas/s)
static uint16_t _acceleration;   // Accélération (pas/s²)

volatile bool flag_autorisation_ = false;
static uint8_t last_PINB = 0;

volatile uint8_t last_PINJ = 0;

void setup() {
      /*** Configuration de la gestion de la détection de l'aiguille ***/
      // Configuration de PB2 (SD_MOSI) et PB0 (SD_SS) en entrée
        DDRB &= ~((1 << PB2) | (1 << PB0));
        DDRC |= 0x50;
        
        // Capture de l'état initial de la broche
        last_PINB = PINB;

        // Activation du groupe d'interruption PCIE0 (Port B)
        PCICR |= (1 << PCIE0);

        // Activation des masques PCINT2 (PB2 / SD_MOSI) et PCINT0 (PB0 / SD_SS)
        PCMSK0 |= (1 << PCINT2) | (1 << PCINT0);

        // Extinction par défaut des sorties au démarrage (état bas 0V)
        PORTC &= ~((1 << PC4) | (1 << PC6));

        /*** Configuration des capteurs fin de course ***/
        // fin course X
        DDRE &= ~0x30; // Configure PE5/INT4 (Pin 7) pour le MIN et PE4/INT5 (Pin 6) pour le MAX en entrée
        DDRJ &= ~0x03; // Configure PJ1/PCINT10 (Pin 64) pour le MIN et PJ0/PCINT9 (Pin 63) pour le MAX en entrée

        EICRB &= ~((1 << ISC41) | (1 << ISC51));
        EICRB |= (1 << ISC40) | (1 << ISC50);

        // Effacement des flags
        EIFR |= (1 << INTF4) | (1 << INTF5);
        // Activation des interruptions
        EIMSK |= (1 << INT4) | (1 << INT5);

        // Activation du groupe PCINT1
        PCICR |= (1 << PCIE1);
        // Activation PCINT9 et PCINT10
        PCMSK1 |= (1 << PCINT9) | (1 << PCINT10);

        // Effacement du flag
        PCIFR |= (1 << PCIF1);
        previousStateJ = PINJ & 0x03;

      /*** Configuration du timer 2 pour les délais précis ***/
      TCCR2A = 0x00;
      TCCR2B = 0x00;
      TCNT2 = 0;

      // Mode CTC : WGM21 = 1
      TCCR2A |= 0x02;
      // Valeur de comparaison : 3
      OCR2A = 3;
      // Prescaler = 8
      TCCR2B |= 0x02;

      // Effacement du flag OCF2A
      TIFR2 |= 0x02;
      // Activation de l'interruption Compare Match A
      TIMSK2 |= 0x02;

      
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
       PORTF &= ~ 0x03;
       PORTD &= ~ 0x80; 

       // Création d'une instance de StepperDriver pour le moteur Y
       DDRF |= 0xC4; // Configure PF6 (Pin 91) et PF7 (Pin 90) en sortie pour STEP et DIR
       // Configure PF2 (Pin 95) en sortie pour ENABLE
       // États par défaut : LOW
       PORTF &= ~ 0xC4;


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
        flag_autorisation_ = true;
  }
  // Détection du front montant sur PB0 (SD_SS) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB0)) && (current_PINB & (1 << PB0))) {
       PORTC |= (1 << PC6);       // Allume PC6 (Pin 31)
        delay(50);                // Maintient à 5V pendant 200 ms (ajustable)
       PORTC &= ~(1 << PC6);      // Éteint PC6 (retour à 0V)
       flag_autorisation_ = false;
  }

  last_PINB = current_PINB;
}

ISR(TIMER2_COMPA_vect)
{
    // Ton code ici
}

ISR(INT4_vect)
{
    // Changement d'état sur INT4
    if ((PINE & 0x10)==0x10) {
      ARUX = false;
    }else{
      ARUX = true
    }
}

ISR(INT5_vect)
{
    // Changement d'état sur INT5
    if ((PINE & 0x20)==0x20) {
      ARUX = false;
    }else{
      ARUX = true
    }
}

ISR(PCINT1_vect)
{
    uint8_t currentStateJ = PINJ & 0x03;

    uint8_t changed = currentStateJ ^ previousStateJ;

    if (changed & (1 << PJ0))
    {
        // Changement d'état PCINT9
        if ((PINJ & 0x01)==0x01) {
          ARUY = false;
        }else{
          ARUY = true
        }
    }

    if (changed & (1 << PJ1))
    {
        // Changement d'état PCINT10
        if ((PINJ & 0x02)==0x02) {
          ARUY = false;
        }else{
          ARUY = true
        }
    }

    previousStateJ = currentStateJ;
}