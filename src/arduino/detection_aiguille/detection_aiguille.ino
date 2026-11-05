volatile bool flag_MOSI_rising = false;
volatile bool flag_SS_rising = false;
static uint8_t last_PINB = 0;

void setup() {
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
}

void loop() {
  if (flag_MOSI_rising) {
    PORTC |= (1 << PC4);       // Allume PC4 (Pin 33)
    delay(50);                // Maintient à 5V pendant 200 ms (ajustable)
    PORTC &= ~(1 << PC4);      // Éteint PC4 (retour à 0V)
    flag_MOSI_rising = false;  // Réinitialise le drapeau d'interruption
  }

  if (flag_SS_rising) {
    PORTC |= (1 << PC6);       // Allume PC6 (Pin 31)
    delay(50);                // Maintient à 5V pendant 200 ms (ajustable)
    PORTC &= ~(1 << PC6);      // Éteint PC6 (retour à 0V)
    flag_SS_rising = false;    // Réinitialise le drapeau d'interruption
  }
}

// Routine d'interruption du groupe PCINT0 (Port B)
ISR(PCINT0_vect) {
  uint8_t current_PINB = PINB;
  uint8_t changed = current_PINB ^ last_PINB;

  // Détection du front montant sur PB2 (SD_MOSI) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB2)) && (current_PINB & (1 << PB2))) {
    flag_MOSI_rising = true;
  }

  // Détection du front montant sur PB0 (SD_SS) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB0)) && (current_PINB & (1 << PB0))) {
    flag_SS_rising = true;
  }

  last_PINB = current_PINB;
}