// ============================================================================
//  Brodeuse à patch : firmware v2 (MKS Base V1.4 / ATmega2560 à 16 MHz)
//  Protocole : docs/05_Logiciel_et_Firmware/Protocole_Serie.md
//
//  Reprend le firmware v1 (controle_moteur_step/main_controle_motor) :
//  - mêmes broches, même génération de pas (Timer 2 à 25 kHz, accumulateurs 16 bits) ;
//  - M100, M101, M102 et les lignes X…/Y… gardent leur comportement v1 ;
//  - ajoute les commandes v2 M110 à M130 (état, mode manuel, chien de garde,
//    rampes, déplacements comptés, prise d'origine).
//
//  Organisation :
//  - interruptions : pas (Timer 2), réception/émission série, capteurs ;
//  - loop() : analyse des lignes reçues, réponses, tâche à 1 kHz (rampes,
//    profils, prise d'origine, chien de garde).
//
//  À RELIRE ET TESTER avant usage (voir README.md de ce dossier).
// ============================================================================

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdlib.h>
#include <util/atomic.h>

// ----------------------------------------------------------------- constantes

#define LINE_MAX            64        // caractères par ligne reçue
#define RX_LINES            4         // lignes reçues en attente de traitement
#define TX_SIZE             128       // file d'émission (puissance de 2)
#define SPEED_MAX           32768L    // vitesse max (unité v1) = 25 000 µpas/s
#define ACCEL_MAX           16000000UL
#define DEFAULT_ACCEL       80000UL   // µpas/s² (1 000 mm/s² à 80 µpas/mm)
#define DEFAULT_VMAX        2097      // ≈ 20 mm/s
#define DEFAULT_HOME_SPEED  1049      // ≈ 10 mm/s
#define V_MIN_UNITS         64        // vitesse plancher en fin de déplacement (≈ 0,6 mm/s)
#define WATCHDOG_MIN_MS     100
#define WATCHDOG_MAX_MS     5000

// Vitesses internes en Q15 : unités v1 × 32768 (±32768 × 32768 = ±2^30, tient dans un int32)
#define Q15(u) ((int32_t)(u) << 15)

// Modes d'un axe
enum { MODE_IDLE, MODE_LEGACY, MODE_SPEED, MODE_MOVE, MODE_HOME };
enum { HOME_SEEK, HOME_BACKOFF };

// Bits d'alarme (champ « al » de M111)
#define AL_WATCHDOG 0x01   // bloquant
#define AL_RX_ERROR 0x02   // bloquant
#define AL_LIMIT_X  0x04   // information
#define AL_LIMIT_Y  0x08   // information
#define AL_BLOCKING (AL_WATCHDOG | AL_RX_ERROR)

// Codes d'erreur (« err M<code> <n> »)
enum { ERR_UNKNOWN = 1, ERR_PARAM, ERR_NOT_HOMED, ERR_HOMING, ERR_MANUAL_ONLY, ERR_ALARM, ERR_MALFORMED };

// Broches des drivers (port F), comme en v1
#define X_STEP PF0   // D54
#define X_DIR  PF1   // D55
#define Y_STEP PF6   // D60
#define Y_DIR  PF7   // D61

// ------------------------------------------------- variables des interruptions

// Fins de course : true = appuyé (contact NO vers GND, pull-up interne)
volatile bool endstop_X_min = false;
volatile bool endstop_X_max = false;
volatile bool endstop_Y_min = false;
volatile bool endstop_Y_max = false;

// Génération des pas (Timer 2)
volatile uint16_t acc_X = 0, acc_Y = 0;          // accumulateurs (« seaux »)
volatile uint16_t vitesse_X = 0, vitesse_Y = 0;  // module de la vitesse, 0..32768
volatile int32_t  pos_X = 0, pos_Y = 0;          // compteurs de micropas émis
volatile bool     actif_X = false, actif_Y = false;   // pas autorisé et vitesse > 0
volatile bool     stop_arme_X = false, stop_arme_Y = false;  // arrêt exact sur cible
volatile int32_t  stop_pos_X = 0, stop_pos_Y = 0;
volatile bool     atteint_X = false, atteint_Y = false;
volatile bool     mode_manuel = false;           // M112 : pas émis à tout moment
volatile bool     tick_1khz = false;
static uint8_t    tick_div = 0;

