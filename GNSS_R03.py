"""
GNSS Multipath R03
SAYAR Production House

True graphical GNSS RF network editor and calculator.

Install:
    pip install customtkinter pillow

Run:
    python GNSS_R03.py
"""

from __future__ import annotations

import csv
import json
import math
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Missing package. Install with: pip install customtkinter")

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None
    HAS_PILLOW = False


ColorPair = Tuple[str, str]

APP_TITLE = "GNSS Multipath R03"
APP_BRAND = "SAYAR Production House"
SCHEMA_VERSION = "R03"

GRID_SIZE = 20
NODE_W = 230
NODE_H = 118
DEBOUNCE_MS = 250

COLOR_APP_BG: ColorPair = ("#EDF4F8", "#111827")
COLOR_PANEL: ColorPair = ("#F8FBFD", "#1F2937")
COLOR_PANEL_ALT: ColorPair = ("#E6F0F6", "#263445")
COLOR_CARD: ColorPair = ("#FFFFFF", "#2B384A")
COLOR_BORDER: ColorPair = ("#C6D6E2", "#4B5E73")
COLOR_TEXT: ColorPair = ("#17202A", "#F3F7FB")
COLOR_MUTED: ColorPair = ("#566573", "#B7C4D2")
COLOR_BLUE: ColorPair = ("#6EA8CC", "#2F6F95")
COLOR_BLUE_DARK: ColorPair = ("#347BA8", "#245B7A")
COLOR_BLUE_HOVER: ColorPair = ("#2E6F98", "#1D4F6C")
COLOR_GREEN: ColorPair = ("#A6D8B8", "#245C3B")
COLOR_GREEN_TEXT: ColorPair = ("#123820", "#E8FFF0")
COLOR_AMBER: ColorPair = ("#F7D794", "#82621E")
COLOR_AMBER_TEXT: ColorPair = ("#4B3600", "#FFF3D1")
COLOR_RED: ColorPair = ("#F1A7A7", "#7A2E2E")
COLOR_RED_TEXT: ColorPair = ("#4A1111", "#FFE8E8")
COLOR_INVALID_ENTRY: ColorPair = ("#FFECEC", "#4A1E1E")
COLOR_VALID_ENTRY: ColorPair = ("#FFFFFF", "#2B384A")
COLOR_INVALID_BORDER: ColorPair = ("#D9534F", "#FF8C8C")
COLOR_DIAGRAM_BG: ColorPair = ("#FAFCFE", "#111827")
COLOR_BLOCK_BORDER: ColorPair = ("#467EA3", "#72A8CE")
COLOR_ARROW: ColorPair = ("#2E6F98", "#88C7EF")
COLOR_NODE_SOURCE: ColorPair = ("#E8F5E9", "#1D3B2A")
COLOR_NODE_CABLE: ColorPair = ("#EAF4FB", "#1E3A4A")
COLOR_NODE_SPLITTER: ColorPair = ("#FFF7E6", "#4A3610")
COLOR_NODE_AMP: ColorPair = ("#E8F5E9", "#1D3B2A")
COLOR_NODE_ATTEN: ColorPair = ("#FFF1F1", "#4A1D1D")
COLOR_NODE_RX: ColorPair = ("#F1F4F7", "#334155")

GNSS_BANDS_MHZ: Dict[str, float] = {
    "GPS L1 / Galileo E1 / BeiDou B1C, 1575.42 MHz": 1575.42,
    "GLONASS G1, 1602.00 MHz": 1602.00,
    "GPS L2, 1227.60 MHz": 1227.60,
    "GLONASS G2, 1246.00 MHz": 1246.00,
    "GPS L5 / Galileo E5a / QZSS L5, 1176.45 MHz": 1176.45,
    "Galileo E5b / BeiDou B2I, 1207.14 MHz": 1207.14,
    "BeiDou B1I, 1561.098 MHz": 1561.098,
    "Custom": 1575.42,
}

CABLE_LOSS_DB_PER_100M: Dict[str, Dict[float, float]] = {
    "LMR-100": {1000.0: 75.0, 1200.0: 84.0, 1500.0: 95.0, 1600.0: 99.0, 1800.0: 106.0},
    "LMR-195": {1000.0: 34.5, 1200.0: 38.0, 1500.0: 43.0, 1600.0: 44.5, 1800.0: 47.5},
    "LMR-200": {1000.0: 32.0, 1200.0: 35.5, 1500.0: 40.0, 1600.0: 41.5, 1800.0: 44.0},
    "LMR-240": {1000.0: 21.5, 1200.0: 24.0, 1500.0: 27.0, 1600.0: 28.0, 1800.0: 30.0},
    "LMR-400": {1000.0: 13.0, 1200.0: 14.5, 1500.0: 16.2, 1600.0: 16.8, 1800.0: 18.0},
    "RG-58": {1000.0: 64.0, 1200.0: 70.0, 1500.0: 79.0, 1600.0: 82.0, 1800.0: 88.0},
    "RG-316": {1000.0: 95.0, 1200.0: 105.0, 1500.0: 118.0, 1600.0: 123.0, 1800.0: 132.0},
    "Custom Cable": {1000.0: 30.0, 1200.0: 34.0, 1500.0: 38.0, 1600.0: 40.0, 1800.0: 43.0},
}

SPLITTER_LOSS_DB: Dict[str, float] = {
    "2-way": 3.6,
    "3-way": 5.8,
    "4-way": 7.2,
    "6-way": 8.7,
    "8-way": 10.5,
    "12-way": 12.3,
    "16-way": 14.2,
    "Custom Splitter": 0.0,
}

RECEIVER_PRESETS: Dict[str, Tuple[float, float, float]] = {
    "Conservative GNSS receiver window": (-130.0, -35.0, -100.0),
    "Weak-signal simulation": (-145.0, -65.0, -125.0),
    "Indoor re-radiated GNSS distribution": (-125.0, -45.0, -95.0),
    "Lab conducted GNSS receiver input": (-120.0, -30.0, -85.0),
    "Custom": (-130.0, -35.0, -100.0),
}

NODE_TYPES = ["Source", "Cable", "Splitter", "Amplifier", "Attenuator", "Receiver"]
NODE_TYPE_COLORS = {
    "Source": COLOR_NODE_SOURCE,
    "Cable": COLOR_NODE_CABLE,
    "Splitter": COLOR_NODE_SPLITTER,
    "Amplifier": COLOR_NODE_AMP,
    "Attenuator": COLOR_NODE_ATTEN,
    "Receiver": COLOR_NODE_RX,
}


class InputValidationHold(Exception):
    pass


def light_color(color: Union[str, ColorPair]) -> str:
    return color[0] if isinstance(color, tuple) else color


def dark_color(color: Union[str, ColorPair]) -> str:
    return color[1] if isinstance(color, tuple) else color


def drawing_color(color: Union[str, ColorPair]) -> str:
    return dark_color(color) if ctk.get_appearance_mode().lower() == "dark" else light_color(color)


def snap(value: float) -> float:
    return round(value / GRID_SIZE) * GRID_SIZE


def set_entry_valid(entry: Optional[ctk.CTkEntry], is_valid: bool) -> None:
    if entry is None:
        return
    try:
        if is_valid:
            entry.configure(fg_color=COLOR_VALID_ENTRY, border_color=COLOR_BORDER)
        else:
            entry.configure(fg_color=COLOR_INVALID_ENTRY, border_color=COLOR_INVALID_BORDER)
    except Exception:
        pass


def safe_float(value: object, default: float = 0.0, entry: Optional[ctk.CTkEntry] = None, allow_blank: bool = True, field_name: str = "numeric field") -> float:
    text = str(value).strip()
    if text == "":
        if allow_blank:
            set_entry_valid(entry, True)
            return default
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} is blank.")
    if text in {"+", "-", ".", "+.", "-."}:
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} is incomplete.")
    try:
        number = float(text)
    except Exception as exc:
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} is not a valid number.") from exc
    if not math.isfinite(number):
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} is not finite.")
    set_entry_valid(entry, True)
    return number


