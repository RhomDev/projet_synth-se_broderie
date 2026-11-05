volatile bool flag_MOSI_rising = false;
volatile bool flag_SS_rising = false;
static uint8_t last_PINB = 0;

void setup() {
  // Configuration de PB2 (SD_MOSI) et PB0 (SD_SS) en entrée
  DDRB &= ~((1 << PB2) | (1 << PB0));

  // Capture de l'état initial de la broche
  last_PINB = PINB;

  // Activation du groupe d'interruption PCIE0 (Port B)
  PCICR |= (1 << PCIE0);

  // Activation des masques PCINT2 (PB2 / SD_MOSI) et PCINT0 (PB0 / SD_SS)
  PCMSK0 |= (1 << PCINT2) | (1 << PCINT0);
}

void loop() {
  if (flag_MOSI_rising) {
    // Traitement front montant SD_MOSI
    flag_MOSI_rising = false;
  }
  if (flag_SS_rising) {
    // Traitement front montant SD_SS
    flag_SS_rising = false;
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