// Fenêtre aiguille (2 × TCST2300) : D53 (PB0) ouvre, D51 (PB2) ferme
volatile bool     flag_autorisation_ = false;
static uint8_t    last_PINB = 0;
static long       _time_tempo = 0;               // v1 : début de fenêtre (pour M100)
volatile uint16_t _V_autorise = 70;              // v1 : M100, 16 bits, 70 au démarrage
static bool       fenetre_commencee = false;
static uint32_t   fenetre_debut_us = 0;
volatile uint32_t fenetre_us = 0;                // v2 : champ va, 0 = jamais mesurée

// Réception : file de lignes complètes (double tampon généralisé)
static char       rx_buf[RX_LINES][LINE_MAX + 1];
static bool       rx_trop_long[RX_LINES];
volatile uint8_t  rx_ecrit = 0, rx_lit = 0, rx_nb = 0;   // indices de la file
volatile uint8_t  rx_pos = 0;                            // caractères de la ligne en cours
volatile bool     rx_debord = false;

// Émission : file circulaire vidée par l'interruption UDRE
volatile uint8_t  tx_buf[TX_SIZE];
volatile uint8_t  tx_tete = 0, tx_queue = 0;

volatile uint8_t  alarmes = 0;

// ----------------------------------------------------- variables de loop()

struct Axe {
  uint8_t  mode;
  int32_t  v;            // vitesse courante signée, Q15
  int32_t  v_cible;      // consigne M120, Q15
  int32_t  cible;        // position visée par M122/M123
  uint8_t  phase;        // prise d'origine
  uint16_t vitesse_home; // F de M130
  bool     origine;      // prise d'origine faite
};
static Axe axe[2];       // 0 = X, 1 = Y

static uint32_t accel = DEFAULT_ACCEL;   // M121 A, µpas/s²
static int32_t  dv_q15 = 0;              // variation de vitesse par ms, Q15
static int32_t  vmax_q15 = Q15(DEFAULT_VMAX);
static uint16_t chien_ms = 0;            // M113 T (0 = coupé)
static uint32_t derniere_ligne_ms = 0;   // dernière ligne valide reçue

// Paramètres de la ligne en cours d'analyse (lettres A..Z)
static int32_t  pval[26];
static uint32_t pmasque = 0;
#define PV(c)     pval[(c) - 'A']
#define A_PARAM(c) (pmasque & (1UL << ((c) - 'A')))

// ======================================================================= setup

void setup() {
  // --- Fenêtre aiguille : PB2 (D51, SD_MOSI) et PB0 (D53, SD_SS) en entrée ---
  // Pas de pull-up interne : les TCST2300 ont leur 33 kΩ externe (voir la fiche capteur).
  DDRB &= ~((1 << PB2) | (1 << PB0));
  DDRC |= 0x50;                       // PC4 (D33) et PC6 (D31) : voyants
  last_PINB = PINB;
  PCICR |= (1 << PCIE0);
  PCMSK0 |= (1 << PCINT2) | (1 << PCINT0);
  PORTC &= ~((1 << PC4) | (1 << PC6));

  // --- Fins de course X : PE4 (D2, X max) et PE5 (D3, X min) ---
  DDRE &= ~0x30;
  PORTE |= 0x30;                      // pull-ups
  EICRB &= ~((1 << ISC41) | (1 << ISC51));
  EICRB |= (1 << ISC40) | (1 << ISC50);   // tout changement
  EIFR |= (1 << INTF4) | (1 << INTF5);
  EIMSK |= (1 << INT4) | (1 << INT5);

  // --- Fins de course Y : PJ0 (D15, Y max) et PJ1 (D14, Y min) ---
  DDRJ &= ~0x03;
  PORTJ |= 0x03;
  PCICR |= (1 << PCIE1);
  PCMSK1 |= (1 << PCINT9) | (1 << PCINT10);
  PCIFR |= (1 << PCIF1);

  // --- Micropas 1/16 : MS1 = MS2 = 1 (X : PE3, PH3 ; Y : PF5, PF4) ---
  DDRE |= 0x08; PORTE |= 0x08;
  DDRH |= 0x08; PORTH |= 0x08;
  DDRF |= 0x30; PORTF |= 0x30;

  // --- Drivers : STEP/DIR X (PF0, PF1), ENABLE X (PD7), STEP/DIR Y (PF6, PF7), ENABLE Y (PF2) ---
  DDRF |= 0x03 | 0xC4;
  DDRD |= 0x80;
  PORTF &= ~(0x03 | 0xC4);            // ENABLE Y à 0 : driver actif
  PORTD &= ~0x80;                     // ENABLE X à 0 : driver actif

  // --- Timer 2 : CTC, prescaler 8, OCR2A = 79 → 25 kHz (tick de 40 µs) ---
  TCCR2A = (1 << WGM21);
  TCCR2B = (1 << CS21);
  TCNT2 = 0;
  OCR2A = 79;
  TIMSK2 |= (1 << OCIE2A);

  // --- UART0 : 1 000 000 bauds (UBRR = 1, U2X), 8N1, interruptions RX ---
  UBRR0H = 0;
  UBRR0L = 1;
  UCSR0A = (1 << U2X0);
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);
  UCSR0B = (1 << RXCIE0) | (1 << RXEN0) | (1 << TXEN0);

  for (uint8_t a = 0; a < 2; a++) {
    axe[a].mode = MODE_IDLE;
    axe[a].v = axe[a].v_cible = 0;
    axe[a].origine = false;
  }
  regler_accel(DEFAULT_ACCEL);
  update_endstops_X();
  update_endstops_Y();
  derniere_ligne_ms = millis();
}

