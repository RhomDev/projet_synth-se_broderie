#include "lib_control.h"

StepperDriver::StepperDriver(volatile uint8_t* portStep, volatile uint8_t* ddrStep, uint8_t bitStep,
                              volatile uint8_t* portDir,  volatile uint8_t* ddrDir,  uint8_t bitDir,
                              uint16_t stepsPerRev)
    : _portStep(portStep),
      _ddrStep(ddrStep),
      _maskStep(1 << bitStep),
      _portDir(portDir),
      _ddrDir(ddrDir),
      _maskDir(1 << bitDir),
      _stepsPerRev(stepsPerRev),
      _stepDelayUs(1000)
{
}

void StepperDriver::begin() {
    // Activer les broches en sortie dans le Data Direction Register (DDR)
    *_ddrStep |= _maskStep;
    *_ddrDir  |= _maskDir;

    // Mettre les broches à l'état BAS par défaut
    *_portStep &= ~_maskStep;
    *_portDir  &= ~_maskDir;
}

void StepperDriver::setSpeed(uint16_t rpm) {
    if (rpm == 0 || _stepsPerRev == 0) return;
    
    // (60s * 1 000 000 µs) / (RPM * pas_par_tour)
    _stepDelayUs = 60000000UL / ((uint32_t)rpm * _stepsPerRev);
}

inline void StepperDriver::setDirection(bool clockwise) {
    if (clockwise) {
        *_portDir |= _maskDir;  // DIR = HIGH
    } else {
        *_portDir &= ~_maskDir; // DIR = LOW
    }
}

inline void StepperDriver::pulseStep() {
    *_portStep |= _maskStep;   // STEP = HIGH
    
    // Délai minimal d'impulsion pour le driver (~1 à 2 µs)
    asm volatile("nop\n\tnop\n\tnop\n\tnop\n\t"); 
    
    *_portStep &= ~_maskStep;  // STEP = LOW
}

void StepperDriver::delayUs(uint32_t us) {
    // Boucle d'attente minimale en bare-metal
    while (us--) {
        _delay_us(1);
    }
}

void StepperDriver::step(int32_t steps) {
    if (steps == 0) return;

    setDirection(steps > 0);

    uint32_t absSteps = (steps < 0) ? -steps : steps;

    for (uint32_t i = 0; i < absSteps; i++) {
        pulseStep();
        delayUs(_stepDelayUs);
    }
}

void StepperDriver::rotateDegrees(float degrees) {
    int32_t steps = (int32_t)((degrees * (float)_stepsPerRev) / 360.0f);
    step(steps);
}