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
import copy
import json
import numpy as np
from pathlib import Path

# Embedded item database from BK_LOC - KDX_MONO.csv
from embedded_item_db import EMBEDDED_ITEM_DB

# PyQt5 for modern UI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QAbstractItemView, QTabWidget,
    QGridLayout, QStatusBar, QMenuBar, QMenu, QAction, QToolBar,
    QRadioButton, QButtonGroup, QInputDialog, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint, QEvent, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QKeySequence, QCursor

# Vispy for GPU-accelerated 3D
from vispy import app, scene
from vispy.scene import visuals
from vispy.color import Color, ColorArray

# Optional pygame for controller support
PYGAME_AVAILABLE = False
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pass

# Gaudy theme definitions (vibrant 2000s colors)
THEMES_GAUDY = {
    "Light": {
        "bg": "#e0f0ff", "fg": "#000066", "accent": "#ff0099",
        "button_bg": "#ff0099", "button_fg": "#ffffff",
        "listbox_select_bg": "#ff0099", "listbox_select_fg": "#ffff00",
        "graph_bg": "#ffffff", "grid_color": "#ccddff", "axis_color": "#6699cc",
        "entity_default": "#00aaff", "entity_selected": "#ffff00", "entity_highlight": "#ff0099"
    },
    "Obsidian": {
        "bg": "#050008", "fg": "#00ffff", "accent": "#ff00ff",
        "button_bg": "#ff00ff", "button_fg": "#ffff00",
        "listbox_select_bg": "#ff00ff", "listbox_select_fg": "#00ffff",
        "graph_bg": "#000000", "grid_color": "#220044", "axis_color": "#4400aa",
        "entity_default": "#00ffff", "entity_selected": "#ffff00", "entity_highlight": "#ff00ff"
    },
    "Olive Grove": {
        "bg": "#1a2010", "fg": "#e0ff99", "accent": "#aaff00",
        "button_bg": "#aaff00", "button_fg": "#0a0f05",
        "listbox_select_bg": "#aaff00", "listbox_select_fg": "#0a0f05",
        "graph_bg": "#0a0f05", "grid_color": "#2a3520", "axis_color": "#4a5530",
        "entity_default": "#e0ff99", "entity_selected": "#ffff00", "entity_highlight": "#aaff00"
    },
    "Deep Ocean": {
        "bg": "#000a1a", "fg": "#00eeff", "accent": "#00ffff",
        "button_bg": "#00ffff", "button_fg": "#000510",
        "listbox_select_bg": "#00ffff", "listbox_select_fg": "#000510",
        "graph_bg": "#000510", "grid_color": "#002244", "axis_color": "#004488",
        "entity_default": "#00eeff", "entity_selected": "#ffff00", "entity_highlight": "#00ffff"
    },
    "Crimson Night": {
        "bg": "#100000", "fg": "#ff3333", "accent": "#ff0000",
        "button_bg": "#ff0000", "button_fg": "#ffffff",
        "listbox_select_bg": "#ff0000", "listbox_select_fg": "#ffff00",
        "graph_bg": "#050000", "grid_color": "#330000", "axis_color": "#880000",
        "entity_default": "#ff3333", "entity_selected": "#ffff00", "entity_highlight": "#ff0000"
    },
    "Burnished Oak": {
        "bg": "#1a0f00", "fg": "#ffdd44", "accent": "#ffaa00",
        "button_bg": "#ffaa00", "button_fg": "#0a0500",
        "listbox_select_bg": "#ffaa00", "listbox_select_fg": "#ffffcc",
        "graph_bg": "#0a0500", "grid_color": "#442200", "axis_color": "#996600",
        "entity_default": "#ffdd44", "entity_selected": "#ffff00", "entity_highlight": "#ffaa00"
    },
    "Amethyst": {
        "bg": "#110011", "fg": "#ff66ff", "accent": "#dd00ff",
        "button_bg": "#dd00ff", "button_fg": "#ffffff",
        "listbox_select_bg": "#dd00ff", "listbox_select_fg": "#ffff00",
        "graph_bg": "#080008", "grid_color": "#330033", "axis_color": "#880088",
        "entity_default": "#ff66ff", "entity_selected": "#ffff00", "entity_highlight": "#dd00ff"
    },
    "Void": {
        "bg": "#000000", "fg": "#cccccc", "accent": "#ff0000",
        "button_bg": "#ff0000", "button_fg": "#ffffff",
        "listbox_select_bg": "#ff0000", "listbox_select_fg": "#ffffff",
        "graph_bg": "#000000", "grid_color": "#222222", "axis_color": "#666666",
        "entity_default": "#cccccc", "entity_selected": "#ffffff", "entity_highlight": "#ff0000"
    },
    "Solar Flare": {
        "bg": "#110500", "fg": "#ffdd00", "accent": "#ff5500",
        "button_bg": "#ff5500", "button_fg": "#0a0300",
        "listbox_select_bg": "#ff5500", "listbox_select_fg": "#ffff00",
        "graph_bg": "#0a0300", "grid_color": "#442200", "axis_color": "#aa5500",
        "entity_default": "#ffdd00", "entity_selected": "#ffff00", "entity_highlight": "#ff5500"
    },
    "Sakura": {
        "bg": "#331025", "fg": "#ffbbdd", "accent": "#ff55aa",
        "button_bg": "#ff55aa", "button_fg": "#1a0812",
        "listbox_select_bg": "#ff55aa", "listbox_select_fg": "#ffffcc",
        "graph_bg": "#1a0812", "grid_color": "#442033", "axis_color": "#884466",
        "entity_default": "#ffbbdd", "entity_selected": "#ffff66", "entity_highlight": "#ff55aa"
    },
    "Northern Lights": {
        "bg": "#000f14", "fg": "#00ffcc", "accent": "#00ff99",
        "button_bg": "#00ff99", "button_fg": "#00080a",
        "listbox_select_bg": "#00ff99", "listbox_select_fg": "#00080a",
        "graph_bg": "#00080a", "grid_color": "#003344", "axis_color": "#006688",
        "entity_default": "#00ffcc", "entity_selected": "#ffff00", "entity_highlight": "#00ff99"
    }
}

# Minimalist theme definitions (subdued professional colors)
THEMES_MINIMALIST = {
    "Light": {
        "bg": "#f5f5f5", "fg": "#1a1a1a", "accent": "#0066cc",
        "button_bg": "#0066cc", "button_fg": "#ffffff",
        "listbox_select_bg": "#0066cc", "listbox_select_fg": "#ffffff",
        "graph_bg": "#ffffff", "grid_color": "#e0e0e0", "axis_color": "#999999",
        "entity_default": "#4fc3f7", "entity_selected": "#ffeb3b", "entity_highlight": "#e94560"
    },
    "Obsidian": {
        "bg": "#0d0d18", "fg": "#e8eeff", "accent": "#5599ff",
        "button_bg": "#5599ff", "button_fg": "#0d0d18",
        "listbox_select_bg": "#5599ff", "listbox_select_fg": "#0d0d18",
        "graph_bg": "#060609", "grid_color": "#1a1a2a", "axis_color": "#333355",
        "entity_default": "#55ddff", "entity_selected": "#ffee55", "entity_highlight": "#ff5588"
    },
    "Olive Grove": {
        "bg": "#1f2418", "fg": "#d8eeb0", "accent": "#b8dd44",
        "button_bg": "#b8dd44", "button_fg": "#0f120c",
        "listbox_select_bg": "#b8dd44", "listbox_select_fg": "#0f120c",
        "graph_bg": "#0f120c", "grid_color": "#2f3428", "axis_color": "#4f5438",
        "entity_default": "#d8eeb0", "entity_selected": "#ffff66", "entity_highlight": "#b8dd44"
    },
    "Deep Ocean": {
        "bg": "#081420", "fg": "#b8e8ff", "accent": "#33aaee",
        "button_bg": "#33aaee", "button_fg": "#040a10",
        "listbox_select_bg": "#33aaee", "listbox_select_fg": "#040a10",
        "graph_bg": "#040a10", "grid_color": "#182838", "axis_color": "#284858",
        "entity_default": "#b8e8ff", "entity_selected": "#ffee55", "entity_highlight": "#33aaee"
    },
    "Crimson Night": {
        "bg": "#1a0808", "fg": "#ffb8b8", "accent": "#ee4455",
        "button_bg": "#ee4455", "button_fg": "#ffffff",
        "listbox_select_bg": "#ee4455", "listbox_select_fg": "#ffffff",
        "graph_bg": "#0d0404", "grid_color": "#2a1818", "axis_color": "#4a2828",
        "entity_default": "#ff9999", "entity_selected": "#ffee55", "entity_highlight": "#ee4455"
    },
    "Burnished Oak": {
        "bg": "#1f1108", "fg": "#ffdd99", "accent": "#ee9944",
        "button_bg": "#ee9944", "button_fg": "#0f0804",
        "listbox_select_bg": "#ee9944", "listbox_select_fg": "#0f0804",
        "graph_bg": "#0f0804", "grid_color": "#2f2218", "axis_color": "#5f4428",
        "entity_default": "#ffdd99", "entity_selected": "#ffee55", "entity_highlight": "#ee9944"
    },
    "Amethyst": {
        "bg": "#180818", "fg": "#eeb8ff", "accent": "#aa44dd",
        "button_bg": "#aa44dd", "button_fg": "#ffffff",
        "listbox_select_bg": "#aa44dd", "listbox_select_fg": "#ffffff",
        "graph_bg": "#0c040c", "grid_color": "#281828", "axis_color": "#483848",
        "entity_default": "#dd99ff", "entity_selected": "#ffee55", "entity_highlight": "#aa44dd"
    },
    "Void": {
        "bg": "#080808", "fg": "#d8d8d8", "accent": "#ff3344",
        "button_bg": "#ff3344", "button_fg": "#ffffff",
        "listbox_select_bg": "#ff3344", "listbox_select_fg": "#ffffff",
        "graph_bg": "#000000", "grid_color": "#1a1a1a", "axis_color": "#444444",
        "entity_default": "#d8d8d8", "entity_selected": "#ffffff", "entity_highlight": "#ff3344"
    },
    "Solar Flare": {
        "bg": "#1f1008", "fg": "#ffee99", "accent": "#ff9933",
        "button_bg": "#ff9933", "button_fg": "#0f0804",
        "listbox_select_bg": "#ff9933", "listbox_select_fg": "#0f0804",
        "graph_bg": "#0f0804", "grid_color": "#3f2818", "axis_color": "#6f4828",
        "entity_default": "#ffee99", "entity_selected": "#ffee55", "entity_highlight": "#ff9933"
    },
    "Sakura": {
        "bg": "#281020", "fg": "#ffccee", "accent": "#ee66aa",
        "button_bg": "#ee66aa", "button_fg": "#140810",
        "listbox_select_bg": "#ee66aa", "listbox_select_fg": "#140810",
        "graph_bg": "#140810", "grid_color": "#382030", "axis_color": "#684050",
        "entity_default": "#ffccee", "entity_selected": "#ffee55", "entity_highlight": "#ee66aa"
    },
    "Northern Lights": {
        "bg": "#081820", "fg": "#b8ffee", "accent": "#33ddaa",
        "button_bg": "#33ddaa", "button_fg": "#040c10",
        "listbox_select_bg": "#33ddaa", "listbox_select_fg": "#040c10",
        "graph_bg": "#040c10", "grid_color": "#183030", "axis_color": "#285050",
        "entity_default": "#b8ffee", "entity_selected": "#ffee55", "entity_highlight": "#33ddaa"
    }
}


class Theme:
    """Theme manager with multiple color schemes"""
    def __init__(self, theme_name="Obsidian", gaudy_mode=False):
        self.theme_name = theme_name
        self.gaudy_mode = gaudy_mode
        self.update_theme(theme_name, gaudy_mode)

    def update_theme(self, theme_name, gaudy_mode):
        """Update the active theme"""
        self.theme_name = theme_name
        self.gaudy_mode = gaudy_mode
        themes = THEMES_GAUDY if gaudy_mode else THEMES_MINIMALIST
        # Fallback if theme name not found
        theme_data = themes.get(theme_name, themes.get("Obsidian", list(themes.values())[0]))

        # Map theme data to class attributes
        self.BG_DARK = theme_data["bg"]
        self.BG_MID = theme_data["bg"]
        self.BG_LIGHT = self._lighten_color(theme_data["bg"], 20)
        self.ACCENT = theme_data["accent"]
        self.ACCENT_HOVER = self._lighten_color(theme_data["accent"], 20)
        self.ACCENT_SECONDARY = self._darken_color(theme_data["accent"], 30)
        self.TEXT_PRIMARY = theme_data["fg"]
        self.TEXT_SECONDARY = self._darken_color(theme_data["fg"], 30)
        self.TEXT_DIM = self._darken_color(theme_data["fg"], 50)
        self.SUCCESS = "#4ecca3"
        self.WARNING = "#ffc107"
        self.ERROR = "#ff5252"
        self.INFO = "#4fc3f7"
        self.ENTITY_DEFAULT = theme_data["entity_default"]
        self.ENTITY_SELECTED = theme_data["entity_selected"]
        self.ENTITY_HIGHLIGHT = theme_data["entity_highlight"]
        self.GRAPH_BG = theme_data["graph_bg"]
        self.GRID_COLOR = theme_data["grid_color"]
        self.AXIS_COLOR = theme_data["axis_color"]

    def _lighten_color(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * amount / 100))
        g = min(255, int(g + (255 - g) * amount / 100))
        b = min(255, int(b + (255 - b) * amount / 100))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _darken_color(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * (100 - amount) / 100))
        g = max(0, int(g * (100 - amount) / 100))
        b = max(0, int(b * (100 - amount) / 100))
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_stylesheet(self):
        return f"""
            QMainWindow {{ background-color: {self.BG_DARK}; }}
            QWidget {{ background-color: {self.BG_DARK}; color: {self.TEXT_PRIMARY}; font-family: 'Segoe UI', 'Arial', sans-serif; font-size: 26px; }}
            QGroupBox {{ background-color: {self.BG_MID}; border: 1px solid {self.BG_LIGHT}; border-radius: 6px; margin-top: 14px; padding: 12px; font-weight: bold; font-size: 26px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; color: {self.ACCENT}; font-size: 28px; }}
            QPushButton {{ background-color: {self.ACCENT_SECONDARY}; border: none; border-radius: 4px; padding: 10px 18px; color: {self.TEXT_PRIMARY}; font-weight: bold; font-size: 26px; }}
            QPushButton:hover {{ background-color: {self.BG_LIGHT}; }}
            QPushButton:pressed {{ background-color: {self.ACCENT}; }}
            QPushButton#primary {{ background-color: {self.ACCENT}; }}
            QPushButton#primary:hover {{ background-color: {self.ACCENT_HOVER}; }}
            QPushButton#success {{ background-color: {self.SUCCESS}; color: {self.BG_DARK}; }}
            QListWidget {{ background-color: {self.BG_MID}; border: 1px solid {self.BG_LIGHT}; border-radius: 4px; padding: 4px; font-size: 26px; }}
            QListWidget::item:selected {{ background-color: {self.ACCENT}; color: {self.TEXT_PRIMARY}; }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background-color: {self.BG_MID}; border: 1px solid {self.BG_LIGHT}; border-radius: 4px; padding: 8px; color: {self.TEXT_PRIMARY}; font-size: 26px; }}
            QStatusBar {{ background-color: {self.BG_MID}; color: {self.SUCCESS}; }}
            QMenuBar {{ background-color: {self.BG_MID}; color: {self.TEXT_PRIMARY}; }}
            QMenu {{ background-color: {self.BG_MID}; border: 1px solid {self.BG_LIGHT}; }}
            QTabWidget::pane {{ background-color: {self.BG_MID}; border: 1px solid {self.BG_LIGHT}; }}
            QTabBar::tab {{ background-color: {self.BG_DARK}; color: {self.TEXT_SECONDARY}; padding: 10px 20px; }}
            QTabBar::tab:selected {{ background-color: {self.BG_MID}; color: {self.ACCENT}; }}
            QRadioButton::indicator:checked {{ background-color: {self.ACCENT}; border-color: {self.ACCENT}; }}
            QLabel#title {{ font-size: 32px; font-weight: bold; color: {self.ACCENT}; }}
            QLabel#info {{ color: {self.TEXT_SECONDARY}; font-size: 24px; }}
        """


