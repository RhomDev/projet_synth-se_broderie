volatile bool object = false;

void setup() {
  Serial.begin(115200);
  
  // Configuration de la broche 7 (PH4) en sortie et extinction par défaut
  DDRH |= (1 << PH4); 
  PORTH &= ~(1 << PH4); 
  
  // Configuration de la broche 19 (PD2) en entrée pour l'interruption INT2
  DDRD &= ~(1 << PD2); 
  PORTD |= (1 << PD2); // Pull-up interne
  
  // Configuration de l'interruption INT2 sur front descendant (FALLING)
  EICRA &= ~((1 << ISC21) | (1 << ISC20));
  EICRA |= (1 << ISC21); 

  // Nettoyage du drapeau et activation de INT2
  EIFR = (1 << INTF2);
  EIMSK |= (1 << INT2);
}

void loop() {
  if (object) {
    PORTH |= (1 << PH4); // Met la broche 7 à l'état haut
    Serial.println("Front détecté ! Sortie 7 activée.");
    
    delay(500); // Maintient le signal actif pendant 500ms
    PORTH &= ~(1 << PH4); // Remet la broche 7 à l'état bas
    
    object = false; // Réarmement
  }
}

// Routine d'interruption pour INT2 (Pin 19 / PD2)
ISR(INT2_vect) {
  object = true;
}