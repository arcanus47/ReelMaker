"""Componentes visuales propios de REELMAKER."""

from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QRect
from PySide6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
    QPixmap, QRadialGradient
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTableWidget, QVBoxLayout, QWidget
)

from app.config import ASSETS_DIR
from app.ui import icons
from app.ui.theme import C


def load_logo(max_side=420):
    """Carga el logo del proyecto ya suavizado para reescalar con calidad."""
    candidates = [
        ASSETS_DIR / "reelmaker.png",
        Path(__file__).resolve().parent.parent / "assets" / "reelmaker.png",
    ]
    for path in candidates:
        if path.is_file():
            pm = QPixmap(str(path))
            if not pm.isNull():
                return pm.scaled(max_side, max_side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QPixmap()


def _rgba(hex_color, alpha):
    col = QColor(hex_color)
    col.setAlpha(alpha)
    return col


def _paint_logo(painter, pixmap, rect: QRectF, glow=True):
    """Dibuja el logo con esquinas redondeadas y un halo azul/cian detrás."""
    if pixmap.isNull():
        return
    if glow:
        halo = QRadialGradient(rect.center(), rect.width() * 0.95)
        halo.setColorAt(0.0, QColor(61, 123, 255, 120))
        halo.setColorAt(0.55, QColor(39, 196, 245, 34))
        halo.setColorAt(1.0, QColor(39, 196, 245, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(halo))
        painter.drawEllipse(rect.center(), rect.width() * 0.95, rect.height() * 0.95)
    painter.save()
    clip = QPainterPath()
    radius = rect.width() * 0.225
    clip.addRoundedRect(rect, radius, radius)
    painter.setClipPath(clip)
    painter.drawPixmap(rect.toRect(), pixmap)
    painter.restore()


class Backdrop(QWidget):
    """Fondo de la ventana: navy profundo con resplandores fríos muy sutiles."""

    def paintEvent(self, _event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(C["bg1"]))
        g1 = QRadialGradient(QPointF(w * 0.92, -h * 0.08), w * 0.55)
        g1.setColorAt(0, QColor(39, 120, 245, 40))
        g1.setColorAt(1, QColor(39, 120, 245, 0))
        p.fillRect(self.rect(), QBrush(g1))
        g2 = QRadialGradient(QPointF(w * 0.30, h * 1.08), w * 0.50)
        g2.setColorAt(0, QColor(106, 116, 255, 26))
        g2.setColorAt(1, QColor(106, 116, 255, 0))
        p.fillRect(self.rect(), QBrush(g2))


class LogoBadge(QWidget):
    """Logo del proyecto para el menú lateral, con halo luminoso."""

    def __init__(self, size=132, parent=None):
        super().__init__(parent)
        self._size = size
        self._pm = load_logo()
        self.setFixedSize(size + 28, size + 28)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        rect = QRectF(14, 14, self._size, self._size)
        _paint_logo(p, self._pm, rect)
        p.setClipping(False)
        p.setPen(QPen(QColor(120, 170, 255, 70), 1))
        p.setBrush(Qt.NoBrush)
        r = self._size * 0.225
        p.drawRoundedRect(rect, r, r)


class Eyebrow(QLabel):
    """Etiqueta en mayúsculas con tracking amplio."""

    def __init__(self, text="", object_name="eyebrow", spacing=1.6, parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)
        font = self.font()
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        self.setFont(font)


class StatusPill(QLabel):
    """Píldora de estado: el color se deduce del texto que se le asigna."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("statusPill")
        self._sync(text)

    def setText(self, text):  # noqa: N802 (API de Qt)
        super().setText(text)
        self._sync(text)

    def _sync(self, text):
        t = text.upper()
        if any(k in t for k in ("ERROR", "ATENCIÓN", "ATENCION")):
            state = "error"
        elif any(k in t for k in ("PREPARACIÓN", "PREPARACION", "CONECTANDO", "CAPTURANDO", "ANALIZANDO")):
            state = "busy"
        elif any(k in t for k in ("LISTO", "FINALIZADO")):
            state = "ok"
        else:
            state = "idle"
        if self.property("state") != state:
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)


class EmptyTable(QTableWidget):
    """Tabla con mensaje centrado cuando no hay filas."""

    def __init__(self, rows=0, columns=0, empty_text="Sin datos todavía", parent=None):
        super().__init__(rows, columns, parent)
        self.empty_text = empty_text

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        if self.rowCount() == 0:
            p = QPainter(self.viewport())
            p.setRenderHint(QPainter.TextAntialiasing, True)
            p.setPen(QColor(C["dim"]))
            font = p.font()
            font.setPointSize(10)
            p.setFont(font)
            p.drawText(self.viewport().rect(), Qt.AlignCenter, self.empty_text)


class IconBadge(QWidget):
    """Cuadro redondeado con un icono de línea y degradado del color de acento."""

    def __init__(self, icon_name, accent, size=48, parent=None):
        super().__init__(parent)
        self._name, self._accent = icon_name, QColor(accent)
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, _rgba(self._accent.name(), 70))
        g.setColorAt(1, _rgba(self._accent.name(), 22))
        p.setPen(QPen(_rgba(self._accent.name(), 120), 1))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 13, 13)
        pm = icons.pixmap(self._name, self._accent.lighter(135).name(), int(self.width() * 0.5))
        s = int(self.width() * 0.5)
        p.drawPixmap(QRect((self.width() - s) // 2, (self.height() - s) // 2, s, s), pm)


class StatCard(QFrame):
    """Tarjeta de métrica con icono, número grande y detalle."""

    def __init__(self, title, value, icon_name, accent, hint="", parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self.setMinimumHeight(104)
        row = QHBoxLayout(self)
        row.setContentsMargins(20, 18, 22, 18)
        row.setSpacing(16)
        row.addWidget(IconBadge(icon_name, accent, 52), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(Eyebrow(title, "statTitle", 1.4))
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        col.addWidget(self.value_label)
        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName("statHint")
        col.addWidget(self.hint_label)
        row.addLayout(col, 1)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 16, 16)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#111c30"))
        g.setColorAt(1, QColor("#0d1524"))
        p.fillPath(path, QBrush(g))
        p.setClipPath(path)
        glow = QRadialGradient(QPointF(r.right() - 20, r.top()), r.width() * 0.7)
        glow.setColorAt(0, _rgba(self._accent.name(), 46))
        glow.setColorAt(1, _rgba(self._accent.name(), 0))
        p.fillRect(self.rect(), QBrush(glow))
        bar = QLinearGradient(r.topLeft(), r.topRight())
        bar.setColorAt(0, _rgba(self._accent.name(), 230))
        bar.setColorAt(1, _rgba(self._accent.name(), 0))
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 2), QBrush(bar))
        p.setClipping(False)
        p.setPen(QPen(QColor(C["line2"]), 1))
        p.drawPath(path)


class StepCard(QFrame):
    """Paso del flujo de trabajo; se comporta como un botón."""

    def __init__(self, number, title, text, callback, parent=None):
        super().__init__(parent)
        self._hover = False
        self._callback = callback
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(86)
        col = QVBoxLayout(self)
        col.setContentsMargins(18, 14, 18, 14)
        col.setSpacing(3)
        col.addWidget(Eyebrow(number, "stepNum", 1.4))
        t = QLabel(title)
        t.setObjectName("stepTitle")
        col.addWidget(t)
        d = QLabel(text)
        d.setObjectName("stepText")
        d.setWordWrap(True)
        col.addWidget(d)
        for child in (t, d):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def enterEvent(self, event):  # noqa: N802
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self._callback()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        if self._hover:
            g.setColorAt(0, QColor("#15294d"))
            g.setColorAt(1, QColor("#0f1d36"))
            border = QColor("#2f5aa8")
        else:
            g.setColorAt(0, QColor("#101a2d"))
            g.setColorAt(1, QColor("#0c1424"))
            border = QColor(C["line2"])
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 14, 14)


class HeroBanner(QFrame):
    """Cabecera protagonista del dashboard con el logo a gran tamaño."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pm = load_logo()
        self.setMinimumHeight(230)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 22, 22)

        base = QLinearGradient(r.topLeft(), r.bottomRight())
        base.setColorAt(0.0, QColor("#12254d"))
        base.setColorAt(0.55, QColor("#0b1730"))
        base.setColorAt(1.0, QColor("#08101f"))
        p.fillPath(path, QBrush(base))
        p.setClipPath(path)

        cyan = QRadialGradient(QPointF(r.right() - 150, r.center().y()), r.height() * 1.25)
        cyan.setColorAt(0, QColor(39, 196, 245, 78))
        cyan.setColorAt(1, QColor(39, 196, 245, 0))
        p.fillRect(self.rect(), QBrush(cyan))
        indigo = QRadialGradient(QPointF(r.left() + 60, r.top() - 20), r.width() * 0.5)
        indigo.setColorAt(0, QColor(106, 116, 255, 60))
        indigo.setColorAt(1, QColor(106, 116, 255, 0))
        p.fillRect(self.rect(), QBrush(indigo))

        # Rejilla de puntos tenue en la mitad derecha
        p.setPen(QPen(QColor(150, 190, 255, 26), 2, Qt.SolidLine, Qt.RoundCap))
        x0 = int(r.width() * 0.52)
        for x in range(x0, int(r.width()), 26):
            for y in range(14, int(r.height()), 26):
                p.drawPoint(x, y)

        if self.width() >= 780:
            side = min(r.height() - 44, 196)
            logo_rect = QRectF(r.right() - side - 46, r.center().y() - side / 2, side, side)
            _paint_logo(p, self._pm, logo_rect)
            p.setClipping(False)
            p.setPen(QPen(QColor(140, 185, 255, 80), 1))
            p.setBrush(Qt.NoBrush)
            rad = side * 0.225
            p.drawRoundedRect(logo_rect, rad, rad)

        p.setClipping(False)
        edge = QLinearGradient(r.topLeft(), r.bottomRight())
        edge.setColorAt(0, QColor("#2f5aa8"))
        edge.setColorAt(1, QColor("#1b2f55"))
        p.setPen(QPen(QBrush(edge), 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