class VispyCanvas(QWidget):
    """Vispy 3D canvas widget for entity visualization"""

    entity_clicked = pyqtSignal(int, bool, bool)  # index, shift, ctrl
    box_select = pyqtSignal(list)  # list of indices
    box_select_toggle = pyqtSignal(list)  # list of indices to toggle
    waypoint_created = pyqtSignal(float, float, float)  # x, y, z
    trail_completed = pyqtSignal(list)  # list of (x, y, z) tuples
    mesh_selection_changed = pyqtSignal(int)  # number of selected meshes
    mesh_clicked = pyqtSignal(int, bool, bool)  # mesh_idx, shift, ctrl

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)

        # Store theme reference
        self.theme = theme or Theme()

        # Create Vispy canvas with scene
        self.canvas = scene.SceneCanvas(
            keys='interactive',
            bgcolor=self.theme.GRAPH_BG,
            show=False
        )

        # Create layout with canvas and overlay controls
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a container for canvas with overlay buttons
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.canvas.native)

        # Create arrow navigation buttons (overlay on top-right of canvas)
        self.nav_widget = QWidget(canvas_container)
        self.nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QGridLayout(self.nav_widget)
        nav_layout.setSpacing(2)

        # Arrow buttons for panning
        btn_up = QPushButton("↑")
        btn_down = QPushButton("↓")
        btn_left = QPushButton("←")
        btn_right = QPushButton("→")
        btn_in = QPushButton("+")
        btn_out = QPushButton("-")

        for btn in [btn_up, btn_down, btn_left, btn_right, btn_in, btn_out]:
            btn.setMaximumSize(35, 35)
            btn.setStyleSheet("background-color: rgba(100, 100, 100, 180); color: white; font-weight: bold; border-radius: 3px;")

        btn_up.clicked.connect(lambda: self._move_camera(0, 10, 0))
        btn_down.clicked.connect(lambda: self._move_camera(0, -10, 0))
        btn_left.clicked.connect(lambda: self._move_camera(-10, 0, 0))
        btn_right.clicked.connect(lambda: self._move_camera(10, 0, 0))
        btn_in.clicked.connect(lambda: self._zoom_camera(-20))
        btn_out.clicked.connect(lambda: self._zoom_camera(20))

        nav_layout.addWidget(btn_up, 0, 1)
        nav_layout.addWidget(btn_left, 1, 0)
        nav_layout.addWidget(btn_right, 1, 2)
        nav_layout.addWidget(btn_down, 2, 1)
        nav_layout.addWidget(btn_in, 0, 3)
        nav_layout.addWidget(btn_out, 2, 3)

        self.nav_widget.setGeometry(10, 10, 150, 110)

        layout.addWidget(canvas_container)

        # Enable focus for keyboard controls
        self.setFocusPolicy(Qt.StrongFocus)
        self.canvas.native.setFocusPolicy(Qt.StrongFocus)

        # Create view with turntable camera (azimuth/elevation only, no roll)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(
            fov=45,
            distance=500,
            elevation=30,
            azimuth=45
        )

        # Create scatter visual for entities
        self.scatter = visuals.Markers(parent=self.view.scene)

        # Create scatter for max-size entities (stars)
        self.max_size_scatter = visuals.Markers(parent=self.view.scene)

        # Create scatter for selected entities (highlight)
        self.highlight_scatter = visuals.Markers(parent=self.view.scene)

        # Grid visual
        self.grid = scene.visuals.GridLines(
            color=(0.3, 0.3, 0.5, 0.5),
            parent=self.view.scene
        )

        # Orientation indicator (RGB axes)
        axis_length = 50
        self.x_axis = visuals.Arrow(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]], dtype=np.float32),
            color=(1.0, 0.0, 0.0, 0.8),
            arrow_size=8,
            arrow_type='stealth',
            parent=self.view.scene
        )
        self.y_axis = visuals.Arrow(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]], dtype=np.float32),
            color=(0.0, 1.0, 0.0, 0.8),
            arrow_size=8,
            arrow_type='stealth',
            parent=self.view.scene
        )
        self.z_axis = visuals.Arrow(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]], dtype=np.float32),
            color=(0.0, 0.0, 1.0, 0.8),
            arrow_size=8,
            arrow_type='stealth',
            parent=self.view.scene
        )

        # Add compass labels (NSEW)
        compass_distance = axis_length * 1.3
        self.compass_texts = []
        compass_labels = [
            ('N', (0, 0, compass_distance), (1, 1, 1, 0.9)),  # North (front)
            ('S', (0, 0, -compass_distance), (0.7, 0.7, 0.7, 0.7)),  # South (back)
            ('E', (compass_distance, 0, 0), (0.7, 0.7, 0.7, 0.7)),  # East (right)
            ('W', (-compass_distance, 0, 0), (0.7, 0.7, 0.7, 0.7)),  # West (left)
        ]
        for label, pos, color in compass_labels:
            text = visuals.Text(
                label,
                pos=pos,
                color=color,
                font_size=20,
                bold=True,
                parent=self.view.scene
            )
            self.compass_texts.append(text)

        # Mesh visual for generated mesh
        self.mesh_visual = None

        # Mesh selection mode
        self.mesh_selection_mode = False
        self.selected_mesh_indices = []  # Track indices of selected mesh triangles/faces
        self.mesh_highlight_visuals = []  # List of highlight visuals for selected meshes
        self.mesh_vertices = None  # Store mesh vertices for intersection testing
        self.mesh_faces = None  # Store mesh face indices
        self.mesh_highlight_hue = 210  # Default hue for mesh highlighting
        self.all_imported_meshes = []  # Reference to all imported meshes for selection

        # Box selection visual
        self.box_visual = None

        # Trail drawing visual
        self.trail_visual = None
        self.trail_mode = False
        self.trail_points = []

        # Rotation preview visual
        self.rotation_preview_visual = None

        # Store entity positions for picking
        self.entity_positions = None
        self.entity_sizes = None
        self.entities = []

        # Selection mode
        self.select_mode = "CLICK"  # CLICK, BOX, PAINT
        self.box_start = None
        self.is_dragging = False
        self.is_panning = False
        self.pan_start = None
        self.paint_processed_entities = set()  # Track entities already processed in current paint drag

        # Connect events
        self.canvas.events.mouse_press.connect(self._on_mouse_press)
        self.canvas.events.mouse_move.connect(self._on_mouse_move)
        self.canvas.events.mouse_release.connect(self._on_mouse_release)
        self.canvas.events.mouse_wheel.connect(self._on_mouse_wheel)

        # Xbox controller support (manual activation)
        self.gamepad = None
        self.gamepad_timer = None

    def set_entities(self, entities, selected_indices=None, sizes=None, use_size_scaling=False, auto_fit_camera=False, base_point_size=8):
        """Update the displayed entities"""
        self.entities = entities

        if not entities:
            self.scatter.set_data(pos=np.zeros((0, 3)))
            self.max_size_scatter.set_data(pos=np.zeros((0, 3)))
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

        # Separate max-size items (size >= 9000000 mm) for star rendering
        max_size_threshold = 9000000
        max_size_mask = None
        regular_mask = None

        # Set marker sizes based on entity size if available
        if use_size_scaling and sizes is not None:
            sizes = np.array(sizes, dtype=np.float32)

            # Identify max-size entities (don't scale them, show as stars)
            max_size_mask = sizes >= max_size_threshold
            regular_mask = ~max_size_mask

            # Process regular entities with logarithmic scaling
            if np.any(regular_mask):
                regular_sizes = sizes[regular_mask]
                regular_sizes_log = np.log10(regular_sizes + 1)
                # Normalize to reasonable marker range
                size_min, size_max = regular_sizes_log.min(), regular_sizes_log.max()
                if size_max > size_min:
                    normalized = (regular_sizes_log - size_min) / (size_max - size_min)
                else:
                    normalized = np.ones_like(regular_sizes_log)
                # Map to marker size range (0.5 to 10) scaled by user's base size
                regular_marker_sizes = (normalized * 9.5 + 0.5) * base_point_size / 8.0
            else:
                regular_marker_sizes = np.array([], dtype=np.float32)

            # Create full marker sizes array
            marker_sizes = np.full(len(entities), base_point_size, dtype=np.float32)
            if np.any(regular_mask):
                marker_sizes[regular_mask] = regular_marker_sizes
            # Max-size entities keep base size for star rendering
            if np.any(max_size_mask):
                marker_sizes[max_size_mask] = base_point_size * 1.5

            self.entity_sizes = marker_sizes
        else:
            marker_sizes = np.full(len(entities), base_point_size, dtype=np.float32)
            self.entity_sizes = marker_sizes
            max_size_mask = np.zeros(len(entities), dtype=bool)
            regular_mask = np.ones(len(entities), dtype=bool)

        # Render regular entities as circles
        if np.any(regular_mask):
            self.scatter.set_data(
                pos=positions[regular_mask],
                face_color=colors[regular_mask],
                edge_color='white',
                edge_width=0.5,
                size=marker_sizes[regular_mask]
            )
        else:
            self.scatter.set_data(pos=np.zeros((0, 3)))

        # Render max-size entities as stars
        if np.any(max_size_mask):
            max_size_positions = positions[max_size_mask]
            max_size_colors = np.full((np.sum(max_size_mask), 4), [1.0, 1.0, 0.0, 0.9], dtype=np.float32)
            max_size_sizes = marker_sizes[max_size_mask]
            self.max_size_scatter.set_data(
                pos=max_size_positions,
                face_color=max_size_colors,
                edge_color='orange',
                edge_width=2,
                size=max_size_sizes,
                symbol='star'
            )
        else:
            self.max_size_scatter.set_data(pos=np.zeros((0, 3)))

        # Update highlights
        self._update_highlights(selected_indices or [])

        # Auto-fit view only when requested
        if auto_fit_camera and len(positions) > 0:
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

        # Create highlight colors (bright yellow with red edge for visibility)
        colors = np.full((len(valid_indices), 4), [1.0, 1.0, 0.0, 1.0], dtype=np.float32)

        # Use larger size than entity markers, or use entity sizes if available
        if hasattr(self, 'entity_sizes') and self.entity_sizes is not None:
            highlight_sizes = np.array([self.entity_sizes[i] * 2.5 for i in valid_indices], dtype=np.float32)
        else:
            highlight_sizes = 20

        self.highlight_scatter.set_data(
            pos=selected_positions,
            face_color=colors,
            edge_color='red',
            edge_width=3,
            size=highlight_sizes
        )

        self.canvas.update()

    def update_selection(self, selected_indices):
        """Update just the selection highlights"""
        self._update_highlights(selected_indices)

    def show_position_preview(self, selected_indices, x, y, z, offset_mode):
        """Show preview of where entities will move to"""
        if not selected_indices or self.entity_positions is None or len(self.entity_positions) == 0:
            self.highlight_scatter.set_data(pos=np.zeros((0, 3)))
            return

        # Filter valid indices
        valid_indices = [i for i in selected_indices if i < len(self.entity_positions)]
        if not valid_indices:
            return

        # Calculate preview positions
        preview_positions = []
        for idx in valid_indices:
            original_pos = self.entity_positions[idx].copy()
            if offset_mode:
                preview_pos = original_pos + np.array([-x, z, y], dtype=np.float32)
            else:
                preview_pos = np.array([-x, z, y], dtype=np.float32)
            preview_positions.append(preview_pos)

        preview_positions = np.array(preview_positions, dtype=np.float32)

        # Create preview colors (cyan/blue to indicate it's a preview)
        colors = np.full((len(valid_indices), 4), [0.0, 0.8, 1.0, 0.7], dtype=np.float32)

        self.highlight_scatter.set_data(
            pos=preview_positions,
            face_color=colors,
            edge_color='cyan',
            edge_width=2,
            size=15
        )
        self.canvas.update()

    def _screen_to_world(self, screen_pos):
        """Convert screen coordinates to 3D world coordinates on the ground plane (z=0)"""
        # Get camera parameters
        cam = self.view.camera

        # Get viewport size
        viewport = (0, 0, self.canvas.size[0], self.canvas.size[1])

        # Calculate ray from camera through screen position
        # For TurntableCamera, compute camera position
        azim_rad = np.radians(cam.azimuth)
        elev_rad = np.radians(cam.elevation)

        # Camera looks at center from distance away
        cam_x = cam.center[0] + cam.distance * np.cos(elev_rad) * np.cos(azim_rad)
        cam_y = cam.center[1] + cam.distance * np.cos(elev_rad) * np.sin(azim_rad)
        cam_z = cam.center[2] + cam.distance * np.sin(elev_rad)

        cam_pos = np.array([cam_x, cam_y, cam_z])

        # Normalize screen coordinates to NDC (-1 to 1)
        ndc_x = (2.0 * screen_pos[0] / viewport[2]) - 1.0
        ndc_y = 1.0 - (2.0 * screen_pos[1] / viewport[3])

        # Get FOV and aspect ratio
        fov_rad = np.radians(cam.fov)
        aspect = viewport[2] / viewport[3]

        # Calculate ray direction in camera space
        tan_fov = np.tan(fov_rad / 2.0)
        ray_x_cam = ndc_x * aspect * tan_fov
        ray_y_cam = ndc_y * tan_fov
        ray_z_cam = -1.0

        # Transform ray direction to world space using camera orientation
        # Camera forward vector (from camera to center)
        forward = np.array(cam.center) - cam_pos
        forward = forward / np.linalg.norm(forward)

        # Right vector
        right = np.array([np.cos(azim_rad), np.sin(azim_rad), 0.0])

        # Up vector
        up = np.cross(right, forward)
        up = up / np.linalg.norm(up)

        # Reconstruct right to ensure orthogonality
        right = np.cross(forward, up)

        # Transform ray direction to world space
        ray_dir = (ray_x_cam * right + ray_y_cam * up + ray_z_cam * forward)
        ray_dir = ray_dir / np.linalg.norm(ray_dir)

        # Intersect ray with ground plane (z = 0)
        # Ray equation: P = cam_pos + t * ray_dir
        # Plane equation: z = 0
        # Solve for t: cam_pos[2] + t * ray_dir[2] = 0

        if abs(ray_dir[2]) < 1e-6:
            # Ray is parallel to ground plane
            return None

        t = -cam_pos[2] / ray_dir[2]

        if t < 0:
            # Intersection is behind camera
            return None

        # Calculate intersection point
        world_pos = cam_pos + t * ray_dir

        return world_pos

    def _on_mouse_press(self, event):
        """Handle mouse click for entity picking and pan initiation"""
        if self.entity_positions is None:
            return

        # Middle Click (Button 3) - Start Pan
        if event.button == 3:
            self.is_panning = True
            self.pan_start = event.pos
            event.handled = True
            return

        # Left Click (Button 1) - Trail drawing or Selection
        if event.button == 1:
            print(f"Left click detected: trail_mode={self.trail_mode}, mesh_selection_mode={self.mesh_selection_mode}, select_mode={self.select_mode}")

            # Trail drawing mode
            if self.trail_mode:
                event.handled = True
                self.is_dragging = True
                # Start trail with first point
                world_pos = self._screen_to_world(event.pos)
                self.trail_points = [world_pos]
                return

            # Mesh selection mode
            if self.mesh_selection_mode:
                print(f"Calling mesh click select, all_imported_meshes count: {len(self.all_imported_meshes)}")
                result = self._do_mesh_click_select(event, self.mesh_highlight_hue)
                print(f"Mesh click select result: {result}")
                if result:
                    event.handled = True
                return

            # Normal selection modes
            if self.select_mode == "CLICK":
                result = self._do_click_select(event)
                if result:
                    event.handled = True
            elif self.select_mode in ["BOX", "PAINT"]:
                event.handled = True
                self.is_dragging = True
                self.box_start = np.array(event.pos[:2])

                if self.select_mode == "PAINT":
                    self.paint_processed_entities.clear()  # Reset for new drag
                    self._do_click_select(event)

    def _on_mouse_move(self, event):
        """Handle mouse move for box selection, paint selection, trail drawing, and panning"""
        # Handle Panning
        if self.is_panning and event.button == 3:
            event.handled = True
            self._pan_camera(event)
            return

        # Handle Trail Drawing
        if self.is_dragging and self.trail_mode:
            event.handled = True
            world_pos = self._screen_to_world(event.pos)
            self.trail_points.append(world_pos)
            self._update_trail_visual()
            return

        # Handle Selection Dragging
        if self.is_dragging:
            if self.select_mode == "BOX":
                event.handled = True
                self._draw_selection_box(event)
            elif self.select_mode == "PAINT":
                event.handled = True
                self._do_click_select(event)

    def _on_mouse_release(self, event):
        """Handle mouse release"""
        # Stop panning
        if self.is_panning and event.button == 3:
            self.is_panning = False
            self.pan_start = None
            event.handled = True
            return

        # Stop trail drawing
        if self.is_dragging and event.button == 1 and self.trail_mode:
            if len(self.trail_points) >= 2:
                # Emit trail completed signal
                self.trail_completed.emit(self.trail_points)
            self.is_dragging = False
            event.handled = True
            return

        # Stop selection
        if self.is_dragging and event.button == 1:
            if self.select_mode == "BOX":
                self._finish_box_select(event)
            elif self.select_mode == "PAINT":
                self.paint_processed_entities.clear()  # Clear after drag completes
            self.is_dragging = False
            self.box_start = None
            self._clear_selection_box()

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel events - block zoom during panning"""
        if self.is_panning:
            event.handled = True  # Block zoom while panning
            return
        # Otherwise, let default camera handle zoom

    def _pan_camera(self, event):
        """Simplified pan implementation - translate camera center"""
        if self.pan_start is None:
            return

        # Calculate delta in screen coordinates
        p1 = np.array(event.last_event.pos[:2])
        p2 = np.array(event.pos[:2])
        delta = p2 - p1

        # Scale based on distance from camera to center
        dist = self.view.camera.distance
        scale = dist * 0.002  # Adjust sensitivity

        # For TurntableCamera, compute right and up vectors from azimuth and elevation
        azim_rad = np.radians(self.view.camera.azimuth)
        elev_rad = np.radians(self.view.camera.elevation)

        # Right vector (perpendicular to view direction in XY plane)
        # When azimuth = 0, camera looks along +Y, right is +X
        # When azimuth = 90, camera looks along -X, right is +Y
        right = np.array([
            np.cos(azim_rad),
            np.sin(azim_rad),
            0.0
        ])

        # Up vector (screen up direction, considering elevation)
        # This is perpendicular to both the view direction and the right vector
        # For turntable camera, up has a Z component based on elevation
        up = np.array([
            -np.sin(azim_rad) * np.sin(elev_rad),
            np.cos(azim_rad) * np.sin(elev_rad),
            np.cos(elev_rad)
        ])

        # Calculate pan offset in world space
        pan_x = -delta[0] * scale
        pan_y = delta[1] * scale
        offset = pan_x * right + pan_y * up

        # Update camera center
        new_center = np.array(self.view.camera.center) + offset
        self.view.camera.center = tuple(new_center)
        self.canvas.update()

    def _apply_controller_pan(self, stick_x, stick_y):
        """Pan camera using controller input with new panning logic"""
        dist = self.view.camera.distance
        scale = dist * 0.002 * 50  # Scale for controller sensitivity

        azim_rad = np.radians(self.view.camera.azimuth)
        elev_rad = np.radians(self.view.camera.elevation)

        # Right vector (perpendicular to view direction in XY plane)
        right = np.array([
            np.cos(azim_rad),
            np.sin(azim_rad),
            0.0
        ])

        # Up vector (screen up direction, considering elevation)
        up = np.array([
            -np.sin(azim_rad) * np.sin(elev_rad),
            np.cos(azim_rad) * np.sin(elev_rad),
            np.cos(elev_rad)
        ])

        # Apply stick input
        offset = stick_x * right * scale + stick_y * up * scale

        new_center = np.array(self.view.camera.center) + offset
        self.view.camera.center = tuple(new_center)
        self.canvas.update()

    def _apply_keyboard_pan(self, dx, dz):
        """Pan camera using keyboard input with proper coordinate transform"""
        dist = self.view.camera.distance
        scale = dist * 0.002 * 50  # Scale for keyboard sensitivity

        azim_rad = np.radians(self.view.camera.azimuth)

        # Right and forward vectors
        right = np.array([np.cos(azim_rad), np.sin(azim_rad), 0])
        forward = np.array([np.sin(azim_rad), -np.cos(azim_rad), 0])

        offset = dx * right * scale + dz * forward * scale

        new_center = np.array(self.view.camera.center) + offset
        self.view.camera.center = tuple(new_center)
        self.canvas.update()

    def _move_camera(self, dx, dy, dz):
        """Move camera by delta in screen-relative coordinates
        dx: right/left movement
        dy: up/down movement (world vertical)
        dz: forward/backward movement
        """
        # For TurntableCamera, calculate movement based on azimuth only (not elevation)
        # This keeps movement in horizontal plane aligned with camera view
        azim_rad = np.radians(self.view.camera.azimuth)

        # Calculate right direction (perpendicular to camera view, in horizontal plane)
        # Azimuth 0 = looking along +Z, 90 = looking along +X
        right = np.array([
            np.cos(azim_rad),
            0,
            -np.sin(azim_rad)
        ])

        # Calculate forward direction (camera looking direction, projected to horizontal plane)
        forward = np.array([
            np.sin(azim_rad),
            0,
            np.cos(azim_rad)
        ])

        # Up is always world up for turntable camera
        up = np.array([0, 1, 0])

        # Apply movement
        offset = dx * right + dy * up + dz * forward

        # Update center
        new_center = np.array(self.view.camera.center) + offset
        self.view.camera.center = tuple(new_center)
        self.canvas.update()

    def _zoom_camera(self, delta):
        """Zoom camera in/out"""
        self.view.camera.distance = max(10, self.view.camera.distance + delta)
        self.canvas.update()

    def keyPressEvent(self, event):
        """Handle keyboard input for WASD navigation with new panning logic"""
        if event.key() == Qt.Key_W:
            self._apply_keyboard_pan(0, 1)  # Forward
        elif event.key() == Qt.Key_S:
            self._apply_keyboard_pan(0, -1)  # Backward
        elif event.key() == Qt.Key_A:
            self._apply_keyboard_pan(-1, 0)  # Left
        elif event.key() == Qt.Key_D:
            self._apply_keyboard_pan(1, 0)  # Right
        elif event.key() == Qt.Key_Space:
            # Up - move camera center up in world Z
            delta = np.array([0, 0, 10])
            new_center = np.array(self.view.camera.center) + delta
            self.view.camera.center = tuple(new_center)
            self.canvas.update()
        elif event.key() == Qt.Key_Shift:
            # Down
            delta = np.array([0, 0, -10])
            new_center = np.array(self.view.camera.center) + delta
            self.view.camera.center = tuple(new_center)
            self.canvas.update()
        elif event.key() == Qt.Key_Q:
            self._zoom_camera(-20)  # Zoom in
        elif event.key() == Qt.Key_E:
            self._zoom_camera(20)  # Zoom out
        else:
            super().keyPressEvent(event)

    def _init_gamepad(self):
        """Initialize Xbox controller support using pygame"""
        if not PYGAME_AVAILABLE:
            return False

        try:
            pygame.init()
            pygame.joystick.init()

            if pygame.joystick.get_count() > 0:
                self.gamepad = pygame.joystick.Joystick(0)
                self.gamepad.init()
                print(f"Xbox controller connected: {self.gamepad.get_name()}")

                # Start polling timer
                if self.gamepad_timer is None:
                    self.gamepad_timer = QTimer(self.parent())
                    self.gamepad_timer.timeout.connect(self._poll_gamepad)
                    self.gamepad_timer.start(16)  # ~60 FPS

                return True
            else:
                print("No Xbox controller detected")
                return False
        except Exception as e:
            print(f"Error initializing gamepad: {e}")
            return False

    def _poll_gamepad(self):
        """Poll Xbox controller for input"""
        if not self.gamepad or not PYGAME_AVAILABLE:
            return

        try:
            pygame.event.pump()  # Process pygame events

            # Left stick for movement (X/Y)
            left_x = self.gamepad.get_axis(0)  # Left stick X
            left_y = self.gamepad.get_axis(1)  # Left stick Y

            # Right stick for rotation (camera orbit)
            right_x = self.gamepad.get_axis(2)  # Right stick X
            right_y = self.gamepad.get_axis(3)  # Right stick Y

            # Triggers for zoom (LT = 2, RT = 3 on Xbox controllers)
            try:
                lt = self.gamepad.get_axis(4)  # Left trigger
                rt = self.gamepad.get_axis(5)  # Right trigger
            except:
                lt, rt = 0, 0

            # Deadzone
            deadzone = 0.15
            move_speed = 5

            # Apply movement if stick is moved (use new pan logic)
            if abs(left_x) > deadzone or abs(left_y) > deadzone:
                dx = left_x if abs(left_x) > deadzone else 0
                dy = -left_y if abs(left_y) > deadzone else 0
                self._apply_controller_pan(dx, dy)

            # Zoom with triggers (RT - LT)
            if abs(lt - rt) > deadzone:
                zoom_delta = (rt - lt) * move_speed * 2  # Multiply for more sensitivity
                self._zoom_camera(zoom_delta)

            # Camera rotation with right stick - use orbit method
            if abs(right_x) > deadzone or abs(right_y) > deadzone:
                rot_speed = 5.0  # Rotation speed multiplier

                # Get canvas center for rotation pivot
                w, h = self.canvas.size
                center_x, center_y = w / 2, h / 2

                # Apply rotation using orbit (right stick controls rotation around center)
                dx = right_x * rot_speed if abs(right_x) > deadzone else 0
                dy = right_y * rot_speed if abs(right_y) > deadzone else 0

                # Use camera's orbit method (simulates dragging)
                self.view.camera.orbit(azim=dx, elev=-dy)
                self.canvas.update()

        except Exception as e:
            # Silently fail if controller disconnected
            pass

    def _do_click_select(self, event):
        """Perform click selection - find nearest entity"""
        if self.entity_positions is None or len(self.entity_positions) == 0:
            return False

        # Get click position
        click_pos = np.array(event.pos[:2])

        # Transform 3D entity positions to 2D screen coordinates
        tr = self.scatter.get_transform(map_from='visual', map_to='canvas')

        # Vectorized projection of all positions to screen space
        try:
            # 1. Map (N, 3) -> (N, 4) and apply transform
            points_4d = np.hstack([self.entity_positions, np.ones((len(self.entity_positions), 1))])
            mapped = tr.map(points_4d)

            # 2. Perspective division (normalize homogeneous coordinates x/w, y/w)
            w = mapped[:, 3:4]
            w[np.abs(w) < 1e-6] = 1.0  # Avoid division by zero
            screen_positions = mapped[:, :2] / w

        except Exception as e:
            print(f"Selection transform error: {e}")
            return False

        # Find nearest entity to click
        distances = np.sqrt(np.sum((screen_positions - click_pos)**2, axis=1))
        nearest_idx = np.argmin(distances)

        # Only select if within reasonable distance (50 pixels)
        if distances[nearest_idx] < 50:
            # In paint mode with dragging, check if entity was already processed this drag
            is_paint = self.select_mode == "PAINT"
            if is_paint and self.is_dragging and nearest_idx in self.paint_processed_entities:
                return True  # Already processed, don't reselect

            # Mark as processed in paint mode
            if is_paint and self.is_dragging:
                self.paint_processed_entities.add(nearest_idx)

            # Check Paint mode for implicit shift
            shift = 'Shift' in event.modifiers or is_paint
            ctrl = 'Control' in event.modifiers
            self.entity_clicked.emit(nearest_idx, shift, ctrl)
            return True

        return False

    def _draw_selection_box(self, event):
        """Draw the selection box during drag"""
        if self.box_start is None:
            return
        self._clear_selection_box()
        current_pos = np.array(event.pos[:2])
        x1, y1 = self.box_start
        x2, y2 = current_pos

        box_points = np.array([
            [x1, y1, 0], [x2, y1, 0], [x2, y2, 0], [x1, y2, 0], [x1, y1, 0]
        ], dtype=np.float32)

        self.box_visual = scene.visuals.Line(
            pos=box_points, color=(0.0, 1.0, 0.0, 0.8), width=2,
            method='gl', parent=self.view.scene
        )
        self.box_visual.transform = self.view.get_transform('canvas', 'visual')
        self.canvas.update()

    def _clear_selection_box(self):
        if self.box_visual is not None:
            self.box_visual.parent = None
            self.box_visual = None
            self.canvas.update()

    def _finish_box_select(self, event):
        """Complete box selection"""
        if self.entity_positions is None or len(self.entity_positions) == 0 or self.box_start is None:
            return

        current_pos = np.array(event.pos[:2])
        x1, y1 = self.box_start
        x2, y2 = current_pos
        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)

        tr = self.scatter.get_transform(map_from='visual', map_to='canvas')

        try:
            points_4d = np.hstack([self.entity_positions, np.ones((len(self.entity_positions), 1))])
            mapped = tr.map(points_4d)
            w = mapped[:, 3:4]
            w[np.abs(w) < 1e-6] = 1.0 
            screen_positions = mapped[:, :2] / w

            x_match = (screen_positions[:, 0] >= xmin) & (screen_positions[:, 0] <= xmax)
            y_match = (screen_positions[:, 1] >= ymin) & (screen_positions[:, 1] <= ymax)
            selected_indices = np.where(x_match & y_match)[0].tolist()
            if selected_indices:
                ctrl = 'Control' in event.modifiers
            # If Ctrl is held, we tell the receiver to toggle these indices
                if ctrl:
                    self.box_select_toggle.emit(selected_indices)
                else:
                    self.box_select.emit(selected_indices)
        except Exception as e:
            print(f"Box selection error: {e}")

    def set_mesh(self, vertices, faces, color=(0.5, 0.8, 0.5, 0.5)):
        if self.mesh_visual is not None:
            self.mesh_visual.parent = None
        if vertices is not None and faces is not None:
            self.mesh_visual = visuals.Mesh(
                vertices=vertices, faces=faces, color=color, parent=self.view.scene
            )
            # Store mesh data for intersection testing
            self.mesh_vertices = vertices
            self.mesh_faces = faces
        self.canvas.update()

    def clear_mesh(self):
        if self.mesh_visual is not None:
            self.mesh_visual.parent = None
            self.mesh_visual = None
        self.mesh_vertices = None
        self.mesh_faces = None
        self._clear_mesh_selection()
        self.canvas.update()

    def set_imported_meshes(self, meshes):
        """Set reference to all imported meshes for selection"""
        self.all_imported_meshes = meshes

    def clear_entity_models(self):
        """Remove all rendered entity-locked models"""
        if not hasattr(self, 'entity_model_visuals'):
            self.entity_model_visuals = {}
        for visual in self.entity_model_visuals.values():
            if visual is not None:
                visual.parent = None
        self.entity_model_visuals.clear()
        self.canvas.update()

    def render_entity_models(self, entities, assignments):
        """Render OBJs at entity positions/rotations"""
        if not hasattr(self, 'entity_model_visuals'):
            self.entity_model_visuals = {}
        
        # Use a simple cache to avoid re-parsing same OBJ multiple times
        obj_cache = {}
        
        for idx, model_path in assignments.items():
            if idx >= len(entities): continue
            entity = entities[idx]
            
            # Use absolute path or relative to script dir
            path = Path(model_path)
            if not path.is_absolute():
                path = Path(__file__).parent / model_path
                
            if not path.exists(): continue
            
            # Load OBJ data
            if str(path) not in obj_cache:
                verts = []
                faces = []
                try:
                    with open(path, 'r') as f:
                        for line in f:
                            if line.startswith('v '):
                                p = line.split()
                                verts.append([float(p[1]), float(p[2]), float(p[3])])
                            elif line.startswith('f '):
                                p = line.split()
                                f_indices = [int(x.split('/')[0]) - 1 for x in p[1:]]
                                for i in range(1, len(f_indices)-1):
                                    faces.append([f_indices[0], f_indices[i], f_indices[i+1]])
                    obj_cache[str(path)] = (np.array(verts, dtype=np.float32), np.array(faces, dtype=np.uint32))
                except: continue
                
            obj_verts, obj_faces = obj_cache[str(path)]
            verts = obj_verts.copy()

            # The model is saved in entity-local space (inverse transform applied during save)
            # To render correctly, we need to:
            # 1. Apply entity rotation (forward transform)
            # 2. Translate to entity position
            # 3. Convert to display coordinate system (-x, z, y)

            # Build rotation matrix from entity quaternion
            rx, ry, rz, rw = entity['rx'], entity['ry'], entity['rz'], entity['rw']

            # Normalize quaternion
            norm = np.sqrt(rx*rx + ry*ry + rz*rz + rw*rw)
            if norm > 1e-10:
                rx, ry, rz, rw = rx/norm, ry/norm, rz/norm, rw/norm
            else:
                rx, ry, rz, rw = 0, 0, 0, 1

            # Convert quaternion to rotation matrix
            rot_matrix = np.array([
                [1 - 2*(ry*ry + rz*rz), 2*(rx*ry - rw*rz), 2*(rx*rz + rw*ry)],
                [2*(rx*ry + rw*rz), 1 - 2*(rx*rx + rz*rz), 2*(ry*rz - rw*rx)],
                [2*(rx*rz - rw*ry), 2*(ry*rz + rw*rx), 1 - 2*(rx*rx + ry*ry)]
            ], dtype=np.float32)

            # Apply rotation to vertices (entity local -> world space)
            verts = verts @ rot_matrix.T

            # Translate to entity position (world space)
            verts += np.array([entity['x'], entity['y'], entity['z']], dtype=np.float32)

            # Convert to display coordinate system (-x, z, y)
            verts_display = np.column_stack([-verts[:, 0], verts[:, 2], verts[:, 1]])

            mesh_visual = visuals.Mesh(
                vertices=verts_display,
                faces=obj_faces,
                color=(0.7, 0.7, 1.0, 0.8),
                shading='smooth',
                parent=self.view.scene
            )
            self.entity_model_visuals[idx] = mesh_visual

    def toggle_mesh_selection_mode(self, enabled):
        """Toggle mesh selection mode on/off"""
        print(f"Mesh selection mode toggled to: {enabled}")
        self.mesh_selection_mode = enabled
        if not enabled:
            self._clear_mesh_selection()
        self.canvas.update()

    def set_mesh_highlight_hue(self, hue):
        """Set the hue value for mesh highlighting"""
        self.mesh_highlight_hue = hue

    def get_mesh_highlight_color(self, hue):
        """Get highlight color from hue value (0-360)"""
        # Convert HSV to RGB
        h = hue / 360.0
        s = 0.8
        v = 1.0

        if s == 0:
            r = g = b = v
        else:
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6

            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            else:
                r, g, b = v, p, q

        return (r, g, b, 0.5)  # Semi-transparent

    def _clear_mesh_selection(self):
        """Clear all mesh highlight visuals"""
        # Clear old list-based visuals
        for visual in self.mesh_highlight_visuals:
            if visual is not None:
                visual.parent = None
        self.mesh_highlight_visuals.clear()

        # Clear new dict-based visuals
        if hasattr(self, 'mesh_highlight_dict'):
            for visual in self.mesh_highlight_dict.values():
                if visual is not None:
                    visual.parent = None
            self.mesh_highlight_dict.clear()

        self.selected_mesh_indices.clear()

        # Emit signal to update UI
        self.mesh_selection_changed.emit(0)
        self.canvas.update()

    def _ray_triangle_intersection(self, ray_origin, ray_direction, triangle):
        """
        Möller–Trumbore ray-triangle intersection algorithm
        Returns distance to intersection, or None if no intersection
        """
        v0, v1, v2 = triangle
        edge1 = v1 - v0
        edge2 = v2 - v0

        h = np.cross(ray_direction, edge2)
        a = np.dot(edge1, h)

        if -1e-6 < a < 1e-6:
            return None  # Ray is parallel to triangle

        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)

        if u < 0.0 or u > 1.0:
            return None

        q = np.cross(s, edge1)
        v = f * np.dot(ray_direction, q)

        if v < 0.0 or u + v > 1.0:
            return None

        t = f * np.dot(edge2, q)

        if t > 1e-6:  # Ray intersection
            return t

        return None

    def _ray_intersects_aabb(self, ray_origin, ray_direction, v_min, v_max):
        """Check if ray intersects AABB (Slab method)"""
        t1 = (v_min - ray_origin) / (ray_direction + 1e-10)
        t2 = (v_max - ray_origin) / (ray_direction + 1e-10)
        
        t_min = np.maximum(np.minimum(t1, t2), 0.0)
        t_max = np.maximum(t1, t2)
        
        t_enter = np.max(t_min)
        t_exit = np.min(t_max)
        
        return t_exit >= t_enter and t_exit > 0

    def _ray_triangle_intersection_vectorized(self, ray_origin, ray_direction, v0, v1, v2):
        """Vectorized Möller–Trumbore ray-triangle intersection"""
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        h = np.cross(ray_direction, edge2)
        # Handle cases where ray_direction is very small
        a = np.einsum('ij,ij->i', edge1, h)
        
        parallel_mask = (np.abs(a) < 1e-6)
        
        safe_a = np.where(parallel_mask, 1.0, a)
        f = 1.0 / safe_a
        s = ray_origin - v0
        u = f * np.einsum('ij,ij->i', s, h)
        
        q = np.cross(s, edge1)
        v = f * np.einsum('ij,j->i', q, ray_direction)
        
        t = f * np.einsum('ij,ij->i', edge2, q)
        
        hit_mask = (~parallel_mask) & (u >= 0.0) & (u <= 1.0) & (v >= 0.0) & (u + v <= 1.0) & (t > 1e-6)
        
        distances = np.full(len(v0), np.inf, dtype=np.float32)
        # Only set distances for hits
        if np.any(hit_mask):
            distances[hit_mask] = t[hit_mask]
        return distances
    def _do_mesh_click_select(self, event, hue):
        """Optimized mesh selection via ray-mesh intersection (mesh-level)"""
        if not self.all_imported_meshes:
            print("No imported meshes available for selection")
            return False

        print(f"Mesh selection mode active, checking {len(self.all_imported_meshes)} meshes")

        # Get the transform from canvas to visual (world) coordinates
        # Use the scatter visual's transform which accounts for camera
        tr = self.scatter.get_transform(map_from='canvas', map_to='visual')

        # Create two points at different depths to define the ray
        click_x, click_y = event.pos[0], event.pos[1]
        near_pt = np.array([[click_x, click_y, 0, 1]])
        far_pt = np.array([[click_x, click_y, 1, 1]])

        # Map to visual (world) coordinates
        try:
            near_world_4d = tr.map(near_pt)
            far_world_4d = tr.map(far_pt)

            if near_world_4d is None or far_world_4d is None:
                print("Transform mapping failed")
                return False

            # Perspective divide
            near_world = near_world_4d[0, :3] / (near_world_4d[0, 3] + 1e-10)
            far_world = far_world_4d[0, :3] / (far_world_4d[0, 3] + 1e-10)

        except Exception as e:
            print(f"Error in ray calculation: {e}")
            return False

        # Ray origin and direction
        cam_pos_world = near_world
        ray_dir_world = far_world - near_world
        ray_length = np.linalg.norm(ray_dir_world)
        if ray_length < 1e-10:
            print("Ray direction too short")
            return False
        ray_dir_world /= ray_length

        print(f"Mesh click: pos={event.pos}, cam_pos={cam_pos_world}, ray_dir={ray_dir_world}")

        closest_distance = float('inf')
        hit_idx = None

        print(f"Checking {len(self.all_imported_meshes)} meshes for intersection...")

        for mesh_idx, mesh in enumerate(self.all_imported_meshes):
            if not mesh.get('visible', True):
                print(f"  Mesh {mesh_idx} not visible, skipping")
                continue
            if mesh.get('visual') is None:
                print(f"  Mesh {mesh_idx} has no visual, skipping")
                continue

            # Apply identical transformations as rendering
            verts = mesh['vertices'].copy()
            flip = mesh.get('flip', [False, False, False])
            if flip[0]: verts[:, 0] *= -1
            if flip[1]: verts[:, 1] *= -1
            if flip[2]: verts[:, 2] *= -1
            
            s = mesh.get('scale_xyz', [1.0, 1.0, 1.0])
            verts *= s
            
            quat = mesh.get('rotation', [0, 0, 0, 1])
            verts = self._apply_quaternion_rotation_simple(verts, quat)
            
            # Match rendering's coordinate swap
            verts_display = np.column_stack([-verts[:, 0], verts[:, 2], verts[:, 1]])
            
            pos = mesh['position']
            verts_display += np.array([-pos[0], pos[2], pos[1]], dtype=np.float32)

            # Check for intersection
            faces = mesh['faces']
            dist = self._ray_triangle_intersection_vectorized(
                cam_pos_world, ray_dir_world,
                verts_display[faces[:, 0]], verts_display[faces[:, 1]], verts_display[faces[:, 2]]
            )

            
            hits = dist[dist < float('inf')]
            if len(hits) > 0:
                min_dist = np.min(hits)
                print(f"  Mesh {mesh_idx} hit at dist {min_dist:.2f}")
                if min_dist < closest_distance:
                    closest_distance = min_dist
                    hit_idx = mesh_idx

        if hit_idx is not None and closest_distance < float('inf'):
            shift = 'Shift' in event.modifiers
            ctrl = 'Control' in event.modifiers
            
            # Emit signal and let main editor handle the state/sync
            self.mesh_clicked.emit(hit_idx, shift, ctrl)
            
            self.canvas.update()
            return True
        return False

    def _apply_quaternion_rotation_simple(self, vertices, quat):
        """Apply quaternion rotation to vertices"""
        qx, qy, qz, qw = quat
        rot_matrix = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
        ], dtype=np.float32)
        return vertices @ rot_matrix.T

    def _highlight_full_mesh(self, mesh_idx, hue):
        """Create a highlight visual for a selected whole mesh"""
        if mesh_idx >= len(self.all_imported_meshes):
            print(f"Warning: mesh_idx {mesh_idx} >= len(all_imported_meshes) {len(self.all_imported_meshes)}")
            return

        print(f"Highlighting mesh {mesh_idx} with hue {hue}")
        mesh_data = self.all_imported_meshes[mesh_idx]

        # Get transformed vertices (same as rendering logic)
        vertices = mesh_data['vertices'].copy()
        faces = mesh_data['faces']

        flip = mesh_data.get('flip', [False, False, False])
        if flip[0]: vertices[:, 0] *= -1
        if flip[1]: vertices[:, 1] *= -1
        if flip[2]: vertices[:, 2] *= -1

        if 'scale_xyz' in mesh_data:
            scale_xyz = mesh_data['scale_xyz']
            vertices[:, 0] *= scale_xyz[0]
            vertices[:, 1] *= scale_xyz[1]
            vertices[:, 2] *= scale_xyz[2]

        quat = mesh_data.get('rotation', np.array([0, 0, 0, 1], dtype=np.float32))
        vertices = self._apply_quaternion_rotation_simple(vertices, quat)
        vertices[:, [0, 1, 2]] = np.column_stack([-vertices[:, 0], vertices[:, 2], vertices[:, 1]])

        pos = mesh_data['position']
        vertices += np.array([-pos[0], pos[2], pos[1]], dtype=np.float32)

        # Highlight color
        highlight_color = self.get_mesh_highlight_color(hue)
        highlight_color = (highlight_color[0], highlight_color[1], highlight_color[2], 0.4) # Semi-transparent overlay

        # Create highlight visual as a slightly scaled-up duplicate
        # We can either use raw vertices or just parent a visual and let Vispy handle it
        # But for reliability with our manual swap/negate logic, we use fixed vertices
        
        # Calculate normals to offset vertices slightly outward
        # Simplified: just use a small scale-up around the mesh center for the highlight
        center = vertices.mean(axis=0)
        highlight_verts = center + (vertices - center) * 1.02 # 2% larger

        highlight_visual = visuals.Mesh(
            vertices=highlight_verts,
            faces=faces,
            color=highlight_color,
            shading=None,
            parent=self.view.scene
        )

        if not hasattr(self, 'mesh_highlight_dict'):
            self.mesh_highlight_dict = {}

        # Remove old visual if exists
        if mesh_idx in self.mesh_highlight_dict:
            old_visual = self.mesh_highlight_dict[mesh_idx]
            if old_visual is not None:
                old_visual.parent = None

        self.mesh_highlight_dict[mesh_idx] = highlight_visual

    def _remove_mesh_highlight(self, mesh_idx):
        """Remove highlight visual for a mesh"""
        if not hasattr(self, 'mesh_highlight_dict'):
            return

        if mesh_idx in self.mesh_highlight_dict:
            visual = self.mesh_highlight_dict[mesh_idx]
            if visual is not None:
                visual.parent = None
            del self.mesh_highlight_dict[mesh_idx]

    def select_meshes_by_indices(self, indices, hue):
        """Manually select multiple meshes (e.g. from UI list)"""
        # Clear existing highlights not in the new selection
        to_remove = [m_idx for m_idx in self.selected_mesh_indices if m_idx not in indices]
        for m_idx in to_remove:
            self._remove_mesh_highlight(m_idx)

        # Add new highlights
        for m_idx in indices:
            if m_idx not in self.selected_mesh_indices:
                self._highlight_full_mesh(m_idx, hue)

        self.selected_mesh_indices = list(indices)

        # Emit signal to update UI
        self.mesh_selection_changed.emit(len(self.selected_mesh_indices))

        self.canvas.update()

    def select_mesh_by_index(self, mesh_idx, hue):
        """Manually select a single mesh (legacy support)"""
        self.select_meshes_by_indices([mesh_idx] if mesh_idx >= 0 else [], hue)

    def set_trail_mode(self, enabled):
        """Enable or disable trail drawing mode"""
        self.trail_mode = enabled
        if not enabled:
            self._clear_trail()
        self.canvas.update()

    def _update_trail_visual(self):
        """Update the trail preview visual"""
        if len(self.trail_points) < 2:
            self._clear_trail()
            return

        # Create line visual showing the trail
        trail_array = np.array(self.trail_points, dtype=np.float32)
        if self.trail_visual is not None:
            self.trail_visual.parent = None

        self.trail_visual = scene.visuals.Line(
            pos=trail_array,
            color=(1.0, 1.0, 0.0, 0.8),  # Yellow
            width=3,
            method='gl',
            parent=self.view.scene
        )
        self.canvas.update()

    def _clear_trail(self):
        """Clear the trail visual"""
        if self.trail_visual is not None:
            self.trail_visual.parent = None
            self.trail_visual = None
        self.trail_points = []
        self.canvas.update()

    def get_trail_waypoints(self):
        """Return the trail points as waypoints"""
        return self.trail_points.copy()

    def show_rotation_preview(self, preview_positions):
        """Show rotation preview markers"""
        if self.rotation_preview_visual is not None:
            self.rotation_preview_visual.parent = None

        # Create semi-transparent markers at preview positions
        self.rotation_preview_visual = visuals.Markers()
        self.rotation_preview_visual.set_data(
            pos=preview_positions,
            face_color=(1.0, 0.5, 0.0, 0.5),  # Semi-transparent orange
            edge_color=(1.0, 0.5, 0.0, 0.8),
            edge_width=2,
            size=15
        )
        self.rotation_preview_visual.parent = self.view.scene
        self.canvas.update()

    def clear_rotation_preview(self):
        """Clear rotation preview markers"""
        if self.rotation_preview_visual is not None:
            self.rotation_preview_visual.parent = None
            self.rotation_preview_visual = None
            self.canvas.update()


class ScrollbarOnlyFilter(QObject):
    """Event filter that only allows scrolling when mouse is over scrollbar"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # Check if the object is a QAbstractScrollArea (like QListWidget)
            if isinstance(obj, QAbstractScrollArea):
                # Get the vertical scrollbar
                scrollbar = obj.verticalScrollBar()
                if scrollbar and scrollbar.isVisible():
                    # Get mouse position relative to the widget
                    mouse_pos = obj.mapFromGlobal(QCursor.pos())
                    # Get scrollbar geometry
                    scrollbar_rect = scrollbar.geometry()

                    # Only allow wheel events if mouse is over the scrollbar
                    if not scrollbar_rect.contains(mouse_pos):
                        return True  # Block the event

        return super().eventFilter(obj, event)


