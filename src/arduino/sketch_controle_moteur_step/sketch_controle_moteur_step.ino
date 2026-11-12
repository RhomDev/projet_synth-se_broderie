// Broches de contrôle pour l'axe X (Carte MKS Base V1.4)
const int X_STEP_PIN = 54;
const int X_DIR_PIN  = 55;
const int X_ENABLE_PIN = 38;

// Broches de contrôle pour l'axe Y (Carte MKS Base V1.4)
const int Y_STEP_PIN = 60;
const int Y_DIR_PIN  = 61;
const int Y_ENABLE_PIN = 56;

// Vitesse de déplacement (pause en microsecondes entre chaque pas)
const int VITESSE_DELAI = 500; 

void setup() {
  // Initialisation de la console série à 115200 bauds
  Serial.begin(115200);

  // Configuration des broches X en sortie
  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_ENABLE_PIN, OUTPUT);

  // Configuration des broches Y en sortie
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_ENABLE_PIN, OUTPUT);

  // Activation des drivers (LOW = Activé sur les cartes MKS)
  digitalWrite(X_ENABLE_PIN, LOW);
  digitalWrite(Y_ENABLE_PIN, LOW);

  Serial.println("Systeme pret. Entrez une commande (ex: X200 ou Y-50) :");
}

void loop() {
  // Vérifie si une commande est disponible dans la console
  if (Serial.available() > 0) {
    char axe = Serial.read(); // Lit la première lettre (X ou Y)
    
    // Si la lettre est X (majuscule ou minuscule)
    if (axe == 'X' || axe == 'x') {
      long nombreDePas = Serial.parseInt(); // Lit le nombre qui suit
      Serial.print("Deplacement axe X de ");
      Serial.print(nombreDePas);
      Serial.println(" pas.");
      bougerMoteur(X_STEP_PIN, X_DIR_PIN, nombreDePas);
    } 
    // Si la lettre est Y (majuscule ou minuscule)
    else if (axe == 'Y' || axe == 'y') {
      long nombreDePas = Serial.parseInt(); // Lit le nombre qui suit
      Serial.print("Deplacement axe Y de ");
      Serial.print(nombreDePas);
      Serial.println(" pas.");
      bougerMoteur(Y_STEP_PIN, Y_DIR_PIN, nombreDePas);
    }
    
    // Nettoie le reste du buffer série (comme les retours à la ligne)
    while (Serial.available() > 0) {
      Serial.read();
    }
    Serial.println("Mouvement termine. En attente...");
  }
}

// Fonction générique pour piloter le mouvement des moteurs
void bougerMoteur(int pinStep, int pinDir, long pas) {
  // Détermination du sens de rotation
  if (pas > 0) {
    digitalWrite(pinDir, HIGH);
  } else {
    digitalWrite(pinDir, LOW);
    pas = -pas; // Convertit en valeur positive pour la boucle
  }

  // Génération des impulsions (signaux PWM logiciels) pour avancer
  for (long i = 0; i < pas; i++) {
    digitalWrite(pinStep, HIGH);
    delayMicroseconds(VITESSE_DELAI);
    digitalWrite(pinStep, LOW);
    delayMicroseconds(VITESSE_DELAI);
  }
}