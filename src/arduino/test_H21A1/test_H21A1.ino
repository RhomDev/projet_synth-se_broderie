volatile bool object = false;

void setup() {
  Serial.begin(115200);
  
  // Configuration de PB7 (Pin 13) en sortie (0x80)
  DDRB |= 0x80; 
  
  // Configuration de PD2 (Pin 19) en entrée (mise à 0 du bit 2 du port D)
  DDRD &= ~0x04; 

  // Configuration de l'interruption INT2 sur front descendant (FALLING)
  // ISC21 = 1 et ISC20 = 0 dans le registre EICRA
  EICRA |= (1 << ISC21);
  EICRA &= ~(1 << ISC20);

  // Activation de l'interruption INT2 dans le registre EIMSK
  EIMSK |= (1 << INT2);
}

void loop() {
  if (object) {
    PORTB |= 0x80; // Met la sortie PB7 à l'état haut
    object = false; 
  }
}

// Routine d'interruption vectorielle pour INT2 (Pin 19)
ISR(INT2_vect) {
  object = true;
}