class EntityListWidget(QWidget):
    """Entity list panel with search and filtering"""
    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entities = []
        self.display_mapping = []
        self.item_db = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        title = QLabel("Entities")
        title.setObjectName("title")
        layout.addWidget(title)

        # Sorting controls
        sort_layout = QHBoxLayout()
        sort_label = QLabel("Sort:")
        sort_layout.addWidget(sort_label)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Default", "ID", "Name", "Size", "X", "Y", "Z", "Distance"])
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        sort_layout.addWidget(self.sort_combo, 1)
        self.reverse_button = QPushButton("⇅")
        self.reverse_button.setMaximumWidth(40)
        self.reverse_button.setToolTip("Reverse sort order")
        self.reverse_button.clicked.connect(self._on_reverse_sort)
        sort_layout.addWidget(self.reverse_button)
        layout.addLayout(sort_layout)

        # Add group hierarchy toggle
        self.group_hierarchy_checkbox = QCheckBox("Group hierarchy")
        self.group_hierarchy_checkbox.setChecked(True)
        self.group_hierarchy_checkbox.setToolTip("Keep parent-child groups together when sorting")
        self.group_hierarchy_checkbox.stateChanged.connect(self._on_group_hierarchy_changed)
        layout.addWidget(self.group_hierarchy_checkbox)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search entities...")
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)
        self.count_label = QLabel("0 entities")
        self.count_label.setObjectName("info")
        layout.addWidget(self.count_label)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

        # Install scrollbar-only event filter
        self.scroll_filter = ScrollbarOnlyFilter(self)
        self.list_widget.installEventFilter(self.scroll_filter)

        layout.addWidget(self.list_widget)

        # Track sorting state
        self.last_sort = "Default"
        self.sort_reverse = False

    def set_entities(self, entities, item_db=None):
        self.entities = entities
        self.item_db = item_db or {}
        self.display_mapping = list(range(len(entities)))
        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()

        # Build parent_map: child_id -> parent_index
        parent_map = {}
        for i, e in enumerate(self.entities):
            for child_id in e.get('child_ids', []):
                padded_id = child_id.strip().zfill(4)
                parent_map[padded_id] = i

        # Track the current parent context as we iterate through display order
        current_parent_idx = None
        current_parent_children = set()

        # Display entities in display_mapping order (respects sorting)
        for display_idx, entity_idx in enumerate(self.display_mapping):
            if entity_idx >= len(self.entities):
                continue

            ent = self.entities[entity_idx]
            db_key = ent['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            name = info.get('NAME', info.get('obj_en', f"Entity {ent['id']}"))

            padded_current_id = ent['id'].strip().zfill(4)

            # Check if this entity is a child of the current parent context
            is_child_of_current_parent = (
                current_parent_idx is not None and
                padded_current_id in current_parent_children
            )

            # Determine prefix based on parent context
            if is_child_of_current_parent:
                # This is a child of the current parent
                prefix = "    ↳ "

                # Check if this child also has its own children following
                # (e.g., Record is child of Gramophone but also parent of Bells)
                child_ids = ent.get('child_ids', [])
                if child_ids:
                    next_entities = []
                    for i in range(display_idx + 1, min(display_idx + 50, len(self.display_mapping))):
                        next_idx = self.display_mapping[i]
                        if next_idx < len(self.entities):
                            next_entities.append(self.entities[next_idx]['id'].strip().zfill(4))
                        else:
                            break

                    # Check if any of this entity's children appear next
                    for child_id in child_ids:
                        padded_child = child_id.strip().zfill(4)
                        if next_entities and next_entities[0] == padded_child:
                            prefix = "    ↳ ▼ "  # Both child and parent
                            break
            else:
                # Not a child of current parent - check if this starts a new parent group
                child_ids = ent.get('child_ids', [])
                if child_ids:
                    # Check if any children appear in the next positions
                    next_entities = []
                    for i in range(display_idx + 1, min(display_idx + 50, len(self.display_mapping))):
                        next_idx = self.display_mapping[i]
                        if next_idx < len(self.entities):
                            next_entities.append(self.entities[next_idx]['id'].strip().zfill(4))
                        else:
                            break

                    # Check if consecutive entities are children of this entity
                    children_follow = False
                    for child_id in child_ids:
                        padded_child = child_id.strip().zfill(4)
                        if next_entities and next_entities[0] == padded_child:
                            children_follow = True
                            break

                    if children_follow:
                        # Start new parent context
                        current_parent_idx = entity_idx
                        current_parent_children = set(child_id.strip().zfill(4) for child_id in child_ids)
                        prefix = "▼ "
                    else:
                        # Has children but they don't follow immediately
                        current_parent_idx = None
                        current_parent_children = set()
                        prefix = ""
                else:
                    # No children
                    current_parent_idx = None
                    current_parent_children = set()
                    prefix = ""

            item = QListWidgetItem(f"{prefix}{name} [{ent['id']}]")
            item.setData(Qt.UserRole, entity_idx)
            self.list_widget.addItem(item)

        self.count_label.setText(f"{len(self.display_mapping)} entities")

    def _on_search(self, text):
        text = text.lower()
        if not text:
            self.display_mapping = list(range(len(self.entities)))
        else:
            self.display_mapping = []
            for i, ent in enumerate(self.entities):
                db_key = ent['id'].lstrip('0') or '0'
                info = self.item_db.get(db_key, {})
                name = info.get('NAME', info.get('obj_en', '')).lower()
                if text in name or text in ent['id'].lower():
                    self.display_mapping.append(i)
        self._refresh_list()

    def _on_selection_changed(self):
        selected = []
        for item in self.list_widget.selectedItems():
            selected.append(item.data(Qt.UserRole))
        self.selection_changed.emit(selected)

    def set_selection(self, indices):
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        first_selected_item = None
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) in indices:
                item.setSelected(True)
                if first_selected_item is None:
                    first_selected_item = item
        # Scroll to first selected item
        if first_selected_item is not None:
            self.list_widget.scrollToItem(first_selected_item)
        self.list_widget.blockSignals(False)

    def apply_size_filter(self, min_size, max_size, item_db):
        self.display_mapping = []
        for i, ent in enumerate(self.entities):
            db_key = ent['id'].lstrip('0') or '0'
            info = item_db.get(db_key, {})
            size = info.get('size_val', 0)
            if min_size <= size <= max_size:
                self.display_mapping.append(i)
        self._refresh_list()

    def _on_sort_changed(self, crit):
        """Handle sort criterion change"""
        if crit == "Default":
            self.display_mapping = list(range(len(self.entities)))
            self.sort_reverse = False
        else:
            self._apply_sort(crit)
        self.last_sort = crit
        self._refresh_list()

    def _on_reverse_sort(self):
        """Reverse the current sort order"""
        self.sort_reverse = not self.sort_reverse
        if self.last_sort != "Default":
            self._apply_sort(self.last_sort)
            self._refresh_list()

    def _on_group_hierarchy_changed(self):
        """Handle group hierarchy toggle change"""
        if self.last_sort != "Default":
            self._apply_sort(self.last_sort)
            self._refresh_list()

    def _apply_sort(self, crit):
        """Sort display_mapping by criterion"""
        def sort_key(idx):
            if idx >= len(self.entities):
                return 0
            e = self.entities[idx]
            db_key = e['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})

            if crit == "ID":
                return int(e['id'])
            elif crit == "Name":
                name = info.get('NAME', info.get('obj_en', ''))
                return name.lower() if name else ''
            elif crit == "Size":
                return info.get('size_val', 0)
            elif crit == "X":
                return e.get('x', 0)
            elif crit == "Y":
                return e.get('y', 0)
            elif crit == "Z":
                return e.get('z', 0)
            elif crit == "Distance":
                x, y, z = e.get('x', 0), e.get('y', 0), e.get('z', 0)
                return math.sqrt(x*x + y*y + z*z)
            return 0

        if self.group_hierarchy_checkbox.isChecked():
            # Group-aware sorting: sort parents, then insert children after their parents
            # Build child-to-parent map
            child_to_parent = {}
            for idx in self.display_mapping:
                if idx < len(self.entities):
                    for child_id in self.entities[idx].get('child_ids', []):
                        # Find child index
                        for child_idx in self.display_mapping:
                            if child_idx < len(self.entities) and self.entities[child_idx]['id'] == child_id:
                                child_to_parent[child_idx] = idx
                                break

            # Identify parents (entities with children) and standalone entities
            parents_and_standalone = []
            children = set(child_to_parent.keys())

            for idx in self.display_mapping:
                if idx not in children:
                    parents_and_standalone.append(idx)

            # Sort only the parents and standalone entities
            parents_and_standalone.sort(key=sort_key, reverse=self.sort_reverse)

            # Build final sorted list with children grouped under parents
            sorted_mapping = []
            for idx in parents_and_standalone:
                sorted_mapping.append(idx)
                # Add children of this parent in their original order
                if idx < len(self.entities):
                    for child_id in self.entities[idx].get('child_ids', []):
                        for child_idx in self.display_mapping:
                            if child_idx < len(self.entities) and self.entities[child_idx]['id'] == child_id:
                                sorted_mapping.append(child_idx)
                                break

            self.display_mapping = sorted_mapping
        else:
            # Normal sorting without hierarchy consideration
            self.display_mapping.sort(key=sort_key, reverse=self.sort_reverse)


class PositionEditor(QGroupBox):
    position_changed = pyqtSignal()
    preview_requested = pyqtSignal(float, float, float, bool)

    def __init__(self, parent=None):
        super().__init__("Position Editor", parent)
        self._setup_ui()
        self.entities = []
        self.selected_indices = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.offset_mode = QCheckBox("Offset Mode")
        self.offset_mode.setToolTip("When enabled, values are added to current position")
        layout.addWidget(self.offset_mode)
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
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_changes)
        layout.addWidget(apply_btn)

    def update_for_selection(self, entities, selected_indices):
        self.entities = entities
        self.selected_indices = selected_indices
        if not selected_indices:
            for axis in ['X', 'Y', 'Z']: self.spinboxes[axis].setValue(0)
            return
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
        if self.selected_indices:
            self.preview_requested.emit(
                self.spinboxes['X'].value(), self.spinboxes['Y'].value(),
                self.spinboxes['Z'].value(), self.offset_mode.isChecked()
            )

    def _on_spinbox_change(self):
        for axis in ['X', 'Y', 'Z']:
            self.sliders[axis].blockSignals(True)
            self.sliders[axis].setValue(int(self.spinboxes[axis].value()))
            self.sliders[axis].blockSignals(False)
        if self.selected_indices:
            self.preview_requested.emit(
                self.spinboxes['X'].value(), self.spinboxes['Y'].value(),
                self.spinboxes['Z'].value(), self.offset_mode.isChecked()
            )

    def _apply_changes(self):
        self.position_changed.emit()


