import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QUrl, QStandardPaths, QSize, QPropertyAnimation, QAbstractAnimation, QEasingCurve
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QProgressBar, QAbstractItemView,
    QFormLayout, QDoubleSpinBox, QCheckBox, QScrollArea, QLineEdit, QGridLayout,
    QGraphicsOpacityEffect
)

from app.config import EXPORTS_DIR, APP_VERSION, TEMP_DIR
from app.database.database import Database
from app.core.video_manager import VideoManager
from app.workers.analysis_worker import AnalysisWorker
from app.workers.live_clipping_worker import LiveClippingWorker
from app.ui.theme import C, build_stylesheet
from app.ui.icons import make_icon, ensure_style_assets
from app.ui.widgets import (
    Backdrop, LogoBadge, Eyebrow, StatusPill, EmptyTable, StatCard, StepCard, HeroBanner
)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.vm = VideoManager()
        self.current_project_id = None
        self.worker = None
        self.live_worker = None
        settings_root = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        settings_dir = Path(settings_root) if settings_root else (Path.home() / ".reelmaker")
        settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings = QSettings(str(settings_dir / "settings.ini"), QSettings.IniFormat)
        self.setWindowTitle("REELMAKER — AI Video Studio")
        self.resize(1480, 940)
        self.setMinimumSize(1120, 720)
        self.setStyleSheet(build_stylesheet(ensure_style_assets(TEMP_DIR / "ui")))
        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        central = Backdrop()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Menú lateral con el logo del proyecto ─────────────────────
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(262)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(16, 20, 16, 18)
        sl.setSpacing(0)

        self.logo_badge = LogoBadge(142)
        sl.addWidget(self.logo_badge, 0, Qt.AlignHCenter)
        sl.addSpacing(2)
        sl.addWidget(Eyebrow("LOCAL AI VIDEO STUDIO", "brandTag", 1.7), 0, Qt.AlignHCenter)
        sl.addSpacing(20)
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        sl.addWidget(divider)
        sl.addSpacing(18)
        sl.addWidget(Eyebrow("ESTUDIO", "navSection", 1.8))
        sl.addSpacing(8)

        self.stack = QStackedWidget()
        navs = [
            ("Dashboard", "dashboard", 0), ("Proyectos", "projects", 1),
            ("Directos y En vivos", "live", 2), ("Análisis IA", "analysis", 3),
            ("Editor de clips", "editor", 4), ("Exportaciones", "exports", 5),
            ("Configuración", "settings", 6)
        ]
        self.nav_buttons = []
        self.nav_icons = []
        for label, icon_name, index in navs:
            if index == 6:
                sl.addSpacing(12)
                sl.addWidget(Eyebrow("SISTEMA", "navSection", 1.8))
                sl.addSpacing(8)
            b = QPushButton("  " + label)
            b.setObjectName("nav")
            b.setCursor(Qt.PointingHandCursor)
            b.setIconSize(QSize(20, 20))
            idle = make_icon(icon_name, C["muted"], C["text"])
            active = make_icon(icon_name, C["cyan_hi"])
            self.nav_icons.append((idle, active))
            b.setIcon(active if index == 0 else idle)
            b.setProperty("active", index == 0)
            b.clicked.connect(lambda _, i=index: self.navigate(i))
            self.nav_buttons.append(b)
            sl.addWidget(b)
            sl.addSpacing(3)
        sl.addStretch()

        footer = QFrame()
        footer.setObjectName("sideFooter")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(14, 12, 14, 12)
        fl.setSpacing(10)
        dot = QLabel("●")
        dot.setObjectName("footDot")
        fl.addWidget(dot, 0, Qt.AlignVCenter)
        ftxt = QVBoxLayout()
        ftxt.setSpacing(1)
        ft = QLabel("Procesamiento local")
        ft.setObjectName("footTitle")
        fs = QLabel("Whisper + FFmpeg en tu equipo")
        fs.setObjectName("footSub")
        ftxt.addWidget(ft)
        ftxt.addWidget(fs)
        fl.addLayout(ftxt, 1)
        sl.addWidget(footer)
        root.addWidget(side)

        # ── Área principal ────────────────────────────────────────────
        body = QVBoxLayout()
        body.setContentsMargins(34, 22, 34, 20)
        body.setSpacing(14)
        top = QHBoxLayout()
        self.crumb = Eyebrow("WORKSPACE  ›  DASHBOARD", "crumb", 1.4)
        top.addWidget(self.crumb)
        top.addStretch()
        self.workspace_status = StatusPill("●  SISTEMA LISTO")
        top.addWidget(self.workspace_status)
        version = QLabel("v" + APP_VERSION)
        version.setObjectName("versionChip")
        top.addSpacing(10)
        top.addWidget(version)
        body.addLayout(top)
        root.addLayout(body, 1)
        body.addWidget(self.stack, 1)

        self.pages = [
            self.dashboard_page(), self.projects_page(), self.live_page(),
            self.analysis_page(), self.editor_page(), self.exports_page(),
            self.settings_page()
        ]
        for page in self.pages:
            self.stack.addWidget(page)

    def page_base(self, title, desc):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(14)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        description = QLabel(desc)
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(description)
        return page, layout

    def scrollable(self, page):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll

    def dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 6, 6, 6)
        layout.setSpacing(20)

        hero = HeroBanner()
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(38, 30, 280, 30)
        hl.setSpacing(8)
        hl.addStretch()
        hl.addWidget(Eyebrow("ESTUDIO DE VÍDEO CON IA  ·  100% LOCAL", "eyebrow", 1.8))
        hero_title = QLabel("Tu estudio creativo.")
        hero_title.setObjectName("heroTitle")
        hl.addWidget(hero_title)
        hero_text = QLabel("Convierte vídeos largos en clips verticales con análisis y transcripción local.")
        hero_text.setObjectName("heroText")
        hero_text.setWordWrap(True)
        hl.addWidget(hero_text)
        hl.addSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(10)
        import_btn = self.button("Importar vídeo", True, self.import_video)
        import_btn.setIcon(make_icon("plus", "#ffffff"))
        import_btn.setIconSize(QSize(18, 18))
        import_btn.setMinimumHeight(44)
        import_btn.setCursor(Qt.PointingHandCursor)
        open_btn = self.button("Abrir proyectos", False, lambda: self.navigate(1))
        open_btn.setMinimumHeight(44)
        open_btn.setCursor(Qt.PointingHandCursor)
        row.addWidget(import_btn)
        row.addWidget(open_btn)
        row.addStretch()
        hl.addLayout(row)
        hl.addStretch()
        layout.addWidget(hero)

        stats = QHBoxLayout()
        stats.setSpacing(16)
        self.stat_projects = StatCard("PROYECTOS", "0", "projects", C["blue"], "Vídeos de origen importados")
        self.stat_clips = StatCard("CLIPS", "0", "editor", C["cyan"], "Momentos detectados por la IA")
        self.stat_exports = StatCard("EXPORTADOS", "0", "exports", C["ok"], "Listos para publicar")
        for widget in (self.stat_projects, self.stat_clips, self.stat_exports):
            stats.addWidget(widget, 1)
        layout.addLayout(stats)

        flow_title = QLabel("Flujo de trabajo")
        flow_title.setObjectName("h2")
        layout.addWidget(flow_title)
        steps = QHBoxLayout()
        steps.setSpacing(14)
        for number, title, text, target in (
            ("01", "Importa", "Sube tu vídeo largo", 1),
            ("02", "Analiza", "Transcripción y momentos clave", 3),
            ("03", "Edita", "Ajusta título y tiempos", 4),
            ("04", "Exporta", "Clips MP4 listos para publicar", 5),
        ):
            steps.addWidget(StepCard(number, title, text, lambda t=target: self.navigate(t)), 1)
        layout.addLayout(steps)

        head = QHBoxLayout()
        recent_title = QLabel("Actividad reciente")
        recent_title.setObjectName("h2")
        head.addWidget(recent_title)
        head.addStretch()
        hint = QLabel("Doble clic para abrir Proyectos")
        hint.setObjectName("muted")
        head.addWidget(hint)
        layout.addLayout(head)
        self.recent = EmptyTable(0, 4, "Aún no hay proyectos. Importa tu primer vídeo para empezar.")
        self.recent.setMinimumHeight(230)
        self.setup_table(self.recent, ["Proyecto", "Vídeo", "Duración", "Estado"])
        self.recent.itemDoubleClicked.connect(lambda *_: self.navigate(1))
        layout.addWidget(self.recent)
        return self.scrollable(page)

    def projects_page(self):
        page, layout = self.page_base("Mis proyectos", "Importa y administra tus vídeos de origen.")
        bar = QHBoxLayout()
        bar.addWidget(self.button("+ Importar vídeo", True, self.import_video))
        bar.addWidget(self.button("Eliminar proyecto", False, self.delete_project))
        bar.addStretch()
        layout.addLayout(bar)
        self.projects_table = EmptyTable(0, 5, "No hay proyectos. Pulsa «Importar vídeo» para crear el primero.")
        self.setup_table(self.projects_table, ["ID", "Nombre", "Archivo de origen", "Duración", "Estado"])
        self.projects_table.itemSelectionChanged.connect(self.project_selected)
        self.projects_table.itemDoubleClicked.connect(lambda *_: self.navigate(3))
        layout.addWidget(self.projects_table)
        return page

    def live_page(self):
        page, layout = self.page_base(
            "Live Clipping",
            "Captura transmisiones en tiempo real y genera clips verticales, horizontales o cuadrados mientras el directo continúa."
        )

        intro = QFrame()
        intro.setObjectName("panel")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(20, 17, 20, 17)
        intro_layout.setSpacing(7)
        eyebrow = Eyebrow("CAPTURA INTELIGENTE  /  EN TIEMPO REAL", "eyebrow", 1.8)
        intro_layout.addWidget(eyebrow)
        intro_text = QLabel("Tu directo. Tus mejores momentos. En automático.")
        intro_text.setObjectName("liveHeadline")
        intro_layout.addWidget(intro_text)
        intro_hint = QLabel("Configura la fuente y el procesamiento. REELMAKER analizará cada segmento mientras la transmisión continúa.")
        intro_hint.setObjectName("muted")
        intro_hint.setWordWrap(True)
        intro_layout.addWidget(intro_hint)
        layout.addWidget(intro)

        config_panel = QFrame()
        config_panel.setObjectName("panel")
        panel_layout = QVBoxLayout(config_panel)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        panel_layout.setSpacing(15)
        panel_title = QLabel("Configuración de captura")
        panel_title.setObjectName("sectionTitle")
        panel_layout.addWidget(panel_title)

        # Grid layout keeps each label/control pair independent and prevents
        # the vertical overlap seen with QFormLayout on some Linux DPI setups.
        form = QGridLayout()
        form.setContentsMargins(0, 2, 0, 2)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(13)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)

        def add_live_field(row, column, title, widget, span=1):
            field = QWidget()
            field_layout = QVBoxLayout(field)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)
            caption = Eyebrow(title, "fieldCaption", 1.2)
            field_layout.addWidget(caption)
            widget.setMinimumHeight(40)
            field_layout.addWidget(widget)
            form.addWidget(field, row, column, 1, span)

        self.live_url_edit = QLineEdit()
        self.live_url_edit.setPlaceholderText("Pega aquí el enlace de YouTube, Twitch u otra plataforma compatible")
        add_live_field(0, 0, "ENLACE DE TRANSMISIÓN", self.live_url_edit, 2)

        self.live_cookie_combo = QComboBox()
        self.live_cookie_combo.addItem("No usar cookies", "")
        for label, browser in [
            ("Chrome", "chrome"), ("Edge", "edge"), ("Firefox", "firefox"),
            ("Brave", "brave"), ("Opera", "opera")
        ]:
            self.live_cookie_combo.addItem(label, browser)
        add_live_field(1, 0, "SESIÓN DEL NAVEGADOR", self.live_cookie_combo)

        self.live_segment_combo = QComboBox()
        for minutes in (2, 3, 5, 10):
            self.live_segment_combo.addItem(f"{minutes} minutos", minutes)
        self.live_segment_combo.setCurrentIndex(2)
        add_live_field(1, 1, "INTERVALO DE ANÁLISIS", self.live_segment_combo)

        self.live_duration_combo = QComboBox()
        for seconds in (15, 30, 45, 60, 90):
            self.live_duration_combo.addItem(f"{seconds} segundos", seconds)
        self.live_duration_combo.setCurrentIndex(1)
        add_live_field(2, 0, "DURACIÓN DE CADA CLIP", self.live_duration_combo)

        self.live_count_combo = QComboBox()
        for count in (1, 2, 3):
            self.live_count_combo.addItem(f"Hasta {count} por segmento", count)
        add_live_field(2, 1, "CLIPS POR SEGMENTO", self.live_count_combo)

        self.live_model_combo = QComboBox()
        for model in ("tiny", "base", "small"):
            self.live_model_combo.addItem(model.title(), model)
        self.live_model_combo.setCurrentIndex(1)
        add_live_field(3, 0, "MODELO DE TRANSCRIPCIÓN", self.live_model_combo)

        self.live_output_edit = QLineEdit(str(EXPORTS_DIR / "directos"))
        self.live_output_edit.setReadOnly(True)
        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)
        output_layout.addWidget(self.live_output_edit, 1)
        choose_button = self.button("Elegir carpeta…", False, self.choose_live_output)
        choose_button.setMinimumHeight(40)
        output_layout.addWidget(choose_button)
        add_live_field(3, 1, "CARPETA DE DESTINO", output_row)

        self.live_format_combo = QComboBox()
        self.live_format_combo.addItem("Vertical · 9:16 · 1080 × 1920", "vertical")
        self.live_format_combo.addItem("Horizontal · 16:9 · 1920 × 1080", "horizontal")
        self.live_format_combo.addItem("Cuadrado · 1:1 · 1080 × 1080", "square")
        saved_format = self.settings.value("live/output_format", "vertical")
        saved_index = self.live_format_combo.findData(saved_format)
        self.live_format_combo.setCurrentIndex(saved_index if saved_index >= 0 else 0)
        add_live_field(4, 0, "FORMATO DE LOS CLIPS", self.live_format_combo)

        options = QWidget()
        options_layout = QHBoxLayout(options)
        options_layout.setContentsMargins(0, 2, 0, 0)
        options_layout.setSpacing(24)
        self.live_subtitles_checkbox = QCheckBox("Incrustar subtítulos en los clips")
        self.live_subtitles_checkbox.setChecked(True)
        self.live_keep_segments_checkbox = QCheckBox("Conservar segmentos originales")
        self.live_keep_segments_checkbox.setChecked(False)
        options_layout.addWidget(self.live_subtitles_checkbox)
        options_layout.addWidget(self.live_keep_segments_checkbox)
        options_layout.addStretch()
        form.addWidget(options, 5, 0, 1, 2)

        panel_layout.addLayout(form)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.live_start_button = self.button("▶  Iniciar captura", True, self.start_live_capture)
        self.live_start_button.setMinimumHeight(43)
        self.live_stop_button = self.button("■  Detener y procesar", False, self.stop_live_capture)
        self.live_stop_button.setMinimumHeight(43)
        self.live_stop_button.setEnabled(False)
        actions.addWidget(self.live_start_button)
        actions.addWidget(self.live_stop_button)
        actions.addStretch()
        panel_layout.addLayout(actions)
        layout.addWidget(config_panel)

        monitor = QFrame()
        monitor.setObjectName("panel")
        monitor_layout = QVBoxLayout(monitor)
        monitor_layout.setContentsMargins(20, 17, 20, 18)
        monitor_layout.setSpacing(10)
        monitor_header = QHBoxLayout()
        monitor_title = QLabel("Monitor de transmisión")
        monitor_title.setObjectName("sectionTitle")
        monitor_header.addWidget(monitor_title)
        monitor_header.addStretch()
        self.live_indicator = StatusPill("●  EN ESPERA")
        monitor_header.addWidget(self.live_indicator)
        monitor_layout.addLayout(monitor_header)

        self.live_status_label = QLabel("Listo para iniciar. La captura y el análisis se ejecutan en segundo plano.")
        self.live_status_label.setWordWrap(True)
        self.live_status_label.setObjectName("liveStatus")
        monitor_layout.addWidget(self.live_status_label)
        self.live_activity_label = QLabel("Actividad: esperando que inicies una transmisión.")
        self.live_activity_label.setObjectName("muted")
        self.live_activity_label.setWordWrap(True)
        monitor_layout.addWidget(self.live_activity_label)

        clips_header = QHBoxLayout()
        clips_label = QLabel("Clips generados durante la transmisión")
        clips_label.setObjectName("sectionTitle")
        clips_header.addWidget(clips_label)
        clips_header.addStretch()
        self.live_clip_count_label = QLabel("0 clips")
        self.live_clip_count_label.setObjectName("muted")
        clips_header.addWidget(self.live_clip_count_label)
        monitor_layout.addLayout(clips_header)

        self.live_clips_table = EmptyTable(0, 4, "Los clips aparecerán aquí a medida que se cierren los segmentos.")
        self.setup_table(self.live_clips_table, ["#", "Momento detectado", "Puntuación", "Archivo generado"])
        self.live_clips_table.setMinimumHeight(175)
        self.live_clips_table.itemDoubleClicked.connect(self.open_live_clip)
        monitor_layout.addWidget(self.live_clips_table)
        note = QLabel(
            "El análisis se realiza por segmentos cerrados. Los directos privados, protegidos o restringidos "
            "pueden no estar disponibles. El rendimiento depende de la velocidad de Whisper y del espacio libre."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        monitor_layout.addWidget(note)
        layout.addWidget(monitor)
        layout.addStretch(1)

        live_scroll = QScrollArea()
        live_scroll.setWidgetResizable(True)
        live_scroll.setFrameShape(QFrame.NoFrame)
        live_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        live_scroll.setWidget(page)
        return live_scroll

    def choose_live_output(self):
        current = self.live_output_edit.text().strip() or str(EXPORTS_DIR)
        folder = QFileDialog.getExistingDirectory(self, "Carpeta para clips en vivo", current)
        if folder:
            self.live_output_edit.setText(folder)

    def start_live_capture(self):
        url = self.live_url_edit.text().strip()
        if not url.lower().startswith(("http://", "https://")):
            QMessageBox.warning(self, "Enlace requerido", "Pega un enlace válido que comience por http:// o https://.")
            return
        if self.live_worker and self.live_worker.isRunning():
            QMessageBox.information(self, "Captura activa", "Ya hay una captura en curso.")
            return

        output = self.live_output_edit.text().strip() or str(EXPORTS_DIR / "directos")
        self.live_clips_table.setRowCount(0)
        self.live_start_button.setEnabled(False)
        self.live_stop_button.setEnabled(True)
        self.live_status_label.setText("Conectando con la plataforma…")
        self.live_activity_label.setText("Preparando la sesión, verificando formatos disponibles e iniciando la captura.")
        self.workspace_status.setText("●  CAPTURA EN PREPARACIÓN")
        self.live_indicator.setText("●  CONECTANDO")
        self.live_worker = LiveClippingWorker(
            stream_url=url,
            output_dir=output,
            model_size=self.live_model_combo.currentData(),
            segment_minutes=int(self.live_segment_combo.currentData()),
            clip_duration=int(self.live_duration_combo.currentData()),
            clips_per_segment=int(self.live_count_combo.currentData()),
            browser_cookies=self.live_cookie_combo.currentData(),
            keep_segments=self.live_keep_segments_checkbox.isChecked(),
            subtitles=self.live_subtitles_checkbox.isChecked(),
            output_format=self.live_format_combo.currentData()
        )
        self.settings.setValue("live/output_format", self.live_format_combo.currentData())
        self.live_worker.status.connect(self.live_status_label.setText)
        self.live_worker.status.connect(self.live_activity_label.setText)
        self.live_worker.clip_generated.connect(self.live_clip_added)
        self.live_worker.failed.connect(self.live_capture_failed)
        self.live_worker.finished_summary.connect(self.live_capture_finished)
        self.live_worker.start()

    def stop_live_capture(self):
        if self.live_worker and self.live_worker.isRunning():
            self.live_stop_button.setEnabled(False)
            self.live_status_label.setText("Deteniendo FFmpeg y procesando el último segmento…")
            self.live_worker.request_stop()

    def live_clip_added(self, path, title, score):
        row = self.live_clips_table.rowCount()
        self.live_clips_table.insertRow(row)
        values = [str(row + 1), title, f"{score:.1f}", Path(path).name]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 3:
                item.setData(Qt.UserRole, path)
            self.live_clips_table.setItem(row, column, item)
        self.live_status_label.setText(f"Clip generado correctamente: {Path(path).name}")
        self.live_activity_label.setText(f"Actividad: {row + 1} clip(s) guardados durante esta transmisión.")
        self.live_clip_count_label.setText(f"{row + 1} clips")
        self.live_indicator.setText("●  CAPTURANDO")

    def open_live_clip(self, item):
        row = item.row()
        path_item = self.live_clips_table.item(row, 3)
        path = path_item.data(Qt.UserRole) if path_item else None
        if path and Path(path).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))
        else:
            QMessageBox.warning(self, "Archivo no encontrado", "El clip ya no está disponible en esa ubicación.")

    def live_capture_failed(self, error):
        self.workspace_status.setText("●  ATENCIÓN REQUERIDA")
        self.live_start_button.setEnabled(True)
        self.live_stop_button.setEnabled(False)
        self.live_indicator.setText("●  ERROR")
        self.live_clip_count_label.setText(f"{self.live_clips_table.rowCount()} clips")
        self.live_status_label.setText("La captura terminó con un error.")
        self.live_activity_label.setText("Diagnóstico: revisa el mensaje de error y el registro FFmpeg de la sesión.")
        QMessageBox.critical(self, "Error en Directos y En vivos", error)

    def live_capture_finished(self, count, message):
        self.workspace_status.setText("●  SISTEMA LISTO")
        self.live_start_button.setEnabled(True)
        self.live_stop_button.setEnabled(False)
        self.live_indicator.setText("●  FINALIZADO")
        self.live_clip_count_label.setText(f"{self.live_clips_table.rowCount()} clips")
        self.live_status_label.setText(f"{message} Clips generados: {count}.")
        self.live_activity_label.setText(f"Actividad finalizada. Clips generados: {count}.")
        self.statusBar().showMessage(f"Live Clipping: {count} clip(s) generados.", 10000)

    def analysis_page(self):
        page, layout = self.page_base(
            "Análisis inteligente",
            "Selecciona aquí el proyecto que quieres analizar. La primera ejecución descarga el modelo Whisper."
        )
        bar = QHBoxLayout()
        self.analysis_project_combo = QComboBox()
        self.analysis_project_combo.setMinimumWidth(300)
        self.analysis_project_combo.currentIndexChanged.connect(self.analysis_project_changed)
        bar.addWidget(QLabel("Proyecto:"))
        bar.addWidget(self.analysis_project_combo)
        bar.addWidget(self.button("Actualizar lista", False, self.refresh_project_selectors))
        bar.addWidget(self.button("Analizar proyecto", True, self.analyze_project))
        layout.addLayout(bar)
        self.analysis_status = QLabel("Selecciona un proyecto para comenzar.")
        self.analysis_status.setObjectName("muted")
        layout.addWidget(self.analysis_status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        layout.addWidget(QLabel("Transcripción del proyecto"))
        self.transcript_table = EmptyTable(0, 3, "Analiza un proyecto para ver su transcripción.")
        self.setup_table(self.transcript_table, ["Inicio", "Fin", "Transcripción"])
        layout.addWidget(self.transcript_table)
        return page

    def editor_page(self):
        page, layout = self.page_base(
            "Editor de clips",
            "Selecciona un proyecto para editar los clips detectados. Modifica título, inicio y final y guarda."
        )
        bar = QHBoxLayout()
        self.editor_project_combo = QComboBox()
        self.editor_project_combo.setMinimumWidth(300)
        self.editor_project_combo.currentIndexChanged.connect(self.editor_project_changed)
        bar.addWidget(QLabel("Proyecto:"))
        bar.addWidget(self.editor_project_combo)
        bar.addWidget(self.button("Recargar clips", False, self.load_clips))
        layout.addLayout(bar)
        layout.addWidget(QLabel("Los tiempos se expresan en segundos y deben estar dentro de la duración del vídeo."))
        self.clips_table = EmptyTable(0, 5, "No hay clips. Analiza un proyecto para detectar momentos.")
        self.setup_table(self.clips_table, ["ID", "Título", "Inicio (s)", "Fin (s)", "Puntuación"])
        self.clips_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        layout.addWidget(self.clips_table)
        actions = QHBoxLayout()
        actions.addWidget(self.button("Guardar cambios", True, self.save_clips))
        actions.addWidget(self.button("Exportar clip seleccionado", False, self.export_selected))
        actions.addWidget(self.button("Exportar todos", False, self.export_all))
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def exports_page(self):
        page, layout = self.page_base(
            "Exportaciones",
            "Consulta los clips exportados. Los archivos MP4 verticales se guardan en la carpeta exports."
        )
        bar = QHBoxLayout()
        self.exports_project_combo = QComboBox()
        self.exports_project_combo.setMinimumWidth(300)
        self.exports_project_combo.currentIndexChanged.connect(self.load_exports)
        bar.addWidget(QLabel("Proyecto:"))
        bar.addWidget(self.exports_project_combo)
        bar.addWidget(self.button("Actualizar", False, self.load_exports))
        bar.addWidget(self.button("Abrir carpeta", True, self.open_exports))
        layout.addLayout(bar)
        self.exports_table = EmptyTable(0, 4, "Todavía no se ha exportado ningún clip.")
        self.setup_table(self.exports_table, ["Clip ID", "Título", "Archivo", "Estado"])
        self.exports_table.itemDoubleClicked.connect(self.open_export_file)
        layout.addWidget(self.exports_table)
        return page

    def settings_page(self):
        page, layout = self.page_base(
            "Configuración avanzada",
            "Personaliza el análisis, la generación de clips, el audio y la publicación de tus vídeos."
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(30)
        form.setVerticalSpacing(15)

        def combo(key, options, default):
            widget = QComboBox()
            for label, value in options:
                widget.addItem(label, value)
            saved = self.settings.value(key, default)
            index = widget.findData(saved)
            widget.setCurrentIndex(index if index >= 0 else max(0, widget.findData(default)))
            return widget

        self.model_combo = combo("whisper_model", [(x.title(), x) for x in ("tiny","base","small")], "base")
        self.clip_duration_combo = combo("clip_duration", [(f"{x} segundos",x) for x in (15,30,45,60,90)], 30)
        self.clip_count_combo = combo("clip_count", [(f"{x} clips",x) for x in (1,5,10,15,20,30,40,50)], 10)
        self.subtitles_checkbox = QCheckBox("Incrustar subtítulos sincronizados")
        self.subtitles_checkbox.setChecked(self.settings.value("include_subtitles", True, type=bool))

        self.aspect_combo = combo("aspect_ratio", [
            ("9:16 · Vertical", "9:16"), ("16:9 · Horizontal", "16:9"), ("1:1 · Cuadrado", "1:1")
        ], "9:16")
        self.resolution_combo = combo("resolution", [
            ("Full HD · 1080 px", "1080"), ("HD · 720 px", "720"), ("Baja · 480 px", "480")
        ], "1080")
        self.audio_combo = combo("audio_mode", [
            ("Conservar audio original", "original"), ("Normalizar volumen", "normalize"), ("Exportar sin audio", "none")
        ], "original")
        self.audio_quality_combo = combo("audio_quality", [
            ("Económica · 96 kbps", "96k"), ("Estándar · 128 kbps", "128k"), ("Alta · 192 kbps", "192k"), ("Máxima · 256 kbps", "256k")
        ], "128k")
        self.performance_combo = combo("performance", [
            ("Rápido", "fast"), ("Equilibrado", "balanced"), ("Máxima calidad", "quality"), ("Optimizado para CPU", "cpu")
        ], "cpu")
        self.format_combo = combo("output_format", [("MP4 · recomendado", "mp4"), ("MKV", "mkv")], "mp4")
        self.folder_edit = QLineEdit(str(self.settings.value("export_folder", str(EXPORTS_DIR))))
        self.folder_edit.setReadOnly(True)
        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0,0,0,0)
        folder_layout.addWidget(self.folder_edit, 1)
        folder_layout.addWidget(self.button("Examinar…", False, self.choose_export_folder))
        self.organize_checkbox = QCheckBox("Crear una subcarpeta para cada proyecto")
        self.organize_checkbox.setChecked(self.settings.value("organize_by_project", True, type=bool))
        originals_note = QLabel("Los vídeos originales siempre se conservan; REELMAKER no los elimina.")
        originals_note.setObjectName("muted")
        originals_note.setWordWrap(True)
        self.overwrite_combo = combo("existing_files", [
            ("Renombrar archivos existentes", "rename"), ("Sobrescribir archivos existentes", "overwrite")
        ], "rename")

        for label, widget in [
            ("Modelo de inteligencia artificial (Whisper):", self.model_combo),
            ("Duración de cada clip:", self.clip_duration_combo),
            ("Cantidad máxima de clips:", self.clip_count_combo),
            ("Subtítulos:", self.subtitles_checkbox),
            ("Formato y orientación:", self.aspect_combo),
            ("Resolución:", self.resolution_combo),
            ("Audio:", self.audio_combo),
            ("Calidad del audio:", self.audio_quality_combo),
            ("Rendimiento:", self.performance_combo),
            ("Formato de archivo:", self.format_combo),
            ("Carpeta de exportación:", folder_row),
            ("Organización:", self.organize_checkbox),
            ("Vídeos originales:", originals_note),
            ("Si el archivo ya existe:", self.overwrite_combo)
        ]:
            form.addRow(label, widget)

        note = QLabel(
            "Las preferencias se guardan en el equipo y se aplican a los siguientes análisis y exportaciones. "
            "El procesamiento de Whisper se realiza localmente en CPU. La opción de conservar originales "
            "evita que REELMAKER elimine el vídeo fuente."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        inner = QVBoxLayout(content)
        inner.setContentsMargins(0, 4, 8, 14)
        inner.setSpacing(16)
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.addLayout(form)
        inner.addWidget(panel)
        inner.addWidget(note)
        save_btn = self.button("Guardar configuración", True, self.save_settings)
        save_btn.setMinimumHeight(42)
        inner.addWidget(save_btn, 0, Qt.AlignLeft)
        inner.addStretch()
        # Persistencia automática: los cambios sobreviven al cierre de la aplicación.
        for widget in (self.model_combo, self.clip_duration_combo, self.clip_count_combo,
                       self.aspect_combo, self.resolution_combo, self.audio_combo,
                       self.audio_quality_combo, self.performance_combo, self.format_combo,
                       self.overwrite_combo):
            widget.currentIndexChanged.connect(lambda *_: self.save_settings(show_message=False))
        for widget in (self.subtitles_checkbox, self.organize_checkbox):
            widget.toggled.connect(lambda *_: self.save_settings(show_message=False))
        self.folder_edit.textChanged.connect(lambda *_: self.save_settings(show_message=False))
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def choose_export_folder(self):
        current = self.folder_edit.text().strip() or str(EXPORTS_DIR)
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de exportación", current)
        if folder:
            self.folder_edit.setText(folder)

    def button(self, text, primary, callback):
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        return button

    def stat(self, title, value):
        return StatCard(title, value, "projects", C["blue"])

    def setup_table(self, table, headers):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels([h.upper() for h in headers])
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.setShowGrid(False)

    def combo_project_id(self, combo):
        value = combo.currentData()
        return int(value) if value is not None else None

    def set_combo_project(self, combo, project_id):
        index = combo.findData(project_id)
        if index >= 0:
            combo.setCurrentIndex(index)

    def refresh_project_selectors(self):
        projects = self.db.get_projects()
        combos = [
            getattr(self, "analysis_project_combo", None),
            getattr(self, "editor_project_combo", None),
            getattr(self, "exports_project_combo", None)
        ]
        for combo in combos:
            if combo is None:
                continue
            previous = self.combo_project_id(combo)
            combo.blockSignals(True)
            combo.clear()
            for project in projects:
                label = f'#{project["id"]} · {project["name"]}'
                combo.addItem(label, int(project["id"]))
            target = previous if previous is not None else self.current_project_id
            if target is not None:
                self.set_combo_project(combo, target)
            if combo.count() and combo.currentIndex() < 0:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

        if self.analysis_project_combo.count():
            self.analysis_project_changed()
        if self.editor_project_combo.count():
            self.editor_project_changed()
        if self.exports_project_combo.count():
            self.load_exports()

    def navigate(self, index):
        previous = self.stack.currentIndex()
        self.stack.setCurrentIndex(index)
        for nav_index, nav_button in enumerate(self.nav_buttons):
            is_active = nav_index == index
            nav_button.setProperty("active", is_active)
            nav_button.setIcon(self.nav_icons[nav_index][1 if is_active else 0])
            nav_button.style().unpolish(nav_button)
            nav_button.style().polish(nav_button)
        names = ["DASHBOARD", "PROJECTS", "LIVE CLIPPING", "AI ANALYSIS",
                 "CLIP EDITOR", "EXPORTS", "SETTINGS"]
        self.crumb.setText("WORKSPACE  ›  " + names[index])
        if index != previous:
            self.fade_in(self.stack.currentWidget())
        if index in (0, 1):
            self.refresh_all()
        elif index == 3:
            self.refresh_project_selectors()
            self.analysis_project_changed()
        elif index == 4:
            self.refresh_project_selectors()
            self.load_clips()
        elif index == 5:
            self.refresh_project_selectors()
            self.load_exports()

    def fade_in(self, widget):
        """Transición suave de entrada al cambiar de sección."""
        try:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", widget)
            anim.setDuration(240)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
            anim.start(QAbstractAnimation.DeleteWhenStopped)
            self._fade_anim = anim
        except Exception:
            widget.setGraphicsEffect(None)

    def refresh_all(self):
        projects = self.db.get_projects()
        clips = self.db.get_clips()
        self.stat_projects.value_label.setText(str(len(projects)))
        self.stat_clips.value_label.setText(str(len(clips)))
        self.stat_exports.value_label.setText(str(sum(1 for clip in clips if clip["status"] == "exported")))
        self.fill_projects(self.projects_table, projects)
        self.fill_projects(self.recent, projects[:8], recent=True)
        self.refresh_project_selectors()

    def fill_projects(self, table, projects, recent=False):
        table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            values = [
                str(project["id"]), project["name"],
                Path(project["source_video"] or "").name,
                self.vm.format_duration(project["duration"]), project["status"]
            ]
            if recent:
                values = [
                    project["name"], Path(project["source_video"] or "").name,
                    self.vm.format_duration(project["duration"]), project["status"]
                ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, int(project["id"]))
                table.setItem(row, col, item)

    def import_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar vídeo", "",
            "Vídeos (*.mp4 *.mov *.mkv *.avi *.webm *.m4v)"
        )
        if not path:
            return
        try:
            info = self.vm.inspect_video(path)
            project_id = self.db.create_project(
                Path(path).stem, info["path"], info["duration"],
                info["resolution"], info["fps"]
            )
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo importar", str(exc))
            return
        self.current_project_id = project_id
        self.refresh_all()
        self.set_combo_project(self.analysis_project_combo, project_id)
        self.set_combo_project(self.editor_project_combo, project_id)
        self.set_combo_project(self.exports_project_combo, project_id)
        QMessageBox.information(
            self, "Proyecto creado",
            f"Proyecto #{project_id}\n{info['name']}\n"
            f"{info['resolution']} · {self.vm.format_duration(info['duration'])}"
        )
        self.navigate(1)

    def selected_project_id(self):
        row = self.projects_table.currentRow()
        if row >= 0:
            item = self.projects_table.item(row, 0)
            if item:
                return int(item.text())
        return self.current_project_id

    def project_selected(self):
        project_id = self.selected_project_id()
        if project_id:
            self.current_project_id = project_id
            self.refresh_project_selectors()

    def delete_project(self):
        project_id = self.selected_project_id()
        if not project_id:
            QMessageBox.warning(self, "Selecciona un proyecto", "Selecciona primero un proyecto.")
            return
        answer = QMessageBox.question(
            self, "Eliminar proyecto",
            "¿Eliminar el proyecto y sus transcripciones y clips?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return
        self.db.delete_project(project_id)
        if self.current_project_id == project_id:
            self.current_project_id = None
        self.refresh_all()

    def analysis_project_changed(self, *_):
        project_id = self.combo_project_id(self.analysis_project_combo)
        self.current_project_id = project_id
        if not project_id:
            self.analysis_status.setText("No hay proyectos. Importa un vídeo desde Proyectos.")
            self.transcript_table.setRowCount(0)
            return
        project = self.db.get_project(project_id)
        if project:
            self.analysis_status.setText(
                f'Proyecto seleccionado: {project["name"]} · '
                f'{self.vm.format_duration(project["duration"])}'
            )
            self.load_transcript(project_id)

    def editor_project_changed(self, *_):
        project_id = self.combo_project_id(self.editor_project_combo)
        if project_id:
            self.current_project_id = project_id
        self.load_clips()

    def analyze_project(self):
        project_id = self.combo_project_id(self.analysis_project_combo)
        if not project_id:
            QMessageBox.warning(
                self, "Proyecto requerido",
                "No hay proyectos disponibles. Ve a Proyectos e importa un vídeo primero."
            )
            return
        project = self.db.get_project(project_id)
        if not project or not project["source_video"] or not Path(project["source_video"]).is_file():
            QMessageBox.warning(self, "Vídeo no disponible", "No se encuentra el archivo de vídeo original.")
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Análisis en curso", "Espera a que termine el análisis actual.")
            return
        self.save_settings(show_message=False)
        model_size = self.model_combo.currentData()
        clip_duration = int(self.clip_duration_combo.currentData())
        clip_count = int(self.clip_count_combo.currentData())
        self.current_project_id = project_id
        self.progress.show()
        self.analysis_status.setText(f'Iniciando análisis de "{project["name"]}" con Whisper {model_size}…')
        self.worker = AnalysisWorker(
            project["source_video"], model_size,
            clip_duration=clip_duration, clip_count=clip_count
        )
        self.worker.progress.connect(self.analysis_status.setText)
        self.worker.completed.connect(
            lambda transcript, clips, pid=project_id: self.analysis_done(pid, transcript, clips)
        )
        self.worker.failed.connect(self.analysis_failed)
        self.worker.start()

    def analysis_done(self, project_id, transcript, clips):
        try:
            self.db.save_transcript(project_id, transcript)
            self.db.save_clips(project_id, clips)
            self.current_project_id = project_id
            self.progress.hide()
            self.analysis_status.setText(
                f"Análisis terminado: {len(transcript)} segmentos y {len(clips)} clips sugeridos."
            )
            self.load_transcript(project_id)
            self.set_combo_project(self.editor_project_combo, project_id)
            self.load_clips()
            self.refresh_all()
            self.set_combo_project(self.analysis_project_combo, project_id)
            QMessageBox.information(
                self, "Análisis completado",
                f"Se guardaron {len(transcript)} segmentos de transcripción "
                f"y {len(clips)} clips sugeridos.\nRevisa el Editor de clips."
            )
        except Exception as exc:
            self.progress.hide()
            QMessageBox.critical(self, "Error guardando el análisis", str(exc))

    def analysis_failed(self, error):
        self.progress.hide()
        self.analysis_status.setText("El análisis no pudo completarse.")
        QMessageBox.critical(self, "Error de análisis", error)

    def load_transcript(self, project_id=None):
        project_id = project_id or self.combo_project_id(self.analysis_project_combo)
        rows = self.db.get_transcript(project_id) if project_id else []
        self.transcript_table.setRowCount(len(rows))
        for row, segment in enumerate(rows):
            values = [
                self.vm.format_duration(segment["start_time"]),
                self.vm.format_duration(segment["end_time"]),
                segment["text"]
            ]
            for col, value in enumerate(values):
                self.transcript_table.setItem(row, col, QTableWidgetItem(str(value)))

    def load_clips(self, *_):
        project_id = self.combo_project_id(self.editor_project_combo)
        if project_id:
            self.current_project_id = project_id
        rows = self.db.get_clips(project_id) if project_id else []
        self.clips_table.setRowCount(len(rows))
        for row, clip in enumerate(rows):
            values = [clip["id"], clip["title"], clip["start_time"], clip["end_time"], clip["score"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.clips_table.setItem(row, col, item)
                if col in (0, 4):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        if not project_id:
            self.clips_table.setRowCount(0)

    def save_clips(self):
        project_id = self.combo_project_id(self.editor_project_combo)
        if not project_id:
            QMessageBox.warning(self, "Proyecto requerido", "Selecciona un proyecto.")
            return
        project = self.db.get_project(project_id)
        try:
            for row in range(self.clips_table.rowCount()):
                clip_id = int(self.clips_table.item(row, 0).text())
                title = self.clips_table.item(row, 1).text().strip()
                start = float(self.clips_table.item(row, 2).text())
                end = float(self.clips_table.item(row, 3).text())
                if not title:
                    raise ValueError(f"El título de la fila {row + 1} está vacío.")
                if start < 0 or end <= start or end > float(project["duration"]) + 0.1:
                    raise ValueError(f"Tiempos inválidos en la fila {row + 1}.")
                self.db.update_clip(clip_id, title, start, end)
            QMessageBox.information(self, "Guardado", "Los cambios de los clips se guardaron.")
            self.load_clips()
            self.refresh_all()
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo guardar", str(exc))

    def export_rows(self, rows, project_id=None):
        project_id = project_id or self.combo_project_id(self.editor_project_combo)
        if not rows:
            QMessageBox.information(self, "Sin clips", "No hay clips para exportar.")
            return
        project = self.db.get_project(project_id) if project_id else None
        if not project:
            QMessageBox.warning(self, "Proyecto", "Selecciona un proyecto.")
            return
        source = project["source_video"]
        if not source or not Path(source).is_file():
            QMessageBox.warning(self, "Vídeo no disponible", "No se encuentra el vídeo original.")
            return
        self.save_settings(show_message=False)
        export_root = Path(self.folder_edit.text()).expanduser()
        if self.organize_checkbox.isChecked():
            export_root = export_root / f"proyecto_{project_id}_{''.join(c if c.isalnum() or c in '-_' else '_' for c in project['name'])[:40]}"
        export_root.mkdir(parents=True, exist_ok=True)
        transcript = self.db.get_transcript(project_id)
        exported = []
        self.setEnabled(False)
        try:
            for clip in rows:
                safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (clip["title"] or "clip"))[:35]
                extension = self.format_combo.currentData()
                filename = f"proyecto_{project_id}_clip_{clip['id']}_{safe}.{extension}"
                output = export_root / filename
                if output.exists() and self.overwrite_combo.currentData() == "rename":
                    stem, suffix, number = output.stem, output.suffix, 2
                    while output.exists():
                        output = output.with_name(f"{stem}_{number}{suffix}")
                        number += 1
                start, end = float(clip["start_time"]), float(clip["end_time"])
                subtitle_path = export_root / f".clip_{clip['id']}.srt"
                subtitle_lines = []
                def stamp(seconds):
                    ms = int(max(0, seconds) * 1000)
                    hours, rem = divmod(ms, 3600000)
                    minutes, rem = divmod(rem, 60000)
                    sec, millis = divmod(rem, 1000)
                    return f"{hours:02}:{minutes:02}:{sec:02},{millis:03}"
                subtitle_arg = None
                if self.subtitles_checkbox.isChecked():
                    for segment in transcript:
                        a, b = max(start, float(segment["start_time"])), min(end, float(segment["end_time"]))
                        if b > a:
                            subtitle_lines.extend([str(len(subtitle_lines)//4+1), f"{stamp(a-start)} --> {stamp(b-start)}", segment["text"], ""])
                    if subtitle_lines:
                        subtitle_path.write_text("\n".join(subtitle_lines), encoding="utf-8")
                        subtitle_arg = subtitle_path
                try:
                    aspect = self.aspect_combo.currentData()
                    base = int(self.resolution_combo.currentData())
                    if aspect == "9:16":
                        width, height = {1080: (1080,1920), 720: (720,1280), 480: (480,854)}[base]
                    elif aspect == "16:9":
                        width, height = {1080: (1920,1080), 720: (1280,720), 480: (854,480)}[base]
                    else:
                        width, height = (base, base)
                    width += width % 2
                    height += height % 2
                    self.statusBar().showMessage(f"Exportando {output.name}…")
                    path = self.vm.export_clip(
                        source, output, start, end, width=width, height=height,
                        subtitle_file=subtitle_arg, audio_mode=self.audio_combo.currentData(),
                        audio_bitrate=self.audio_quality_combo.currentData(),
                        performance=self.performance_combo.currentData()
                    )
                    self.db.mark_clip_exported(clip["id"], path)
                    exported.append(path)
                finally:
                    if subtitle_path.exists():
                        subtitle_path.unlink()
            self.statusBar().showMessage(f"Exportación completada: {len(exported)} clip(s).", 10000)
            self.refresh_all()
            self.load_exports()
            QMessageBox.information(self, "Exportación completada", f"Se exportaron {len(exported)} clip(s) en:\n{export_root}")
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc))[-4000:]
            QMessageBox.critical(self, "Error de FFmpeg", detail)
        except Exception as exc:
            QMessageBox.critical(self, "Error de exportación", str(exc))
        finally:
            self.setEnabled(True)

    def export_selected(self):
        project_id = self.combo_project_id(self.editor_project_combo)
        row = self.clips_table.currentRow()
        if not project_id:
            QMessageBox.warning(self, "Proyecto requerido", "Selecciona un proyecto.")
            return
        if row < 0:
            QMessageBox.warning(self, "Selecciona un clip", "Selecciona un clip de la tabla.")
            return
        clip_id = int(self.clips_table.item(row, 0).text())
        clip = next((item for item in self.db.get_clips(project_id) if item["id"] == clip_id), None)
        if clip:
            self.export_rows([clip], project_id)

    def export_all(self):
        project_id = self.combo_project_id(self.editor_project_combo)
        rows = self.db.get_clips(project_id) if project_id else []
        self.export_rows(rows, project_id)

    def load_exports(self, *_):
        project_id = self.combo_project_id(self.exports_project_combo)
        rows = [
            clip for clip in (self.db.get_clips(project_id) if project_id else [])
            if clip["status"] == "exported" and clip["output_path"]
        ]
        self.exports_table.setRowCount(len(rows))
        for row, clip in enumerate(rows):
            values = [clip["id"], clip["title"], clip["output_path"], "Completado"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 2:
                    item.setData(Qt.UserRole, clip["output_path"])
                self.exports_table.setItem(row, col, item)

    def open_export_file(self, item):
        row = item.row()
        path_item = self.exports_table.item(row, 2)
        path = path_item.data(Qt.UserRole) if path_item else None
        if path and Path(path).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            QMessageBox.warning(self, "Archivo no encontrado", "El vídeo exportado ya no existe en esa ubicación.")

    def save_settings(self, show_message=True):
        values = {
            "whisper_model": self.model_combo.currentData(),
            "clip_duration": int(self.clip_duration_combo.currentData()),
            "clip_count": int(self.clip_count_combo.currentData()),
            "include_subtitles": self.subtitles_checkbox.isChecked(),
            "aspect_ratio": self.aspect_combo.currentData(),
            "resolution": self.resolution_combo.currentData(),
            "audio_mode": self.audio_combo.currentData(),
            "audio_quality": self.audio_quality_combo.currentData(),
            "performance": self.performance_combo.currentData(),
            "output_format": self.format_combo.currentData(),
            "export_folder": self.folder_edit.text().strip() or str(EXPORTS_DIR),
            "organize_by_project": self.organize_checkbox.isChecked(),
            "existing_files": self.overwrite_combo.currentData()
        }
        try:
            for key, value in values.items():
                self.settings.setValue(key, value)
            self.settings.sync()
            if self.settings.status() != QSettings.NoError:
                raise OSError("Qt no pudo escribir el archivo de configuración.")
        except Exception as exc:
            QMessageBox.critical(
                self, "No se pudo guardar", f"No fue posible guardar la configuración:\n{exc}"
            )
            return False
        if show_message:
            QMessageBox.information(self, "Configuración", "Todas las preferencias se guardaron correctamente.")
        return True

    def open_exports(self):
        folder = Path(self.settings.value("export_folder", str(EXPORTS_DIR))).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def closeEvent(self, event):
        if self.live_worker and self.live_worker.isRunning():
            QMessageBox.warning(
                self, "Captura en vivo activa",
                "Detén la captura y espera a que se procese el último segmento antes de cerrar REELMAKER."
            )
            event.ignore()
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(
                self, "Análisis en curso",
                "Espera a que termine el análisis antes de cerrar la aplicación."
            )
            event.ignore()
            return
        self.db.close()
        event.accept()
