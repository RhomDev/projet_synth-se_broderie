"""Vue de dessus du plateau, en millimètres.

Repère : origine aux fins de course Xmin (gauche) et Ymin (bas), X vers la droite,
Y vers le haut. La scène est en mm ; la vue applique une échelle (px/mm) et
retourne l'axe Y.

Interactions : molette = zoom sous le curseur ; glisser (clic gauche, milieu ou
droit) = déplacer la vue ; clic gauche sans glisser = viser un point, avec une carte
de confirmation avant tout déplacement.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from communication.protocol import Endstops

from . import theme

ZOOM_MIN, ZOOM_MAX = 0.3, 300.0  # px/mm
GRID_STEPS = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0)


def _cosmetic(color: str | QColor, width: float = 1.0, style=Qt.PenStyle.SolidLine) -> QPen:
    pen = QPen(QColor(color), width, style)
    pen.setCosmetic(True)
    return pen


class _HeadItem(QGraphicsItem):
    """Tête / chariot : taille constante à l'écran."""

    def __init__(self) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setZValue(30)
        self._color = QColor(theme.ACCENT)
        self._dashed = False

    def set_style(self, color: str, dashed: bool) -> None:
        self._color, self._dashed = QColor(color), dashed
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-20, -20, 40, 40)

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        halo = QColor(self._color)
        halo.setAlpha(45)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(0, 0), 15, 15)
        pen = QPen(self._color, 2, Qt.PenStyle.DashLine if self._dashed else Qt.PenStyle.SolidLine)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 9, 9)
        p.setPen(QPen(self._color, 1.5))
        for a, b in (((-18, 0), (-5, 0)), ((5, 0), (18, 0)), ((0, -18), (0, -5)), ((0, 5), (0, 18))):
            p.drawLine(QPointF(*a), QPointF(*b))
        p.setBrush(self._color)
        p.drawEllipse(QPointF(0, 0), 1.8, 1.8)


class _TargetItem(QGraphicsItem):
    def __init__(self) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setZValue(25)
        self._color = QColor(theme.WARNING)

    def set_allowed(self, allowed: bool) -> None:
        self._color = QColor(theme.WARNING if allowed else theme.ERROR)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-12, -12, 24, 24)

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(self._color, 2))
        p.drawLine(QPointF(-8, -8), QPointF(8, 8))
        p.drawLine(QPointF(-8, 8), QPointF(8, -8))
        p.setPen(QPen(self._color, 1, Qt.PenStyle.DotLine))
        p.drawEllipse(QPointF(0, 0), 11, 11)


class _OriginItem(QGraphicsItem):
    """Origine machine (Xmin, Ymin) avec les sens positifs des axes."""

    def __init__(self) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setZValue(20)

    def boundingRect(self) -> QRectF:
        return QRectF(-200, -64, 270, 106)

    def paint(self, p: QPainter, option, widget=None) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor(theme.TEXT)
        p.setPen(QPen(col, 1.6))
        # X+ vers la droite, Y+ vers le haut (repère écran : y négatif)
        p.drawLine(QPointF(0, 0), QPointF(42, 0))
        p.drawLine(QPointF(0, 0), QPointF(0, -42))
        p.setBrush(col)
        p.drawPolygon(QPolygonF([QPointF(48, 0), QPointF(40, -4), QPointF(40, 4)]))
        p.drawPolygon(QPolygonF([QPointF(0, -48), QPointF(-4, -40), QPointF(4, -40)]))
        p.setBrush(QColor(theme.BG))
        p.drawEllipse(QPointF(0, 0), 4.5, 4.5)
        font = QFont(p.font())
        font.setPointSizeF(8)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QPointF(50, 4), "X+")
        p.drawText(QPointF(-7, -52), "Y+")
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor(theme.TEXT_DIM))
        p.drawText(QRectF(-196, 22, 188, 16), Qt.AlignmentFlag.AlignRight, "Origine (Xmin, Ymin)")


