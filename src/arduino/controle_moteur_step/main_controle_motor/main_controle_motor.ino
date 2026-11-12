
// true = capteur touché, false = libre
volatile bool endstop_X_min = false; 
volatile bool endstop_X_max = false;
volatile bool endstop_Y_min = false;
volatile bool endstop_Y_max = false;

// --- VARIABLES POUR LE PARSEUR SÉRIE ---
volatile char current_cmd = 0;       // 'M', 'X', ou 'Y'
volatile uint32_t current_val = 0;   // La valeur numérique en cours de lecture
volatile int8_t current_sign = 1;    // 1 pour positif, -1 pour négatif

volatile uint16_t buffer_V_autorise = 0; // Pour éviter la corruption des 16 bits

// Les accumulateurs (les "seaux")
volatile uint16_t acc_X = 0;
volatile uint16_t acc_Y = 0;

// Les vitesses (0 = moteur à l'arrêt, 32768 = vitesse maximum théorique)
volatile uint16_t vitesse_X = 0; 
volatile uint16_t vitesse_Y = 0;

static long _time_tempo=0;
static uint16_t _V_autorise = 70;

volatile bool flag_autorisation_ = false;
static uint8_t last_PINB = 0;

volatile uint8_t last_PINJ = 0;
volatile uint8_t previousStateJ = 0;
// Variable pour savoir où on en est dans l'envoi
volatile bool envoyerPoidsFort = false;

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
  DDRE &= ~0x30; // Entrées PE4 et PE5
  PORTE |= 0x30; // ACTIVATION DES PULL-UPS

  // fin course Y
  DDRJ &= ~0x03; // Entrées PJ0 et PJ1
  PORTJ |= 0x03; // ACTIVATION DES PULL-UPS

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

  /*** Configuration du timer 2 à 25 kHz (Tick = 40µs) ***/
  TCCR2A = 0x00;
  TCCR2B = 0x00;
  TCNT2 = 0;

  // Mode CTC : WGM21 = 1
  TCCR2A |= (1 << WGM21);
  
  // Valeur de comparaison = 79
  // Fréquence = 16 000 000 / (Prescaler 8 * (79 + 1)) = 25 000 Hz
  OCR2A = 79;
  
  // Prescaler = 8
  TCCR2B |= (1 << CS21);

  // Activation de l'interruption Compare Match A
  TIMSK2 |= (1 << OCIE2A);

  
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

  // Baud Rate à 1 000 000 bauds (F_CPU = 16 MHz)
  UBRR0H = 0;
  UBRR0L = 1;
  UCSR0A = (1 << U2X0);

  // RXCIE0 : Interruption de réception
  // RXEN0 / TXEN0 : Activation RX et TX
  UCSR0B = (1 << RXCIE0) | (1 << RXEN0) | (1 << TXEN0);
  
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);

  update_endstops_X();
  update_endstops_Y();
}

void loop() {
  if (flag_autorisation_) {
    PORTC |= (1 << PC4);       // Allume PC4 (Pin 33)
    PORTC &= ~(1 << PC6);      // Éteint PC6 (retour à 0V)
    
  }else{
    PORTC |= (1 << PC6);       // Allume PC6 (Pin 31)
    PORTC &= ~(1 << PC4);      // Éteint PC4 (retour à 0V)
  }
}


ISR(USART0_RX_vect) {
  uint8_t c = UDR0; // Lecture immédiate du caractère reçu

  // 1. Si on reçoit une lettre de commande
  if (c == 'M' || c == 'X' || c == 'Y') {
    current_cmd = c;
    current_val = 0;   // Remise à zéro de la valeur
    current_sign = 1;  // Par défaut positif
  } 
  // 2. Si on reçoit le signe moins
  else if (c == '-') {
    current_sign = -1;
  }
  // 3. Si on reçoit un chiffre, on reconstruit le nombre entier à la volée
  else if (c >= '0' && c <= '9') {
    current_val = (current_val * 10) + (c - '0');
  }
  // 4. Si on reçoit un Espace, un Retour Chariot (\r) ou une Fin de Ligne (\n) -> ON EXÉCUTE
  else if (c == ' ' || c == '\n' || c == '\r') {
    
    // Si aucune commande n'était en cours, on ignore
    if (current_cmd != 0) {
      
      // --- COMMANDE M100 : Demande de V_autorise (Renvoie 2 octets) ---
      if (current_cmd == 'M' && current_val == 100) {
        buffer_V_autorise = _V_autorise;
        UDR0 = (uint8_t)(buffer_V_autorise & 0xFF); // Envoi immédiat du Low Byte
        envoyerPoidsFort = true;
        UCSR0B |= (1 << UDRIE0); // Active l'ISR d'envoi pour le High Byte
      }
      
      // --- COMMANDE M101 : Demande de l'état des 4 fins de course ---
      else if (current_cmd == 'M' && current_val == 101) {
        uint8_t etat_aru = 0;
        if (endstop_X_min) etat_aru |= (1 << 0); // Bit 0
        if (endstop_X_max) etat_aru |= (1 << 1); // Bit 1
        if (endstop_Y_min) etat_aru |= (1 << 2); // Bit 2
        if (endstop_Y_max) etat_aru |= (1 << 3); // Bit 3
        
        UDR0 = etat_aru; // Envoi immédiat (1 seul octet)
      }
      // --- COMMANDE M102 : Demande de l'état d'autorisation (Renvoie 1 octet) ---
      else if (current_cmd == 'M' && current_val == 102) {
        // Envoie 1 si flag_autorisation_ est true, 0 s'il est false
        UDR0 = (uint8_t)flag_autorisation_; 
      }
      
      // --- COMMANDE X : Moteur X ---
      else if (current_cmd == 'X') {
        if (current_sign == -1) {
          PORTF &= ~(1 << PF1); // DIR X en LOW (Recul)
        } else {
          PORTF |= (1 << PF1);  // DIR X en HIGH (Avance)
        }
        vitesse_X = (uint16_t)current_val;
      }
      
      // --- COMMANDE Y : Moteur Y ---
      else if (current_cmd == 'Y') {
        if (current_sign == -1) {
          PORTF &= ~(1 << PF7); // DIR Y en LOW (Recul)
        } else {
          PORTF |= (1 << PF7);  // DIR Y en HIGH (Avance)
        }
        vitesse_Y = (uint16_t)current_val;
      }

      // On réinitialise la commande en cours
      current_cmd = 0; 
    }
  }
}