// ======================================================================== loop

void loop() {
  while (rx_nb) {
    uint8_t i = rx_lit;
    traiter_ligne(rx_buf[i], rx_trop_long[i]);
    rx_lit = (i + 1) % RX_LINES;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { rx_nb--; }
  }
  if (tick_1khz) {
    tick_1khz = false;
    tache_1khz();
  }
  // Voyants de la fenêtre aiguille (comme en v1)
  if (flag_autorisation_) {
    PORTC |= (1 << PC4);
    PORTC &= ~(1 << PC6);
  } else {
    PORTC |= (1 << PC6);
    PORTC &= ~(1 << PC4);
  }
}

// =========================================================== interruptions

// Génération des pas à 25 kHz. Un pas n'est émis que si la fin de course du sens
// est libre ET (mode manuel OU fenêtre aiguille ouverte).
ISR(TIMER2_COMPA_vect) {
  uint8_t portf = PORTF;
  bool porte = mode_manuel || flag_autorisation_;

  bool dir_x = portf & (1 << X_DIR);
  bool ok_x = porte && (dir_x ? !endstop_X_max : !endstop_X_min);
  actif_X = ok_x && vitesse_X;
  if (ok_x) {
    acc_X += vitesse_X;
    if (acc_X >= 32768) {
      acc_X -= 32768;
      portf |= (1 << X_STEP);
      if (dir_x) pos_X++; else pos_X--;
      if (stop_arme_X && pos_X == stop_pos_X) {   // arrêt exact sur la cible
        vitesse_X = 0;
        stop_arme_X = false;
        atteint_X = true;
      }
    }
  }

  bool dir_y = portf & (1 << Y_DIR);
  bool ok_y = porte && (dir_y ? !endstop_Y_max : !endstop_Y_min);
  actif_Y = ok_y && vitesse_Y;
  if (ok_y) {
    acc_Y += vitesse_Y;
    if (acc_Y >= 32768) {
      acc_Y -= 32768;
      portf |= (1 << Y_STEP);
      if (dir_y) pos_Y++; else pos_Y--;
      if (stop_arme_Y && pos_Y == stop_pos_Y) {
        vitesse_Y = 0;
        stop_arme_Y = false;
        atteint_Y = true;
      }
    }
  }

  PORTF = portf;
  asm volatile("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
  PORTF &= ~((1 << X_STEP) | (1 << Y_STEP));

  if (++tick_div >= 25) {   // 25 kHz / 25 = 1 kHz
    tick_div = 0;
    tick_1khz = true;
  }
}

// Réception : on range seulement les caractères ; l'analyse se fait dans loop().
ISR(USART0_RX_vect) {
  uint8_t etat = UCSR0A;              // à lire avant UDR0
  uint8_t c = UDR0;
  if (etat & ((1 << FE0) | (1 << DOR0))) alarmes |= AL_RX_ERROR;
  if (c == '\n') {
    if (rx_nb >= RX_LINES) {
      alarmes |= AL_RX_ERROR;         // file pleine : ligne perdue
    } else {
      rx_buf[rx_ecrit][rx_pos] = 0;
      rx_trop_long[rx_ecrit] = rx_debord;
      rx_ecrit = (rx_ecrit + 1) % RX_LINES;
      rx_nb++;
    }
    rx_pos = 0;
    rx_debord = false;
  } else if (c == '\r') {
    // ignoré
  } else if (rx_pos < LINE_MAX) {
    rx_buf[rx_ecrit][rx_pos++] = c;
  } else {
    rx_debord = true;
  }
}

ISR(USART0_UDRE_vect) {
  if (tx_tete == tx_queue) {
    UCSR0B &= ~(1 << UDRIE0);         // file vide
    return;
  }
  UDR0 = tx_buf[tx_queue];
  tx_queue = (tx_queue + 1) & (TX_SIZE - 1);
}

// Fenêtre aiguille : front montant D53 (PB0) = ouverture, D51 (PB2) = fermeture.
ISR(PCINT0_vect) {
  uint8_t pinb = PINB;
  uint8_t change = pinb ^ last_PINB;
  if ((change & (1 << PB2)) && (pinb & (1 << PB2))) {
    uint32_t maintenant = micros();
    _V_autorise = (uint16_t)(maintenant - _time_tempo);    // v1, inchangé
    if (fenetre_commencee) {
      fenetre_us = maintenant - fenetre_debut_us;          // v2, 32 bits
      fenetre_commencee = false;
    }
    flag_autorisation_ = false;
  }
  if ((change & (1 << PB0)) && (pinb & (1 << PB0))) {
    _time_tempo = micros();
    fenetre_debut_us = (uint32_t)_time_tempo;
    fenetre_commencee = true;
    flag_autorisation_ = true;
  }
  last_PINB = pinb;
}

void update_endstops_X() {
  endstop_X_max = ((PINE & (1 << PE4)) == 0);
  endstop_X_min = ((PINE & (1 << PE5)) == 0);
}
ISR(INT4_vect) { update_endstops_X(); }
ISR(INT5_vect) { update_endstops_X(); }

void update_endstops_Y() {
  endstop_Y_max = ((PINJ & (1 << PJ0)) == 0);
  endstop_Y_min = ((PINJ & (1 << PJ1)) == 0);
}
ISR(PCINT1_vect) { update_endstops_Y(); }

// ===================================================================== émission

static void tx_put(uint8_t c) {
  uint8_t suivant = (tx_tete + 1) & (TX_SIZE - 1);
  while (suivant == tx_queue) { }     // file pleine : l'interruption UDRE la vide
  tx_buf[tx_tete] = c;
  tx_tete = suivant;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { UCSR0B |= (1 << UDRIE0); }
}

static void tx_str(const char *s) { while (*s) tx_put(*s++); }

static void tx_u32(uint32_t v) {
  char b[11];
  ultoa(v, b, 10);
  tx_str(b);
}

static void tx_i32(int32_t v) {
  char b[12];
  ltoa(v, b, 10);
  tx_str(b);
}

static void tx_champ(const char *nom, int32_t v) {   // " nom=valeur"
  tx_put(' ');
  tx_str(nom);
  tx_put('=');
  tx_i32(v);
}

static void tx_param(char lettre, int32_t v) {        // " X123"
  tx_put(' ');
  tx_put(lettre);
  tx_i32(v);
}

static void repondre_debut(uint16_t code) {
  tx_str("ok M");
  tx_u32(code);
}

static void repondre_err(uint16_t code, uint8_t err) {
  tx_str("err M");
  tx_u32(code);
  tx_put(' ');
  tx_u32(err);
  tx_put('\n');
}

// ==================================================================== axes

static int32_t lire_pos(uint8_t a) {
  int32_t p;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { p = a ? pos_Y : pos_X; }
  return p;
}

static bool fc_min(uint8_t a) { return a ? endstop_Y_min : endstop_X_min; }
static bool fc_max(uint8_t a) { return a ? endstop_Y_max : endstop_X_max; }

// Applique une vitesse signée (Q15) au Timer 2. DIR ne change que si la vitesse
// est non nulle (comme en v1, le dernier sens reste en place à l'arrêt).
// En déplacement compté, ne réapplique pas une vitesse si l'interruption vient
// d'arrêter l'axe sur sa cible.
static void appliquer_vitesse(uint8_t a, int32_t v_q15, bool seulement_si_arme) {
  bool positif = v_q15 >= 0;
  uint32_t mag = (uint32_t)(positif ? v_q15 : -v_q15) >> 15;
  if (mag > SPEED_MAX) mag = SPEED_MAX;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    if (seulement_si_arme && !(a ? stop_arme_Y : stop_arme_X)) return;
    if (a == 0) {
      if (mag) { if (positif) PORTF |= (1 << X_DIR); else PORTF &= ~(1 << X_DIR); }
      vitesse_X = mag;
    } else {
      if (mag) { if (positif) PORTF |= (1 << Y_DIR); else PORTF &= ~(1 << Y_DIR); }
      vitesse_Y = mag;
    }
  }
}

