#!/usr/bin/env python3
"""
Beautiful Katamari Entity Editor - Vispy Edition
A modern, GPU-accelerated 3D level editor for Beautiful Katamari
"""

import sys
import re
import csv
import os
import numpy as np
from pathlib import Path

# PyQt5 for modern UI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QAbstractItemView, QTabWidget,
    QGridLayout, QStatusBar, QMenuBar, QMenu, QAction, QToolBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QKeySequence

# Vispy for GPU-accelerated 3D
from vispy import app, scene
from vispy.scene import visuals
from vispy.color import Color, ColorArray


class Theme:
    """Modern dark theme colors"""
    # Main colors
    BG_DARK = "#1a1a2e"
    BG_MID = "#16213e"
    BG_LIGHT = "#1f3460"

    # Accent colors
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b6b"
    ACCENT_SECONDARY = "#0f3460"

    # Text colors
    TEXT_PRIMARY = "#eaeaea"
    TEXT_SECONDARY = "#a0a0a0"
    TEXT_DIM = "#606060"

    # Status colors
    SUCCESS = "#4ecca3"
    WARNING = "#ffc107"
    ERROR = "#ff5252"
    INFO = "#4fc3f7"

    # Entity colors for visualization
    ENTITY_DEFAULT = "#4fc3f7"
    ENTITY_SELECTED = "#ffeb3b"
    ENTITY_HIGHLIGHT = "#e94560"

    # Graph/3D colors
    GRAPH_BG = "#0a0a15"
    GRID_COLOR = "#2a2a4a"
    AXIS_COLOR = "#4a4a6a"

    @classmethod
    def get_stylesheet(cls):
        return f"""
            QMainWindow {{
                background-color: {cls.BG_DARK};
            }}
            QWidget {{
                background-color: {cls.BG_DARK};
                color: {cls.TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
            }}
            QGroupBox {{
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
                border-radius: 6px;
                margin-top: 14px;
                padding: 12px;
                font-weight: bold;
                font-size: 13px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {cls.ACCENT};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {cls.ACCENT_SECONDARY};
                border: none;
                border-radius: 4px;
                padding: 10px 18px;
                color: {cls.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cls.BG_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {cls.ACCENT};
            }}
            QPushButton#primary {{
                background-color: {cls.ACCENT};
            }}
            QPushButton#primary:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}
            QPushButton#success {{
                background-color: {cls.SUCCESS};
                color: {cls.BG_DARK};
            }}
            QListWidget {{
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
                border-radius: 4px;
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {cls.ACCENT};
                color: {cls.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: {cls.BG_LIGHT};
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
                border-radius: 4px;
                padding: 8px;
                color: {cls.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {cls.ACCENT};
            }}
            QSlider::groove:horizontal {{
                background: {cls.BG_LIGHT};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {cls.ACCENT};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {cls.ACCENT_HOVER};
            }}
            QScrollBar:vertical {{
                background: {cls.BG_MID};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.BG_LIGHT};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.ACCENT_SECONDARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QStatusBar {{
                background-color: {cls.BG_MID};
                color: {cls.SUCCESS};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 4px;
            }}
            QMenuBar {{
                background-color: {cls.BG_MID};
                color: {cls.TEXT_PRIMARY};
            }}
            QMenuBar::item:selected {{
                background-color: {cls.ACCENT};
            }}
            QMenu {{
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
            }}
            QMenu::item:selected {{
                background-color: {cls.ACCENT};
            }}
            QTabWidget::pane {{
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {cls.BG_DARK};
                color: {cls.TEXT_SECONDARY};
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {cls.BG_MID};
                color: {cls.ACCENT};
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {cls.ACCENT};
                border-color: {cls.ACCENT};
            }}
            QLabel#title {{
                font-size: 16px;
                font-weight: bold;
                color: {cls.ACCENT};
            }}
            QLabel#info {{
                color: {cls.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QLabel#section {{
                font-size: 14px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
                padding: 4px 0px;
            }}
            QMenuBar {{
                font-size: 13px;
                padding: 2px;
            }}
            QMenu {{
                font-size: 13px;
            }}
        """