def safe_int(value: object, default: int = 1, minimum: int = 0, entry: Optional[ctk.CTkEntry] = None, allow_blank: bool = True, field_name: str = "integer field") -> int:
    number = safe_float(value, float(default), entry=entry, allow_blank=allow_blank, field_name=field_name)
    result = int(round(number))
    if result < minimum:
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} must be at least {minimum}.")
    set_entry_valid(entry, True)
    return result


def interpolate_loss(table: Dict[float, float], freq_mhz: float) -> float:
    points = sorted(table.items())
    if not points:
        return 0.0
    if freq_mhz <= points[0][0]:
        return points[0][1]
    if freq_mhz >= points[-1][0]:
        return points[-1][1]
    for (f1, l1), (f2, l2) in zip(points, points[1:]):
        if f1 <= freq_mhz <= f2:
            ratio = (freq_mhz - f1) / (f2 - f1)
            return l1 + ratio * (l2 - l1)
    return points[-1][1]


def cable_loss_db(cable_type: str, length_m: float, freq_mhz: float, custom_db_per_100m: float = 0.0) -> float:
    if cable_type == "Custom Cable" and custom_db_per_100m > 0:
        loss_per_100m = custom_db_per_100m
    else:
        loss_per_100m = interpolate_loss(CABLE_LOSS_DB_PER_100M.get(cable_type, CABLE_LOSS_DB_PER_100M["LMR-200"]), freq_mhz)
    return loss_per_100m * length_m / 100.0


def db_to_linear(db: float) -> float:
    if not math.isfinite(db):
        return 1.0
    return 10 ** (db / 10.0)


