import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QProgressBar, QAbstractItemView,
    QFormLayout, QDoubleSpinBox, QCheckBox, QScrollArea, QLineEdit
)

from app.config import EXPORTS_DIR, APP_VERSION
from app.database.database import Database
from app.core.video_manager import VideoManager
from app.workers.analysis_worker import AnalysisWorker


STYLE = """
QMainWindow,QWidget#central{background:#0b0f17;color:#edf2fa;font-family:'Inter','Segoe UI',sans-serif}
QFrame#sidebar{background:#101725;border-right:1px solid #263247}
QLabel#logo{font-size:24px;font-weight:900;color:#fff}
QLabel#muted{color:#91a0b7;font-size:12px}
QLabel#title{font-size:28px;font-weight:800;color:#fff}
QPushButton{background:#1b2638;color:#e3eaf5;border:1px solid #30405a;border-radius:8px;padding:10px 14px}
QPushButton:hover{background:#293852}
QPushButton#primary{background:#7657f6;border:0;color:white;font-weight:700}
QPushButton#danger{background:#612b39;border:0;color:white}
QPushButton#nav{background:transparent;border:0;text-align:left;padding:13px;color:#b3c0d3}
QPushButton#nav:hover{background:#202d42;color:white}
QFrame#card{background:#131d2b;border:1px solid #26364c;border-radius:12px}
QTableWidget{background:#111a28;alternate-background-color:#162235;border:1px solid #2a3a51;gridline-color:#29384d;border-radius:8px}
QHeaderView::section{background:#1b293d;color:#cbd7e8;padding:8px;border:0}
QLineEdit,QComboBox,QDoubleSpinBox{background:#111a28;color:#fff;border:1px solid #34445c;border-radius:7px;padding:8px}
QComboBox QAbstractItemView{background:#111a28;color:#fff;selection-background-color:#7657f6}
QProgressBar{background:#1b293d;border:0;border-radius:5px;height:12px;text-align:center}
QProgressBar::chunk{background:#8065fa;border-radius:5px}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.vm = VideoManager()
        self.current_project_id = None
        self.worker = None
        self.settings = QSettings("ReelMaker", "ReelMaker")
        self.setWindowTitle("REELMAKER — AI Video Studio")
        self.resize(1420, 900)
        self.setMinimumSize(1050, 680)
        self.setStyleSheet(STYLE)
        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(225)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(18, 28, 18, 22)
        logo = QLabel("REELMAKER")
        logo.setObjectName("logo")
        sl.addWidget(logo)
        sub = QLabel("LOCAL AI VIDEO STUDIO")
        sub.setObjectName("muted")
        sl.addWidget(sub)
        sl.addSpacing(28)

        self.stack = QStackedWidget()
        navs = [
            ("⌂   Dashboard", 0), ("▤   Proyectos", 1),
            ("✦   Análisis IA", 2), ("▣   Editor de clips", 3),
            ("⇧   Exportaciones", 4), ("⚙   Configuración", 5)
        ]
        for label, index in navs:
            b = QPushButton(label)
            b.setObjectName("nav")
            b.clicked.connect(lambda _, i=index: self.navigate(i))
            sl.addWidget(b)
        sl.addStretch()
        status = QLabel("●  PROCESAMIENTO LOCAL")
        status.setStyleSheet("color:#46d69b;font-size:10px;font-weight:bold")
        sl.addWidget(status)
        root.addWidget(side)

        body = QVBoxLayout()
        body.setContentsMargins(28, 22, 28, 22)
        body.setSpacing(15)
        top = QHBoxLayout()
        self.crumb = QLabel("WORKSPACE / DASHBOARD")
        self.crumb.setObjectName("muted")
        top.addWidget(self.crumb)
        top.addStretch()
        version = QLabel("v" + APP_VERSION)
        version.setObjectName("muted")
        top.addWidget(version)
        body.addLayout(top)
        root.addLayout(body, 1)
        body.addWidget(self.stack)

        self.pages = [
            self.dashboard_page(), self.projects_page(), self.analysis_page(),
            self.editor_page(), self.exports_page(), self.settings_page()
        ]
        for page in self.pages:
            self.stack.addWidget(page)

    def page_base(self, title, desc):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(14)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        description = QLabel(desc)
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(description)
        return page, layout

    def dashboard_page(self):
        page, layout = self.page_base(
            "Tu estudio creativo.",
            "Convierte vídeos largos en clips verticales con análisis y transcripción local."
        )
        row = QHBoxLayout()
        row.addWidget(self.button("+ Importar vídeo", True, self.import_video))
        row.addWidget(self.button("Abrir proyectos", False, lambda: self.navigate(1)))
        row.addStretch()
        layout.addLayout(row)
        stats = QHBoxLayout()
        self.stat_projects = self.stat("PROYECTOS", "0")
        self.stat_clips = self.stat("CLIPS", "0")
        self.stat_exports = self.stat("EXPORTADOS", "0")
        for widget in (self.stat_projects, self.stat_clips, self.stat_exports):
            stats.addWidget(widget)
        layout.addLayout(stats)
        layout.addWidget(QLabel("Actividad reciente"))
        self.recent = QTableWidget(0, 4)
        self.setup_table(self.recent, ["Proyecto", "Vídeo", "Duración", "Estado"])
        self.recent.itemDoubleClicked.connect(lambda *_: self.navigate(1))
        layout.addWidget(self.recent)
        return page

    def projects_page(self):
        page, layout = self.page_base("Mis proyectos", "Importa y administra tus vídeos de origen.")
        bar = QHBoxLayout()
        bar.addWidget(self.button("+ Importar vídeo", True, self.import_video))
        bar.addWidget(self.button("Eliminar proyecto", False, self.delete_project))
        bar.addStretch()
        layout.addLayout(bar)
        self.projects_table = QTableWidget(0, 5)
        self.setup_table(self.projects_table, ["ID", "Nombre", "Archivo de origen", "Duración", "Estado"])
        self.projects_table.itemSelectionChanged.connect(self.project_selected)
        self.projects_table.itemDoubleClicked.connect(lambda *_: self.navigate(2))
        layout.addWidget(self.projects_table)
        return page

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
        self.transcript_table = QTableWidget(0, 3)
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
        self.clips_table = QTableWidget(0, 5)
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
        self.exports_table = QTableWidget(0, 4)
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
        inner.addLayout(form)
        inner.addWidget(note)
        inner.addWidget(self.button("Guardar configuración", True, self.save_settings))
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
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        label = QLabel(title)
        label.setObjectName("muted")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:27px;font-weight:800;color:white")
        layout.addWidget(label)
        layout.addWidget(value_label)
        frame.value_label = value_label
        return frame

    def setup_table(self, table, headers):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)

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
        self.stack.setCurrentIndex(index)
        names = ["DASHBOARD", "PROJECTS", "AI ANALYSIS", "CLIP EDITOR", "EXPORTS", "SETTINGS"]
        self.crumb.setText("WORKSPACE / " + names[index])
        if index in (0, 1):
            self.refresh_all()
        elif index == 2:
            self.refresh_project_selectors()
            self.analysis_project_changed()
        elif index == 3:
            self.refresh_project_selectors()
            self.load_clips()
        elif index == 4:
            self.refresh_project_selectors()
            self.load_exports()

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
        for key, value in values.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        if show_message:
            QMessageBox.information(self, "Configuración", "Todas las preferencias se guardaron correctamente.")

    def open_exports(self):
        folder = Path(self.settings.value("export_folder", str(EXPORTS_DIR))).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(
                self, "Análisis en curso",
                "Espera a que termine el análisis antes de cerrar la aplicación."
            )
            event.ignore()
            return
        self.db.close()
        event.accept()