class VispyCanvas(QWidget):
    """Vispy 3D canvas widget for entity visualization"""

    entity_clicked = pyqtSignal(int)  # Emits entity index

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create Vispy canvas with scene
        self.canvas = scene.SceneCanvas(
            keys='interactive',
            bgcolor=Theme.GRAPH_BG,
            show=False
        )

        # Create layout and add canvas
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)

        # Create view with turntable camera
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(
            fov=45,
            distance=500,
            elevation=30,
            azimuth=45
        )

        # Create scatter visual for entities
        self.scatter = visuals.Markers(parent=self.view.scene)

        # Create scatter for selected entities (highlight)
        self.highlight_scatter = visuals.Markers(parent=self.view.scene)

        # Grid visual
        self.grid = scene.visuals.GridLines(
            color=(0.3, 0.3, 0.5, 0.5),
            parent=self.view.scene
        )

        # Store entity positions for picking
        self.entity_positions = None
        self.entities = []

        # Connect events
        self.canvas.events.mouse_press.connect(self._on_mouse_press)

    def set_entities(self, entities, selected_indices=None):
        """Update the displayed entities"""
        self.entities = entities

        if not entities:
            self.scatter.set_data(pos=np.zeros((0, 3)))
            self.highlight_scatter.set_data(pos=np.zeros((0, 3)))
            self.canvas.update()
            return

        # Extract positions - negate X and swap Y/Z for display like original
        positions = np.array([
            [-e['x'], e['z'], e['y']] for e in entities
        ], dtype=np.float32)

        self.entity_positions = positions

        # Default colors
        colors = np.full((len(entities), 4), [0.3, 0.7, 0.9, 0.7], dtype=np.float32)

        # Set marker sizes based on entity size if available
        sizes = np.full(len(entities), 8, dtype=np.float32)

        self.scatter.set_data(
            pos=positions,
            face_color=colors,
            edge_color='white',
            edge_width=0.5,
            size=sizes
        )

        # Update highlights
        self._update_highlights(selected_indices or [])

        # Auto-fit view
        if len(positions) > 0:
            center = positions.mean(axis=0)
            max_range = np.ptp(positions, axis=0).max()
            self.view.camera.center = center
            self.view.camera.distance = max_range * 2

        self.canvas.update()

    def _update_highlights(self, selected_indices):
        """Update highlight markers for selected entities"""
        if not selected_indices or not self.entity_positions is not None:
            self.highlight_scatter.set_data(pos=np.zeros((0, 3)))
            return

        # Get positions of selected entities
        selected_positions = self.entity_positions[selected_indices]

        # Create highlight colors (gold with red edge)
        colors = np.full((len(selected_indices), 4), [1.0, 0.85, 0.0, 1.0], dtype=np.float32)

        self.highlight_scatter.set_data(
            pos=selected_positions,
            face_color=colors,
            edge_color='red',
            edge_width=2,
            size=15
        )

        self.canvas.update()

    def update_selection(self, selected_indices):
        """Update just the selection highlights"""
        self._update_highlights(selected_indices)

    def _on_mouse_press(self, event):
        """Handle mouse click for entity picking"""
        if event.button != 1 or self.entity_positions is None:
            return

        # Get click position in screen coordinates
        pos = event.pos

        # Transform to find nearest entity
        # This is a simplified picking - for production would use GPU picking
        tr = self.view.scene.transform

        # For now, emit a basic pick signal
        # TODO: Implement proper 3D picking
        pass