class EntityInfoPanel(QGroupBox):
    changes_committed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__("Entity Info & Editor", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(6)

        # Read-only fields
        self.name_label = QLabel("-")
        self.name_label.setWordWrap(True)
        self.name_label.setObjectName("title")
        form.addRow("Name:", self.name_label)

        # Custom name field (editable)
        self.custom_name_entry = QLineEdit()
        self.custom_name_entry.setPlaceholderText("Enter custom name...")
        form.addRow("Custom Name:", self.custom_name_entry)

        self.size_label = QLabel("-")
        form.addRow("Size:", self.size_label)

        self.map_label = QLabel("-")
        form.addRow("Map:", self.map_label)

        self.pack_label = QLabel("-")
        form.addRow("Pack:", self.pack_label)

        # Parent/Child relationships
        self.relationship_label = QLabel("-")
        self.relationship_label.setStyleSheet("font-family: monospace; color: #4fc3f7;")
        self.relationship_label.setWordWrap(True)
        form.addRow("Relationships:", self.relationship_label)

        # Separator
        separator = QLabel("─" * 40)
        separator.setStyleSheet("color: #555;")
        form.addRow(separator)

        # Editable fields (from Batch Editor)
        self.entries = {}

        # ID field (editable)
        self.id_entry = QLineEdit()
        self.id_entry.setStyleSheet("font-family: monospace;")
        self.entries['index'] = self.id_entry
        form.addRow("ID:", self.id_entry)

        # Position
        self.pos_label = QLabel("-")
        self.pos_label.setStyleSheet("font-family: monospace;")
        form.addRow("Position:", self.pos_label)

        # Rotation
        self.rot_label = QLabel("-")
        self.rot_label.setStyleSheet("font-family: monospace; font-size: 22px;")
        self.rot_label.setWordWrap(True)
        form.addRow("Rotation:", self.rot_label)

        # Editable properties - 2 columns layout
        fields = [('atk', 'Attack Type'), ('mov', 'Move Type'), ('esc', 'Escape Type'),
                  ('spd', 'Speed'), ('pth', 'Path ID'), ('scale', 'Scale'),
                  ('plus_type', 'Plus Type'), ('parent_type', 'Parent Type'), ('clash_type', 'Clash Type'),
                  ('script_type', 'Script Type'), ('script_id', 'Script ID'), ('random_type', 'Random Type'),
                  ('random_id', 'Random ID'), ('random_put_range', 'Random Put Range'), ('comment_type', 'Comment Type'),
                  ('comment_id', 'Comment ID'), ('name_type', 'Name Type'), ('anim_type', 'Anim Type'),
                  ('anim_motion_id', 'Anim Motion ID'), ('change_type', 'Change Type'), ('change_mono_id', 'Change Mono ID'),
                  ('spmove_type', 'SpMove Type'), ('spmove_rise_height', 'SpMove Rise Height'),
                  ('spmove_appear_second', 'SpMove Appear Second'), ('plus_timing', 'Plus Timing'),
                  ('start_type', 'Start Type'), ('move_start_size', 'Move Start Size'), ('move_end_size', 'Move End Size')]

        # Use grid layout for 2 columns
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        for i, (key, label) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 3  # Each field takes 3 columns: label, entry, spacing

            label_widget = QLabel(f"{label}:")
            label_widget.setMinimumWidth(80)
            entry = QLineEdit()
            entry.setPlaceholderText(f"{label}")
            entry.setMaximumWidth(120)
            self.entries[key] = entry

            grid.addWidget(label_widget, row, col)
            grid.addWidget(entry, row, col + 1)

        form.addRow(grid)

        layout.addLayout(form)

        # Commit button
        commit_btn = QPushButton("COMMIT CHANGES")
        commit_btn.setObjectName("primary")
        commit_btn.clicked.connect(self._commit_changes)
        layout.addWidget(commit_btn)

    def update_info(self, entity, item_db=None, entities=None):
        if entity is None:
            self.name_label.setText("-")
            self.size_label.setText("-")
            self.map_label.setText("-")
            self.pack_label.setText("-")
            self.relationship_label.setText("-")
            self.pos_label.setText("-")
            self.rot_label.setText("-")
            for entry in self.entries.values():
                entry.clear()
            return

        db_key = entity['id'].lstrip('0') or '0'
        info = (item_db or {}).get(db_key, {})
        csv_name = entity.get('csv_name', info.get('obj_en', ''))
        custom_name = entity.get('custom_name', '')
        # Display custom name if set, otherwise CSV name
        display_name = custom_name if custom_name else (csv_name if csv_name else f"Entity {entity['id']}")

        # Format size display: show both human-readable and mm value
        size_display = info.get('size', '-')
        size_mm = info.get('size_mm', '')
        if size_display != '-' and size_mm:
            size_display = f"{size_display} ({size_mm} mm)"

        # Update read-only fields
        self.name_label.setText(display_name)
        self.custom_name_entry.setText(custom_name)
        self.size_label.setText(size_display)
        self.map_label.setText(entity.get('map_name', '-'))
        self.pack_label.setText(entity.get('pack', '-') or '-')
        self.pos_label.setText(f"X: {entity['x']:.2f}\nY: {entity['y']:.2f}\nZ: {entity['z']:.2f}")
        self.rot_label.setText(f"({entity['rx']:.3f}, {entity['ry']:.3f}, {entity['rz']:.3f}, {entity['rw']:.3f})")

        # Calculate and display parent/child relationships (matching kata.py logic)
        rel_text = ""
        if entities:
            # Build parent_map: child_id (padded) -> parent_entity_index
            parent_map = {}
            for i, e in enumerate(entities):
                for child_id in e.get('child_ids', []):
                    padded_id = child_id.strip().zfill(4)
                    parent_map[padded_id] = i

            # Check if this entity is a child
            padded_current_id = entity['id'].strip().zfill(4)
            if padded_current_id in parent_map:
                parent_idx = parent_map[padded_current_id]
                parent_e = entities[parent_idx]
                parent_db_key = parent_e['id'].lstrip('0') or '0'
                parent_info = (item_db or {}).get(parent_db_key, {})
                parent_name = parent_info.get('obj_en', f"Entity {parent_e['id']}")
                rel_text = f"Parent: {parent_name} ({parent_e['id']})"

            # Check if this entity has children
            child_count = len(entity.get('child_ids', []))
            if child_count > 0:
                if rel_text:
                    rel_text += f"\n{child_count} child{'ren' if child_count != 1 else ''}"
                else:
                    rel_text = f"{child_count} child{'ren' if child_count != 1 else ''}"

        self.relationship_label.setText(rel_text if rel_text else "-")

        # Update editable fields
        self.entries['index'].setText(entity.get('id', ''))
        self.entries['atk'].setText(entity.get('atk', ''))
        self.entries['mov'].setText(entity.get('mov', ''))
        self.entries['esc'].setText(entity.get('esc', ''))
        self.entries['spd'].setText(entity.get('spd', ''))
        self.entries['pth'].setText(entity.get('pth', ''))
        self.entries['scale'].setText(entity.get('scale', ''))
        self.entries['plus_type'].setText(entity.get('plus_type', ''))
        self.entries['parent_type'].setText(entity.get('parent_type', ''))
        self.entries['clash_type'].setText(entity.get('clash_type', ''))
        self.entries['script_type'].setText(entity.get('script_type', ''))
        self.entries['script_id'].setText(entity.get('script_id', ''))
        self.entries['random_type'].setText(entity.get('random_type', ''))
        self.entries['random_id'].setText(entity.get('random_id', ''))
        self.entries['random_put_range'].setText(entity.get('random_put_range', ''))
        self.entries['comment_type'].setText(entity.get('comment_type', ''))
        self.entries['comment_id'].setText(entity.get('comment_id', ''))
        self.entries['name_type'].setText(entity.get('name_type', ''))
        self.entries['anim_type'].setText(entity.get('anim_type', ''))
        self.entries['anim_motion_id'].setText(entity.get('anim_motion_id', ''))
        self.entries['change_type'].setText(entity.get('change_type', ''))
        self.entries['change_mono_id'].setText(entity.get('change_mono_id', ''))
        self.entries['spmove_type'].setText(entity.get('spmove_type', ''))
        self.entries['spmove_rise_height'].setText(entity.get('spmove_rise_height', ''))
        self.entries['spmove_appear_second'].setText(entity.get('spmove_appear_second', ''))
        self.entries['plus_timing'].setText(entity.get('plus_timing', ''))
        self.entries['start_type'].setText(entity.get('start_type', ''))
        self.entries['move_start_size'].setText(entity.get('move_start_size', ''))
        self.entries['move_end_size'].setText(entity.get('move_end_size', ''))

    def _commit_changes(self):
        changes = {}
        for key, entry in self.entries.items():
            text = entry.text().strip()
            if text: changes[key] = text
        # Handle custom name separately
        custom_name = self.custom_name_entry.text().strip()
        changes['custom_name'] = custom_name  # Empty string is valid (clears custom name)
        if changes: self.changes_committed.emit(changes)


class QuaternionViewer(QGroupBox):
    rotation_changed = pyqtSignal(float, float, float, float)

    def __init__(self, parent=None):
        super().__init__("Quaternion Viewer", parent)
        self._setup_ui()
        self.is_updating = False
        self.current_quaternion = (0, 0, 0, 1)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        viz_label = QLabel("Rotation Visualization:")
        viz_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(viz_label)

        # Add axis direction labels
        axis_info = QLabel("Red (X): Right | Green (Y): Top | Blue (Z): Front")
        axis_info.setStyleSheet("font-size: 10pt; color: #888; font-style: italic;")
        axis_info.setWordWrap(True)
        layout.addWidget(axis_info)

        self.rot_canvas = scene.SceneCanvas(keys='interactive', bgcolor='#0a0a0a', size=(200, 200), show=False)
        self.rot_view = self.rot_canvas.central_widget.add_view()
        self.rot_view.camera = scene.TurntableCamera(fov=45, distance=5, elevation=20, azimuth=45)
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.rot_canvas.native)
        canvas_widget.setFixedHeight(200)
        layout.addWidget(canvas_widget)
        self._create_rotation_visuals()
        quat_label = QLabel("Quaternion (X, Y, Z, W):")
        quat_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(quat_label)
        self.quat_display = QLabel("X: 0.000  Y: 0.000  Z: 0.000  W: 1.000")
        self.quat_display.setStyleSheet("font-family: monospace; background: #1a1a2e; padding: 5px;")
        layout.addWidget(self.quat_display)
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

        apply_btn = QPushButton("Apply Rotation")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_rotation)
        layout.addWidget(apply_btn)

    def _create_rotation_visuals(self):
        # Add cardinal direction grid
        self.grid = scene.visuals.GridLines(
            color=(0.3, 0.3, 0.3, 0.5),
            parent=self.rot_view.scene
        )

        box_vertices = np.array([
            [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
            [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]
        ], dtype=np.float32)
        box_faces = np.array([
            [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
            [2, 3, 7], [2, 7, 6], [0, 3, 7], [0, 7, 4], [1, 2, 6], [1, 6, 5]
        ], dtype=np.uint32)
        self.box_mesh = visuals.Mesh(vertices=box_vertices, faces=box_faces, color=(0.3, 0.5, 0.8, 0.3), parent=self.rot_view.scene)
        x_axis_points = np.array([[0, 0, 0], [1.2, 0, 0]], dtype=np.float32)
        self.x_axis = visuals.Arrow(pos=x_axis_points, color=(1.0, 0.0, 0.0, 1.0), arrow_size=5, arrow_type='stealth', parent=self.rot_view.scene)
        y_axis_points = np.array([[0, 0, 0], [0, 1.2, 0]], dtype=np.float32)
        self.y_axis = visuals.Arrow(pos=y_axis_points, color=(0.0, 1.0, 0.0, 1.0), arrow_size=5, arrow_type='stealth', parent=self.rot_view.scene)
        z_axis_points = np.array([[0, 0, 0], [0, 0, 1.2]], dtype=np.float32)
        self.z_axis = visuals.Arrow(pos=z_axis_points, color=(0.0, 0.0, 1.0, 1.0), arrow_size=5, arrow_type='stealth', parent=self.rot_view.scene)
        from vispy.scene import transforms
        self.rotation_transform = transforms.MatrixTransform()
        self.box_mesh.transform = self.rotation_transform
        self.x_axis.transform = self.rotation_transform
        self.y_axis.transform = self.rotation_transform
        self.z_axis.transform = self.rotation_transform

    def _update_rotation_visual(self, x, y, z, w):
        from vispy.util.quaternion import Quaternion
        quat = Quaternion(w, x, y, z)
        rotation_matrix = quat.get_matrix()
        self.rotation_transform.matrix = rotation_matrix
        self.rot_canvas.update()

    def update_quaternion(self, x, y, z, w):
        self.is_updating = True
        self.current_quaternion = (x, y, z, w)
        self.quat_display.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}  W: {w:.3f}")
        self._update_rotation_visual(x, y, z, w)
        roll, pitch, yaw = self.quaternion_to_euler(x, y, z, w)
        for axis, val in [('roll', roll), ('pitch', pitch), ('yaw', yaw)]:
            self.euler_sliders[axis].setValue(int(val))
            self.euler_spinboxes[axis].setValue(val)
        self.is_updating = False

    def _on_euler_slider_change(self, axis):
        if self.is_updating: return
        self.euler_spinboxes[axis].blockSignals(True)
        self.euler_spinboxes[axis].setValue(self.euler_sliders[axis].value())
        self.euler_spinboxes[axis].blockSignals(False)
        self._update_quat_preview()

    def _on_euler_spinbox_change(self, axis):
        if self.is_updating: return
        self.euler_sliders[axis].blockSignals(True)
        self.euler_sliders[axis].setValue(int(self.euler_spinboxes[axis].value()))
        self.euler_sliders[axis].blockSignals(False)
        self._update_quat_preview()

    def _update_quat_preview(self):
        roll = self.euler_spinboxes['roll'].value()
        pitch = self.euler_spinboxes['pitch'].value()
        yaw = self.euler_spinboxes['yaw'].value()
        x, y, z, w = self.euler_to_quaternion(roll, pitch, yaw)
        self.current_quaternion = (x, y, z, w)
        self.quat_display.setText(f"X: {x:.3f}  Y: {y:.3f}  Z: {z:.3f}  W: {w:.3f}")
        self._update_rotation_visual(x, y, z, w)

    def _apply_rotation(self):
        roll = self.euler_spinboxes['roll'].value()
        pitch = self.euler_spinboxes['pitch'].value()
        yaw = self.euler_spinboxes['yaw'].value()
        x, y, z, w = self.euler_to_quaternion(roll, pitch, yaw)
        self.rotation_changed.emit(x, y, z, w)

    @staticmethod
    def quaternion_to_euler(x, y, z, w):
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        sinp = 2 * (w * y - z * x)
        pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

    @staticmethod
    def euler_to_quaternion(roll, pitch, yaw):
        roll_rad, pitch_rad, yaw_rad = math.radians(roll), math.radians(pitch), math.radians(yaw)
        cy, sy = math.cos(yaw_rad * 0.5), math.sin(yaw_rad * 0.5)
        cp, sp = math.cos(pitch_rad * 0.5), math.sin(pitch_rad * 0.5)
        cr, sr = math.cos(roll_rad * 0.5), math.sin(roll_rad * 0.5)
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        return x, y, z, w


class SizeFilterPanel(QGroupBox):
    filter_changed = pyqtSignal(float, float, bool)

    def __init__(self, parent=None):
        super().__init__("Size Filter", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.enabled = QCheckBox("Enable Size Filter")
        self.enabled.stateChanged.connect(self._emit_filter)
        layout.addWidget(self.enabled)
        min_row = QHBoxLayout()
        min_row.addWidget(QLabel("Min:"))
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(0, 100000000)
        self.min_spin.setValue(0)
        self.min_spin.valueChanged.connect(self._emit_filter)
        min_row.addWidget(self.min_spin)
        layout.addLayout(min_row)
        max_row = QHBoxLayout()
        max_row.addWidget(QLabel("Max:"))
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(0, 100000000)
        self.max_spin.setValue(10000000)
        self.max_spin.valueChanged.connect(self._emit_filter)
        max_row.addWidget(self.max_spin)
        layout.addLayout(max_row)

    def _emit_filter(self):
        self.filter_changed.emit(self.min_spin.value(), self.max_spin.value(), self.enabled.isChecked())


class ImportedMeshControlPanel(QGroupBox):
    """Control panel for manipulating imported meshes"""
    mesh_updated = pyqtSignal(int)  # mesh_idx
    mesh_selection_mode_changed = pyqtSignal(bool)  # True = mesh selection mode, False = entity selection mode
    mesh_highlight_hue_changed = pyqtSignal(int)  # hue value (0-360)
    apply_transform_requested = pyqtSignal()  # Signal to request baking transforms

    def __init__(self, parent=None):
        super().__init__("Imported Mesh Controls", parent)
        self.imported_meshes = []
        self.current_mesh_idx = -1
        self.selected_mesh_indices = []  # Track multiple selected meshes
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Mesh selection mode toggle
        mesh_mode_row = QHBoxLayout()
        self.mesh_selection_toggle = QCheckBox("Mesh Selection Mode")
        self.mesh_selection_toggle.setToolTip("Enable to select and highlight meshes by clicking")
        self.mesh_selection_toggle.stateChanged.connect(self._on_mesh_mode_toggled)
        mesh_mode_row.addWidget(self.mesh_selection_toggle)

        self.mesh_count_label = QLabel("(0 selected)")
        self.mesh_count_label.setStyleSheet("color: #4fc3f7; font-weight: bold;")
        mesh_mode_row.addWidget(self.mesh_count_label)
        mesh_mode_row.addStretch()
        layout.addLayout(mesh_mode_row)

        # Mesh highlight hue slider
        hue_row = QHBoxLayout()
        hue_row.addWidget(QLabel("Highlight Hue:"))
        self.hue_slider = QSlider(Qt.Horizontal)
        self.hue_slider.setRange(0, 360)
        self.hue_slider.setValue(210)  # Default blue hue
        self.hue_slider.setToolTip("Adjust the color of mesh highlighting")
        self.hue_slider.valueChanged.connect(self._on_hue_changed)
        hue_row.addWidget(self.hue_slider)
        self.hue_label = QLabel("210°")
        hue_row.addWidget(self.hue_label)
        layout.addLayout(hue_row)

        # Auto-load entity meshes toggle
        autoload_row = QHBoxLayout()
        self.autoload_meshes_toggle = QCheckBox("Auto-load Entity Meshes")
        self.autoload_meshes_toggle.setToolTip("Automatically load saved mesh/OBJ files for entities on map load")
        self.autoload_meshes_toggle.setChecked(True)  # Default enabled
        autoload_row.addWidget(self.autoload_meshes_toggle)
        autoload_row.addStretch()
        layout.addLayout(autoload_row)

        # Separator
        separator = QLabel("─" * 40)
        separator.setStyleSheet("color: #555;")
        layout.addWidget(separator)

        # Mesh selection
        self.mesh_combo = QComboBox()
        self.mesh_combo.currentIndexChanged.connect(self._on_mesh_selected)
        layout.addWidget(QLabel("Select Mesh:"))
        layout.addWidget(self.mesh_combo)

        # Position controls (horizontal layout)
        pos_group = QGroupBox("Position")
        pos_layout = QGridLayout(pos_group)
        pos_layout.addWidget(QLabel("X:"), 0, 0)
        self.pos_x = QDoubleSpinBox()
        self.pos_x.setRange(-100000, 100000)
        self.pos_x.setFocusPolicy(Qt.StrongFocus)
        self.pos_x.valueChanged.connect(self._on_transform_changed)
        pos_layout.addWidget(self.pos_x, 0, 1)
        pos_layout.addWidget(QLabel("Y:"), 0, 2)
        self.pos_y = QDoubleSpinBox()
        self.pos_y.setRange(-100000, 100000)
        self.pos_y.setFocusPolicy(Qt.StrongFocus)
        self.pos_y.valueChanged.connect(self._on_transform_changed)
        pos_layout.addWidget(self.pos_y, 0, 3)
        pos_layout.addWidget(QLabel("Z:"), 0, 4)
        self.pos_z = QDoubleSpinBox()
        self.pos_z.setRange(-100000, 100000)
        self.pos_z.setFocusPolicy(Qt.StrongFocus)
        self.pos_z.valueChanged.connect(self._on_transform_changed)
        pos_layout.addWidget(self.pos_z, 0, 5)
        layout.addWidget(pos_group)

        # Scale controls (horizontal layout)
        scale_group = QGroupBox("Scale")
        scale_layout = QGridLayout(scale_group)
        scale_layout.addWidget(QLabel("X:"), 0, 0)
        self.scale_x = QDoubleSpinBox()
        self.scale_x.setRange(0.01, 1000.0)
        self.scale_x.setValue(1.0)
        self.scale_x.setSingleStep(0.1)
        self.scale_x.setFocusPolicy(Qt.StrongFocus)
        self.scale_x.valueChanged.connect(self._on_transform_changed)
        scale_layout.addWidget(self.scale_x, 0, 1)
        scale_layout.addWidget(QLabel("Y:"), 0, 2)
        self.scale_y = QDoubleSpinBox()
        self.scale_y.setRange(0.01, 1000.0)
        self.scale_y.setValue(1.0)
        self.scale_y.setSingleStep(0.1)
        self.scale_y.setFocusPolicy(Qt.StrongFocus)
        self.scale_y.valueChanged.connect(self._on_transform_changed)
        scale_layout.addWidget(self.scale_y, 0, 3)
        scale_layout.addWidget(QLabel("Z:"), 0, 4)
        self.scale_z = QDoubleSpinBox()
        self.scale_z.setRange(0.01, 1000.0)
        self.scale_z.setValue(1.0)
        self.scale_z.setSingleStep(0.1)
        self.scale_z.setFocusPolicy(Qt.StrongFocus)
        self.scale_z.valueChanged.connect(self._on_transform_changed)
        scale_layout.addWidget(self.scale_z, 0, 5)
        layout.addWidget(scale_group)

        # Rotation controls (horizontal layout)
        rot_group = QGroupBox("Rotation (Degrees)")
        rot_layout = QGridLayout(rot_group)
        rot_layout.addWidget(QLabel("X:"), 0, 0)
        self.rot_x = QDoubleSpinBox()
        self.rot_x.setRange(-180, 180)
        self.rot_x.setFocusPolicy(Qt.StrongFocus)
        self.rot_x.valueChanged.connect(self._on_transform_changed)
        rot_layout.addWidget(self.rot_x, 0, 1)
        rot_layout.addWidget(QLabel("Y:"), 0, 2)
        self.rot_y = QDoubleSpinBox()
        self.rot_y.setRange(-180, 180)
        self.rot_y.setFocusPolicy(Qt.StrongFocus)
        self.rot_y.valueChanged.connect(self._on_transform_changed)
        rot_layout.addWidget(self.rot_y, 0, 3)
        rot_layout.addWidget(QLabel("Z:"), 0, 4)
        self.rot_z = QDoubleSpinBox()
        self.rot_z.setRange(-180, 180)
        self.rot_z.setFocusPolicy(Qt.StrongFocus)
        self.rot_z.valueChanged.connect(self._on_transform_changed)
        rot_layout.addWidget(self.rot_z, 0, 5)
        layout.addWidget(rot_group)

        # Flip controls
        flip_group = QGroupBox("Flip")
        flip_layout = QHBoxLayout(flip_group)
        self.flip_x = QCheckBox("X")
        self.flip_x.stateChanged.connect(self._on_transform_changed)
        flip_layout.addWidget(self.flip_x)
        self.flip_y = QCheckBox("Y")
        self.flip_y.stateChanged.connect(self._on_transform_changed)
        flip_layout.addWidget(self.flip_y)
        self.flip_z = QCheckBox("Z")
        self.flip_z.stateChanged.connect(self._on_transform_changed)
        flip_layout.addWidget(self.flip_z)
        layout.addWidget(flip_group)

        # Apply Transform Button
        apply_btn = QPushButton("Apply (Bake) Transforms")
        apply_btn.setToolTip("Permanently apply current Scale, Rotation, and Flip to vertices (resets transform controls)")
        apply_btn.clicked.connect(self._emit_apply_transform)
        layout.addWidget(apply_btn)

        layout.addStretch()

        # Visibility
        self.visible_check = QCheckBox("Visible")
        self.visible_check.setChecked(True)
        self.visible_check.stateChanged.connect(self._on_transform_changed)
        layout.addWidget(self.visible_check)

        # Delete button
        delete_btn = QPushButton("Delete Mesh")
        delete_btn.clicked.connect(self._delete_current_mesh)
        layout.addWidget(delete_btn)

    def _emit_apply_transform(self):
        """Emit signal to apply transforms"""
        self.apply_transform_requested.emit()

    def set_meshes(self, meshes):
        self.imported_meshes = meshes
        self.mesh_combo.blockSignals(True)
        self.mesh_combo.clear()
        for i, mesh in enumerate(meshes):
            self.mesh_combo.addItem(f"{i}: {mesh['name']}", i)
        self.mesh_combo.blockSignals(False)
        if meshes:
            self.current_mesh_idx = 0
            self._update_ui_from_mesh()

    def set_current_mesh(self, index):
        """Set the current mesh by index and update UI"""
        if 0 <= index < len(self.imported_meshes):
            self.current_mesh_idx = index
            self.mesh_combo.blockSignals(True)
            self.mesh_combo.setCurrentIndex(index)
            self.mesh_combo.blockSignals(False)
            self._update_ui_from_mesh()

    def _on_mesh_selected(self, index):
        self.current_mesh_idx = self.mesh_combo.currentData()
        if self.current_mesh_idx is not None:
            self._update_ui_from_mesh()

    def _update_ui_from_mesh(self):
        if self.current_mesh_idx < 0 or self.current_mesh_idx >= len(self.imported_meshes):
            return
        mesh = self.imported_meshes[self.current_mesh_idx]

        # Block signals during update
        for widget in [self.pos_x, self.pos_y, self.pos_z,
                       self.scale_x, self.scale_y, self.scale_z,
                       self.rot_x, self.rot_y, self.rot_z, self.visible_check,
                       self.flip_x, self.flip_y, self.flip_z]:
            widget.blockSignals(True)

        self.pos_x.setValue(mesh['position'][0])
        self.pos_y.setValue(mesh['position'][1])
        self.pos_z.setValue(mesh['position'][2])

        # Handle both old 'scale' and new 'scale_xyz'
        if 'scale_xyz' in mesh:
            self.scale_x.setValue(mesh['scale_xyz'][0])
            self.scale_y.setValue(mesh['scale_xyz'][1])
            self.scale_z.setValue(mesh['scale_xyz'][2])
        else:
            uniform_scale = mesh.get('scale', 1.0)
            self.scale_x.setValue(uniform_scale)
            self.scale_y.setValue(uniform_scale)
            self.scale_z.setValue(uniform_scale)

        # Convert quaternion to Euler for display
        quat = mesh.get('rotation', np.array([0, 0, 0, 1]))
        euler = self._quat_to_euler(quat)
        self.rot_x.setValue(np.degrees(euler[0]))
        self.rot_y.setValue(np.degrees(euler[1]))
        self.rot_z.setValue(np.degrees(euler[2]))

        self.visible_check.setChecked(mesh.get('visible', True))

        # Flip states
        flip = mesh.get('flip', [False, False, False])
        self.flip_x.setChecked(flip[0])
        self.flip_y.setChecked(flip[1])
        self.flip_z.setChecked(flip[2])

        # Unblock signals
        for widget in [self.pos_x, self.pos_y, self.pos_z,
                       self.scale_x, self.scale_y, self.scale_z,
                       self.rot_x, self.rot_y, self.rot_z, self.visible_check,
                       self.flip_x, self.flip_y, self.flip_z]:
            widget.blockSignals(False)

    def _on_transform_changed(self):
        """Handle transformation changes and apply to ALL meshes simultaneously"""
        if not self.imported_meshes:
            return
            
        pos = np.array([self.pos_x.value(), self.pos_y.value(), self.pos_z.value()], dtype=np.float32)
        scale = np.array([self.scale_x.value(), self.scale_y.value(), self.scale_z.value()], dtype=np.float32)
        visible = self.visible_check.isChecked()
        flip = [self.flip_x.isChecked(), self.flip_y.isChecked(), self.flip_z.isChecked()]
        
        # Convert Euler to quaternion
        euler_rad = np.radians([self.rot_x.value(), self.rot_y.value(), self.rot_z.value()])
        quat = self._euler_to_quat(euler_rad)

        # Apply to all imported meshes
        for mesh in self.imported_meshes:
            mesh['position'] = pos.copy()
            mesh['scale_xyz'] = scale.copy()
            mesh['visible'] = visible
            mesh['flip'] = flip.copy()
            mesh['rotation'] = quat.copy()

        # Signal update for all (index -1)
        self.mesh_updated.emit(-1)

    def _euler_to_quat(self, euler):
        """Convert Euler angles (XYZ order) to quaternion"""
        cx, cy, cz = np.cos(euler / 2)
        sx, sy, sz = np.sin(euler / 2)

        qw = cx * cy * cz + sx * sy * sz
        qx = sx * cy * cz - cx * sy * sz
        qy = cx * sy * cz + sx * cy * sz
        qz = cx * cy * sz - sx * sy * cz

        return np.array([qx, qy, qz, qw], dtype=np.float32)

    def _quat_to_euler(self, quat):
        """Convert quaternion to Euler angles (XYZ order)"""
        qx, qy, qz, qw = quat

        # Roll (x-axis rotation)
        sinr_cosp = 2 * (qw * qx + qy * qz)
        cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
        roll = np.arctan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (qw * qy - qz * qx)
        if abs(sinp) >= 1:
            pitch = np.copysign(np.pi / 2, sinp)
        else:
            pitch = np.arcsin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (qw * qz + qx * qy)
        cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
        yaw = np.arctan2(siny_cosp, cosy_cosp)

        return np.array([roll, pitch, yaw])

    def _on_mesh_mode_toggled(self, state):
        """Handle mesh selection mode toggle"""
        is_mesh_mode = state == Qt.Checked
        self.mesh_selection_mode_changed.emit(is_mesh_mode)

    def _on_hue_changed(self, value):
        """Handle highlight hue slider change"""
        self.hue_label.setText(f"{value}°")
        # Emit signal to update mesh highlight hue
        self.mesh_highlight_hue_changed.emit(value)

    def update_selected_count(self, count):
        """Update the selected mesh count label"""
        self.mesh_count_label.setText(f"({count} selected)")

    def get_highlight_color(self):
        """Get the current highlight color based on hue slider"""
        hue = self.hue_slider.value()
        # Convert HSV to RGB (with S=1, V=1 for full saturation/brightness)
        # Then add alpha for translucency
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.8, 1.0)
        return (r, g, b, 0.5)  # 50% opacity

    def _delete_current_mesh(self):
        if self.current_mesh_idx < 0 or self.current_mesh_idx >= len(self.imported_meshes):
            return
        reply = QMessageBox.question(self, "Delete Mesh",
                                     "Are you sure you want to delete this mesh?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Signal will be handled by main window
            self.imported_meshes.pop(self.current_mesh_idx)
            self.set_meshes(self.imported_meshes)
            self.mesh_updated.emit(-1)  # -1 signals full refresh


class MeshGeneratorPanel(QGroupBox):
    generate_requested = pyqtSignal(dict)
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Mesh Generator", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
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
        self.selected_only = QCheckBox("Selected entities only")
        layout.addWidget(self.selected_only)
        self.exclude_large = QCheckBox("Exclude size >9M")
        self.exclude_large.setChecked(True)
        layout.addWidget(self.exclude_large)
        self.floor_priority = QCheckBox("Prioritize floors")
        self.floor_priority.setChecked(True)
        layout.addWidget(self.floor_priority)
        self.snap_to_mesh = QCheckBox("Snap entities to mesh")
        self.snap_to_mesh.setToolTip("Move selected entities to nearest mesh surface")
        layout.addWidget(self.snap_to_mesh)
        alpha_row = QHBoxLayout()
        alpha_row.addWidget(QLabel("Opacity:"))
        self.mesh_alpha = QSlider(Qt.Horizontal)
        self.mesh_alpha.setRange(10, 100)
        self.mesh_alpha.setValue(50)
        alpha_row.addWidget(self.mesh_alpha)
        layout.addLayout(alpha_row)
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
            'snap_to_mesh': self.snap_to_mesh.isChecked(),
        })


