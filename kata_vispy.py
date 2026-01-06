#!/usr/bin/env python3
"""
Beautiful Katamari Entity Editor - Vispy Edition
A modern, GPU-accelerated 3D level editor for Beautiful Katamari
"""

import sys
import re
import csv
import os
import math
import numpy as np
from pathlib import Path

# PyQt5 for modern UI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QAbstractItemView, QTabWidget,
    QGridLayout, QStatusBar, QMenuBar, QMenu, QAction, QToolBar,
    QRadioButton, QButtonGroup, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QKeySequence, QCursor

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
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                background-color: {cls.BG_MID};
                border: 1px solid {cls.BG_LIGHT};
            }}
            QRadioButton::indicator:checked {{
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

    entity_clicked = pyqtSignal(int, bool, bool)  # index, shift, ctrl
    paint_select = pyqtSignal(float, float, float)  # x, y, radius in 3D

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

        # Mesh visual for generated mesh
        self.mesh_visual = None

        # Store entity positions for picking
        self.entity_positions = None
        self.entity_sizes = None
        self.entities = []

        # Selection mode
        self.select_mode = "CLICK"  # NONE, CLICK, PAINT
        self.brush_size = 25.0
        self.is_painting = False

        # Connect events
        self.canvas.events.mouse_press.connect(self._on_mouse_press)
        self.canvas.events.mouse_move.connect(self._on_mouse_move)
        self.canvas.events.mouse_release.connect(self._on_mouse_release)

    def set_entities(self, entities, selected_indices=None, sizes=None, use_size_scaling=False):
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
        if use_size_scaling and sizes is not None:
            # Clip sizes, treating >9M as outliers (size 200)
            sizes = np.array(sizes, dtype=np.float32)
            sizes = np.where(sizes > 9000000, 200, sizes)
            marker_sizes = np.clip(sizes / 50.0, 3, 50)
            self.entity_sizes = marker_sizes
        else:
            marker_sizes = np.full(len(entities), 8, dtype=np.float32)
            self.entity_sizes = marker_sizes

        self.scatter.set_data(
            pos=positions,
            face_color=colors,
            edge_color='white',
            edge_width=0.5,
            size=marker_sizes
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
        if not selected_indices or self.entity_positions is None or len(self.entity_positions) == 0:
            self.highlight_scatter.set_data(pos=np.zeros((0, 3)))
            return

        # Filter valid indices
        valid_indices = [i for i in selected_indices if i < len(self.entity_positions)]
        if not valid_indices:
            self.highlight_scatter.set_data(pos=np.zeros((0, 3)))
            return

        # Get positions of selected entities
        selected_positions = self.entity_positions[valid_indices]

        # Create highlight colors (gold with red edge)
        colors = np.full((len(valid_indices), 4), [1.0, 0.85, 0.0, 1.0], dtype=np.float32)

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

        if self.select_mode == "NONE":
            return

        if self.select_mode == "PAINT":
            self.is_painting = True
            self._do_paint_select(event)
            return

        if self.select_mode == "CLICK":
            self._do_click_select(event)

    def _on_mouse_move(self, event):
        """Handle mouse move for paint selection"""
        if self.is_painting and self.select_mode == "PAINT":
            self._do_paint_select(event)

    def _on_mouse_release(self, event):
        """Handle mouse release"""
        self.is_painting = False

    def _do_click_select(self, event):
        """Perform click selection - find nearest entity"""
        if self.entity_positions is None or len(self.entity_positions) == 0:
            return

        # Get click position
        click_pos = event.pos

        # Transform entity positions to screen coordinates
        transform = self.view.scene.transform
        screen_positions = transform.map(self.entity_positions)[:, :2]

        # Find nearest entity to click
        distances = np.sqrt(np.sum((screen_positions - click_pos[:2])**2, axis=1))
        nearest_idx = np.argmin(distances)

        # Only select if within reasonable distance (50 pixels)
        if distances[nearest_idx] < 50:
            shift = 'Shift' in event.modifiers
            ctrl = 'Control' in event.modifiers
            self.entity_clicked.emit(nearest_idx, shift, ctrl)

    def _do_paint_select(self, event):
        """Perform paint selection - select entities within brush radius"""
        if self.entity_positions is None or len(self.entity_positions) == 0:
            return

        click_pos = event.pos

        # Transform entity positions to screen coordinates
        transform = self.view.scene.transform
        screen_positions = transform.map(self.entity_positions)[:, :2]

        # Find entities within brush radius
        distances = np.sqrt(np.sum((screen_positions - click_pos[:2])**2, axis=1))

        # Emit signal for each entity within brush
        for idx in np.where(distances < self.brush_size)[0]:
            self.entity_clicked.emit(idx, True, False)  # Always additive in paint mode

    def set_mesh(self, vertices, faces, color=(0.5, 0.8, 0.5, 0.5)):
        """Display a mesh"""
        if self.mesh_visual is not None:
            self.mesh_visual.parent = None

        if vertices is not None and faces is not None:
            self.mesh_visual = visuals.Mesh(
                vertices=vertices,
                faces=faces,
                color=color,
                parent=self.view.scene
            )
        self.canvas.update()

    def clear_mesh(self):
        """Remove the mesh"""
        if self.mesh_visual is not None:
            self.mesh_visual.parent = None
            self.mesh_visual = None
        self.canvas.update()


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

    def apply_size_filter(self, min_size, max_size, item_db):
        """Filter entities by size"""
        self.display_mapping = []
        for i, ent in enumerate(self.entities):
            db_key = ent['id'].lstrip('0') or '0'
            info = item_db.get(db_key, {})
            try:
                size = float(info.get('size', 0))
            except:
                size = 0
            if min_size <= size <= max_size:
                self.display_mapping.append(i)
        self._refresh_list()


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


class QuaternionViewer(QGroupBox):
    """Quaternion visualization and Euler angle conversion"""

    rotation_changed = pyqtSignal(float, float, float, float)  # x, y, z, w

    def __init__(self, parent=None):
        super().__init__("Quaternion Viewer", parent)
        self._setup_ui()
        self.is_updating = False

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Quaternion display
        quat_label = QLabel("Quaternion (X, Y, Z, W):")
        quat_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(quat_label)

        self.quat_display = QLabel("X: 0.000  Y: 0.000  Z: 0.000  W: 1.000")
        self.quat_display.setStyleSheet("font-family: monospace; background: #1a1a2e; padding: 5px;")
        layout.addWidget(self.quat_display)

        # Euler angles
        euler_label = QLabel("Euler Angles (degrees):")
        euler_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(euler_label)

        self.euler_sliders = {}
        self.euler_spinboxes = {}

        for axis, name in [('roll', 'Roll (X)'), ('pitch', 'Pitch (Y)'), ('yaw', 'Yaw (Z)')]:
            row = QHBoxLayout()

            label = QLabel(f"{name}:")
            label.setMinimumWidth(70)
            row.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(-180, 180)
            slider.setValue(0)
            slider.valueChanged.connect(lambda v, a=axis: self._on_euler_slider_change(a))
            row.addWidget(slider, stretch=2)

            spinbox = QDoubleSpinBox()
            spinbox.setRange(-180, 180)
            spinbox.setDecimals(1)
            spinbox.setValue(0)
            spinbox.valueChanged.connect(lambda v, a=axis: self._on_euler_spinbox_change(a))
            row.addWidget(spinbox)

            self.euler_sliders[axis] = slider
            self.euler_spinboxes[axis] = spinbox

            layout.addLayout(row)

        # Apply button
        apply_btn = QPushButton("Apply Rotation")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_rotation)
        layout.addWidget(apply_btn)

    def update_quaternion(self, x, y, z, w):
        """Update display from quaternion values"""
        self.is_updating = True

        self.quat_display.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}  W: {w:.3f}")

        # Convert to Euler
        roll, pitch, yaw = self.quaternion_to_euler(x, y, z, w)

        for axis, val in [('roll', roll), ('pitch', pitch), ('yaw', yaw)]:
            self.euler_sliders[axis].setValue(int(val))
            self.euler_spinboxes[axis].setValue(val)

        self.is_updating = False

    def _on_euler_slider_change(self, axis):
        if self.is_updating:
            return
        self.euler_spinboxes[axis].blockSignals(True)
        self.euler_spinboxes[axis].setValue(self.euler_sliders[axis].value())
        self.euler_spinboxes[axis].blockSignals(False)
        self._update_quat_preview()

    def _on_euler_spinbox_change(self, axis):
        if self.is_updating:
            return
        self.euler_sliders[axis].blockSignals(True)
        self.euler_sliders[axis].setValue(int(self.euler_spinboxes[axis].value()))
        self.euler_sliders[axis].blockSignals(False)
        self._update_quat_preview()

    def _update_quat_preview(self):
        """Update quaternion preview from Euler angles"""
        roll = self.euler_spinboxes['roll'].value()
        pitch = self.euler_spinboxes['pitch'].value()
        yaw = self.euler_spinboxes['yaw'].value()

        x, y, z, w = self.euler_to_quaternion(roll, pitch, yaw)
        self.quat_display.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}  W: {w:.3f}")

    def _apply_rotation(self):
        """Emit rotation changed signal"""
        roll = self.euler_spinboxes['roll'].value()
        pitch = self.euler_spinboxes['pitch'].value()
        yaw = self.euler_spinboxes['yaw'].value()

        x, y, z, w = self.euler_to_quaternion(roll, pitch, yaw)
        self.rotation_changed.emit(x, y, z, w)

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        """Convert quaternion to Euler angles (roll, pitch, yaw) in degrees"""
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

    @staticmethod
    def euler_to_quaternion(roll, pitch, yaw):
        """Convert Euler angles (in degrees) to quaternion (x, y, z, w)"""
        roll_rad = math.radians(roll)
        pitch_rad = math.radians(pitch)
        yaw_rad = math.radians(yaw)

        cy = math.cos(yaw_rad * 0.5)
        sy = math.sin(yaw_rad * 0.5)
        cp = math.cos(pitch_rad * 0.5)
        sp = math.sin(pitch_rad * 0.5)
        cr = math.cos(roll_rad * 0.5)
        sr = math.sin(roll_rad * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return x, y, z, w


class BatchEditor(QGroupBox):
    """Batch editor for entity properties"""

    changes_committed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__("Batch Editor", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Create entry fields
        form = QFormLayout()

        self.entries = {}
        fields = [
            ('index', 'Entity Index'),
            ('atk', 'Attack Type'),
            ('mov', 'Move Type'),
            ('esc', 'Escape Type'),
            ('spd', 'Speed'),
            ('pth', 'Path ID'),
            ('scale', 'Scale'),
            ('plus_type', 'Plus Type'),
            ('parent_type', 'Parent Type'),
            ('clash_type', 'Clash Type'),
        ]

        for key, label in fields:
            entry = QLineEdit()
            entry.setPlaceholderText(f"Enter {label.lower()}")
            self.entries[key] = entry
            form.addRow(f"{label}:", entry)

        layout.addLayout(form)

        # Commit button
        commit_btn = QPushButton("COMMIT CHANGES")
        commit_btn.setObjectName("primary")
        commit_btn.clicked.connect(self._commit_changes)
        layout.addWidget(commit_btn)

    def update_for_selection(self, entities, selected_indices):
        """Update fields for selected entities"""
        if not selected_indices:
            for entry in self.entries.values():
                entry.clear()
            return

        # Show values from last selected entity
        ent = entities[selected_indices[-1]]
        self.entries['index'].setText(ent.get('id', ''))
        self.entries['atk'].setText(ent.get('atk', ''))
        self.entries['mov'].setText(ent.get('mov', ''))
        self.entries['esc'].setText(ent.get('esc', ''))
        self.entries['spd'].setText(ent.get('spd', ''))
        self.entries['pth'].setText(ent.get('pth', ''))
        self.entries['scale'].setText(ent.get('scale', ''))
        self.entries['plus_type'].setText(ent.get('plus_type', ''))
        self.entries['parent_type'].setText(ent.get('parent_type', ''))
        self.entries['clash_type'].setText(ent.get('clash_type', ''))

    def _commit_changes(self):
        """Emit changes to be committed"""
        changes = {}
        for key, entry in self.entries.items():
            text = entry.text().strip()
            if text:
                changes[key] = text
        if changes:
            self.changes_committed.emit(changes)


class SizeFilterPanel(QGroupBox):
    """Size filter panel"""

    filter_changed = pyqtSignal(float, float, bool)

    def __init__(self, parent=None):
        super().__init__("Size Filter", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Enable checkbox
        self.enabled = QCheckBox("Enable Size Filter")
        self.enabled.stateChanged.connect(self._emit_filter)
        layout.addWidget(self.enabled)

        # Min size
        min_row = QHBoxLayout()
        min_row.addWidget(QLabel("Min:"))
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(0, 100000000)
        self.min_spin.setValue(0)
        self.min_spin.valueChanged.connect(self._emit_filter)
        min_row.addWidget(self.min_spin)
        layout.addLayout(min_row)

        # Max size
        max_row = QHBoxLayout()
        max_row.addWidget(QLabel("Max:"))
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(0, 100000000)
        self.max_spin.setValue(10000000)
        self.max_spin.valueChanged.connect(self._emit_filter)
        max_row.addWidget(self.max_spin)
        layout.addLayout(max_row)

    def _emit_filter(self):
        self.filter_changed.emit(
            self.min_spin.value(),
            self.max_spin.value(),
            self.enabled.isChecked()
        )


class MeshGeneratorPanel(QGroupBox):
    """Mesh generation panel"""

    generate_requested = pyqtSignal(dict)
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Mesh Generator", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Grid resolution
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Resolution:"))
        self.resolution = QSlider(Qt.Horizontal)
        self.resolution.setRange(5, 100)
        self.resolution.setValue(20)
        res_row.addWidget(self.resolution)
        self.res_label = QLabel("20")
        self.resolution.valueChanged.connect(lambda v: self.res_label.setText(str(v)))
        res_row.addWidget(self.res_label)
        layout.addLayout(res_row)

        # Averaging
        avg_row = QHBoxLayout()
        avg_row.addWidget(QLabel("Averaging:"))
        self.averaging = QSlider(Qt.Horizontal)
        self.averaging.setRange(5, 100)
        self.averaging.setValue(15)
        avg_row.addWidget(self.averaging)
        self.avg_label = QLabel("1.5")
        self.averaging.valueChanged.connect(lambda v: self.avg_label.setText(f"{v/10:.1f}"))
        avg_row.addWidget(self.avg_label)
        layout.addLayout(avg_row)

        # Options
        self.selected_only = QCheckBox("Selected entities only")
        layout.addWidget(self.selected_only)

        self.exclude_large = QCheckBox("Exclude size >9M")
        self.exclude_large.setChecked(True)
        layout.addWidget(self.exclude_large)

        self.floor_priority = QCheckBox("Prioritize floors")
        self.floor_priority.setChecked(True)
        layout.addWidget(self.floor_priority)

        # Mesh alpha
        alpha_row = QHBoxLayout()
        alpha_row.addWidget(QLabel("Opacity:"))
        self.mesh_alpha = QSlider(Qt.Horizontal)
        self.mesh_alpha.setRange(10, 100)
        self.mesh_alpha.setValue(50)
        alpha_row.addWidget(self.mesh_alpha)
        layout.addLayout(alpha_row)

        # Buttons
        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Generate")
        gen_btn.setObjectName("success")
        gen_btn.clicked.connect(self._generate)
        btn_row.addWidget(gen_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_requested.emit)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)

    def _generate(self):
        self.generate_requested.emit({
            'resolution': self.resolution.value(),
            'averaging': self.averaging.value() / 10.0,
            'selected_only': self.selected_only.isChecked(),
            'exclude_large': self.exclude_large.isChecked(),
            'floor_priority': self.floor_priority.isChecked(),
            'alpha': self.mesh_alpha.value() / 100.0,
        })


class PatternPlacerPanel(QGroupBox):
    """Pattern placement tool"""

    pattern_applied = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Pattern Placer", parent)
        self._setup_ui()
        self.waypoints = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Pattern type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Pattern:"))
        self.pattern_group = QButtonGroup(self)
        for ptype in ["Circle", "Line", "Path"]:
            rb = QRadioButton(ptype)
            if ptype == "Circle":
                rb.setChecked(True)
            self.pattern_group.addButton(rb)
            type_row.addWidget(rb)
        layout.addLayout(type_row)

        # Selection count
        self.count_label = QLabel("Selected: 0")
        self.count_label.setStyleSheet(f"color: {Theme.ACCENT};")
        layout.addWidget(self.count_label)

        # Radius (for circle)
        radius_row = QHBoxLayout()
        radius_row.addWidget(QLabel("Radius:"))
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(1, 500)
        self.radius_slider.setValue(50)
        radius_row.addWidget(self.radius_slider)
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 5000)
        self.radius_spin.setValue(50)
        self.radius_slider.valueChanged.connect(self.radius_spin.setValue)
        self.radius_spin.valueChanged.connect(self.radius_slider.setValue)
        radius_row.addWidget(self.radius_spin)
        layout.addLayout(radius_row)

        # Spacing (for line/path)
        spacing_row = QHBoxLayout()
        spacing_row.addWidget(QLabel("Spacing:"))
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(1, 100)
        self.spacing_slider.setValue(10)
        spacing_row.addWidget(self.spacing_slider)
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(1, 1000)
        self.spacing_spin.setValue(10)
        self.spacing_slider.valueChanged.connect(self.spacing_spin.setValue)
        self.spacing_spin.valueChanged.connect(self.spacing_slider.setValue)
        spacing_row.addWidget(self.spacing_spin)
        layout.addLayout(spacing_row)

        # Waypoints (for path)
        wp_label = QLabel("Waypoints:")
        layout.addWidget(wp_label)
        self.waypoint_list = QListWidget()
        self.waypoint_list.setMaximumHeight(80)
        layout.addWidget(self.waypoint_list)

        wp_btn_row = QHBoxLayout()
        add_wp_btn = QPushButton("Add from Selection")
        add_wp_btn.clicked.connect(lambda: self.pattern_applied.emit("add_waypoint", {}))
        wp_btn_row.addWidget(add_wp_btn)
        clear_wp_btn = QPushButton("Clear")
        clear_wp_btn.clicked.connect(self._clear_waypoints)
        wp_btn_row.addWidget(clear_wp_btn)
        layout.addLayout(wp_btn_row)

        # Apply button
        apply_btn = QPushButton("APPLY PATTERN")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_pattern)
        layout.addWidget(apply_btn)

    def update_count(self, count):
        self.count_label.setText(f"Selected: {count}")

    def add_waypoint(self, x, y, z):
        self.waypoints.append((x, y, z))
        self.waypoint_list.addItem(f"WP{len(self.waypoints)}: ({x:.1f}, {y:.1f}, {z:.1f})")

    def _clear_waypoints(self):
        self.waypoints = []
        self.waypoint_list.clear()

    def _apply_pattern(self):
        checked = self.pattern_group.checkedButton()
        if checked:
            pattern_type = checked.text()
            params = {
                'radius': self.radius_spin.value(),
                'spacing': self.spacing_spin.value(),
                'waypoints': self.waypoints.copy(),
            }
            self.pattern_applied.emit(pattern_type, params)


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
        self.display_mapping = []
        self.item_db = {}
        self.undo_stack = []
        self.max_undo = 50

        # Visualization options
        self.use_size_scaling = False
        self.select_mode = "CLICK"

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
                            # Parse size value
                            try:
                                self.item_db[key]['size_val'] = float(row.get('size', 0))
                            except:
                                self.item_db[key]['size_val'] = 0.0
                    self.statusBar().showMessage(f"Loaded {len(self.item_db)} items from database")
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

        # Center panel - 3D View + toolbar
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Selection mode
        toolbar_layout.addWidget(QLabel("Select:"))
        self.select_mode_group = QButtonGroup(self)
        for mode in ["NONE", "CLICK", "PAINT"]:
            rb = QRadioButton(mode.title())
            if mode == "CLICK":
                rb.setChecked(True)
            rb.toggled.connect(lambda checked, m=mode: self._set_select_mode(m) if checked else None)
            self.select_mode_group.addButton(rb)
            toolbar_layout.addWidget(rb)

        # Brush size for paint mode
        toolbar_layout.addWidget(QLabel("  Brush:"))
        self.brush_size_slider = QSlider(Qt.Horizontal)
        self.brush_size_slider.setRange(10, 100)
        self.brush_size_slider.setValue(25)
        self.brush_size_slider.setMaximumWidth(100)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        toolbar_layout.addWidget(self.brush_size_slider)

        # Size scaling toggle
        self.size_scaling_cb = QCheckBox("Size by CSV")
        self.size_scaling_cb.stateChanged.connect(self._on_size_scaling_changed)
        toolbar_layout.addWidget(self.size_scaling_cb)

        # Zoom fit button
        zoom_btn = QPushButton("Zoom Fit")
        zoom_btn.clicked.connect(self._zoom_to_fit)
        toolbar_layout.addWidget(zoom_btn)

        toolbar_layout.addStretch()
        center_layout.addWidget(toolbar)

        # 3D View
        self.vispy_canvas = VispyCanvas()
        self.vispy_canvas.entity_clicked.connect(self._on_entity_clicked)
        center_layout.addWidget(self.vispy_canvas)

        splitter.addWidget(center_panel)

        # Right panel - Tools (tabbed)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for tools
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Tab widget for tools
        tabs = QTabWidget()

        # Tab 1: Info & Position
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setAlignment(Qt.AlignTop)

        self.entity_info = EntityInfoPanel()
        tab1_layout.addWidget(self.entity_info)

        self.position_editor = PositionEditor()
        self.position_editor.position_changed.connect(self._on_position_changed)
        tab1_layout.addWidget(self.position_editor)

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

        tab1_layout.addWidget(actions_group)
        tab1_layout.addStretch()

        tabs.addTab(tab1, "Info")

        # Tab 2: Rotation & Batch
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setAlignment(Qt.AlignTop)

        self.quat_viewer = QuaternionViewer()
        self.quat_viewer.rotation_changed.connect(self._on_rotation_changed)
        tab2_layout.addWidget(self.quat_viewer)

        self.batch_editor = BatchEditor()
        self.batch_editor.changes_committed.connect(self._on_batch_changes)
        tab2_layout.addWidget(self.batch_editor)

        tab2_layout.addStretch()
        tabs.addTab(tab2, "Edit")

        # Tab 3: Tools
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setAlignment(Qt.AlignTop)

        self.size_filter = SizeFilterPanel()
        self.size_filter.filter_changed.connect(self._on_size_filter_changed)
        tab3_layout.addWidget(self.size_filter)

        self.mesh_generator = MeshGeneratorPanel()
        self.mesh_generator.generate_requested.connect(self._generate_mesh)
        self.mesh_generator.clear_requested.connect(self._clear_mesh)
        tab3_layout.addWidget(self.mesh_generator)

        self.pattern_placer = PatternPlacerPanel()
        self.pattern_placer.pattern_applied.connect(self._apply_pattern)
        tab3_layout.addWidget(self.pattern_placer)

        tab3_layout.addStretch()
        tabs.addTab(tab3, "Tools")

        # Visualization tab
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.setAlignment(Qt.AlignTop)

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

        # Point size
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Point Size:"))
        self.point_size_slider = QSlider(Qt.Horizontal)
        self.point_size_slider.setRange(2, 30)
        self.point_size_slider.setValue(8)
        self.point_size_slider.valueChanged.connect(self._on_point_size_changed)
        size_row.addWidget(self.point_size_slider)
        viz_layout.addLayout(size_row)

        # Entity opacity
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        viz_layout.addLayout(opacity_row)

        tab4_layout.addWidget(viz_group)
        tab4_layout.addStretch()
        tabs.addTab(tab4, "View")

        scroll.setWidget(tabs)
        right_layout.addWidget(scroll)

        splitter.addWidget(right_panel)

        # Set initial splitter sizes
        splitter.setSizes([250, 850, 350])

    def _setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        load_csv = QAction("Load CSV Database...", self)
        load_csv.triggered.connect(self._load_csv_dialog)
        file_menu.addAction(load_csv)

        file_menu.addSeparator()

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

        edit_menu.addSeparator()

        select_all = QAction("Select All", self)
        select_all.setShortcut(QKeySequence.SelectAll)
        select_all.triggered.connect(self._select_all)
        edit_menu.addAction(select_all)

        deselect_all = QAction("Deselect All", self)
        deselect_all.setShortcut("Escape")
        deselect_all.triggered.connect(self._deselect_all)
        edit_menu.addAction(deselect_all)

        # View menu
        view_menu = menubar.addMenu("View")

        zoom_fit = QAction("Zoom to Fit", self)
        zoom_fit.setShortcut("Ctrl+0")
        zoom_fit.triggered.connect(self._zoom_to_fit)
        view_menu.addAction(zoom_fit)

    def _load_csv_dialog(self):
        """Open dialog to load CSV database"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load CSV Database", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.item_db = {}
                for row in reader:
                    key = row.get('index', '').lstrip('0') or '0'
                    self.item_db[key] = row
                    try:
                        self.item_db[key]['size_val'] = float(row.get('size', 0))
                    except:
                        self.item_db[key]['size_val'] = 0.0

            # Refresh entity list with new database
            self.entity_list.set_entities(self.entities, self.item_db)
            self._refresh_3d_view()
            self.statusBar().showMessage(f"Loaded {len(self.item_db)} items from {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")

    def _set_select_mode(self, mode):
        """Set selection mode"""
        self.select_mode = mode
        self.vispy_canvas.select_mode = mode

    def _on_brush_size_changed(self, value):
        """Update brush size"""
        self.vispy_canvas.brush_size = value

    def _on_size_scaling_changed(self, state):
        """Toggle size scaling"""
        self.use_size_scaling = state == Qt.Checked
        self._refresh_3d_view()

    def _on_entity_clicked(self, index, shift, ctrl):
        """Handle entity click from 3D view"""
        if shift or ctrl:
            # Add to selection
            if index not in self.selected_indices:
                self.selected_indices.append(index)
        else:
            # Replace selection
            self.selected_indices = [index]

        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _on_selection_changed(self, indices):
        """Handle entity selection change from list"""
        self.selected_indices = indices
        self._update_selection_ui()

    def _update_selection_ui(self):
        """Update all UI elements for current selection"""
        self.vispy_canvas.update_selection(self.selected_indices)
        self.position_editor.update_for_selection(self.entities, self.selected_indices)
        self.pattern_placer.update_count(len(self.selected_indices))

        if self.selected_indices:
            ent = self.entities[self.selected_indices[-1]]
            self.entity_info.update_info(ent, self.item_db)
            self.quat_viewer.update_quaternion(ent['rx'], ent['ry'], ent['rz'], ent['rw'])
            self.batch_editor.update_for_selection(self.entities, self.selected_indices)

            db_key = ent['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            name = info.get('obj_en', f"Entity {ent['id']}")
            self.statusBar().showMessage(
                f"Selected: {name} | ID: {ent['id']} | Pos: ({ent['x']:.1f}, {ent['y']:.1f}, {ent['z']:.1f})"
            )
        else:
            self.entity_info.update_info(None)
            self.quat_viewer.update_quaternion(0, 0, 0, 1)

    def _select_all(self):
        """Select all entities"""
        self.selected_indices = list(range(len(self.entities)))
        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _deselect_all(self):
        """Deselect all entities"""
        self.selected_indices = []
        self.entity_list.set_selection([])
        self._update_selection_ui()

    def _on_position_changed(self):
        """Handle position change from editor"""
        if not self.selected_indices:
            return

        self._save_undo_state("Position Change")

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

            self._sync_entity_raw(ent)

        self._refresh_3d_view()
        self.statusBar().showMessage("Position updated")

    def _on_rotation_changed(self, x, y, z, w):
        """Handle rotation change from quaternion viewer"""
        if not self.selected_indices:
            QMessageBox.warning(self, "Selection", "Select at least one entity to rotate.")
            return

        self._save_undo_state("Apply Rotation")

        for idx in self.selected_indices:
            ent = self.entities[idx]
            ent['rx'] = x
            ent['ry'] = y
            ent['rz'] = z
            ent['rw'] = w
            self._sync_entity_rotation(ent)

        self._update_selection_ui()
        QMessageBox.information(self, "Success", f"Applied rotation to {len(self.selected_indices)} entities.")

    def _on_batch_changes(self, changes):
        """Handle batch editor changes"""
        if not self.selected_indices:
            QMessageBox.warning(self, "Selection", "Select at least one entity to edit.")
            return

        self._save_undo_state("Batch Edit")

        for idx in self.selected_indices:
            ent = self.entities[idx]
            for key, value in changes.items():
                if key in ent:
                    ent[key] = value
            # TODO: Sync raw data for batch changes

        self._update_selection_ui()
        self.statusBar().showMessage(f"Updated {len(self.selected_indices)} entities")

    def _on_size_filter_changed(self, min_size, max_size, enabled):
        """Handle size filter change"""
        if enabled:
            self.entity_list.apply_size_filter(min_size, max_size, self.item_db)
        else:
            self.entity_list.set_entities(self.entities, self.item_db)

    def _zoom_to_fit(self):
        """Zoom camera to fit all entities"""
        self._refresh_3d_view()

    def _refresh_3d_view(self):
        """Refresh the 3D view with current settings"""
        if not self.entities:
            return

        # Get sizes for size scaling
        sizes = None
        if self.use_size_scaling:
            sizes = []
            for ent in self.entities:
                db_key = ent['id'].lstrip('0') or '0'
                # Exclude entity IDs 3226 and 3227 as outliers
                if ent['id'].lstrip('0') in ['3226', '3227']:
                    sizes.append(200)  # Default size for outliers
                else:
                    info = self.item_db.get(db_key, {})
                    sizes.append(info.get('size_val', 0))

        self.vispy_canvas.set_entities(
            self.entities,
            self.selected_indices,
            sizes=sizes,
            use_size_scaling=self.use_size_scaling
        )

    def _on_color_mode_changed(self, mode):
        """Change entity coloring mode"""
        if not self.entities:
            return

        positions = self.vispy_canvas.entity_positions
        if positions is None:
            return

        n = len(self.entities)
        colors = np.zeros((n, 4), dtype=np.float32)
        opacity = self.opacity_slider.value() / 100.0

        if mode == "Default":
            colors[:] = [0.3, 0.7, 0.9, opacity]

        elif mode == "By ID":
            for i, ent in enumerate(self.entities):
                id_hash = hash(ent['id']) % 360
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
                colors[i] = [r, g, b, opacity]

        elif mode == "By Size":
            sizes = []
            for ent in self.entities:
                db_key = ent['id'].lstrip('0') or '0'
                info = self.item_db.get(db_key, {})
                sizes.append(info.get('size_val', 0))

            sizes = np.array(sizes)
            if sizes.max() > sizes.min():
                normalized = (sizes - sizes.min()) / (sizes.max() - sizes.min())
            else:
                normalized = np.zeros(n)

            for i, val in enumerate(normalized):
                colors[i] = [val, 0.3, 1 - val, opacity]

        elif mode == "By Height":
            heights = np.array([e['y'] for e in self.entities])
            if heights.max() > heights.min():
                normalized = (heights - heights.min()) / (heights.max() - heights.min())
            else:
                normalized = np.zeros(n)

            for i, val in enumerate(normalized):
                colors[i] = [val, val, 1 - val, opacity]

        elif mode == "By Map":
            map_colors = [
                [0.3, 0.7, 0.9, opacity],
                [0.9, 0.5, 0.3, opacity],
                [0.4, 0.9, 0.4, opacity],
                [0.9, 0.3, 0.6, opacity],
                [0.7, 0.7, 0.3, opacity],
            ]
            for i, ent in enumerate(self.entities):
                map_idx = ent.get('map_index', 0) % len(map_colors)
                colors[i] = map_colors[map_idx]

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
            self._on_color_mode_changed(self.color_mode.currentText())

    def _on_opacity_changed(self, value):
        """Change entity opacity"""
        if self.vispy_canvas.entity_positions is not None:
            self._on_color_mode_changed(self.color_mode.currentText())

    def _generate_mesh(self, params):
        """Generate mesh from entity positions"""
        try:
            from scipy.interpolate import griddata
            from scipy.spatial import Delaunay
        except ImportError:
            QMessageBox.critical(self, "Error", "scipy is required for mesh generation. Install with: pip install scipy")
            return

        if not self.entities:
            QMessageBox.warning(self, "Error", "No entities loaded.")
            return

        # Get indices to use
        if params['selected_only']:
            if not self.selected_indices:
                QMessageBox.warning(self, "Error", "No entities selected.")
                return
            indices = self.selected_indices.copy()
        else:
            indices = list(range(len(self.entities)))

        # Filter by size
        if params['exclude_large']:
            filtered = []
            for i in indices:
                db_key = self.entities[i]['id'].lstrip('0') or '0'
                size = self.item_db.get(db_key, {}).get('size_val', 0)
                if size <= 9000000:
                    filtered.append(i)
            indices = filtered

        if len(indices) < 4:
            QMessageBox.warning(self, "Error", "Need at least 4 entities to generate mesh.")
            return

        # Collect points
        points = np.array([[self.entities[i]['x'], self.entities[i]['y'], self.entities[i]['z']] for i in indices])

        # Average points
        if params['averaging'] > 0.5:
            points = self._average_points(points, params['averaging'])

        if len(points) < 4:
            QMessageBox.warning(self, "Error", "Too few points after averaging.")
            return

        resolution = params['resolution']
        alpha = params['alpha']

        try:
            if params['floor_priority']:
                # Floor mesh: XZ plane, interpolate Y
                x = points[:, 0]
                y = points[:, 1]
                z = points[:, 2]

                xi = np.linspace(x.min(), x.max(), resolution)
                zi = np.linspace(z.min(), z.max(), resolution)
                Xi, Zi = np.meshgrid(xi, zi)

                Yi = griddata((x, z), y, (Xi, Zi), method='linear', fill_value=np.nan)

                # Create mesh vertices and faces
                vertices = []
                faces = []

                for i in range(resolution):
                    for j in range(resolution):
                        if not np.isnan(Yi[i, j]):
                            vertices.append([-Xi[i, j], Zi[i, j], Yi[i, j]])

                vertices = np.array(vertices, dtype=np.float32)

                # Create faces from grid
                valid_idx = {}
                idx = 0
                for i in range(resolution):
                    for j in range(resolution):
                        if not np.isnan(Yi[i, j]):
                            valid_idx[(i, j)] = idx
                            idx += 1

                for i in range(resolution - 1):
                    for j in range(resolution - 1):
                        if (i, j) in valid_idx and (i+1, j) in valid_idx and \
                           (i, j+1) in valid_idx and (i+1, j+1) in valid_idx:
                            v00 = valid_idx[(i, j)]
                            v10 = valid_idx[(i+1, j)]
                            v01 = valid_idx[(i, j+1)]
                            v11 = valid_idx[(i+1, j+1)]
                            faces.append([v00, v10, v11])
                            faces.append([v00, v11, v01])

                faces = np.array(faces, dtype=np.uint32)

            else:
                # General mesh using Delaunay
                tri = Delaunay(points[:, [0, 2]])  # XZ projection

                # Transform vertices for display
                vertices = np.array([[-p[0], p[2], p[1]] for p in points], dtype=np.float32)
                faces = tri.simplices.astype(np.uint32)

            self.vispy_canvas.set_mesh(vertices, faces, color=(0.5, 0.8, 0.5, alpha))
            self.statusBar().showMessage(f"Mesh generated from {len(points)} points")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate mesh: {e}")

    def _average_points(self, points, cell_size):
        """Average nearby points"""
        if len(points) == 0:
            return points

        x_min, y_min, z_min = points.min(axis=0)

        cells = {}
        for p in points:
            cx = int((p[0] - x_min) / cell_size)
            cy = int((p[1] - y_min) / cell_size)
            cz = int((p[2] - z_min) / cell_size)
            key = (cx, cy, cz)

            if key not in cells:
                cells[key] = []
            cells[key].append(p)

        averaged = []
        for cell_points in cells.values():
            avg_point = np.mean(cell_points, axis=0)
            averaged.append(avg_point)

        return np.array(averaged)

    def _clear_mesh(self):
        """Clear the generated mesh"""
        self.vispy_canvas.clear_mesh()
        self.statusBar().showMessage("Mesh cleared")

    def _apply_pattern(self, pattern_type, params):
        """Apply pattern to selected entities"""
        if pattern_type == "add_waypoint":
            # Add waypoint from selection
            if not self.selected_indices:
                QMessageBox.warning(self, "Selection", "Select at least one entity to use as waypoint.")
                return
            x_avg = sum(self.entities[i]['x'] for i in self.selected_indices) / len(self.selected_indices)
            y_avg = sum(self.entities[i]['y'] for i in self.selected_indices) / len(self.selected_indices)
            z_avg = sum(self.entities[i]['z'] for i in self.selected_indices) / len(self.selected_indices)
            self.pattern_placer.add_waypoint(x_avg, y_avg, z_avg)
            return

        if not self.selected_indices:
            QMessageBox.warning(self, "Selection", "Select entities to arrange in pattern.")
            return

        count = len(self.selected_indices)

        if pattern_type == "Path" and len(params['waypoints']) < 2:
            QMessageBox.warning(self, "Waypoints", "Path mode requires at least 2 waypoints.")
            return

        self._save_undo_state(f"Apply {pattern_type} Pattern")

        # Calculate center
        center_x = sum(self.entities[i]['x'] for i in self.selected_indices) / count
        center_y = sum(self.entities[i]['y'] for i in self.selected_indices) / count
        center_z = sum(self.entities[i]['z'] for i in self.selected_indices) / count

        if pattern_type == "Circle":
            radius = params['radius']
            for idx, entity_idx in enumerate(self.selected_indices):
                angle = (2 * math.pi * idx) / count
                self.entities[entity_idx]['x'] = center_x + radius * math.cos(angle)
                self.entities[entity_idx]['z'] = center_z + radius * math.sin(angle)
                self.entities[entity_idx]['y'] = center_y
                self._sync_entity_raw(self.entities[entity_idx])

        elif pattern_type == "Line":
            spacing = params['spacing']
            start_offset = -(count - 1) * spacing / 2

            for idx, entity_idx in enumerate(self.selected_indices):
                self.entities[entity_idx]['x'] = center_x + start_offset + (idx * spacing)
                self.entities[entity_idx]['y'] = center_y
                self.entities[entity_idx]['z'] = center_z
                self._sync_entity_raw(self.entities[entity_idx])

        elif pattern_type == "Path":
            waypoints = params['waypoints']
            spacing = params['spacing']

            # Calculate total path length
            total_length = 0
            for i in range(len(waypoints) - 1):
                dx = waypoints[i+1][0] - waypoints[i][0]
                dy = waypoints[i+1][1] - waypoints[i][1]
                dz = waypoints[i+1][2] - waypoints[i][2]
                total_length += math.sqrt(dx*dx + dy*dy + dz*dz)

            # Distribute entities along path
            for idx, entity_idx in enumerate(self.selected_indices):
                t = idx / max(1, count - 1)
                target_dist = t * total_length

                # Find position along path
                current_dist = 0
                for i in range(len(waypoints) - 1):
                    dx = waypoints[i+1][0] - waypoints[i][0]
                    dy = waypoints[i+1][1] - waypoints[i][1]
                    dz = waypoints[i+1][2] - waypoints[i][2]
                    seg_len = math.sqrt(dx*dx + dy*dy + dz*dz)

                    if current_dist + seg_len >= target_dist:
                        # Interpolate within this segment
                        seg_t = (target_dist - current_dist) / seg_len if seg_len > 0 else 0
                        self.entities[entity_idx]['x'] = waypoints[i][0] + dx * seg_t
                        self.entities[entity_idx]['y'] = waypoints[i][1] + dy * seg_t
                        self.entities[entity_idx]['z'] = waypoints[i][2] + dz * seg_t
                        break
                    current_dist += seg_len
                else:
                    # Place at last waypoint
                    self.entities[entity_idx]['x'] = waypoints[-1][0]
                    self.entities[entity_idx]['y'] = waypoints[-1][1]
                    self.entities[entity_idx]['z'] = waypoints[-1][2]

                self._sync_entity_raw(self.entities[entity_idx])

        self._refresh_3d_view()
        self._update_selection_ui()
        self.statusBar().showMessage(f"Applied {pattern_type} pattern to {count} entities")

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
        self._refresh_3d_view()

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

    def _sync_entity_rotation(self, ent):
        """Sync rotation values back to raw entity data"""
        if len(ent['r_indices']) != 4:
            return

        original_content = ent['r_raw_content']
        new_parts = []
        last_idx = 0
        ax_keys = ['rx', 'ry', 'rz', 'rw']

        for i in range(4):
            start, end = ent['r_indices'][i]
            new_parts.append(original_content[last_idx:start])
            new_parts.append(self._format_strict(ent[ax_keys[i]], end - start))
            last_idx = end
        new_parts.append(original_content[last_idx:])

        ent['r_raw_content'] = "".join(new_parts)

        s, e = "<roll>", "</roll>"
        si = ent['raw'].find(s) + len(s)
        ei = ent['raw'].find(e)
        if si != -1 and ei != -1:
            final_block = ent['r_raw_content'][:ei-si].ljust(ei-si)
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
        self._refresh_3d_view()

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
