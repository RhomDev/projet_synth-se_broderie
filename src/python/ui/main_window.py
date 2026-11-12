"""Fenêtre principale : bandeau d'état permanent, plateau, pilotage, capteurs, journal."""
from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFontMetrics, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from communication.link import LinkState, MachineLink
from communication.ports import find_board_ports
from communication.protocol import ALARM_TEXT, BLOCKING_ALARMS
from communication.serial_transport import SerialTransport
from communication.simulator import SimulatedMachine
from machine.config import AppConfig, save_config
from machine.line_test import LineTest
from machine.motion import MotionController
from machine.safety import can_home, can_move, check_target, speed_cap
from machine.state import MachineModel, MachineState

from . import theme
from .jog_panel import JogPanel
from .line_panel import LinePanel
from .log_panel import LogPanel
from .plate_view import PlateView
from .sensors_panel import SensorsPanel
from .settings_dialog import SettingsDialog
from .widgets import Led, panel

APP_TITLE = "Brodeuse — Pilotage"
ui_log = logging.getLogger("brodeuse.ui")


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.config = config
        self.model = MachineModel(config.link.stale_after_s, self)
        self.controller = MotionController(self.model, config, self)
        self.line_test = LineTest(self.controller, self.model, self)
        self.link: MachineLink | None = None
        self.sim: SimulatedMachine | None = None

        self._build_ui()
        self._build_menus()
        self._wire()
        self._apply_config_to_ui()

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self.model.tick)
        self._ticker.start(100)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.stop,
                  context=Qt.ShortcutContext.ApplicationShortcut)
        QGuiApplication.instance().applicationStateChanged.connect(self._app_state_changed)
        self._refresh()

    # ------------------------------------------------------------- construction

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        self.sim_banner = QLabel(
            "SIMULATION — aucune machine réelle n'est pilotée. Positions, capteurs et réponses sont simulés : "
            "ce ne sont pas des mesures.")
        self.sim_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sim_banner.setStyleSheet(
            f"background: {theme.WARNING}; color: #1a1205; font-weight: 700; border-radius: 6px; padding: 6px;")
        self.sim_banner.hide()
        root.addWidget(self.sim_banner)
        root.addWidget(self._build_top_bar())

        self.alarm_banner = QFrame()
        self.alarm_banner.setStyleSheet(
            f"QFrame {{ background: #3a1517; border: 1px solid {theme.ERROR}; border-radius: 6px; }}"
            "QLabel { background: transparent; color: #ffd0d1; font-weight: 600; }")
        self.alarm_text = QLabel()
        self.alarm_text.setWordWrap(True)
        self.alarm_button = QPushButton()
        self.alarm_button.clicked.connect(self._alarm_action)
        bl = QHBoxLayout(self.alarm_banner)
        bl.setContentsMargins(12, 8, 12, 8)
        bl.addWidget(self.alarm_text, 1)
        bl.addWidget(self.alarm_button)
        self.alarm_banner.hide()
        root.addWidget(self.alarm_banner)

        body = QHBoxLayout()
        body.setSpacing(10)
        plate_frame = panel(QFrame())
        pl = QVBoxLayout(plate_frame)
        pl.setContentsMargins(1, 1, 1, 1)
        self.plate = PlateView()
        pl.addWidget(self.plate)
        body.addWidget(plate_frame, 1)

        side = QWidget()
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 0, 4, 0)
        sl.setSpacing(10)
        self.jog = JogPanel(self.config.manual.increments_mm)
        self.line_panel = LinePanel(self.config)
        self.sensors = SensorsPanel()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.jog, "Pilotage manuel")
        self.tabs.addTab(self.line_panel, "Ligne de test")
        sl.addWidget(self.tabs)
        sl.addWidget(self.sensors)
        sl.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidget(side)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(430)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body.addWidget(scroll)
        root.addLayout(body, 1)
        self.setCentralWidget(central)

        self.log = LogPanel()
        self.log_dock = QDockWidget("Journal des échanges", self)
        self.log_dock.setObjectName("journal")
        self.log_dock.setWidget(self.log)
        self.log_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        self.resizeDocks([self.log_dock], [170], Qt.Orientation.Vertical)

        self.command_label = QLabel("Aucune commande envoyée")
        self.command_label.setFont(theme.mono_font(9))
        self.statusBar().addPermanentWidget(self.command_label)

    def _build_top_bar(self) -> QFrame:
        bar = panel(QFrame())
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(16)

        self.state_led = Led(18)
        self.state_label = QLabel()
        self.state_label.setStyleSheet("font-size: 15pt; font-weight: 700;")
        self.state_sub = QLabel()
        self.state_sub.setProperty("role", "dim")
        state_text = QVBoxLayout()
        state_text.setSpacing(0)
        state_text.addWidget(self.state_label)
        state_text.addWidget(self.state_sub)
        lay.addWidget(self.state_led)
        lay.addLayout(state_text)
        lay.addStretch(1)

        coords = QHBoxLayout()
        coords.setSpacing(18)
        self.coord_labels = {}
        for axis in ("X", "Y"):
            name = QLabel(axis)
            name.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 13pt; font-weight: 700;")
            value = QLabel("—")
            font = theme.mono_font(22, bold=True)
            value.setFont(font)
            value.setMinimumWidth(QFontMetrics(font).horizontalAdvance("-0000.000") + 6)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            box = QHBoxLayout()
            box.setSpacing(8)
            box.addWidget(name)
            box.addWidget(value)
            coords.addLayout(box)
            self.coord_labels[axis] = value
        unit = QLabel("mm")
        unit.setProperty("role", "dim")
        coords.addWidget(unit)
        coord_col = QVBoxLayout()
        coord_col.setSpacing(0)
        coord_col.addLayout(coords)
        self.coord_ref = QLabel()
        self.coord_ref.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.coord_ref.setStyleSheet("font-size: 8.5pt;")
        coord_col.addWidget(self.coord_ref)
        lay.addLayout(coord_col)
        lay.addStretch(1)

        self.connect_button = QPushButton()
        self.connect_button.setProperty("role", "primary")
        self.connect_button.setMinimumHeight(44)
        self.connect_button.clicked.connect(self._toggle_connection)
        lay.addWidget(self.connect_button)

        self.estop_button = QPushButton("ARRÊT")
        self.estop_button.setProperty("role", "estop")
        self.estop_button.setMinimumSize(150, 56)
        self.estop_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.estop_button.setToolTip(
            "Arrêt logiciel immédiat des axes (touche Échap).\n"
            "Ne remplace PAS un arrêt d'urgence matériel câblé, indépendant du PC.")
        self.estop_button.clicked.connect(self.stop)
        estop_col = QVBoxLayout()
        estop_col.setSpacing(2)
        estop_col.addWidget(self.estop_button)
        caption = QLabel("arrêt logiciel · Échap")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 8pt;")
        estop_col.addWidget(caption)
        lay.addLayout(estop_col)
        return bar

    def _build_menus(self) -> None:
        mb = self.menuBar()
        machine = mb.addMenu("&Machine")
        machine.setToolTipsVisible(True)
        self.connect_menu = QMenu("Connecter", self)
        self.connect_menu.setToolTipsVisible(True)
        self.connect_menu.aboutToShow.connect(self._fill_connect_menu)
        machine.addMenu(self.connect_menu)
        self.act_connect_sim = QAction("Simulation (firmware v2 proposé)", self)
        self.act_connect_sim.triggered.connect(self.connect_simulation)
        self.act_connect_sim_v1 = QAction("Simulation (firmware v1 actuel)", self)
        self.act_connect_sim_v1.triggered.connect(lambda: self.connect_simulation(firmware_version=1))
        self.act_disconnect = QAction("Déconnecter", self)
        self.act_disconnect.triggered.connect(self.disconnect_link)
        self.act_home = QAction("Prise d'origine…", self)
        self.act_home.triggered.connect(self._confirm_home)
        self.act_calib = QAction("Mesurer les courses…", self)
        self.act_calib.triggered.connect(self._confirm_calibration)
        self.act_clear = QAction("Acquitter les alarmes…", self)
        self.act_clear.triggered.connect(self._confirm_clear_alarms)
        settings = QAction("Paramètres…", self)
        settings.setShortcut(QKeySequence("Ctrl+,"))
        settings.triggered.connect(self._open_settings)
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        for item in (self.act_disconnect, None, self.act_home, self.act_calib, self.act_clear, None,
                     settings, None, quit_action):
            machine.addSeparator() if item is None else machine.addAction(item)

        sim = mb.addMenu("&Simulation")
        sewing = sim.addMenu("Machine à coudre simulée")
        self.sewing_group = QActionGroup(self)
        for rpm in (0, 300, 600, 860):
            act = QAction("Arrêtée" if rpm == 0 else f"{rpm} tr/min", self, checkable=True)
            act.setData(rpm)
            act.setChecked(rpm == 0)
            act.triggered.connect(lambda _=False, r=rpm: self.sim and self.sim.set_sewing_rpm(r))
            self.sewing_group.addAction(act)
            sewing.addAction(act)
        self.act_window = QAction("Fenêtre aiguille ouverte (machine arrêtée)", self, checkable=True)
        self.act_window.toggled.connect(lambda on: self.sim and self.sim.set_window_open(on))
        self.act_cut = QAction("Couper la liaison", self, checkable=True)
        self.act_cut.toggled.connect(self._cut_link)
        self.act_reboot = QAction("Redémarrer la carte simulée", self)
        self.act_reboot.triggered.connect(lambda: self.sim and self.sim.reboot())
        for a in (self.act_window, self.act_cut, self.act_reboot):
            sim.addAction(a)
        self.sim_menu = sim

        view = mb.addMenu("&Affichage")
        fit = QAction("Recadrer le plateau", self)
        fit.triggered.connect(self.plate.fit)
        view.addAction(fit)
        view.addAction(self.log_dock.toggleViewAction())

        help_menu = mb.addMenu("&Aide")
        about = QAction("À propos", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    def _wire(self) -> None:
        c = self.controller
        self.jog.jog_pressed.connect(c.jog_start)
        self.jog.jog_released.connect(c.jog_stop)
        self.jog.step_requested.connect(c.step)
        self.jog.stop_requested.connect(self.stop)
        self.jog.goto_requested.connect(self._confirm_goto)
        self.jog.home_requested.connect(self._confirm_home)
        self.jog.calibrate_requested.connect(self._confirm_calibration)
        self.jog.speed_changed.connect(self._speed_changed)
        self.jog.accel_changed.connect(self._accel_changed)
        self.plate.target_clicked.connect(self._plate_clicked)
        self.plate.target_confirmed.connect(self._plate_confirmed)
        self.model.changed.connect(self._refresh)
        self.model.alarm_raised.connect(self._alarm_raised)
        c.message.connect(self._message)
        c.command_status.connect(lambda cmd, status: self.command_label.setText(f"{cmd}  —  {status}"))
        c.calibration_changed.connect(self.jog.set_progress)
        c.config_changed.connect(self._apply_config_to_ui)
        lt = self.line_test
        self.line_panel.arm_requested.connect(self._confirm_line)
        self.line_panel.stop_requested.connect(self.stop)
        self.line_panel.preview_changed.connect(self.plate.set_line_preview)
        lt.progress.connect(self.line_panel.set_progress)
        lt.finished.connect(self._line_finished)
        lt.running_changed.connect(self.line_panel.set_running)
        lt.trace_point.connect(self.plate.trace_add)

    # ---------------------------------------------------------------- liaison

    def _fill_connect_menu(self) -> None:
        menu = self.connect_menu
        menu.clear()
        ports = find_board_ports()
        if ports:
            for port in ports:
                act = menu.addAction(f"Carte réelle : {port}")
                act.setToolTip("Ouvrir le port redémarre la carte (DTR)")
                act.triggered.connect(lambda _=False, dev=port.device: self.connect_board(dev))
        else:
            act = menu.addAction("Aucune carte FT232R (0403:6001) détectée")
            act.setEnabled(False)
        menu.addSeparator()
        menu.addAction(self.act_connect_sim)
        menu.addAction(self.act_connect_sim_v1)
        for act in menu.actions():
            if self.link is not None:
                act.setEnabled(False)

    def connect_board(self, device: str) -> None:
        if self.link is not None:
            return
        if not self._confirm("Connecter la carte réelle",
                             f"Ouvrir {device} redémarre la carte (signal DTR) : les moteurs s'arrêtent, "
                             "l'origine est perdue et la carte met environ 2 s à démarrer.\n\nContinuer ?"):
            return
        self._start_link(SerialTransport(device), description=device)

    def connect_simulation(self, firmware_version: int = 2) -> None:
        if self.link is not None:
            return
        s = self.config.simulation
        self.sim = SimulatedMachine(tuple(s.travel_mm), tuple(s.start_mm), steps_per_mm=self.config.x.steps_per_mm,
                                    firmware_version=firmware_version)
        self._start_link(self.sim, description=f"SIMULATION v{firmware_version}")

    def _start_link(self, transport, description: str) -> None:
        lk = self.config.link
        link = MachineLink(transport, lk.poll_hz, lk.reply_timeout_s, lk.lost_after_timeouts, parent=self)
        link.status_received.connect(self.model.update_status)
        link.status_received.connect(self.controller.on_status)
        link.status_received.connect(self.line_test.on_status)
        link.v1_status_received.connect(self.model.update_v1_status)
        link.state_changed.connect(lambda state, lk_=link: self._link_state_changed(lk_, state))
        link.traffic.connect(self.log.add_traffic)
        link.finished.connect(self._link_finished)
        self.controller.attach(link)
        self.model.simulation = bool(getattr(transport, "is_simulation", False))
        self.model.port_description = description
        self.link = link
        self.act_window.setChecked(False)
        self.act_cut.setChecked(False)
        for act in self.sewing_group.actions():
            act.setChecked(act.data() == 0)
        self.plate.trace_clear()
        self.line_panel.set_progress("")
        link.start()
        self._refresh()

    def _link_state_changed(self, link: MachineLink, state: LinkState) -> None:
        self.model.set_link_state(state, link.protocol)
        if state is LinkState.LOST:
            self.line_test.abort("liaison perdue")

    def disconnect_link(self) -> None:
        if self.link is None:
            return
        self.controller.stop()
        self.link.shutdown()

    def _link_finished(self) -> None:
        link, self.link = self.link, None
        self.controller.detach()
        self.sim = None
        self.model.simulation = False
        self.model.set_link_state(LinkState.DISCONNECTED)
        if link is not None:
            link.deleteLater()
        self._refresh()

    def _toggle_connection(self) -> None:
        if self.link is None:
            self._fill_connect_menu()
            self.connect_menu.exec(self.connect_button.mapToGlobal(QPoint(0, self.connect_button.height())))
        else:
            self.disconnect_link()

    def _cut_link(self, on: bool) -> None:
        if self.sim is not None:
            self.sim.link_cut = on

    # ---------------------------------------------------------------- actions

    def stop(self) -> None:
        self.jog.release_all()
        if self.link is None:
            self.statusBar().showMessage("Aucune liaison : rien à arrêter", 4000)
            return
        self.controller.stop()
        self.line_test.notify_stopped()
        self.log.add_message("warning", "ARRÊT logiciel demandé")
        ui_log.warning("ARRÊT logiciel demandé")

    def _confirm_line(self, plan) -> None:
        if not self._confirm(
                "Armer la ligne de test",
                f"Ligne de {plan.length_mm:g} mm à {plan.angle_deg:g}°, points de {plan.stitch_mm:g} mm "
                f"(≈ {plan.stitches} points, cadre à {plan.speed_mm_s:.1f} mm/s pendant les fenêtres).\n\n"
                "La carte passe en mode broderie : le cadre n'avance que lorsque l'aiguille est hors du tissu. "
                "Lancez ensuite la machine à coudre à vitesse régulière.\n\n"
                "Le tissu est-il tendu dans le cadre et le cadre dégagé ?"):
            return
        self.plate.trace_clear()
        if self.line_test.start(plan):
            self.tabs.setCurrentWidget(self.line_panel)

    def _line_finished(self, level: str, text: str) -> None:
        self.line_panel.set_progress(text)
        self._message(level, text)

    def _speed_changed(self, value: float) -> None:
        self.controller.jog_speed_mm_s = value
        self._refresh()

    def _accel_changed(self, value: float) -> None:
        self.controller.jog_accel_mm_s2 = value

    def _plate_clicked(self, x: float, y: float) -> None:
        decision = can_move(self.model.state, self.model.status)
        if decision:
            decision = check_target(self.config, self.model.status, x, y)
        self.plate.show_target(x, y, decision.allowed, "" if decision else f"Impossible : {decision.reason}")

    def _plate_confirmed(self, x: float, y: float) -> None:
        if self.controller.go_to(x, y):
            self.plate.clear_target()

    def _confirm(self, title: str, text: str) -> bool:
        answer = QMessageBox.question(self, title, text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
        return answer == QMessageBox.StandardButton.Yes

    def _confirm_goto(self, x: float, y: float) -> None:
        decision = check_target(self.config, self.model.status, x, y)
        if not decision:
            self._message("warning", f"Mouvement refusé : {decision.reason}")
            return
        if self._confirm("Aller à une position", f"Déplacer le cadre vers X = {x:.2f} mm, Y = {y:.2f} mm ?"):
            self.controller.go_to(x, y)

    def _confirm_home(self) -> None:
        v = self.config.manual.home_speed_mm_s
        if self._confirm("Prise d'origine",
                         f"Les axes vont avancer vers Xmin et Ymin à {v:g} mm/s, puis reculer jusqu'au "
                         "relâchement des contacts.\n\nLe cadre est-il dégagé ?"):
            self.controller.home()

    def _confirm_calibration(self) -> None:
        v = self.config.manual.calibration_speed_mm_s
        if self._confirm("Mesurer les courses",
                         f"Chaque axe va avancer à {v:g} mm/s jusqu'à sa fin de course max (Xmax puis Ymax), "
                         "puis revenir près de l'origine.\n\nLes fins de course max sont-elles en place ?"):
            self.controller.start_calibration()

    def _confirm_clear_alarms(self) -> None:
        st = self.model.status
        causes = [t for flag, t in ALARM_TEXT.items() if st and st.alarms & flag] or ["aucune alarme active"]
        if self._confirm("Acquitter les alarmes",
                         "Alarmes : " + ", ".join(causes) + ".\n\nLa cause est-elle comprise et traitée ?"):
            self.controller.clear_alarms()

    def _alarm_action(self) -> None:
        if self.model.state is MachineState.ALARM:
            self._confirm_clear_alarms()
        else:
            self.disconnect_link()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() and dialog.result_config is not None:
            new = dialog.result_config
            try:
                path = save_config(new)
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Paramètres", f"Enregistrement impossible : {exc}")
                return
            self.config = new
            self.controller.apply_config(new)
            self._message("info", f"Paramètres enregistrés dans {path}")

    def _about(self) -> None:
        QMessageBox.about(
            self, "À propos",
            f"<b>{APP_TITLE}</b><br>Interface de pilotage de la brodeuse à patch.<br><br>"
            "Le bouton ARRÊT est un arrêt <b>logiciel</b>. Il ne remplace pas un arrêt d'urgence "
            "matériel câblé indépendamment du PC et du logiciel.")

    def _alarm_raised(self, text: str) -> None:
        if self.controller.calibrating and "fin de course" in text:
            self.log.add_message("info", f"{text} (attendu pendant la mesure des courses)")
            ui_log.info("Alarme attendue : %s", text)
        else:
            self.log.add_message("warning", f"Alarme : {text}")
            ui_log.warning("Alarme : %s", text)

    def _message(self, level: str, text: str) -> None:
        self.log.add_message(level, text)
        self.statusBar().showMessage(text, 6000)
        ui_log.log({"error": logging.ERROR, "warning": logging.WARNING}.get(level, logging.INFO), text)

    def _app_state_changed(self, state) -> None:
        if state != Qt.ApplicationState.ApplicationActive:
            self.jog.release_all()

    def changeEvent(self, event) -> None:
        if event.type() == event.Type.ActivationChange and not self.isActiveWindow():
            self.jog.release_all()
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        if self.link is not None:
            self.controller.stop()
            self.link.shutdown()
            if not self.link.wait(2000):
                self.link.abort()
                self.link.wait(1000)
        event.accept()

    # ------------------------------------------------------------- affichage

    def _apply_config_to_ui(self) -> None:
        cfg = self.config
        self.plate.set_geometry(cfg.x.travel_mm, cfg.y.travel_mm, cfg.limits.soft_margin_mm,
                                cfg.view.forbidden_zones, cfg.view.grid_step_mm, cfg.view.show_grid)
        self.jog.set_values(self.controller.jog_speed_mm_s, self.controller.jog_accel_mm_s2,
                            cfg.limits.speed_max_mm_s, cfg.limits.accel_max_mm_s2)
        self._refresh()

    def _refresh(self) -> None:
        m, cfg = self.model, self.config
        st, state = m.status, m.state
        fresh = m.fresh
        connected = self.link is not None

        self.state_led.set_level(state.level)
        self.state_label.setText(state.label)
        self.state_label.setStyleSheet(
            f"font-size: 15pt; font-weight: 700; color: {theme.LEVEL_COLOR.get(state.level, theme.TEXT)};")
        sub = [f"Liaison : {m.link_state.value}"]
        if connected:
            sub.append("SIMULATION" if m.simulation else m.port_description)
        if m.protocol:
            sub.append(f"firmware v{m.protocol}")
        if connected and not cfg.safety.watchdog_enabled:
            sub.append("⚠ chien de garde désactivé")
        elif m.watchdog_ms:
            sub.append(f"chien de garde {m.watchdog_ms} ms")
        self.state_sub.setText("  ·  ".join(sub))

        if st is not None and fresh:
            homed = st.homed
            for axis, steps in (("X", st.x), ("Y", st.y)):
                lbl = self.coord_labels[axis]
                lbl.setText(f"{cfg.axis(axis).units.steps_to_mm(steps):.3f}")
                lbl.setStyleSheet(f"color: {theme.TEXT if homed else theme.WARNING};")
            self.coord_ref.setText("position référencée" if homed else
                                   "non référencée : relative à la mise sous tension")
            self.coord_ref.setStyleSheet(f"font-size: 8.5pt; color: {theme.OK if homed else theme.WARNING};")
            self.plate.set_head(cfg.x.units.steps_to_mm(st.x), cfg.y.units.steps_to_mm(st.y),
                                "ok" if homed else "unreferenced")
            self.plate.set_endstops(st.endstops)
        else:
            for lbl in self.coord_labels.values():
                lbl.setText("—")
                lbl.setStyleSheet(f"color: {theme.TEXT_DIM};")
            if m.protocol == 1:
                ref = "position non disponible : firmware v1"
            else:
                ref = "position inconnue" if connected else ""
            self.coord_ref.setText(ref)
            self.coord_ref.setStyleSheet(f"font-size: 8.5pt; color: {theme.TEXT_DIM};")
            if st is not None and connected:
                self.plate.set_head(cfg.x.units.steps_to_mm(st.x), cfg.y.units.steps_to_mm(st.y), "stale")
            else:
                self.plate.set_head(None, None, "stale")
            v1 = m.v1_status if (m.protocol == 1 and fresh) else None
            self.plate.set_endstops(v1.endstops if v1 else None)

        if not connected:
            notice = "Non connecté : bouton « Connecter… » (carte réelle ou simulation)."
        elif m.protocol == 1:
            notice = ("Firmware v1 détecté : diagnostic des capteurs seulement. Pour piloter, "
                      "flashez src/arduino/controle_moteur_v2.")
        elif st is not None and fresh and not st.homed:
            notice = "Position non référencée : lancez la prise d'origine (Xmin, Ymin)."
        elif cfg.x.travel_mm is None or cfg.y.travel_mm is None:
            notice = "Courses inconnues : Machine › Mesurer les courses, ou saisie dans Paramètres › Axes."
        else:
            notice = ""
        self.plate.set_notice(notice)

        move = can_move(state, st)
        homed = bool(st and st.homed)
        self.jog.update_state(
            can_move=bool(move), reason=move.reason, homed=homed,
            cap=None if homed else speed_cap(cfg, False),
            can_home=bool(can_home(state, st)), calibrating=self.controller.calibrating)

        self.sensors.refresh(m, cfg.safety.watchdog_enabled)
        self.line_panel.refresh(m, cfg)
        self._refresh_alarm_banner(state, st)

        self.connect_button.setText("Déconnecter" if connected else "Connecter…")
        self.act_connect_sim.setEnabled(not connected)
        self.act_connect_sim_v1.setEnabled(not connected)
        self.act_disconnect.setEnabled(connected)
        self.act_home.setEnabled(bool(can_home(state, st)))
        self.act_calib.setEnabled(bool(can_home(state, st)) and homed)
        self.act_clear.setEnabled(bool(st and st.alarms))
        self.sim_menu.setEnabled(self.sim is not None)
        self.sim_banner.setVisible(m.simulation and connected)
        title = APP_TITLE + ("  [SIMULATION]" if m.simulation and connected else "")
        if self.windowTitle() != title:
            self.setWindowTitle(title)

    def _refresh_alarm_banner(self, state: MachineState, st) -> None:
        if state is MachineState.ALARM and st is not None:
            causes = [t for flag, t in ALARM_TEXT.items() if st.alarms & flag & BLOCKING_ALARMS]
            self.alarm_text.setText("Alarme : " + ", ".join(causes) + ". Axes arrêtés, déplacements bloqués.")
            self.alarm_button.setText("Acquitter…")
        elif state is MachineState.LOST:
            self.alarm_text.setText(
                "Liaison perdue : la carte ne répond plus. Si le chien de garde est actif, elle a arrêté les axes "
                "d'elle-même. Se reconnecter redémarre la carte : l'origine sera perdue.")
            self.alarm_button.setText("Déconnecter")
        elif state is MachineState.STALE:
            self.alarm_text.setText("État inconnu : aucune donnée récente de la carte. Déplacements bloqués.")
            self.alarm_button.setText("Déconnecter")
        else:
            self.alarm_banner.hide()
            return
        self.alarm_banner.show()
