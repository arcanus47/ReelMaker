"""Iconos de línea dibujados con QPainter (nítidos en cualquier DPI, sin archivos extra)."""

from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF


# Todos los iconos se dibujan en una rejilla de 24 × 24.
def _dashboard(p, col):
    for x, y in ((3, 3), (13, 3), (3, 13), (13, 13)):
        p.drawRoundedRect(QRectF(x, y, 8, 8), 2.2, 2.2)


def _projects(p, col):
    pts = [QPointF(3, 6.5), QPointF(9.2, 6.5), QPointF(11.2, 9), QPointF(21, 9),
           QPointF(21, 19), QPointF(3, 19)]
    p.drawPolygon(QPolygonF(pts))


def _live(p, col):
    p.setBrush(col)
    p.drawEllipse(QPointF(12, 12), 2.2, 2.2)
    p.setBrush(Qt.NoBrush)
    for r in (5.6, 9.2):
        rect = QRectF(12 - r, 12 - r, 2 * r, 2 * r)
        p.drawArc(rect, 135 * 16, 90 * 16)
        p.drawArc(rect, -45 * 16, 90 * 16)


def _star(path, cx, cy, r):
    path.moveTo(cx, cy - r)
    path.quadTo(cx, cy, cx + r, cy)
    path.quadTo(cx, cy, cx, cy + r)
    path.quadTo(cx, cy, cx - r, cy)
    path.quadTo(cx, cy, cx, cy - r)


def _analysis(p, col):
    path = QPainterPath()
    _star(path, 10.5, 13.5, 7.5)
    _star(path, 19, 5.5, 2.8)
    p.drawPath(path)


def _editor(p, col):
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2.6, 2.6)
    p.drawLine(QPointF(8, 5), QPointF(8, 19))
    p.drawLine(QPointF(16, 5), QPointF(16, 19))
    for y in (9, 15):
        p.drawLine(QPointF(3, y), QPointF(5.4, y))
        p.drawLine(QPointF(18.6, y), QPointF(21, y))


def _exports(p, col):
    p.drawPolyline(QPolygonF([QPointF(4, 15), QPointF(4, 19.5), QPointF(20, 19.5), QPointF(20, 15)]))
    p.drawLine(QPointF(12, 15), QPointF(12, 4))
    p.drawPolyline(QPolygonF([QPointF(7.6, 8.4), QPointF(12, 4), QPointF(16.4, 8.4)]))


def _settings(p, col):
    for y, kx in ((6, 8), (12, 16), (18, 10.5)):
        p.drawLine(QPointF(3, y), QPointF(kx - 2.9, y))
        p.drawLine(QPointF(kx + 2.9, y), QPointF(21, y))
        p.drawEllipse(QPointF(kx, y), 2.3, 2.3)


def _plus(p, col):
    p.drawLine(QPointF(12, 5), QPointF(12, 19))
    p.drawLine(QPointF(5, 12), QPointF(19, 12))


def _folder_open(p, col):
    _projects(p, col)


_DRAWERS = {
    "dashboard": _dashboard, "projects": _projects, "live": _live,
    "analysis": _analysis, "editor": _editor, "exports": _exports,
    "settings": _settings, "plus": _plus, "folder": _folder_open,
}


def pixmap(name, color, size=20, dpr=2.0, stroke=1.9):
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(size / 24.0, size / 24.0)
    qcol = QColor(color)
    p.setPen(QPen(qcol, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    _DRAWERS[name](p, qcol)
    p.end()
    return pm


def make_icon(name, normal, hover=None, size=20):
    icon = QIcon()
    icon.addPixmap(pixmap(name, normal, size), QIcon.Normal)
    icon.addPixmap(pixmap(name, hover or normal, size), QIcon.Active)
    return icon


# ── Imágenes auxiliares que la hoja de estilos necesita como archivo ──────
def _chevron(path: Path, up: bool, color: str, size=12):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    m = size * 0.28
    mid, top, bot = size / 2, size * 0.36, size * 0.64
    pts = [QPointF(m, bot if up else top), QPointF(mid, top if up else bot),
           QPointF(size - m, bot if up else top)]
    p.drawPolyline(QPolygonF(pts))
    p.end()
    pm.save(str(path), "PNG")


def _check(path: Path, size=14):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(QColor("#ffffff"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPolyline(QPolygonF([QPointF(3.3, 7.4), QPointF(5.9, 10.0), QPointF(10.8, 4.3)]))
    p.end()
    pm.save(str(path), "PNG")


def ensure_style_assets(directory: Path) -> dict:
    """Genera (una vez por ejecución) las flechas y el check usados por el QSS."""
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "chevron_down": directory / "chevron_down.png",
        "chevron_up": directory / "chevron_up.png",
        "check": directory / "check.png",
    }
    _chevron(files["chevron_down"], False, "#8ea6cc")
    _chevron(files["chevron_up"], True, "#8ea6cc")
    _check(files["check"])
    return {k: v.as_posix() for k, v in files.items()}