// 2. INTERRUPTION DE TRANSMISSION (Se déclenche toute seule quand le 1er octet est parti)
ISR(USART0_UDRE_vect) {
  if (envoyerPoidsFort) {
    // UTILISER buffer_V_autorise (et non _V_autorise) !
    UDR0 = (uint8_t)(buffer_V_autorise >> 8); 
    
    envoyerPoidsFort = false;
    UCSR0B &= ~(1 << UDRIE0);
  }
}

// Routine d'interruption du groupe PCINT0 (Port B)
ISR(PCINT0_vect) {
  uint8_t current_PINB = PINB;
  uint8_t changed = current_PINB ^ last_PINB;

  // Détection du front montant sur PB2 (SD_MOSI) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB2)) && (current_PINB & (1 << PB2))) {
    _V_autorise = micros() - _time_tempo;
    flag_autorisation_ = false;
  }
  // Détection du front montant sur PB0 (SD_SS) : état modifié ET actuellement HAUT (1)
  if ((changed & (1 << PB0)) && (current_PINB & (1 << PB0))) {
    _time_tempo = micros();
    flag_autorisation_ = true;
  }
  last_PINB = current_PINB;
}

ISR(TIMER2_COMPA_vect) {
  uint8_t portf_state = PORTF; 

  // --- MOTEUR X ---
  bool dir_X_positif = (portf_state & (1 << PF1)); 
  bool allow_X = (dir_X_positif && !endstop_X_max) || (!dir_X_positif && !endstop_X_min);

  // NOUVEAU : On ajoute flag_autorisation_ !
  if (allow_X && flag_autorisation_) {
    acc_X += vitesse_X;
    if (acc_X >= 32768) {
      acc_X -= 32768;            
      portf_state |= (1 << PF0); 
    }
  }

  // --- MOTEUR Y ---
  bool dir_Y_positif = (portf_state & (1 << PF7)); 
  bool allow_Y = (dir_Y_positif && !endstop_Y_max) || (!dir_Y_positif && !endstop_Y_min);

  // NOUVEAU : On ajoute flag_autorisation_ !
  if (allow_Y && flag_autorisation_) {
    acc_Y += vitesse_Y;
    if (acc_Y >= 32768) {
      acc_Y -= 32768;            
      portf_state |= (1 << PF6); 
    }
  }

  // Exécution de l'impulsion... (Garder le reste de l'ISR identique avec l'asm volatile)
  PORTF = portf_state;
  asm volatile("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
  PORTF &= ~((1 << PF0) | (1 << PF6));
}

// --- GESTION FIN DE COURSE X ---
void update_endstops_X() {
  // Si le bit vaut 0 (relié au GND), alors "== 0" renvoie 'true' (Appuyé)
  endstop_X_max = ((PINE & (1 << PE4)) == 0); 
  endstop_X_min = ((PINE & (1 << PE5)) == 0); 
}

ISR(INT4_vect) { update_endstops_X(); }
ISR(INT5_vect) { update_endstops_X(); }

// --- GESTION FIN DE COURSE Y ---
void update_endstops_Y() {
  endstop_Y_max = ((PINJ & (1 << PJ0)) == 0); 
  endstop_Y_min = ((PINJ & (1 << PJ1)) == 0); 
}

ISR(PCINT1_vect) {
  update_endstops_Y();
  previousStateJ = PINJ & 0x03; // Historique pour le groupe PCINT
}
