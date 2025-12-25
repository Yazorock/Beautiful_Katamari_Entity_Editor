import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import csv
import math
import matplotlib
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d 
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

matplotlib.use("TkAgg")

class KatamariEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Katamari Editor 17.0 - Enhanced Vis & Layout")
        self.root.geometry("1600x1000")

        # --- Data & State ---
        self.entities = []
        self.item_db = {} 
        self.file_sequence = [] 
        self.display_mapping = [] 
        self.selected_indices = []
        self.highlights = [None, None, None, None]
        self.is_updating_ui = False 
        
        self.pos_buffer = {"all": None, "x": None, "y": None, "z": None}
        self.offset_mode = tk.BooleanVar(value=False)
        self.dirty_fields = set()
        self.last_sort = None
        self.sort_reverse = False
        
        # --- Plane Management ---
        self.planes = []  # List of dicts: {"name": str, "coeffs": (a, b, c, d), "points": []}
        
        # --- Visualization Variables ---
        self.select_mode = tk.StringVar(value="CLICK") 
        self.viz_mode = tk.StringVar(value="Standard") 
        self.entity_opacity = tk.DoubleVar(value=0.4)
        self.brush_size = tk.DoubleVar(value=25.0)
        self.color_radius = tk.DoubleVar(value=1.0) 
        self.depth_shading = tk.BooleanVar(value=True)
        self.use_size_scaling = tk.BooleanVar(value=False)
        
        # --- Size Filter Variables ---
        self.size_filter_min = tk.DoubleVar(value=0.0)
        self.size_filter_max = tk.DoubleVar(value=10000.0)
        self.size_filter_enabled = tk.BooleanVar(value=False)
        
        self.is_dragging = False
        self.drag_start = None 
        self.rect_patch = None
        self.active_ax = None

        self.slice_axis = tk.StringVar(value="None")
        self.slice_depth = tk.DoubleVar(value=0.0)
        self.slice_thickness = tk.DoubleVar(value=20.0)
        # Default bounds to prevent crash if no file loaded
        self.axis_bounds = {'x':(-100,100), 'y':(-100,100), 'z':(-100,100)} 
        self.pos_sliders = []

        # --- UI Config ---
        self.batch_side = tk.StringVar(value="Right")
        self.pos_side = tk.StringVar(value="Right")
        self.tool_frames = {"batch": None, "pos": None}
        
        # --- Batch Editor Vars ---
        self.pos_vars = [tk.DoubleVar() for _ in range(3)]
        self.rot_vars = [tk.DoubleVar() for _ in range(4)]

        # --- Layout Structure ---
        self.create_menu()
        
        # 3-Pane Layout: Left | Middle (Graph) | Right
        self.main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=6, bg="#777")
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        # 1. Left Col
        self.col_left = tk.Frame(self.main_pane, bg="#ddd")
        self.main_pane.add(self.col_left, width=320, minsize=250)

        # 2. Middle Col (Graph + Tools if selected)
        self.col_mid = tk.Frame(self.main_pane)
        self.main_pane.add(self.col_mid, stretch="always", minsize=400)

        # 3. Right Col
        self.col_right = tk.Frame(self.main_pane, bg="#eee")
        self.main_pane.add(self.col_right, width=300, minsize=50)

        # --- Left Panel Content ---
        self._build_left_panel()

        # --- Middle Panel Content (Graph) ---
        self.info_frame = tk.Frame(self.col_mid, bg="#333", pady=8)
        self.info_frame.pack(fill=tk.X, side=tk.TOP)
        self.lbl_info = tk.Label(self.info_frame, text="Ready", fg="#00FF00", bg="#333", font=("Consolas", 10, "bold"), justify=tk.LEFT)
        self.lbl_info.pack(anchor="w", padx=10)

        self.graph_container = tk.Frame(self.col_mid)
        self.graph_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tool_frame = tk.Frame(self.graph_container, bg="#ccc", pady=2)
        tool_frame.pack(fill=tk.X)
        
        # Visualization Controls
        viz_row1 = tk.Frame(tool_frame, bg="#ccc")
        viz_row1.pack(fill=tk.X, pady=1)
        
        tk.Label(viz_row1, text="Color:", bg="#ccc", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=5)
        for m in ["Standard", "XYZ", "Logic", "ID", "Size", "Hierarchy"]:
            tk.Radiobutton(viz_row1, text=m, variable=self.viz_mode, value=m, bg="#ccc", command=self.plot_all).pack(side=tk.LEFT)
            
        tk.Label(viz_row1, text="| Size By CSV:", bg="#ccc", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=(10,2))
        tk.Checkbutton(viz_row1, variable=self.use_size_scaling, bg="#ccc", command=self.plot_all).pack(side=tk.LEFT)

        viz_row2 = tk.Frame(tool_frame, bg="#ccc")
        viz_row2.pack(fill=tk.X, pady=1)
        
        tk.Label(viz_row2, text="Rad:", bg="#ccc").pack(side=tk.LEFT, padx=5)
        tk.Scale(viz_row2, from_=0.1, to=10.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.color_radius, showvalue=0, bg="#ccc", length=60, command=lambda v: self.plot_all()).pack(side=tk.LEFT)

        tk.Label(viz_row2, text="Alpha:", bg="#ccc").pack(side=tk.LEFT, padx=5)
        tk.Scale(viz_row2, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.entity_opacity, showvalue=0, bg="#ccc", length=60, command=lambda v: self.plot_all()).pack(side=tk.LEFT)

        tk.Checkbutton(viz_row2, text="Depth Fog", variable=self.depth_shading, bg="#ccc", command=self.plot_all).pack(side=tk.LEFT, padx=10)

        tk.Label(viz_row2, text="| Select:", bg="#ccc").pack(side=tk.LEFT, padx=(10,0))
        for m in ["CLICK", "PAINT"]:
            tk.Radiobutton(viz_row2, text=m.title(), variable=self.select_mode, value=m, bg="#ccc").pack(side=tk.LEFT)

        # Matplotlib Setup
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.ax3d = self.figure.add_subplot(111, projection='3d')
        self.ax3d.set_visible(True)
        
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_container); self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_container)
        
        self.canvas.mpl_connect('pick_event', self.on_graph_pick)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_down)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_up)

        # --- Dynamic Tool Construction ---
        self.refresh_ui_layout()
        self.view_state = {'3d': None}

    def _build_left_panel(self):
        # --- Plane Manager UI ---
        plane_frame = tk.LabelFrame(self.col_left, text="Plane Manager (Max 5)", bg="#ddd", padx=5, pady=5)
        plane_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.plane_listbox = tk.Listbox(plane_frame, height=5, font=("Courier", 9))
        self.plane_listbox.pack(fill=tk.X, pady=2)
        self.plane_listbox.bind('<<ListboxSelect>>', lambda e: self.plot_all())
        
        p_btns = tk.Frame(plane_frame, bg="#ddd")
        p_btns.pack(fill=tk.X)
        tk.Button(p_btns, text="Add Plane (Select 3-5)", command=self.create_plane_from_selection, bg="#4CAF50", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        tk.Button(p_btns, text="Delete", command=self.delete_selected_plane, bg="#f44336", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        
        tk.Button(plane_frame, text="SNAP SELECTION TO PLANE", command=self.snap_to_plane, bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=(4,2))

        # --- Size Filter UI ---
        size_filter_frame = tk.LabelFrame(self.col_left, text="Size Filter (mm)", bg="#ddd", padx=5, pady=5)
        size_filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Checkbutton(size_filter_frame, text="Enable Size Filter", variable=self.size_filter_enabled, bg="#ddd", command=self.on_size_filter_change).pack(anchor="w")
        
        tk.Label(size_filter_frame, text="Min Size:", bg="#ddd").pack(anchor="w")
        self.scale_size_min = tk.Scale(size_filter_frame, from_=0, to=10000, orient=tk.HORIZONTAL, variable=self.size_filter_min, showvalue=1, resolution=10, command=lambda v: self.on_size_filter_change())
        self.scale_size_min.pack(fill=tk.X)
        
        tk.Label(size_filter_frame, text="Max Size:", bg="#ddd").pack(anchor="w")
        self.scale_size_max = tk.Scale(size_filter_frame, from_=0, to=10000, orient=tk.HORIZONTAL, variable=self.size_filter_max, showvalue=1, resolution=10, command=lambda v: self.on_size_filter_change())
        self.scale_size_max.pack(fill=tk.X)

        # --- Sorting UI ---
        sort_frame = tk.LabelFrame(self.col_left, text="Sort Items", bg="#ddd", padx=5, pady=5)
        sort_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(sort_frame, text="Name", command=lambda: self.sort_entities("NAME")).grid(row=0, column=0, sticky="ew")
        tk.Button(sort_frame, text="Size", command=lambda: self.sort_entities("SIZE")).grid(row=0, column=1, sticky="ew")
        tk.Button(sort_frame, text="Atk", command=lambda: self.sort_entities("ATK")).grid(row=1, column=0, sticky="ew")
        tk.Button(sort_frame, text="Mov", command=lambda: self.sort_entities("MOV")).grid(row=1, column=1, sticky="ew")
        tk.Button(sort_frame, text="RESET", command=self.reset_sort).grid(row=2, column=0, columnspan=2, sticky="ew")
        sort_frame.columnconfigure(0, weight=1); sort_frame.columnconfigure(1, weight=1)

        # --- Slicing UI ---
        slice_frame = tk.LabelFrame(self.col_left, text="Filter & Slice", bg="#ddd", padx=5, pady=5)
        slice_frame.pack(fill=tk.X, padx=5, pady=5)
        
        cb_slice = ttk.Combobox(slice_frame, textvariable=self.slice_axis, state="readonly", 
                                values=["None", "Y-Axis (Height)", "Z-Axis (Depth)", "X-Axis (Width)"])
        cb_slice.pack(fill=tk.X, pady=2)
        cb_slice.bind("<<ComboboxSelected>>", self.on_slice_axis_change)
        
        self.scale_depth = tk.Scale(slice_frame, label="Position", orient=tk.HORIZONTAL, variable=self.slice_depth, showvalue=1, command=lambda v: self.on_slice_update())
        self.scale_depth.pack(fill=tk.X)
        self.scale_thick = tk.Scale(slice_frame, label="Thickness", from_=0.5, to=75.0, orient=tk.HORIZONTAL, variable=self.slice_thickness, resolution=0.5, command=lambda v: self.on_slice_update())
        self.scale_thick.pack(fill=tk.X)

        self.entity_listbox = tk.Listbox(self.col_left, font=("Courier", 9), selectmode=tk.EXTENDED, exportselection=False)
        self.entity_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.entity_listbox.bind('<<ListboxSelect>>', self.on_list_select)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load CSV Database...", command=self.load_csv)
        file_menu.add_command(label="Load Map (.dat)...", command=self.load_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Map...", command=self.save_map_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # --- View Menu ---
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        batch_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Batch Editor Location", menu=batch_menu)
        for loc in ["Left", "Middle", "Right"]:
            batch_menu.add_radiobutton(label=loc, variable=self.batch_side, value=loc, command=self.refresh_ui_layout)
        
        pos_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Position Tools Location", menu=pos_menu)
        for loc in ["Left", "Middle", "Right"]:
            pos_menu.add_radiobutton(label=loc, variable=self.pos_side, value=loc, command=self.refresh_ui_layout)

    def refresh_ui_layout(self):
        # Clear old frames if they exist
        if self.tool_frames["pos"]: self.tool_frames["pos"].destroy()
        if self.tool_frames["batch"]: self.tool_frames["batch"].destroy()
        
        def get_parent(loc_str):
            if loc_str == "Left": return self.col_left
            if loc_str == "Middle": return self.col_mid
            return self.col_right
        
        # Position Tools
        pos_parent = get_parent(self.pos_side.get())
        self.tool_frames["pos"] = self.build_position_tools(pos_parent)
        # If middle, pack at bottom of middle col. If others, pack at top.
        side_pack = tk.BOTTOM if self.pos_side.get() == "Middle" else tk.TOP
        self.tool_frames["pos"].pack(fill=tk.X, padx=10, pady=2, side=side_pack)
        
        # Batch Editor
        batch_parent = get_parent(self.batch_side.get())
        self.tool_frames["batch"] = self.build_batch_editor(batch_parent)
        # If middle, pack above Position tools (if also bottom) or just bottom
        side_pack = tk.BOTTOM if self.batch_side.get() == "Middle" else tk.TOP
        self.tool_frames["batch"].pack(fill=tk.X, padx=10, pady=5, side=side_pack)

    def build_position_tools(self, parent):
        clip_frame = tk.LabelFrame(parent, text="Position Tools", padx=5, pady=5)
        
        c_row = tk.Frame(clip_frame); c_row.pack(fill=tk.X)
        tk.Label(c_row, text="COPY:", width=6, anchor="e").pack(side=tk.LEFT)
        tk.Button(c_row, text="All", command=lambda: self.copy_pos("all"), bg="#2196F3", fg="white", width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(c_row, text="X", command=lambda: self.copy_pos("x"), bg="#555", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(c_row, text="Y", command=lambda: self.copy_pos("y"), bg="#555", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(c_row, text="Z", command=lambda: self.copy_pos("z"), bg="#555", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        
        p_row = tk.Frame(clip_frame); p_row.pack(fill=tk.X, pady=(2,0))
        tk.Label(p_row, text="PASTE:", width=6, anchor="e").pack(side=tk.LEFT)
        tk.Button(p_row, text="All", command=lambda: self.paste_pos("all"), bg="#9C27B0", fg="white", width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(p_row, text="X", command=lambda: self.paste_pos("x"), bg="#777", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(p_row, text="Y", command=lambda: self.paste_pos("y"), bg="#777", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(p_row, text="Z", command=lambda: self.paste_pos("z"), bg="#777", fg="white", width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(p_row, text="SWAP", command=self.swap_positions, bg="#E91E63", fg="white", font=("Arial", 8, "bold"), width=6).pack(side=tk.RIGHT, padx=5)
        return clip_frame

    def build_batch_editor(self, parent):
        editor_frame = tk.LabelFrame(parent, text="Batch Editor", padx=10, pady=5)
        tk.Checkbutton(editor_frame, text="OFFSET MODE", variable=self.offset_mode, command=self.on_offset_toggle, font=("Arial", 9, "bold")).pack(anchor="w")
        
        r1 = tk.Frame(editor_frame); r1.pack(fill=tk.X)
        r2 = tk.Frame(editor_frame); r2.pack(fill=tk.X)
        r3 = tk.Frame(editor_frame); r3.pack(fill=tk.X)
        r4 = tk.Frame(editor_frame); r4.pack(fill=tk.X)
        r5 = tk.Frame(editor_frame); r5.pack(fill=tk.X)
        
        def qe(p, l, t):
            f = tk.Frame(p); f.pack(side=tk.LEFT, padx=5); tk.Label(f, text=l).pack(side=tk.LEFT)
            e = tk.Entry(f, width=8); e.pack(side=tk.LEFT)
            e.bind("<KeyRelease>", lambda ev: self.dirty_fields.add(t))
            return e
        
        self.entry_index = qe(r1, "Index:", "id")
        self.entry_attack = qe(r1, "Atk:", "atk")
        self.entry_move = qe(r1, "Mov:", "mov")
        self.entry_escape = qe(r1, "Esc:", "esc")
        self.entry_speed = qe(r2, "Speed:", "spd")
        self.entry_path = qe(r2, "PathID:", "pth")
        
        # Row 3: Scale, Plus Type, Plus Fly Height
        self.entry_scale = qe(r3, "Scale:", "scale")
        self.entry_plus_type = qe(r3, "PlusType:", "plus_type")
        self.entry_plus_fly_height = qe(r3, "PlusFlyH:", "plus_fly_height")
        
        # Row 4: Plus Roll Speed, Plus Angle
        self.entry_plus_roll_speed = qe(r4, "PlusRollSpd:", "plus_roll_speed")
        self.entry_plus_angle = qe(r4, "PlusAngle:", "plus_angle")
        
        # Row 5: Parent Type
        self.entry_parent_type = qe(r5, "ParentType:", "parent_type")

        slide_container = tk.Frame(editor_frame); slide_container.pack(fill=tk.X, pady=5)
        self.pos_sliders = [] 

        def make_sliders(parent, title, vars, labels, tag_prefix, is_pos=False):
            lf = tk.LabelFrame(parent, text=title); lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            limit = 333 if is_pos else 1.0 
            for i, v in enumerate(vars):
                r = tk.Frame(lf); r.pack(fill=tk.X); tk.Label(r, text=labels[i], width=2).pack(side=tk.LEFT)
                s = tk.Scale(r, from_=-limit, to=limit, orient=tk.HORIZONTAL, variable=v, showvalue=0, resolution=0.000001, command=lambda val, t=f"{tag_prefix}_{i}": self.on_slider_move(t))
                s.pack(side=tk.LEFT, fill=tk.X, expand=True)
                if is_pos: self.pos_sliders.append(s)
                s.bind("<ButtonRelease-1>", lambda ev, t=f"{tag_prefix}_{i}": self.dirty_fields.add(t))
                tk.Entry(r, textvariable=v, width=12).pack(side=tk.LEFT)

        make_sliders(slide_container, "Position", self.pos_vars, ["X","Y","Z"], "pos", True)
        make_sliders(slide_container, "Rotation", self.rot_vars, ["W","X","Y","Z"], "rot")
        
        tk.Button(editor_frame, text="COMMIT CHANGES", command=self.commit_batch_changes, bg="#FF5722", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        
        if self.selected_indices: self.update_editor_fields()
        return editor_frame

    # --- Plane Logic ---
    def create_plane_from_selection(self):
        if not (3 <= len(self.selected_indices) <= 5):
            messagebox.showwarning("Error", "Select 3 to 5 entities to define a plane.")
            return
        if len([p for p in self.planes if not p.get("auto", False)]) >= 5:
            messagebox.showwarning("Limit", "Maximum of 5 planes allowed.")
            return

        pts = np.array([[self.entities[i]['x'], self.entities[i]['z'], self.entities[i]['y']] for i in self.selected_indices])
        
        centroid = pts.mean(axis=0)
        _, _, vh = np.linalg.svd(pts - centroid)
        normal = vh[2, :] 
        a, b, c = normal
        d = -np.dot(normal, centroid)
        
        name = f"Plane {len(self.planes)+1} (h~{centroid[2]:.1f})"
        self.planes.append({"name": name, "coeffs": (a, b, c, d), "points": pts})
        self.refresh_plane_list()
        self.plot_all()

    def delete_selected_plane(self):
        sel = self.plane_listbox.curselection()
        if sel:
            self.planes.pop(sel[0])
            self.refresh_plane_list()
            self.plot_all()
    
    def refresh_plane_list(self):
        self.plane_listbox.delete(0, tk.END)
        for p in self.planes:
            self.plane_listbox.insert(tk.END, p["name"])
    
    def snap_to_plane(self):
        sel_plane_idx = self.plane_listbox.curselection()
        if not sel_plane_idx or not self.selected_indices:
            messagebox.showwarning("Selection", "Select a plane from the list AND at least one entity.")
            return
        
        a, b, c, d = self.planes[sel_plane_idx[0]]["coeffs"]
        snap_axis = 'y'
        if abs(c) > 0.5: snap_axis = 'y'
        elif abs(b) > 0.5: snap_axis = 'z'
        elif abs(a) > 0.5: snap_axis = 'x'
        
        denom = c if snap_axis == 'y' else (b if snap_axis == 'z' else a)
        if abs(denom) < 1e-6:
            messagebox.showerror("Error", f"Plane is parallel to {snap_axis.upper()}-axis, cannot snap.")
            return

        count = 0
        for idx in self.selected_indices:
            ent = self.entities[idx]
            if snap_axis == 'y': val = -(a * ent['x'] + b * ent['z'] + d) / c
            elif snap_axis == 'z': val = -(a * ent['x'] + c * ent['y'] + d) / b
            else: val = -(b * ent['z'] + c * ent['y'] + d) / a
                
            if ent[snap_axis] != val:
                ent[snap_axis] = val
                self._sync_entity_raw(ent)
                count += 1
        
        if count > 0:
            self.update_editor_fields()
            self.plot_all()
            self.highlight_pts()
            messagebox.showinfo("Success", f"Snapped {count} items to plane ({snap_axis.upper()}).")

    # --- Size Filter Logic ---
    def on_size_filter_change(self):
        self.on_slice_update()

    # --- Shading Logic ---
    def get_colors(self, indices):
        mode = self.viz_mode.get()
        rad_scale = self.color_radius.get()
        if not indices: return np.zeros((0, 3))
        
        coords = np.array([[self.entities[i]['x'], self.entities[i]['y'], self.entities[i]['z']] for i in indices])
        
        if mode == "XYZ":
            z_values = coords[:, 2]
            z_min, z_max = z_values.min(), z_values.max()
            rng = (z_max - z_min) if (z_max - z_min) > 0 else 1.0
            norm_z = np.clip((z_values - z_min) / rng, 0, 1)
            return matplotlib.cm.plasma(norm_z)[:, :3]
            
        elif mode == "Logic":
            logic_pts = np.array([[e['x'], e['y'], e['z']] for e in self.entities if e['id'] == "3226"])
            if len(logic_pts) == 0: return np.array([[0.5, 0.5, 0.5]] * len(indices))
            dists = []
            for p in coords:
                d = np.sqrt(np.sum((logic_pts - p)**2, axis=1)).min()
                dists.append(d)
            dists = np.array(dists)
            max_d = (dists.max() if dists.max() > 0 else 1.0) / rad_scale
            dists = np.clip(1.0 - (dists / max_d), 0, 1)
            return matplotlib.cm.plasma(dists)[:, :3] 

        elif mode == "ID":
            ids = []
            for i in indices:
                try: ids.append(int(self.entities[i]['id']))
                except: ids.append(0)
            ids = np.array(ids)
            norm_ids = (ids % 20) / 20.0
            return matplotlib.cm.tab20(norm_ids)[:, :3]

        elif mode == "Size":
            sizes = []
            for i in indices:
                sizes.append(self.get_size_from_db(self.entities[i]))
            sizes = np.array(sizes)
            valid_sizes = sizes[sizes < 9000000]
            if len(valid_sizes) > 0:
                mn, mx = valid_sizes.min(), valid_sizes.max()
                rng = mx - mn if mx > mn else 1.0
                norm_sizes = np.clip((sizes - mn) / rng, 0, 1)
            else:
                norm_sizes = np.zeros_like(sizes)
            return matplotlib.cm.viridis(norm_sizes)[:, :3]
        
        elif mode == "Hierarchy":
            # Build parent map: child_id -> parent_index
            parent_map = {}
            for i, e in enumerate(self.entities):
                for child_id in e.get('child_ids', []):
                    clean_id = child_id.strip().zfill(4)
                    parent_map[clean_id] = i
            
            # Calculate depth: 0 = root/orphan, 1 = direct child, 2 = grandchild, etc.
            def get_depth(idx):
                ent_id = self.entities[idx]['id'].strip().zfill(4)
                depth = 0
                visited = set()
                current_id = ent_id
                
                while current_id in parent_map and current_id not in visited:
                    visited.add(current_id)
                    parent_idx = parent_map[current_id]
                    current_id = self.entities[parent_idx]['id'].strip().zfill(4)
                    depth += 1
                
                return depth
            
            depths = np.array([get_depth(i) for i in indices])
            max_depth = depths.max() if len(depths) > 0 else 0
            
            if max_depth == 0:
                # Everything is a root
                return np.array([[0.3, 0.3, 0.8]] * len(indices))
            
            # Normalize: 0.0 = root (blue), 1.0 = deepest child (red)
            norm_depths = depths / max_depth
            return matplotlib.cm.turbo(norm_depths)[:, :3]
            
        return np.array([[0.0, 0.0, 1.0]] * len(indices))

    def get_size_from_db(self, ent):
        db_key = ent['id'].lstrip('0') or '0'
        return self.item_db.get(db_key, {}).get('size_val', 0.0)

    def apply_depth_shading(self, base_colors, indices):
        if not self.depth_shading.get() or not self.ax3d.get_visible():
            return base_colors
        
        if len(indices) == 0:
            return base_colors
        
        proj = self.ax3d.get_proj()
        depths = []
        for i in indices:
            e = self.entities[i]
            _, _, z_depth = proj3d.proj_transform(e['x'], e['z'], e['y'], proj)
            depths.append(z_depth)
        
        depths = np.array(depths)
        if len(depths) == 0: return base_colors
        d_min, d_max = depths.min(), depths.max()
        if d_max == d_min: return base_colors
        
        fog = (depths - d_min) / (d_max - d_min)
        
        if not isinstance(base_colors, np.ndarray):
             base_colors = np.array([matplotlib.colors.to_rgb(base_colors)] * len(indices))
        
        shaded = base_colors * (1.0 - (fog[:, np.newaxis] * 0.7))
        return np.clip(shaded, 0, 1)

    def on_slice_axis_change(self, e):
        ax = self.slice_axis.get()
        if ax == "None":
            self.scale_depth.config(state="disabled"); self.scale_thick.config(state="disabled")
        else:
            self.scale_depth.config(state="normal"); self.scale_thick.config(state="normal")
            key = 'y' if "Y-Axis" in ax else ('z' if "Z-Axis" in ax else 'x')
            mn, mx = self.axis_bounds[key]
            self.scale_depth.config(from_=mn-10, to=mx+10)
        self.on_slice_update()

    def plot_all(self):
        if self.ax3d.get_visible():
            self.view_state['3d'] = (self.ax3d.azim, self.ax3d.elev, self.ax3d.get_xlim(), self.ax3d.get_ylim(), self.ax3d.get_zlim())

        if not self.entities: 
            self.ax3d.clear()
            self.canvas.draw()
            return
        
        visible_indices = self.display_mapping
        self.ax3d.clear()

        s_vals = 20
        if self.use_size_scaling.get():
            sizes = []
            for i in visible_indices:
                sv = self.get_size_from_db(self.entities[i])
                if sv > 9000000: sv = 200
                sizes.append(sv)
            if sizes:
                sizes = np.array(sizes)
                s_vals = np.clip(sizes / 2.0, 5, 1000)
            else:
                s_vals = 20

        colors = self.get_colors(visible_indices)
        
        if visible_indices:
            xs = [self.entities[i]['x'] for i in visible_indices]
            ys = [self.entities[i]['y'] for i in visible_indices]
            zs = [self.entities[i]['z'] for i in visible_indices]
            
            alpha = self.entity_opacity.get()
            shaded_colors = self.apply_depth_shading(colors, visible_indices)
            
            # Draw entities with edges (edgecolors with slightly transparent black)
            self.ax3d.scatter([-x for x in xs], zs, ys, c=shaded_colors, alpha=alpha, s=s_vals, 
                            picker=True, zorder=1, edgecolors='black', linewidths=0.5)
        
        self.figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
        active_plane_idx = self.plane_listbox.curselection()
        
        for idx, p in enumerate(self.planes):
            a, b, c, d = p["coeffs"]
            pts = p["points"]
            
            if len(pts) == 0: continue
            
            x_min, x_max = pts[:,0].min(), pts[:,0].max()
            z_min, z_max = pts[:,1].min(), pts[:,1].max()
            
            x_range = np.linspace(x_min, x_max, 2)
            z_range = np.linspace(z_min, z_max, 2)
            X, Z = np.meshgrid(x_range, z_range)
            
            X = -X
            
            if abs(c) > 1e-6:
                Y = -(a*X + b*Z + d) / c
            elif abs(b) > 1e-6:
                Y = np.zeros_like(X)
            else:
                Y = np.zeros_like(X)

            is_active = (active_plane_idx and active_plane_idx[0] == idx)
            is_auto = p.get("auto", False)
            color = 'cyan' if is_auto else ('gold' if is_active else 'gray')
            p_alpha = 0.2 if is_auto else (0.4 if is_active else 0.1)
            
            if is_auto or abs(c) <= 1e-6:
                flipped_pts = pts.copy()
                flipped_pts[:,0] = -flipped_pts[:,0]
                verts = [list(zip(flipped_pts[:,0], flipped_pts[:,1], flipped_pts[:,2]))]
                poly = Poly3DCollection(verts, alpha=p_alpha, facecolors=color)
                self.ax3d.add_collection3d(poly)
            elif abs(c) > 1e-6:
                self.ax3d.plot_surface(X, Z, Y, color=color, alpha=p_alpha, shade=False)

        if self.view_state['3d']:
            azim, elev, xlim, ylim, zlim = self.view_state['3d']
            self.ax3d.view_init(elev=elev, azim=azim)
            self.ax3d.set_xlim(xlim); self.ax3d.set_ylim(ylim); self.ax3d.set_zlim(zlim)
        else:
            self.ax3d.set_xlabel('X'); self.ax3d.set_ylabel('Z'); self.ax3d.set_zlabel('Y')

        self.canvas.draw()
        self.highlight_pts()

    def highlight_pts(self, live_preview=False):
        for i, h in enumerate(self.highlights):
            if h:
                try: h.remove()
                except: pass
                self.highlights[i] = None
        if not self.selected_indices: return
        
        xs, ys, zs = [], [], []
        off = self.offset_mode.get()
        p_vals = [v.get() for v in self.pos_vars]
        
        for i in self.selected_indices:
            e = self.entities[i]
            if live_preview:
                # Negate p_vals back when applying to entity coords
                px = (e['x'] - p_vals[0]) if off else -p_vals[0]
                py = (e['y'] - p_vals[1]) if off else -p_vals[1]
                pz = (e['z'] - p_vals[2]) if off else -p_vals[2]
            else:
                px, py, pz = e['x'], e['y'], e['z']
            xs.append(px); ys.append(py); zs.append(pz)
            
        if self.ax3d.get_visible():
            # Make selected entities MUCH more visible: larger size, bright color, thick edge, render on top
            self.highlights[3] = self.ax3d.scatter([-x for x in xs], zs, ys, 
                                                   c='#FF0000', s=150, 
                                                   edgecolors='yellow', linewidths=2.5, 
                                                   zorder=10000, depthshade=False, alpha=1.0)
        self.canvas.draw_idle()

    def swap_positions(self):
        if len(self.selected_indices) != 2:
            messagebox.showwarning("Warning", "Select exactly 2 items.")
            return
        idx1, idx2 = self.selected_indices
        e1, e2 = self.entities[idx1], self.entities[idx2]
        p1 = (e1['x'], e1['y'], e1['z']); p2 = (e2['x'], e2['y'], e2['z'])
        e1['x'], e1['y'], e1['z'] = p2; e2['x'], e2['y'], e2['z'] = p1
        self._sync_entity_raw(e1); self._sync_entity_raw(e2)
        self.update_editor_fields(); self.plot_all(); self.highlight_pts()

    def copy_pos(self, mode):
        if not self.selected_indices: return
        vals = [v.get() for v in self.pos_vars]
        if mode == "all": self.pos_buffer["all"] = vals
        else: self.pos_buffer[mode] = vals[{"x":0, "y":1, "z":2}[mode]]
        self.lbl_info.config(text=f"Copied {mode.upper()} to clipboard.")

    def paste_pos(self, mode):
        if not self.selected_indices: return
        updated = False
        if mode == "all" and self.pos_buffer["all"]:
            for i in range(3): 
                self.pos_vars[i].set(self.pos_buffer["all"][i])
                self.dirty_fields.add(f"pos_{i}")
            updated = True
        elif mode in ["x", "y", "z"] and self.pos_buffer[mode] is not None:
            idx = {"x":0, "y":1, "z":2}[mode]
            self.pos_vars[idx].set(self.pos_buffer[mode])
            self.dirty_fields.add(f"pos_{idx}")
            updated = True
        if updated: self.highlight_pts(live_preview=True)

    def _sync_entity_raw(self, ent):
        original_content = ent['p_raw_content']
        new_parts, last_idx, ax_keys = [], 0, ['x', 'y', 'z']
        for i in range(3):
            start, end = ent['p_indices'][i]
            new_parts.append(original_content[last_idx:start])
            new_parts.append(self.format_strict(ent[ax_keys[i]], end - start))
            last_idx = end
        new_parts.append(original_content[last_idx:])
        reconstructed = "".join(new_parts)
        ent['p_raw_content'] = reconstructed
        s, e = "<posi>", "</posi>"
        si = ent['raw'].find(s) + len(s); ei = ent['raw'].find(e)
        final_block = reconstructed[:ei-si].ljust(ei-si)
        ent['raw'] = ent['raw'][:si] + final_block + ent['raw'][ei:]

    def on_offset_toggle(self):
        if self.offset_mode.get(): 
            [v.set(0.0) for v in self.pos_vars]
            # Switch to offset range (±1000)
            for s in self.pos_sliders:
                s.configure(from_=-1000, to=1000)
        else:
            # Switch to absolute positioning range based on map bounds
            if self.entities:
                max_range = max(
                    self.axis_bounds['x'][1] - self.axis_bounds['x'][0],
                    self.axis_bounds['y'][1] - self.axis_bounds['y'][0],
                    self.axis_bounds['z'][1] - self.axis_bounds['z'][0],
                    10.0
                )
                absolute_limit = max_range * 0.6
                for s in self.pos_sliders:
                    s.configure(from_=-absolute_limit, to=absolute_limit)

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
        else: p = [0.0, 0.0, 0.0]; p_indices = []
        r_raw, r_len = get_t('roll', b)
        r_matches = list(re.finditer(r'[^\s]+', r_raw))
        if len(r_matches) == 4:
            r = [float(m.group(0)) for m in r_matches]
            r_indices = [(m.start(), m.end()) for m in r_matches]
        else: r = [0.0, 0.0, 0.0, 1.0]; r_indices = []
        id_raw, id_len = get_t('index', b)
        
        return {
            'raw': b, 'p_raw_content': p_raw, 'r_raw_content': r_raw,
            'p_indices': p_indices, 'r_indices': r_indices,
            'id_tag_len': id_len, 'x': p[0], 'y': p[1], 'z': p[2], 
            'rx': r[1], 'ry': r[2], 'rz': r[3], 'rw': r[0],
            'id': id_raw.strip(), 'pack': get_t('pack_id', b)[0].strip(), 
            'atk': get_t('attack_type', b)[0].strip(), 'mov': get_t('move_type', b)[0].strip(), 
            'esc': get_t('escape_type', b)[0].strip(), 'spd': find_val(['move_speed', 'speed'], b), 
            'pth': find_val(['move_path_id', 'path_id'], b),
            'scale': find_val(['scale'], b),
            'plus_type': find_val(['plus_type'], b),
            'plus_fly_height': find_val(['plus_fly_height'], b),
            'plus_roll_speed': find_val(['plus_roll_speed'], b),
            'plus_angle': find_val(['plus_angle'], b),
            'parent_type': find_val(['parent_type'], b),
            'child_ids': []  # Populated during load_file
        }

    def format_strict(self, val, width):
        s = f"{val:.10f}"
        if len(s) > width:
            s = s[:width]
            if s.endswith('.'): s = s[:-1].rjust(width)
        return s.ljust(width)

    def commit_batch_changes(self):
        if not self.selected_indices: return
        use_offset = self.offset_mode.get(); id_changed = False
        vals = { 'pos': [v.get() for v in self.pos_vars], 'rot': [v.get() for v in self.rot_vars] }
        for idx in self.selected_indices:
            ent = self.entities[idx]; raw = ent['raw']
            def safe_rep(tag, new_content, block):
                s, e = f"<{tag}>", f"</{tag}>"
                si = block.find(s) + len(s); ei = block.find(e)
                if si == -1 or ei == -1: return block
                orig_len = ei - si
                final_str = new_content[:orig_len].ljust(orig_len)
                return block[:si] + final_str + block[ei:]
            if any(f"pos_{i}" in self.dirty_fields for i in range(3)) and len(ent['p_indices']) == 3:
                original_content = ent['p_raw_content']
                new_parts, last_idx, ax_keys = [], 0, ['x', 'y', 'z']
                for i in range(3):
                    start, end = ent['p_indices'][i]
                    new_parts.append(original_content[last_idx:start])
                    if f"pos_{i}" in self.dirty_fields:
                        # Negate the displayed value back to file format
                        file_val = -vals['pos'][i]
                        if use_offset:
                            ent[ax_keys[i]] = ent[ax_keys[i]] + file_val
                        else:
                            ent[ax_keys[i]] = file_val
                    new_parts.append(self.format_strict(ent[ax_keys[i]], end - start))
                    last_idx = end
                new_parts.append(original_content[last_idx:])
                ent['p_raw_content'] = "".join(new_parts)
                raw = safe_rep('posi', ent['p_raw_content'], raw)
            if any(f"rot_{i}" in self.dirty_fields for i in range(4)) and len(ent['r_indices']) == 4:
                original_content = ent['r_raw_content']
                new_parts, last_idx, ax_keys = [], 0, ['rw', 'rx', 'ry', 'rz']
                for i in range(4):
                    start, end = ent['r_indices'][i]
                    new_parts.append(original_content[last_idx:start])
                    if f"rot_{i}" in self.dirty_fields: ent[ax_keys[i]] = vals['rot'][i]
                    new_parts.append(self.format_strict(ent[ax_keys[i]], end - start))
                    last_idx = end
                new_parts.append(original_content[last_idx:])
                ent['r_raw_content'] = "".join(new_parts)
                raw = safe_rep('roll', ent['r_raw_content'], raw)
            for f, t in [('id','index'), ('atk','attack_type'), ('mov','move_type'), ('esc','escape_type'), 
                         ('spd','speed'), ('pth','path_id'), ('scale','scale'), ('plus_type','plus_type'),
                         ('plus_fly_height','plus_fly_height'), ('plus_roll_speed','plus_roll_speed'),
                         ('plus_angle','plus_angle'), ('parent_type','parent_type')]:
                if f in self.dirty_fields:
                    val_str = str(self.get_entry_val(f)).strip()
                    if f == 'id':
                        target_w = ent['id_tag_len'] - 2
                        val_str = val_str.zfill(target_w); id_changed = True
                    ent[f] = val_str
                    raw = safe_rep(t, f" {val_str} ", raw)
            ent['raw'] = raw
        self.dirty_fields.clear()
        
        # Reset position sliders to 0 after offset commit
        if use_offset:
            for v in self.pos_vars:
                v.set(0.0)
        
        if id_changed: self.refresh_list()
        self.plot_all(); self.highlight_pts(); messagebox.showinfo("Done", "Changes Committed.")

    def get_entry_val(self, k):
        m = {'id':self.entry_index, 'atk':self.entry_attack, 'mov':self.entry_move, 'esc':self.entry_escape, 
             'spd':self.entry_speed, 'pth':self.entry_path, 'scale':self.entry_scale, 
             'plus_type':self.entry_plus_type, 'plus_fly_height':self.entry_plus_fly_height,
             'plus_roll_speed':self.entry_plus_roll_speed, 'plus_angle':self.entry_plus_angle,
             'parent_type':self.entry_parent_type}
        return m[k].get()

    def on_slice_update(self):
        if not self.entities: return
        mode = self.slice_axis.get()
        if mode == "None": 
            visible = list(range(len(self.entities)))
        else:
            tax = 'y' if "Y-Axis" in mode else ('z' if "Z-Axis" in mode else 'x')
            d, t = self.slice_depth.get(), self.slice_thickness.get()
            visible = [i for i, e in enumerate(self.entities) if (d-t) <= e[tax] <= (d+t)]
        
        if self.size_filter_enabled.get():
            size_min = self.size_filter_min.get()
            size_max = self.size_filter_max.get()
            visible = [i for i in visible if size_min <= self.get_size_from_db(self.entities[i]) <= size_max]
        
        self.planes = [p for p in self.planes if not p.get("auto", False)]
        
        if mode != "None":
            depth = self.slice_depth.get()
            
            xb = self.axis_bounds['x']
            yb = self.axis_bounds['y']
            zb = self.axis_bounds['z']
            
            if "Y-Axis" in mode:
                coeffs = (0, 0, 1, -depth)
                pts = np.array([
                    [xb[0], zb[0], depth],
                    [xb[1], zb[0], depth],
                    [xb[1], zb[1], depth],
                    [xb[0], zb[1], depth]
                ])
            elif "Z-Axis" in mode:
                coeffs = (0, 1, 0, -depth)
                pts = np.array([
                    [xb[0], depth, yb[0]],
                    [xb[1], depth, yb[0]],
                    [xb[1], depth, yb[1]],
                    [xb[0], depth, yb[1]]
                ])
            else:
                coeffs = (1, 0, 0, -depth)
                pts = np.array([
                    [depth, zb[0], yb[0]],
                    [depth, zb[1], yb[0]],
                    [depth, zb[1], yb[1]],
                    [depth, zb[0], yb[1]]
                ])

            self.planes.append({"name": "Slice Plane [Auto]", "coeffs": coeffs, "points": pts, "auto": True})
            self.refresh_plane_list()

        self.display_mapping = visible
        self.refresh_list(); self.plot_all(); self.highlight_pts()

    def on_graph_pick(self, event):
        if self.toolbar.mode != "" or self.select_mode.get() != "CLICK": return
        if not self.display_mapping: return
        try:
            midx = self.display_mapping[event.ind[0]]
            shift, ctrl = (event.mouseevent.key == 'shift'), (event.mouseevent.key == 'control')
            if ctrl:
                if midx in self.selected_indices: self.selected_indices.remove(midx)
                else: self.selected_indices.append(midx)
            elif shift:
                if midx not in self.selected_indices: self.selected_indices.append(midx)
            else: self.selected_indices = [midx]
            self.sync_selection_ui()
        except Exception: pass

    def on_mouse_down(self, event):
        if not event.inaxes or self.toolbar.mode != "": return
        mode = self.select_mode.get()
        if mode == "CLICK": return 
        self.is_dragging = True; self.drag_start = (event.xdata, event.ydata); self.active_ax = event.inaxes
        if mode == "PAINT": self.do_paint_select(event)
    
    def on_mouse_move(self, event):
        if not self.is_dragging or not event.inaxes or event.inaxes != self.active_ax: return
        if self.select_mode.get() == "PAINT": self.do_paint_select(event)

    def on_mouse_up(self, event):
        self.is_dragging = False

    def do_paint_select(self, event):
        rad = self.brush_size.get(); ctrl = (event.key == 'control'); changed = False
        if event.inaxes == self.ax3d:
            proj_matrix = self.ax3d.get_proj()
            for midx in self.display_mapping:
                e = self.entities[midx]
                x2d, y2d, _ = proj3d.proj_transform(-e['x'], e['z'], e['y'], proj_matrix)
                disp_coord = self.ax3d.transData.transform((x2d, y2d))
                pixel_dist = math.sqrt((disp_coord[0]-event.x)**2 + (disp_coord[1]-event.y)**2)
                if pixel_dist < rad:
                    if ctrl and midx in self.selected_indices: self.selected_indices.remove(midx); changed = True
                    elif not ctrl and midx not in self.selected_indices: self.selected_indices.append(midx); changed = True
        if changed: self.highlight_pts()

    def sync_selection_ui(self):
        self.is_updating_ui = True; self.entity_listbox.selection_clear(0, tk.END)
        for i in self.selected_indices:
            if i in self.display_mapping:
                pos = self.display_mapping.index(i); self.entity_listbox.selection_set(pos)
                if i == self.selected_indices[-1]: self.entity_listbox.see(pos)
        self.update_editor_fields(); self.highlight_pts(); self.is_updating_ui = False

    def on_list_select(self, e):
        if not self.is_updating_ui:
            sel = self.entity_listbox.curselection()
            self.selected_indices = [self.display_mapping[i] for i in sel]
            self.update_editor_fields(); self.highlight_pts()

    def on_slider_move(self, t):
        if not self.is_updating_ui and self.selected_indices: self.highlight_pts(live_preview=True)

    def sort_entities(self, crit):
        self.sort_reverse = (not self.sort_reverse) if self.last_sort == crit else False
        self.last_sort = crit
        def sk(idx):
            e = self.entities[idx]; db_key = e['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key) or {}
            if crit == "NAME": return "logic" if e['id'] == "3226" else info.get('name','').lower()
            if crit == "SIZE": return info.get('size_val', 0)
            if crit == "ATK": return int(e.get('atk', 0))
            if crit == "MOV": return int(e.get('mov', 0))
            return e['id']
        self.display_mapping.sort(key=sk, reverse=self.sort_reverse); self.refresh_list(); self.plot_all()

    def reset_sort(self): 
        self.last_sort = None
        self.on_slice_update()
    
    def load_csv(self):
        p = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if p:
            with open(p, 'r', encoding='utf-8-sig') as f:
                self.item_db = {r['ID'].strip().lstrip('0'): {'name': r['NAME'], 'size_val': float(re.sub(r'[^\d.]', '', r['SIZE (mm)'])) if r.get('SIZE (mm)') else 0} for r in csv.DictReader(f)}
            
            if self.item_db:
                sizes = [info['size_val'] for info in self.item_db.values() if info['size_val'] < 9000000]
                if sizes:
                    max_size = max(sizes)
                    self.scale_size_max.config(to=max_size * 1.1)
                    self.size_filter_max.set(max_size * 1.1)
            
            self.refresh_list()

    def load_file(self):
        p = filedialog.askopenfilename(filetypes=[("DAT","*.dat")])
        if not p: return
        with open(p, 'rb') as f: content = f.read().decode('utf-8', errors='ignore')
        
        self.file_sequence, self.entities = [], []
        
        # We search for structural tokens to handle nesting correctly
        token_pattern = re.compile(r'(<entity>|</entity>|<child>|</child>)')
        
        last_pos = 0
        entity_start_pos = None
        parent_stack = [] # Tracks indices of parents to populate child_ids automatically
        
        for match in token_pattern.finditer(content):
            token = match.group(1)
            start, end = match.start(), match.end()
            
            # 1. Handle "Gap" text (whitespace, garbage, or content inside an entity)
            # If we are NOT currently recording an entity, this text is file structure (to be saved)
            if entity_start_pos is None:
                if start > last_pos:
                    self.file_sequence.append(content[last_pos:start])
            
            # 2. Process Tokens
            if token == "<entity>":
                entity_start_pos = start
            
            elif token == "<child>":
                # If we hit a <child> tag while recording an entity, it means the current 
                # entity is a Parent. We must "seal" the Parent entity *Head* here 
                # so the children can be processed as separate, editable objects.
                if entity_start_pos is not None:
                    raw_chunk = content[entity_start_pos:start]
                    ent = self._parse_block(raw_chunk)
                    ent['child_ids'] = [] 
                    self.entities.append(ent)
                    self.file_sequence.append(ent)
                    
                    # Track this entity as the active parent
                    parent_stack.append(len(self.entities) - 1)
                    entity_start_pos = None # Stop recording the parent (head is done)
                
                # Add the <child> tag to the file sequence explicitly
                self.file_sequence.append(token)
            
            elif token == "</entity>":
                if entity_start_pos is not None:
                    # This is a standard closing tag (for a leaf entity or child)
                    raw_chunk = content[entity_start_pos:end]
                    ent = self._parse_block(raw_chunk)
                    ent['child_ids'] = []
                    self.entities.append(ent)
                    self.file_sequence.append(ent)
                    
                    # Link this child to its parent if inside a <child> block
                    if parent_stack:
                        self.entities[parent_stack[-1]]['child_ids'].append(ent['id'])
                    
                    entity_start_pos = None
                else:
                    # This is the closing tag of a Parent (whose head was processed at <child>)
                    # We treat it as structural text string
                    self.file_sequence.append(token)
            
            elif token == "</child>":
                self.file_sequence.append(token)
                if parent_stack:
                    parent_stack.pop()

            last_pos = end

        # Catch any trailing file content
        if last_pos < len(content):
            self.file_sequence.append(content[last_pos:])
        
        # --- Recalculate Bounds for Sliders ---
        if self.entities:
            xs, ys, zs = [e['x'] for e in self.entities], [e['y'] for e in self.entities], [e['z'] for e in self.entities]
            self.axis_bounds = {'x':(min(xs), max(xs)), 'y':(min(ys), max(ys)), 'z':(min(zs), max(zs))}
            
            max_range = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 10.0)
            absolute_limit = max_range * 0.6
            
            for s in self.pos_sliders:
                if self.offset_mode.get():
                    s.configure(from_=-1000, to=1000)
                else:
                    s.configure(from_=-absolute_limit, to=absolute_limit)
        self.on_slice_update()

    def refresh_list(self):
        self.entity_listbox.delete(0, tk.END)
        
        # Build parent-child mapping
        parent_map = {}  # child_id (as string with padding) -> parent_index
        for i, e in enumerate(self.entities):
            for child_id in e.get('child_ids', []):
                padded_id = child_id.strip().zfill(4)
                parent_map[padded_id] = i
        
        # Check if we're in default sort (display_mapping matches entity order)
        is_default_sort = (self.display_mapping == list(range(len(self.entities))))
        
        for i in self.display_mapping:
            e = self.entities[i]
            db_key = e['id'].lstrip('0') or '0'
            info = self.item_db.get(db_key) or {}
            name = "Logic" if e['id'] == "3226" else info.get('name','Unknown')
            size = info.get('size_val','?')
            
            # Check if this entity is a child
            padded_current_id = e['id'].strip().zfill(4)
            is_child = padded_current_id in parent_map
            
            # Indent children only in default sort
            if is_default_sort and is_child:
                prefix = "    "  # 4 spaces for indent
            else:
                prefix = ""
            
            self.entity_listbox.insert(tk.END, f"{prefix}{name} ({e['id']}) [{size}]")

    def update_editor_fields(self):
        if not self.selected_indices: return
        self.is_updating_ui = True
        ent = self.entities[self.selected_indices[-1]]
        db_key = ent['id'].lstrip('0') or '0'
        info = self.item_db.get(db_key) or {}
        name = "Logic" if ent['id'] == "3226" else info.get('name','Unknown')
        
        # Build parent-child info
        parent_map = {}
        for i, e in enumerate(self.entities):
            for child_id in e.get('child_ids', []):
                padded_id = child_id.strip().zfill(4)
                parent_map[padded_id] = i
        
        rel_info = ""
        padded_current_id = ent['id'].strip().zfill(4)
        if padded_current_id in parent_map:
            parent_idx = parent_map[padded_current_id]
            parent_e = self.entities[parent_idx]
            parent_db_key = parent_e['id'].lstrip('0') or '0'
            parent_info = self.item_db.get(parent_db_key) or {}
            parent_name = "Logic" if parent_e['id'] == "3226" else parent_info.get('name','Unknown')
            rel_info = f" | Parent: {parent_name} ({parent_e['id']})"
        
        if len(ent.get('child_ids', [])) > 0:
            rel_info += f" | Children: {len(ent['child_ids'])}"
        
        self.lbl_info.config(text=f"OBJ: {name} | ID: {ent['id']} | Size: {info.get('size_val','?')} | Pack: {ent.get('pack','?')}{rel_info}\nSelected: {len(self.selected_indices)}")
        
        if not self.offset_mode.get():
            for e, k in [(self.entry_index,'id'), (self.entry_attack,'atk'), (self.entry_move,'mov'), (self.entry_escape,'esc'), 
                         (self.entry_speed,'spd'), (self.entry_path,'pth'), (self.entry_scale,'scale'),
                         (self.entry_plus_type,'plus_type'), (self.entry_plus_fly_height,'plus_fly_height'),
                         (self.entry_plus_roll_speed,'plus_roll_speed'), (self.entry_plus_angle,'plus_angle'),
                         (self.entry_parent_type,'parent_type')]:
                e.delete(0, tk.END); e.insert(0, ent.get(k, '0'))
            # Display negated for in-game representation
            for i in range(3): self.pos_vars[i].set([-ent['x'], -ent['y'], -ent['z']][i])
            for i in range(4): self.rot_vars[i].set([ent['rw'], ent['rx'], ent['ry'], ent['rz']][i])
        self.is_updating_ui = False

    def save_map_file(self):
        p = filedialog.asksaveasfilename(defaultextension=".dat")
        if p:
            out = "".join([i if isinstance(i, str) else i['raw'] for i in self.file_sequence])
            with open(p, 'wb') as f: f.write(out.encode('utf-8'))
            messagebox.showinfo("Success", "Saved.")

if __name__ == "__main__":
    root = tk.Tk(); app = KatamariEditor(root); root.mainloop()