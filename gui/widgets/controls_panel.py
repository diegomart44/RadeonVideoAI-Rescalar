"""
Controls and Configuration Panel.

This build is focused solely on "Reescalar con IA": Real-ESRGAN-family
restoration/upscaling (core/engine.py + core/inference.py). The Generar
(Stable Diffusion recreation) and Interpolar (RIFE frame interpolation)
tabs from the full RadeonVideoAI suite were deliberately removed here to
keep this variant single-purpose.
"""

import os
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QSpinBox, QCheckBox,
    QGroupBox, QFileDialog, QScrollArea, QSizePolicy
)


class ControlsPanel(QWidget):
    """Configuration controls styled with modern obsidian & Radeon Ruby aesthetics."""

    start_requested = pyqtSignal(dict)
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    file_selected = pyqtSignal(str)

    PANEL_WIDTH = 400

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.PANEL_WIDTH)
        self._is_paused = False

        self._build_ui()

    def _combo(self, items_with_tooltips):
        """Builds a QComboBox that never grows past the panel width, no
        matter how long an item's label is; the full description is
        available as a tooltip on the item and on the box itself."""
        box = QComboBox()
        box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        box.setMinimumContentsLength(1)
        box.setMaximumWidth(self.PANEL_WIDTH - 56)
        for text, tooltip in items_with_tooltips:
            box.addItem(text)
            if tooltip:
                box.setItemData(box.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole)
        if items_with_tooltips and items_with_tooltips[0][1]:
            box.setToolTip(items_with_tooltips[0][1])
            box.currentIndexChanged.connect(
                lambda i, b=box: b.setToolTip(b.itemData(i, Qt.ItemDataRole.ToolTipRole) or "")
            )
        return box

    def _section_label(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        lbl.setWordWrap(True)
        return lbl

    def _scroll_wrap(self, container: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        scroll.setWidget(container)
        return scroll

    # -----------------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        grp_files = QGroupBox("📁  Video a Reescalar")
        lay_files = QVBoxLayout(grp_files)
        lay_files.setSpacing(6)

        lay_files.addWidget(self._section_label("Video original"))
        h_in = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Seleccionar archivo...")
        btn_in = QPushButton("Examinar")
        btn_in.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_in.clicked.connect(self._browse_input)
        h_in.addWidget(self.txt_input)
        h_in.addWidget(btn_in)
        lay_files.addLayout(h_in)

        lay_files.addWidget(self._section_label("Video reescalado (destino)"))
        h_out = QHBoxLayout()
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("Ruta de salida generada...")
        btn_out = QPushButton("Guardar")
        btn_out.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_out.clicked.connect(self._browse_output)
        h_out.addWidget(self.txt_output)
        h_out.addWidget(btn_out)
        lay_files.addLayout(h_out)
        layout.addWidget(grp_files)

        grp_ai = QGroupBox("🧠  Modelo de IA")
        lay_ai = QVBoxLayout(grp_ai)
        lay_ai.setSpacing(6)
        lay_ai.addWidget(self._section_label("Arquitectura / checkpoint"))
        self.cmb_model = self._combo([
            ("Universal (rápido)", "general_v3 — Rápido, uso general, con control de desruido real."),
            ("Máxima calidad 4x", "x4plus — Mayor detalle, más lento. Ideal para escala 4x."),
            ("Alta fidelidad 2x", "x2plus — Red nativa 2x, mejor que reescalar desde un modelo 4x."),
            ("Vídeo real / compresión", "BSRGAN — Entrenado para ruido y artefactos de compresión reales."),
            ("Animación y CG", "anime6B — Optimizado para animación y contenido dibujado."),
            ("Ultra nitidez (comunidad)", "4x-UltraSharp — Muy popular por su nitidez. Licencia CC BY-NC-SA: SOLO uso no comercial/personal."),
        ])
        self._model_name_map = ["general_v3", "x4plus", "x2plus", "bsrgan", "anime6b", "ultrasharp"]
        lay_ai.addWidget(self.cmb_model)

        lay_ai.addWidget(self._section_label("Factor de reescalado"))
        self.cmb_scale = self._combo([
            ("2x — Recomendado", "Duplica ancho y alto. Mejor equilibrio velocidad/calidad."),
            ("4x — Ultra HD / 4K", "Cuadruplica ancho y alto. Más lento, máximo detalle."),
            ("1x — Solo restauración", "Mantiene la resolución; solo desruido y nitidez."),
        ])
        lay_ai.addWidget(self.cmb_scale)

        self.lbl_denoise = QLabel("Filtro de desruido — 15%")
        self.lbl_denoise.setObjectName("FieldLabel")
        self.lbl_denoise.setWordWrap(True)
        lay_ai.addWidget(self.lbl_denoise)
        self.sld_denoise = QSlider(Qt.Orientation.Horizontal)
        self.sld_denoise.setRange(0, 100)
        self.sld_denoise.setValue(15)
        self.sld_denoise.valueChanged.connect(lambda v: self.lbl_denoise.setText(f"Filtro de desruido — {v}%"))
        lay_ai.addWidget(self.sld_denoise)

        self.lbl_sharpen = QLabel("Nitidez y detalle — 20%")
        self.lbl_sharpen.setObjectName("FieldLabel")
        self.lbl_sharpen.setWordWrap(True)
        lay_ai.addWidget(self.lbl_sharpen)
        self.sld_sharpen = QSlider(Qt.Orientation.Horizontal)
        self.sld_sharpen.setRange(0, 100)
        self.sld_sharpen.setValue(20)
        self.sld_sharpen.valueChanged.connect(lambda v: self.lbl_sharpen.setText(f"Nitidez y detalle — {v}%"))
        lay_ai.addWidget(self.sld_sharpen)
        layout.addWidget(grp_ai)

        grp_vram = QGroupBox("🧩  Memoria GPU y Parches")
        lay_vram = QVBoxLayout(grp_vram)
        lay_vram.setSpacing(6)

        lay_vram.addWidget(self._section_label("Tamaño de parche (tile)"))
        self.cmb_tile = self._combo([
            ("768 px — Recomendado 16GB", "Máximo aprovechamiento de GPU en tarjetas de 16GB como la RX 9060 XT."),
            ("1024 px — Máximo", "Menos parches por fotograma; exprime más la GPU en tarjetas de 16GB con vídeo de alta resolución."),
            ("512 px — Equilibrado", "Buen balance entre velocidad y uso de memoria."),
            ("384 px", "Menor uso de memoria, algo más lento por fotograma."),
            ("256 px — Bajo consumo", "Para GPUs con poca VRAM."),
        ])
        lay_vram.addWidget(self.cmb_tile)

        lay_vram.addWidget(self._section_label("Solapamiento (fusión de bordes)"))
        self.cmb_overlap = self._combo([
            ("48 px — Fusión suave", "Sin costuras visibles entre parches. Recomendado."),
            ("32 px — Rápido", "Menos solapamiento, procesa algo más rápido."),
            ("64 px — Ultra suave", "Máxima suavidad en los bordes, más lento."),
        ])
        lay_vram.addWidget(self.cmb_overlap)

        lay_vram.addWidget(self._section_label("Umbral de seguridad anti-OOM"))
        self.cmb_vram_limit = self._combo([
            ("90% VRAM — Automático", "Degrada el tamaño de parche automáticamente cerca del límite."),
            ("85% VRAM — Conservador", "Deja más margen libre de memoria."),
            ("95% VRAM — Agresivo", "Exprime al máximo la memoria disponible."),
        ])
        lay_vram.addWidget(self.cmb_vram_limit)
        layout.addWidget(grp_vram)

        grp_enc = QGroupBox("🎬  Codificación (AMD AMF)")
        lay_enc = QVBoxLayout(grp_enc)
        lay_enc.setSpacing(6)

        lay_enc.addWidget(self._section_label("Códec de salida"))
        self.cmb_encoder = self._combo([
            ("HEVC (H.265) — Hardware AMD", "hevc_amf — Acelerado por la GPU AMD. Mejor compresión."),
            ("H.264 — Hardware AMD", "h264_amf — Acelerado por la GPU AMD. Máxima compatibilidad."),
            ("HEVC (H.265) — Software", "libx265 — Usa la CPU. Más lento, sin AMF."),
            ("H.264 — Software", "libx264 — Usa la CPU. Más lento, sin AMF."),
        ])
        lay_enc.addWidget(self.cmb_encoder)

        lay_enc.addWidget(self._section_label("Tasa de bits"))
        h_bitrate = QHBoxLayout()
        self.spn_bitrate = QSpinBox()
        self.spn_bitrate.setRange(5, 150)
        self.spn_bitrate.setValue(25)
        self.spn_bitrate.setSuffix(" Mbps")
        h_bitrate.addWidget(self.spn_bitrate)
        lay_enc.addLayout(h_bitrate)

        self.chk_audio = QCheckBox("Preservar audio original")
        self.chk_audio.setToolTip("Copia las pistas de audio sin recodificar (-c:a copy).")
        self.chk_audio.setChecked(True)
        lay_enc.addWidget(self.chk_audio)
        layout.addWidget(grp_enc)

        layout.addStretch(1)
        main_layout.addWidget(self._scroll_wrap(container), stretch=1)

        self.btn_start = QPushButton("✨  REESCALAR VIDEO")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setToolTip("Reescala/restaura este video con Real-ESRGAN (fiel al original, más nítido y sin ruido).")
        self.btn_start.clicked.connect(self._on_start_clicked)
        main_layout.addWidget(self.btn_start)

        h_actions = QHBoxLayout()
        h_actions.setSpacing(10)
        self.btn_pause = QPushButton("⏸  Pausar")
        self.btn_pause.setEnabled(False)
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        h_actions.addWidget(self.btn_pause)

        self.btn_cancel = QPushButton("✕  Cancelar")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        h_actions.addWidget(self.btn_cancel)
        main_layout.addLayout(h_actions)

    def set_input_path(self, path: str):
        """Sets the input file path and notifies listeners (used both by the
        Browse dialog and by drag-and-drop) so the viewer can immediately
        show the first frame instead of waiting for a job."""
        self.txt_input.setText(path)
        base, ext = os.path.splitext(path)
        scale_tag = "2x" if self.cmb_scale.currentIndex() == 0 else ("4x" if self.cmb_scale.currentIndex() == 1 else "restored")
        self.txt_output.setText(f"{base}_AI_{scale_tag}.mp4")
        self.file_selected.emit(path)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Video", "",
            "Archivos de Video (*.mp4 *.mkv *.mov *.avi *.webm *.ts);;Todos los Archivos (*.*)"
        )
        if path:
            self.set_input_path(path)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Video Reescalado", self.txt_output.text() or "",
            "Archivo MP4 (*.mp4);;Archivo MKV (*.mkv)"
        )
        if path:
            self.txt_output.setText(path)

    def _on_start_clicked(self):
        in_p = self.txt_input.text().strip()
        out_p = self.txt_output.text().strip()
        if not in_p or not os.path.isfile(in_p):
            return

        scale_idx = self.cmb_scale.currentIndex()
        scale = 2 if scale_idx == 0 else (4 if scale_idx == 1 else 1)

        tile_str = "".join(ch for ch in self.cmb_tile.currentText().split(" ")[0] if ch.isdigit())
        tile_size = int(tile_str) if tile_str.isdigit() else 512

        overlap_str = "".join(ch for ch in self.cmb_overlap.currentText().split(" ")[0] if ch.isdigit())
        overlap = int(overlap_str) if overlap_str.isdigit() else 48

        enc_raw = self.cmb_encoder.currentText()
        if "HEVC" in enc_raw and "Hardware" in enc_raw:
            encoder = "hevc_amf"
        elif "H.264" in enc_raw and "Hardware" in enc_raw:
            encoder = "h264_amf"
        elif "HEVC" in enc_raw:
            encoder = "libx265"
        else:
            encoder = "libx264"

        model_idx = self.cmb_model.currentIndex()
        model_name = self._model_name_map[model_idx] if 0 <= model_idx < len(self._model_name_map) else "general_v3"

        config = {
            "input_path": in_p,
            "output_path": out_p,
            "scale": scale,
            "model_name": model_name,
            "tile_size": tile_size,
            "overlap": overlap,
            "denoise": self.sld_denoise.value() / 100.0,
            "sharpen": self.sld_sharpen.value() / 100.0,
            "encoder": encoder,
            "bitrate_mbps": self.spn_bitrate.value(),
            "vram_safety": 0.90,
            "has_audio": self.chk_audio.isChecked()
        }

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.start_requested.emit(config)

    def _on_pause_clicked(self):
        if not self._is_paused:
            self._is_paused = True
            self.btn_pause.setText("▶  Reanudar")
            self.pause_requested.emit()
        else:
            self._is_paused = False
            self.btn_pause.setText("⏸  Pausar")
            self.resume_requested.emit()

    def _on_cancel_clicked(self):
        self.cancel_requested.emit()

    def set_processing_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_pause.setText("⏸  Pausar")
        self._is_paused = False