static void arreter_axe(uint8_t a) {
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    if (a == 0) { vitesse_X = 0; stop_arme_X = false; atteint_X = false; }
    else        { vitesse_Y = 0; stop_arme_Y = false; atteint_Y = false; }
  }
  axe[a].v = 0;
  axe[a].v_cible = 0;
  axe[a].mode = MODE_IDLE;
}

static void arreter_tout() {
  arreter_axe(0);
  arreter_axe(1);
}

static bool prise_origine_en_cours() {
  return axe[0].mode == MODE_HOME || axe[1].mode == MODE_HOME;
}

static bool axes_actifs() {
  return axe[0].mode != MODE_IDLE || axe[1].mode != MODE_IDLE;
}

static void regler_accel(uint32_t a) {
  accel = a;
  // unités par ms = a / 1000 × 32768 / 25000 ; en Q15 : a × 42,94967 = a × 2814750 / 65536
  dv_q15 = (int32_t)(((uint64_t)a * 2814750ULL) >> 16);
  if (dv_q15 < 1) dv_q15 = 1;
}

static int32_t approcher(int32_t v, int32_t cible, int32_t pas) {
  if (v < cible) return (cible - v > pas) ? v + pas : cible;
  return (v - cible > pas) ? v - pas : cible;
}

// Ligne v1 « X100 Y-200 » : DIR selon le signe, vitesse immédiate, pas de réponse.
static void vitesse_legacy(uint8_t a, bool negatif, uint32_t val) {
  if (val > (uint32_t)SPEED_MAX) val = SPEED_MAX;   // v1 devenait erratique au-delà
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    if (a == 0) {
      if (negatif) PORTF &= ~(1 << X_DIR); else PORTF |= (1 << X_DIR);
      vitesse_X = val;
      stop_arme_X = false;
    } else {
      if (negatif) PORTF &= ~(1 << Y_DIR); else PORTF |= (1 << Y_DIR);
      vitesse_Y = val;
      stop_arme_Y = false;
    }
  }
  axe[a].v = negatif ? -Q15(val) : Q15(val);
  axe[a].v_cible = 0;
  axe[a].mode = val ? MODE_LEGACY : MODE_IDLE;
}

