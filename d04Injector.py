#!/usr/bin/env python3
"""
Katamari DAT Editor - Optimized with Exact Byte Offsets
========================================================
Combines level injection, parameter editing, and lighting editing.
Uses memory mapping for instant loading and low RAM usage.

KNOWN FILE STRUCTURE (hex offsets):
- <loc> blocks (levels):        0x3D3800 to 0x38FC0685
- <SMiDataFile> (parameters):   0x27A818 to 0x297B78  
- <SDataSet> (lighting):        0x1B7817 to 0x1B9080
- Warp info:                    0x298017 to 0x2A9958

Level order (84 total, index 0 is unused):
UNUSED, TUTORIAL, BIG-1_A, BIG-2_A, BIG-2_B, BIG-2_C, BIG-3_A, BIG-3_B, BIG-3_C,
BIG-4_A, BIG-4_B, BIG-4_C, BIG-4_D, BIG-4_TIME, BIG-5_A, BIG-5_B, BIG-5_C, BIG-5_D,
BIG-5_TIME, BIG-6_A, BIG-6_B, BIG-6_C, BIG-6_D, BIG-6_TIME, BIG-7_A, BIG-7_B,
BIG-8_A, BIG-8_B, BIG-8_C, BIG-8_D, BIG-8_E, BIG-9_A, BIG-9_B, BIG-9_C, BIG-9_D,
BIG-9_E, BIG-9_F, BIG-9_G, BIG-9_H, FOOD_A, HOT_A, HOT_B, CAR_A, CAR_B, CAR_TIME,
SHOPPING_A, DRESS_A, SEIZA_A, SEIZA_C, SEIZA_TIME, JUSTSIZE-1_A, JUSTSIZE-2_A,
JUSTSIZE-3_A, OUSAMA_A, OUSAMA_B, OUSAMA_C, OUSAMA_D, OUSAMA_E, OUSAMA_F, OUSAMA_G,
OUSAMA_H, OUSAMA_I, OUSAMA_J, BIG-10_A, BIG-10_B, BIG-11_A, BIG-11_B, BIG-11_C,
JOIN-A-1_A, JOIN-A-1_B, JOIN-A-1_C, JOIN-A-1_TIME, JOIN-A-2_A, JOIN-A-2_B,
JOIN-A-2_C, JOIN-A-2_D, JOIN-A-2_TIME, JOIN-A-3_A, JOIN-A-3_B, JOIN-A-3_C,
JOIN-A-3_D, JOIN-A-3_E, SELECTMAP_A
"""

import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, ttk, scrolledtext
import os
import re
import math
import mmap
import threading

# =============================================================================
# CONSTANTS
# =============================================================================

# Known byte offsets (converted from hex)
LOC_START = 0x3D3800        # 4012032
LOC_END = 0x38FC0685        # 956302981 (approx - actual end determined by scanning)
SMIDATA_START = 0x27A818    # 2598936
SMIDATA_END = 0x297B78      # 2718584
SDATA_START = 0x1B7817      # 1800215
SDATA_END = 0x1B9080        # 1806464
WARP_START = 0x298017       # 2719767
WARP_END = 0x2A9958         # 2791768

# Bonus Categories (0-90)
BONUS_CATEGORIES = {
    0: "(None)",
    1: "Veggies", 2: "Fruit", 3: "Food", 4: "Snacks", 5: "Japanese Food",
    6: "Drinks", 7: "Cooking", 8: "Cleaning", 9: "Washing", 10: "Reading",
    11: "Stationary", 12: "Fashion", 13: "Sound", 14: "Sports", 15: "Powerful",
    16: "Playtime", 17: "Games", 18: "Containers", 19: "Decorations", 20: "Necessities",
    21: "Rain", 22: "Electronics", 23: "Furniture", 24: "Post", 25: "Luggage",
    26: "Gardening", 27: "Flowers", 28: "Communication", 29: "Tools", 30: "Summer",
    31: "Police", 32: "Science", 33: "Rich", 34: "Lighting", 35: "Hot",
    36: "Cold", 37: "Seating", 38: "Weapons", 39: "Danger", 40: "Measuring",
    41: "Art", 42: "Control", 43: "Japan", 44: "Festival", 45: "Celebration",
    46: "Evil", 47: "Heroes", 48: "School", 49: "Playground", 50: "Energy",
    51: "Farming", 52: "Industry", 53: "Symbols", 54: "House", 55: "Stores",
    56: "Facilities", 57: "Partitions", 58: "Entrances and Exits", 59: "Roadways", 60: "Streets",
    61: "Advertising", 62: "Guidance", 63: "Plants", 64: "Nature", 65: "Wheels",
    66: "Transport", 67: "Work Vehicles", 68: "Romance", 69: "Children", 70: "Teenagers",
    71: "Adults", 72: "Workers", 73: "Professionals", 74: "Cousins", 75: "Cute", 76: "Zodiac",
    77: "Fierce", 78: "Aquarium", 79: "Wings", 80: "Animals", 81: "Sewing",
    82: "Clouds", 83: "Ocean", 84: "Fantasy", 85: "Antique", 86: "Royal",
    87: "Famous Sites", 88: "World", 89: "Weird Things", 90: "Cosmos"
}