class PatternPlacerPanel(QGroupBox):
    pattern_applied = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Pattern Placer", parent)
        self._setup_ui()
        self.waypoints = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Pattern type and count in one row
        top_row = QHBoxLayout()
        self.pattern_group = QButtonGroup(self)
        for ptype in ["Circle", "Line", "Path"]:
            rb = QRadioButton(ptype)
            if ptype == "Circle": rb.setChecked(True)
            self.pattern_group.addButton(rb)
            top_row.addWidget(rb)
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("font-weight: bold;")
        top_row.addWidget(self.count_label)
        layout.addLayout(top_row)

        # Size parameter (used as radius for Circle, spacing for Line/Path)
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 5000)
        self.size_spin.setValue(50)
        self.size_spin.setMaximumWidth(100)
        self.size_spin.setToolTip("Radius for Circle pattern, spacing for Line/Path patterns")
        size_row.addWidget(self.size_spin)
        layout.addLayout(size_row)

        # Waypoints compact
        wp_row = QHBoxLayout()
        place_entities_btn = QPushButton("Place Entities")
        place_entities_btn.clicked.connect(lambda: self.pattern_applied.emit("add_waypoint", {}))
        wp_row.addWidget(place_entities_btn)

        position_btn = QPushButton("Position")
        position_btn.setToolTip("Move selected entities to waypoint positions")
        position_btn.clicked.connect(lambda: self.pattern_applied.emit("position_to_waypoints", {}))
        wp_row.addWidget(position_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_waypoints)
        wp_row.addWidget(clear_btn)
        layout.addLayout(wp_row)

        self.waypoint_list = QListWidget()
        self.waypoint_list.setMaximumHeight(60)
        layout.addWidget(self.waypoint_list)

        apply_btn = QPushButton("APPLY PATTERN")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_pattern)
        layout.addWidget(apply_btn)

        # Trail drawing button
        self.trail_btn = QPushButton("Create Trail")
        self.trail_btn.setCheckable(True)
        self.trail_btn.setToolTip("Draw a 3D trail path by dragging in the canvas")
        self.trail_btn.clicked.connect(self._on_trail_mode_toggled)
        layout.addWidget(self.trail_btn)

    def _on_trail_mode_toggled(self, checked):
        """Emit signal to toggle trail drawing mode"""
        self.pattern_applied.emit("trail_mode", {"enabled": checked})

    def update_count(self, count):
        self.count_label.setText(f"({count})")

    def add_waypoint(self, x, y, z):
        self.waypoints.append((x, y, z))
        self.waypoint_list.addItem(f"WP{len(self.waypoints)}: ({x:.1f}, {y:.1f}, {z:.1f})")

        # Auto-select Path mode after first waypoint
        if len(self.waypoints) == 1:
            for btn in self.pattern_group.buttons():
                if btn.text() == "Path":
                    btn.setChecked(True)
                    break

    def _clear_waypoints(self):
        self.waypoints = []
        self.waypoint_list.clear()

    def _apply_pattern(self):
        checked = self.pattern_group.checkedButton()
        if checked:
            pattern_type = checked.text()
            size_value = self.size_spin.value()
            params = {
                'radius': size_value,  # Used for Circle
                'spacing': size_value,  # Used for Line/Path
                'waypoints': self.waypoints.copy(),
            }
            self.pattern_applied.emit(pattern_type, params)


class RotateAroundAxisPanel(QGroupBox):
    """Separate panel for rotation controls"""
    operation_requested = pyqtSignal(str, dict)
    preview_requested = pyqtSignal(str, dict)  # For live preview

    def __init__(self, parent=None):
        super().__init__("Rotate Around Axis", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Angle slider
        angle_row = QHBoxLayout()
        angle_row.addWidget(QLabel("Angle:"))
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        angle_row.addWidget(self.angle_slider)
        self.angle_label = QLabel("0°")
        self.angle_slider.valueChanged.connect(self._on_angle_changed)
        angle_row.addWidget(self.angle_label)
        layout.addLayout(angle_row)

        # Axis toggles (checkboxes that control which axis the slider affects)
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Active Axis:"))
        self.axis_x = QCheckBox("X")
        self.axis_x.setToolTip("Slider rotates around X axis")
        self.axis_x.toggled.connect(self._on_axis_toggle)
        axis_row.addWidget(self.axis_x)
        self.axis_y = QCheckBox("Y")
        self.axis_y.setToolTip("Slider rotates around Y axis")
        self.axis_y.toggled.connect(self._on_axis_toggle)
        axis_row.addWidget(self.axis_y)
        self.axis_z = QCheckBox("Z")
        self.axis_z.setToolTip("Slider rotates around Z axis")
        self.axis_z.toggled.connect(self._on_axis_toggle)
        axis_row.addWidget(self.axis_z)
        layout.addLayout(axis_row)

        # Preview checkbox
        self.preview_check = QCheckBox("Live Preview")
        self.preview_check.setChecked(True)
        self.preview_check.setToolTip("Show rotation preview in 3D view")
        layout.addWidget(self.preview_check)

        # Apply button
        apply_btn = QPushButton("Apply Rotation")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self._apply_rotation)
        layout.addWidget(apply_btn)

    def _on_angle_changed(self, value):
        self.angle_label.setText(f"{value}°")
        # Trigger preview if enabled and an axis is selected
        if self.preview_check.isChecked():
            active_axis = self._get_active_axis()
            if active_axis:
                self.preview_requested.emit("rotate_preview", {"axis": active_axis, "angle": value})

    def _on_axis_toggle(self, checked):
        # Only allow one axis to be active at a time
        sender = self.sender()
        if checked:
            for checkbox in [self.axis_x, self.axis_y, self.axis_z]:
                if checkbox != sender:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
            # Trigger preview
            if self.preview_check.isChecked():
                active_axis = self._get_active_axis()
                if active_axis:
                    self.preview_requested.emit("rotate_preview", {"axis": active_axis, "angle": self.angle_slider.value()})

    def _get_active_axis(self):
        """Get the currently active axis"""
        if self.axis_x.isChecked():
            return 'x'
        elif self.axis_y.isChecked():
            return 'y'
        elif self.axis_z.isChecked():
            return 'z'
        return None

    def _apply_rotation(self):
        """Apply the rotation to selected entities"""
        active_axis = self._get_active_axis()
        if not active_axis:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Axis", "Select an axis (X, Y, or Z) to rotate around.")
            return
        self._emit_operation("rotate", {"axis": active_axis, "angle": self.angle_slider.value()})

    def _emit_operation(self, op_type, params):
        self.operation_requested.emit(op_type, params)