static void armer_deplacement(uint8_t a, int32_t cible) {
  axe[a].cible = cible;
  if (cible == lire_pos(a)) {
    arreter_axe(a);
    return;
  }
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    if (a == 0) { stop_pos_X = cible; stop_arme_X = true; atteint_X = false; }
    else        { stop_pos_Y = cible; stop_arme_Y = true; atteint_Y = false; }
  }
  axe[a].mode = MODE_MOVE;
}

// Tâche à 1 kHz : rampes, profils trapèze, prise d'origine, chien de garde.
static void tache_1khz() {
  if (chien_ms && axes_actifs() && (uint32_t)(millis() - derniere_ligne_ms) > chien_ms) {
    arreter_tout();
    alarmes |= AL_WATCHDOG;
  }
  for (uint8_t a = 0; a < 2; a++) gerer_axe(a);
}

static void gerer_axe(uint8_t a) {
  Axe &x = axe[a];
  switch (x.mode) {
    case MODE_SPEED:
      x.v = approcher(x.v, x.v_cible, dv_q15);
      if (x.v_cible == 0 && x.v == 0) { arreter_axe(a); return; }
      break;

    case MODE_MOVE: {
      bool atteint;
      ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        atteint = a ? atteint_Y : atteint_X;
        if (a) atteint_Y = false; else atteint_X = false;
      }
      if (atteint) { arreter_axe(a); return; }
      int32_t reste = x.cible - lire_pos(a);
      if (reste == 0) { arreter_axe(a); return; }
      bool vers_plus = reste > 0;
      if (x.v != 0 && ((x.v > 0) != vers_plus)) {
        x.v = approcher(x.v, 0, dv_q15);          // freine avant d'inverser
      } else {
        int32_t vabs = x.v >= 0 ? x.v : -x.v;
        uint32_t v_pas = ((uint32_t)(vabs >> 15) * 25000UL) >> 15;   // µpas/s
        uint32_t freinage = (v_pas * v_pas) / (2UL * accel);         // µpas
        uint32_t areste = reste > 0 ? (uint32_t)reste : (uint32_t)(-reste);
        int32_t v_min = Q15(V_MIN_UNITS) < vmax_q15 ? Q15(V_MIN_UNITS) : vmax_q15;
        if (areste <= freinage + 1) {
          vabs -= dv_q15;
          if (vabs < v_min) vabs = v_min;          // on finit doucement ; l'ISR arrête pile
        } else {
          vabs += dv_q15;
          if (vabs > vmax_q15) vabs = vmax_q15;
        }
        x.v = vers_plus ? vabs : -vabs;
      }
      break;
    }

    case MODE_HOME:
      if (x.phase == HOME_SEEK) {
        if (fc_min(a)) {
          x.v = 0;
          x.phase = HOME_BACKOFF;
        } else {
          x.v = approcher(x.v, -Q15(x.vitesse_home), dv_q15);
        }
      }
      if (x.phase == HOME_BACKOFF) {
        if (!fc_min(a)) {                         // contact relâché : origine
          arreter_axe(a);
          ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { if (a) pos_Y = 0; else pos_X = 0; }
          x.origine = true;
          return;
        }
        uint16_t lent = x.vitesse_home / 4;
        x.v = Q15(lent ? lent : 1);
      }
      appliquer_vitesse(a, x.v, false);
      return;

    default:                                      // IDLE, LEGACY : rien à faire
      return;
  }

  // Fin de course dans le sens du mouvement (hors prise d'origine) : arrêt + alarme
  if ((x.v > 0 && fc_max(a)) || (x.v < 0 && fc_min(a))) {
    arreter_axe(a);
    alarmes |= a ? AL_LIMIT_Y : AL_LIMIT_X;
    return;
  }
  appliquer_vitesse(a, x.v, x.mode == MODE_MOVE);
}