class _TargetCard(QFrame):
    """Carte de confirmation affichée après un clic sur le plateau."""

    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            f"QFrame#card {{ background: {theme.SURFACE}; border: 1px solid {theme.WARNING}; border-radius: 8px; }}"
            "QFrame#card QLabel { background: transparent; }"
        )
        title = QLabel("CIBLE")
        title.setProperty("role", "section")
        self.coords = QLabel()
        self.coords.setFont(theme.mono_font(12, bold=True))
        self.reason = QLabel()
        self.reason.setWordWrap(True)
        self.reason.setProperty("role", "note")
        self.go = QPushButton("Aller ici")
        self.go.setProperty("role", "primary")
        cancel = QPushButton("Annuler")
        self.go.clicked.connect(self.confirmed)
        cancel.clicked.connect(self.cancelled)
        buttons = QHBoxLayout()
        buttons.addWidget(self.go)
        buttons.addWidget(cancel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(6)
        lay.addWidget(title)
        lay.addWidget(self.coords)
        lay.addWidget(self.reason)
        lay.addLayout(buttons)
        self.setFixedWidth(300)
        self.hide()

    def show_target(self, x: float, y: float, allowed: bool, reason: str) -> None:
        self.coords.setText(f"X {x:9.3f} mm\nY {y:9.3f} mm")
        self.reason.setText(reason)
        self.reason.setVisible(bool(reason))
        self.go.setEnabled(allowed)
        self.adjustSize()
        self.show()
        self.raise_()


class PlateView(QGraphicsView):
    target_clicked = Signal(float, float)
    target_confirmed = Signal(float, float)
    target_cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(-3000, -3000, 9000, 9000)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMouseTracking(True)
        self.setMinimumSize(420, 320)

        self._travel: tuple[float | None, float | None] = (None, None)
        self._margin = 1.0
        self._grid_step = 10.0
        self._show_grid = True
        self._head_pos: QPointF | None = None
        self._target_pos: QPointF | None = None
        self._press: QPointF | None = None
        self._last: QPointF | None = None
        self._panning = False
        self._fitted = False

        self._plate = QGraphicsRectItem()
        self._plate.setPen(_cosmetic(theme.BORDER, 1.2))
        self._plate.setBrush(QBrush(QColor(theme.PLATE_FILL)))
        self._plate.setZValue(-10)
        self._soft = QGraphicsRectItem()
        self._soft.setPen(_cosmetic(theme.TEXT_DIM, 1, Qt.PenStyle.DashLine))
        self._soft.setZValue(5)
        self._soft.setToolTip("Limites logicielles (course moins la marge)")
        for item in (self._plate, self._soft):
            self._scene.addItem(item)
            item.hide()
        self._marks = {name: QGraphicsLineItem() for name in ("x_min", "x_max", "y_min", "y_max")}
        for name, item in self._marks.items():
            item.setZValue(8)
            item.setToolTip(f"Fin de course {name.replace('_min', 'min').replace('_max', 'max').upper()}")
            self._scene.addItem(item)
        self._zone_items: list = []
        self._origin = _OriginItem()
        self._scene.addItem(self._origin)
        self._target_line = QGraphicsLineItem()
        self._target_line.setPen(_cosmetic(theme.WARNING, 1.2, Qt.PenStyle.DashLine))
        self._target_line.setZValue(24)
        self._target_line.hide()
        self._scene.addItem(self._target_line)
        self._target = _TargetItem()
        self._target.hide()
        self._scene.addItem(self._target)
        self._head = _HeadItem()
        self._head.hide()
        self._scene.addItem(self._head)
        self._preview = QGraphicsPathItem()
        self._preview.setPen(_cosmetic(theme.WARNING, 1.4, Qt.PenStyle.DashLine))
        self._preview.setZValue(22)
        self._preview.setToolTip("Ligne de test prévue (repères : points)")
        self._scene.addItem(self._preview)
        self._trace = QGraphicsPathItem()
        self._trace.setPen(_cosmetic(theme.ACCENT, 2.0))
        self._trace.setZValue(23)
        self._trace.setToolTip("Trajet parcouru pendant la ligne de test")
        self._scene.addItem(self._trace)
        self._trace_path: QPainterPath | None = None

        self._build_overlays()
        self.setTransform(QTransform.fromScale(2.0, -2.0))
        self.set_endstops(None)

    # ---------------------------------------------------------- calques

    def _build_overlays(self) -> None:
        vp = self.viewport()
        self._hud = QLabel(vp)
        self._hud.setFont(theme.mono_font(9.5))
        self._hud.setStyleSheet(
            f"background: rgba(15,18,22,210); color: {theme.TEXT_DIM}; border: 1px solid {theme.BORDER};"
            "border-radius: 5px; padding: 4px 8px;"
        )
        self._set_hud(None)

        self._notice = QLabel(vp)
        self._notice.setWordWrap(True)
        self._notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._notice.setStyleSheet(
            f"background: rgba(40,30,10,215); color: {theme.WARNING}; border: 1px solid #5c4413;"
            "border-radius: 6px; padding: 6px 12px;"
        )
        self._notice.hide()

        self._tools = QFrame(vp)
        self._tools.setStyleSheet(
            f"QFrame {{ background: rgba(23,27,33,225); border: 1px solid {theme.BORDER}; border-radius: 6px; }}"
            "QLabel, QCheckBox { background: transparent; border: none; }"
        )
        fit = QPushButton("Ajuster")
        fit.setToolTip("Recadrer sur le plateau")
        fit.clicked.connect(self.fit)
        self._grid_box = QCheckBox("Grille")
        self._grid_box.setChecked(True)
        self._grid_box.toggled.connect(self._toggle_grid)
        self._step_combo = QComboBox()
        for s in GRID_STEPS:
            self._step_combo.addItem(f"{s:g} mm", s)
        self._step_combo.currentIndexChanged.connect(self._grid_step_changed)
        lay = QHBoxLayout(self._tools)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.addWidget(fit)
        lay.addWidget(self._grid_box)
        lay.addWidget(self._step_combo)

        self._card = _TargetCard(vp)
        self._card.confirmed.connect(self._confirm_target)
        self._card.cancelled.connect(self.target_cancelled)
        self._card.cancelled.connect(self.clear_target)

    def _place_overlays(self) -> None:
        vp = self.viewport().rect()
        self._hud.adjustSize()
        self._hud.move(vp.width() - self._hud.width() - 10, vp.height() - self._hud.height() - 10)
        self._tools.adjustSize()
        self._tools.move(vp.width() - self._tools.width() - 10, 10)
        card_y = 10
        if self._notice.isVisible():
            w = max(220, min(460, vp.width() - 2 * self._tools.width() - 40))
            self._notice.setFixedWidth(w)
            self._notice.adjustSize()
            self._notice.move((vp.width() - w) // 2, 10)
            card_y = 10 + self._notice.height() + 8
        self._card.move(10, card_y)

    def _set_hud(self, pos: QPointF | None) -> None:
        if pos is None:
            self._hud.setText("Curseur   X     —      Y     —")
        else:
            self._hud.setText(f"Curseur   X {pos.x():8.2f}   Y {pos.y():8.2f}  mm")
        self._hud.adjustSize()

    def _toggle_grid(self, on: bool) -> None:
        self._show_grid = on
        self.viewport().update()

    def _grid_step_changed(self) -> None:
        self._grid_step = float(self._step_combo.currentData())
        self.viewport().update()

    # -------------------------------------------------------------- API

    def set_geometry(self, travel_x: float | None, travel_y: float | None, margin: float, zones, grid_step: float,
                     show_grid: bool) -> None:
        changed = (travel_x, travel_y) != self._travel
        self._travel = (travel_x, travel_y)
        self._margin = margin
        known = travel_x is not None and travel_y is not None
        if known:
            self._plate.setRect(QRectF(0, 0, travel_x, travel_y))
            self._soft.setRect(QRectF(margin, margin, travel_x - 2 * margin, travel_y - 2 * margin))
        self._plate.setVisible(known)
        self._soft.setVisible(known)
        for item in self._zone_items:
            self._scene.removeItem(item)
        self._zone_items = []
        for z in zones:
            rect = QGraphicsRectItem(QRectF(z.x_mm, z.y_mm, z.width_mm, z.height_mm))
            rect.setPen(_cosmetic(theme.ERROR, 1.2))
            rect.setBrush(QBrush(QColor(229, 72, 77, 120), Qt.BrushStyle.BDiagPattern))
            rect.setZValue(6)
            rect.setToolTip(f"Zone interdite : {z.name}")
            label = QGraphicsSimpleTextItem(z.name)
            label.setBrush(QColor(theme.ERROR))
            label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            label.setPos(z.x_mm, z.y_mm + z.height_mm)
            for item in (rect, label):
                self._scene.addItem(item)
                self._zone_items.append(item)
        if self._step_combo.findData(grid_step) < 0:
            self._step_combo.addItem(f"{grid_step:g} mm", grid_step)
        self._step_combo.blockSignals(True)
        self._step_combo.setCurrentIndex(self._step_combo.findData(grid_step))
        self._step_combo.blockSignals(False)
        self._grid_step = grid_step
        self._grid_box.setChecked(show_grid)
        self._update_marks_geometry()
        if changed and self._fitted:
            self.fit()
        self.viewport().update()

    def set_head(self, x: float | None, y: float | None, style: str) -> None:
        """``style`` : ``ok`` (référencée), ``unreferenced`` ou ``stale``."""
        if x is None or y is None:
            self._head.hide()
            self._head_pos = None
        else:
            self._head_pos = QPointF(x, y)
            self._head.setPos(self._head_pos)
            colors = {"ok": theme.ACCENT, "unreferenced": theme.WARNING, "stale": theme.INACTIVE}
            self._head.set_style(colors.get(style, theme.INACTIVE), dashed=style != "ok")
            self._head.show()
        self._update_target_line()

    def set_endstops(self, endstops: Endstops | None) -> None:
        for name, item in self._marks.items():
            if endstops is None:
                item.setPen(_cosmetic(theme.INACTIVE, 4, Qt.PenStyle.DotLine))
            else:
                pressed = getattr(endstops, name)
                item.setPen(_cosmetic(theme.OK if pressed else theme.INACTIVE, 6 if pressed else 4))

    def set_line_preview(self, plan) -> None:
        """Ligne prévue avec un repère par point ; ``None`` l'efface."""
        path = QPainterPath()
        if plan is not None:
            path.moveTo(plan.x0, plan.y0)
            path.lineTo(plan.x1, plan.y1)
            nx, ny = -plan.uy, plan.ux  # normale
            half = min(1.5, plan.stitch_mm)
            for k in range(1, plan.stitches + 1):
                d = min(k * plan.stitch_mm, plan.length_mm)
                cx, cy = plan.x0 + d * plan.ux, plan.y0 + d * plan.uy
                path.moveTo(cx - half * nx, cy - half * ny)
                path.lineTo(cx + half * nx, cy + half * ny)
        self._preview.setPath(path)

    def trace_clear(self) -> None:
        self._trace_path = None
        self._trace.setPath(QPainterPath())

    def trace_add(self, x: float, y: float) -> None:
        if self._trace_path is None:
            self._trace_path = QPainterPath(QPointF(x, y))
        else:
            self._trace_path.lineTo(x, y)
        self._trace.setPath(self._trace_path)

    def set_notice(self, text: str) -> None:
        self._notice.setText(text)
        self._notice.setVisible(bool(text))
        self._place_overlays()

    def show_target(self, x: float, y: float, allowed: bool, reason: str) -> None:
        self._target_pos = QPointF(x, y)
        self._target.setPos(self._target_pos)
        self._target.set_allowed(allowed)
        self._target.show()
        self._update_target_line()
        self._card.show_target(x, y, allowed, reason)
        self._place_overlays()

    def clear_target(self) -> None:
        self._target_pos = None
        self._target.hide()
        self._target_line.hide()
        self._card.hide()

    def fit(self) -> None:
        tx, ty = self._travel
        if tx is not None and ty is not None:
            rect = QRectF(0, 0, tx, ty)
        else:
            rect = QRectF(-20, -20, 140, 100)
            if self._head_pos is not None:
                rect = rect.united(QRectF(self._head_pos.x() - 30, self._head_pos.y() - 30, 60, 60))
        vp = self.viewport().rect()
        pad_x, pad_y = 70, 80
        sx = max(vp.width() - 2 * pad_x, 50) / max(rect.width(), 1e-6)
        sy = max(vp.height() - 2 * pad_y, 50) / max(rect.height(), 1e-6)
        z = max(ZOOM_MIN, min(ZOOM_MAX, min(sx, sy)))
        self.setTransform(QTransform.fromScale(z, -z))
        self.centerOn(rect.center())
        self._fitted = True

    # --------------------------------------------------------- interne

    def _update_marks_geometry(self) -> None:
        tx, ty = self._travel
        lx = tx if tx is not None else 60.0
        ly = ty if ty is not None else 60.0
        self._marks["x_min"].setLine(QLineF(0, 0, 0, ly))
        self._marks["y_min"].setLine(QLineF(0, 0, lx, 0))
        if tx is not None and ty is not None:
            self._marks["x_max"].setLine(QLineF(tx, 0, tx, ty))
            self._marks["y_max"].setLine(QLineF(0, ty, tx, ty))
        self._marks["x_max"].setVisible(tx is not None and ty is not None)
        self._marks["y_max"].setVisible(tx is not None and ty is not None)

    def _update_target_line(self) -> None:
        if self._target_pos is not None and self._head_pos is not None:
            self._target_line.setLine(QLineF(self._head_pos, self._target_pos))
            self._target_line.show()
        else:
            self._target_line.hide()

    def _confirm_target(self) -> None:
        if self._target_pos is not None:
            self.target_confirmed.emit(self._target_pos.x(), self._target_pos.y())

    def _zoom(self) -> float:
        return abs(self.transform().m11())

    # ----------------------------------------------------------- dessin

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(theme.BG))
        if not self._show_grid:
            return
        tx, ty = self._travel
        area = QRectF(0, 0, tx, ty) if (tx is not None and ty is not None) else QRectF(rect)
        area = area.intersected(rect)
        if area.isEmpty():
            return
        step = self._grid_step
        z = self._zoom()
        while step * z < 7:
            step *= 5
        major = step * 5
        for s, color in ((step, theme.GRID_MINOR), (major, theme.GRID_MAJOR)):
            painter.setPen(_cosmetic(color, 1))
            x = math.ceil(area.left() / s) * s
            while x <= area.right():
                painter.drawLine(QPointF(x, area.top()), QPointF(x, area.bottom()))
                x += s
            y = math.ceil(area.top() / s) * s
            while y <= area.bottom():
                painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
                y += s

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """Graduations en mm le long des axes X (bas) et Y (gauche)."""
        z = self._zoom()
        step = self._grid_step * 5
        while step * z < 55:
            step *= 2
        tx, ty = self._travel
        x_end = tx if tx is not None else rect.right()
        y_end = ty if ty is not None else rect.bottom()
        painter.save()
        painter.resetTransform()
        font = QFont(painter.font())
        font.setPointSizeF(7.5)
        painter.setFont(font)
        painter.setPen(QColor(theme.TEXT_DIM))
        x = max(0.0, math.ceil(rect.left() / step) * step)
        while x <= min(x_end, rect.right()):
            pt = self.mapFromScene(QPointF(x, 0))
            painter.drawText(pt.x() - 20, pt.y() + 6, 40, 14, Qt.AlignmentFlag.AlignHCenter, f"{x:g}")
            x += step
        y = max(step, math.ceil(rect.top() / step) * step)
        while y <= min(y_end, rect.bottom()):
            pt = self.mapFromScene(QPointF(0, y))
            painter.drawText(pt.x() - 46, pt.y() - 7, 40, 14,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{y:g}")
            y += step
        painter.restore()

    # ------------------------------------------------------- événements

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._fitted:
            self.fit()
        self._place_overlays()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_overlays()

    def wheelEvent(self, event) -> None:
        factor = 1.0015 ** event.angleDelta().y()
        z = self._zoom()
        factor = max(ZOOM_MIN / z, min(ZOOM_MAX / z, factor))
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        self._press = self._last = event.position()
        self._panning = event.button() != Qt.MouseButton.LeftButton
        if self._panning:
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        self._set_hud(self.mapToScene(pos.toPoint()))
        self._place_overlays()
        if self._press is None:
            return
        if not self._panning and (pos - self._press).manhattanLength() > 5:
            self._panning = True
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
        if self._panning:
            delta = pos - self._last
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
        self._last = pos

    def mouseReleaseEvent(self, event) -> None:
        if self._press is not None and not self._panning and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.position().toPoint())
            self.target_clicked.emit(sp.x(), sp.y())
        self._press = None
        self._panning = False
        self.viewport().unsetCursor()

    def mouseDoubleClickEvent(self, event) -> None:
        event.accept()  # pas de double déclenchement

    def leaveEvent(self, event) -> None:
        self._set_hud(None)
        super().leaveEvent(event)