class PositionOperationsPanel(QGroupBox):
    operation_requested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Position Operations", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        spread_label = QLabel("Spread/Compress:")
        spread_label.setObjectName("section")
        layout.addWidget(spread_label)
        spread_row = QHBoxLayout()
        spread_row.addWidget(QLabel("Factor:"))
        self.spread_slider = QSlider(Qt.Horizontal)
        self.spread_slider.setRange(1, 50)
        self.spread_slider.setValue(10)
        spread_row.addWidget(self.spread_slider)
        self.spread_label = QLabel("1.0")
        self.spread_slider.valueChanged.connect(lambda v: self.spread_label.setText(f"{v/10.0:.1f}"))
        spread_row.addWidget(self.spread_label)
        layout.addLayout(spread_row)
        spread_btns = QHBoxLayout()
        for axis in ["X", "Y", "Z", "All"]:
            btn = QPushButton(f"Spread {axis}")
            btn.clicked.connect(lambda checked, a=axis.lower(): self._emit_operation("spread", {"axis": a, "factor": self.spread_slider.value() / 10.0}))
            spread_btns.addWidget(btn)
        layout.addLayout(spread_btns)

        # Snap to Waypoint controls
        snap_row = QHBoxLayout()
        snap_row.addWidget(QLabel("Snap to Waypoint:"))
        snap_floor_btn = QPushButton("Floor")
        snap_floor_btn.setToolTip("Snap to waypoint's XZ position, keep entity Y")
        snap_floor_btn.clicked.connect(lambda: self._emit_operation("snap_waypoint", {"axis": "floor"}))
        snap_row.addWidget(snap_floor_btn)
        snap_x_btn = QPushButton("X")
        snap_x_btn.setToolTip("Snap X coordinate only")
        snap_x_btn.clicked.connect(lambda: self._emit_operation("snap_waypoint", {"axis": "x"}))
        snap_row.addWidget(snap_x_btn)
        snap_z_btn = QPushButton("Z")
        snap_z_btn.setToolTip("Snap Z coordinate only")
        snap_z_btn.clicked.connect(lambda: self._emit_operation("snap_waypoint", {"axis": "z"}))
        snap_row.addWidget(snap_z_btn)
        layout.addLayout(snap_row)

        scatter_label = QLabel("Scatter Positions:")
        scatter_label.setObjectName("section")
        layout.addWidget(scatter_label)
        for axis in ["X", "Y", "Z"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{axis} Range:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(10)
            row.addWidget(slider)
            label = QLabel("5.0")
            slider.valueChanged.connect(lambda v, lbl=label: lbl.setText(f"{v/2.0:.1f}"))
            row.addWidget(label)
            setattr(self, f"scatter_{axis.lower()}_slider", slider)
            setattr(self, f"scatter_{axis.lower()}_label", label)
            layout.addLayout(row)
        scatter_btn = QPushButton("Apply Scatter")
        scatter_btn.setObjectName("primary")
        scatter_btn.clicked.connect(lambda: self._emit_operation("scatter", {
            "x_range": self.scatter_x_slider.value() / 2.0,
            "y_range": self.scatter_y_slider.value() / 2.0,
            "z_range": self.scatter_z_slider.value() / 2.0
        }))
        layout.addWidget(scatter_btn)
        swap_btn = QPushButton("Swap Positions (2 entities)")
        swap_btn.clicked.connect(lambda: self._emit_operation("swap", {}))
        layout.addWidget(swap_btn)

    def _emit_operation(self, op_type, params):
        self.operation_requested.emit(op_type, params)


class KatamariEditorVispy(QMainWindow):
    """Main editor window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Katamari Editor - Vispy Edition")
        self.setMinimumSize(1400, 900)
        self.entities = []
        self.file_sequence = []
        self.loaded_maps = []
        self.selected_indices = []
        self.display_mapping = []
        self.item_db = {}
        self.undo_stack = []
        self.max_undo = 50
        self.use_size_scaling = False
        self.select_mode = "CLICK"
        self.theme = Theme("Obsidian", gaudy_mode=True)  # Gaudy mode default
        self.imported_meshes = []  # List of imported mesh objects
        self.entity_models = {}  # Map entity index to model path
        self.text_size = 13  # Default text size
        self.custom_names = {}  # Map entity ID to custom name
        self._load_item_db()
        self._load_custom_names()
        self._setup_ui()
        self._setup_menus()
        self._load_entity_models()
        self.setStyleSheet(self.theme.get_stylesheet())
        self.statusBar().showMessage("Ready - Open a DAT file to begin")

    def _load_item_db(self):
        # Use embedded database by default
        self.item_db = EMBEDDED_ITEM_DB.copy()
        self.statusBar().showMessage(f"Loaded {len(self.item_db)} items from embedded database")

        # Optionally override with external CSV if it exists (for debugging/updates)
        csv_paths = [Path(__file__).parent / "BK_LOC - KDX_MONO.csv", Path(__file__).parent / "ObjectList.csv", Path(__file__).parent / "objectlist.csv"]
        for csv_path in csv_paths:
            if csv_path.exists():
                try:
                    with open(csv_path, encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            key = row.get('ID', row.get('index', '')).lstrip('0') or '0'
                            self.item_db[key] = row
                            try:
                                size_str = row.get('SIZE (mm)', row.get('size', '0'))
                                size_str = re.sub(r'[^\d.]', '', str(size_str))
                                self.item_db[key]['size_val'] = float(size_str) if size_str else 0.0
                            except: self.item_db[key]['size_val'] = 0.0
                    self.statusBar().showMessage(f"Loaded {len(self.item_db)} items from external CSV (overriding embedded)")
                    break
                except Exception as e: print(f"Error loading CSV: {e}")

    def _load_custom_names(self):
        """Load custom entity name overrides from JSON file"""
        custom_names_path = Path(__file__).parent / "entity_name_overrides.json"
        if custom_names_path.exists():
            try:
                with open(custom_names_path, 'r', encoding='utf-8') as f:
                    self.custom_names = json.load(f)
            except Exception as e:
                print(f"Error loading custom names: {e}")
                self.custom_names = {}
        else:
            self.custom_names = {}

    def _save_custom_names(self):
        """Save custom entity name overrides to JSON file"""
        custom_names_path = Path(__file__).parent / "entity_name_overrides.json"
        try:
            with open(custom_names_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_names, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving custom names: {e}")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.entity_list = EntityListWidget()
        self.entity_list.selection_changed.connect(self._on_selection_changed)
        left_layout.addWidget(self.entity_list)

        # --- Selection controls ---
        select_group = QGroupBox("Selection Mode")
        select_layout = QVBoxLayout(select_group)
        self.select_mode_group = QButtonGroup(self)
        
        # Click Mode
        self.rb_click = QRadioButton("Click: Single Select")
        self.rb_click.setChecked(True)
        self.rb_click.toggled.connect(lambda checked: self._set_select_mode("CLICK") if checked else None)
        self.select_mode_group.addButton(self.rb_click)
        select_layout.addWidget(self.rb_click)
        
        # Box Mode
        self.rb_box = QRadioButton("Box: Alt + Drag to select multiple")
        self.rb_box.toggled.connect(lambda checked: self._set_select_mode("BOX") if checked else None)
        self.select_mode_group.addButton(self.rb_box)
        select_layout.addWidget(self.rb_box)

        # Paint Mode
        self.rb_paint = QRadioButton("Paint: Drag to select")
        self.rb_paint.toggled.connect(lambda checked: self._set_select_mode("PAINT") if checked else None)
        self.select_mode_group.addButton(self.rb_paint)
        select_layout.addWidget(self.rb_paint)

        left_layout.addWidget(select_group)
        splitter.addWidget(left_panel)
        
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self.vispy_canvas = VispyCanvas(theme=self.theme)
        self.vispy_canvas.entity_clicked.connect(self._on_entity_clicked)
        self.vispy_canvas.box_select.connect(self._on_box_select)
        self.vispy_canvas.box_select_toggle.connect(self._on_box_select_toggle)
        self.vispy_canvas.waypoint_created.connect(self._on_waypoint_created)
        self.vispy_canvas.trail_completed.connect(self._on_trail_completed)
        self.vispy_canvas.mesh_clicked.connect(self._on_mesh_clicked_in_3d)
        center_layout.addWidget(self.vispy_canvas)
        splitter.addWidget(center_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tabs = QTabWidget()
        
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setAlignment(Qt.AlignTop)
        self.entity_info = EntityInfoPanel()
        self.entity_info.changes_committed.connect(self._on_batch_changes)
        tab1_layout.addWidget(self.entity_info)
        self.position_editor = PositionEditor()
        self.position_editor.position_changed.connect(self._on_position_changed)
        self.position_editor.preview_requested.connect(self._on_position_preview)
        tab1_layout.addWidget(self.position_editor)

        # Visualization controls (moved from View tab)
        viz_group = QGroupBox("Visualization")
        viz_layout = QVBoxLayout(viz_group)
        size_scale_row = QHBoxLayout()
        self.size_scaling_checkbox = QCheckBox("Scale by Size")
        self.size_scaling_checkbox.setToolTip("Scale entity markers by their size value")
        self.size_scaling_checkbox.toggled.connect(self._on_size_scaling_changed)
        size_scale_row.addWidget(self.size_scaling_checkbox)
        viz_layout.addLayout(size_scale_row)
        point_size_row = QHBoxLayout()
        point_size_row.addWidget(QLabel("Point Size:"))
        self.point_size_slider = QSlider(Qt.Horizontal)
        self.point_size_slider.setRange(1, 50)
        self.point_size_slider.setValue(8)
        self.point_size_slider.valueChanged.connect(self._on_point_size_changed)
        point_size_row.addWidget(self.point_size_slider)
        self.point_size_label = QLabel("8")
        point_size_row.addWidget(self.point_size_label)
        viz_layout.addLayout(point_size_row)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Entity Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("70%")
        opacity_row.addWidget(self.opacity_label)
        viz_layout.addLayout(opacity_row)

        # Color mode selector
        color_mode_row = QHBoxLayout()
        color_mode_row.addWidget(QLabel("Color Mode:"))
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Default", "By ID", "By XYZ", "By Size", "By Height", "By Map"])
        self.color_mode_combo.currentTextChanged.connect(self._on_color_mode_changed)
        color_mode_row.addWidget(self.color_mode_combo)
        viz_layout.addLayout(color_mode_row)

        # Hue shift slider
        hue_row = QHBoxLayout()
        hue_row.addWidget(QLabel("Hue Shift:"))
        self.hue_shift_slider = QSlider(Qt.Horizontal)
        self.hue_shift_slider.setRange(0, 360)
        self.hue_shift_slider.setValue(0)
        self.hue_shift_slider.valueChanged.connect(self._on_hue_shift_changed)
        hue_row.addWidget(self.hue_shift_slider)
        self.hue_shift_label = QLabel("0°")
        hue_row.addWidget(self.hue_shift_label)
        viz_layout.addLayout(hue_row)

        tab1_layout.addWidget(viz_group)

        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        save_btn = QPushButton("Save Map")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self.save_map_file)
        actions_layout.addWidget(save_btn)
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo)
        actions_layout.addWidget(undo_btn)
        tab1_layout.addWidget(actions_group)
        tab1_layout.addStretch()
        tabs.addTab(tab1, "Info")
        
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setAlignment(Qt.AlignTop)
        self.quat_viewer = QuaternionViewer()
        self.quat_viewer.rotation_changed.connect(self._on_rotation_changed)
        tab2_layout.addWidget(self.quat_viewer)
        self.position_ops = PositionOperationsPanel()
        self.position_ops.operation_requested.connect(self._on_position_operation)
        tab2_layout.addWidget(self.position_ops)
        self.rotate_panel = RotateAroundAxisPanel()
        self.rotate_panel.operation_requested.connect(self._on_position_operation)
        self.rotate_panel.preview_requested.connect(self._on_rotation_preview)
        tab2_layout.addWidget(self.rotate_panel)
        self.pattern_placer = PatternPlacerPanel()
        self.pattern_placer.pattern_applied.connect(self._apply_pattern)
        tab2_layout.addWidget(self.pattern_placer)
        tab2_layout.addStretch()
        tabs.addTab(tab2, "Edit")
        
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setAlignment(Qt.AlignTop)
        self.size_filter = SizeFilterPanel()
        self.size_filter.filter_changed.connect(self._on_size_filter_changed)
        tab3_layout.addWidget(self.size_filter)
        self.mesh_control = ImportedMeshControlPanel()
        self.mesh_control.mesh_updated.connect(self._on_mesh_updated)
        self.mesh_control.mesh_selection_mode_changed.connect(self._on_mesh_selection_mode_changed)
        self.mesh_control.mesh_highlight_hue_changed.connect(self._on_mesh_highlight_hue_changed)
        self.mesh_control.apply_transform_requested.connect(self._apply_transform_to_mesh)
        self.vispy_canvas.mesh_selection_changed.connect(self.mesh_control.update_selected_count)
        tab3_layout.addWidget(self.mesh_control)
        # Mesh list
        mesh_list_group = QGroupBox("Imported Meshes")
        mesh_list_layout = QVBoxLayout(mesh_list_group)
        self.mesh_list_widget = QListWidget()
        self.mesh_list_widget.setMaximumHeight(150)
        self.mesh_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.mesh_list_widget.itemSelectionChanged.connect(self._on_mesh_list_selection_changed)
        mesh_list_layout.addWidget(self.mesh_list_widget)

        # Mesh list buttons
        mesh_list_btns = QHBoxLayout()
        delete_mesh_btn = QPushButton("Delete Selected")
        delete_mesh_btn.clicked.connect(self._delete_selected_mesh)
        mesh_list_btns.addWidget(delete_mesh_btn)
        toggle_visibility_btn = QPushButton("Toggle Visibility")
        toggle_visibility_btn.clicked.connect(self._toggle_mesh_visibility)
        mesh_list_btns.addWidget(toggle_visibility_btn)
        mesh_list_layout.addLayout(mesh_list_btns)
        
        # Load models button
        load_models_btn = QPushButton("Load/Refresh Entity Model Visuals")
        load_models_btn.setToolTip("Renders assigned OBJ models at entity positions. Can be slow if many models exist.")
        load_models_btn.clicked.connect(self._refresh_entity_model_renders)
        mesh_list_layout.addWidget(load_models_btn)
        
        tab3_layout.addWidget(mesh_list_group)

        self.mesh_generator = MeshGeneratorPanel()
        self.mesh_generator.generate_requested.connect(self._generate_mesh)
        self.mesh_generator.clear_requested.connect(self._clear_mesh)
        tab3_layout.addWidget(self.mesh_generator)
        tab3_layout.addStretch()
        tabs.addTab(tab3, "Tools")

        # View tab removed - visualization controls moved to Info tab

        scroll.setWidget(tabs)
        right_layout.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 850, 350])

    def _setup_menus(self):
        menubar = self.menuBar()
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
        import_mesh_action = QAction("Import Mesh (OBJ)...", self)
        import_mesh_action.triggered.connect(self.import_mesh)
        file_menu.addAction(import_mesh_action)
        file_menu.addSeparator()
        save_action = QAction("Save Map", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_map_file)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
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
        tools_menu = menubar.addMenu("Tools")
        assign_mesh_action = QAction("Assign Mesh to Selected Entity...", self)
        assign_mesh_action.triggered.connect(self._assign_mesh_to_entity)
        tools_menu.addAction(assign_mesh_action)
        view_entity_models_action = QAction("View Entity Model Assignments...", self)
        view_entity_models_action.triggered.connect(self._view_entity_models)
        tools_menu.addAction(view_entity_models_action)
        # Controllers menu
        controllers_menu = menubar.addMenu("Controllers")
        add_controller = QAction("Add Controller", self)
        add_controller.triggered.connect(self._add_controller)
        controllers_menu.addAction(add_controller)
        controllers_menu.addSeparator()
        self.controller_actions = []
        # Don't populate on startup - wait for user to click "Add Controller"

        view_menu = menubar.addMenu("View")
        zoom_fit = QAction("Zoom to Fit", self)
        zoom_fit.setShortcut("Ctrl+0")
        zoom_fit.triggered.connect(self._zoom_to_fit)
        view_menu.addAction(zoom_fit)
        view_menu.addSeparator()
        text_size_menu = view_menu.addMenu("Text Size")
        for size_name, size_value in [("Small", 22), ("Medium", 26), ("Large", 30), ("Extra Large", 34)]:
            size_action = QAction(size_name, self)
            size_action.triggered.connect(lambda checked, s=size_value: self._change_text_size(s))
            text_size_menu.addAction(size_action)
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        gaudy_action = QAction("Gaudy Mode", self)
        gaudy_action.setCheckable(True)
        gaudy_action.setChecked(True)  # Gaudy mode default
        gaudy_action.triggered.connect(self._toggle_gaudy_mode)
        theme_menu.addAction(gaudy_action)
        theme_menu.addSeparator()
        for theme_name in THEMES_MINIMALIST.keys():
            theme_action = QAction(theme_name, self)
            theme_action.triggered.connect(lambda checked, name=theme_name: self._change_theme(name))
            theme_menu.addAction(theme_action)
        view_menu.addSeparator()
        self.size_by_csv_action = QAction("Size by CSV", self)
        self.size_by_csv_action.setCheckable(True)
        self.size_by_csv_action.setChecked(False)
        self.size_by_csv_action.triggered.connect(self._on_size_scaling_changed_menu)
        view_menu.addAction(self.size_by_csv_action)

    def _change_text_size(self, size):
        app = QApplication.instance()
        font = app.font()
        font.setPointSize(size)
        app.setFont(font)
        self.statusBar().showMessage(f"Text size changed to {size}pt")

    def _on_size_scaling_changed_menu(self, checked):
        self.use_size_scaling = checked
        # Sync checkbox
        self.size_scaling_checkbox.blockSignals(True)
        self.size_scaling_checkbox.setChecked(checked)
        self.size_scaling_checkbox.blockSignals(False)
        self._refresh_3d_view()
        self.statusBar().showMessage(f"Size by CSV: {'On' if checked else 'Off'}")

    def _load_csv_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load CSV Database", "", "CSV Files (*.csv);;All Files (*)")
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.item_db = {}
                for row in reader:
                    key = row.get('ID', row.get('index', '')).lstrip('0') or '0'
                    self.item_db[key] = row
                    try:
                        size_str = row.get('SIZE (mm)', row.get('size', '0'))
                        size_str = re.sub(r'[^\d.]', '', str(size_str))
                        self.item_db[key]['size_val'] = float(size_str) if size_str else 0.0
                    except: self.item_db[key]['size_val'] = 0.0
            self.entity_list.set_entities(self.entities, self.item_db)
            self._refresh_3d_view()
            self.statusBar().showMessage(f"Loaded {len(self.item_db)} items from {os.path.basename(filepath)}")
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")

    def _set_select_mode(self, mode):
        self.select_mode = mode
        self.vispy_canvas.select_mode = mode

    def _on_size_scaling_changed(self, state):
        self.use_size_scaling = state == Qt.Checked
        # Sync menu action
        self.size_by_csv_action.blockSignals(True)
        self.size_by_csv_action.setChecked(self.use_size_scaling)
        self.size_by_csv_action.blockSignals(False)
        self._refresh_3d_view()

    def _on_entity_clicked(self, index, shift, ctrl):
        if ctrl:
            # Invert selection for this specific index
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.append(index)
        elif shift:
            # Standard additive selection
            if index not in self.selected_indices:
                self.selected_indices.append(index)
        else:
            # Standard single selection
            self.selected_indices = [index]

        # Highlight and scroll to selected entity in the list
        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _on_box_select(self, indices):
        from PyQt5.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier or modifiers & Qt.ControlModifier:
            for idx in indices:
                if idx not in self.selected_indices: self.selected_indices.append(idx)
        else:
            self.selected_indices = list(indices)
        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _on_waypoint_created(self, x, y, z):
        """Handle waypoint creation from Alt+Click on canvas"""
        self.pattern_placer.add_waypoint(x, y, z)

    def _on_selection_changed(self, indices):
        self.selected_indices = indices
        self._update_selection_ui()

    def _update_selection_ui(self):
        self.vispy_canvas.update_selection(self.selected_indices)
        self.position_editor.update_for_selection(self.entities, self.selected_indices)
        self.pattern_placer.update_count(len(self.selected_indices))
        if self.selected_indices:
            ent = self.entities[self.selected_indices[-1]]
            self.entity_info.update_info(ent, self.item_db, self.entities)
            self.quat_viewer.update_quaternion(ent['rx'], ent['ry'], ent['rz'], ent['rw'])
            db_key = ent['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            name = info.get('obj_en', f"Entity {ent['id']}")
            self.statusBar().showMessage(f"Selected: {name} | ID: {ent['id']} | Pos: ({ent['x']:.1f}, {ent['y']:.1f}, {ent['z']:.1f})")
        else:
            self.entity_info.update_info(None, self.item_db, self.entities)
            self.quat_viewer.update_quaternion(0, 0, 0, 1)

    def _select_all(self):
        self.selected_indices = list(range(len(self.entities)))
        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _deselect_all(self):
        self.selected_indices = []
        self.entity_list.set_selection([])
        self._update_selection_ui()

    def _change_theme(self, theme_name):
        self.theme.update_theme(theme_name, self.theme.gaudy_mode)
        self.setStyleSheet(self.theme.get_stylesheet())
        self.vispy_canvas.canvas.bgcolor = self.theme.GRAPH_BG
        self.vispy_canvas.canvas.update()
        self.statusBar().showMessage(f"Theme changed to: {theme_name}")

    def _toggle_gaudy_mode(self, checked):
        self.theme.update_theme(self.theme.theme_name, gaudy_mode=checked)
        self.setStyleSheet(self.theme.get_stylesheet())
        self.vispy_canvas.canvas.bgcolor = self.theme.GRAPH_BG
        self.vispy_canvas.canvas.update()
        mode_text = "Gaudy" if checked else "Minimalist"
        self.statusBar().showMessage(f"Theme mode changed to: {mode_text}")

    def _change_text_size(self, size):
        """Change the global text size for all UI elements"""
        self.text_size = size
        # Update theme to use new font size
        old_stylesheet = self.theme.get_stylesheet()
        # Replace font-size entries in stylesheet (doubled base values)
        new_stylesheet = old_stylesheet.replace("font-size: 26px", f"font-size: {size}px")
        new_stylesheet = new_stylesheet.replace("font-size: 28px", f"font-size: {size+2}px")
        new_stylesheet = new_stylesheet.replace("font-size: 24px", f"font-size: {size-2}px")
        new_stylesheet = new_stylesheet.replace("font-size: 22px", f"font-size: {size-4}px")
        new_stylesheet = new_stylesheet.replace("font-size: 32px", f"font-size: {size+6}px")
        self.setStyleSheet(new_stylesheet)
        self.statusBar().showMessage(f"Text size changed to: {size}pt")

    def _on_position_changed(self):
        if not self.selected_indices: return
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

    def _on_position_preview(self, x, y, z, offset_mode):
        if not self.selected_indices: return
        self.vispy_canvas.show_position_preview(self.selected_indices, x, y, z, offset_mode)

    def _on_rotation_changed(self, x, y, z, w):
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
        if not self.selected_indices:
            QMessageBox.warning(self, "Selection", "Select at least one entity to edit.")
            return
        self._save_undo_state("Batch Edit")

        # Map of entity key to XML tag name
        tag_map = {
            'index': 'index', 'atk': 'attack_type', 'mov': 'move_type', 'esc': 'escape_type',
            'spd': 'speed', 'pth': 'path_id', 'scale': 'scale', 'plus_type': 'plus_type',
            'parent_type': 'parent_type', 'clash_type': 'clash_type',
            'script_type': 'script_type', 'script_id': 'script_id', 'random_type': 'random_type',
            'random_id': 'random_id', 'random_put_range': 'random_put_range', 'comment_type': 'comment_type',
            'comment_id': 'comment_id', 'name_type': 'name_type', 'anim_type': 'anim_type',
            'anim_motion_id': 'anim_motion_id', 'change_type': 'change_type', 'change_mono_id': 'change_mono_id',
            'spmove_type': 'spmove_type', 'spmove_rise_height': 'spmove_rise_height',
            'spmove_appear_second': 'spmove_appear_second', 'plus_timing': 'plus_timing',
            'start_type': 'start_type', 'move_start_size': 'move_start_size', 'move_end_size': 'move_end_size'
        }

        def safe_rep(tag, new_content, block):
            s, e = f"<{tag}>", f"</{tag}>"
            si = block.find(s) + len(s)
            ei = block.find(e)
            if si == -1 or ei == -1:
                return block
            orig_len = ei - si
            final_str = new_content[:orig_len].ljust(orig_len)
            return block[:si] + final_str + block[ei:]

        for idx in self.selected_indices:
            ent = self.entities[idx]
            raw = ent['raw']
            for key, value in changes.items():
                if key == 'custom_name':
                    # Handle custom name specially - save to both entity and global dict
                    ent['custom_name'] = value
                    db_key = ent['id'].lstrip('0') or '0'
                    if value:  # Save if not empty
                        self.custom_names[db_key] = value
                    elif db_key in self.custom_names:  # Remove if empty
                        del self.custom_names[db_key]
                elif key in ent:
                    ent[key] = value
                    # Update the raw XML data
                    if key in tag_map:
                        xml_tag = tag_map[key]
                        raw = safe_rep(xml_tag, f" {value} ", raw)
            ent['raw'] = raw

        # Save custom names to file
        if 'custom_name' in changes:
            self._save_custom_names()

        self._update_selection_ui()
        self.statusBar().showMessage(f"Updated {len(self.selected_indices)} entities")

    def _on_size_filter_changed(self, min_size, max_size, enabled):
        if enabled: self.entity_list.apply_size_filter(min_size, max_size, self.item_db)
        else: self.entity_list.set_entities(self.entities, self.item_db)

    def _zoom_to_fit(self):
        self._refresh_3d_view(auto_fit=True)

    def _populate_controller_menu(self, menu):
        """Populate the controller menu with detected gamepads"""
        if not PYGAME_AVAILABLE:
            no_pygame = QAction("pygame not installed", self)
            no_pygame.setEnabled(False)
            menu.addAction(no_pygame)
            info_action = QAction("Install: pip install pygame", self)
            info_action.setEnabled(False)
            menu.addAction(info_action)
            return

        try:
            pygame.init()
            pygame.joystick.init()

            count = pygame.joystick.get_count()
            if count == 0:
                no_controller = QAction("No controllers detected", self)
                no_controller.setEnabled(False)
                menu.addAction(no_controller)
            else:
                for i in range(count):
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    name = joystick.get_name()
                    action = QAction(f"Controller {i}: {name}", self)
                    action.setCheckable(True)
                    action.setChecked(i == 0)  # First controller is default
                    action.triggered.connect(lambda checked, idx=i: self._select_controller(idx))
                    menu.addAction(action)
                    self.controller_actions.append(action)
                    joystick.quit()
        except ImportError:
            no_pygame = QAction("pygame not installed", self)
            no_pygame.setEnabled(False)
            menu.addAction(no_pygame)
            info_action = QAction("Install: pip install pygame", self)
            info_action.setEnabled(False)
            menu.addAction(info_action)
        except Exception as e:
            error_action = QAction(f"Error: {e}", self)
            error_action.setEnabled(False)
            menu.addAction(error_action)

    def _add_controller(self):
        """Add/enable controller support"""
        if not PYGAME_AVAILABLE:
            QMessageBox.warning(self, "pygame Not Available",
                "pygame is not installed. Controller support requires pygame.\n\n"
                "Install it with: pip install pygame")
            return

        # Initialize gamepad in canvas
        if hasattr(self, 'vispy_canvas'):
            success = self.vispy_canvas._init_gamepad()
            if success:
                self.statusBar().showMessage("Controller enabled successfully", 3000)
            else:
                QMessageBox.information(self, "No Controller",
                    "No controller detected. Please connect a controller and try again.")
        else:
            QMessageBox.warning(self, "Error", "Canvas not initialized")

    def _select_controller(self, idx):
        """Select a specific controller"""
        if not PYGAME_AVAILABLE:
            QMessageBox.warning(self, "pygame Not Available",
                "pygame is not installed. Install it with:\npip install pygame")
            return

        try:
            # Uncheck all other controller actions
            for action in self.controller_actions:
                action.setChecked(False)
            # Check the selected one
            self.controller_actions[idx].setChecked(True)

            # Reinitialize gamepad with selected controller
            if hasattr(self, 'vispy_canvas'):
                if self.vispy_canvas.gamepad:
                    self.vispy_canvas.gamepad.quit()
                self.vispy_canvas.gamepad = pygame.joystick.Joystick(idx)
                self.vispy_canvas.gamepad.init()
                self.statusBar().showMessage(f"Controller {idx} selected: {self.vispy_canvas.gamepad.get_name()}", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Controller Error", f"Failed to select controller {idx}: {e}")

    def _refresh_3d_view(self, auto_fit=False):
        if not self.entities: return
        sizes = None
        if self.use_size_scaling:
            sizes = []
            for ent in self.entities:
                # Use csv_size_mm field if available (from Phase 1 enrichment)
                size_mm = ent.get('csv_size_mm', 0.0)
                if size_mm > 0:
                    sizes.append(size_mm)
                else:
                    # Fallback to item_db lookup
                    db_key = ent['id'].lstrip('0') or '0'
                    if ent['id'].lstrip('0') in ['3226', '3227']:
                        sizes.append(200)
                    else:
                        info = self.item_db.get(db_key, {})
                        sizes.append(info.get('size_val', 0))
        self.vispy_canvas.set_entities(
            self.entities, self.selected_indices, sizes=sizes,
            use_size_scaling=self.use_size_scaling, auto_fit_camera=auto_fit,
            base_point_size=self.point_size_slider.value()
        )
        
        # Sync entity models if loaded
        if hasattr(self.vispy_canvas, 'entity_model_visuals') and self.vispy_canvas.entity_model_visuals:
            self._refresh_entity_model_renders()

        # Apply current color mode after setting entities
        if hasattr(self, 'color_mode_combo'):
            mode = self.color_mode_combo.currentText()
            self._on_color_mode_changed(mode)

    def _on_color_mode_changed(self, mode):
        if not self.entities: return
        positions = self.vispy_canvas.entity_positions
        if positions is None: return
        n = len(self.entities)
        colors = np.zeros((n, 4), dtype=np.float32)
        opacity = self.opacity_slider.value() / 100.0
        hue_shift = self.hue_shift_slider.value()

        if mode == "Default":
            colors[:] = [0.3, 0.7, 0.9, opacity]
        elif mode == "By ID":
            for i, ent in enumerate(self.entities):
                id_hash = (hash(ent['id']) + hue_shift) % 360
                h = id_hash / 60.0
                c = 0.8
                x = c * (1 - abs(h % 2 - 1))
                if h < 1: r, g, b = c, x, 0
                elif h < 2: r, g, b = x, c, 0
                elif h < 3: r, g, b = 0, c, x
                elif h < 4: r, g, b = 0, x, c
                elif h < 5: r, g, b = x, 0, c
                else: r, g, b = c, 0, x
                colors[i] = [r, g, b, opacity]
        elif mode == "By XYZ":
            # Color by XYZ coordinates based on distance from center
            positions_3d = np.array([[e['x'], e['y'], e['z']] for e in self.entities])
            center = positions_3d.mean(axis=0)
            distances_from_center = np.linalg.norm(positions_3d - center, axis=1)

            # Normalize distances
            if distances_from_center.max() > distances_from_center.min():
                normalized_dist = (distances_from_center - distances_from_center.min()) / (distances_from_center.max() - distances_from_center.min())
            else:
                normalized_dist = np.zeros(n)

            # Apply hue shift
            for i, (ent, dist_val) in enumerate(zip(self.entities, normalized_dist)):
                hue = (dist_val * 360 + hue_shift) % 360
                h = hue / 60.0
                c = 0.8
                x = c * (1 - abs(h % 2 - 1))
                if h < 1: r, g, b = c, x, 0
                elif h < 2: r, g, b = x, c, 0
                elif h < 3: r, g, b = 0, c, x
                elif h < 4: r, g, b = 0, x, c
                elif h < 5: r, g, b = x, 0, c
                else: r, g, b = c, 0, x
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
            else: normalized = np.zeros(n)
            for i, val in enumerate(normalized):
                hue = (val * 240 + hue_shift) % 360  # Apply hue shift
                h = hue / 60.0
                c = 0.8
                x = c * (1 - abs(h % 2 - 1))
                if h < 1: r, g, b = c, x, 0
                elif h < 2: r, g, b = x, c, 0
                elif h < 3: r, g, b = 0, c, x
                elif h < 4: r, g, b = 0, x, c
                elif h < 5: r, g, b = x, 0, c
                else: r, g, b = c, 0, x
                colors[i] = [r, g, b, opacity]
        elif mode == "By Height":
            heights = np.array([e['y'] for e in self.entities])
            if heights.max() > heights.min():
                normalized = (heights - heights.min()) / (heights.max() - heights.min())
            else: normalized = np.zeros(n)
            for i, val in enumerate(normalized):
                hue = (val * 240 + hue_shift) % 360  # Apply hue shift
                h = hue / 60.0
                c = 0.8
                x = c * (1 - abs(h % 2 - 1))
                if h < 1: r, g, b = c, x, 0
                elif h < 2: r, g, b = x, c, 0
                elif h < 3: r, g, b = 0, c, x
                elif h < 4: r, g, b = 0, x, c
                elif h < 5: r, g, b = x, 0, c
                else: r, g, b = c, 0, x
                colors[i] = [r, g, b, opacity]
        elif mode == "By Map":
            map_colors = [[0.3, 0.7, 0.9, opacity], [0.9, 0.5, 0.3, opacity], [0.4, 0.9, 0.4, opacity], [0.9, 0.3, 0.6, opacity], [0.7, 0.7, 0.3, opacity]]
            for i, ent in enumerate(self.entities):
                map_idx = ent.get('map_index', 0) % len(map_colors)
                colors[i] = map_colors[map_idx]

        # Apply colors and update canvas
        sizes = None
        if hasattr(self, 'use_size_scaling') and self.use_size_scaling:
            sizes = []
            for ent in self.entities:
                db_key = ent['id'].lstrip('0') or '0'
                if ent['id'].lstrip('0') in ['3226', '3227']:
                    sizes.append(200)
                else:
                    info = self.item_db.get(db_key, {})
                    sizes.append(max(1, min(50, info.get('size_val', 0) / 10000)))

        if sizes:
            self.vispy_canvas.scatter.set_data(pos=positions, face_color=colors, edge_color='white', edge_width=0.5, size=sizes)
        else:
            self.vispy_canvas.scatter.set_data(pos=positions, face_color=colors, edge_color='white', edge_width=0.5, size=self.point_size_slider.value())

        self.vispy_canvas.canvas.update()

    def _on_point_size_changed(self, size):
        self.point_size_label.setText(str(size))
        self._refresh_3d_view()

    def _on_opacity_changed(self, value):
        self.opacity_label.setText(f"{value}%")
        mode = self.color_mode_combo.currentText() if hasattr(self, 'color_mode_combo') else "Default"
        self._on_color_mode_changed(mode)

    def _on_hue_shift_changed(self, value):
        self.hue_shift_label.setText(f"{value}°")
        mode = self.color_mode_combo.currentText() if hasattr(self, 'color_mode_combo') else "Default"
        self._on_color_mode_changed(mode)

    def _generate_mesh(self, params):
        try:
            from scipy.interpolate import griddata
            from scipy.spatial import Delaunay
        except ImportError:
            QMessageBox.critical(self, "Error", "scipy is required for mesh generation. Install with: pip install scipy")
            return
        if not self.entities:
            QMessageBox.warning(self, "Error", "No entities loaded.")
            return
        if params['selected_only']:
            if not self.selected_indices:
                QMessageBox.warning(self, "Error", "No entities selected.")
                return
            indices = self.selected_indices.copy()
        else: indices = list(range(len(self.entities)))
        if params['exclude_large']:
            filtered = []
            for i in indices:
                db_key = self.entities[i]['id'].lstrip('0') or '0'
                size = self.item_db.get(db_key, {}).get('size_val', 0)
                if size <= 9000000: filtered.append(i)
            indices = filtered
        if len(indices) < 4:
            QMessageBox.warning(self, "Error", "Need at least 4 entities to generate mesh.")
            return
        points = np.array([[self.entities[i]['x'], self.entities[i]['y'], self.entities[i]['z']] for i in indices])
        if params['averaging'] > 0.5: points = self._average_points(points, params['averaging'])
        if len(points) < 4:
            QMessageBox.warning(self, "Error", "Too few points after averaging.")
            return
        resolution = params['resolution']
        alpha = params['alpha']
        try:
            if params['floor_priority']:
                x = points[:, 0]
                y = points[:, 1]
                z = points[:, 2]
                xi = np.linspace(x.min(), x.max(), resolution)
                zi = np.linspace(z.min(), z.max(), resolution)
                Xi, Zi = np.meshgrid(xi, zi)
                Yi = griddata((x, z), y, (Xi, Zi), method='linear', fill_value=np.nan)
                vertices = []
                faces = []
                for i in range(resolution):
                    for j in range(resolution):
                        if not np.isnan(Yi[i, j]): vertices.append([-Xi[i, j], Zi[i, j], Yi[i, j]])
                vertices = np.array(vertices, dtype=np.float32)
                valid_idx = {}
                idx = 0
                for i in range(resolution):
                    for j in range(resolution):
                        if not np.isnan(Yi[i, j]):
                            valid_idx[(i, j)] = idx
                            idx += 1
                for i in range(resolution - 1):
                    for j in range(resolution - 1):
                        if (i, j) in valid_idx and (i+1, j) in valid_idx and (i, j+1) in valid_idx and (i+1, j+1) in valid_idx:
                            v00 = valid_idx[(i, j)]
                            v10 = valid_idx[(i+1, j)]
                            v01 = valid_idx[(i, j+1)]
                            v11 = valid_idx[(i+1, j+1)]
                            faces.append([v00, v10, v11])
                            faces.append([v00, v11, v01])
                faces = np.array(faces, dtype=np.uint32)
            else:
                tri = Delaunay(points[:, [0, 2]])
                vertices = np.array([[-p[0], p[2], p[1]] for p in points], dtype=np.float32)
                faces = tri.simplices.astype(np.uint32)
            self.vispy_canvas.set_mesh(vertices, faces, color=(0.5, 0.8, 0.5, alpha))
            if params.get('snap_to_mesh', False) and self.selected_indices:
                self._snap_entities_to_mesh(vertices, faces)
                self.statusBar().showMessage(f"Mesh generated from {len(points)} points, {len(self.selected_indices)} entities snapped")
            else: self.statusBar().showMessage(f"Mesh generated from {len(points)} points")
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to generate mesh: {e}")

    def _snap_entities_to_mesh(self, vertices, faces):
        if not self.selected_indices or vertices is None or faces is None: return
        self._save_undo_state()
        world_vertices = np.array([[-v[0], v[2], v[1]] for v in vertices])
        for idx in self.selected_indices:
            entity = self.entities[idx]
            entity_pos = np.array([entity['x'], entity['y'], entity['z']])
            distances = np.linalg.norm(world_vertices - entity_pos, axis=1)
            nearest_idx = np.argmin(distances)
            nearest_vertex = world_vertices[nearest_idx]

            # Get entity size from database to calculate radius offset
            db_key = entity['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key, {})
            size_mm = info.get('size_val', 0)
            # Convert size in mm to game units (radius = diameter/2)
            # Assuming 1 game unit = 1mm for simplicity
            radius = size_mm / 2.0 if size_mm > 0 else 0

            # Calculate direction from mesh to entity (for offset)
            direction = entity_pos - nearest_vertex
            if np.linalg.norm(direction) > 0.001:
                direction = direction / np.linalg.norm(direction)
            else:
                direction = np.array([0, 0, 1])  # Default up if coincident

            # Apply position with radius offset
            offset_pos = nearest_vertex + direction * radius
            entity['x'] = float(offset_pos[0])
            entity['y'] = float(offset_pos[1])
            entity['z'] = float(offset_pos[2])

        self._refresh_3d_view()
        self._update_selection_ui()

    def _average_points(self, points, cell_size):
        if len(points) == 0: return points
        x_min, y_min, z_min = points.min(axis=0)
        cells = {}
        for p in points:
            cx = int((p[0] - x_min) / cell_size)
            cy = int((p[1] - y_min) / cell_size)
            cz = int((p[2] - z_min) / cell_size)
            key = (cx, cy, cz)
            if key not in cells: cells[key] = []
            cells[key].append(p)
        averaged = []
        for cell_points in cells.values():
            avg_point = np.mean(cell_points, axis=0)
            averaged.append(avg_point)
        return np.array(averaged)

    def _clear_mesh(self):
        self.vispy_canvas.clear_mesh()
        self.statusBar().showMessage("Mesh cleared")

    def _apply_pattern(self, pattern_type, params):
        # Handle trail mode toggle
        if pattern_type == "trail_mode":
            enabled = params.get('enabled', False)
            self.vispy_canvas.set_trail_mode(enabled)
            if enabled:
                self.statusBar().showMessage("Trail drawing mode enabled - drag in 3D view to draw trail")
            else:
                self.statusBar().showMessage("Trail drawing mode disabled")
            return

        # Handle position to waypoints
        if pattern_type == "position_to_waypoints":
            waypoints = self.pattern_placer.waypoints
            if not waypoints:
                QMessageBox.warning(self, "No Waypoints", "Create waypoints first using 'Place Entities'")
                return
            if not self.selected_indices:
                QMessageBox.warning(self, "Selection", "Select entities to position at waypoints")
                return
            self._save_undo_state("Position to Waypoints")
            # Distribute selected entities to waypoint positions
            for i, idx in enumerate(self.selected_indices):
                wp_idx = i % len(waypoints)  # Wrap around if more entities than waypoints
                wp = waypoints[wp_idx]
                self.entities[idx]['x'] = wp[0]
                self.entities[idx]['y'] = wp[1]
                self.entities[idx]['z'] = wp[2]
                self._sync_entity_raw(self.entities[idx])
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage(f"Positioned {len(self.selected_indices)} entities to {len(waypoints)} waypoints")
            return

        # Handle add waypoint (from selected entity average)
        if pattern_type == "add_waypoint":
            if not self.selected_indices:
                QMessageBox.warning(self, "Selection", "Select at least one entity to use as waypoint.")
                return
            x_avg = sum(self.entities[i]['x'] for i in self.selected_indices) / len(self.selected_indices)
            y_avg = sum(self.entities[i]['y'] for i in self.selected_indices) / len(self.selected_indices)
            z_avg = sum(self.entities[i]['z'] for i in self.selected_indices) / len(self.selected_indices)
            self.pattern_placer.add_waypoint(x_avg, y_avg, z_avg)
            return

        # Standard pattern application requires selection
        if not self.selected_indices:
            QMessageBox.warning(self, "Selection", "Select entities to arrange in pattern.")
            return
        count = len(self.selected_indices)
        if pattern_type == "Path" and len(params['waypoints']) < 2:
            QMessageBox.warning(self, "Waypoints", "Path mode requires at least 2 waypoints.")
            return
        self._save_undo_state(f"Apply {pattern_type} Pattern")
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
            total_length = 0
            for i in range(len(waypoints) - 1):
                dx = waypoints[i+1][0] - waypoints[i][0]
                dy = waypoints[i+1][1] - waypoints[i][1]
                dz = waypoints[i+1][2] - waypoints[i][2]
                total_length += math.sqrt(dx*dx + dy*dy + dz*dz)
            for idx, entity_idx in enumerate(self.selected_indices):
                t = idx / max(1, count - 1)
                target_dist = t * total_length
                current_dist = 0
                for i in range(len(waypoints) - 1):
                    dx = waypoints[i+1][0] - waypoints[i][0]
                    dy = waypoints[i+1][1] - waypoints[i][1]
                    dz = waypoints[i+1][2] - waypoints[i][2]
                    seg_len = math.sqrt(dx*dx + dy*dy + dz*dz)
                    if current_dist + seg_len >= target_dist:
                        seg_t = (target_dist - current_dist) / seg_len if seg_len > 0 else 0
                        self.entities[entity_idx]['x'] = waypoints[i][0] + dx * seg_t
                        self.entities[entity_idx]['y'] = waypoints[i][1] + dy * seg_t
                        self.entities[entity_idx]['z'] = waypoints[i][2] + dz * seg_t
                        break
                    current_dist += seg_len
                else:
                    self.entities[entity_idx]['x'] = waypoints[-1][0]
                    self.entities[entity_idx]['y'] = waypoints[-1][1]
                    self.entities[entity_idx]['z'] = waypoints[-1][2]
                self._sync_entity_raw(self.entities[entity_idx])
        self._refresh_3d_view()
        self._update_selection_ui()
        self.statusBar().showMessage(f"Applied {pattern_type} pattern to {count} entities")

    def _on_trail_completed(self, trail_points):
        """Handle trail drawing completion"""
        if len(trail_points) < 2:
            return

        # Add all trail points as waypoints
        for point in trail_points:
            self.pattern_placer.add_waypoint(point[0], point[1], point[2])

        self.statusBar().showMessage(f"Added {len(trail_points)} waypoints from trail")

        # Auto-disable trail mode and clear the visual
        self.pattern_placer.trail_btn.setChecked(False)
        self.vispy_canvas.set_trail_mode(False)

    def _on_box_select_toggle(self, indices):
        """Handle Ctrl+box selection to toggle entities"""
        current_set = set(self.selected_indices)
        for idx in indices:
            if idx in current_set:
                current_set.remove(idx)
            else:
                current_set.add(idx)
        self.selected_indices = sorted(list(current_set))
        self.entity_list.set_selection(self.selected_indices)
        self._update_selection_ui()

    def _on_rotation_preview(self, op_type, params):
        """Show rotation preview in 3D view"""
        if op_type == "rotate_preview":
            if not self.selected_indices:
                self.vispy_canvas.clear_rotation_preview()
                return

            axis = params.get('axis')
            angle_deg = params.get('angle', 0)

            if not axis or angle_deg == 0:
                self.vispy_canvas.clear_rotation_preview()
                return

            # Calculate preview positions
            angle_rad = math.radians(angle_deg)
            positions = np.array([[self.entities[i]['x'], self.entities[i]['y'], self.entities[i]['z']]
                                  for i in self.selected_indices])
            centroid = positions.mean(axis=0)

            # Create rotation matrix
            if axis == 'x':
                rot_matrix = np.array([[1, 0, 0],
                                      [0, math.cos(angle_rad), -math.sin(angle_rad)],
                                      [0, math.sin(angle_rad), math.cos(angle_rad)]])
            elif axis == 'y':
                rot_matrix = np.array([[math.cos(angle_rad), 0, math.sin(angle_rad)],
                                      [0, 1, 0],
                                      [-math.sin(angle_rad), 0, math.cos(angle_rad)]])
            else:  # z
                rot_matrix = np.array([[math.cos(angle_rad), -math.sin(angle_rad), 0],
                                      [math.sin(angle_rad), math.cos(angle_rad), 0],
                                      [0, 0, 1]])

            # Rotate positions
            preview_positions = []
            for pos in positions:
                relative = pos - centroid
                rotated = rot_matrix.dot(relative)
                new_pos = centroid + rotated
                preview_positions.append(new_pos)

            # Show preview in canvas
            self.vispy_canvas.show_rotation_preview(np.array(preview_positions))

    def _on_position_operation(self, op_type, params):
        import random
        if op_type == "average":
            if len(self.selected_indices) < 2:
                QMessageBox.warning(self, "Selection", "Select at least 2 entities to average.")
                return
            axis = params['axis']
            self._save_undo_state(f"Average {axis.upper()}")
            axes = ['x', 'y', 'z'] if axis == "all" else [axis]
            for ax in axes:
                positions = [self.entities[i][ax] for i in self.selected_indices]
                avg = sum(positions) / len(positions)
                for idx in self.selected_indices:
                    self.entities[idx][ax] = avg
                    self._sync_entity_raw(self.entities[idx])
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage(f"Averaged {axis.upper()} positions for {len(self.selected_indices)} entities")
        elif op_type == "spread":
            if len(self.selected_indices) < 2:
                QMessageBox.warning(self, "Selection", "Select at least 2 entities to spread.")
                return
            axis = params['axis']
            factor = params['factor']
            self._save_undo_state(f"Spread {axis.upper()} ({factor}x)")
            axes = ['x', 'y', 'z'] if axis == "all" else [axis]
            for ax in axes:
                positions = [self.entities[i][ax] for i in self.selected_indices]
                centroid = sum(positions) / len(positions)
                for idx in self.selected_indices:
                    offset = self.entities[idx][ax] - centroid
                    self.entities[idx][ax] = centroid + (offset * factor)
                    self._sync_entity_raw(self.entities[idx])
            self._refresh_3d_view()
            self._update_selection_ui()
            action = "Spread" if factor > 1.0 else "Compressed"
            self.statusBar().showMessage(f"{action} {len(self.selected_indices)} entities along {axis.upper()} (factor: {factor})")
        elif op_type == "rotate":
            if len(self.selected_indices) < 2:
                QMessageBox.warning(self, "Selection", "Select at least 2 entities to rotate.")
                return
            axis = params['axis']
            angle_deg = params['angle']
            self._save_undo_state(f"Rotate {axis.upper()} ({angle_deg}°)")
            angle_rad = math.radians(angle_deg)
            positions = np.array([[self.entities[i]['x'], self.entities[i]['y'], self.entities[i]['z']] for i in self.selected_indices])
            centroid = positions.mean(axis=0)
            if axis == 'x': rot_matrix = np.array([[1, 0, 0], [0, math.cos(angle_rad), -math.sin(angle_rad)], [0, math.sin(angle_rad), math.cos(angle_rad)]])
            elif axis == 'y': rot_matrix = np.array([[math.cos(angle_rad), 0, math.sin(angle_rad)], [0, 1, 0], [-math.sin(angle_rad), 0, math.cos(angle_rad)]])
            else: rot_matrix = np.array([[math.cos(angle_rad), -math.sin(angle_rad), 0], [math.sin(angle_rad), math.cos(angle_rad), 0], [0, 0, 1]])
            for idx in self.selected_indices:
                pos = np.array([self.entities[idx]['x'], self.entities[idx]['y'], self.entities[idx]['z']])
                relative = pos - centroid
                rotated = rot_matrix.dot(relative)
                new_pos = centroid + rotated
                self.entities[idx]['x'] = new_pos[0]
                self.entities[idx]['y'] = new_pos[1]
                self.entities[idx]['z'] = new_pos[2]
                self._sync_entity_raw(self.entities[idx])
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage(f"Rotated {len(self.selected_indices)} entities {angle_deg}° around {axis.upper()}-axis")
        elif op_type == "scatter":
            if not self.selected_indices:
                QMessageBox.warning(self, "Selection", "Select entities to scatter.")
                return
            x_range = params['x_range']
            y_range = params['y_range']
            z_range = params['z_range']
            self._save_undo_state(f"Scatter Positions (X:±{x_range}, Y:±{y_range}, Z:±{z_range})")
            for idx in self.selected_indices:
                if x_range > 0: self.entities[idx]['x'] += random.uniform(-x_range, x_range)
                if y_range > 0: self.entities[idx]['y'] += random.uniform(-y_range, y_range)
                if z_range > 0: self.entities[idx]['z'] += random.uniform(-z_range, z_range)
                self._sync_entity_raw(self.entities[idx])
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage(f"Scattered {len(self.selected_indices)} entities with ranges X:±{x_range}, Y:±{y_range}, Z:±{z_range}")
        elif op_type == "snap_waypoint":
            if not self.selected_indices:
                QMessageBox.warning(self, "Selection", "Select entities to snap.")
                return
            waypoints = self.pattern_placer.waypoints
            if not waypoints:
                QMessageBox.warning(self, "No Waypoints", "Create waypoints first")
                return
            axis = params.get('axis', 'floor')
            self._save_undo_state(f"Snap to Waypoint ({axis})")
            for idx in self.selected_indices:
                entity = self.entities[idx]
                # Find nearest waypoint
                entity_pos = np.array([entity['x'], entity['y'], entity['z']])
                distances = [np.linalg.norm(entity_pos - np.array(wp)) for wp in waypoints]
                nearest_wp = waypoints[np.argmin(distances)]

                if axis == 'floor':
                    entity['x'] = nearest_wp[0]
                    entity['z'] = nearest_wp[2]
                    # Keep entity['y']
                elif axis == 'x':
                    entity['x'] = nearest_wp[0]
                elif axis == 'z':
                    entity['z'] = nearest_wp[2]
                self._sync_entity_raw(entity)
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage(f"Snapped {len(self.selected_indices)} entities to nearest waypoint ({axis})")
        elif op_type == "swap":
            if len(self.selected_indices) != 2:
                QMessageBox.warning(self, "Selection", "Select exactly 2 entities to swap.")
                return
            self._save_undo_state("Swap Positions")
            idx1, idx2 = self.selected_indices
            e1, e2 = self.entities[idx1], self.entities[idx2]
            p1 = (e1['x'], e1['y'], e1['z'])
            p2 = (e2['x'], e2['y'], e2['z'])
            e1['x'], e1['y'], e1['z'] = p2
            e2['x'], e2['y'], e2['z'] = p1
            self._sync_entity_raw(e1)
            self._sync_entity_raw(e2)
            self._refresh_3d_view()
            self._update_selection_ui()
            self.statusBar().showMessage("Swapped positions of 2 entities")

    def load_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open DAT File", "", "DAT Files (*.dat);;All Files (*)")
        if not filepath: return
        self.loaded_maps = []
        self._load_map_file(filepath, is_primary=True)

    def add_map(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Add Map", "", "DAT Files (*.dat);;All Files (*)")
        if not filepath: return
        self._load_map_file(filepath, is_primary=False)

    def _load_map_file(self, filepath, is_primary=True):
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

                    # Enrich with CSV data
                    self._enrich_entity_with_csv(ent)

                    self.entities.append(ent)
                    map_entities.append(ent)
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

                    # Enrich with CSV data
                    self._enrich_entity_with_csv(ent)

                    self.entities.append(ent)
                    map_entities.append(ent)
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

        self.loaded_maps.append({
            'name': map_name, 'filepath': filepath, 'entities': map_entities,
            'file_sequence': map_sequence, 'start_idx': start_idx
        })

        if is_primary:
            self.file_sequence = list(map_sequence)
        else:
            self.file_sequence.extend(map_sequence)

        if len(self.loaded_maps) == 1:
            self.setWindowTitle(f"Katamari Editor - {map_name}")
        else:
            names = " + ".join([m['name'] for m in self.loaded_maps])
            self.setWindowTitle(f"Katamari Editor - {names}")

        self.entity_list.set_entities(self.entities, self.item_db)
        self._load_entity_models()
        self._refresh_3d_view(auto_fit=True)
        self.statusBar().showMessage(f"Loaded {map_name}: {len(map_entities)} entities")

    def _parse_block(self, b):
        def get_t(t, src):
            m = re.search(fr'<{t}>(.*?)</{t}>', src, re.DOTALL)
            return (m.group(1), len(m.group(1))) if m else ("", 0)
        def find_val(tags, src):
            for t in tags:
                m = re.search(fr'<{t}>(.*?)</{t}>', src, re.DOTALL)
                if m: return m.group(1).strip()
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
            'script_type': find_val(['script_type'], b),
            'script_id': find_val(['script_id'], b),
            'random_type': find_val(['random_type'], b),
            'random_id': find_val(['random_id'], b),
            'random_put_range': find_val(['random_put_range'], b),
            'comment_type': find_val(['comment_type'], b),
            'comment_id': find_val(['comment_id'], b),
            'name_type': find_val(['name_type'], b),
            'anim_type': find_val(['anim_type'], b),
            'anim_motion_id': find_val(['anim_motion_id'], b),
            'change_type': find_val(['change_type'], b),
            'change_mono_id': find_val(['change_mono_id'], b),
            'spmove_type': find_val(['spmove_type'], b),
            'spmove_rise_height': find_val(['spmove_rise_height'], b),
            'spmove_appear_second': find_val(['spmove_appear_second'], b),
            'plus_timing': find_val(['plus_timing'], b),
            'start_type': find_val(['start_type'], b),
            'move_start_size': find_val(['move_start_size'], b),
            'move_end_size': find_val(['move_end_size'], b),
            'child_ids': []
        }

    def _enrich_entity_with_csv(self, entity):
        """Add CSV data fields to entity dict"""
        db_key = entity['id'].lstrip('0') or '0'
        info = self.item_db.get(db_key, {})

        entity['csv_name'] = info.get('NAME', '')
        entity['csv_size_ingame'] = info.get('SIZE (In-Game)', '')
        entity['csv_size_mm'] = info.get('size_val', 0.0)

        # Load custom name from global dict if exists, otherwise preserve existing or use empty
        if db_key in self.custom_names:
            entity['custom_name'] = self.custom_names[db_key]
        else:
            entity['custom_name'] = entity.get('custom_name', '')

        return entity

    def _format_strict(self, val, width):
        s = f"{val:.10f}"
        if len(s) > width:
            s = s[:width]
            if s.endswith('.'): s = s[:-1].rjust(width)
        return s.ljust(width)

    def _sync_entity_raw(self, ent):
        original_content = ent['p_raw_content']
        new_parts, last_idx, ax_keys = [], 0, ['x', 'y', 'z']
        for i in range(3):
            start, end = ent['p_indices'][i]
            new_parts.append(original_content[last_idx:start])
            new_parts.append(self._format_strict(ent[ax_keys[i]], end - start))
            last_idx = end
        new_parts.append(original_content[last_idx:])
        reconstructed = "".join(new_parts)
        ent['p_raw_content'] = reconstructed
        s, e = "<posi>", "</posi>"
        si = ent['raw'].find(s) + len(s); ei = ent['raw'].find(e)
        final_block = reconstructed[:ei-si].ljust(ei-si)
        ent['raw'] = ent['raw'][:si] + final_block + ent['raw'][ei:]

    def _sync_entity_rotation(self, ent):
        if len(ent['r_indices']) != 4: return
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

    def save_map_file(self):
        """Save map - if multiple maps loaded, ask which one to save"""
        if len(self.loaded_maps) > 1:
            # Show dialog to choose which map to save
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
            choice = QDialog(self)
            choice.setWindowTitle("Save Which Map?")
            choice.setModal(True)
            layout = QVBoxLayout(choice)

            layout.addWidget(QLabel("Multiple maps loaded.\nWhich map do you want to save?"))

            for i, map_data in enumerate(self.loaded_maps):
                btn = QPushButton(f"Save: {map_data['name']}")
                btn.clicked.connect(lambda checked, idx=i, win=choice: (self._save_single_map(idx), win.accept()))
                layout.addWidget(btn)

            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(choice.reject)
            layout.addWidget(cancel_btn)

            choice.exec_()
        elif len(self.loaded_maps) == 1:
            self._save_single_map(0)
        else:
            # No loaded_maps - shouldn't happen but handle it
            filepath, _ = QFileDialog.getSaveFileName(self, "Save Map", "", "DAT Files (*.dat)")
            if filepath:
                out = "".join([i if isinstance(i, str) else i['raw'] for i in self.file_sequence])
                with open(filepath, 'wb') as f:
                    f.write(out.encode('utf-8'))
                QMessageBox.information(self, "Success", "Saved.")

    def _save_single_map(self, map_idx):
        """Save a single map by index"""
        map_data = self.loaded_maps[map_idx]

        # Ask where to save
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Map",
            map_data['name'],
            "DAT Files (*.dat)"
        )
        if not filepath:
            return

        # Reconstruct this map's file from its file_sequence
        out = "".join([i if isinstance(i, str) else i['raw'] for i in map_data['file_sequence']])
        with open(filepath, 'wb') as f:
            f.write(out.encode('utf-8'))
        QMessageBox.information(self, "Success", f"Saved {map_data['name']}.")

    def save_all_maps(self):
        """Save all loaded maps to their original files"""
        if not self.loaded_maps:
            QMessageBox.warning(self, "No Maps", "No maps loaded to save.")
            return

        saved_count = 0
        for map_data in self.loaded_maps:
            try:
                # Reconstruct this map's file from its entities
                out = "".join([i if isinstance(i, str) else i['raw'] for i in map_data['file_sequence']])
                with open(map_data['filepath'], 'wb') as f:
                    f.write(out.encode('utf-8'))
                saved_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save {map_data['name']}: {e}")

        if saved_count > 0:
            QMessageBox.information(self, "Success", f"Saved {saved_count} map(s).")
            self.statusBar().showMessage(f"Saved {saved_count} map(s)")

    def _parse_obj_file(self, filepath):
        """Parse OBJ file and return vertices, faces, and object names"""
        vertices = []
        faces = []
        objects = []  # List of (name, face_start, face_end) tuples
        current_object = None
        face_start = 0

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    if parts[0] == 'v':  # Vertex
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif parts[0] == 'f':  # Face
                        # Parse face indices (handle v/vt/vn format)
                        face_indices = []
                        for part in parts[1:]:
                            idx = part.split('/')[0]
                            face_indices.append(int(idx) - 1)  # OBJ indices are 1-based
                        # Triangulate if needed (assuming convex polygons)
                        if len(face_indices) == 3:
                            faces.append(face_indices)
                        elif len(face_indices) == 4:  # Quad to triangles
                            faces.append([face_indices[0], face_indices[1], face_indices[2]])
                            faces.append([face_indices[0], face_indices[2], face_indices[3]])
                        else:  # n-gon simple fan triangulation
                            for i in range(1, len(face_indices) - 1):
                                faces.append([face_indices[0], face_indices[i], face_indices[i+1]])
                    elif parts[0] == 'o':  # Object name
                        if current_object is not None:
                            objects.append((current_object, face_start, len(faces)))
                        current_object = parts[1] if len(parts) > 1 else "unnamed"
                        face_start = len(faces)

                # Add last object
                if current_object is not None:
                    objects.append((current_object, face_start, len(faces)))

            return np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.uint32), objects
        except Exception as e:
            raise Exception(f"Error parsing OBJ file: {e}")

    def import_mesh(self):
        """Import a 3D mesh from OBJ file, splitting into individual objects"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Import Mesh", "", "OBJ Files (*.obj);;All Files (*)")
        if not filepath:
            return

        try:
            vertices, faces, objects = self._parse_obj_file(filepath)

            if len(vertices) == 0 or len(faces) == 0:
                QMessageBox.warning(self, "Warning", "No geometry found in OBJ file.")
                return

            # Default transforms
            default_euler = np.radians([83, 55.8, 0])
            cx, cy, cz = np.cos(default_euler / 2)
            sx, sy, sz = np.sin(default_euler / 2)
            default_quat = np.array([
                sx * cy * cz - cx * sy * sz,  # qx
                cx * sy * cz + sx * cy * sz,  # qy
                cx * cy * sz - sx * sy * cz,  # qz
                cx * cy * cz + sx * sy * sz   # qw
            ], dtype=np.float32)

            obj_count = 0
            for obj_name, f_start, f_end in objects:
                obj_faces = faces[f_start:f_end]
                if len(obj_faces) == 0:
                    continue
                
                # Get unique vertices for this object and remap indices
                used_verts = np.unique(obj_faces.flatten())
                obj_vertices = vertices[used_verts].copy()
                
                # Remap indices
                old_to_new = np.zeros(len(vertices), dtype=np.uint32)
                old_to_new[used_verts] = np.arange(len(used_verts), dtype=np.uint32)
                mapped_faces = old_to_new[obj_faces]

                # Use current global transforms if any exist, otherwise default
                if self.imported_meshes:
                    ref = self.imported_meshes[0]
                    m_pos = ref['position'].copy()
                    m_quat = ref['rotation'].copy()
                    m_scale = ref['scale_xyz'].copy()
                    m_flip = list(ref['flip'])
                    m_visible = ref['visible']
                else:
                    m_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                    m_quat = default_quat.copy()
                    m_scale = np.array([1.25, 1.03, 0.7], dtype=np.float32)
                    m_flip = [False, True, False]
                    m_visible = True

                mesh_data = {
                    'filepath': filepath,
                    'name': f"{os.path.basename(filepath)} - {obj_name}",
                    'vertices': obj_vertices,
                    'faces': mapped_faces,
                    'position': m_pos,
                    'rotation': m_quat,
                    'scale_xyz': m_scale,
                    'flip': m_flip,
                    'visible': m_visible,
                    'visual': None
                }
                self.imported_meshes.append(mesh_data)
                self._render_imported_mesh(len(self.imported_meshes) - 1)
                obj_count += 1

            if obj_count == 0:
                # Same for fallback
                if self.imported_meshes:
                    ref = self.imported_meshes[0]
                    m_pos = ref['position'].copy()
                    m_quat = ref['rotation'].copy()
                    m_scale = ref['scale_xyz'].copy()
                    m_flip = list(ref['flip'])
                    m_visible = ref['visible']
                else:
                    m_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                    m_quat = default_quat.copy()
                    m_scale = np.array([1.25, 1.03, 0.7], dtype=np.float32)
                    m_flip = [False, True, False]
                    m_visible = True

                mesh_data = {
                    'filepath': filepath,
                    'name': os.path.basename(filepath),
                    'vertices': vertices,
                    'faces': faces,
                    'position': m_pos,
                    'rotation': m_quat,
                    'scale_xyz': m_scale,
                    'flip': m_flip,
                    'visible': m_visible,
                    'visual': None
                }
                self.imported_meshes.append(mesh_data)
                self._render_imported_mesh(len(self.imported_meshes) - 1)
                obj_count = 1

            self.mesh_control.set_meshes(self.imported_meshes)
            self._update_mesh_list()
            self.vispy_canvas.set_imported_meshes(self.imported_meshes)
            self.statusBar().showMessage(f"Imported {obj_count} mesh objects from {os.path.basename(filepath)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import mesh: {e}")

    def _apply_transform_to_mesh(self):
        """Bake current transformations into all selected meshes"""
        indices = [self.mesh_list_widget.row(item) for item in self.mesh_list_widget.selectedItems()]
        if not indices:
            # Fallback to current if list empty but current set
            current = self.mesh_control.current_mesh_idx
            if current >= 0: indices = [current]

        if not indices:
            QMessageBox.warning(self, "Selection", "Select meshes to apply transform.")
            return

        # Group meshes by filepath to avoid overwriting
        filepath_groups = {}
        count = 0

        for idx in indices:
            if idx >= len(self.imported_meshes): continue
            mesh = self.imported_meshes[idx]

            # 1. Get current transform data
            verts = mesh['vertices'].copy()
            flip = mesh.get('flip', [False, False, False])
            scale = mesh.get('scale_xyz', [1.0, 1.0, 1.0])
            quat = mesh.get('rotation', [0, 0, 0, 1])
            pos = mesh.get('position', np.array([0.,0.,0.]))

            # 2. Apply to vertices
            if flip[0]: verts[:, 0] *= -1
            if flip[1]: verts[:, 1] *= -1
            if flip[2]: verts[:, 2] *= -1

            verts *= scale
            verts = self._apply_quaternion_rotation(verts, quat)
            verts += pos

            # 3. Update Mesh Data with Baked Verts and Reset Transforms
            mesh['vertices'] = verts
            mesh['position'] = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            mesh['rotation'] = [0, 0, 0, 1]
            mesh['rotation_deg'] = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            mesh['scale_xyz'] = np.array([1.0, 1.0, 1.0], dtype=np.float32)
            mesh['flip'] = [False, False, False]

            # 4. Group by filepath for combined saving
            filepath = mesh.get('filepath', '')
            if filepath:
                if filepath not in filepath_groups:
                    filepath_groups[filepath] = []
                filepath_groups[filepath].append((mesh['vertices'], mesh['faces'], mesh['name']))

            count += 1

        # 5. Write combined OBJ files (all meshes with same filepath into one file)
        for filepath, mesh_parts in filepath_groups.items():
            try:
                self._write_combined_obj_file(filepath, mesh_parts)
                print(f"Updated OBJ file: {filepath} with {len(mesh_parts)} objects")
            except Exception as e:
                print(f"Failed to update OBJ file {filepath}: {e}")

        self._on_mesh_updated(-1) # Full refresh
        self.mesh_control._update_ui_from_mesh()
        self.statusBar().showMessage(f"Baked transforms for {count} meshes and updated OBJ files")

    def _write_obj_file(self, filepath, vertices, faces):
        """Write mesh data to OBJ file"""
        with open(filepath, 'w') as f:
            f.write(f"# Auto-generated by Katamari Editor\n")
            f.write(f"o Mesh\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face in faces:
                # OBJ indices are 1-based
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    def _write_combined_obj_file(self, filepath, mesh_parts):
        """Write multiple mesh objects to a single OBJ file"""
        with open(filepath, 'w') as f:
            f.write(f"# Auto-generated by Katamari Editor\n")
            f.write(f"# Combined {len(mesh_parts)} mesh objects\n\n")

            vertex_offset = 0
            for i, (vertices, faces, name) in enumerate(mesh_parts):
                # Write object header
                obj_name = name.split(' - ')[-1] if ' - ' in name else f"Mesh_{i}"
                f.write(f"o {obj_name}\n")

                # Write vertices
                for v in vertices:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

                # Write faces with offset
                for face in faces:
                    # OBJ indices are 1-based, add vertex_offset for multi-object files
                    f.write(f"f {face[0]+1+vertex_offset} {face[1]+1+vertex_offset} {face[2]+1+vertex_offset}\n")

                f.write("\n")
                vertex_offset += len(vertices)

    def _render_imported_mesh(self, mesh_idx):
        """Render imported mesh in the 3D view"""
        if mesh_idx >= len(self.imported_meshes):
            return

        mesh_data = self.imported_meshes[mesh_idx]

        # Remove old visual if exists
        if mesh_data['visual'] is not None:
            mesh_data['visual'].parent = None
            mesh_data['visual'] = None

        if not mesh_data['visible']:
            return

        # Start with original vertices
        vertices = mesh_data['vertices'].copy()

        # Apply flip before scale
        flip = mesh_data.get('flip', [False, False, False])
        if flip[0]:
            vertices[:, 0] *= -1
        if flip[1]:
            vertices[:, 1] *= -1
        if flip[2]:
            vertices[:, 2] *= -1

        # Apply non-uniform scale
        if 'scale_xyz' in mesh_data:
            scale_xyz = mesh_data['scale_xyz']
            vertices[:, 0] *= scale_xyz[0]
            vertices[:, 1] *= scale_xyz[1]
            vertices[:, 2] *= scale_xyz[2]
        else:
            # Fallback to uniform scale
            vertices *= mesh_data.get('scale', 1.0)

        # Apply rotation (quaternion)
        quat = mesh_data.get('rotation', np.array([0, 0, 0, 1], dtype=np.float32))
        vertices = self._apply_quaternion_rotation(vertices, quat)

        # Transform vertices: negate X and swap Y/Z like entities
        vertices[:, [0, 1, 2]] = np.column_stack([-vertices[:, 0], vertices[:, 2], vertices[:, 1]])

        # Apply position offset
        pos = mesh_data['position']
        vertices += np.array([-pos[0], pos[2], pos[1]], dtype=np.float32)

        # Create mesh visual
        mesh_visual = visuals.Mesh(
            vertices=vertices,
            faces=mesh_data['faces'],
            color=(0.7, 0.7, 0.9, 0.5),  # Semi-transparent blue-ish
            parent=self.vispy_canvas.view.scene
        )

        mesh_data['visual'] = mesh_visual
        self.vispy_canvas.canvas.update()

    def _apply_quaternion_rotation(self, vertices, quat):
        """Apply quaternion rotation to vertices"""
        qx, qy, qz, qw = quat

        # Convert quaternion to rotation matrix
        xx, yy, zz = qx * qx, qy * qy, qz * qz
        xy, xz, yz = qx * qy, qx * qz, qy * qz
        wx, wy, wz = qw * qx, qw * qy, qw * qz

        rot_matrix = np.array([
            [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
            [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)]
        ], dtype=np.float32)

        # Apply rotation matrix to all vertices
        return vertices @ rot_matrix.T

    def _on_mesh_updated(self, mesh_idx):
        """Handle mesh transformation update"""
        if mesh_idx == -1:
            # Full refresh
            for i in range(len(self.imported_meshes)):
                self._render_imported_mesh(i)
        else:
            self._render_imported_mesh(mesh_idx)

        self.vispy_canvas.set_imported_meshes(self.imported_meshes)

    def _update_mesh_list(self):
        """Update the mesh list widget"""
        self.mesh_list_widget.clear()
        for i, mesh in enumerate(self.imported_meshes):
            visibility = "👁" if mesh.get('visible', True) else "🚫"
            item_text = f"{visibility} {i}: {mesh['name']} ({len(mesh['vertices'])} verts)"
            self.mesh_list_widget.addItem(item_text)

    def _on_mesh_list_selection_changed(self):
        """Handle mesh list selection and update 3D highlighting for multiple meshes"""
        items = self.mesh_list_widget.selectedItems()
        indices = [self.mesh_list_widget.row(item) for item in items]
        
        if indices:
            # Set the first/most recent as current for the control panel
            self.mesh_control.set_current_mesh(indices[0])
            
        hue = self.mesh_control.hue_slider.value()
        self.vispy_canvas.select_meshes_by_indices(indices, hue)

    def _on_mesh_clicked_in_3d(self, mesh_idx, shift, ctrl):
        """Sync 3D mesh click back to the mesh list widget with multi-select support"""
        # Safety check
        if mesh_idx < 0 or mesh_idx >= self.mesh_list_widget.count():
            print(f"Warning: mesh_idx {mesh_idx} out of range (list has {self.mesh_list_widget.count()} items)")
            return

        self.mesh_list_widget.blockSignals(True)

        item = self.mesh_list_widget.item(mesh_idx)
        if item is None:
            print(f"Warning: Could not get item at mesh_idx {mesh_idx}")
            self.mesh_list_widget.blockSignals(False)
            return

        if ctrl:
            # Toggle item
            item.setSelected(not item.isSelected())
        elif shift:
            # Add to selection
            item.setSelected(True)
        else:
            # Single select - clear others first
            self.mesh_list_widget.clearSelection()
            item.setSelected(True)
            self.mesh_list_widget.setCurrentItem(item)

        self.mesh_list_widget.blockSignals(False)

        # Now synchronize the 3D view with the new list state
        self._on_mesh_list_selection_changed()

    def _delete_selected_mesh(self):
        """Delete the selected mesh from the list"""
        row = self.mesh_list_widget.currentRow()
        if row < 0 or row >= len(self.imported_meshes):
            return

        reply = QMessageBox.question(
            self, "Delete Mesh",
            f"Delete mesh '{self.imported_meshes[row]['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove visual from scene
            if self.imported_meshes[row]['visual'] is not None:
                self.imported_meshes[row]['visual'].parent = None

            self.imported_meshes.pop(row)
            self._update_mesh_list()
            self.mesh_control.set_meshes(self.imported_meshes)
            self.vispy_canvas.set_imported_meshes(self.imported_meshes)
            self.vispy_canvas.canvas.update()

    def _toggle_mesh_visibility(self):
        """Toggle visibility of the selected mesh"""
        row = self.mesh_list_widget.currentRow()
        if row < 0 or row >= len(self.imported_meshes):
            return

        mesh = self.imported_meshes[row]
        mesh['visible'] = not mesh.get('visible', True)
        self._render_imported_mesh(row)
        self._update_mesh_list()

    def _on_mesh_selection_mode_changed(self, enabled):
        """Handle mesh selection mode toggle"""
        print(f"Main window: mesh selection mode changed to {enabled}")
        self.vispy_canvas.toggle_mesh_selection_mode(enabled)
        # Update hue value when mode changes
        hue = self.mesh_control.hue_slider.value()
        self.vispy_canvas.set_mesh_highlight_hue(hue)
        print(f"Set mesh highlight hue to {hue}")
        if enabled:
            self.statusBar().showMessage("Mesh Selection Mode: Click on mesh to select/highlight")
        else:
            self.statusBar().showMessage("Entity Selection Mode")

    def _on_mesh_highlight_hue_changed(self, hue):
        """Handle mesh highlight hue slider change"""
        self.vispy_canvas.set_mesh_highlight_hue(hue)

    def _assign_mesh_to_entity(self):
        """Assign mesh geometry (from selection or dialog) to the selected entity"""
        if len(self.selected_indices) != 1:
            QMessageBox.warning(self, "Selection Error", "Please select exactly one entity to assign a mesh.")
            return

        if not self.imported_meshes:
            QMessageBox.warning(self, "No Meshes", "No meshes have been imported. Please import a mesh first.")
            return

        entity_idx = self.selected_indices[0]
        entity = self.entities[entity_idx]

        # Use new selection format (list of (mesh_idx, face_idx))
        selected_mesh_indices = self.vispy_canvas.selected_mesh_indices
        use_mesh_selection = self.vispy_canvas.mesh_selection_mode and len(selected_mesh_indices) > 0

        if use_mesh_selection:
            # Extract and combine geometry from all selected meshes
            combined_verts = []
            combined_faces = []
            vert_offset = 0
            
            # Sort by mesh_idx to process predictably
            meshes_to_process = sorted(list(set(selected_mesh_indices)))
            
            # Get common transforms (assuming all meshes share them as per current global design)
            ref_mesh = self.imported_meshes[meshes_to_process[0]]
            m_pos = ref_mesh['position']
            m_scale = ref_mesh.get('scale_xyz', [1.0, 1.0, 1.0])
            m_quat = ref_mesh.get('rotation', [0, 0, 0, 1])
            m_flip = ref_mesh.get('flip', [False, False, False])
            
            # Convert rotation to Euler degrees for the filename
            m_euler_rad = self.mesh_control._quat_to_euler(m_quat)
            m_euler_deg = np.degrees(m_euler_rad)
            
            for m_idx in meshes_to_process:
                mesh = self.imported_meshes[m_idx]
                # Process the entire mesh part
                obj_faces = mesh['faces']
                used_v_indices = np.unique(obj_faces.flatten())
                obj_verts = mesh['vertices'][used_v_indices].copy()
                
                # Apply mesh-specific transforms to world space
                flip = mesh.get('flip', [False, False, False])
                if flip[0]: obj_verts[:, 0] *= -1
                if flip[1]: obj_verts[:, 1] *= -1
                if flip[2]: obj_verts[:, 2] *= -1
                
                s = mesh.get('scale_xyz', [1.0, 1.0, 1.0])
                obj_verts *= s
                
                quat = mesh.get('rotation', [0, 0, 0, 1])
                obj_verts = self._apply_quaternion_rotation(obj_verts, quat)
                
                # Apply position offset
                obj_verts += mesh['position']
                
                # Remap faces to our new subset
                old_to_new = {old: new + vert_offset for new, old in enumerate(used_v_indices)}
                temp_faces = []
                for f in obj_faces:
                    temp_faces.append([old_to_new[idx] for idx in f])
                
                combined_faces.extend(temp_faces)
                combined_verts.append(obj_verts)
                vert_offset += len(obj_verts)
                
            model_vertices = np.vstack(combined_verts)
            model_faces = np.array(combined_faces, dtype=np.uint32)
            mesh_center = model_vertices.mean(axis=0)

            # Transform vertices to entity-local space
            # (treat entity as the exact center of the combined mesh)
            e_x, e_y, e_z = entity['x'], entity['y'], entity['z']
            model_vertices -= np.array([e_x, e_y, e_z])

            # Rotate by inverse entity rotation to get entity-local coordinates
            e_rx, e_ry, e_rz, e_rw = entity['rx'], entity['ry'], entity['rz'], entity['rw']
            inv_quat = [-e_rx, -e_ry, -e_rz, e_rw]  # Conjugate for unit quaternion
            model_vertices = self._apply_quaternion_rotation(model_vertices, inv_quat)

            # Format filename with transform metadata
            flip_str = "".join([c for i, c in enumerate("XYZ") if m_flip[i]])
            if not flip_str: flip_str = "None"
            trans_suffix = f"_s{m_scale[0]:.2f}-{m_scale[1]:.2f}-{m_scale[2]:.2f}_r{int(m_euler_deg[0])}-{int(m_euler_deg[1])}-{int(m_euler_deg[2])}_f{flip_str}"


        else:
            # Simplified dialog-based mesh selection (one mesh per entry)
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QLabel

            dialog = QDialog(self)
            dialog.setWindowTitle("Assign Mesh to Entity")
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel(f"Assigning mesh to Entity ID: {entity['id']}"))
            layout.addWidget(QLabel("Select imported mesh:"))

            mesh_combo = QComboBox()
            for i, m in enumerate(self.imported_meshes):
                mesh_combo.addItem(f"{i}: {m['name']}", i)
            layout.addWidget(mesh_combo)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec_() != QDialog.Accepted:
                return

            mesh_idx = mesh_combo.currentData()
            mesh = self.imported_meshes[mesh_idx]
            
            # Use vertices with current transforms
            model_vertices = mesh['vertices'].copy()
            model_faces = mesh['faces'].copy()
            
            flip = mesh.get('flip', [False, False, False])
            if flip[0]: model_vertices[:, 0] *= -1
            if flip[1]: model_vertices[:, 1] *= -1
            if flip[2]: model_vertices[:, 2] *= -1
            
            s = mesh.get('scale_xyz', [1.0, 1.0, 1.0])
            model_vertices *= s
            
            quat = mesh.get('rotation', [0, 0, 0, 1])
            model_vertices = self._apply_quaternion_rotation(model_vertices, quat)
            
            model_vertices += mesh['position']

            # --- KEY CHANGE: Convert to Entity Local Space ---
            # 1. Translate World -> Relative to Entity
            e_x, e_y, e_z = entity['x'], entity['y'], entity['z']
            
            # BK World Space conversion used for display is (-x, z, y).
            # But our `model_vertices` are in our EDITOR World Space (which matches BK World Space?)
            # Let's assume model_vertices are in the same coordinate system as Entity Pos.
            # Wait, our editor inputs (ImportedMeshControl) are just X, Y, Z.
            # We assume these match the Entity X, Y, Z.
            
            model_vertices -= np.array([e_x, e_y, e_z])
            
            # 2. Rotate World -> Local (Inverse Entity Rotation)
            # Q_entity = (rx, ry, rz, rw)
            # We want to rotate by Conjugate(Q).
            e_rx, e_ry, e_rz, e_rw = entity['rx'], entity['ry'], entity['rz'], entity['rw']
            # Conjugate for unit quat is (-x, -y, -z, w)
            inv_quat = [-e_rx, -e_ry, -e_rz, e_rw]
            
            model_vertices = self._apply_quaternion_rotation(model_vertices, inv_quat)

            # Capture transform for metadata
            m_scale = s
            m_euler_deg = np.degrees(self.mesh_control._quat_to_euler(quat))
            m_flip = flip
            flip_str = "".join([c for i, c in enumerate("XYZ") if m_flip[i]])
            if not flip_str: flip_str = "None"
            trans_suffix = f"_s{m_scale[0]:.2f}-{m_scale[1]:.2f}-{m_scale[2]:.2f}_r{int(m_euler_deg[0])}-{int(m_euler_deg[1])}-{int(m_euler_deg[2])}_f{flip_str}"

        # Generate filename using ItemName+ID format
        models_dir = Path(__file__).parent / "entity_models"
        models_dir.mkdir(exist_ok=True)

        # Get item name from database
        db_key = entity['id'].lstrip('0') or '0'
        info = self.item_db.get(db_key, {})
        item_name = info.get('obj_en', '').replace(' ', '_').replace('/', '_').replace('\\', '_')

        # Create filename: ItemName_ID_Transforms.obj (or just ID_Transforms.obj if no item name)
        if item_name and item_name != '----':
            model_filename = f"{item_name}_{entity['id']}{trans_suffix}.obj"
        else:
            model_filename = f"{entity['id']}{trans_suffix}.obj"

        model_path = models_dir / model_filename

        if model_path.exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"The file '{model_filename}' already exists.\n\nDo you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.statusBar().showMessage("Mesh assignment cancelled")
                return

        try:
            with open(model_path, 'w') as f:
                f.write(f"# Entity {entity['id']} model\n")
                if item_name and item_name != '----':
                    f.write(f"# Item: {item_name}\n")
                
                # Write transformation metadata
                f.write(f"# Scale: {m_scale[0]:.4f}, {m_scale[1]:.4f}, {m_scale[2]:.4f}\n")
                f.write(f"# Rotation (Euler): {m_euler_deg[0]:.2f}, {m_euler_deg[1]:.2f}, {m_euler_deg[2]:.2f}\n")
                f.write(f"# Flip: {m_flip}\n")
                f.write(f"o entity_{entity['id']}\n")
                for v in model_vertices:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                for face in model_faces:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

            # Store assignment
            self.entity_models[entity_idx] = str(model_path)
            self._save_entity_models()

            mode_msg = " (from selected mesh faces)" if use_mesh_selection else ""
            QMessageBox.information(self, "Success", f"Mesh assigned to entity {entity['id']}{mode_msg} and saved to {model_filename}")
            self.statusBar().showMessage(f"Assigned mesh to entity {entity['id']}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save model: {e}")

    def _view_entity_models(self):
        """Show a dialog with all entity model assignments"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Entity Model Assignments")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        if not self.entity_models:
            text_edit.setPlainText("No entity models assigned yet.")
        else:
            lines = ["Entity Model Assignments:", "=" * 50, ""]
            for entity_idx, model_path in sorted(self.entity_models.items()):
                if entity_idx < len(self.entities):
                    entity = self.entities[entity_idx]
                    lines.append(f"Entity {entity['id']} (Index {entity_idx}): {model_path}")
                else:
                    lines.append(f"Entity Index {entity_idx}: {model_path} (entity not found)")
            text_edit.setPlainText("\n".join(lines))

        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()

    def _save_entity_models(self):
        """Save entity model assignments to JSON file"""
        models_file = Path(__file__).parent / "entity_models.json"
        try:
            # Convert entity indices to entity IDs for portability
            id_based_models = {}
            for entity_idx, model_path in self.entity_models.items():
                if entity_idx < len(self.entities):
                    entity_id = self.entities[entity_idx]['id']
                    # Use absolute path or relative to project? Let's use relative if possible
                    p = Path(model_path)
                    try:
                        rel_path = p.relative_to(Path(__file__).parent)
                        id_based_models[entity_id] = str(rel_path)
                    except:
                        id_based_models[entity_id] = model_path

            with open(models_file, 'w') as f:
                json.dump(id_based_models, f, indent=2)
        except Exception as e:
            print(f"Error saving entity models: {e}")

    def _load_entity_models(self):
        """Load entity model assignments from JSON file and auto-load mesh files if enabled"""
        import json
        models_file = Path(__file__).parent / "entity_models.json"
        models_dir = Path(__file__).parent / "entity_models"

        # Load assignments from JSON
        if models_file.exists():
            try:
                with open(models_file, 'r') as f:
                    id_based_models = json.load(f)

                # Convert entity IDs back to indices
                # IMPORTANT: All entities with the same ID share the same model
                self.entity_models = {}
                for entity_idx, entity in enumerate(self.entities):
                    entity_id = entity['id']
                    if entity_id in id_based_models:
                        model_path = id_based_models[entity_id]
                        # Verify if relative path exists
                        p = Path(model_path)
                        if not p.is_absolute():
                            p = Path(__file__).parent / model_path
                        
                        if p.exists():
                            self.entity_models[entity_idx] = str(p)

            except Exception as e:
                print(f"Error loading entity models: {e}")

        pass

    def _auto_import_entity_mesh(self, obj_path, entity_idx):
        """Import and display a mesh for an entity from an OBJ file"""
        # Parse OBJ file
        vertices = []
        faces = []

        with open(obj_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('v '):
                    parts = line.split()
                    if len(parts) >= 4:
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    parts = line.split()
                    # Handle face indices (1-based in OBJ)
                    face_verts = []
                    for i in range(1, len(parts)):
                        # Handle formats like "v", "v/vt", "v/vt/vn", "v//vn"
                        idx = parts[i].split('/')[0]
                        face_verts.append(int(idx) - 1)  # Convert to 0-based
                    # Triangulate if needed (assumes convex faces)
                    for i in range(1, len(face_verts) - 1):
                        faces.append([face_verts[0], face_verts[i], face_verts[i + 1]])

        if not vertices or not faces:
            return

        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.uint32)

        # Add to imported meshes
        mesh_name = obj_path.stem
        mesh_data = {
            'name': mesh_name,
            'vertices': vertices,
            'faces': faces,
            'objects': [],  # No object groups for auto-loaded meshes
            'position': np.array([0.0, 0.0, 0.0], dtype=np.float32),
            'rotation_deg': np.array([0.0, 0.0, 0.0], dtype=np.float32),
            'scale_xyz': np.array([1.0, 1.0, 1.0], dtype=np.float32),
            'flip': [False, False, False],
            'visible': True,
            'visual': None
        }

        self.imported_meshes.append(mesh_data)
        self._render_imported_mesh(len(self.imported_meshes) - 1)
        self.mesh_control.set_meshes(self.imported_meshes)
        self._update_mesh_list()
        self.vispy_canvas.set_imported_meshes(self.imported_meshes)

        # Store assignment
        self.entity_models[entity_idx] = str(obj_path)

    def _refresh_entity_model_renders(self):
        """Trigger Vispy to render models for all entities that have assignments"""
        if not self.entities: return
        self.statusBar().showMessage("Loading and rendering entity models...")
        self.vispy_canvas.clear_entity_models()
        self.vispy_canvas.render_entity_models(self.entities, self.entity_models)
        self.statusBar().showMessage("Entity models loaded.", 3000)

    def _save_undo_state(self, action_name="Change"):
        state = {
            'action': action_name,
            'entities': copy.deepcopy(self.entities),
            'file_sequence': copy.deepcopy(self.file_sequence),
            'loaded_maps': copy.deepcopy(self.loaded_maps),
            'selected_indices': self.selected_indices.copy()  # Save selection
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo: self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self.statusBar().showMessage("Nothing to undo")
            return
        state = self.undo_stack.pop()
        self.entities = state['entities']
        self.file_sequence = state['file_sequence']
        self.loaded_maps = state['loaded_maps']
        self.selected_indices = state.get('selected_indices', [])  # Restore selection
        self.entity_list.set_entities(self.entities, self.item_db)
        self.entity_list.set_selection(self.selected_indices)  # Update list selection
        self._refresh_3d_view()
        self._update_selection_ui()  # Update entity info panel
        self.statusBar().showMessage(f"Undid: {state['action']}")


def main():
    app.use_app('pyqt5')
    qt_app = QApplication(sys.argv)
    qt_app.setStyle('Fusion')
    window = KatamariEditorVispy()
    window.show()
    sys.exit(qt_app.exec_())

if __name__ == "__main__":
    main()