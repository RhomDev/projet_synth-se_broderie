"""Supervision des capteurs et de l'état de la carte.

Couleurs : vert = actif / normal, gris = inactif, rouge = défaut, orange = avertissement.
Une donnée trop ancienne s'affiche « inconnu » (voyant en pointillés) et n'est
jamais présentée comme une mesure actuelle.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QVBoxLayout

from communication.link import LinkState
from communication.protocol import Alarm, BLOCKING_ALARMS
from machine.state import MachineModel

from .widgets import IndicatorTile, panel, section_title


class SensorsPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        panel(self)
        self.link = IndicatorTile("Liaison carte", "Liaison série avec la carte MKS Base")
        self.mode = IndicatorTile("Mode de la carte", "M112 : manuel = pas à tout moment ; broderie = fenêtre aiguille")
        self.x_min = IndicatorTile("Fin de course X− (Xmin)", "D3 (PE5), contact NO, origine X")
        self.x_max = IndicatorTile("Fin de course X+ (Xmax)", "D2 (PE4), contact NO")
        self.y_min = IndicatorTile("Fin de course Y− (Ymin)", "D14 (PJ1), contact NO, origine Y")
        self.y_max = IndicatorTile("Fin de course Y+ (Ymax)", "D15 (PJ0), contact NO")
        self.window = IndicatorTile("Fenêtre aiguille", "2 × TCST2300 sur D53 (ouverture) et D51 (fermeture)")
        self.origin = IndicatorTile("Origine machine", "Prise d'origine sur Xmin et Ymin")
        self.watchdog = IndicatorTile("Chien de garde", "Arrêt des axes par la carte si le PC se tait")
        self.alarms = IndicatorTile("Alarmes", "Bits « al » de la ligne d'état M111")
        self.ac_motor = IndicatorTile("Moteur AC", "Module de pilotage AC pas encore disponible")

        grid = QGridLayout()
        grid.setSpacing(6)
        tiles = [self.link, self.mode, self.x_min, self.x_max, self.y_min, self.y_max,
                 self.window, self.origin, self.watchdog, self.alarms, self.ac_motor]
        for i, tile in enumerate(tiles):
            grid.addWidget(tile, i // 2, i % 2)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(10)
        lay.addWidget(section_title("Capteurs et état"))
        lay.addLayout(grid)
        self.ac_motor.set_state("inactive", "non disponible", "module AC à venir (étape 5)")

    def refresh(self, model: MachineModel, watchdog_enabled: bool) -> None:
        link = model.link_state
        sim = " — SIMULATION" if model.simulation else ""
        if link is LinkState.CONNECTED:
            self.link.set_state("ok", "connectée" + sim)
        elif link is LinkState.CONNECTING:
            self.link.set_state("warning", "connexion…" + sim)
        elif link is LinkState.LOST:
            self.link.set_state("error", "perdue", "aucune réponse de la carte")
        else:
            self.link.set_state("inactive", "déconnectée")

        if model.protocol == 1 and link is not LinkState.DISCONNECTED:
            self._refresh_v1(model)
            return
        st = model.status
        if st is None or link is LinkState.DISCONNECTED:
            for tile in (self.mode, self.x_min, self.x_max, self.y_min, self.y_max,
                         self.window, self.origin, self.alarms):
                tile.set_state("inactive", "—", unknown=True)
            self.watchdog.set_state("inactive", "—", unknown=True)
            return
        if not model.fresh:
            for tile in (self.mode, self.x_min, self.x_max, self.y_min, self.y_max,
                         self.window, self.origin, self.alarms):
                tile.set_state("warning", "inconnu", "données trop anciennes", unknown=True)
            self.watchdog.set_state("warning", "inconnu", unknown=True)
            return

        self.mode.set_state("ok" if st.manual_mode else "warning",
                            "manuel" if st.manual_mode else "broderie",
                            "" if st.manual_mode else "pas émis seulement fenêtre ouverte")
        es = st.endstops
        for tile, pressed, limit_flag in (
            (self.x_min, es.x_min, Alarm.LIMIT_X), (self.x_max, es.x_max, Alarm.LIMIT_X),
            (self.y_min, es.y_min, Alarm.LIMIT_Y), (self.y_max, es.y_max, Alarm.LIMIT_Y),
        ):
            if pressed and st.alarms & limit_flag:
                tile.set_state("error", "appuyé", "touché pendant un mouvement")
            elif pressed:
                tile.set_state("ok", "appuyé")
            else:
                tile.set_state("inactive", "libre")

        if st.window_us:
            detail = f"dernière fenêtre : {st.window_us / 1000:.1f} ms"
        else:
            detail = "aucune fenêtre mesurée depuis le démarrage"
        self.window.set_state("ok" if st.window_open else "inactive",
                              "ouverte (aiguille hors tissu)" if st.window_open else "fermée", detail)

        if st.homed:
            self.origin.set_state("ok", "faite")
        elif st.homed_x or st.homed_y:
            self.origin.set_state("warning", f"{'X' if st.homed_x else 'Y'} seulement")
        else:
            self.origin.set_state("warning", "non faite", "position non référencée")

        if st.alarms & Alarm.WATCHDOG:
            self.watchdog.set_state("error", "déclenché", "axes arrêtés par la carte")
        elif model.watchdog_ms:
            self.watchdog.set_state("ok", f"actif ({model.watchdog_ms} ms)")
        elif watchdog_enabled:
            self.watchdog.set_state("warning", "non confirmé", "réglage en cours d'envoi")
        else:
            self.watchdog.set_state("warning", "désactivé", "aucun arrêt si le PC plante")

        self._alarms(st)

    def _refresh_v1(self, model: MachineModel) -> None:
        """Firmware v1 : fins de course (M101), fenêtre (M102, M100), rien d'autre."""
        st = model.v1_status
        tiles = (self.x_min, self.x_max, self.y_min, self.y_max, self.window)
        if st is None or not model.fresh:
            for tile in tiles:
                tile.set_state("warning", "inconnu", "données trop anciennes", unknown=True)
        else:
            es = st.endstops
            for tile, pressed in ((self.x_min, es.x_min), (self.x_max, es.x_max),
                                  (self.y_min, es.y_min), (self.y_max, es.y_max)):
                tile.set_state("ok" if pressed else "inactive", "appuyé" if pressed else "libre")
            detail = (f"M100 : {st.window_v1} µs (16 bits ; 70 = valeur de démarrage, pas une mesure)"
                      if st.window_v1 is not None else "M100 non lu")
            self.window.set_state("ok" if st.window_open else "inactive",
                                  "ouverte (aiguille hors tissu)" if st.window_open else "fermée", detail)
        self.mode.set_state("warning", "firmware v1", "pas émis seulement fenêtre ouverte")
        self.origin.set_state("inactive", "non disponible", "pas de compteur de position en v1", unknown=True)
        self.watchdog.set_state("warning", "absent", "le firmware v1 n'en a pas")
        self.alarms.set_state("inactive", "non disponible", "pas d'alarmes en v1", unknown=True)

    def _alarms(self, st) -> None:
        blocking = st.alarms & BLOCKING_ALARMS
        if blocking:
            self.alarms.set_state("error", "bloquante", "acquittement nécessaire")
        elif st.alarms:
            self.alarms.set_state("warning", "information", "fin de course touchée en mouvement")
        else:
            self.alarms.set_state("inactive", "aucune")
