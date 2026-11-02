volatile bool object = false;

void setup() {
  // Initialisation de la console série pour observer les résultats
  Serial.begin(115200);
  
  // Configuration de PB7 (Pin 13) en sortie et extinction par défaut
  DDRB |= 0x80; 
  PORTB &= ~0x80; 
  
  // Configuration de PD2 (Pin 19) en entrée
  DDRD &= ~0x04; 
  
  // Activation du Pull-up interne sur PD2 pour stabiliser le signal à 5V
  PORTD |= 0x04; 

  // Configuration de l'interruption INT2 sur front descendant (FALLING)
  // 1. Mise à zéro des deux bits par sécurité
  EICRA &= ~((1 << ISC21) | (1 << ISC20));
  // 2. Configuration du mode FALLING (ISC21 = 1, ISC20 = 0)
  EICRA |= (1 << ISC21);

  // Nettoyage du drapeau d'interruption (écriture d'un 1 pour l'effacer)
  EIFR = (1 << INTF2);

  // Activation de l'interruption INT2 dans le registre de masque
  EIMSK |= (1 << INT2);
}

void loop() {
  if (object) {
    PORTB |= 0x80; // Met la sortie PB7 à l'état haut (Allume la LED)
    Serial.println("Détection : Capteur masqué !");
    
    delay(100); // Court délai pour visualiser l'action
    
    PORTB &= ~0x80; // Remet la sortie PB7 à l'état bas (Éteint la LED)
    object = false; // Réarmement pour la prochaine détection
  }
}

// Routine d'interruption vectorielle pour INT2 (Pin 19)
ISR(INT2_vect) {
  object = true;
}