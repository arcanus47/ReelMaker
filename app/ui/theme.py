"""REELMAKER design system — paleta oscura y fría (navy / acero / cian)."""

from PySide6.QtGui import QColor, QPalette

# ── Paleta ────────────────────────────────────────────────────────────────
C = {
    # Superficies
    "bg0": "#060a12",        # fondo más profundo
    "bg1": "#080d17",        # ventana
    "sidebar": "#0a101c",
    "surface": "#0e1626",    # tarjetas / paneles
    "surface2": "#121d32",   # elevado
    "surface3": "#18263f",   # hover
    # Bordes
    "line": "#17253b",
    "line2": "#223452",
    "line3": "#2f4670",
    # Texto
    "text": "#e8eef9",
    "text2": "#b4c2d9",
    "muted": "#7e91b0",
    "dim": "#556885",
    # Acentos
    "blue": "#3d7bff",
    "blue_hi": "#6aa0ff",
    "cyan": "#27c4f5",
    "cyan_hi": "#6ee0ff",
    "indigo": "#6a74ff",
    # Semánticos
    "ok": "#34dcb0",
    "warn": "#f6bd45",
    "danger": "#ff6b87",
}


def build_stylesheet(icons: dict) -> str:
    """Devuelve la hoja de estilos global. `icons` mapea nombre → ruta PNG."""
    c = C
    return f"""
* {{ font-family: "Inter", "Segoe UI", "Noto Sans", "Ubuntu", sans-serif; outline: 0; }}
QMainWindow {{ background:{c['bg1']}; }}
QWidget {{ color:{c['text']}; font-size:13px; }}
QDialog, QMessageBox {{ background:{c['surface']}; }}
QMessageBox QLabel {{ color:{c['text']}; font-size:13px; }}
QMessageBox QPushButton, QDialogButtonBox QPushButton {{ min-width:92px; }}
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background:transparent; border:0; }}
QStackedWidget {{ background:transparent; }}

/* ── Sidebar ───────────────────────────────────────────── */
QFrame#sidebar {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0c1424, stop:1 #080d17);
    border-right:1px solid {c['line']};
}}
QLabel#brandTag {{ color:{c['cyan']}; font-size:10px; font-weight:700; }}
QLabel#navSection {{ color:{c['dim']}; font-size:10px; font-weight:700; padding:0 6px; }}
QFrame#sideFooter {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1c30, stop:1 #0b1423);
    border:1px solid {c['line2']}; border-radius:12px;
}}
QLabel#footTitle {{ color:{c['text']}; font-size:11px; font-weight:700; }}
QLabel#footSub {{ color:{c['muted']}; font-size:10px; }}
QLabel#footDot {{ color:{c['ok']}; font-size:14px; }}

QPushButton#nav {{
    background:transparent; border:1px solid transparent; border-radius:10px;
    text-align:left; padding:0 14px; min-height:42px;
    color:{c['muted']}; font-size:13px; font-weight:600;
}}
QPushButton#nav:hover {{ background:#101b30; color:{c['text']}; border:1px solid #182a47; }}
QPushButton#nav[active="true"] {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #17305c, stop:1 #0f1c34);
    color:#ffffff; border:1px solid #28457c; border-left:3px solid {c['cyan']};
}}

/* ── Tipografía ────────────────────────────────────────── */
QLabel#title {{ font-size:28px; font-weight:800; color:#f6f9ff; }}
QLabel#heroTitle {{ font-size:34px; font-weight:800; color:#ffffff; }}
QLabel#heroText {{ font-size:14px; color:{c['text2']}; }}
QLabel#sectionTitle {{ color:{c['text']}; font-size:15px; font-weight:700; }}
QLabel#h2 {{ color:{c['text']}; font-size:16px; font-weight:700; }}
QLabel#muted {{ color:{c['muted']}; font-size:12px; }}
QLabel#eyebrow {{ color:{c['cyan']}; font-size:10px; font-weight:700; }}
QLabel#crumb {{ color:{c['muted']}; font-size:11px; font-weight:600; }}
QLabel#fieldCaption {{ color:{c['muted']}; font-size:10px; font-weight:700; }}
QLabel#liveHeadline {{ font-size:19px; font-weight:800; color:#f6f9ff; }}
QLabel#liveStatus {{ font-size:13px; font-weight:600; color:{c['text']}; }}
QLabel#versionChip {{
    color:{c['text2']}; font-size:10px; font-weight:700;
    background:{c['surface2']}; border:1px solid {c['line2']}; border-radius:9px; padding:5px 10px;
}}
QLabel#statValue {{ font-size:32px; font-weight:800; color:#ffffff; }}
QLabel#statTitle {{ font-size:10px; font-weight:700; color:{c['muted']}; }}
QLabel#statHint {{ font-size:11px; color:{c['dim']}; }}
QLabel#stepNum {{ font-size:11px; font-weight:800; color:{c['cyan']}; }}
QLabel#stepTitle {{ font-size:13px; font-weight:700; color:{c['text']}; }}
QLabel#stepText {{ font-size:11px; color:{c['muted']}; }}

/* ── Píldora de estado ─────────────────────────────────── */
QLabel#statusPill {{ border-radius:11px; padding:6px 12px; font-size:10px; font-weight:800;
    background:#131f35; color:{c['muted']}; border:1px solid {c['line2']}; }}
QLabel#statusPill[state="ok"] {{ background:#0d2a2c; color:{c['ok']}; border:1px solid #1b5953; }}
QLabel#statusPill[state="busy"] {{ background:#0d2542; color:{c['cyan_hi']}; border:1px solid #1d4f88; }}
QLabel#statusPill[state="error"] {{ background:#341424; color:{c['danger']}; border:1px solid #772c47; }}

/* ── Botones ───────────────────────────────────────────── */
QPushButton {{
    background:{c['surface2']}; color:{c['text']}; border:1px solid {c['line2']};
    border-radius:10px; padding:10px 18px; font-weight:600; min-height:20px;
}}
QPushButton:hover {{ background:{c['surface3']}; border-color:{c['line3']}; }}
QPushButton:pressed {{ background:#0f192b; }}
QPushButton:disabled {{ background:#0e1626; color:{c['dim']}; border-color:{c['line']}; }}
QPushButton#primary {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3566f5, stop:1 #1fa3ee);
    border:1px solid #5d93ff; color:#ffffff; font-weight:700;
}}
QPushButton#primary:hover {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4a7bff, stop:1 #33b7fa);
    border:1px solid #8fb6ff;
}}
QPushButton#primary:pressed {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2a56d8, stop:1 #1790d6);
}}
QPushButton#primary:disabled {{ background:#13203a; border:1px solid #1d2f50; color:{c['dim']}; }}
QPushButton#danger {{ background:#3a1626; border:1px solid #7a2f48; color:#ffe6ec; }}
QPushButton#danger:hover {{ background:#4a1b30; border-color:#a8405f; }}

/* ── Tarjetas y paneles ────────────────────────────────── */
QFrame#card, QFrame#panel {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #101a2d, stop:1 #0d1524);
    border:1px solid {c['line2']}; border-radius:16px;
}}
QFrame#divider {{ background:{c['line']}; border:0; max-height:1px; min-height:1px; }}

/* ── Campos ────────────────────────────────────────────── */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background:#0a1220; color:{c['text']}; border:1px solid {c['line2']};
    border-radius:10px; padding:8px 12px; min-height:22px;
    selection-background-color:{c['blue']}; selection-color:#ffffff;
}}
QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover, QSpinBox:hover {{ border:1px solid {c['line3']}; }}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border:1px solid {c['cyan']}; background:#0c1527;
}}
QLineEdit:read-only {{ color:{c['muted']}; background:#0a111e; }}
QComboBox {{ min-height:24px; padding-right:34px; }}
QComboBox::drop-down {{ subcontrol-origin:padding; subcontrol-position:center right; width:32px; border:0; }}
QComboBox::down-arrow {{ image:url("{icons['chevron_down']}"); width:12px; height:12px; }}
QComboBox QAbstractItemView {{
    background:#0f192c; color:{c['text']}; border:1px solid {c['line3']}; border-radius:8px;
    selection-background-color:#1a3a6e; selection-color:#ffffff; padding:5px; outline:0;
}}
QComboBox QAbstractItemView::item {{ min-height:28px; padding:4px 9px; border-radius:6px; }}
QDoubleSpinBox::up-button, QSpinBox::up-button, QDoubleSpinBox::down-button, QSpinBox::down-button {{
    width:22px; border:0; background:transparent;
}}
QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{ image:url("{icons['chevron_up']}"); width:10px; height:10px; }}
QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{ image:url("{icons['chevron_down']}"); width:10px; height:10px; }}

QCheckBox {{ spacing:10px; color:{c['text2']}; padding:4px 0; }}
QCheckBox:hover {{ color:#ffffff; }}
QCheckBox::indicator {{ width:18px; height:18px; border-radius:6px; border:1px solid #33496d; background:#0a1220; }}
QCheckBox::indicator:hover {{ border:1px solid {c['cyan']}; }}
QCheckBox::indicator:checked {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #3566f5, stop:1 #1fa3ee);
    border:1px solid #6aa0ff; image:url("{icons['check']}");
}}

/* ── Tablas ────────────────────────────────────────────── */
QTableWidget {{
    background:#0b1322; alternate-background-color:#0d1628; color:{c['text2']};
    border:1px solid {c['line2']}; border-radius:14px; gridline-color:transparent;
    selection-background-color:#173a70; selection-color:#ffffff; padding:4px;
}}
QTableWidget::item {{ padding:6px 10px; border-bottom:1px solid #121f35; }}
QTableWidget::item:hover {{ background:#10213f; }}
QTableWidget::item:selected {{ background:#173a70; color:#ffffff; }}
QHeaderView {{ background:transparent; }}
QHeaderView::section {{
    background:#0f1a2e; color:{c['muted']}; padding:12px 10px; border:0;
    border-bottom:1px solid {c['line2']}; font-size:10px; font-weight:800;
}}
QTableCornerButton::section {{ background:#0f1a2e; border:0; }}

/* ── Progreso ──────────────────────────────────────────── */
QProgressBar {{ background:#101c31; border:0; border-radius:5px; max-height:8px; min-height:8px; text-align:center; color:transparent; }}
QProgressBar::chunk {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['blue']}, stop:1 {c['cyan']}); border-radius:5px;
}}

/* ── Scrollbars ────────────────────────────────────────── */
QScrollBar:vertical {{ background:transparent; width:12px; margin:3px; }}
QScrollBar::handle:vertical {{ background:#26395a; min-height:34px; border-radius:3px; margin:0 3px; }}
QScrollBar::handle:vertical:hover {{ background:#3a5688; }}
QScrollBar:horizontal {{ background:transparent; height:12px; margin:3px; }}
QScrollBar::handle:horizontal {{ background:#26395a; min-width:34px; border-radius:3px; margin:3px 0; }}
QScrollBar::handle:horizontal:hover {{ background:#3a5688; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; background:none; border:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:none; }}

QStatusBar {{ background:#080d17; color:{c['muted']}; border-top:1px solid {c['line']}; font-size:11px; }}
QStatusBar::item {{ border:0; }}
QToolTip {{ background:#14233d; color:#f4f7ff; border:1px solid {c['line3']}; padding:7px 9px; border-radius:6px; }}
"""


def apply_palette(app) -> None:
    """Paleta Qt oscura para diálogos nativos, menús y controles sin estilo propio."""
    p = QPalette()
    p.setColor(QPalette.Window, QColor(C["bg1"]))
    p.setColor(QPalette.WindowText, QColor(C["text"]))
    p.setColor(QPalette.Base, QColor("#0a1220"))
    p.setColor(QPalette.AlternateBase, QColor("#0d1628"))
    p.setColor(QPalette.Text, QColor(C["text"]))
    p.setColor(QPalette.Button, QColor(C["surface2"]))
    p.setColor(QPalette.ButtonText, QColor(C["text"]))
    p.setColor(QPalette.ToolTipBase, QColor("#14233d"))
    p.setColor(QPalette.ToolTipText, QColor("#f4f7ff"))
    p.setColor(QPalette.Highlight, QColor(C["blue"]))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.PlaceholderText, QColor(C["dim"]))
    p.setColor(QPalette.Link, QColor(C["cyan"]))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(C["dim"]))
    app.setPalette(p)