// ================================================================ analyse

// Lit un entier signé ; renvoie false si aucun chiffre. *deborde si hors int32.
static bool lire_entier(char **p, int32_t *val, bool *deborde) {
  char *s = *p;
  bool neg = false;
  if (*s == '-') { neg = true; s++; }
  if (*s < '0' || *s > '9') return false;
  uint32_t v = 0;
  while (*s >= '0' && *s <= '9') {
    uint8_t d = *s - '0';
    if (v > (2147483648UL - d) / 10) *deborde = true;
    else v = v * 10 + d;
    s++;
  }
  if (!neg && v > 2147483647UL) *deborde = true;
  *val = neg ? -(int32_t)(v - 1) - 1 : (int32_t)v;
  *p = s;
  return true;
}

static bool seulement(const char *permis) {
  uint32_t ok = 0;
  for (const char *c = permis; *c; c++) ok |= 1UL << (*c - 'A');
  return (pmasque & ~ok) == 0;
}

static void lignes_legacy(char *s) {
  if (alarmes & AL_BLOCKING) return;              // précision v2 n° 5
  if (prise_origine_en_cours()) return;
  while (*s) {
    while (*s == ' ') s++;
    if (*s != 'X' && *s != 'Y') {                 // mot ignoré (comme en v1)
      while (*s && *s != ' ') s++;
      continue;
    }
    uint8_t a = (*s == 'Y');
    s++;
    bool neg = false;
    if (*s == '-') { neg = true; s++; }
    uint32_t v = 0;
    while (*s >= '0' && *s <= '9') { v = v * 10 + (*s - '0'); v &= 0xFFFFFUL; s++; }
    v &= 0xFFFF;                                  // v1 : troncature uint16
    if (*s && *s != ' ') { while (*s && *s != ' ') s++; continue; }
    vitesse_legacy(a, neg, v);
  }
}

static void traiter_ligne(char *s, bool trop_long) {
  while (*s == ' ') s++;
  if (trop_long) { repondre_err(0, ERR_MALFORMED); return; }
  if (*s == 0) return;
  if (*s == 'X' || *s == 'Y') {
    derniere_ligne_ms = millis();
    lignes_legacy(s);
    return;
  }
  if (*s != 'M') { repondre_err(0, ERR_MALFORMED); return; }
  s++;
  int32_t code;
  bool deborde = false;
  if (*s == '-' || !lire_entier(&s, &code, &deborde) || deborde || code < 0 || code > 9999 || (*s && *s != ' ')) {
    repondre_err(0, ERR_MALFORMED);
    return;
  }
  pmasque = 0;
  deborde = false;
  while (*s) {
    while (*s == ' ') s++;
    if (!*s) break;
    char lettre = *s++;
    int32_t v;
    if (lettre < 'A' || lettre > 'Z' || !lire_entier(&s, &v, &deborde) || (*s && *s != ' ')) {
      repondre_err(code, ERR_MALFORMED);
      return;
    }
    PV(lettre) = v;
    pmasque |= 1UL << (lettre - 'A');
  }
  derniere_ligne_ms = millis();
  if (deborde) { repondre_err(code, ERR_PARAM); return; }
  executer((uint16_t)code);
}