def linear_to_db(value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        return 0.0
    return 10 * math.log10(value)


def cascade_noise_figure_db(stages: List[Tuple[float, float]]) -> float:
    valid: List[Tuple[float, float]] = []
    for gain_db, nf_db in stages:
        if not (math.isfinite(gain_db) and math.isfinite(nf_db)):
            continue
        valid.append((gain_db, max(0.0, nf_db)))
    if not valid:
        return 0.0
    eps = 1e-12
    total_f = db_to_linear(valid[0][1])
    gain_product = max(db_to_linear(valid[0][0]), eps)
    for gain_db, nf_db in valid[1:]:
        stage_f = db_to_linear(nf_db)
        total_f += (stage_f - 1.0) / max(gain_product, eps)
        gain_product *= max(db_to_linear(gain_db), eps)
    return linear_to_db(total_f)


def compact_text(text: str, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def dbm_to_watt_text(dbm: float) -> str:
    watt = 10 ** ((dbm - 30.0) / 10.0)
    if watt >= 1:
        return f"{watt:.3f} W"
    if watt >= 1e-3:
        return f"{watt * 1e3:.3f} mW"
    if watt >= 1e-6:
        return f"{watt * 1e6:.3f} uW"
    if watt >= 1e-9:
        return f"{watt * 1e9:.3f} nW"
    if watt >= 1e-12:
        return f"{watt * 1e12:.3f} pW"
    return f"{watt:.3e} W"


@dataclass
class RFNode:
    node_id: str
    node_type: str
    name: str
    x: float
    y: float
    enabled: bool = True
    cable_type: str = "LMR-200"
    length_m: str = "10"
    value_db: str = "0"
    custom_loss_db_per_100m: str = "0"
    splitter_type: str = "2-way"
    splitter_custom_loss_db: str = "0"
    ports: str = "2"
    noise_figure_db: str = "0"
    p1db_dbm: str = ""
    dc_pass: bool = True
    dc_required: bool = False
    receiver_quantity: str = "1"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "RFNode":
        return RFNode(
            node_id=str(data.get("node_id", "")),
            node_type=str(data.get("node_type", "Cable")),
            name=str(data.get("name", "Node")),
            x=float(data.get("x", 100.0)),
            y=float(data.get("y", 100.0)),
            enabled=bool(data.get("enabled", True)),
            cable_type=str(data.get("cable_type", "LMR-200")),
            length_m=str(data.get("length_m", "10")),
            value_db=str(data.get("value_db", "0")),
            custom_loss_db_per_100m=str(data.get("custom_loss_db_per_100m", "0")),
            splitter_type=str(data.get("splitter_type", "2-way")),
            splitter_custom_loss_db=str(data.get("splitter_custom_loss_db", "0")),
            ports=str(data.get("ports", "2")),
            noise_figure_db=str(data.get("noise_figure_db", "0")),
            p1db_dbm=str(data.get("p1db_dbm", "")),
            dc_pass=bool(data.get("dc_pass", True)),
            dc_required=bool(data.get("dc_required", False)),
            receiver_quantity=str(data.get("receiver_quantity", "1")),
        )


@dataclass
class RFEdge:
    edge_id: str
    source_id: str
    target_id: str
    source_port: int = 1
    name: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "RFEdge":
        return RFEdge(
            edge_id=str(data.get("edge_id", "")),
            source_id=str(data.get("source_id", "")),
            target_id=str(data.get("target_id", "")),
            source_port=int(data.get("source_port", 1)),
            name=str(data.get("name", "")),
        )


@dataclass
class NodeCalc:
    node_id: str
    name: str
    node_type: str
    input_dbm: float
    output_dbm: float
    gain_db: float
    nf_db: float
    cumulative_gain_db: float
    system_nf_db: float
    dc_available: bool
    status: str
    warnings: List[str] = field(default_factory=list)


class DebouncedAction:
    def __init__(self, widget: tk.Misc, delay_ms: int, callback):
        self.widget = widget
        self.delay_ms = delay_ms
        self.callback = callback
        self._after_id: Optional[str] = None

    def schedule(self):
        self.cancel()
        self._after_id = self.widget.after(self.delay_ms, self._run)

    def run_now(self):
        self.cancel()
        self.callback()

    def cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _run(self):
        self._after_id = None
        self.callback()


class FontManager:
    def __init__(self):
        self.cache: Dict[Tuple[int, bool], object] = {}
        self.system = platform.system().lower()

    def get(self, size: int, bold: bool = False):
        if not HAS_PILLOW or ImageFont is None:
            return None
        key = (size, bold)
        if key in self.cache:
            return self.cache[key]
        for item in self._candidates(bold):
            try:
                font = ImageFont.truetype(item, size=size)
                self.cache[key] = font
                return font
            except Exception:
                pass
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            font = ImageFont.load_default()
        self.cache[key] = font
        return font

    def _candidates(self, bold: bool) -> List[str]:
        if self.system == "windows":
            base = Path("C:/Windows/Fonts")
            return [str(base / ("arialbd.ttf" if bold else "arial.ttf")), str(base / ("segoeuib.ttf" if bold else "segoeui.ttf"))]
        if self.system == "darwin":
            return ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"]
        return ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


class PropertyPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.app = app
        self.node: Optional[RFNode] = None
        self.entry_widgets: Dict[str, ctk.CTkEntry] = {}
        self.var_map: Dict[str, Union[tk.StringVar, tk.BooleanVar]] = {}
        self.build_empty()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.entry_widgets.clear()
        self.var_map.clear()

    def build_empty(self):
        self.clear()
        ctk.CTkLabel(self, text="Node Properties", text_color=COLOR_TEXT, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(self, text="Select a node to edit its RF parameters.", text_color=COLOR_MUTED, anchor="w", justify="left", wraplength=280).pack(fill="x", padx=12, pady=(0, 12))

    def show_node(self, node: RFNode):
        self.node = node
        self.clear()
        ctk.CTkLabel(self, text="Node Properties", text_color=COLOR_TEXT, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(self, text=f"{node.node_type} node", text_color=COLOR_MUTED, anchor="w").pack(fill="x", padx=12, pady=(0, 10))

        self._field("Name", "name", node.name)
        self._check("Enabled", "enabled", node.enabled)

        if node.node_type == "Cable":
            self._combo("Cable Type", "cable_type", node.cable_type, list(CABLE_LOSS_DB_PER_100M.keys()))
            self._field("Length m", "length_m", node.length_m)
            self._field("Custom dB/100 m", "custom_loss_db_per_100m", node.custom_loss_db_per_100m)
            self._check("DC Pass", "dc_pass", node.dc_pass)
        elif node.node_type == "Splitter":
            self._combo("Splitter Type", "splitter_type", node.splitter_type, list(SPLITTER_LOSS_DB.keys()))
            self._field("Custom Loss dB", "splitter_custom_loss_db", node.splitter_custom_loss_db)
            self._field("Output Ports", "ports", node.ports)
            self._check("DC Pass", "dc_pass", node.dc_pass)
        elif node.node_type == "Amplifier":
            self._field("Gain dB", "value_db", node.value_db)
            self._field("Noise Figure dB", "noise_figure_db", node.noise_figure_db)
            self._field("P1dB dBm", "p1db_dbm", node.p1db_dbm)
            self._check("DC Pass", "dc_pass", node.dc_pass)
        elif node.node_type == "Attenuator":
            self._field("Loss dB", "value_db", node.value_db)
            self._check("DC Pass", "dc_pass", node.dc_pass)
        elif node.node_type == "Receiver":
            self._field("Receiver Quantity", "receiver_quantity", node.receiver_quantity)
            self._check("DC Required", "dc_required", node.dc_required)
        elif node.node_type == "Source":
            self._check("DC Pass", "dc_pass", node.dc_pass)

        ctk.CTkButton(self, text="Apply Properties", command=self.apply, fg_color=COLOR_BLUE_DARK, hover_color=COLOR_BLUE_HOVER).pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkButton(self, text="Delete Node", command=self.delete_selected, fg_color=COLOR_RED, text_color=COLOR_RED_TEXT, hover_color=("#D98888", "#8F3D3D")).pack(fill="x", padx=12, pady=(0, 12))

    def _field(self, label: str, attr: str, value: str):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(frame, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x")
        var = tk.StringVar(value=str(value))
        ent = ctk.CTkEntry(frame, textvariable=var, fg_color=COLOR_CARD, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        ent.pack(fill="x", pady=(2, 0))
        var.trace_add("write", lambda *_: self.app.request_recalculate())
        self.var_map[attr] = var
        self.entry_widgets[attr] = ent

    def _combo(self, label: str, attr: str, value: str, values: List[str]):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(frame, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x")
        var = tk.StringVar(value=str(value))
        menu = ctk.CTkOptionMenu(frame, values=values, variable=var, command=lambda _v: self.app.request_recalculate(), fg_color=COLOR_BLUE, button_color=COLOR_BLUE_DARK, button_hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"))
        menu.pack(fill="x", pady=(2, 0))
        self.var_map[attr] = var

    def _check(self, label: str, attr: str, value: bool):
        var = tk.BooleanVar(value=bool(value))
        cb = ctk.CTkCheckBox(self, text=label, variable=var, command=self.app.request_recalculate, fg_color=COLOR_BLUE_DARK)
        cb.pack(fill="x", padx=12, pady=6)
        self.var_map[attr] = var

    def apply(self):
        if self.node is None:
            return
        for attr, var in self.var_map.items():
            try:
                setattr(self.node, attr, var.get())
            except Exception:
                pass
        self.app.recalculate()
        self.app.redraw_graph()

    def delete_selected(self):
        if self.node:
            self.app.delete_node(self.node.node_id)

    def apply_live(self):
        if self.node is None:
            return
        for attr, var in self.var_map.items():
            try:
                setattr(self.node, attr, var.get())
            except Exception:
                pass


class GraphEditor(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.app = app
        self.scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.drag_node: Optional[str] = None
        self.drag_offset = (0.0, 0.0)
        self.connect_from: Optional[str] = None
        self.pan_start: Optional[Tuple[float, float, float, float]] = None
        self.item_to_node: Dict[int, str] = {}
        self.edge_items: Dict[int, str] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=10)
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        for col in range(12):
            toolbar.grid_columnconfigure(col, weight=1)

        self._button(toolbar, "Source", lambda: app.add_node("Source")).grid(row=0, column=0, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Cable", lambda: app.add_node("Cable")).grid(row=0, column=1, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Splitter", lambda: app.add_node("Splitter")).grid(row=0, column=2, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Amplifier", lambda: app.add_node("Amplifier")).grid(row=0, column=3, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Attenuator", lambda: app.add_node("Attenuator")).grid(row=0, column=4, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Receiver", lambda: app.add_node("Receiver")).grid(row=0, column=5, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Connect", self.start_connect_mode).grid(row=0, column=6, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Auto Layout", app.auto_layout).grid(row=0, column=7, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Zoom In", lambda: self.zoom(1.15)).grid(row=0, column=8, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Zoom Out", lambda: self.zoom(0.87)).grid(row=0, column=9, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Fit", self.fit_view).grid(row=0, column=10, padx=4, pady=8, sticky="ew")
        self._button(toolbar, "Calculate", app.calculate_now).grid(row=0, column=11, padx=4, pady=8, sticky="ew")

        self.status = ctk.CTkLabel(toolbar, text="Select, drag, right-click, or use Connect.", text_color=COLOR_MUTED, anchor="w")
        self.status.grid(row=1, column=0, columnspan=12, padx=8, pady=(0, 8), sticky="ew")

        self.canvas = tk.Canvas(self, bg=drawing_color(COLOR_DIAGRAM_BG), highlightthickness=1, highlightbackground=drawing_color(COLOR_BORDER))
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom(1.1, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self.zoom(0.9, e.x, e.y))
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit Node", command=self.open_selected_properties)
        self.menu.add_command(label="Connect From This Node", command=self.start_connect_from_selected)
        self.menu.add_command(label="Delete Node", command=self.delete_selected_node)
        self.menu.add_separator()
        self.menu.add_command(label="Delete Selected Edge", command=self.delete_selected_edge)

        self.selected_edge_id: Optional[str] = None

    def _button(self, master, text, command):
        return ctk.CTkButton(master, text=text, command=command, fg_color=COLOR_BLUE_DARK, hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"), height=32)

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        return x * self.scale + self.pan_x, y * self.scale + self.pan_y

    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        return (x - self.pan_x) / self.scale, (y - self.pan_y) / self.scale

    def draw(self):
        self.canvas.delete("all")
        self.item_to_node.clear()
        self.edge_items.clear()
        self.canvas.configure(bg=drawing_color(COLOR_DIAGRAM_BG), highlightbackground=drawing_color(COLOR_BORDER))
        self.draw_grid()
        self.draw_edges()
        self.draw_nodes()

    def draw_grid(self):
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        grid_screen = GRID_SIZE * self.scale
        if grid_screen < 8:
            return
        start_x_world, start_y_world = self.screen_to_world(0, 0)
        end_x_world, end_y_world = self.screen_to_world(width, height)
        gx0 = math.floor(start_x_world / GRID_SIZE) * GRID_SIZE
        gy0 = math.floor(start_y_world / GRID_SIZE) * GRID_SIZE
        color = "#DCE8EF" if ctk.get_appearance_mode().lower() == "light" else "#223042"
        x = gx0
        while x <= end_x_world:
            sx, _ = self.world_to_screen(x, 0)
            self.canvas.create_line(sx, 0, sx, height, fill=color)
            x += GRID_SIZE
        y = gy0
        while y <= end_y_world:
            _, sy = self.world_to_screen(0, y)
            self.canvas.create_line(0, sy, width, sy, fill=color)
            y += GRID_SIZE

    def draw_edges(self):
        for edge in self.app.edges.values():
            src = self.app.nodes.get(edge.source_id)
            dst = self.app.nodes.get(edge.target_id)
            if not src or not dst:
                continue
            x1, y1 = self.world_to_screen(src.x + NODE_W, src.y + NODE_H / 2)
            x2, y2 = self.world_to_screen(dst.x, dst.y + NODE_H / 2)
            color = drawing_color(COLOR_ARROW)
            width = 4 if edge.edge_id == self.selected_edge_id else 2
            line = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=tk.LAST, smooth=True)
            self.edge_items[line] = edge.edge_id
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            label = f"Port {edge.source_port}" if src.node_type == "Splitter" else ""
            if label:
                txt = self.canvas.create_text(mx, my - 12, text=label, fill=drawing_color(COLOR_MUTED), font=("TkDefaultFont", max(7, int(9 * self.scale))))
                self.edge_items[txt] = edge.edge_id

    def draw_nodes(self):
        for node in self.app.nodes.values():
            self.draw_node(node)

    def draw_node(self, node: RFNode):
        x, y = self.world_to_screen(node.x, node.y)
        w = NODE_W * self.scale
        h = NODE_H * self.scale
        fill = drawing_color(NODE_TYPE_COLORS.get(node.node_type, COLOR_NODE_RX))
        outline = drawing_color(COLOR_RED if node.node_id == self.app.selected_node_id else COLOR_BLOCK_BORDER)
        text_fill = drawing_color(COLOR_TEXT)
        if node.node_id in self.app.calcs and self.app.calcs[node.node_id].status in ("OVERDRIVE RISK", "WEAK SIGNAL", "DC BLOCKED"):
            outline = drawing_color(COLOR_RED if self.app.calcs[node.node_id].status != "WEAK SIGNAL" else COLOR_AMBER)

        items = []
        items.append(self.canvas.create_rectangle(x + 4, y + 4, x + w + 4, y + h + 4, fill=("#D5DEE7" if ctk.get_appearance_mode().lower() == "light" else "#0B1220"), outline=""))
        items.append(self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline, width=3 if node.node_id == self.app.selected_node_id else 2))
        fs_title = max(8, int(11 * self.scale))
        fs_text = max(7, int(9 * self.scale))
        items.append(self.canvas.create_text(x + 10 * self.scale, y + 16 * self.scale, anchor="w", text=compact_text(node.name, 25), fill=text_fill, font=("TkDefaultFont", fs_title, "bold")))
        items.append(self.canvas.create_text(x + 10 * self.scale, y + 38 * self.scale, anchor="w", text=node.node_type, fill=text_fill, font=("TkDefaultFont", fs_text)))
        self.canvas.create_line(x + 10 * self.scale, y + 52 * self.scale, x + w - 10 * self.scale, y + 52 * self.scale, fill=outline)
        lines = self.node_lines(node)
        for idx, line in enumerate(lines[:3]):
            items.append(self.canvas.create_text(x + 10 * self.scale, y + (72 + 16 * idx) * self.scale, anchor="w", text=line, fill=text_fill, font=("TkDefaultFont", fs_text, "bold" if idx == 0 else "normal")))
        for item in items:
            self.item_to_node[item] = node.node_id

    def node_lines(self, node: RFNode) -> List[str]:
        calc = self.app.calcs.get(node.node_id)
        if calc:
            return [f"In {calc.input_dbm:.2f} dBm", f"Out {calc.output_dbm:.2f} dBm", calc.status]
        if node.node_type == "Cable":
            return [node.cable_type, f"{node.length_m} m", "Not calculated"]
        if node.node_type == "Splitter":
            return [node.splitter_type, f"{node.ports} ports", "Not calculated"]
        if node.node_type == "Amplifier":
            return [f"Gain {node.value_db} dB", f"NF {node.noise_figure_db} dB", "Not calculated"]
        if node.node_type == "Attenuator":
            return [f"Loss {node.value_db} dB", "Not calculated"]
        if node.node_type == "Receiver":
            return [f"Qty {node.receiver_quantity}", "Not calculated"]
        return ["RF source", "Not calculated"]

    def node_at_event(self, event) -> Optional[str]:
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)
        if not item:
            return None
        tags_node = self.item_to_node.get(item[0])
        if tags_node:
            return tags_node
        return None

    def edge_at_event(self, event) -> Optional[str]:
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)
        if not item:
            return None
        return self.edge_items.get(item[0])

    def on_left_press(self, event):
        node_id = self.node_at_event(event)
        edge_id = self.edge_at_event(event)
        if self.connect_from and node_id and node_id != self.connect_from:
            self.app.add_edge(self.connect_from, node_id)
            self.connect_from = None
            self.status.configure(text="Connection added.")
            return
        if node_id:
            self.app.select_node(node_id)
            node = self.app.nodes[node_id]
            wx, wy = self.screen_to_world(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self.drag_node = node_id
            self.drag_offset = (wx - node.x, wy - node.y)
            self.draw()
        elif edge_id:
            self.selected_edge_id = edge_id
            self.app.select_node(None)
            self.draw()
        else:
            self.selected_edge_id = None
            self.app.select_node(None)
            self.pan_start = (event.x, event.y, self.pan_x, self.pan_y)

    def on_left_drag(self, event):
        if self.drag_node:
            wx, wy = self.screen_to_world(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            node = self.app.nodes[self.drag_node]
            node.x = snap(wx - self.drag_offset[0])
            node.y = snap(wy - self.drag_offset[1])
            self.draw()
        elif self.pan_start:
            sx, sy, px, py = self.pan_start
            self.pan_x = px + event.x - sx
            self.pan_y = py + event.y - sy
            self.draw()

    def on_left_release(self, _event):
        if self.drag_node:
            self.app.recalculate()
        self.drag_node = None
        self.pan_start = None

    def on_pan_start(self, event):
        self.pan_start = (event.x, event.y, self.pan_x, self.pan_y)

    def on_pan_drag(self, event):
        if not self.pan_start:
            return
        sx, sy, px, py = self.pan_start
        self.pan_x = px + event.x - sx
        self.pan_y = py + event.y - sy
        self.draw()

    def on_right_click(self, event):
        node_id = self.node_at_event(event)
        edge_id = self.edge_at_event(event)
        self.app.select_node(node_id)
        self.selected_edge_id = edge_id
        self.draw()
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def on_double_click(self, event):
        node_id = self.node_at_event(event)
        if node_id:
            self.app.select_node(node_id)

    def start_connect_mode(self):
        if self.app.selected_node_id:
            self.connect_from = self.app.selected_node_id
            self.status.configure(text=f"Connect from {self.app.nodes[self.connect_from].name}: click target node.")
        else:
            self.status.configure(text="Select a source node first, then press Connect.")

    def start_connect_from_selected(self):
        if self.app.selected_node_id:
            self.connect_from = self.app.selected_node_id
            self.status.configure(text=f"Connect from {self.app.nodes[self.connect_from].name}: click target node.")

    def open_selected_properties(self):
        if self.app.selected_node_id:
            self.app.property_panel.show_node(self.app.nodes[self.app.selected_node_id])

    def delete_selected_node(self):
        if self.app.selected_node_id:
            self.app.delete_node(self.app.selected_node_id)

    def delete_selected_edge(self):
        if self.selected_edge_id:
            self.app.delete_edge(self.selected_edge_id)
            self.selected_edge_id = None

    def zoom(self, factor: float, cx: Optional[float] = None, cy: Optional[float] = None):
        if cx is None:
            cx = self.canvas.winfo_width() / 2
        if cy is None:
            cy = self.canvas.winfo_height() / 2
        wx, wy = self.screen_to_world(cx, cy)
        self.scale = max(0.35, min(2.5, self.scale * factor))
        self.pan_x = cx - wx * self.scale
        self.pan_y = cy - wy * self.scale
        self.draw()

    def on_mousewheel(self, event):
        self.zoom(1.1 if event.delta > 0 else 0.9, event.x, event.y)

    def fit_view(self):
        if not self.app.nodes:
            return
        min_x = min(n.x for n in self.app.nodes.values())
        min_y = min(n.y for n in self.app.nodes.values())
        max_x = max(n.x + NODE_W for n in self.app.nodes.values())
        max_y = max(n.y + NODE_H for n in self.app.nodes.values())
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        sx = canvas_w / max(1, max_x - min_x + 160)
        sy = canvas_h / max(1, max_y - min_y + 160)
        self.scale = max(0.35, min(1.6, min(sx, sy)))
        self.pan_x = 80 - min_x * self.scale
        self.pan_y = 80 - min_y * self.scale
        self.draw()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1720x980")
        self.minsize(1500, 860)
        self.configure(fg_color=COLOR_APP_BG)

        self.nodes: Dict[str, RFNode] = {}
        self.edges: Dict[str, RFEdge] = {}
        self.calcs: Dict[str, NodeCalc] = {}
        self.selected_node_id: Optional[str] = None
        self.next_node_number = 1
        self.next_edge_number = 1
        self._is_loading = False
        self.global_warnings: List[str] = []

        self.scenario_var = tk.StringVar(value="GNSS Graph Network")
        self.band_var = tk.StringVar(value=list(GNSS_BANDS_MHZ.keys())[0])
        self.freq_var = tk.StringVar(value=str(GNSS_BANDS_MHZ[self.band_var.get()]))
        self.source_var = tk.StringVar(value="1")
        self.receiver_preset_var = tk.StringVar(value="Conservative GNSS receiver window")
        self.min_var = tk.StringVar(value="-130")
        self.max_var = tk.StringVar(value="-35")
        self.target_var = tk.StringVar(value="-100")

        self.debouncer = DebouncedAction(self, DEBOUNCE_MS, self.recalculate)

        self._build_ui()
        self.load_example()

    def _button(self, master, text, command):
        return ctk.CTkButton(master, text=text, command=command, fg_color=COLOR_BLUE_DARK, hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"), height=32)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=APP_TITLE, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, padx=18, pady=(14, 0), sticky="ew")
        ctk.CTkLabel(header, text=f"{APP_BRAND}  |  True graphical RF network editor", text_color=COLOR_MUTED, anchor="w", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=18, pady=(2, 14), sticky="ew")

        settings = ctk.CTkFrame(self, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        settings.grid(row=1, column=0, sticky="ew", padx=14, pady=(12, 0))
        for col in range(12):
            settings.grid_columnconfigure(col, weight=1)

        self._labeled_entry(settings, "Scenario", self.scenario_var, 0, 0, 2)
        self._band_control(settings, 0, 2, 3)
        self.freq_entry = self._labeled_entry(settings, "Freq MHz", self.freq_var, 0, 5, 1)
        self.source_entry = self._labeled_entry(settings, "Source dBm", self.source_var, 0, 6, 1)
        self._preset_control(settings, 0, 7, 2)
        self.min_entry = self._labeled_entry(settings, "Min dBm", self.min_var, 0, 9, 1)
        self.max_entry = self._labeled_entry(settings, "Max dBm", self.max_var, 0, 10, 1)
        self.target_entry = self._labeled_entry(settings, "Target dBm", self.target_var, 0, 11, 1)

        self.main = ctk.CTkFrame(self, fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.main.grid(row=2, column=0, padx=14, pady=14, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=5)
        self.main.grid_columnconfigure(1, weight=0, minsize=330)
        self.main.grid_rowconfigure(0, weight=1)

        self.graph = GraphEditor(self.main, self)
        self.graph.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        right = ctk.CTkFrame(self.main, fg_color=COLOR_PANEL, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_rowconfigure(2, weight=1)

        action_bar = ctk.CTkFrame(right, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=10)
        action_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        action_bar.grid_columnconfigure(0, weight=1)
        action_bar.grid_columnconfigure(1, weight=1)
        self._button(action_bar, "Save JSON", self.save_json).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self._button(action_bar, "Load JSON", self.load_json).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self._button(action_bar, "Export CSV", self.export_csv).grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        self._button(action_bar, "Export PNG", self.export_png).grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        self._button(action_bar, "New Example", self.load_example).grid(row=2, column=0, padx=6, pady=6, sticky="ew")
        self._button(action_bar, "Clear All", self.clear_all).grid(row=2, column=1, padx=6, pady=6, sticky="ew")

        self.property_panel = PropertyPanel(right, self)
        self.property_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 8))

        self.results_box = ctk.CTkTextbox(right, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=10, text_color=COLOR_TEXT, font=ctk.CTkFont(family="Consolas", size=10))
        self.results_box.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)

        for var in [self.scenario_var, self.freq_var, self.source_var, self.min_var, self.max_var, self.target_var]:
            var.trace_add("write", lambda *_: self.request_recalculate())

    def _labeled_entry(self, master, label, variable, row, col, colspan):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        entry = ctk.CTkEntry(frame, textvariable=variable, fg_color=COLOR_CARD, border_color=COLOR_BORDER, text_color=COLOR_TEXT, height=30)
        entry.grid(row=1, column=0, sticky="ew")
        frame.grid(row=row, column=col, columnspan=colspan, padx=7, pady=8, sticky="ew")
        return entry

    def _band_control(self, master, row, col, colspan):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="GNSS Band", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        menu = ctk.CTkOptionMenu(frame, values=list(GNSS_BANDS_MHZ.keys()), variable=self.band_var, command=self.band_changed, fg_color=COLOR_BLUE, button_color=COLOR_BLUE_DARK, button_hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"), dropdown_fg_color=COLOR_CARD, dropdown_text_color=COLOR_TEXT, dropdown_hover_color=COLOR_PANEL_ALT, height=30)
        menu.grid(row=1, column=0, sticky="ew")
        frame.grid(row=row, column=col, columnspan=colspan, padx=7, pady=8, sticky="ew")

    def _preset_control(self, master, row, col, colspan):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Receiver Preset", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        menu = ctk.CTkOptionMenu(frame, values=list(RECEIVER_PRESETS.keys()), variable=self.receiver_preset_var, command=self.receiver_preset_changed, fg_color=COLOR_BLUE, button_color=COLOR_BLUE_DARK, button_hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"), dropdown_fg_color=COLOR_CARD, dropdown_text_color=COLOR_TEXT, dropdown_hover_color=COLOR_PANEL_ALT, height=30)
        menu.grid(row=1, column=0, sticky="ew")
        frame.grid(row=row, column=col, columnspan=colspan, padx=7, pady=8, sticky="ew")

    def band_changed(self, value: str):
        if value != "Custom":
            self.freq_var.set(str(GNSS_BANDS_MHZ[value]))
        self.request_recalculate()

    def receiver_preset_changed(self, value: str):
        if value != "Custom":
            mn, mx, target = RECEIVER_PRESETS[value]
            self.min_var.set(str(mn))
            self.max_var.set(str(mx))
            self.target_var.set(str(target))
        self.request_recalculate()

    def request_recalculate(self):
        if not self._is_loading:
            self.debouncer.schedule()

    def calculate_now(self):
        self.debouncer.run_now()

    def new_node_id(self) -> str:
        node_id = f"N{self.next_node_number:03d}"
        self.next_node_number += 1
        return node_id

    def new_edge_id(self) -> str:
        edge_id = f"E{self.next_edge_number:03d}"
        self.next_edge_number += 1
        return edge_id

    def add_node(self, node_type: str, x: Optional[float] = None, y: Optional[float] = None):
        node_id = self.new_node_id()
        if x is None or y is None:
            x = 160 + (len(self.nodes) % 5) * 260
            y = 120 + (len(self.nodes) // 5) * 170
        name = f"{node_type} {node_id}"
        node = RFNode(node_id=node_id, node_type=node_type, name=name, x=snap(x), y=snap(y))
        if node_type == "Source":
            node.name = "GNSS Source"
        elif node_type == "Receiver":
            node.name = f"Receiver {node_id}"
            node.dc_pass = False
        elif node_type == "Amplifier":
            node.value_db = "20"
            node.noise_figure_db = "2"
            node.p1db_dbm = "10"
        elif node_type == "Attenuator":
            node.value_db = "6"
        elif node_type == "Splitter":
            node.splitter_type = "2-way"
            node.ports = "2"
        self.nodes[node_id] = node
        self.select_node(node_id)
        self.recalculate()
        self.redraw_graph()

    def delete_node(self, node_id: str):
        if node_id not in self.nodes:
            return
        self.edges = {eid: e for eid, e in self.edges.items() if e.source_id != node_id and e.target_id != node_id}
        del self.nodes[node_id]
        if self.selected_node_id == node_id:
            self.selected_node_id = None
            self.property_panel.build_empty()
        self.recalculate()
        self.redraw_graph()

    def add_edge(self, source_id: str, target_id: str):
        if source_id == target_id or source_id not in self.nodes or target_id not in self.nodes:
            return
        if self.nodes[target_id].node_type == "Source":
            messagebox.showwarning("Invalid Connection", "A source node cannot be the target of another RF path.")
            return
        for edge in self.edges.values():
            if edge.source_id == source_id and edge.target_id == target_id:
                return

        source_node = self.nodes[source_id]
        source_port = 1
        if source_node.node_type == "Splitter":
            used_ports = {e.source_port for e in self.edges.values() if e.source_id == source_id}
            port_limit = max(1, self.node_port_count(source_node))
            available = [p for p in range(1, port_limit + 1) if p not in used_ports]
            if not available:
                messagebox.showwarning("No Splitter Port", f"{source_node.name} has no unused output port.")
                return
            source_port = available[0]

        edge = RFEdge(edge_id=self.new_edge_id(), source_id=source_id, target_id=target_id, source_port=source_port)
        self.edges[edge.edge_id] = edge
        self.recalculate()
        self.redraw_graph()

    def delete_edge(self, edge_id: str):
        if edge_id in self.edges:
            del self.edges[edge_id]
            self.recalculate()
            self.redraw_graph()

    def node_port_count(self, node: RFNode) -> int:
        if node.node_type != "Splitter":
            return 1
        try:
            if node.splitter_type != "Custom Splitter" and "-way" in node.splitter_type:
                return int(node.splitter_type.split("-")[0])
            return max(1, int(round(float(node.ports))))
        except Exception:
            return 1

    def select_node(self, node_id: Optional[str]):
        self.selected_node_id = node_id
        if node_id and node_id in self.nodes:
            self.property_panel.show_node(self.nodes[node_id])
        else:
            self.property_panel.build_empty()

    def clear_all(self):
        if not messagebox.askyesno("Clear Network", "Clear all nodes and connections?"):
            return
        self.nodes.clear()
        self.edges.clear()
        self.calcs.clear()
        self.selected_node_id = None
        self.next_node_number = 1
        self.next_edge_number = 1
        self.property_panel.build_empty()
        self.update_results()
        self.redraw_graph()

    def load_example(self):
        self._is_loading = True
        try:
            self.nodes.clear()
            self.edges.clear()
            self.calcs.clear()
            self.next_node_number = 1
            self.next_edge_number = 1
            self.scenario_var.set("Example: Graph RF network with splitter branches")
            self.band_var.set(list(GNSS_BANDS_MHZ.keys())[0])
            self.freq_var.set(str(GNSS_BANDS_MHZ[self.band_var.get()]))
            self.source_var.set("1")
            self.min_var.set("-130")
            self.max_var.set("-35")
            self.target_var.set("-100")

            source = RFNode(self.new_node_id(), "Source", "GNSS Source", 80, 240)
            amp = RFNode(self.new_node_id(), "Amplifier", "Main amplifier", 360, 240, value_db="20", noise_figure_db="2", p1db_dbm="10")
            split = RFNode(self.new_node_id(), "Splitter", "Main 16-way splitter", 640, 240, splitter_type="16-way", ports="16")
            cable1 = RFNode(self.new_node_id(), "Cable", "Cable to Cube 2025", 930, 80, cable_type="LMR-200", length_m="48")
            rx1 = RFNode(self.new_node_id(), "Receiver", "Cube 2025 Receiver", 1220, 80, receiver_quantity="1")
            cable2 = RFNode(self.new_node_id(), "Cable", "Cable to Cube 2142", 930, 260, cable_type="LMR-200", length_m="115")
            atten = RFNode(self.new_node_id(), "Attenuator", "Local 6 dB attenuator", 1210, 260, value_db="6")
            split2 = RFNode(self.new_node_id(), "Splitter", "Cube 2142 6-way", 1490, 260, splitter_type="6-way", ports="6")
            rx2 = RFNode(self.new_node_id(), "Receiver", "Cube 2142 receivers", 1770, 260, receiver_quantity="6")
            cable3 = RFNode(self.new_node_id(), "Cable", "Reference cable", 930, 440, cable_type="LMR-240", length_m="30")
            rx3 = RFNode(self.new_node_id(), "Receiver", "Reference Receiver", 1220, 440, receiver_quantity="1", dc_required=True)

            for n in [source, amp, split, cable1, rx1, cable2, atten, split2, rx2, cable3, rx3]:
                self.nodes[n.node_id] = n
            self.add_edge_no_calc(source.node_id, amp.node_id)
            self.add_edge_no_calc(amp.node_id, split.node_id)
            self.add_edge_no_calc(split.node_id, cable1.node_id, 1)
            self.add_edge_no_calc(cable1.node_id, rx1.node_id)
            self.add_edge_no_calc(split.node_id, cable2.node_id, 2)
            self.add_edge_no_calc(cable2.node_id, atten.node_id)
            self.add_edge_no_calc(atten.node_id, split2.node_id)
            self.add_edge_no_calc(split2.node_id, rx2.node_id, 1)
            self.add_edge_no_calc(split.node_id, cable3.node_id, 3)
            self.add_edge_no_calc(cable3.node_id, rx3.node_id)
            self.selected_node_id = source.node_id
        finally:
            self._is_loading = False
        self.recalculate()
        self.property_panel.show_node(self.nodes[self.selected_node_id])
        self.graph.fit_view()

    def add_edge_no_calc(self, source_id: str, target_id: str, port: int = 1):
        edge = RFEdge(self.new_edge_id(), source_id, target_id, source_port=port)
        self.edges[edge.edge_id] = edge

    def auto_layout(self):
        sources = [n for n in self.nodes.values() if n.node_type == "Source"]
        roots = sources or list(self.nodes.values())[:1]
        if not roots:
            return

        children: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        indeg: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges.values():
            if edge.source_id in children and edge.target_id in self.nodes:
                children[edge.source_id].append(edge.target_id)
                indeg[edge.target_id] = indeg.get(edge.target_id, 0) + 1

        levels: Dict[str, int] = {}
        queue: List[str] = [r.node_id for r in roots]
        for r in roots:
            levels[r.node_id] = 0
        while queue:
            current = queue.pop(0)
            for child in children.get(current, []):
                level = levels[current] + 1
                if child not in levels or level > levels[child]:
                    levels[child] = level
                    queue.append(child)

        for nid in self.nodes:
            if nid not in levels:
                levels[nid] = max(levels.values(), default=0) + 1

        buckets: Dict[int, List[str]] = {}
        for nid, lev in levels.items():
            buckets.setdefault(lev, []).append(nid)

        for lev, ids in buckets.items():
            ids.sort(key=lambda item: self.nodes[item].y)
            for idx, nid in enumerate(ids):
                self.nodes[nid].x = 80 + lev * 290
                self.nodes[nid].y = 100 + idx * 170
        self.recalculate()
        self.redraw_graph()
        self.graph.fit_view()

    def recalculate(self):
        try:
            self.property_panel.apply_live()
            freq_mhz = safe_float(self.freq_var.get(), 1575.42, self.freq_entry, allow_blank=False, field_name="Frequency MHz")
            source_dbm = safe_float(self.source_var.get(), 1.0, self.source_entry, allow_blank=False, field_name="Source dBm")
            min_dbm = safe_float(self.min_var.get(), -130.0, self.min_entry, allow_blank=False, field_name="Receiver minimum dBm")
            max_dbm = safe_float(self.max_var.get(), -35.0, self.max_entry, allow_blank=False, field_name="Receiver maximum dBm")
            target_dbm = safe_float(self.target_var.get(), -100.0, self.target_entry, allow_blank=False, field_name="Target dBm")
        except InputValidationHold as exc:
            self.show_hold(str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Calculation Error", f"Input validation failed.\n\nDetail: {exc}")
            return

        self.calcs.clear()
        self.global_warnings = []
        if freq_mhz < 1000.0 or freq_mhz > 1800.0:
            self.global_warnings.append(f"Frequency {freq_mhz:.1f} MHz is outside the 1000 to 1800 MHz cable table range.")

        children: Dict[str, List[RFEdge]] = {nid: [] for nid in self.nodes}
        for edge in self.edges.values():
            if edge.source_id in self.nodes and edge.target_id in self.nodes:
                children.setdefault(edge.source_id, []).append(edge)
        for edges in children.values():
            edges.sort(key=lambda e: e.source_port)

        sources = [n for n in self.nodes.values() if n.node_type == "Source" and n.enabled]
        if not sources:
            self.global_warnings.append("No enabled Source node exists.")
        visited_path: Set[str] = set()

        for source in sources:
            calc = NodeCalc(source.node_id, source.name, source.node_type, source_dbm, source_dbm, 0.0, 0.0, 0.0, 0.0, True, "SOURCE", [])
            self.calcs[source.node_id] = calc
            self._walk(source.node_id, children, calc, [], visited_path, freq_mhz, min_dbm, max_dbm, target_dbm)

        for nid, node in self.nodes.items():
            if node.node_type == "Receiver" and nid not in self.calcs and node.enabled:
                self.global_warnings.append(f"Receiver {node.name} is not connected to a calculated source path.")

        self.update_results()
        self.redraw_graph()

    def _walk(
        self,
        node_id: str,
        children: Dict[str, List[RFEdge]],
        parent_calc: NodeCalc,
        nf_stages: List[Tuple[float, float]],
        path: Set[str],
        freq_mhz: float,
        min_dbm: float,
        max_dbm: float,
        target_dbm: float,
    ):
        if node_id in path:
            self.global_warnings.append("Cycle detected. A loop was ignored during calculation.")
            return
        path = set(path)
        path.add(node_id)

        for edge in children.get(node_id, []):
            child = self.nodes.get(edge.target_id)
            parent = self.nodes.get(edge.source_id)
            if child is None or parent is None or not child.enabled:
                continue
            try:
                child_calc, child_nf_stages = self.calculate_node(child, parent_calc, nf_stages, edge, freq_mhz, min_dbm, max_dbm, target_dbm)
                self.calcs[child.node_id] = child_calc
                self._walk(child.node_id, children, child_calc, child_nf_stages, path, freq_mhz, min_dbm, max_dbm, target_dbm)
            except InputValidationHold as exc:
                self.global_warnings.append(str(exc))
            except Exception as exc:
                self.global_warnings.append(f"{child.name}: calculation failed: {exc}")

    def calculate_node(
        self,
        node: RFNode,
        parent_calc: NodeCalc,
        nf_stages: List[Tuple[float, float]],
        edge: RFEdge,
        freq_mhz: float,
        min_dbm: float,
        max_dbm: float,
        target_dbm: float,
    ) -> Tuple[NodeCalc, List[Tuple[float, float]]]:
        input_dbm = parent_calc.output_dbm
        gain_db = 0.0
        nf_db = 0.0
        dc_available = parent_calc.dc_available and node.dc_pass
        warnings: List[str] = []

        if node.node_type == "Cable":
            length_m = safe_float(node.length_m, 0.0, field_name=f"{node.name} length")
            custom = safe_float(node.custom_loss_db_per_100m, 0.0, field_name=f"{node.name} custom cable loss")
            loss = cable_loss_db(node.cable_type, length_m, freq_mhz, custom)
            gain_db = -loss
            nf_db = loss
        elif node.node_type == "Splitter":
            loss = SPLITTER_LOSS_DB.get(node.splitter_type, 0.0)
            if node.splitter_type == "Custom Splitter":
                loss = abs(safe_float(node.splitter_custom_loss_db, 0.0, field_name=f"{node.name} custom splitter loss"))
            gain_db = -loss
            nf_db = loss
            port_limit = self.node_port_count(node)
            if edge.source_port > port_limit:
                warnings.append(f"Output port {edge.source_port} exceeds configured {port_limit} ports.")
        elif node.node_type == "Amplifier":
            gain_db = safe_float(node.value_db, 0.0, field_name=f"{node.name} gain")
            nf_db = max(0.0, safe_float(node.noise_figure_db, 2.0, field_name=f"{node.name} noise figure"))
        elif node.node_type == "Attenuator":
            loss = abs(safe_float(node.value_db, 0.0, field_name=f"{node.name} attenuation"))
            gain_db = -loss
            nf_db = loss
        elif node.node_type == "Receiver":
            gain_db = 0.0
            nf_db = 0.0
            if node.dc_required and not parent_calc.dc_available:
                dc_available = False
                warnings.append("DC path blocked while receiver requires DC.")
        elif node.node_type == "Source":
            gain_db = 0.0
            nf_db = 0.0

        output_dbm = input_dbm + gain_db
        cumulative_gain = parent_calc.cumulative_gain_db + gain_db
        new_nf_stages = list(nf_stages)
        if node.node_type not in ("Source", "Receiver"):
            new_nf_stages.append((gain_db, nf_db))
        system_nf = cascade_noise_figure_db(new_nf_stages)

        if node.node_type in ("Amplifier",):
            if node.p1db_dbm.strip():
                p1db = safe_float(node.p1db_dbm, 10.0, field_name=f"{node.name} P1dB")
                if output_dbm > p1db - 10.0:
                    warnings.append(f"Output {output_dbm:.2f} dBm is within 10 dB of P1dB {p1db:.2f} dBm.")

        if node.node_type == "Receiver":
            if node.dc_required and not dc_available:
                status = "DC BLOCKED"
            elif output_dbm < min_dbm:
                status = "WEAK SIGNAL"
            elif output_dbm > max_dbm:
                status = "OVERDRIVE RISK"
            elif abs(output_dbm - target_dbm) <= 3.0:
                status = "NEAR TARGET"
            else:
                status = "PASS"
        else:
            status = "PASS" if not warnings else "WARNING"

        return (
            NodeCalc(node.node_id, node.name, node.node_type, input_dbm, output_dbm, gain_db, nf_db, cumulative_gain, system_nf, dc_available, status, warnings),
            new_nf_stages,
        )

    def show_hold(self, msg: str):
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"Calculation paused.\n\n{msg}\n\nFinish typing the value, then press Calculate.")
        self.results_box.configure(state="disabled")

    def update_results(self):
        receivers = [n for n in self.nodes.values() if n.node_type == "Receiver"]
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"{self.scenario_var.get()}\n")
        self.results_box.insert("end", "=" * 80 + "\n")
        for w in self.global_warnings:
            self.results_box.insert("end", f"Warning: {w}\n")
        if self.global_warnings:
            self.results_box.insert("end", "\n")
        self.results_box.insert("end", f"{'Receiver':<24} {'Level':>10} {'Margin':>10} {'NF':>8} {'DC':>8} {'Status':>14}\n")
        self.results_box.insert("end", "-" * 80 + "\n")
        target = float(self.target_var.get() or "-100") if self.target_var.get().strip() not in {"", "-", "."} else -100.0
        for rx in receivers:
            calc = self.calcs.get(rx.node_id)
            if not calc:
                self.results_box.insert("end", f"{rx.name[:24]:<24} {'N/C':>10} {'N/C':>10} {'N/C':>8} {'N/C':>8} {'NOT CONNECTED':>14}\n")
                continue
            dc = "OK" if calc.dc_available else "Blocked"
            self.results_box.insert("end", f"{rx.name[:24]:<24} {calc.output_dbm:>10.2f} {calc.output_dbm - target:>+10.2f} {calc.system_nf_db:>8.2f} {dc:>8} {calc.status:>14}\n")
            for warning in calc.warnings:
                self.results_box.insert("end", f"  Warning: {warning}\n")
        self.results_box.configure(state="disabled")

    def redraw_graph(self):
        if hasattr(self, "graph"):
            self.graph.draw()

    def project_to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "app": APP_TITLE,
            "scenario": self.scenario_var.get(),
            "band": self.band_var.get(),
            "frequency_mhz": self.freq_var.get(),
            "source_dbm": self.source_var.get(),
            "receiver_preset": self.receiver_preset_var.get(),
            "receiver_min_dbm": self.min_var.get(),
            "receiver_max_dbm": self.max_var.get(),
            "target_dbm": self.target_var.get(),
            "next_node_number": self.next_node_number,
            "next_edge_number": self.next_edge_number,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
        }

    def load_project_dict(self, data: dict):
        self._is_loading = True
        try:
            self.nodes.clear()
            self.edges.clear()
            self.scenario_var.set(str(data.get("scenario", "GNSS Graph Network")))
            self.band_var.set(str(data.get("band", list(GNSS_BANDS_MHZ.keys())[0])))
            self.freq_var.set(str(data.get("frequency_mhz", "1575.42")))
            self.source_var.set(str(data.get("source_dbm", "1")))
            self.receiver_preset_var.set(str(data.get("receiver_preset", "Custom")))
            self.min_var.set(str(data.get("receiver_min_dbm", "-130")))
            self.max_var.set(str(data.get("receiver_max_dbm", "-35")))
            self.target_var.set(str(data.get("target_dbm", "-100")))
            self.next_node_number = int(data.get("next_node_number", 1))
            self.next_edge_number = int(data.get("next_edge_number", 1))
            for node_data in data.get("nodes", []):
                node = RFNode.from_dict(node_data)
                if node.node_id:
                    self.nodes[node.node_id] = node
            for edge_data in data.get("edges", []):
                edge = RFEdge.from_dict(edge_data)
                if edge.edge_id and edge.source_id in self.nodes and edge.target_id in self.nodes:
                    self.edges[edge.edge_id] = edge
            self.selected_node_id = None
        finally:
            self._is_loading = False
        self.recalculate()
        self.redraw_graph()

    def save_json(self):
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Save GNSS R03 Project", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.project_to_dict(), handle, indent=2)
            messagebox.showinfo("Saved", f"Project saved:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Save Failed", f"Permission denied.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Unable to save file.\n\nDetail: {exc}")

    def load_json(self):
        path = filedialog.askopenfilename(title="Load GNSS R03 Project", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Top-level JSON must be an object.", doc="", pos=0)
            self.load_project_dict(data)
            messagebox.showinfo("Loaded", f"Project loaded:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Load Failed", f"Permission denied.\n\nDetail: {exc}")
        except json.JSONDecodeError as exc:
            messagebox.showerror("Load Failed", f"Invalid JSON file.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Load Failed", f"Unable to read file.\n\nDetail: {exc}")
        except Exception as exc:
            messagebox.showerror("Load Failed", f"Project load failed.\n\nDetail: {exc}")

    def export_csv(self):
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Export GNSS R03 CSV", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([APP_TITLE])
                writer.writerow([APP_BRAND])
                writer.writerow(["Scenario", self.scenario_var.get()])
                writer.writerow(["Band", self.band_var.get()])
                writer.writerow(["Frequency MHz", self.freq_var.get()])
                writer.writerow(["Source dBm", self.source_var.get()])
                writer.writerow([])
                writer.writerow(["Nodes"])
                writer.writerow(["Node ID", "Name", "Type", "Input dBm", "Output dBm", "Gain dB", "System NF dB", "DC Available", "Status", "Warnings"])
                for node in self.nodes.values():
                    calc = self.calcs.get(node.node_id)
                    if calc:
                        writer.writerow([node.node_id, node.name, node.node_type, f"{calc.input_dbm:.2f}", f"{calc.output_dbm:.2f}", f"{calc.gain_db:.2f}", f"{calc.system_nf_db:.2f}", calc.dc_available, calc.status, " | ".join(calc.warnings)])
                    else:
                        writer.writerow([node.node_id, node.name, node.node_type, "", "", "", "", "", "NOT CALCULATED", ""])
                writer.writerow([])
                writer.writerow(["Edges"])
                writer.writerow(["Edge ID", "Source", "Target", "Source Port"])
                for edge in self.edges.values():
                    writer.writerow([edge.edge_id, edge.source_id, edge.target_id, edge.source_port])
            messagebox.showinfo("Exported", f"CSV exported:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Export Failed", f"Permission denied.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Unable to write CSV.\n\nDetail: {exc}")

    def export_png(self):
        if not HAS_PILLOW:
            messagebox.showerror("Pillow Missing", "PNG export requires Pillow. Install it with:\n\npip install pillow")
            return
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Export GNSS R03 PNG", defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not path:
            return
        try:
            self.render_png(path)
            messagebox.showinfo("Exported", f"PNG exported:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Export Failed", f"Permission denied.\n\nDetail: {exc}")
        except Exception as exc:
            messagebox.showerror("Export Failed", f"PNG export failed.\n\nDetail: {exc}")

    def render_png(self, filepath: str):
        if not HAS_PILLOW or Image is None or ImageDraw is None:
            raise RuntimeError("Pillow is not available.")

        fm = FontManager()
        title_font = fm.get(22, True)
        head_font = fm.get(12, True)
        text_font = fm.get(9, False)

        if not self.nodes:
            image = Image.new("RGB", (1000, 700), light_color(COLOR_DIAGRAM_BG))
            image.save(filepath)
            return

        min_x = min(n.x for n in self.nodes.values())
        min_y = min(n.y for n in self.nodes.values())
        max_x = max(n.x + NODE_W for n in self.nodes.values())
        max_y = max(n.y + NODE_H for n in self.nodes.values())
        pad = 120
        width = int(max(1000, max_x - min_x + pad * 2))
        height = int(max(700, max_y - min_y + pad * 2))
        image = Image.new("RGB", (width, height), light_color(COLOR_DIAGRAM_BG))
        draw = ImageDraw.Draw(image)

        def tx(x):
            return x - min_x + pad

        def ty(y):
            return y - min_y + pad

        draw.text((40, 30), APP_TITLE, fill=light_color(COLOR_TEXT), font=title_font)
        draw.text((40, 62), self.scenario_var.get(), fill=light_color(COLOR_MUTED), font=text_font)

        for edge in self.edges.values():
            src = self.nodes.get(edge.source_id)
            dst = self.nodes.get(edge.target_id)
            if not src or not dst:
                continue
            x1 = tx(src.x + NODE_W)
            y1 = ty(src.y + NODE_H / 2)
            x2 = tx(dst.x)
            y2 = ty(dst.y + NODE_H / 2)
            draw.line((x1, y1, x2, y2), fill=light_color(COLOR_ARROW), width=3)
            draw.polygon([(x2, y2), (x2 - 12, y2 - 6), (x2 - 12, y2 + 6)], fill=light_color(COLOR_ARROW))
            if src.node_type == "Splitter":
                draw.text(((x1 + x2) / 2, (y1 + y2) / 2 - 12), f"Port {edge.source_port}", fill=light_color(COLOR_MUTED), font=text_font)

        for node in self.nodes.values():
            x = tx(node.x)
            y = ty(node.y)
            fill = light_color(NODE_TYPE_COLORS.get(node.node_type, COLOR_NODE_RX))
            outline = light_color(COLOR_BLOCK_BORDER)
            draw.rectangle((x + 4, y + 4, x + NODE_W + 4, y + NODE_H + 4), fill="#D5DEE7")
            draw.rectangle((x, y, x + NODE_W, y + NODE_H), fill=fill, outline=outline, width=2)
            draw.text((x + 10, y + 10), compact_text(node.name, 25), fill=light_color(COLOR_TEXT), font=head_font)
            draw.text((x + 10, y + 32), node.node_type, fill=light_color(COLOR_TEXT), font=text_font)
            draw.line((x + 10, y + 52, x + NODE_W - 10, y + 52), fill=outline, width=1)
            lines = self.graph.node_lines(node) if hasattr(self, "graph") else []
            for idx, line in enumerate(lines[:3]):
                draw.text((x + 10, y + 68 + idx * 16), line, fill=light_color(COLOR_TEXT), font=text_font)

        image.save(filepath, "PNG")


if __name__ == "__main__":
    app = App()
    app.mainloop()