# SMiData parameter definitions with full documentation
SMIDATA_PARAMS = {
    "c8Code": {"desc": "Internal stage name", "type": "str"},
    "s32Rating_0": {"desc": "Par scores for king rating (6 values). First = minimum clear requirement", "type": "str"},
    "s32Rating_1": {"desc": "Additional rating values (-1 = unused)", "type": "str"},
    "s32Rating_2": {"desc": "Additional rating values (-1 = unused)", "type": "str"},
    "s32BonusPoint": {"desc": "Par scores for category points (6 values)", "type": "str"},
    "f32Time": {"desc": "Time limit in seconds (0.0 = unlimited)", "type": "float"},
    "s32ShootingStarTime": {"desc": "Unused (remnant of scrapped feature)", "type": "int"},
    "u32Target": {"desc": "Time Attack goal / Temperature goal / Target size (3 values)", "type": "str"},
    "f32DispScaleCoef": {"desc": "Display scale coefficient", "type": "float"},
    "s8Index": {"desc": "Level ID (decimal)", "type": "int"},
    "u8Enabled": {"desc": "Level enabled (0=disabled/test, 1=enabled)", "type": "int", "range": (0, 1)},
    "u8Override": {"desc": "Override flag", "type": "int"},
    "s8PlayerNum": {"desc": "Player count (1=single, 2=co-op/local VS, 4=online VS)", "type": "int", "range": (1, 4)},
    "u8Eternal": {"desc": "Eternal Mode (0=off, 1=on)", "type": "int", "range": (0, 1)},
    "u8Modoki": {"desc": "Time Attack enabled (0=off, 1=on)", "type": "int", "range": (0, 1)},
    "u8BonusCategory": {
        "desc": "Bonus category ID (0=none, 1-89=category)", "type": "int", "range": (0, 89),
        "options": BONUS_CATEGORIES
    },
    "u8Star": {"desc": "Star flag", "type": "int"},
    "u8NetworkRanking": {"desc": "Leaderboard (0=disabled, 1=enabled)", "type": "int", "range": (0, 1)},
    "u8Proc": {
        "desc": "Game mode (>15 crashes!)", "type": "int", "range": (0, 15),
        "options": {
            0: "Test Mode", 1: "As Large As Possible", 2: "Schloss Kosmos", 3: "Co-Op",
            4: "Separate But Together (unfinished)", 5: "Munchies Manor/Shani Circuit",
            6: "Fancy & Schmancy's", 7: "Hubble Horoscope", 8: "Roller Roaster",
            9: "Lovers Loom", 10: "Instituto Exactamundo", 11: "Chateau Notre Desir",
            12: "Egg School", 13: "VS Local", 14: "VS Online", 15: "VS Biggy Battle (unfinished)"
        }
    },
    "u8ClearOnlySpace": {"desc": "Has 3km-10000km/Cosmos section", "type": "int", "range": (0, 1)},
    "s82dScale": {"desc": "2D scale setting", "type": "int"},
    "s82dCore": {
        "desc": "Gauge graphics style (>16 = same as 0)", "type": "int", "range": (0, 16),
        "options": {
            0: "VS Online", 1: "Dirigible/Seadome/VS Local/Co-Op:Neighborhood", 
            2: "Oasis/Seadome/Schloss", 3: "Casino/Dynaville", 
            4: "Sunrise/Lovers/House/Mechanical", 5: "Cloud 9/World/Dangerous",
            6: "bug (UNUSED)", 7: "Shani Circuit", 8: "flower (UNUSED)", 
            9: "n/a (UNUSED)", 10: "Munchies Manor", 11: "girl (UNUSED)", 
            12: "Fancy & Schmancy's", 13: "Hubble Horoscope", 
            14: "Instituto Exactamundo", 15: "Roller Roaster", 16: "Chateau Notre Desir"
        }
    },
    "s82dOujiBase": {
        "desc": "Cousin view earth type", "type": "int", "range": (-1, 8),
        "options": {
            -1: "Disabled (Egg School)", 0: "Standard", 1: "Standard", 2: "Standard",
            3: "Galaxy (Cosmos)", 4: "Standard", 5: "Standard", 6: "Co-Op",
            7: "Co-Op Galaxy", 8: "Local VS/TwoPlayer"
        }
    },
    "u8UseCore": {
        "desc": "Katamari type (>14 CRASHES!)", "type": "int", "range": (0, 14),
        "options": {
            0: "Dirigible/Cloud9/Schloss/Lovers", 1: "Egg School", 2: "Munchies Manor",
            3: "Roller Roaster", 4: "Shani Circuit", 5: "Fancy & Schmancy's",
            6: "Hubble Horoscope", 7: "Instituto Exactamundo", 8: "Chateau Notre Desir",
            9: "VS Local/Online", 10: "Co-Op: Neighborhood/House", 11: "Time Attack",
            12: "Oasis/Dynaville", 13: "Casino/Coolhouse", 14: "Sunrise/Seadome/Co-Op World"
        }
    },
    "u8Fog": {"desc": "Fog type (4 values: 0000=std, 1111=Sunrise, 2222=Lovers)", "type": "str"},
    "u8Light": {"desc": "Lighting table (0=standard, 1=Sunrise/Night, >1=too bright)", "type": "int", "range": (0, 1)},
    "u8Acc": {"desc": "Acceleration setting", "type": "int"},
    "u8Camera": {"desc": "Camera settings", "type": "int"},
    "s8Crumble": {"desc": "Crumble setting", "type": "int"},
    "u8Scale2d": {"desc": "2D scale flag", "type": "int"},
    "u8ViewCore": {"desc": "View core setting", "type": "int"},
    "s8Present": {"desc": "Present setting (-1=none)", "type": "int"},
    "u8TgtMonoIdx": {
        "desc": "Target type for modes 5/7 (>7 = nothing)", "type": "int", "range": (0, 6),
        "options": {
            0: "kcal/Calories", 1: "Rings", 2: "Constellations",
            3: "Insects", 4: "People (Women)", 5: "Fish", 6: "Flowers"
        }
    },
    "s8ChainEff": {"desc": "Chain effect", "type": "int"},
    "s8SnowFlowerEff": {"desc": "Snow/Flower effect", "type": "int"},
    "u8GameMessage": {"desc": "Game message ID", "type": "int"},
    "u8LectureMessage": {"desc": "Lecture message ID", "type": "int"},
    "u8ResultMessage": {"desc": "Result message ID", "type": "int"},
    "s16TgtMono": {"desc": "Target mono (3 values)", "type": "str"},
    "s16BonusCategoryRate": {"desc": "Category points multiplier (always 1000)", "type": "int"},
    "s16CoreInitID": {"desc": "Stage connection (12 hex: Standard/TimeAttack/Eternal)", "type": "str"},
    "u8AriaNum": {"desc": "Number of zones (6 digits)", "type": "str"},
    "u8MapScript_0": {"desc": "Map script for Standard (hex)", "type": "str"},
    "u8MapScript_1": {"desc": "Map script for Time Attack (hex)", "type": "str"},
    "u8MapScript_2": {"desc": "Map script for Eternal (hex)", "type": "str"},
    "u8LocScript_0": {"desc": "Object layout for Standard (hex)", "type": "str"},
    "u8LocScript_1": {"desc": "Object layout for Time Attack (hex)", "type": "str"},
    "u8LocScript_2": {"desc": "Object layout for Eternal (hex)", "type": "str"},
    "s16MonoMdl": {"desc": "Object set (3 values: std/timeattack/eternal)", "type": "str"},
    "s8Warp": {"desc": "Warp points (6 values: 2 Std, 2 TA, 2 Eternal)", "type": "str"},
    "s8AreaChange": {"desc": "Area change table (3 values)", "type": "str"},
}

# Level names (index 0 = UNUSED, then 1-83)
LEVEL_NAMES = [
    "UNUSED",  # Index 0
    "TUTORIAL", "BIG-1_A", "BIG-2_A", "BIG-2_B", "BIG-2_C", "BIG-3_A", "BIG-3_B", "BIG-3_C",
    "BIG-4_A", "BIG-4_B", "BIG-4_C", "BIG-4_D", "BIG-4_TIME", "BIG-5_A", "BIG-5_B", "BIG-5_C",
    "BIG-5_D", "BIG-5_TIME", "BIG-6_A", "BIG-6_B", "BIG-6_C", "BIG-6_D", "BIG-6_TIME",
    "BIG-7_A", "BIG-7_B", "BIG-8_A", "BIG-8_B", "BIG-8_C", "BIG-8_D", "BIG-8_E",
    "BIG-9_A", "BIG-9_B", "BIG-9_C", "BIG-9_D", "BIG-9_E", "BIG-9_F", "BIG-9_G", "BIG-9_H",
    "FOOD_A", "HOT_A", "HOT_B", "CAR_A", "CAR_B", "CAR_TIME",
    "SHOPPING_A", "DRESS_A", "SEIZA_A", "SEIZA_C", "SEIZA_TIME",
    "JUSTSIZE-1_A", "JUSTSIZE-2_A", "JUSTSIZE-3_A",
    "OUSAMA_A", "OUSAMA_B", "OUSAMA_C", "OUSAMA_D", "OUSAMA_E", "OUSAMA_F", "OUSAMA_G",
    "OUSAMA_H", "OUSAMA_I", "OUSAMA_J",
    "BIG-10_A", "BIG-10_B", "BIG-11_A", "BIG-11_B", "BIG-11_C",
    "JOIN-A-1_A", "JOIN-A-1_B", "JOIN-A-1_C", "JOIN-A-1_TIME",
    "JOIN-A-2_A", "JOIN-A-2_B", "JOIN-A-2_C", "JOIN-A-2_D", "JOIN-A-2_TIME",
    "JOIN-A-3_A", "JOIN-A-3_B", "JOIN-A-3_C", "JOIN-A-3_D", "JOIN-A-3_E",
    "SELECTMAP_A"
]