class EntityListWidget(QWidget):
    """Entity list panel with search and filtering"""

    selection_changed = pyqtSignal(list)  # Emits list of selected indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entities = []
        self.display_mapping = []
        self.item_db = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("Entities")
        title.setObjectName("title")
        layout.addWidget(title)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search entities...")
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)

        # Entity count label
        self.count_label = QLabel("0 entities")
        self.count_label.setObjectName("info")
        layout.addWidget(self.count_label)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

    def set_entities(self, entities, item_db=None):
        """Update the entity list"""
        self.entities = entities
        self.item_db = item_db or {}
        self.display_mapping = list(range(len(entities)))
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the list widget"""
        self.list_widget.clear()

        for idx in self.display_mapping:
            if idx >= len(self.entities):
                continue
            ent = self.entities[idx]

            # Get display name
            db_key = ent['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            name = info.get('obj_en', f"Entity {ent['id']}")

            item = QListWidgetItem(f"{name} [{ent['id']}]")
            item.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item)

        self.count_label.setText(f"{len(self.display_mapping)} entities")

    def _on_search(self, text):
        """Filter entities by search text"""
        text = text.lower()

        if not text:
            self.display_mapping = list(range(len(self.entities)))
        else:
            self.display_mapping = []
            for i, ent in enumerate(self.entities):
                db_key = ent['id'].lstrip('0') or '0'
                info = self.item_db.get(db_key, {})
                name = info.get('obj_en', '').lower()

                if text in name or text in ent['id'].lower():
                    self.display_mapping.append(i)

        self._refresh_list()

    def _on_selection_changed(self):
        """Handle selection change"""
        selected = []
        for item in self.list_widget.selectedItems():
            idx = item.data(Qt.UserRole)
            selected.append(idx)

        self.selection_changed.emit(selected)

    def set_selection(self, indices):
        """Set selection programmatically"""
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) in indices:
                item.setSelected(True)

        self.list_widget.blockSignals(False)


class PositionEditor(QGroupBox):
    """Position editing panel"""

    position_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Position Editor", parent)
        self._setup_ui()
        self.entities = []
        self.selected_indices = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Offset mode toggle
        self.offset_mode = QCheckBox("Offset Mode")
        self.offset_mode.setToolTip("When enabled, values are added to current position")
        layout.addWidget(self.offset_mode)

        # Position sliders
        form = QFormLayout()

        self.sliders = {}
        self.spinboxes = {}

        for axis, color in [('X', '#ff6b6b'), ('Y', '#4ecca3'), ('Z', '#4fc3f7')]:
            row = QHBoxLayout()

            slider = QSlider(Qt.Horizontal)
            slider.setRange(-1000, 1000)
            slider.setValue(0)
            slider.valueChanged.connect(self._on_slider_change)

            spinbox = QDoubleSpinBox()
            spinbox.setRange(-10000, 10000)
            spinbox.setDecimals(2)
            spinbox.setValue(0)
            spinbox.valueChanged.connect(self._on_spinbox_change)

            row.addWidget(slider, stretch=3)
            row.addWidget(spinbox, stretch=1)

            self.sliders[axis] = slider
            self.spinboxes[axis] = spinbox

            label = QLabel(f"{axis}:")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            form.addRow(label, row)

        layout.addLayout(form)

        # Apply button
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)

    def update_for_selection(self, entities, selected_indices):
        """Update display for selected entities"""
        self.entities = entities
        self.selected_indices = selected_indices

        if not selected_indices:
            for axis in ['X', 'Y', 'Z']:
                self.spinboxes[axis].setValue(0)
            return

        # Show position of last selected entity
        ent = entities[selected_indices[-1]]
        self.spinboxes['X'].blockSignals(True)
        self.spinboxes['Y'].blockSignals(True)
        self.spinboxes['Z'].blockSignals(True)

        self.spinboxes['X'].setValue(-ent['x'])
        self.spinboxes['Y'].setValue(-ent['y'])
        self.spinboxes['Z'].setValue(-ent['z'])

        self.spinboxes['X'].blockSignals(False)
        self.spinboxes['Y'].blockSignals(False)
        self.spinboxes['Z'].blockSignals(False)

    def _on_slider_change(self):
        for axis in ['X', 'Y', 'Z']:
            self.spinboxes[axis].blockSignals(True)
            self.spinboxes[axis].setValue(self.sliders[axis].value())
            self.spinboxes[axis].blockSignals(False)

    def _on_spinbox_change(self):
        for axis in ['X', 'Y', 'Z']:
            self.sliders[axis].blockSignals(True)
            self.sliders[axis].setValue(int(self.spinboxes[axis].value()))
            self.sliders[axis].blockSignals(False)

    def _apply_changes(self):
        self.position_changed.emit()


class EntityInfoPanel(QGroupBox):
    """Panel showing detailed information about selected entity"""

    def __init__(self, parent=None):
        super().__init__("Entity Info", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(8)

        # Entity name
        self.name_label = QLabel("-")
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold; font-size: 14px;")
        layout.addRow("Name:", self.name_label)

        # Entity ID
        self.id_label = QLabel("-")
        self.id_label.setStyleSheet("font-family: monospace;")
        layout.addRow("ID:", self.id_label)

        # Size
        self.size_label = QLabel("-")
        layout.addRow("Size:", self.size_label)

        # Position
        self.pos_label = QLabel("-")
        self.pos_label.setStyleSheet("font-family: monospace;")
        layout.addRow("Position:", self.pos_label)

        # Rotation (quaternion)
        self.rot_label = QLabel("-")
        self.rot_label.setStyleSheet("font-family: monospace; font-size: 11px;")
        self.rot_label.setWordWrap(True)
        layout.addRow("Rotation:", self.rot_label)

        # Map
        self.map_label = QLabel("-")
        layout.addRow("Map:", self.map_label)

        # Pack ID
        self.pack_label = QLabel("-")
        layout.addRow("Pack:", self.pack_label)

        # Behavior types
        self.attack_label = QLabel("-")
        layout.addRow("Attack:", self.attack_label)

        self.move_label = QLabel("-")
        layout.addRow("Move:", self.move_label)

        self.escape_label = QLabel("-")
        layout.addRow("Escape:", self.escape_label)

    def update_info(self, entity, item_db=None):
        """Update display with entity information"""
        if entity is None:
            self.name_label.setText("-")
            self.id_label.setText("-")
            self.size_label.setText("-")
            self.pos_label.setText("-")
            self.rot_label.setText("-")
            self.map_label.setText("-")
            self.pack_label.setText("-")
            self.attack_label.setText("-")
            self.move_label.setText("-")
            self.escape_label.setText("-")
            return

        # Get name from database
        db_key = entity['id'].lstrip('0') or '0'
        info = (item_db or {}).get(db_key, {})
        name = info.get('obj_en', f"Entity {entity['id']}")
        size = info.get('size', '-')

        self.name_label.setText(name)
        self.id_label.setText(entity['id'])
        self.size_label.setText(str(size))
        self.pos_label.setText(f"X: {entity['x']:.2f}\nY: {entity['y']:.2f}\nZ: {entity['z']:.2f}")
        self.rot_label.setText(f"({entity['rx']:.3f}, {entity['ry']:.3f}, {entity['rz']:.3f}, {entity['rw']:.3f})")
        self.map_label.setText(entity.get('map_name', '-'))
        self.pack_label.setText(entity.get('pack', '-') or '-')
        self.attack_label.setText(entity.get('atk', '-') or '-')
        self.move_label.setText(entity.get('mov', '-') or '-')
        self.escape_label.setText(entity.get('esc', '-') or '-')


class KatamariEditorVispy(QMainWindow):
    """Main editor window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Katamari Editor - Vispy Edition")
        self.setMinimumSize(1400, 900)

        # Data
        self.entities = []
        self.file_sequence = []
        self.loaded_maps = []
        self.selected_indices = []
        self.item_db = {}
        self.undo_stack = []
        self.max_undo = 50

        # Load item database
        self._load_item_db()

        # Setup UI
        self._setup_ui()
        self._setup_menus()

        # Apply theme
        self.setStyleSheet(Theme.get_stylesheet())

        # Status bar
        self.statusBar().showMessage("Ready - Open a DAT file to begin")

    def _load_item_db(self):
        """Load the item database CSV"""
        csv_paths = [
            Path(__file__).parent / "ObjectList.csv",
            Path(__file__).parent / "objectlist.csv",
        ]

        for csv_path in csv_paths:
            if csv_path.exists():
                try:
                    with open(csv_path, encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            key = row.get('index', '').lstrip('0') or '0'
                            self.item_db[key] = row
                    break
                except Exception as e:
                    print(f"Error loading CSV: {e}")

    def _setup_ui(self):
        """Setup the main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Entity list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.entity_list = EntityListWidget()
        self.entity_list.selection_changed.connect(self._on_selection_changed)
        left_layout.addWidget(self.entity_list)

        splitter.addWidget(left_panel)

        # Center - 3D View
        self.vispy_canvas = VispyCanvas()
        splitter.addWidget(self.vispy_canvas)

        # Right panel - Tools
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for tools
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setAlignment(Qt.AlignTop)

        # Entity Info panel
        self.entity_info = EntityInfoPanel()
        tools_layout.addWidget(self.entity_info)

        # Position editor
        self.position_editor = PositionEditor()
        self.position_editor.position_changed.connect(self._on_position_changed)
        tools_layout.addWidget(self.position_editor)

        # Visualization options
        viz_group = QGroupBox("Visualization")
        viz_layout = QVBoxLayout(viz_group)

        # Color mode
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color by:"))
        self.color_mode = QComboBox()
        self.color_mode.addItems(["Default", "By ID", "By Size", "By Height", "By Map"])
        self.color_mode.currentTextChanged.connect(self._on_color_mode_changed)
        color_row.addWidget(self.color_mode)
        viz_layout.addLayout(color_row)

        # Entity size slider
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Point Size:"))
        self.point_size_slider = QSlider(Qt.Horizontal)
        self.point_size_slider.setRange(2, 30)
        self.point_size_slider.setValue(8)
        self.point_size_slider.valueChanged.connect(self._on_point_size_changed)
        size_row.addWidget(self.point_size_slider)
        viz_layout.addLayout(size_row)

        tools_layout.addWidget(viz_group)

        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)

        save_btn = QPushButton("Save All Maps")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self.save_all_maps)
        actions_layout.addWidget(save_btn)

        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo)
        actions_layout.addWidget(undo_btn)

        zoom_btn = QPushButton("Zoom to Fit")
        zoom_btn.clicked.connect(self._zoom_to_fit)
        actions_layout.addWidget(zoom_btn)

        tools_layout.addWidget(actions_group)

        # Add stretch to push everything up
        tools_layout.addStretch()

        scroll.setWidget(tools_widget)
        right_layout.addWidget(scroll)

        splitter.addWidget(right_panel)

        # Set initial splitter sizes
        splitter.setSizes([250, 900, 300])

    def _setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open DAT...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.load_file)
        file_menu.addAction(open_action)

        add_map_action = QAction("Add Map...", self)
        add_map_action.triggered.connect(self.add_map)
        file_menu.addAction(add_map_action)

        file_menu.addSeparator()

        save_action = QAction("Save All", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_all_maps)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        # View menu
        view_menu = menubar.addMenu("View")

        zoom_fit = QAction("Zoom to Fit", self)
        zoom_fit.setShortcut("Ctrl+0")
        zoom_fit.triggered.connect(self._zoom_to_fit)
        view_menu.addAction(zoom_fit)

    def _on_selection_changed(self, indices):
        """Handle entity selection change"""
        self.selected_indices = indices
        self.vispy_canvas.update_selection(indices)
        self.position_editor.update_for_selection(self.entities, indices)

        if indices:
            ent = self.entities[indices[-1]]
            self.entity_info.update_info(ent, self.item_db)
            db_key = ent['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            name = info.get('obj_en', f"Entity {ent['id']}")
            self.statusBar().showMessage(f"Selected: {name} | ID: {ent['id']} | Pos: ({ent['x']:.1f}, {ent['y']:.1f}, {ent['z']:.1f})")
        else:
            self.entity_info.update_info(None)

    def _on_position_changed(self):
        """Handle position change from editor"""
        if not self.selected_indices:
            return

        # Save undo state
        self._save_undo_state("Position Change")

        # Get values
        x = -self.position_editor.spinboxes['X'].value()
        y = -self.position_editor.spinboxes['Y'].value()
        z = -self.position_editor.spinboxes['Z'].value()

        offset_mode = self.position_editor.offset_mode.isChecked()

        for idx in self.selected_indices:
            ent = self.entities[idx]

            if offset_mode:
                ent['x'] += x
                ent['y'] += y
                ent['z'] += z
            else:
                ent['x'] = x
                ent['y'] = y
                ent['z'] = z

            # Sync raw data
            self._sync_entity_raw(ent)

        # Update display
        self.vispy_canvas.set_entities(self.entities, self.selected_indices)
        self.statusBar().showMessage("Position updated")

    def _zoom_to_fit(self):
        """Zoom camera to fit all entities"""
        if self.entities:
            self.vispy_canvas.set_entities(self.entities, self.selected_indices)

    def _on_color_mode_changed(self, mode):
        """Change entity coloring mode"""
        if not self.entities:
            return

        positions = self.vispy_canvas.entity_positions
        if positions is None:
            return

        n = len(self.entities)
        colors = np.zeros((n, 4), dtype=np.float32)

        if mode == "Default":
            colors[:] = [0.3, 0.7, 0.9, 0.7]

        elif mode == "By ID":
            # Color by entity ID hash
            for i, ent in enumerate(self.entities):
                id_hash = hash(ent['id']) % 360
                # HSV to RGB (simplified)
                h = id_hash / 60.0
                c = 0.8
                x = c * (1 - abs(h % 2 - 1))
                if h < 1:
                    r, g, b = c, x, 0
                elif h < 2:
                    r, g, b = x, c, 0
                elif h < 3:
                    r, g, b = 0, c, x
                elif h < 4:
                    r, g, b = 0, x, c
                elif h < 5:
                    r, g, b = x, 0, c
                else:
                    r, g, b = c, 0, x
                colors[i] = [r, g, b, 0.8]

        elif mode == "By Size":
            # Color by entity size from database
            sizes = []
            for ent in self.entities:
                db_key = ent['id'].lstrip('0') or '0'
                info = self.item_db.get(db_key, {})
                try:
                    size = float(info.get('size', 0))
                except:
                    size = 0
                sizes.append(size)

            sizes = np.array(sizes)
            if sizes.max() > sizes.min():
                normalized = (sizes - sizes.min()) / (sizes.max() - sizes.min())
            else:
                normalized = np.zeros(n)

            # Blue (small) to Red (large)
            for i, val in enumerate(normalized):
                colors[i] = [val, 0.3, 1 - val, 0.8]

        elif mode == "By Height":
            # Color by Y position (height)
            heights = np.array([e['y'] for e in self.entities])
            if heights.max() > heights.min():
                normalized = (heights - heights.min()) / (heights.max() - heights.min())
            else:
                normalized = np.zeros(n)

            # Gradient from purple (low) to yellow (high)
            for i, val in enumerate(normalized):
                colors[i] = [val, val, 1 - val, 0.8]

        elif mode == "By Map":
            # Color each map differently
            map_colors = [
                [0.3, 0.7, 0.9, 0.8],  # Blue
                [0.9, 0.5, 0.3, 0.8],  # Orange
                [0.4, 0.9, 0.4, 0.8],  # Green
                [0.9, 0.3, 0.6, 0.8],  # Pink
                [0.7, 0.7, 0.3, 0.8],  # Yellow
            ]
            for i, ent in enumerate(self.entities):
                map_idx = ent.get('map_index', 0) % len(map_colors)
                colors[i] = map_colors[map_idx]

        # Update scatter colors
        self.vispy_canvas.scatter.set_data(
            pos=positions,
            face_color=colors,
            edge_color='white',
            edge_width=0.5,
            size=self.point_size_slider.value()
        )
        self.vispy_canvas.canvas.update()

    def _on_point_size_changed(self, size):
        """Change entity point size"""
        if self.vispy_canvas.entity_positions is not None:
            # Re-apply current color mode with new size
            self._on_color_mode_changed(self.color_mode.currentText())

    # ============== File Operations ==============

    def load_file(self):
        """Load a DAT file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open DAT File", "", "DAT Files (*.dat);;All Files (*)"
        )
        if not filepath:
            return

        self.loaded_maps = []
        self._load_map_file(filepath, is_primary=True)

    def add_map(self):
        """Add another map to the view"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Add Map", "", "DAT Files (*.dat);;All Files (*)"
        )
        if not filepath:
            return

        self._load_map_file(filepath, is_primary=False)

    def _load_map_file(self, filepath, is_primary=True):
        """Internal method to load a map file"""
        map_name = os.path.basename(filepath)

        try:
            with open(filepath, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
            return

        if is_primary:
            self.file_sequence = []
            self.entities = []
            self.undo_stack = []

        start_idx = len(self.entities)
        map_entities = []
        map_sequence = []

        token_pattern = re.compile(r'(<entity>|</entity>|<child>|</child>)')

        last_pos = 0
        entity_start_pos = None
        parent_stack = []

        for match in token_pattern.finditer(content):
            token = match.group(1)
            start, end = match.start(), match.end()

            if entity_start_pos is None:
                if start > last_pos:
                    map_sequence.append(content[last_pos:start])

            if token == "<entity>":
                entity_start_pos = start

            elif token == "<child>":
                if entity_start_pos is not None:
                    raw_chunk = content[entity_start_pos:start]
                    ent = self._parse_block(raw_chunk)
                    ent['child_ids'] = []
                    ent['map_index'] = len(self.loaded_maps)
                    ent['map_name'] = map_name
                    map_entities.append(ent)
                    self.entities.append(ent)
                    map_sequence.append(ent)

                    parent_stack.append(len(self.entities) - 1)
                    entity_start_pos = None

                map_sequence.append(token)

            elif token == "</entity>":
                if entity_start_pos is not None:
                    raw_chunk = content[entity_start_pos:end]
                    ent = self._parse_block(raw_chunk)
                    ent['child_ids'] = []
                    ent['map_index'] = len(self.loaded_maps)
                    ent['map_name'] = map_name
                    map_entities.append(ent)
                    self.entities.append(ent)
                    map_sequence.append(ent)

                    if parent_stack:
                        self.entities[parent_stack[-1]]['child_ids'].append(ent['id'])

                    entity_start_pos = None
                else:
                    map_sequence.append(token)

            elif token == "</child>":
                map_sequence.append(token)
                if parent_stack:
                    parent_stack.pop()

            last_pos = end

        if last_pos < len(content):
            map_sequence.append(content[last_pos:])

        # Store map data
        self.loaded_maps.append({
            'name': map_name,
            'filepath': filepath,
            'entities': map_entities,
            'file_sequence': map_sequence,
            'start_idx': start_idx
        })

        if is_primary:
            self.file_sequence = list(map_sequence)
        else:
            self.file_sequence.extend(map_sequence)

        # Update title
        if len(self.loaded_maps) == 1:
            self.setWindowTitle(f"Katamari Editor - {map_name}")
        else:
            names = " + ".join([m['name'] for m in self.loaded_maps])
            self.setWindowTitle(f"Katamari Editor - {names}")

        # Update displays
        self.entity_list.set_entities(self.entities, self.item_db)
        self.vispy_canvas.set_entities(self.entities, [])

        self.statusBar().showMessage(f"Loaded {map_name}: {len(map_entities)} entities")

    def _parse_block(self, b):
        """Parse an entity block from the DAT file"""
        def get_t(t, src):
            m = re.search(fr'<{t}>(.*?)</{t}>', src, re.DOTALL)
            return (m.group(1), len(m.group(1))) if m else ("", 0)

        def find_val(tags, src):
            for t in tags:
                m = re.search(fr'<{t}>(.*?)</{t}>', src, re.DOTALL)
                if m:
                    return m.group(1).strip()
            return "0"

        p_raw, p_len = get_t('posi', b)
        p_matches = list(re.finditer(r'[^\s]+', p_raw))
        if len(p_matches) == 3:
            p = [float(m.group(0)) for m in p_matches]
            p_indices = [(m.start(), m.end()) for m in p_matches]
        else:
            p = [0.0, 0.0, 0.0]
            p_indices = []

        r_raw, r_len = get_t('roll', b)
        r_matches = list(re.finditer(r'[^\s]+', r_raw))
        if len(r_matches) == 4:
            r = [float(m.group(0)) for m in r_matches]
            r_indices = [(m.start(), m.end()) for m in r_matches]
        else:
            r = [0.0, 0.0, 0.0, 1.0]
            r_indices = []

        id_raw, id_len = get_t('index', b)

        return {
            'raw': b, 'p_raw_content': p_raw, 'r_raw_content': r_raw,
            'p_indices': p_indices, 'r_indices': r_indices,
            'id_tag_len': id_len, 'x': p[0], 'y': p[1], 'z': p[2],
            'rx': r[0], 'ry': r[1], 'rz': r[2], 'rw': r[3],
            'id': id_raw.strip(), 'pack': get_t('pack_id', b)[0].strip(),
            'atk': get_t('attack_type', b)[0].strip(),
            'mov': get_t('move_type', b)[0].strip(),
            'esc': get_t('escape_type', b)[0].strip(),
            'spd': find_val(['move_speed', 'speed'], b),
            'pth': find_val(['move_path_id', 'path_id'], b),
            'scale': find_val(['scale'], b),
            'plus_type': find_val(['plus_type'], b),
            'plus_fly_height': find_val(['plus_fly_height'], b),
            'plus_roll_speed': find_val(['plus_roll_speed'], b),
            'plus_angle': find_val(['plus_angle'], b),
            'parent_type': find_val(['parent_type'], b),
            'clash_type': find_val(['clash_type'], b),
            'child_ids': []
        }

    def _format_strict(self, val, width):
        """Format a float value to exact width"""
        s = f"{val:.10f}"
        if len(s) > width:
            s = s[:width]
            if s.endswith('.'):
                s = s[:-1].rjust(width)
        return s.ljust(width)

    def _sync_entity_raw(self, ent):
        """Sync entity raw data after position change"""
        if not ent['p_indices']:
            return

        original_content = ent['p_raw_content']
        new_parts = []
        last_idx = 0
        ax_keys = ['x', 'y', 'z']

        for i in range(3):
            start, end = ent['p_indices'][i]
            new_parts.append(original_content[last_idx:start])
            new_parts.append(self._format_strict(ent[ax_keys[i]], end - start))
            last_idx = end

        new_parts.append(original_content[last_idx:])
        reconstructed = "".join(new_parts)
        ent['p_raw_content'] = reconstructed

        # Update raw block
        s, e = "<posi>", "</posi>"
        si = ent['raw'].find(s) + len(s)
        ei = ent['raw'].find(e)
        if si > -1 and ei > -1:
            final_block = reconstructed[:ei-si].ljust(ei-si)
            ent['raw'] = ent['raw'][:si] + final_block + ent['raw'][ei:]

    def save_all_maps(self):
        """Save all loaded maps"""
        if not self.loaded_maps:
            QMessageBox.warning(self, "No Maps", "No maps loaded to save.")
            return

        saved_count = 0
        for map_data in self.loaded_maps:
            try:
                out = "".join([
                    i if isinstance(i, str) else i['raw']
                    for i in map_data['file_sequence']
                ])
                with open(map_data['filepath'], 'wb') as f:
                    f.write(out.encode('utf-8'))
                saved_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save {map_data['name']}: {e}")

        if saved_count > 0:
            QMessageBox.information(self, "Success", f"Saved {saved_count} map(s).")
            self.statusBar().showMessage(f"Saved {saved_count} map(s)")

    # ============== Undo System ==============

    def _save_undo_state(self, action_name="Change"):
        """Save current state to undo stack"""
        import copy
        state = {
            'action': action_name,
            'entities': copy.deepcopy(self.entities),
            'file_sequence': copy.deepcopy(self.file_sequence),
            'loaded_maps': copy.deepcopy(self.loaded_maps)
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)

    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            self.statusBar().showMessage("Nothing to undo")
            return

        state = self.undo_stack.pop()
        self.entities = state['entities']
        self.file_sequence = state['file_sequence']
        self.loaded_maps = state['loaded_maps']

        # Update displays
        self.entity_list.set_entities(self.entities, self.item_db)
        self.vispy_canvas.set_entities(self.entities, self.selected_indices)

        self.statusBar().showMessage(f"Undid: {state['action']}")


def main():
    # Set up Vispy to use PyQt5
    app.use_app('pyqt5')

    # Create Qt application
    qt_app = QApplication(sys.argv)
    qt_app.setStyle('Fusion')

    # Create and show main window
    window = KatamariEditorVispy()
    window.show()

    # Run application
    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()