// ============================================================== commandes

static uint8_t garde_mouvement() {
  if (!mode_manuel) return ERR_MANUAL_ONLY;
  if (alarmes & AL_BLOCKING) return ERR_ALARM;
  if (prise_origine_en_cours()) return ERR_HOMING;
  return 0;
}

static void executer(uint16_t code) {
  uint8_t err;
  switch (code) {
    // ---------------------------------------------------------- v1 (binaire)
    case 100: {
      uint16_t v;
      ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { v = _V_autorise; }
      tx_put(v & 0xFF);
      tx_put(v >> 8);
      return;
    }
    case 101: {
      uint8_t e = 0;
      if (endstop_X_min) e |= 1;
      if (endstop_X_max) e |= 2;
      if (endstop_Y_min) e |= 4;
      if (endstop_Y_max) e |= 8;
      tx_put(e);
      return;
    }
    case 102:
      tx_put((uint8_t)flag_autorisation_);
      return;

    // ------------------------------------------------------------------ v2
    case 110:                                     // arrêt immédiat
      arreter_tout();
      repondre_debut(110);
      tx_put('\n');
      return;

    case 111: {                                   // état
      int32_t px, py, vx, vy;
      uint32_t va;
      ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
        px = pos_X; py = pos_Y; va = fenetre_us;
        vx = actif_X ? ((PORTF & (1 << X_DIR)) ? (int32_t)vitesse_X : -(int32_t)vitesse_X) : 0;
        vy = actif_Y ? ((PORTF & (1 << Y_DIR)) ? (int32_t)vitesse_Y : -(int32_t)vitesse_Y) : 0;
      }
      uint8_t es = (endstop_X_min ? 1 : 0) | (endstop_X_max ? 2 : 0) | (endstop_Y_min ? 4 : 0) | (endstop_Y_max ? 8 : 0);
      repondre_debut(111);
      tx_str(" t="); tx_u32(millis());
      tx_champ("x", px);
      tx_champ("y", py);
      tx_champ("vx", vx);
      tx_champ("vy", vy);
      tx_champ("es", es);
      tx_champ("win", flag_autorisation_ ? 1 : 0);
      tx_champ("mode", mode_manuel ? 1 : 0);
      tx_champ("home", (axe[0].origine ? 1 : 0) | (axe[1].origine ? 2 : 0));
      tx_champ("mv", (axe[0].mode != MODE_IDLE ? 1 : 0) | (axe[1].mode != MODE_IDLE ? 2 : 0));
      tx_champ("al", alarmes);
      tx_str(" va="); tx_u32(va);
      tx_put('\n');
      return;
    }

    case 112:                                     // mode
      if (!seulement("S") || !A_PARAM('S') || (PV('S') != 0 && PV('S') != 1)) { repondre_err(112, ERR_PARAM); return; }
      if (!PV('S')) {
        // Les mouvements v2 sont réservés au mode manuel : on les arrête en repassant en broderie.
        for (uint8_t a = 0; a < 2; a++) {
          if (axe[a].mode == MODE_SPEED || axe[a].mode == MODE_MOVE || axe[a].mode == MODE_HOME) arreter_axe(a);
        }
      }
      mode_manuel = PV('S');
      repondre_debut(112);
      tx_param('S', PV('S'));
      tx_put('\n');
      return;

    case 113:                                     // chien de garde
      if (!seulement("T") || !A_PARAM('T') ||
          !(PV('T') == 0 || (PV('T') >= WATCHDOG_MIN_MS && PV('T') <= WATCHDOG_MAX_MS))) {
        repondre_err(113, ERR_PARAM);
        return;
      }
      chien_ms = PV('T');
      repondre_debut(113);
      tx_param('T', chien_ms);
      tx_put('\n');
      return;

    case 114:                                     // acquittement
      ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { alarmes = 0; }
      repondre_debut(114);
      tx_put('\n');
      return;

    case 120: {                                   // vitesse avec rampe
      if ((err = garde_mouvement())) { repondre_err(120, err); return; }
      if (!pmasque || !seulement("XY") ||
          (A_PARAM('X') && (PV('X') < -SPEED_MAX || PV('X') > SPEED_MAX)) ||
          (A_PARAM('Y') && (PV('Y') < -SPEED_MAX || PV('Y') > SPEED_MAX))) {
        repondre_err(120, ERR_PARAM);
        return;
      }
      for (uint8_t a = 0; a < 2; a++) {
        char l = a ? 'Y' : 'X';
        if (!A_PARAM(l)) continue;
        if (axe[a].mode == MODE_MOVE) {           // remplace un déplacement compté
          ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { if (a) stop_arme_Y = false; else stop_arme_X = false; }
        }
        axe[a].v_cible = Q15(PV(l));
        if (PV(l) != 0 || axe[a].v != 0) axe[a].mode = MODE_SPEED;
        else arreter_axe(a);
      }
      repondre_debut(120);
      tx_param('X', axe[0].mode == MODE_SPEED ? (axe[0].v_cible >> 15) : 0);
      tx_param('Y', axe[1].mode == MODE_SPEED ? (axe[1].v_cible >> 15) : 0);
      tx_put('\n');
      return;
    }

    case 121:                                     // accélération, vitesse max
      if (!pmasque || !seulement("AV") ||
          (A_PARAM('A') && (PV('A') < 1 || (uint32_t)PV('A') > ACCEL_MAX)) ||
          (A_PARAM('V') && (PV('V') < 1 || PV('V') > SPEED_MAX))) {
        repondre_err(121, ERR_PARAM);
        return;
      }
      if (A_PARAM('A')) regler_accel(PV('A'));
      if (A_PARAM('V')) vmax_q15 = Q15(PV('V'));
      repondre_debut(121);
      tx_param('A', accel);
      tx_param('V', vmax_q15 >> 15);
      tx_put('\n');
      return;

    case 122:                                     // déplacement relatif
    case 123: {                                   // déplacement absolu
      if ((err = garde_mouvement())) { repondre_err(code, err); return; }
      if (!pmasque || !seulement("XY")) { repondre_err(code, ERR_PARAM); return; }
      if (code == 123 && ((A_PARAM('X') && !axe[0].origine) || (A_PARAM('Y') && !axe[1].origine))) {
        repondre_err(123, ERR_NOT_HOMED);
        return;
      }
      for (uint8_t a = 0; a < 2; a++) {
        char l = a ? 'Y' : 'X';
        if (!A_PARAM(l)) continue;
        int32_t cible = PV(l);
        if (code == 122) {
          int64_t c = (int64_t)lire_pos(a) + PV(l);
          if (c > 2147483647LL) c = 2147483647LL;
          if (c < -2147483647LL - 1) c = -2147483647LL - 1;
          cible = (int32_t)c;
        }
        armer_deplacement(a, cible);
      }
      repondre_debut(code);
      if (A_PARAM('X')) tx_param('X', PV('X'));
      if (A_PARAM('Y')) tx_param('Y', PV('Y'));
      tx_put('\n');
      return;
    }

    case 130: {                                   // prise d'origine
      if ((err = garde_mouvement())) { repondre_err(130, err); return; }
      int32_t hx = A_PARAM('X') ? PV('X') : 0;
      int32_t hy = A_PARAM('Y') ? PV('Y') : 0;
      int32_t f = A_PARAM('F') ? PV('F') : DEFAULT_HOME_SPEED;
      if (!seulement("XYF") || (hx != 0 && hx != 1) || (hy != 0 && hy != 1) || !(hx || hy) ||
          f < 1 || f > SPEED_MAX) {
        repondre_err(130, ERR_PARAM);
        return;
      }
      for (uint8_t a = 0; a < 2; a++) {
        if (!(a ? hy : hx)) continue;
        if (axe[a].mode == MODE_MOVE) {
          ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { if (a) stop_arme_Y = false; else stop_arme_X = false; }
        }
        axe[a].mode = MODE_HOME;
        axe[a].phase = HOME_SEEK;
        axe[a].vitesse_home = f;
        axe[a].origine = false;
      }
      repondre_debut(130);
      tx_param('X', hx);
      tx_param('Y', hy);
      tx_param('F', f);
      tx_put('\n');
      return;
    }

    default:
      repondre_err(code, ERR_UNKNOWN);
      return;
  }
}