EXPECTED_FILE_SIZE = 1629420 * 1024  # 1,668,526,080 bytes


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class KatamariDatEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Katamari DAT Editor v2.0 - Fast mmap + Exact Offsets")
        self.root.geometry("1050x800")
        
        # Main file state
        self.dat_path = None
        self.file_size = 0
        
        # Level data
        self.level_offsets = []
        
        # Lighting data
        self.lighting_blocks = []
        self.current_lighting_block = None
        self.lighting_entries = {}
        self.color_buttons = {}
        self.dir_canvases = {}
        self.dir_sliders = {}
        
        # SMiData (level parameters) data
        self.smidata_blocks = []
        self.current_smidata_block = None
        self.smidata_entries = {}
        
        # Warp data
        self.warp_blocks = []
        self.current_warp_block = None
        self.warp_entries = {}
        
        self.create_ui()
    
    def create_ui(self):
        # ===== TOP BAR =====
        top_frame = tk.Frame(self.root, bg="#444", pady=8)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Main DAT File:", fg="white", bg="#444", 
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.lbl_file = tk.Label(top_frame, text="(none loaded)", fg="#aaa", bg="#444")
        self.lbl_file.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="Load .dat", command=self.load_dat_file).pack(side=tk.LEFT, padx=5)
        self.btn_scan = tk.Button(top_frame, text="Scan All", command=self.start_scan_thread, state="disabled")
        self.btn_scan.pack(side=tk.LEFT, padx=5)
        
        self.lbl_status = tk.Label(top_frame, text="Ready", fg="#0f0", bg="#444", font=("Consolas", 9))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)
        
        self.progress = ttk.Progressbar(top_frame, mode='indeterminate', length=100)
        
        # ===== NOTEBOOK (Tabs) =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_levels = tk.Frame(self.notebook)
        self.notebook.add(self.tab_levels, text="  Level Injector  ")
        self.create_level_tab()
        
        self.tab_params = tk.Frame(self.notebook)
        self.notebook.add(self.tab_params, text="  Level Parameters  ")
        self.create_params_tab()
        
        self.tab_lighting = tk.Frame(self.notebook)
        self.notebook.add(self.tab_lighting, text="  Lighting Editor  ")
        self.create_lighting_tab()
        
        self.tab_warp = tk.Frame(self.notebook)
        self.notebook.add(self.tab_warp, text="  Area Changes  ")
        self.create_warp_tab()
        
        self.tab_log = tk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text="  Log  ")
        self.create_log_tab()
    
    def create_level_tab(self):
        pane = tk.PanedWindow(self.tab_levels, orient=tk.HORIZONTAL, sashwidth=5)
        pane.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - level list
        left = tk.Frame(pane)
        pane.add(left, width=320)
        
        tk.Label(left, text="Levels (<loc> blocks):", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=5)
        
        list_frame = tk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.level_listbox = tk.Listbox(list_frame, font=("Courier", 9), 
                                         yscrollcommand=scroll.set, exportselection=False)
        self.level_listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.level_listbox.yview)
        self.level_listbox.bind('<<ListboxSelect>>', self.on_level_select)
        
        # Right panel - operations
        right = tk.Frame(pane)
        pane.add(right)
        
        info_frame = tk.LabelFrame(right, text="Selected Level", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.lbl_level_info = tk.Label(info_frame, text="Select a level from the list",
                                        font=("Consolas", 9), justify=tk.LEFT, anchor="w")
        self.lbl_level_info.pack(fill=tk.X)
        
        ops_frame = tk.LabelFrame(right, text="Operations", padx=10, pady=10)
        ops_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_row1 = tk.Frame(ops_frame)
        btn_row1.pack(fill=tk.X, pady=5)
        tk.Button(btn_row1, text="Extract Level to File", width=25, 
                  command=self.extract_level).pack(side=tk.LEFT, padx=5)
        
        btn_row2 = tk.Frame(ops_frame)
        btn_row2.pack(fill=tk.X, pady=5)
        tk.Button(btn_row2, text="Inject from .dat File", width=20, 
                  command=lambda: self.inject_level(False)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row2, text="Inject from .txt File", width=20, 
                  command=lambda: self.inject_level(True)).pack(side=tk.LEFT, padx=5)
        
        pad_frame = tk.Frame(ops_frame)
        pad_frame.pack(fill=tk.X, pady=5)
        tk.Label(pad_frame, text="Padding mode (if shorter):").pack(anchor="w")
        self.pad_mode = tk.StringVar(value="spaces_end")
        tk.Radiobutton(pad_frame, text="Spaces before </entityTree>", 
                       variable=self.pad_mode, value="spaces_end").pack(anchor="w")
        tk.Radiobutton(pad_frame, text="Spaces at end of content", 
                       variable=self.pad_mode, value="spaces_tail").pack(anchor="w")
        
        warn_frame = tk.Frame(ops_frame, bg="#fee", padx=5, pady=5)
        warn_frame.pack(fill=tk.X, pady=10)
        tk.Label(warn_frame, text="⚠️ Injection modifies main .dat directly!", 
                 bg="#fee", fg="red", font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Label(warn_frame, text="• Content longer than slot = REJECTED", 
                 bg="#fee", font=("Arial", 8)).pack(anchor="w")
        tk.Label(warn_frame, text="• Always keep a backup!", 
                 bg="#fee", font=("Arial", 8)).pack(anchor="w")
    
    def create_params_tab(self):
        top = tk.Frame(self.tab_params)
        top.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top, text="Level:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.smidata_var = tk.StringVar()
        self.smidata_combo = ttk.Combobox(top, textvariable=self.smidata_var, 
                                           state="disabled", width=40)
        self.smidata_combo.pack(side=tk.LEFT, padx=10)
        self.smidata_combo.bind("<<ComboboxSelected>>", self.on_smidata_change)
        
        tk.Button(top, text="Export Block", command=self.export_smidata_block).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Inject to Main DAT", command=self.inject_smidata_block).pack(side=tk.LEFT, padx=5)
        
        self.smidata_info = tk.Label(top, text="", fg="gray", font=("Arial", 8))
        self.smidata_info.pack(side=tk.RIGHT, padx=10)
        
        container = tk.Frame(self.tab_params)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.param_canvas = tk.Canvas(container)
        self.param_scrollbar = tk.Scrollbar(container, orient="vertical", 
                                             command=self.param_canvas.yview)
        self.param_scroll_frame = tk.Frame(self.param_canvas)
        
        self.param_scroll_frame.bind(
            "<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
        )
        
        self.param_canvas.create_window((0, 0), window=self.param_scroll_frame, anchor="nw")
        self.param_canvas.configure(yscrollcommand=self.param_scrollbar.set)
        
        self.param_canvas.pack(side="left", fill="both", expand=True)
        self.param_scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            self.param_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.param_canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def create_lighting_tab(self):
        top = tk.Frame(self.tab_lighting)
        top.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top, text="Stage:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.stage_var = tk.StringVar()
        self.stage_combo = ttk.Combobox(top, textvariable=self.stage_var, 
                                         state="disabled", width=35)
        self.stage_combo.pack(side=tk.LEFT, padx=10)
        self.stage_combo.bind("<<ComboboxSelected>>", self.on_stage_change)
        
        tk.Button(top, text="Export Stage Block", command=self.export_lighting_block).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Inject to Main DAT", command=self.inject_lighting_block).pack(side=tk.LEFT, padx=5)
        
        container = tk.Frame(self.tab_lighting)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.light_canvas = tk.Canvas(container)
        self.light_scrollbar = tk.Scrollbar(container, orient="vertical", 
                                             command=self.light_canvas.yview)
        self.light_scroll_frame = tk.Frame(self.light_canvas)
        
        self.light_scroll_frame.bind(
            "<Configure>",
            lambda e: self.light_canvas.configure(scrollregion=self.light_canvas.bbox("all"))
        )
        
        self.light_canvas.create_window((0, 0), window=self.light_scroll_frame, anchor="nw")
        self.light_canvas.configure(yscrollcommand=self.light_scrollbar.set)
        
        self.light_canvas.pack(side="left", fill="both", expand=True)
        self.light_scrollbar.pack(side="right", fill="y")
    
    def create_warp_tab(self):
        top = tk.Frame(self.tab_warp)
        top.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top, text="Level:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.warp_var = tk.StringVar()
        self.warp_combo = ttk.Combobox(top, textvariable=self.warp_var, 
                                        state="disabled", width=50)
        self.warp_combo.pack(side=tk.LEFT, padx=10)
        self.warp_combo.bind("<<ComboboxSelected>>", self.on_warp_change)
        
        tk.Button(top, text="Export Block", command=self.export_warp_block).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Inject to Main DAT", command=self.inject_warp_block).pack(side=tk.LEFT, padx=5)
        
        self.warp_info = tk.Label(top, text="", fg="gray", font=("Arial", 8))
        self.warp_info.pack(side=tk.RIGHT, padx=10)
        
        # Info frame explaining area change data
        info_frame = tk.LabelFrame(self.tab_warp, text="Area Change Data Info", padx=10, pady=5)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(info_frame, text="Controls map transitions when katamari reaches certain sizes.", 
                 font=("Arial", 9)).pack(anchor="w")
        tk.Label(info_frame, text="• s32CoreSize: Size (mm) that triggers the area change", 
                 font=("Arial", 8), fg="gray").pack(anchor="w")
        tk.Label(info_frame, text="• s16Map/s16Loc: Which maps and entity layouts to load (-1 = none)", 
                 font=("Arial", 8), fg="gray").pack(anchor="w")
        tk.Label(info_frame, text="• s16DeleteMap: Which maps to unload when transitioning", 
                 font=("Arial", 8), fg="gray").pack(anchor="w")
        
        # Scrollable parameter area
        container = tk.Frame(self.tab_warp)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.warp_canvas = tk.Canvas(container)
        self.warp_scrollbar = tk.Scrollbar(container, orient="vertical", 
                                            command=self.warp_canvas.yview)
        self.warp_scroll_frame = tk.Frame(self.warp_canvas)
        
        self.warp_scroll_frame.bind(
            "<Configure>",
            lambda e: self.warp_canvas.configure(scrollregion=self.warp_canvas.bbox("all"))
        )
        
        self.warp_canvas.create_window((0, 0), window=self.warp_scroll_frame, anchor="nw")
        self.warp_canvas.configure(yscrollcommand=self.warp_scrollbar.set)
        
        self.warp_canvas.pack(side="left", fill="both", expand=True)
        self.warp_scrollbar.pack(side="right", fill="y")
    
    def create_log_tab(self):
        self.log_text = scrolledtext.ScrolledText(self.tab_log, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def log(self, msg):
        # Thread-safe logging
        def do_log():
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, do_log)
    
    # =========================================================================
    # FILE LOADING
    # =========================================================================
    
    def load_dat_file(self):
        path = filedialog.askopenfilename(
            title="Select Main .dat File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if not path:
            return
        
        self.dat_path = path
        self.file_size = os.path.getsize(path)
        size_kb = self.file_size // 1024
        
        self.lbl_file.config(text=os.path.basename(path), fg="white")
        self.btn_scan.config(state="normal")
        
        if self.file_size == EXPECTED_FILE_SIZE:
            self.lbl_status.config(text=f"✓ {size_kb:,} KB (exact)", fg="#0f0")
            self.log(f"Loaded: {path}")
            self.log(f"Size: {self.file_size:,} bytes - EXACT MATCH")
        else:
            diff = self.file_size - EXPECTED_FILE_SIZE
            self.lbl_status.config(text=f"⚠ {size_kb:,} KB (diff: {diff:+,})", fg="orange")
            self.log(f"WARNING: Size differs by {diff:+,} bytes")
        
        self.log("Ready to scan. Press 'Scan All'.")
    
    def start_scan_thread(self):
        self.btn_scan.config(state="disabled")
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start()
        
        thread = threading.Thread(target=self.scan_all_worker)
        thread.daemon = True
        thread.start()
    
    def scan_all_worker(self):
        try:
            with open(self.dat_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    self.log("Scanning Levels (<loc>) starting from known offset...")
                    self.scan_levels_mmap(mm)
                    
                    self.log("Scanning Parameters (<SMiData>) in known range...")
                    self.scan_smidata_mmap(mm)
                    
                    self.log("Scanning Lighting (<SData>) in known range...")
                    self.scan_lighting_mmap(mm)
                    
                    self.log("Scanning Warp Data (<SWarpData>) in known range...")
                    self.scan_warp_mmap(mm)
            
            self.root.after(0, self.finish_scan)
            
        except Exception as e:
            self.log(f"ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.stop_progress)
    
    def stop_progress(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_scan.config(state="normal")
    
    def finish_scan(self):
        self.stop_progress()
        self.lbl_status.config(text="✓ Scan complete", fg="#0f0")
        
        self.refresh_level_list()
        
        stages = [b["stage"] for b in self.lighting_blocks]
        self.stage_combo.config(values=stages, state="readonly")
        if stages:
            self.stage_combo.current(0)
            self.on_stage_change(None)
        
        codes = [f"{b['code']} (idx:{b['params'].get('s8Index', '?')})" for b in self.smidata_blocks]
        self.smidata_combo.config(values=codes, state="readonly")
        if codes:
            self.smidata_combo.current(0)
            self.on_smidata_change(None)
        
        # Populate warp combo
        warp_names = [f"{b['name']} ({len(b['params'])} params)" for b in self.warp_blocks]
        self.warp_combo.config(values=warp_names, state="readonly")
        if warp_names:
            self.warp_combo.current(0)
            self.on_warp_change(None)
        
        self.log(f"Scan Complete: {len(self.level_offsets)} levels, {len(self.smidata_blocks)} params, {len(self.lighting_blocks)} lighting, {len(self.warp_blocks)} warps")
    
    # =========================================================================
    # SCANNING FUNCTIONS (Using known offsets for efficiency)
    # =========================================================================
    
    def scan_levels_mmap(self, mm):
        """Scan for <loc>...</loc> blocks starting from known offset"""
        self.level_offsets = []
        
        loc_start_sig = b'<loc>'
        loc_end_sig = b'</loc>'
        
        # Start scanning from known loc region
        pos = LOC_START
        count = 0
        
        while pos < len(mm):
            start = mm.find(loc_start_sig, pos)
            if start == -1:
                break
            
            end = mm.find(loc_end_sig, start)
            if end == -1:
                break
            
            content_start = start + len(loc_start_sig)
            content_end = end
            
            self.level_offsets.append({
                'loc_start': start,
                'content_start': content_start,
                'content_end': content_end,
                'loc_end': end + len(loc_end_sig),
                'content_length': content_end - content_start
            })
            
            count += 1
            pos = end + len(loc_end_sig)
            
            # Log progress every 10 levels
            if count % 10 == 0:
                self.log(f"  Found {count} levels...")
        
        self.log(f"  Total: {len(self.level_offsets)} <loc> blocks found")
    
    def scan_smidata_mmap(self, mm):
        """Scan for <SMiData.../> blocks in known range"""
        self.smidata_blocks = []
        
        start_sig = b'<SMiData'
        end_sig = b'/>'
        
        # Scan within known SMiData region for efficiency
        pos = SMIDATA_START
        end_limit = min(SMIDATA_END + 100000, len(mm))  # Some buffer
        
        while pos < end_limit:
            start = mm.find(start_sig, pos)
            if start == -1 or start > end_limit:
                break
            
            end = mm.find(end_sig, start)
            if end == -1:
                break
            
            block_end = end + len(end_sig)
            block_bytes = mm[start:block_end]
            
            try:
                block_text = block_bytes.decode('utf-8', errors='ignore')
            except:
                block_text = block_bytes.decode('latin-1')
            
            params = {}
            code = "Unknown"
            
            for k, v in re.findall(r'(\w+)\s*=\s*"(.*?)"', block_text):
                params[k] = v
                if k == "c8Code":
                    code = v
            
            self.smidata_blocks.append({
                "code": code,
                "start": start,
                "end": block_end,
                "text": block_text,
                "params": params
            })
            
            pos = block_end
        
        self.log(f"  Total: {len(self.smidata_blocks)} <SMiData> blocks found")
    
    def scan_lighting_mmap(self, mm):
        """Scan for <SData.../> blocks in known range"""
        self.lighting_blocks = []
        
        start_sig = b'<SData'
        end_sig = b'/>'
        
        # Scan within known SData region
        pos = SDATA_START
        end_limit = min(SDATA_END + 10000, len(mm))
        
        while pos < end_limit:
            start = mm.find(start_sig, pos)
            if start == -1 or start > end_limit:
                break
            
            end = mm.find(end_sig, start)
            if end == -1:
                break
            
            block_end = end + len(end_sig)
            block_bytes = mm[start:block_end]
            
            try:
                block_text = block_bytes.decode('utf-8', errors='ignore')
            except:
                block_text = block_bytes.decode('latin-1')
            
            inner = block_text
            
            params = []
            stage = "Unknown"
            
            for k, v in re.findall(r'(\w+)\s*=\s*"(.*?)"', inner):
                if k == "Stage":
                    stage = v
                parts = v.split()
                params.append({
                    "key": k,
                    "original": v,
                    "parts": parts,
                    "is_color": ("Color" in k or k == "Ambient"),
                    "is_dir": ("Dir" in k and len(parts) == 3)
                })
            
            self.lighting_blocks.append({
                "stage": stage,
                "start": start,
                "end": block_end,
                "text": block_text,
                "params": params
            })
            
            pos = block_end
        
        self.log(f"  Total: {len(self.lighting_blocks)} <SData> blocks found")
    
    def scan_warp_mmap(self, mm):
        """Scan for area change and warp data blocks in known range (0x298017 - 0x2A9958)
        
        Two formats exist:
        
        1. SGiAreaChangeData - Map transitions at size thresholds
           Parameters: s32CoreSize, s16Map, s16Loc, s16DeleteMap, etc.
        
        2. SGiMiWarp - Actual warp point positions  
           Parameters: fvPosi (XYZ position), s16InDir, s16OutDir, s16OutStage, 
                       f32FadeColor, s32CoreSize, s8SyncAreaChange
        """
        self.warp_blocks = []
        
        root_start_sig = b'<root>'
        root_end_sig = b'</root>'
        
        pos = WARP_START
        end_limit = min(WARP_END + 5000, len(mm))
        
        block_count = 0
        
        while pos < end_limit:
            root_start = mm.find(root_start_sig, pos)
            if root_start == -1 or root_start > end_limit:
                break
            
            root_end = mm.find(root_end_sig, root_start)
            if root_end == -1:
                break
            
            root_end = root_end + len(root_end_sig)
            
            block_bytes = mm[root_start:root_end]
            
            try:
                block_text = block_bytes.decode('utf-8', errors='ignore')
            except:
                block_text = block_bytes.decode('latin-1')
            
            # Look for comment above identifying the level
            search_start = max(0, root_start - 200)
            prefix_bytes = mm[search_start:root_start]
            try:
                prefix_text = prefix_bytes.decode('utf-8', errors='ignore')
            except:
                prefix_text = prefix_bytes.decode('latin-1')
            
            comment_match = re.search(r'<!--\s*(\S+)\s*-->', prefix_text)
            if comment_match:
                block_name = comment_match.group(1)
            else:
                block_name = f"Block_{block_count}"
            
            # Determine block type and parse entries
            entries = []
            block_type = "unknown"
            
            # Check for SGiAreaChangeData entries
            area_change_matches = list(re.finditer(r'<SGiAreaChangeData\s+(.*?)\s*/>', block_text, re.DOTALL))
            if area_change_matches:
                block_type = "area_change"
                for entry_match in area_change_matches:
                    entry_text = entry_match.group(0)
                    entry_inner = entry_match.group(1)
                    
                    entry_params = {}
                    for k, v in re.findall(r'(\w+)\s*=\s*"(.*?)"', entry_inner):
                        entry_params[k] = v
                    
                    entries.append({
                        "text": entry_text,
                        "params": entry_params,
                        "type": "area_change"
                    })
            
            # Check for SGiMiWarp entries
            warp_matches = list(re.finditer(r'<SGiMiWarp\s+(.*?)\s*/>', block_text, re.DOTALL))
            if warp_matches:
                block_type = "warp" if not area_change_matches else "mixed"
                for entry_match in warp_matches:
                    entry_text = entry_match.group(0)
                    entry_inner = entry_match.group(1)
                    
                    entry_params = {}
                    for k, v in re.findall(r'(\w+)\s*=\s*"(.*?)"', entry_inner):
                        entry_params[k] = v
                    
                    entries.append({
                        "text": entry_text,
                        "params": entry_params,
                        "type": "warp"
                    })
            
            self.warp_blocks.append({
                "name": block_name,
                "start": root_start,
                "end": root_end,
                "text": block_text,
                "prefix": prefix_text if comment_match else "",
                "entries": entries,
                "block_type": block_type,
                "params": {}
            })
            
            block_count += 1
            pos = root_end
        
        self.log(f"  Total: {len(self.warp_blocks)} area/warp block(s) found")
    
    def refresh_level_list(self):
        self.level_listbox.delete(0, tk.END)
        for i, info in enumerate(self.level_offsets):
            if i < len(LEVEL_NAMES):
                name = LEVEL_NAMES[i]
            else:
                name = f"(EXTRA #{i})"
            self.level_listbox.insert(tk.END, f"[{i}] {name} - {info['content_length']:,} bytes")
    
    # =========================================================================
    # LEVEL OPERATIONS
    # =========================================================================
    
    def on_level_select(self, event):
        sel = self.level_listbox.curselection()
        if not sel or not self.level_offsets:
            return
        
        idx = sel[0]
        info = self.level_offsets[idx]
        
        if idx < len(LEVEL_NAMES):
            name = LEVEL_NAMES[idx]
        else:
            name = f"(EXTRA #{idx})"
        
        self.lbl_level_info.config(text=f"""Level: {name}
Slot Index: {idx}
Content Start: {info['content_start']:,} (0x{info['content_start']:X})
Content End: {info['content_end']:,} (0x{info['content_end']:X})
Content Length: {info['content_length']:,} bytes""")
    
    def extract_level(self):
        sel = self.level_listbox.curselection()
        if not sel or not self.level_offsets:
            messagebox.showwarning("Warning", "Select a level first")
            return
        
        idx = sel[0]
        info = self.level_offsets[idx]
        
        if idx < len(LEVEL_NAMES):
            name = LEVEL_NAMES[idx]
        else:
            name = f"EXTRA_{idx}"
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            initialfile=f"{name}.dat",
            filetypes=[("DAT files", "*.dat"), ("Text files", "*.txt")]
        )
        
        if not save_path:
            return
        
        with open(self.dat_path, 'rb') as f:
            f.seek(info['content_start'])
            content = f.read(info['content_length'])
        
        with open(save_path, 'wb') as f:
            f.write(content)
        
        self.log(f"Extracted {name} ({len(content):,} bytes) -> {save_path}")
        messagebox.showinfo("Success", f"Extracted to:\n{save_path}")
    
    def inject_level(self, from_text=False):
        sel = self.level_listbox.curselection()
        if not sel or not self.level_offsets:
            messagebox.showwarning("Warning", "Select a target level slot")
            return
        
        idx = sel[0]
        info = self.level_offsets[idx]
        original_length = info['content_length']
        
        if idx < len(LEVEL_NAMES):
            name = LEVEL_NAMES[idx]
        else:
            name = f"(EXTRA #{idx})"
        
        filetypes = [("Text files", "*.txt"), ("DAT files", "*.dat")] if from_text else [("DAT files", "*.dat"), ("All", "*.*")]
        
        source_path = filedialog.askopenfilename(title="Select Level Data", filetypes=filetypes)
        if not source_path:
            return
        
        with open(source_path, 'rb') as f:
            new_content = f.read()
        
        new_length = len(new_content)
        
        self.log(f"Source: {new_length:,} bytes | Target: {original_length:,} bytes")
        
        if new_length > original_length:
            diff = new_length - original_length
            messagebox.showerror("Error", 
                f"Content is {diff:,} bytes TOO LONG!\n\n"
                f"Source: {new_length:,}\nTarget: {original_length:,}\n\n"
                "Cannot inject.")
            return
        
        # Pad if needed
        if new_length < original_length:
            diff = original_length - new_length
            self.log(f"Padding with {diff:,} spaces")
            
            if self.pad_mode.get() == "spaces_end":
                end_tag = b'</entityTree>'
                end_pos = new_content.rfind(end_tag)
                if end_pos != -1:
                    new_content = new_content[:end_pos] + (b' ' * diff) + new_content[end_pos:]
                else:
                    new_content = new_content + (b' ' * diff)
            else:
                new_content = new_content + (b' ' * diff)
        
        if len(new_content) != original_length:
            messagebox.showerror("Error", "Padding failed!")
            return
        
        if not messagebox.askyesno("Confirm", 
            f"Inject into {name} (slot {idx})?\n\n"
            f"Original: {original_length:,} bytes\n"
            f"New: {new_length:,} bytes (+ {original_length - new_length:,} padding)\n\n"
            f"This modifies the main .dat file.\nBackup recommended!"):
            return
        
        # Perform surgery
        with open(self.dat_path, 'r+b') as f:
            f.seek(info['content_start'])
            f.write(new_content)
        
        new_size = os.path.getsize(self.dat_path)
        self.log(f"✓ Injected {name}! File size: {new_size:,} bytes")
        
        if new_size == EXPECTED_FILE_SIZE:
            messagebox.showinfo("Success", "Level injected!\nFile size verified.")
        else:
            messagebox.showwarning("Warning", "Injected, but file size changed!")
    
    # =========================================================================
    # SMIDATA (LEVEL PARAMETERS) OPERATIONS
    # =========================================================================
    
    def on_smidata_change(self, event):
        idx = self.smidata_combo.current()
        if idx < 0 or idx >= len(self.smidata_blocks):
            return
        
        self.current_smidata_block = self.smidata_blocks[idx]
        self.build_smidata_ui(self.current_smidata_block)
        
        block = self.current_smidata_block
        self.smidata_info.config(text=f"Size: {len(block['text'])} chars | Offset: 0x{block['start']:X}")
    
    def build_smidata_ui(self, block):
        for w in self.param_scroll_frame.winfo_children():
            w.destroy()
        
        self.smidata_entries.clear()
        params = block["params"]
        
        categories = {
            "Basic Info": ["c8Code", "s8Index", "u8Enabled", "s8PlayerNum"],
            "Scoring": ["s32Rating_0", "s32Rating_1", "s32Rating_2", "s32BonusPoint", "s16BonusCategoryRate"],
            "Time & Goals": ["f32Time", "s32ShootingStarTime", "u32Target", "f32DispScaleCoef"],
            "Game Mode": ["u8Proc", "u8Eternal", "u8Modoki", "u8BonusCategory", "u8TgtMonoIdx"],
            "Display": ["s82dScale", "s82dCore", "s82dOujiBase", "u8UseCore", "u8ViewCore", "u8Scale2d"],
            "Environment": ["u8Fog", "u8Light", "u8Acc", "u8Camera", "s8Crumble"],
            "Messages": ["u8GameMessage", "u8LectureMessage", "u8ResultMessage"],
            "Maps & Scripts": ["u8MapScript_0", "u8MapScript_1", "u8MapScript_2", 
                              "u8LocScript_0", "u8LocScript_1", "u8LocScript_2"],
            "Other": ["u8Override", "u8Star", "u8NetworkRanking", "u8ClearOnlySpace",
                     "s8Present", "s8ChainEff", "s8SnowFlowerEff", "s16TgtMono",
                     "s16CoreInitID", "u8AriaNum", "s16MonoMdl", "s8Warp", "s8AreaChange"]
        }
        
        shown = set()
        
        for cat_name, cat_keys in categories.items():
            has_params = any(k in params for k in cat_keys)
            if not has_params:
                continue
            
            header = tk.Label(self.param_scroll_frame, text=f"━━━ {cat_name} ━━━",
                             font=("Arial", 10, "bold"), fg="#444")
            header.pack(fill=tk.X, pady=(10, 5), padx=5)
            
            for key in cat_keys:
                if key not in params:
                    continue
                shown.add(key)
                self.create_param_row(key, params[key])
        
        remaining = [k for k in params if k not in shown]
        if remaining:
            header = tk.Label(self.param_scroll_frame, text="━━━ Other ━━━",
                             font=("Arial", 10, "bold"), fg="#444")
            header.pack(fill=tk.X, pady=(10, 5), padx=5)
            for key in remaining:
                self.create_param_row(key, params[key])
    
    def create_param_row(self, key, value):
        frame = tk.Frame(self.param_scroll_frame, relief="groove", borderwidth=1)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        param_info = SMIDATA_PARAMS.get(key, {"desc": "", "type": "str"})
        
        key_label = tk.Label(frame, text=key, width=18, anchor="w", font=("Consolas", 9, "bold"))
        key_label.pack(side=tk.LEFT, padx=5)
        
        content = tk.Frame(frame)
        content.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        if "options" in param_info:
            row = tk.Frame(content)
            row.pack(anchor="w", fill=tk.X)
            
            entry = tk.Entry(row, width=8, font=("Consolas", 9))
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, padx=2)
            
            options = param_info["options"]
            try:
                current_int = int(value)
            except:
                current_int = 0
            option_text = options.get(current_int, "(unknown)")
            
            opt_label = tk.Label(row, text=f"→ {option_text}", fg="blue", font=("Arial", 8))
            opt_label.pack(side=tk.LEFT, padx=5)
            
            def update_option(event, e=entry, lbl=opt_label, opts=options):
                try:
                    v = int(e.get())
                    lbl.config(text=f"→ {opts.get(v, '(unknown)')}")
                except:
                    lbl.config(text="→ (invalid)")
            
            entry.bind("<KeyRelease>", update_option)
            self.smidata_entries[key] = {"widget": entry, "orig": value}
        
        elif len(value) > 30:
            entry = tk.Entry(content, width=60, font=("Consolas", 8))
            entry.insert(0, value)
            entry.pack(anchor="w", padx=2)
            self.smidata_entries[key] = {"widget": entry, "orig": value}
        
        else:
            entry = tk.Entry(content, width=max(12, len(value) + 4), font=("Consolas", 9))
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, padx=2)
            self.smidata_entries[key] = {"widget": entry, "orig": value}
        
        if param_info.get("desc"):
            desc = param_info["desc"]
            if len(desc) > 45:
                desc = desc[:42] + "..."
            desc_label = tk.Label(frame, text=f"? {desc}", fg="gray", font=("Arial", 7))
            desc_label.pack(side=tk.RIGHT, padx=5)
    
    def build_smidata_text(self, block):
        new_text = block["text"]
        
        for key, entry_info in self.smidata_entries.items():
            new_val = entry_info["widget"].get()
            orig_val = entry_info["orig"]
            
            if len(new_val) != len(orig_val):
                if len(new_val) < len(orig_val):
                    new_val = new_val + ' ' * (len(orig_val) - len(new_val))
                else:
                    new_val = new_val[:len(orig_val)]
            
            new_text = re.sub(
                f'({key}\\s*=\\s*").*?(")',
                lambda m, nv=new_val: m.group(1) + nv + m.group(2),
                new_text,
                count=1
            )
        
        return new_text
    
    def export_smidata_block(self):
        if not self.current_smidata_block:
            messagebox.showwarning("Warning", "Select a level first")
            return
        
        block = self.current_smidata_block
        new_text = self.build_smidata_text(block)
        
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"{block['code']}_params.txt"
        )
        
        if path:
            with open(path, "w") as f:
                f.write(new_text)
            self.log(f"Exported params: {block['code']} -> {path}")
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
    
    def inject_smidata_block(self):
        if not self.current_smidata_block or not self.dat_path:
            messagebox.showwarning("Warning", "Load DAT and select a level first")
            return
        
        block = self.current_smidata_block
        new_text = self.build_smidata_text(block)
        new_bytes = new_text.encode('utf-8')
        
        orig_len = block['end'] - block['start']
        
        if len(new_bytes) != orig_len:
            diff = orig_len - len(new_bytes)
            if diff > 0:
                new_text = new_text[:-2] + (' ' * diff) + new_text[-2:]
                new_bytes = new_text.encode('utf-8')
            else:
                messagebox.showerror("Error", f"New content is {-diff} bytes too long!")
                return
        
        if len(new_bytes) != orig_len:
            messagebox.showerror("Error", f"Length mismatch: {len(new_bytes)} vs {orig_len}")
            return
        
        if not messagebox.askyesno("Confirm", f"Inject params for '{block['code']}'?"):
            return
        
        with open(self.dat_path, 'r+b') as f:
            f.seek(block['start'])
            f.write(new_bytes)
        
        block["text"] = new_text
        self.log(f"✓ Injected params: {block['code']} at 0x{block['start']:X}")
        messagebox.showinfo("Success", "Parameters injected!")
    
    # =========================================================================
    # LIGHTING OPERATIONS
    # =========================================================================
    
    def on_stage_change(self, event):
        name = self.stage_var.get()
        self.current_lighting_block = next((b for b in self.lighting_blocks if b["stage"] == name), None)
        if self.current_lighting_block:
            self.build_lighting_ui(self.current_lighting_block["params"])
    
    def build_lighting_ui(self, params):
        for w in self.light_scroll_frame.winfo_children():
            w.destroy()
        
        self.lighting_entries.clear()
        self.color_buttons.clear()
        self.dir_canvases.clear()
        self.dir_sliders.clear()
        
        for item in params:
            key = item["key"]
            if key == "Stage":
                continue
            
            frame = tk.Frame(self.light_scroll_frame, relief="groove", borderwidth=1)
            frame.pack(fill=tk.X, padx=5, pady=3)
            
            tk.Label(frame, text=key, width=12, anchor="w", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
            
            content = tk.Frame(frame)
            content.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            row = tk.Frame(content)
            row.pack(anchor="w")
            
            ents = []
            vals = []
            
            for p in item["parts"]:
                e = tk.Entry(row, width=9)
                e.insert(0, p)
                e.pack(side=tk.LEFT, padx=2)
                ents.append({"widget": e, "orig": p})
                try:
                    vals.append(float(p))
                except:
                    vals.append(0.0)
            
            self.lighting_entries[key] = ents
            
            if item["is_color"] and len(vals) >= 3:
                btn = tk.Button(row, text="Pick", width=5, command=lambda k=key: self.pick_color(k))
                btn.config(bg=self.rgb_to_hex(vals[0], vals[1], vals[2]))
                btn.pack(side=tk.LEFT, padx=5)
                self.color_buttons[key] = btn
            
            if item["is_dir"] and len(vals) >= 3:
                ctrl = tk.Frame(content)
                ctrl.pack(fill=tk.X, pady=3)
                
                canvas = tk.Canvas(ctrl, width=40, height=40, bg="#ddd")
                canvas.pack(side=tk.LEFT, padx=5)
                self.dir_canvases[key] = canvas
                self.draw_arrow(canvas, vals[0], vals[1])
                
                slider_frame = tk.Frame(ctrl)
                slider_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                sliders = []
                for i, axis in enumerate("XYZ"):
                    row_s = tk.Frame(slider_frame)
                    row_s.pack(fill=tk.X)
                    tk.Label(row_s, text=axis, width=2).pack(side=tk.LEFT)
                    s = tk.Scale(row_s, from_=-2, to=2, resolution=0.01,
                                 orient=tk.HORIZONTAL, showvalue=0,
                                 command=lambda v, idx=i, k=key: self.move_dir(v, idx, k))
                    s.set(vals[i])
                    s.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    sliders.append(s)
                
                self.dir_sliders[key] = sliders
    
    def pick_color(self, key):
        c = colorchooser.askcolor()
        if not c[0]:
            return
        rgb = [v / 255 for v in c[0]]
        for i, e in enumerate(self.lighting_entries[key]):
            if i < 3:
                e["widget"].delete(0, tk.END)
                e["widget"].insert(0, f"{rgb[i]:.3f}")
        self.color_buttons[key].config(bg=c[1])
    
    def move_dir(self, val, idx, key):
        ent = self.lighting_entries[key][idx]
        ent["widget"].delete(0, tk.END)
        ent["widget"].insert(0, f"{float(val):.3f}")
        x = float(self.lighting_entries[key][0]["widget"].get())
        y = float(self.lighting_entries[key][1]["widget"].get())
        self.draw_arrow(self.dir_canvases[key], x, y)
    
    def draw_arrow(self, canvas, x, y):
        canvas.delete("all")
        cx, cy = 20, 20
        mag = math.hypot(x, y)
        if mag:
            x, y = x / mag * 15, y / mag * 15
        canvas.create_oval(cx-2, cy-2, cx+2, cy+2, fill="black")
        canvas.create_line(cx, cy, cx+x, cy-y, arrow=tk.LAST, width=2)
    
    def rgb_to_hex(self, r, g, b):
        return f"#{int(max(0,min(1,r))*255):02x}{int(max(0,min(1,g))*255):02x}{int(max(0,min(1,b))*255):02x}"
    
    def enforce_length(self, orig, val):
        s = f"{val:.6f}"
        if len(s) < len(orig):
            s += "0" * (len(orig) - len(s))
        return s[:len(orig)]
    
    def export_lighting_block(self):
        if not self.current_lighting_block:
            return
        block = self.current_lighting_block
        new_text = self.build_lighting_text(block)
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"{block['stage']}.txt")
        if path:
            with open(path, "w") as f:
                f.write(new_text)
            self.log(f"Exported lighting: {block['stage']} -> {path}")
    
    def build_lighting_text(self, block):
        new_text = block["text"]
        for p in block["params"]:
            key = p["key"]
            if key == "Stage":
                continue
            parts = []
            for e in self.lighting_entries[key]:
                try:
                    val = float(e["widget"].get())
                    parts.append(self.enforce_length(e["orig"], val))
                except:
                    parts.append(e["orig"])
            new_val = " ".join(parts)
            new_text = re.sub(f'({key}\\s*=\\s*").*?(")', lambda m: m.group(1) + new_val + m.group(2), new_text, count=1)
        return new_text
    
    def inject_lighting_block(self):
        if not self.current_lighting_block:
            return
        block = self.current_lighting_block
        new_text = self.build_lighting_text(block)
        new_bytes = new_text.encode('utf-8')
        orig_len = block['end'] - block['start']
        
        if len(new_bytes) != orig_len:
            messagebox.showerror("Error", f"Length mismatch: {len(new_bytes)} vs {orig_len}")
            return
        
        if not messagebox.askyesno("Confirm", f"Inject lighting for '{block['stage']}'?"):
            return
        
        with open(self.dat_path, 'r+b') as f:
            f.seek(block['start'])
            f.write(new_bytes)
        
        block["text"] = new_text
        self.log(f"✓ Injected lighting: {block['stage']} at 0x{block['start']:X}")
        messagebox.showinfo("Success", "Lighting injected!")
    
    # =========================================================================
    # WARP OPERATIONS
    # =========================================================================
    
    def on_warp_change(self, event):
        idx = self.warp_combo.current()
        if idx < 0 or idx >= len(self.warp_blocks):
            return
        
        self.current_warp_block = self.warp_blocks[idx]
        self.build_warp_ui(self.current_warp_block)
        
        block = self.current_warp_block
        self.warp_info.config(text=f"Size: {len(block['text']):,} chars | Offset: 0x{block['start']:X}")
    
    def build_warp_ui(self, block):
        for w in self.warp_scroll_frame.winfo_children():
            w.destroy()
        
        self.warp_entries.clear()
        
        # Header with block name and type
        block_type = block.get("block_type", "unknown")
        type_label = {"area_change": "Area Change", "warp": "Warp Points", "mixed": "Mixed", "unknown": "Unknown"}
        
        header = tk.Label(self.warp_scroll_frame, 
                         text=f"━━━ {block['name']} ({type_label.get(block_type, block_type)}) ━━━",
                         font=("Arial", 11, "bold"), fg="#444")
        header.pack(fill=tk.X, pady=(10, 5), padx=5)
        
        info = tk.Label(self.warp_scroll_frame, 
                       text=f"Offset: 0x{block['start']:X} - 0x{block['end']:X} ({block['end'] - block['start']:,} bytes)",
                       font=("Consolas", 8), fg="gray")
        info.pack(anchor="w", padx=5)
        
        entries = block.get("entries", [])
        
        if entries:
            for i, entry in enumerate(entries):
                params = entry["params"]
                entry_type = entry.get("type", "unknown")
                
                # Skip end marker entries
                if params.get("s32CoreSize") == "-1" and entry_type == "area_change":
                    continue
                
                if entry_type == "area_change":
                    self._build_area_change_entry(i, params)
                elif entry_type == "warp":
                    self._build_warp_entry(i, params)
        else:
            # Fallback to raw text
            header = tk.Label(self.warp_scroll_frame, 
                             text="Raw Data (edit with caution)",
                             font=("Arial", 10, "bold"), fg="#c00")
            header.pack(fill=tk.X, pady=10, padx=5)
            
            text_frame = tk.Frame(self.warp_scroll_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
            
            raw_text = scrolledtext.ScrolledText(text_frame, font=("Consolas", 8), 
                                                  width=100, height=30, wrap=tk.NONE)
            raw_text.insert(tk.END, block["text"])
            raw_text.pack(fill=tk.BOTH, expand=True)
            
            self.warp_entries["_raw_text"] = {"widget": raw_text, "orig": block["text"]}
    
    def _build_area_change_entry(self, i, params):
        """Build UI for SGiAreaChangeData entry"""
        entry_frame = tk.LabelFrame(self.warp_scroll_frame, 
                                   text=f"Area Change #{i} (CoreSize: {params.get('s32CoreSize', '?')}mm)",
                                   padx=10, pady=5, bg="#f0f8ff")
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Size parameters row
        size_frame = tk.Frame(entry_frame, bg="#f0f8ff")
        size_frame.pack(fill=tk.X, pady=2)
        tk.Label(size_frame, text="Sizes:", font=("Arial", 8, "bold"), width=8, anchor="w", bg="#f0f8ff").pack(side=tk.LEFT)
        
        size_params = ["s32CoreSize", "s32DeleteStartSize0", "s32DeleteStartSize", "s32DeleteMonoSize"]
        for key in size_params:
            if key in params:
                short_name = key.replace("s32", "").replace("Delete", "Del").replace("Start", "St")
                tk.Label(size_frame, text=f"{short_name}:", font=("Arial", 7), fg="gray", bg="#f0f8ff").pack(side=tk.LEFT)
                e = tk.Entry(size_frame, width=10, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "area_change"}
        
        # ID parameters row
        id_frame = tk.Frame(entry_frame, bg="#f0f8ff")
        id_frame.pack(fill=tk.X, pady=2)
        tk.Label(id_frame, text="IDs:", font=("Arial", 8, "bold"), width=8, anchor="w", bg="#f0f8ff").pack(side=tk.LEFT)
        
        for key in ["s8CoreID", "s16Mdl"]:
            if key in params:
                tk.Label(id_frame, text=f"{key.replace('s8','').replace('s16','')}:", font=("Arial", 7), fg="gray", bg="#f0f8ff").pack(side=tk.LEFT)
                e = tk.Entry(id_frame, width=6, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "area_change"}
        
        # Map parameters row
        map_frame = tk.Frame(entry_frame, bg="#f0f8ff")
        map_frame.pack(fill=tk.X, pady=2)
        tk.Label(map_frame, text="Maps:", font=("Arial", 8, "bold"), width=8, anchor="w", bg="#f0f8ff").pack(side=tk.LEFT)
        
        for key in ["s16DeleteMap", "s16Map", "s16Loc"]:
            if key in params:
                tk.Label(map_frame, text=f"{key.replace('s16','')}:", font=("Arial", 7), fg="gray", bg="#f0f8ff").pack(side=tk.LEFT)
                e = tk.Entry(map_frame, width=8, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "area_change"}
        
        # Other parameters row
        other_frame = tk.Frame(entry_frame, bg="#f0f8ff")
        other_frame.pack(fill=tk.X, pady=2)
        tk.Label(other_frame, text="Other:", font=("Arial", 8, "bold"), width=8, anchor="w", bg="#f0f8ff").pack(side=tk.LEFT)
        
        for key in ["s8WarpID", "s8ChangeType", "s8FogID"]:
            if key in params:
                tk.Label(other_frame, text=f"{key.replace('s8','')}:", font=("Arial", 7), fg="gray", bg="#f0f8ff").pack(side=tk.LEFT)
                e = tk.Entry(other_frame, width=8, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "area_change"}
    
    def _build_warp_entry(self, i, params):
        """Build UI for SGiMiWarp entry"""
        entry_frame = tk.LabelFrame(self.warp_scroll_frame, 
                                   text=f"Warp Point #{i}",
                                   padx=10, pady=5, bg="#fff0f5")
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Position row (fvPosi)
        if "fvPosi" in params:
            pos_frame = tk.Frame(entry_frame, bg="#fff0f5")
            pos_frame.pack(fill=tk.X, pady=2)
            tk.Label(pos_frame, text="Position:", font=("Arial", 8, "bold"), width=10, anchor="w", bg="#fff0f5").pack(side=tk.LEFT)
            
            pos_parts = params["fvPosi"].split()
            for j, (label, val) in enumerate(zip(["X:", "Y:", "Z:"], pos_parts)):
                tk.Label(pos_frame, text=label, font=("Arial", 7), fg="gray", bg="#fff0f5").pack(side=tk.LEFT)
                e = tk.Entry(pos_frame, width=10, font=("Consolas", 9))
                e.insert(0, val)
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_fvPosi_{j}"] = {"widget": e, "orig": val, "entry_idx": i, "type": "warp", "is_position": True, "pos_idx": j}
        
        # Direction row
        dir_frame = tk.Frame(entry_frame, bg="#fff0f5")
        dir_frame.pack(fill=tk.X, pady=2)
        tk.Label(dir_frame, text="Direction:", font=("Arial", 8, "bold"), width=10, anchor="w", bg="#fff0f5").pack(side=tk.LEFT)
        
        for key in ["s16InDir", "s16OutDir"]:
            if key in params:
                tk.Label(dir_frame, text=f"{key.replace('s16','')}:", font=("Arial", 7), fg="gray", bg="#fff0f5").pack(side=tk.LEFT)
                e = tk.Entry(dir_frame, width=6, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "warp"}
        
        # Stage row
        stage_frame = tk.Frame(entry_frame, bg="#fff0f5")
        stage_frame.pack(fill=tk.X, pady=2)
        tk.Label(stage_frame, text="Stage:", font=("Arial", 8, "bold"), width=10, anchor="w", bg="#fff0f5").pack(side=tk.LEFT)
        
        for key in ["s16OutStage", "s8OutStageFlag"]:
            if key in params:
                tk.Label(stage_frame, text=f"{key.replace('s16','').replace('s8','')}:", font=("Arial", 7), fg="gray", bg="#fff0f5").pack(side=tk.LEFT)
                e = tk.Entry(stage_frame, width=8, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "warp"}
        
        # Fade color row (f32FadeColor)
        if "f32FadeColor" in params:
            fade_frame = tk.Frame(entry_frame, bg="#fff0f5")
            fade_frame.pack(fill=tk.X, pady=2)
            tk.Label(fade_frame, text="Fade RGBA:", font=("Arial", 8, "bold"), width=10, anchor="w", bg="#fff0f5").pack(side=tk.LEFT)
            
            fade_parts = params["f32FadeColor"].split()
            for j, (label, val) in enumerate(zip(["R:", "G:", "B:", "A:"], fade_parts)):
                tk.Label(fade_frame, text=label, font=("Arial", 7), fg="gray", bg="#fff0f5").pack(side=tk.LEFT)
                e = tk.Entry(fade_frame, width=6, font=("Consolas", 9))
                e.insert(0, val)
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_f32FadeColor_{j}"] = {"widget": e, "orig": val, "entry_idx": i, "type": "warp", "is_fade": True, "fade_idx": j}
        
        # Other params row
        other_frame = tk.Frame(entry_frame, bg="#fff0f5")
        other_frame.pack(fill=tk.X, pady=2)
        tk.Label(other_frame, text="Other:", font=("Arial", 8, "bold"), width=10, anchor="w", bg="#fff0f5").pack(side=tk.LEFT)
        
        for key in ["s32CoreSize", "s8SyncAreaChange"]:
            if key in params:
                tk.Label(other_frame, text=f"{key.replace('s32','').replace('s8','')}:", font=("Arial", 7), fg="gray", bg="#fff0f5").pack(side=tk.LEFT)
                e = tk.Entry(other_frame, width=8, font=("Consolas", 9))
                e.insert(0, params[key])
                e.pack(side=tk.LEFT, padx=2)
                self.warp_entries[f"{i}_{key}"] = {"widget": e, "orig": params[key], "entry_idx": i, "type": "warp"}
    
    def _is_float(self, s):
        try:
            float(s)
            return True
        except:
            return False
    
    def build_warp_text(self, block):
        """Build modified warp/area change block text with current UI values"""
        if "_raw_text" in self.warp_entries:
            return self.warp_entries["_raw_text"]["widget"].get("1.0", tk.END).rstrip('\n')
        
        new_text = block["text"]
        entries = block.get("entries", [])
        
        for i, entry in enumerate(entries):
            old_entry_text = entry["text"]
            new_entry_text = old_entry_text
            
            # Handle position components (fvPosi)
            if f"{i}_fvPosi_0" in self.warp_entries:
                pos_parts = []
                for j in range(3):
                    key = f"{i}_fvPosi_{j}"
                    if key in self.warp_entries:
                        pos_parts.append(self.warp_entries[key]["widget"].get())
                if len(pos_parts) == 3:
                    orig_posi = entry["params"].get("fvPosi", "")
                    new_posi = " ".join(pos_parts)
                    # Enforce length
                    if len(new_posi) < len(orig_posi):
                        new_posi = new_posi + ' ' * (len(orig_posi) - len(new_posi))
                    elif len(new_posi) > len(orig_posi):
                        new_posi = new_posi[:len(orig_posi)]
                    new_entry_text = re.sub(
                        r'(fvPosi\s*=\s*").*?(")',
                        lambda m: m.group(1) + new_posi + m.group(2),
                        new_entry_text, count=1
                    )
            
            # Handle fade color components (f32FadeColor)
            if f"{i}_f32FadeColor_0" in self.warp_entries:
                fade_parts = []
                for j in range(4):
                    key = f"{i}_f32FadeColor_{j}"
                    if key in self.warp_entries:
                        fade_parts.append(self.warp_entries[key]["widget"].get())
                if len(fade_parts) == 4:
                    orig_fade = entry["params"].get("f32FadeColor", "")
                    new_fade = " ".join(fade_parts)
                    if len(new_fade) < len(orig_fade):
                        new_fade = new_fade + ' ' * (len(orig_fade) - len(new_fade))
                    elif len(new_fade) > len(orig_fade):
                        new_fade = new_fade[:len(orig_fade)]
                    new_entry_text = re.sub(
                        r'(f32FadeColor\s*=\s*").*?(")',
                        lambda m: m.group(1) + new_fade + m.group(2),
                        new_entry_text, count=1
                    )
            
            # Handle regular parameters
            for key, orig_val in entry["params"].items():
                if key in ["fvPosi", "f32FadeColor"]:
                    continue  # Already handled above
                
                entry_key = f"{i}_{key}"
                if entry_key in self.warp_entries:
                    new_val = self.warp_entries[entry_key]["widget"].get()
                    orig_val = self.warp_entries[entry_key]["orig"]
                    
                    if len(new_val) < len(orig_val):
                        new_val = new_val + ' ' * (len(orig_val) - len(new_val))
                    elif len(new_val) > len(orig_val):
                        new_val = new_val[:len(orig_val)]
                    
                    new_entry_text = re.sub(
                        f'({key}\\s*=\\s*").*?(")',
                        lambda m, nv=new_val: m.group(1) + nv + m.group(2),
                        new_entry_text, count=1
                    )
            
            new_text = new_text.replace(old_entry_text, new_entry_text)
            entry["text"] = new_entry_text
        
        return new_text
    
    def export_warp_block(self):
        if not self.current_warp_block:
            messagebox.showwarning("Warning", "Select a warp block first")
            return
        
        block = self.current_warp_block
        new_text = self.build_warp_text(block)
        
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"{block['name'].replace(' ', '_')}_warp.txt"
        )
        
        if path:
            with open(path, "w") as f:
                f.write(new_text)
            self.log(f"Exported warp: {block['name']} -> {path}")
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
    
    def inject_warp_block(self):
        if not self.current_warp_block or not self.dat_path:
            messagebox.showwarning("Warning", "Load DAT and select a warp block first")
            return
        
        block = self.current_warp_block
        new_text = self.build_warp_text(block)
        new_bytes = new_text.encode('utf-8')
        
        orig_len = block['end'] - block['start']
        
        if len(new_bytes) != orig_len:
            diff = orig_len - len(new_bytes)
            if diff > 0:
                # Pad with spaces
                new_bytes = new_bytes + (b' ' * diff)
            else:
                messagebox.showerror("Error", 
                    f"New content is {-diff} bytes too long!\n"
                    f"Original: {orig_len:,} bytes\n"
                    f"New: {len(new_bytes):,} bytes")
                return
        
        if len(new_bytes) != orig_len:
            messagebox.showerror("Error", f"Length mismatch: {len(new_bytes)} vs {orig_len}")
            return
        
        if not messagebox.askyesno("Confirm", 
            f"Inject warp data for '{block['name']}'?\n\n"
            f"This will modify {orig_len:,} bytes at offset 0x{block['start']:X}"):
            return
        
        with open(self.dat_path, 'r+b') as f:
            f.seek(block['start'])
            f.write(new_bytes)
        
        block["text"] = new_text
        self.log(f"✓ Injected warp: {block['name']} at 0x{block['start']:X}")
        messagebox.showinfo("Success", "Warp data injected!")


# =============================================================================
# MAIN
# =============================================================================

def main():
    root = tk.Tk()
    app = KatamariDatEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()