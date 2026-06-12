"""
GNSS Multipath R02
SAYAR Production House

Multi-branch GNSS RF distribution calculator with aligned card-based GUI.

Install:
    pip install customtkinter pillow

Run:
    python GNSS_R02.py
"""

from __future__ import annotations

import csv
import json
import math
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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

APP_TITLE = "GNSS Multipath R02"
APP_BRAND = "SAYAR Production House"
SCHEMA_VERSION = "R02"
DEBOUNCE_MS = 350

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
COLOR_BLOCK_FILL: ColorPair = ("#FFFFFF", "#2B384A")
COLOR_BLOCK_BORDER: ColorPair = ("#467EA3", "#72A8CE")
COLOR_ARROW: ColorPair = ("#2E6F98", "#88C7EF")
COLOR_CABLE: ColorPair = ("#EAF4FB", "#1E3A4A")

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
    "None": 0.0,
    "2-way": 3.6,
    "3-way": 5.8,
    "4-way": 7.2,
    "6-way": 8.7,
    "8-way": 10.5,
    "12-way": 12.3,
    "16-way": 14.2,
    "Custom Splitter": 0.0,
}

COMPONENT_TYPES = [
    "Cable",
    "Splitter",
    "Attenuator",
    "Amplifier",
    "Bias-T",
    "DC Block",
    "Connector Pair",
    "Lightning Protector",
    "Custom Loss",
    "Custom Gain",
]

RECEIVER_PRESETS: Dict[str, Tuple[float, float, float]] = {
    "Conservative GNSS receiver window": (-130.0, -35.0, -100.0),
    "Weak-signal simulation": (-145.0, -65.0, -125.0),
    "Indoor re-radiated GNSS distribution": (-125.0, -45.0, -95.0),
    "Lab conducted GNSS receiver input": (-120.0, -30.0, -85.0),
    "Custom": (-130.0, -35.0, -100.0),
}

DEFAULT_RECEIVER_MIN_DBM = -130.0
DEFAULT_RECEIVER_MAX_DBM = -35.0
DEFAULT_TARGET_DBM = -100.0


class InputValidationHold(Exception):
    """Raised when a numeric input is incomplete or invalid during live editing."""


def light_color(color: Union[str, ColorPair]) -> str:
    return color[0] if isinstance(color, tuple) else color


def dark_color(color: Union[str, ColorPair]) -> str:
    return color[1] if isinstance(color, tuple) else color


def drawing_color(color: Union[str, ColorPair]) -> str:
    return dark_color(color) if ctk.get_appearance_mode().lower() == "dark" else light_color(color)


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


def safe_float(
    value: object,
    default: float = 0.0,
    entry: Optional[ctk.CTkEntry] = None,
    allow_blank: bool = True,
    field_name: str = "numeric field",
) -> float:
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


def safe_int(
    value: object,
    default: int = 1,
    minimum: int = 0,
    entry: Optional[ctk.CTkEntry] = None,
    allow_blank: bool = True,
    field_name: str = "integer field",
) -> int:
    number = safe_float(value, float(default), entry=entry, allow_blank=allow_blank, field_name=field_name)
    result = int(round(number))
    if result < minimum:
        set_entry_valid(entry, False)
        raise InputValidationHold(f"{field_name} must be at least {minimum}.")
    set_entry_valid(entry, True)
    return result


def interpolate_loss(table: Dict[float, float], freq_mhz: float) -> float:
    if not table:
        return 0.0
    points = sorted(table.items())
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
    valid_stages: List[Tuple[float, float]] = []
    for gain_db, nf_db in stages:
        if not (math.isfinite(gain_db) and math.isfinite(nf_db)):
            continue
        gain_linear = db_to_linear(gain_db)
        nf_linear = db_to_linear(max(0.0, nf_db))
        if gain_linear <= 0.0 or nf_linear <= 0.0:
            continue
        valid_stages.append((gain_db, max(0.0, nf_db)))

    if not valid_stages:
        return 0.0

    epsilon_gain = 1e-12
    first_gain_db, first_nf_db = valid_stages[0]
    total_noise_factor = db_to_linear(first_nf_db)
    cumulative_gain_linear = max(db_to_linear(first_gain_db), epsilon_gain)

    for gain_db, nf_db in valid_stages[1:]:
        stage_noise_factor = db_to_linear(nf_db)
        total_noise_factor += (stage_noise_factor - 1.0) / max(cumulative_gain_linear, epsilon_gain)
        cumulative_gain_linear *= max(db_to_linear(gain_db), epsilon_gain)

    if not math.isfinite(total_noise_factor) or total_noise_factor <= 0.0:
        return 0.0

    return linear_to_db(total_noise_factor)


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
    if watt >= 1e-15:
        return f"{watt * 1e15:.3f} fW"
    return f"{watt:.3e} W"


def compact_text(text: str, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


@dataclass
class StageResult:
    name: str
    component_type: str
    option: str
    detail: str
    gain_db: float
    nf_db: float
    dc_pass: bool
    p1db_dbm: Optional[float]
    input_dbm: float
    output_dbm: float
    cumulative_gain_db: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class BranchResult:
    name: str
    enabled: bool
    cable_type: str
    cable_length_m: float
    branch_gain_db: float
    final_level_dbm: float
    target_margin_db: float
    min_margin_db: float
    max_headroom_db: float
    status: str
    dc_required: bool
    dc_available: bool
    system_nf_db: float
    receiver_count: int
    warnings: List[str]
    stage_lines: List[str]


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


class PillowFontManager:
    def __init__(self):
        self.cache: Dict[Tuple[int, bool], object] = {}
        self.system = platform.system().lower()

    def get(self, size: int, bold: bool = False):
        if not HAS_PILLOW or ImageFont is None:
            return None

        key = (size, bold)
        if key in self.cache:
            return self.cache[key]

        for candidate in self._font_candidates(bold):
            try:
                font = ImageFont.truetype(candidate, size=size)
                self.cache[key] = font
                return font
            except Exception:
                continue

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            font = ImageFont.load_default()

        self.cache[key] = font
        return font

    def _font_candidates(self, bold: bool) -> List[str]:
        if self.system == "windows":
            base = Path("C:/Windows/Fonts")
            return [str(base / ("arialbd.ttf" if bold else "arial.ttf")), str(base / ("segoeuib.ttf" if bold else "segoeui.ttf"))]
        if self.system == "darwin":
            return [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]


class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, label: str, variable: tk.StringVar, width: int = 100):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
        self.entry = ctk.CTkEntry(self, textvariable=variable, fg_color=COLOR_CARD, border_color=COLOR_BORDER, text_color=COLOR_TEXT, height=30, width=width)
        self.label.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.entry.grid(row=1, column=0, sticky="ew")


class SummaryCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=COLOR_MUTED, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self.value_label = ctk.CTkLabel(self, text="", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=15, weight="bold"))
        self.value_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 8))

    def set_value(self, value: str):
        self.value_label.configure(text=value)


class TrunkCard(ctk.CTkFrame):
    def __init__(self, master, row_number: int, on_change, on_delete):
        super().__init__(master, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.on_change = on_change
        self.on_delete = on_delete
        self._updating = False

        self.enabled_var = tk.BooleanVar(value=True)
        self.name_var = tk.StringVar(value=f"Trunk Component {row_number}")
        self.type_var = tk.StringVar(value="Cable")
        self.option_var = tk.StringVar(value="LMR-200")
        self.length_var = tk.StringVar(value="10")
        self.value_var = tk.StringVar(value="0")
        self.qty_var = tk.StringVar(value="1")
        self.nf_var = tk.StringVar(value="0")
        self.p1db_var = tk.StringVar(value="")
        self.dc_pass_var = tk.BooleanVar(value=True)

        for col in range(12):
            self.grid_columnconfigure(col, weight=1)

        self.enabled_cb = ctk.CTkCheckBox(self, text="On", variable=self.enabled_var, command=self._changed, fg_color=COLOR_BLUE_DARK)
        self.name_field = LabeledEntry(self, "Name", self.name_var, 220)
        self.type_menu = self._labeled_menu("Type", COMPONENT_TYPES, self.type_var, self._type_changed)
        self.option_menu = self._labeled_menu("Option", list(CABLE_LOSS_DB_PER_100M.keys()), self.option_var, self._changed)
        self.length_field = LabeledEntry(self, "Length m", self.length_var, 80)
        self.value_field = LabeledEntry(self, "Value dB", self.value_var, 80)
        self.qty_field = LabeledEntry(self, "Qty", self.qty_var, 60)
        self.nf_field = LabeledEntry(self, "NF dB", self.nf_var, 70)
        self.p1db_field = LabeledEntry(self, "P1dB dBm", self.p1db_var, 80)
        self.dc_cb = ctk.CTkCheckBox(self, text="DC Pass", variable=self.dc_pass_var, command=self._changed, fg_color=COLOR_BLUE_DARK)
        self.remove_btn = ctk.CTkButton(self, text="Remove", command=lambda: self.on_delete(self), fg_color=COLOR_RED, hover_color=("#D98888", "#8F3D3D"), text_color=COLOR_RED_TEXT, width=80)

        self.enabled_cb.grid(row=0, column=0, padx=8, pady=12, sticky="w")
        self.name_field.grid(row=0, column=1, columnspan=3, padx=6, pady=8, sticky="ew")
        self.type_menu.grid(row=0, column=4, columnspan=2, padx=6, pady=8, sticky="ew")
        self.option_menu.grid(row=0, column=6, columnspan=3, padx=6, pady=8, sticky="ew")
        self.dc_cb.grid(row=0, column=9, padx=8, pady=12, sticky="w")
        self.remove_btn.grid(row=0, column=10, columnspan=2, padx=8, pady=12, sticky="ew")

        self.length_field.grid(row=1, column=1, padx=6, pady=(0, 10), sticky="ew")
        self.value_field.grid(row=1, column=2, padx=6, pady=(0, 10), sticky="ew")
        self.qty_field.grid(row=1, column=3, padx=6, pady=(0, 10), sticky="ew")
        self.nf_field.grid(row=1, column=4, padx=6, pady=(0, 10), sticky="ew")
        self.p1db_field.grid(row=1, column=5, padx=6, pady=(0, 10), sticky="ew")

        self.length_entry = self.length_field.entry
        self.value_entry = self.value_field.entry
        self.qty_entry = self.qty_field.entry
        self.nf_entry = self.nf_field.entry
        self.p1db_entry = self.p1db_field.entry

        for var in [self.name_var, self.length_var, self.value_var, self.qty_var, self.nf_var, self.p1db_var]:
            var.trace_add("write", lambda *_: self._changed())

        self._type_changed("Cable")

    def _labeled_menu(self, label: str, values: List[str], variable: tk.StringVar, command):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        menu = ctk.CTkOptionMenu(
            frame,
            values=values,
            variable=variable,
            command=command,
            fg_color=COLOR_BLUE,
            button_color=COLOR_BLUE_DARK,
            button_hover_color=COLOR_BLUE_HOVER,
            text_color=("white", "white"),
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_PANEL_ALT,
            height=30,
        )
        menu.grid(row=1, column=0, sticky="ew")
        frame.menu = menu
        return frame

    def _set_option_values(self, values: List[str]):
        self.option_menu.menu.configure(values=values)

    def _changed(self, *_):
        if not self._updating:
            self.on_change()

    def _type_changed(self, choice: str):
        self._updating = True
        try:
            self.length_entry.configure(state="disabled")
            self.p1db_entry.configure(state="disabled")
            self.nf_entry.configure(state="normal")
            self.dc_pass_var.set(True)

            if choice == "Cable":
                self._set_option_values(list(CABLE_LOSS_DB_PER_100M.keys()))
                self.option_var.set("LMR-200")
                self.length_entry.configure(state="normal")
                self.value_var.set("0")
                self.nf_var.set("0")
            elif choice == "Splitter":
                self._set_option_values(list(SPLITTER_LOSS_DB.keys()))
                self.option_var.set("2-way")
                self.length_var.set("0")
                self.value_var.set("0")
                self.nf_var.set("0")
            elif choice == "Attenuator":
                self._set_option_values(["Fixed Attenuator"])
                self.option_var.set("Fixed Attenuator")
                self.length_var.set("0")
                self.value_var.set("6")
                self.nf_var.set("0")
            elif choice == "Amplifier":
                self._set_option_values(["LNA / Line Amp"])
                self.option_var.set("LNA / Line Amp")
                self.length_var.set("0")
                self.value_var.set("20")
                self.nf_var.set("2")
                self.p1db_entry.configure(state="normal")
                if not self.p1db_var.get().strip():
                    self.p1db_var.set("10")
            elif choice == "Bias-T":
                self._set_option_values(["Bias-T"])
                self.option_var.set("Bias-T")
                self.length_var.set("0")
                self.value_var.set("0.8")
                self.nf_var.set("0")
            elif choice == "DC Block":
                self._set_option_values(["DC Block"])
                self.option_var.set("DC Block")
                self.length_var.set("0")
                self.value_var.set("0.5")
                self.nf_var.set("0")
                self.dc_pass_var.set(False)
            elif choice == "Connector Pair":
                self._set_option_values(["SMA Pair", "N-Type Pair", "TNC Pair", "Custom Pair"])
                self.option_var.set("SMA Pair")
                self.length_var.set("0")
                self.value_var.set("0.2")
                self.nf_var.set("0")
            elif choice == "Lightning Protector":
                self._set_option_values(["GNSS Protector"])
                self.option_var.set("GNSS Protector")
                self.length_var.set("0")
                self.value_var.set("0.5")
                self.nf_var.set("0")
            elif choice == "Custom Loss":
                self._set_option_values(["Manual Loss"])
                self.option_var.set("Manual Loss")
                self.length_var.set("0")
                self.value_var.set("1")
                self.nf_var.set("0")
            elif choice == "Custom Gain":
                self._set_option_values(["Manual Gain"])
                self.option_var.set("Manual Gain")
                self.length_var.set("0")
                self.value_var.set("1")
                self.nf_var.set("2")
                self.p1db_entry.configure(state="normal")
        finally:
            self._updating = False
        self._changed()

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled_var.get(),
            "name": self.name_var.get(),
            "type": self.type_var.get(),
            "option": self.option_var.get(),
            "length_m": self.length_var.get(),
            "value_db": self.value_var.get(),
            "qty": self.qty_var.get(),
            "nf_db": self.nf_var.get(),
            "p1db_dbm": self.p1db_var.get(),
            "dc_pass": self.dc_pass_var.get(),
        }

    def from_dict(self, data: dict):
        self._updating = True
        try:
            self.enabled_var.set(bool(data.get("enabled", True)))
            self.name_var.set(str(data.get("name", "Trunk Component")))
            self.type_var.set(str(data.get("type", "Cable")))
            self._type_changed(self.type_var.get())
            self.option_var.set(str(data.get("option", self.option_var.get())))
            self.length_var.set(str(data.get("length_m", "0")))
            self.value_var.set(str(data.get("value_db", "0")))
            self.qty_var.set(str(data.get("qty", "1")))
            self.nf_var.set(str(data.get("nf_db", self.nf_var.get())))
            self.p1db_var.set(str(data.get("p1db_dbm", self.p1db_var.get())))
            self.dc_pass_var.set(bool(data.get("dc_pass", self.dc_pass_var.get())))
        finally:
            self._updating = False
        self._changed()

    def calculate(self, freq_mhz: float, input_dbm: float, cumulative_gain_db: float) -> Tuple[List[StageResult], float, float]:
        if not self.enabled_var.get():
            return [], input_dbm, cumulative_gain_db

        ctype = self.type_var.get()
        option = self.option_var.get()
        qty = safe_int(self.qty_var.get(), 1, 1, self.qty_entry, field_name="trunk quantity")
        length_m = safe_float(self.length_var.get(), 0.0, self.length_entry, field_name="trunk length")
        value_db = safe_float(self.value_var.get(), 0.0, self.value_entry, field_name="trunk value dB")
        nf_setting = safe_float(self.nf_var.get(), 0.0, self.nf_entry, field_name="trunk NF dB")
        p1db = None
        if self.p1db_var.get().strip():
            p1db = safe_float(self.p1db_var.get(), 10.0, self.p1db_entry, field_name="trunk P1dB")

        stages: List[StageResult] = []
        current_level = input_dbm
        current_cumulative = cumulative_gain_db

        for q in range(qty):
            if ctype == "Cable":
                loss = cable_loss_db(option, length_m, freq_mhz, value_db)
                gain_db = -loss
                nf_db = loss
                detail = f"{option}, {length_m:.2f} m, loss {loss:.2f} dB"
            elif ctype == "Splitter":
                loss = SPLITTER_LOSS_DB.get(option, 0.0)
                if option == "Custom Splitter":
                    loss = abs(value_db)
                gain_db = -loss
                nf_db = loss
                detail = f"{option}, loss {loss:.2f} dB"
            elif ctype in ["Attenuator", "Bias-T", "DC Block", "Connector Pair", "Lightning Protector", "Custom Loss"]:
                loss = abs(value_db)
                gain_db = -loss
                nf_db = loss
                detail = f"{option}, loss {loss:.2f} dB"
            elif ctype in ["Amplifier", "Custom Gain"]:
                gain_db = abs(value_db)
                nf_db = max(0.0, nf_setting)
                detail = f"{option}, gain {gain_db:.2f} dB, NF {nf_db:.2f} dB"
            else:
                gain_db = 0.0
                nf_db = 0.0
                detail = "No calculation"

            output = current_level + gain_db
            current_cumulative += gain_db
            warnings: List[str] = []
            if ctype in ("Amplifier", "Custom Gain") and p1db is not None:
                if output > p1db - 10.0:
                    warnings.append(f"Output {output:.2f} dBm within 10 dB of P1dB {p1db:.2f} dBm")

            stages.append(
                StageResult(
                    name=self.name_var.get() if qty == 1 else f"{self.name_var.get()} #{q + 1}",
                    component_type=ctype,
                    option=option,
                    detail=detail,
                    gain_db=gain_db,
                    nf_db=nf_db,
                    dc_pass=self.dc_pass_var.get(),
                    p1db_dbm=p1db,
                    input_dbm=current_level,
                    output_dbm=output,
                    cumulative_gain_db=current_cumulative,
                    warnings=warnings,
                )
            )
            current_level = output

        return stages, current_level, current_cumulative


class BranchCard(ctk.CTkFrame):
    def __init__(self, master, row_number: int, on_change, on_delete):
        super().__init__(master, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.on_change = on_change
        self.on_delete = on_delete

        self.enabled_var = tk.BooleanVar(value=True)
        self.name_var = tk.StringVar(value=f"Branch {row_number}")
        self.cable_type_var = tk.StringVar(value="LMR-200")
        self.length_var = tk.StringVar(value="30")
        self.atten_var = tk.StringVar(value="0")
        self.amp_gain_var = tk.StringVar(value="0")
        self.amp_nf_var = tk.StringVar(value="2")
        self.amp_p1db_var = tk.StringVar(value="10")
        self.splitter_var = tk.StringVar(value="None")
        self.custom_splitter_var = tk.StringVar(value="0")
        self.connector_var = tk.StringVar(value="0.4")
        self.receiver_count_var = tk.StringVar(value="1")
        self.dc_required_var = tk.BooleanVar(value=False)
        self.dc_pass_var = tk.BooleanVar(value=True)

        for col in range(12):
            self.grid_columnconfigure(col, weight=1)

        self.enabled_cb = ctk.CTkCheckBox(self, text="On", variable=self.enabled_var, command=self._changed, fg_color=COLOR_BLUE_DARK)
        self.name_field = LabeledEntry(self, "Branch Name", self.name_var, 220)
        self.cable_menu = self._labeled_menu("Cable", list(CABLE_LOSS_DB_PER_100M.keys()), self.cable_type_var, self._changed)
        self.length_field = LabeledEntry(self, "Length m", self.length_var, 80)
        self.splitter_menu = self._labeled_menu("Local Splitter", list(SPLITTER_LOSS_DB.keys()), self.splitter_var, self._changed)
        self.rx_field = LabeledEntry(self, "Receiver Qty", self.receiver_count_var, 80)
        self.dc_required_cb = ctk.CTkCheckBox(self, text="DC Required", variable=self.dc_required_var, command=self._changed, fg_color=COLOR_BLUE_DARK)
        self.dc_pass_cb = ctk.CTkCheckBox(self, text="DC Pass", variable=self.dc_pass_var, command=self._changed, fg_color=COLOR_BLUE_DARK)
        self.remove_btn = ctk.CTkButton(self, text="Remove", command=lambda: self.on_delete(self), fg_color=COLOR_RED, hover_color=("#D98888", "#8F3D3D"), text_color=COLOR_RED_TEXT, width=80)

        self.atten_field = LabeledEntry(self, "Attenuator dB", self.atten_var, 90)
        self.amp_gain_field = LabeledEntry(self, "Amp Gain dB", self.amp_gain_var, 90)
        self.amp_nf_field = LabeledEntry(self, "Amp NF dB", self.amp_nf_var, 80)
        self.amp_p1db_field = LabeledEntry(self, "Amp P1dB", self.amp_p1db_var, 80)
        self.custom_splitter_field = LabeledEntry(self, "Custom Splitter dB", self.custom_splitter_var, 90)
        self.connector_field = LabeledEntry(self, "Connector dB", self.connector_var, 80)

        self.enabled_cb.grid(row=0, column=0, padx=8, pady=12, sticky="w")
        self.name_field.grid(row=0, column=1, columnspan=3, padx=6, pady=8, sticky="ew")
        self.cable_menu.grid(row=0, column=4, columnspan=2, padx=6, pady=8, sticky="ew")
        self.length_field.grid(row=0, column=6, padx=6, pady=8, sticky="ew")
        self.splitter_menu.grid(row=0, column=7, columnspan=2, padx=6, pady=8, sticky="ew")
        self.rx_field.grid(row=0, column=9, padx=6, pady=8, sticky="ew")
        self.remove_btn.grid(row=0, column=10, columnspan=2, padx=8, pady=12, sticky="ew")

        self.atten_field.grid(row=1, column=1, padx=6, pady=(0, 10), sticky="ew")
        self.amp_gain_field.grid(row=1, column=2, padx=6, pady=(0, 10), sticky="ew")
        self.amp_nf_field.grid(row=1, column=3, padx=6, pady=(0, 10), sticky="ew")
        self.amp_p1db_field.grid(row=1, column=4, padx=6, pady=(0, 10), sticky="ew")
        self.custom_splitter_field.grid(row=1, column=5, padx=6, pady=(0, 10), sticky="ew")
        self.connector_field.grid(row=1, column=6, padx=6, pady=(0, 10), sticky="ew")
        self.dc_required_cb.grid(row=1, column=7, padx=8, pady=(8, 10), sticky="w")
        self.dc_pass_cb.grid(row=1, column=8, padx=8, pady=(8, 10), sticky="w")

        self.length_entry = self.length_field.entry
        self.atten_entry = self.atten_field.entry
        self.amp_gain_entry = self.amp_gain_field.entry
        self.amp_nf_entry = self.amp_nf_field.entry
        self.amp_p1db_entry = self.amp_p1db_field.entry
        self.custom_splitter_entry = self.custom_splitter_field.entry
        self.connector_entry = self.connector_field.entry
        self.receiver_count_entry = self.rx_field.entry

        for var in [
            self.name_var,
            self.length_var,
            self.atten_var,
            self.amp_gain_var,
            self.amp_nf_var,
            self.amp_p1db_var,
            self.custom_splitter_var,
            self.connector_var,
            self.receiver_count_var,
        ]:
            var.trace_add("write", lambda *_: self._changed())

    def _labeled_menu(self, label: str, values: List[str], variable: tk.StringVar, command):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        menu = ctk.CTkOptionMenu(
            frame,
            values=values,
            variable=variable,
            command=command,
            fg_color=COLOR_BLUE,
            button_color=COLOR_BLUE_DARK,
            button_hover_color=COLOR_BLUE_HOVER,
            text_color=("white", "white"),
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_PANEL_ALT,
            height=30,
        )
        menu.grid(row=1, column=0, sticky="ew")
        return frame

    def _changed(self, *_):
        self.on_change()

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled_var.get(),
            "name": self.name_var.get(),
            "cable_type": self.cable_type_var.get(),
            "length_m": self.length_var.get(),
            "attenuator_db": self.atten_var.get(),
            "amp_gain_db": self.amp_gain_var.get(),
            "amp_nf_db": self.amp_nf_var.get(),
            "amp_p1db_dbm": self.amp_p1db_var.get(),
            "splitter": self.splitter_var.get(),
            "custom_splitter_db": self.custom_splitter_var.get(),
            "connector_loss_db": self.connector_var.get(),
            "receiver_count": self.receiver_count_var.get(),
            "dc_required": self.dc_required_var.get(),
            "dc_pass": self.dc_pass_var.get(),
        }

    def from_dict(self, data: dict):
        self.enabled_var.set(bool(data.get("enabled", True)))
        self.name_var.set(str(data.get("name", "Branch")))
        self.cable_type_var.set(str(data.get("cable_type", "LMR-200")))
        self.length_var.set(str(data.get("length_m", "30")))
        self.atten_var.set(str(data.get("attenuator_db", "0")))
        self.amp_gain_var.set(str(data.get("amp_gain_db", "0")))
        self.amp_nf_var.set(str(data.get("amp_nf_db", "2")))
        self.amp_p1db_var.set(str(data.get("amp_p1db_dbm", "10")))
        self.splitter_var.set(str(data.get("splitter", "None")))
        self.custom_splitter_var.set(str(data.get("custom_splitter_db", "0")))
        self.connector_var.set(str(data.get("connector_loss_db", "0.4")))
        self.receiver_count_var.set(str(data.get("receiver_count", "1")))
        self.dc_required_var.set(bool(data.get("dc_required", False)))
        self.dc_pass_var.set(bool(data.get("dc_pass", True)))
        self._changed()


class CardList(ctk.CTkFrame):
    def __init__(self, master, title: str, card_class, on_change):
        super().__init__(master, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.card_class = card_class
        self.on_change = on_change
        self.cards: List[Union[TrunkCard, BranchCard]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title_bar = ctk.CTkFrame(self, fg_color=COLOR_PANEL_ALT)
        title_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        title_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(title_bar, text=title, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="ew")

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=8,
            scrollbar_button_color=COLOR_BLUE,
            scrollbar_button_hover_color=COLOR_BLUE_DARK,
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.scroll.grid_columnconfigure(0, weight=1)

    def add_card(self, data: Optional[dict] = None):
        card = self.card_class(self.scroll, len(self.cards) + 1, self.on_change, self.delete_card)
        if data:
            card.from_dict(data)
        card.grid(row=len(self.cards), column=0, sticky="ew", padx=(0, 8), pady=5)
        self.cards.append(card)
        self.on_change()

    def delete_card(self, card):
        def finalize_delete():
            try:
                if card in self.cards:
                    self.cards.remove(card)
                if card.winfo_exists():
                    card.destroy()
                self._regrid()
                self.on_change()
            except Exception as exc:
                messagebox.showerror("Delete Error", f"Unable to delete row.\n\nDetail: {exc}")

        self.after(0, finalize_delete)

    def _regrid(self):
        for idx, card in enumerate(self.cards):
            if card.winfo_exists():
                card.grid(row=idx, column=0, sticky="ew", padx=(0, 8), pady=5)

    def clear_cards(self):
        for card in list(self.cards):
            if card.winfo_exists():
                card.destroy()
        self.cards.clear()
        self.on_change()

    def active_cards(self):
        self.cards = [c for c in self.cards if c.winfo_exists()]
        return self.cards

    def to_list(self) -> List[dict]:
        return [c.to_dict() for c in self.active_cards()]

    def from_list(self, items: List[dict]):
        self.clear_cards()
        for item in items:
            self.add_card(item)


class GraphBuilder(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.app = app
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.node_items: Dict[int, str] = {}
        self.drag_node_id: Optional[str] = None
        self.drag_offset = (0.0, 0.0)
        self.selected_node_id: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=10)
        toolbar.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="ew")
        for col in range(7):
            toolbar.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(
            toolbar,
            text="Graph Builder: drag nodes to arrange the GNSS network. Buttons add real trunk components and output branches.",
            text_color=COLOR_TEXT,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=8, sticky="ew")

        app.button(toolbar, "+ Trunk Amplifier", self.add_trunk_amp).grid(row=0, column=3, padx=6, pady=8, sticky="ew")
        app.button(toolbar, "+ Trunk Splitter", self.add_trunk_splitter).grid(row=0, column=4, padx=6, pady=8, sticky="ew")
        app.button(toolbar, "+ Output Branch", self.add_branch).grid(row=0, column=5, padx=6, pady=8, sticky="ew")
        app.button(toolbar, "Auto Layout", self.auto_layout).grid(row=0, column=6, padx=6, pady=8, sticky="ew")

        self.canvas = tk.Canvas(
            self,
            bg=drawing_color(COLOR_DIAGRAM_BG),
            highlightthickness=1,
            highlightbackground=drawing_color(COLOR_BORDER),
        )
        self.x_scroll = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.y_scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)

        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 0))
        self.y_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=(0, 0))
        self.x_scroll.grid(row=2, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Configure>", lambda _event: self.update_scrollregion())

    def add_trunk_amp(self):
        self.app.trunk_cards.add_card({
            "enabled": True,
            "name": "Graph trunk amplifier",
            "type": "Amplifier",
            "option": "LNA / Line Amp",
            "length_m": "0",
            "value_db": "20",
            "qty": "1",
            "nf_db": "2",
            "p1db_dbm": "10",
            "dc_pass": True,
        })
        self.app.calculate_now()
        self.refresh()

    def add_trunk_splitter(self):
        self.app.trunk_cards.add_card({
            "enabled": True,
            "name": "Graph trunk splitter",
            "type": "Splitter",
            "option": "2-way",
            "length_m": "0",
            "value_db": "0",
            "qty": "1",
            "nf_db": "0",
            "p1db_dbm": "",
            "dc_pass": True,
        })
        self.app.calculate_now()
        self.refresh()

    def add_branch(self):
        count = len(self.app.branch_cards.active_cards()) + 1
        self.app.branch_cards.add_card({
            "enabled": True,
            "name": f"Graph Branch {count}",
            "cable_type": "LMR-200",
            "length_m": "30",
            "attenuator_db": "0",
            "amp_gain_db": "0",
            "amp_nf_db": "2",
            "amp_p1db_dbm": "10",
            "splitter": "None",
            "custom_splitter_db": "0",
            "connector_loss_db": "0.4",
            "receiver_count": "1",
            "dc_required": False,
            "dc_pass": True,
        })
        self.app.calculate_now()
        self.refresh()

    def auto_layout(self):
        self.node_positions.clear()
        self.refresh(force_layout=True)

    def node_key_for_trunk(self, index: int) -> str:
        return f"trunk:{index}"

    def node_key_for_branch(self, index: int) -> str:
        return f"branch:{index}"

    def update_from_app(self):
        self.refresh()

    def refresh(self, force_layout: bool = False):
        self.canvas.delete("all")
        self.node_items.clear()
        self.canvas.configure(bg=drawing_color(COLOR_DIAGRAM_BG), highlightbackground=drawing_color(COLOR_BORDER))

        trunk_cards = self.app.trunk_cards.active_cards() if hasattr(self.app, "trunk_cards") else []
        branch_cards = self.app.branch_cards.active_cards() if hasattr(self.app, "branch_cards") else []
        trunk_results = self.app.trunk_results
        branch_results = [b for b in self.app.branch_results if b.enabled]

        source_level = self.app.current_source_dbm
        trunk_output = trunk_results[-1].output_dbm if trunk_results else source_level

        if force_layout or not self.node_positions:
            self._default_positions(len(trunk_cards), len(branch_cards))

        self._draw_title()
        self._draw_connections(len(trunk_cards), len(branch_cards))
        self._draw_source(source_level)
        self._draw_trunk_nodes(trunk_cards, trunk_results)
        self._draw_distribution_node(trunk_output)
        self._draw_branch_nodes(branch_cards, branch_results)
        self.update_scrollregion()

    def _default_positions(self, trunk_count: int, branch_count: int):
        x = 80
        y = 230
        self.node_positions["source"] = (x, y)
        for idx in range(trunk_count):
            self.node_positions[self.node_key_for_trunk(idx)] = (x + 300 * (idx + 1), y)
        dist_x = x + 300 * (trunk_count + 1)
        self.node_positions["dist"] = (dist_x, y)
        branch_x = dist_x + 330
        for idx in range(branch_count):
            self.node_positions[self.node_key_for_branch(idx)] = (branch_x, 90 + idx * 170)

    def _draw_title(self):
        self.canvas.create_text(
            60,
            35,
            anchor="w",
            text="Interactive Graph Builder",
            fill=drawing_color(COLOR_TEXT),
            font=("TkDefaultFont", 22, "bold"),
        )
        self.canvas.create_text(
            60,
            66,
            anchor="w",
            text="Drag blocks to arrange the network. Double-click a block to jump back to the Network Design tab.",
            fill=drawing_color(COLOR_MUTED),
            font=("TkDefaultFont", 11),
        )

    def _draw_connections(self, trunk_count: int, branch_count: int):
        chain = ["source"] + [self.node_key_for_trunk(i) for i in range(trunk_count)] + ["dist"]
        for a, b in zip(chain, chain[1:]):
            self._line_between_nodes(a, b)
        for idx in range(branch_count):
            self._line_between_nodes("dist", self.node_key_for_branch(idx))

    def _line_between_nodes(self, node_a: str, node_b: str):
        if node_a not in self.node_positions or node_b not in self.node_positions:
            return
        ax, ay = self.node_positions[node_a]
        bx, by = self.node_positions[node_b]
        self.canvas.create_line(
            ax + 250,
            ay + 55,
            bx,
            by + 55,
            fill=drawing_color(COLOR_ARROW),
            width=3,
            arrow=tk.LAST,
            tags=("connection",),
        )

    def _draw_source(self, source_level: float):
        x, y = self.node_positions.get("source", (80, 230))
        self._node(
            "source",
            x,
            y,
            "GNSS Source",
            "Input reference",
            [f"{source_level:.2f} dBm", f"{self.app.current_freq_mhz:.3f} MHz"],
            ("#E8F5E9", "#1D3B2A"),
            ("#4F9D69", "#7FD49B"),
        )

    def _draw_trunk_nodes(self, trunk_cards, trunk_results: List[StageResult]):
        result_idx = 0
        for idx, card in enumerate(trunk_cards):
            key = self.node_key_for_trunk(idx)
            x, y = self.node_positions.get(key, (380 + idx * 300, 230))
            output = ""
            gain = ""
            warnings = []
            if result_idx < len(trunk_results):
                st = trunk_results[result_idx]
                output = f"Out {st.output_dbm:.2f} dBm"
                gain = f"Stage {st.gain_db:+.2f} dB"
                warnings = st.warnings
                result_idx += 1
            fill = COLOR_CABLE if card.type_var.get() == "Cable" else COLOR_BLOCK_FILL
            if card.type_var.get() in ["Amplifier", "Custom Gain"]:
                fill = ("#E8F5E9", "#1D3B2A")
            elif card.type_var.get() in ["Splitter", "Attenuator", "Custom Loss"]:
                fill = ("#FFF7E6", "#4A3610")
            lines = [card.type_var.get(), gain, output]
            if warnings:
                lines.append("Warning")
            self._node(key, x, y, compact_text(card.name_var.get(), 25), compact_text(card.option_var.get(), 22), lines, fill, COLOR_BLOCK_BORDER)

    def _draw_distribution_node(self, trunk_output: float):
        x, y = self.node_positions.get("dist", (680, 230))
        self._node(
            "dist",
            x,
            y,
            "Distribution Node",
            "Branch launch point",
            [f"Launch {trunk_output:.2f} dBm", f"Branches {len(self.app.branch_results)}"],
            ("#E8F2FF", "#1B314A"),
            ("#467EA3", "#72A8CE"),
        )

    def _draw_branch_nodes(self, branch_cards, branch_results: List[BranchResult]):
        for idx, card in enumerate(branch_cards):
            key = self.node_key_for_branch(idx)
            x, y = self.node_positions.get(key, (1000, 90 + idx * 170))
            br = branch_results[idx] if idx < len(branch_results) else None

            fill = COLOR_BLOCK_FILL
            text_fill = COLOR_TEXT
            lines = [f"Cable {card.cable_type_var.get()}", f"{card.length_var.get()} m"]
            subtitle = "Output branch"

            if br:
                lines = [f"Final {br.final_level_dbm:.2f} dBm", f"Margin {br.target_margin_db:+.2f} dB", f"Rx {br.receiver_count} | NF {br.system_nf_db:.2f} dB"]
                subtitle = br.status
                fill, text_fill = self._status_colors(br.status)

            self._node(key, x, y, compact_text(card.name_var.get(), 25), subtitle, lines, fill, COLOR_BORDER, text_fill)

    def _status_colors(self, status: str):
        if status == "WEAK SIGNAL":
            return COLOR_AMBER, COLOR_AMBER_TEXT
        if status == "OVERDRIVE RISK" or "DC BLOCKED" in status:
            return COLOR_RED, COLOR_RED_TEXT
        if status == "NEAR TARGET":
            return COLOR_BLUE, ("#FFFFFF", "#FFFFFF")
        return COLOR_GREEN, COLOR_GREEN_TEXT

    def _node(
        self,
        node_id: str,
        x: float,
        y: float,
        title: str,
        subtitle: str,
        lines: List[str],
        fill: ColorPair,
        outline: ColorPair,
        text_fill: ColorPair = COLOR_TEXT,
    ):
        w = 250
        h = 116
        selected = node_id == self.selected_node_id
        outline_color = drawing_color(COLOR_RED if selected else outline)
        width = 3 if selected else 2

        items = []
        items.append(self.canvas.create_rectangle(x + 4, y + 4, x + w + 4, y + h + 4, fill=("#D5DEE7" if ctk.get_appearance_mode().lower() == "light" else "#0B1220"), outline="", tags=("node", node_id)))
        items.append(self.canvas.create_rectangle(x, y, x + w, y + h, fill=drawing_color(fill), outline=outline_color, width=width, tags=("node", node_id)))
        items.append(self.canvas.create_text(x + 12, y + 16, anchor="w", text=title, fill=drawing_color(text_fill), font=("TkDefaultFont", 11, "bold"), tags=("node", node_id)))
        items.append(self.canvas.create_text(x + 12, y + 38, anchor="w", text=subtitle, fill=drawing_color(text_fill), font=("TkDefaultFont", 9), tags=("node", node_id)))
        items.append(self.canvas.create_line(x + 12, y + 52, x + w - 12, y + 52, fill=outline_color, tags=("node", node_id)))
        for idx, line in enumerate(lines[:3]):
            items.append(self.canvas.create_text(x + 12, y + 72 + idx * 16, anchor="w", text=line, fill=drawing_color(text_fill), font=("TkDefaultFont", 9, "bold" if idx == 0 else "normal"), tags=("node", node_id)))

        for item in items:
            self.node_items[item] = node_id

    def on_press(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if not item:
            return
        tags = self.canvas.gettags(item[0])
        node_id = next((tag for tag in tags if tag in self.node_positions), None)
        if node_id is None:
            return
        self.selected_node_id = node_id
        self.drag_node_id = node_id
        x, y = self.node_positions[node_id]
        self.drag_offset = (self.canvas.canvasx(event.x) - x, self.canvas.canvasy(event.y) - y)
        self.refresh()

    def on_drag(self, event):
        if self.drag_node_id is None:
            return
        new_x = self.canvas.canvasx(event.x) - self.drag_offset[0]
        new_y = self.canvas.canvasy(event.y) - self.drag_offset[1]
        self.node_positions[self.drag_node_id] = (max(20, new_x), max(20, new_y))
        self.refresh()

    def on_release(self, _event):
        self.drag_node_id = None
        self.update_scrollregion()

    def on_double_click(self, _event):
        self.app.tabs.set("Network Design")

    def update_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox is None or len(bbox) < 4:
            self.canvas.configure(scrollregion=(0, 0, max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())))
            return
        pad = 80
        self.canvas.configure(scrollregion=(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))




class DiagramCanvas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_PANEL, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=drawing_color(COLOR_DIAGRAM_BG), highlightthickness=1, highlightbackground=drawing_color(COLOR_BORDER))
        self.x_scroll = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.y_scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.y_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=(8, 0))
        self.x_scroll.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self._update_scrollregion())

    def _update_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox is None or len(bbox) < 4:
            self.canvas.configure(scrollregion=(0, 0, max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())))
            return
        pad = 60
        self.canvas.configure(scrollregion=(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))

    def draw_network(self, source_dbm: float, frequency_mhz: float, scenario: str, trunk: List[StageResult], branches: List[BranchResult]):
        self.canvas.delete("all")
        self.canvas.configure(bg=drawing_color(COLOR_DIAGRAM_BG), highlightbackground=drawing_color(COLOR_BORDER))

        x0 = 70
        y0 = 150
        bw = 230
        bh = 116
        gap = 90
        font_family = "TkDefaultFont"
        text_c = drawing_color(COLOR_TEXT)
        muted = drawing_color(COLOR_MUTED)

        self.canvas.create_text(60, 40, anchor="w", text="Multi-Branch GNSS RF Distribution Diagram", fill=text_c, font=(font_family, 22, "bold"))
        self.canvas.create_text(60, 75, anchor="w", text=f"Scenario: {scenario}", fill=text_c, font=(font_family, 12, "bold"))
        self.canvas.create_text(60, 98, anchor="w", text=f"Frequency: {frequency_mhz:.3f} MHz", fill=muted, font=(font_family, 11))

        self._block(x0, y0, bw, bh, "GNSS Source", "Reference Input", [f"{source_dbm:.2f} dBm"], ("#E8F5E9", "#1D3B2A"), ("#4F9D69", "#7FD49B"))
        prev_x = x0 + bw
        prev_level = source_dbm

        for idx, st in enumerate(trunk):
            x = x0 + (idx + 1) * (bw + gap)
            self._arrow(prev_x + 5, y0 + bh / 2, x - 10, y0 + bh / 2, f"{st.gain_db:+.2f} dB", f"{prev_level:.1f} to {st.output_dbm:.1f} dBm")
            fill = COLOR_CABLE if st.component_type == "Cable" else COLOR_BLOCK_FILL
            if st.component_type in ["Amplifier", "Custom Gain"]:
                fill = ("#E8F5E9", "#1D3B2A")
            if st.component_type in ["Splitter", "Attenuator", "Custom Loss"]:
                fill = ("#FFF7E6", "#4A3610")
            self._block(
                x,
                y0,
                bw,
                bh,
                compact_text(st.name, 24),
                f"{st.component_type} | {compact_text(st.option, 18)}",
                [f"Stage {st.gain_db:+.2f} dB", f"Out {st.output_dbm:.2f} dBm", f"DC {'Pass' if st.dc_pass else 'Blocked'}"],
                fill,
                COLOR_BLOCK_BORDER,
            )
            prev_x = x + bw
            prev_level = st.output_dbm

        node_x = x0 + (len(trunk) + 1) * (bw + gap)
        self._arrow(prev_x + 5, y0 + bh / 2, node_x - 10, y0 + bh / 2, "Branch Node", f"{prev_level:.1f} dBm")
        self._block(node_x, y0, bw, bh, "Distribution Node", "Branch launch point", [f"Launch {prev_level:.2f} dBm", f"Branches {len(branches)}"], ("#E8F2FF", "#1B314A"), ("#467EA3", "#72A8CE"))

        branch_start_x = node_x + bw + 160
        branch_gap_y = 170
        first_y = 55
        for idx, br in enumerate(branches):
            by = first_y + idx * branch_gap_y
            status_fill = COLOR_GREEN
            status_text = COLOR_GREEN_TEXT
            if br.status == "WEAK SIGNAL":
                status_fill = COLOR_AMBER
                status_text = COLOR_AMBER_TEXT
            elif br.status == "OVERDRIVE RISK" or "DC BLOCKED" in br.status:
                status_fill = COLOR_RED
                status_text = COLOR_RED_TEXT
            elif br.status == "NEAR TARGET":
                status_fill = COLOR_BLUE
                status_text = ("#FFFFFF", "#FFFFFF")

            self.canvas.create_line(node_x + bw, y0 + bh / 2, branch_start_x - 45, by + bh / 2, fill=drawing_color(COLOR_ARROW), width=3, arrow=tk.LAST)
            self.canvas.create_text((node_x + bw + branch_start_x - 45) / 2, (y0 + bh / 2 + by + bh / 2) / 2 - 10, text=f"{br.branch_gain_db:+.2f} dB", fill=text_c, font=(font_family, 9, "bold"))
            self._block(
                branch_start_x,
                by,
                bw + 40,
                bh,
                compact_text(br.name, 26),
                f"{br.cable_type}, {br.cable_length_m:.1f} m",
                [f"Final {br.final_level_dbm:.2f} dBm", f"Margin {br.target_margin_db:+.2f} dB", f"NF {br.system_nf_db:.2f} dB | Rx {br.receiver_count}"],
                status_fill,
                COLOR_BORDER,
                status_text,
            )
            self.canvas.create_text(branch_start_x + bw + 70, by + bh / 2, anchor="w", text=br.status, fill=drawing_color(status_text), font=(font_family, 10, "bold"))

        max_y = max(700, first_y + max(1, len(branches)) * branch_gap_y + 90)
        max_x = branch_start_x + bw + 360
        self.canvas.create_rectangle(0, 0, max_x, max_y, outline="", tags=("bounds",))
        self.canvas.tag_lower("bounds")
        self._update_scrollregion()

    def _block(self, x, y, w, h, title, subtitle, lines, fill, outline, text_fill=COLOR_TEXT):
        self.canvas.create_rectangle(x + 4, y + 4, x + w + 4, y + h + 4, fill=("#D5DEE7" if ctk.get_appearance_mode().lower() == "light" else "#0B1220"), outline="")
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=drawing_color(fill), outline=drawing_color(outline), width=2)
        self.canvas.create_text(x + 10, y + 16, anchor="w", text=title, fill=drawing_color(text_fill), font=("TkDefaultFont", 11, "bold"))
        self.canvas.create_text(x + 10, y + 38, anchor="w", text=subtitle, fill=drawing_color(text_fill), font=("TkDefaultFont", 9))
        self.canvas.create_line(x + 10, y + 52, x + w - 10, y + 52, fill=drawing_color(outline))
        for idx, line in enumerate(lines):
            self.canvas.create_text(x + 10, y + 72 + idx * 16, anchor="w", text=line, fill=drawing_color(text_fill), font=("TkDefaultFont", 9, "bold" if idx == 0 else "normal"))

    def _arrow(self, x1, y1, x2, y2, label, sublabel):
        mid_x = (x1 + x2) / 2
        self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=drawing_color(COLOR_ARROW), width=3)
        self.canvas.create_rectangle(mid_x - 65, y1 - 45, mid_x + 65, y1 - 8, fill=drawing_color(COLOR_CARD), outline=drawing_color(COLOR_BORDER))
        self.canvas.create_text(mid_x, y1 - 34, text=label, fill=drawing_color(COLOR_TEXT), font=("TkDefaultFont", 9, "bold"))
        self.canvas.create_text(mid_x, y1 - 19, text=sublabel, fill=drawing_color(COLOR_MUTED), font=("TkDefaultFont", 8))

    def export_png(self, filepath: str, source_dbm: float, frequency_mhz: float, scenario: str, trunk: List[StageResult], branches: List[BranchResult]):
        if not HAS_PILLOW or Image is None or ImageDraw is None:
            raise RuntimeError("PNG export requires Pillow. Install it with: pip install pillow")

        fm = PillowFontManager()
        f_title = fm.get(22, True)
        f_h = fm.get(12, True)
        f_s = fm.get(9, False)

        bw = 230
        bh = 116
        gap = 90
        x0 = 70
        y0 = 150
        node_x = x0 + (len(trunk) + 1) * (bw + gap)
        branch_start_x = node_x + bw + 160
        width = int(max(1650, branch_start_x + bw + 400))
        height = int(max(760, 55 + max(1, len(branches)) * 170 + 110))

        img = Image.new("RGB", (width, height), drawing_color(COLOR_DIAGRAM_BG))
        draw = ImageDraw.Draw(img)

        def center_text(xy, text, fill, font):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            except Exception:
                tw = len(text) * 7
                th = 10
            draw.text((xy[0] - tw / 2, xy[1] - th / 2), text, fill=fill, font=font)

        def block(x, y, w, h, title, subtitle, lines, fill, outline, text_fill=drawing_color(COLOR_TEXT)):
            draw.rectangle((x + 4, y + 4, x + w + 4, y + h + 4), fill="#D5DEE7" if ctk.get_appearance_mode().lower() == "light" else "#0B1220")
            draw.rectangle((x, y, x + w, y + h), fill=fill, outline=outline, width=2)
            draw.text((x + 10, y + 10), title, fill=text_fill, font=f_h)
            draw.text((x + 10, y + 32), subtitle, fill=text_fill, font=f_s)
            draw.line((x + 10, y + 52, x + w - 10, y + 52), fill=outline, width=1)
            for i, line in enumerate(lines):
                draw.text((x + 10, y + 67 + i * 16), line, fill=text_fill, font=f_s)

        def arrow(x1, y1, x2, y2, label, sublabel):
            draw.line((x1, y1, x2, y2), fill=drawing_color(COLOR_ARROW), width=3)
            draw.polygon([(x2, y2), (x2 - 12, y2 - 6), (x2 - 12, y2 + 6)], fill=drawing_color(COLOR_ARROW))
            mx = (x1 + x2) / 2
            draw.rectangle((mx - 65, y1 - 45, mx + 65, y1 - 8), fill=drawing_color(COLOR_CARD), outline=drawing_color(COLOR_BORDER))
            center_text((mx, y1 - 34), label, drawing_color(COLOR_TEXT), f_s)
            center_text((mx, y1 - 19), sublabel, drawing_color(COLOR_MUTED), f_s)

        draw.text((60, 40), "Multi-Branch GNSS RF Distribution Diagram", fill=drawing_color(COLOR_TEXT), font=f_title)
        draw.text((60, 75), f"Scenario: {scenario}", fill=drawing_color(COLOR_TEXT), font=f_h)
        draw.text((60, 98), f"Frequency: {frequency_mhz:.3f} MHz", fill=drawing_color(COLOR_MUTED), font=f_s)

        block(x0, y0, bw, bh, "GNSS Source", "Reference Input", [f"{source_dbm:.2f} dBm"], drawing_color(("#E8F5E9", "#1D3B2A")), drawing_color(("#4F9D69", "#7FD49B")))
        prev_x = x0 + bw
        prev_level = source_dbm

        for idx, st in enumerate(trunk):
            x = x0 + (idx + 1) * (bw + gap)
            arrow(prev_x + 5, y0 + bh / 2, x - 10, y0 + bh / 2, f"{st.gain_db:+.2f} dB", f"{prev_level:.1f} to {st.output_dbm:.1f} dBm")
            fill = drawing_color(COLOR_CABLE) if st.component_type == "Cable" else drawing_color(COLOR_BLOCK_FILL)
            if st.component_type in ["Amplifier", "Custom Gain"]:
                fill = drawing_color(("#E8F5E9", "#1D3B2A"))
            if st.component_type in ["Splitter", "Attenuator", "Custom Loss"]:
                fill = drawing_color(("#FFF7E6", "#4A3610"))
            block(x, y0, bw, bh, compact_text(st.name, 24), f"{st.component_type} | {compact_text(st.option, 18)}", [f"Stage {st.gain_db:+.2f} dB", f"Out {st.output_dbm:.2f} dBm", f"DC {'Pass' if st.dc_pass else 'Blocked'}"], fill, drawing_color(COLOR_BLOCK_BORDER))
            prev_x = x + bw
            prev_level = st.output_dbm

        arrow(prev_x + 5, y0 + bh / 2, node_x - 10, y0 + bh / 2, "Branch Node", f"{prev_level:.1f} dBm")
        block(node_x, y0, bw, bh, "Distribution Node", "Branch launch point", [f"Launch {prev_level:.2f} dBm", f"Branches {len(branches)}"], drawing_color(("#E8F2FF", "#1B314A")), drawing_color(("#467EA3", "#72A8CE")))

        for idx, br in enumerate(branches):
            by = 55 + idx * 170
            fill = drawing_color(COLOR_GREEN)
            text_fill = drawing_color(COLOR_GREEN_TEXT)
            if br.status == "WEAK SIGNAL":
                fill = drawing_color(COLOR_AMBER)
                text_fill = drawing_color(COLOR_AMBER_TEXT)
            elif br.status == "OVERDRIVE RISK" or "DC BLOCKED" in br.status:
                fill = drawing_color(COLOR_RED)
                text_fill = drawing_color(COLOR_RED_TEXT)
            elif br.status == "NEAR TARGET":
                fill = drawing_color(COLOR_BLUE)
                text_fill = "white"

            draw.line((node_x + bw, y0 + bh / 2, branch_start_x - 45, by + bh / 2), fill=drawing_color(COLOR_ARROW), width=3)
            draw.polygon([(branch_start_x - 45, by + bh / 2), (branch_start_x - 57, by + bh / 2 - 6), (branch_start_x - 57, by + bh / 2 + 6)], fill=drawing_color(COLOR_ARROW))
            block(branch_start_x, by, bw + 40, bh, compact_text(br.name, 26), f"{br.cable_type}, {br.cable_length_m:.1f} m", [f"Final {br.final_level_dbm:.2f} dBm", f"Margin {br.target_margin_db:+.2f} dB", f"NF {br.system_nf_db:.2f} dB | Rx {br.receiver_count}"], fill, drawing_color(COLOR_BORDER), text_fill)
            draw.text((branch_start_x + bw + 75, by + bh / 2 - 8), br.status, fill=text_fill, font=f_h)

        img.save(filepath, "PNG")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1680x960")
        self.minsize(1480, 840)
        self.configure(fg_color=COLOR_APP_BG)

        self._is_loading = False
        self.trunk_results: List[StageResult] = []
        self.branch_results: List[BranchResult] = []
        self.global_warnings: List[str] = []
        self.current_freq_mhz = 1575.42
        self.current_source_dbm = -85.0

        self.scenario_var = tk.StringVar(value="GNSS Building Distribution Network")
        self.band_var = tk.StringVar(value=list(GNSS_BANDS_MHZ.keys())[0])
        self.freq_var = tk.StringVar(value=str(GNSS_BANDS_MHZ[self.band_var.get()]))
        self.source_var = tk.StringVar(value="-85")
        self.receiver_preset_var = tk.StringVar(value="Conservative GNSS receiver window")
        self.min_var = tk.StringVar(value=str(DEFAULT_RECEIVER_MIN_DBM))
        self.max_var = tk.StringVar(value=str(DEFAULT_RECEIVER_MAX_DBM))
        self.target_var = tk.StringVar(value=str(DEFAULT_TARGET_DBM))

        self.debouncer = DebouncedAction(self, DEBOUNCE_MS, self.recalculate)

        self._build_ui()
        self.load_example()

    def button(self, master, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(master, text=text, command=command, fg_color=COLOR_BLUE_DARK, hover_color=COLOR_BLUE_HOVER, text_color=("white", "white"), height=34, font=ctk.CTkFont(size=12, weight="bold"))

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=APP_TITLE, text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, padx=18, pady=(14, 0), sticky="ew")
        ctk.CTkLabel(header, text=f"{APP_BRAND}  |  Multi-Branch Indoor GNSS RF Distribution Link Budget", text_color=COLOR_MUTED, anchor="w", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=18, pady=(2, 14), sticky="ew")

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=COLOR_PANEL,
            segmented_button_fg_color=COLOR_PANEL_ALT,
            segmented_button_selected_color=COLOR_BLUE_DARK,
            segmented_button_selected_hover_color=COLOR_BLUE_HOVER,
            segmented_button_unselected_color=COLOR_PANEL_ALT,
            segmented_button_unselected_hover_color=COLOR_BLUE,
            text_color=COLOR_TEXT,
        )
        self.tabs.grid(row=1, column=0, padx=14, pady=14, sticky="nsew")

        self.tab_design = self.tabs.add("Network Design")
        self.tab_results = self.tabs.add("Branch Results")
        self.tab_graph = self.tabs.add("Graph Builder")
        self.tab_diagram = self.tabs.add("Block Diagram")
        self.tab_report = self.tabs.add("Report")

        self._build_design_tab()
        self._build_results_tab()
        self._build_graph_tab()
        self._build_diagram_tab()
        self._build_report_tab()

    def _build_design_tab(self):
        self.tab_design.grid_columnconfigure(0, weight=1)
        self.tab_design.grid_rowconfigure(2, weight=1)
        self.tab_design.grid_rowconfigure(3, weight=1)

        settings = ctk.CTkFrame(self.tab_design, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        settings.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="ew")
        for col in range(12):
            settings.grid_columnconfigure(col, weight=1)

        self.scenario_field = LabeledEntry(settings, "Scenario", self.scenario_var)
        self.scenario_field.grid(row=0, column=0, columnspan=2, padx=8, pady=8, sticky="ew")

        self.band_frame = ctk.CTkFrame(settings, fg_color="transparent")
        self.band_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.band_frame, text="GNSS Band", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.band_menu = ctk.CTkOptionMenu(
            self.band_frame,
            values=list(GNSS_BANDS_MHZ.keys()),
            variable=self.band_var,
            command=self.band_changed,
            fg_color=COLOR_BLUE,
            button_color=COLOR_BLUE_DARK,
            button_hover_color=COLOR_BLUE_HOVER,
            text_color=("white", "white"),
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_PANEL_ALT,
            height=30,
        )
        self.band_menu.grid(row=1, column=0, sticky="ew")
        self.band_frame.grid(row=0, column=2, columnspan=3, padx=8, pady=8, sticky="ew")

        self.freq_field = LabeledEntry(settings, "Freq MHz", self.freq_var)
        self.source_field = LabeledEntry(settings, "Source dBm", self.source_var)
        self.freq_field.grid(row=0, column=5, padx=8, pady=8, sticky="ew")
        self.source_field.grid(row=0, column=6, padx=8, pady=8, sticky="ew")

        self.preset_frame = ctk.CTkFrame(settings, fg_color="transparent")
        self.preset_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.preset_frame, text="Receiver Preset", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.preset_menu = ctk.CTkOptionMenu(
            self.preset_frame,
            values=list(RECEIVER_PRESETS.keys()),
            variable=self.receiver_preset_var,
            command=self.receiver_preset_changed,
            fg_color=COLOR_BLUE,
            button_color=COLOR_BLUE_DARK,
            button_hover_color=COLOR_BLUE_HOVER,
            text_color=("white", "white"),
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_PANEL_ALT,
            height=30,
        )
        self.preset_menu.grid(row=1, column=0, sticky="ew")
        self.preset_frame.grid(row=0, column=7, columnspan=2, padx=8, pady=8, sticky="ew")

        self.min_field = LabeledEntry(settings, "Min dBm", self.min_var)
        self.max_field = LabeledEntry(settings, "Max dBm", self.max_var)
        self.target_field = LabeledEntry(settings, "Target dBm", self.target_var)
        self.min_field.grid(row=0, column=9, padx=8, pady=8, sticky="ew")
        self.max_field.grid(row=0, column=10, padx=8, pady=8, sticky="ew")
        self.target_field.grid(row=0, column=11, padx=8, pady=8, sticky="ew")

        self.freq_entry = self.freq_field.entry
        self.source_entry = self.source_field.entry
        self.min_entry = self.min_field.entry
        self.max_entry = self.max_field.entry
        self.target_entry = self.target_field.entry

        actions = ctk.CTkFrame(self.tab_design, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        actions.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="ew")
        for col in range(10):
            actions.grid_columnconfigure(col, weight=1)

        self.button(actions, "+ Add Trunk Component", lambda: self.trunk_cards.add_card()).grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        self.button(actions, "+ Add Branch", lambda: self.branch_cards.add_card()).grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        self.button(actions, "Calculate", self.calculate_now).grid(row=0, column=2, padx=6, pady=8, sticky="ew")
        self.button(actions, "Load Example", self.load_example).grid(row=0, column=3, padx=6, pady=8, sticky="ew")
        self.button(actions, "Clear", self.clear_network).grid(row=0, column=4, padx=6, pady=8, sticky="ew")
        self.button(actions, "Save JSON", self.save_json).grid(row=0, column=5, padx=6, pady=8, sticky="ew")
        self.button(actions, "Load JSON", self.load_json).grid(row=0, column=6, padx=6, pady=8, sticky="ew")
        self.button(actions, "Export CSV", self.export_csv).grid(row=0, column=7, padx=6, pady=8, sticky="ew")
        self.button(actions, "Export PNG", self.export_png).grid(row=0, column=8, padx=6, pady=8, sticky="ew")
        self.button(actions, "Graph Builder", lambda: self.tabs.set("Graph Builder")).grid(row=0, column=9, padx=6, pady=8, sticky="ew")

        self.trunk_cards = CardList(self.tab_design, "Common Trunk Components", TrunkCard, self.request_recalculate)
        self.trunk_cards.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="nsew")

        self.branch_cards = CardList(self.tab_design, "Output Branches", BranchCard, self.request_recalculate)
        self.branch_cards.grid(row=3, column=0, padx=8, pady=(0, 8), sticky="nsew")

        for var in [self.scenario_var, self.freq_var, self.source_var, self.min_var, self.max_var, self.target_var]:
            var.trace_add("write", lambda *_: self.request_recalculate())

    def _build_results_tab(self):
        self.tab_results.grid_columnconfigure(0, weight=1)
        self.tab_results.grid_rowconfigure(1, weight=1)

        summary = ctk.CTkFrame(self.tab_results, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        summary.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="ew")
        for col in range(6):
            summary.grid_columnconfigure(col, weight=1)

        self.cards: Dict[str, SummaryCard] = {}
        for idx, name in enumerate(["Trunk Output", "Branches", "Pass", "Warnings", "Worst Low", "Worst High"]):
            card = SummaryCard(summary, name)
            card.grid(row=0, column=idx, padx=6, pady=8, sticky="ew")
            self.cards[name] = card

        self.results_box = ctk.CTkTextbox(self.tab_results, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=10, text_color=COLOR_TEXT, font=ctk.CTkFont(family="Consolas", size=11))
        self.results_box.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _build_graph_tab(self):
        self.tab_graph.grid_columnconfigure(0, weight=1)
        self.tab_graph.grid_rowconfigure(0, weight=1)
        self.graph_builder = GraphBuilder(self.tab_graph, self)
        self.graph_builder.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

    def _build_diagram_tab(self):
        self.tab_diagram.grid_columnconfigure(0, weight=1)
        self.tab_diagram.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self.tab_diagram, fg_color=COLOR_PANEL_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        toolbar.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(toolbar, text="Multi-branch block diagram with trunk path and per-branch receiver levels.", text_color=COLOR_TEXT, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        self.button(toolbar, "Refresh Diagram", self.refresh_diagram).grid(row=0, column=1, padx=8, pady=8)
        self.button(toolbar, "Export PNG", self.export_png).grid(row=0, column=2, padx=(0, 8), pady=8)

        self.diagram = DiagramCanvas(self.tab_diagram)
        self.diagram.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _build_report_tab(self):
        self.tab_report.grid_columnconfigure(0, weight=1)
        self.tab_report.grid_rowconfigure(0, weight=1)
        self.report_box = ctk.CTkTextbox(self.tab_report, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=10, text_color=COLOR_TEXT, font=ctk.CTkFont(family="Consolas", size=11))
        self.report_box.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

    def request_recalculate(self):
        if not self._is_loading:
            self.debouncer.schedule()

    def calculate_now(self):
        self.debouncer.run_now()

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

    def clear_network(self):
        self._is_loading = True
        try:
            self.trunk_cards.clear_cards()
            self.branch_cards.clear_cards()
        finally:
            self._is_loading = False
        self.calculate_now()

    def load_example(self):
        self._is_loading = True
        try:
            self.scenario_var.set("Example: Source to 16-way trunk with Cube branches")
            self.band_var.set(list(GNSS_BANDS_MHZ.keys())[0])
            self.freq_var.set(str(GNSS_BANDS_MHZ[self.band_var.get()]))
            self.source_var.set("1")
            self.receiver_preset_var.set("Conservative GNSS receiver window")
            self.min_var.set("-130")
            self.max_var.set("-35")
            self.target_var.set("-100")

            self.trunk_cards.from_list([
                {"enabled": True, "name": "Main amplifier", "type": "Amplifier", "option": "LNA / Line Amp", "length_m": "0", "value_db": "20", "qty": "1", "nf_db": "2", "p1db_dbm": "10", "dc_pass": True},
                {"enabled": True, "name": "Main 16-way splitter", "type": "Splitter", "option": "16-way", "length_m": "0", "value_db": "0", "qty": "1", "nf_db": "0", "p1db_dbm": "", "dc_pass": True},
            ])

            self.branch_cards.from_list([
                {"enabled": True, "name": "Cube 2025", "cable_type": "LMR-200", "length_m": "48", "attenuator_db": "0", "amp_gain_db": "0", "amp_nf_db": "2", "amp_p1db_dbm": "10", "splitter": "None", "custom_splitter_db": "0", "connector_loss_db": "0.4", "receiver_count": "1", "dc_required": False, "dc_pass": True},
                {"enabled": True, "name": "Cube 2142 local 6-way", "cable_type": "LMR-200", "length_m": "115", "attenuator_db": "6", "amp_gain_db": "0", "amp_nf_db": "2", "amp_p1db_dbm": "10", "splitter": "6-way", "custom_splitter_db": "0", "connector_loss_db": "0.4", "receiver_count": "6", "dc_required": False, "dc_pass": True},
                {"enabled": True, "name": "Reference receiver", "cable_type": "LMR-240", "length_m": "30", "attenuator_db": "10", "amp_gain_db": "0", "amp_nf_db": "2", "amp_p1db_dbm": "10", "splitter": "None", "custom_splitter_db": "0", "connector_loss_db": "0.4", "receiver_count": "1", "dc_required": True, "dc_pass": True},
            ])
        finally:
            self._is_loading = False
        self.calculate_now()

    def calculate_trunk(self, freq_mhz: float, source_dbm: float) -> Tuple[List[StageResult], float, float]:
        results: List[StageResult] = []
        current = source_dbm
        cumulative = 0.0
        for card in self.trunk_cards.active_cards():
            stages, current, cumulative = card.calculate(freq_mhz, current, cumulative)
            results.extend(stages)
        return results, current, cumulative

    def calculate_branch(
        self,
        card: BranchCard,
        trunk_output_dbm: float,
        common_stages: List[StageResult],
        freq_mhz: float,
        target_dbm: float,
        min_dbm: float,
        max_dbm: float,
        trunk_dc_available: bool,
    ) -> BranchResult:
        name = card.name_var.get()
        enabled = card.enabled_var.get()
        if not enabled:
            return BranchResult(name, False, card.cable_type_var.get(), 0.0, 0.0, trunk_output_dbm, 0.0, 0.0, 0.0, "DISABLED", False, False, 0.0, 0, [], [])

        cable_type = card.cable_type_var.get()
        length_m = safe_float(card.length_var.get(), 0.0, card.length_entry, field_name=f"{name} length")
        atten = abs(safe_float(card.atten_var.get(), 0.0, card.atten_entry, field_name=f"{name} attenuator"))
        amp_gain = safe_float(card.amp_gain_var.get(), 0.0, card.amp_gain_entry, field_name=f"{name} amplifier gain")
        amp_nf = max(0.0, safe_float(card.amp_nf_var.get(), 2.0, card.amp_nf_entry, field_name=f"{name} amplifier NF"))
        amp_p1db = safe_float(card.amp_p1db_var.get(), 10.0, card.amp_p1db_entry, field_name=f"{name} amplifier P1dB")
        splitter = card.splitter_var.get()
        custom_splitter = abs(safe_float(card.custom_splitter_var.get(), 0.0, card.custom_splitter_entry, field_name=f"{name} custom splitter"))
        connector_loss = abs(safe_float(card.connector_var.get(), 0.4, card.connector_entry, field_name=f"{name} connector loss"))
        rx_count = safe_int(card.receiver_count_var.get(), 1, 1, card.receiver_count_entry, field_name=f"{name} receiver quantity")
        dc_required = card.dc_required_var.get()
        branch_dc_pass = card.dc_pass_var.get()

        stage_lines: List[str] = []
        nf_stages: List[Tuple[float, float]] = [(s.gain_db, s.nf_db) for s in common_stages]
        level = trunk_output_dbm
        gain_total = 0.0
        warnings: List[str] = []

        loss = cable_loss_db(cable_type, length_m, freq_mhz)
        level -= loss
        gain_total -= loss
        nf_stages.append((-loss, loss))
        stage_lines.append(f"Cable {cable_type}, {length_m:.2f} m: -{loss:.2f} dB, level {level:.2f} dBm")

        if atten > 0:
            level -= atten
            gain_total -= atten
            nf_stages.append((-atten, atten))
            stage_lines.append(f"Attenuator: -{atten:.2f} dB, level {level:.2f} dBm")

        if amp_gain != 0:
            amp_input = level
            level += amp_gain
            gain_total += amp_gain
            nf_stages.append((amp_gain, amp_nf))
            stage_lines.append(f"Branch amplifier: +{amp_gain:.2f} dB, NF {amp_nf:.2f} dB, level {level:.2f} dBm")
            if level > amp_p1db - 10:
                warnings.append(f"Branch amplifier output {level:.2f} dBm is within 10 dB of P1dB {amp_p1db:.2f} dBm")
            if amp_input > amp_p1db - amp_gain - 10:
                warnings.append("Branch amplifier input may be too high for linear operation")

        splitter_loss = SPLITTER_LOSS_DB.get(splitter, 0.0)
        if splitter == "Custom Splitter":
            splitter_loss = custom_splitter
        if splitter_loss > 0:
            level -= splitter_loss
            gain_total -= splitter_loss
            nf_stages.append((-splitter_loss, splitter_loss))
            stage_lines.append(f"Local splitter {splitter}: -{splitter_loss:.2f} dB, level {level:.2f} dBm")

        if connector_loss > 0:
            level -= connector_loss
            gain_total -= connector_loss
            nf_stages.append((-connector_loss, connector_loss))
            stage_lines.append(f"Receiver jumper/connectors: -{connector_loss:.2f} dB, level {level:.2f} dBm")

        dc_available = trunk_dc_available and branch_dc_pass
        if dc_required and not dc_available:
            warnings.append("DC path blocked while this branch requires DC power")

        min_margin = level - min_dbm
        max_headroom = max_dbm - level
        target_margin = level - target_dbm

        if dc_required and not dc_available:
            status = "DC BLOCKED"
        elif level < min_dbm:
            status = "WEAK SIGNAL"
        elif level > max_dbm:
            status = "OVERDRIVE RISK"
        elif abs(target_margin) <= 3.0:
            status = "NEAR TARGET"
        else:
            status = "PASS"

        if level < min_dbm:
            warnings.append(f"Final level is {abs(min_margin):.2f} dB below receiver minimum")
        if level > max_dbm:
            warnings.append(f"Final level is {abs(max_headroom):.2f} dB above receiver maximum")

        system_nf = cascade_noise_figure_db(nf_stages)

        return BranchResult(
            name=name,
            enabled=True,
            cable_type=cable_type,
            cable_length_m=length_m,
            branch_gain_db=gain_total,
            final_level_dbm=level,
            target_margin_db=target_margin,
            min_margin_db=min_margin,
            max_headroom_db=max_headroom,
            status=status,
            dc_required=dc_required,
            dc_available=dc_available,
            system_nf_db=system_nf,
            receiver_count=rx_count,
            warnings=warnings,
            stage_lines=stage_lines,
        )

    def recalculate(self):
        if not hasattr(self, "trunk_cards"):
            return

        try:
            freq_mhz = safe_float(self.freq_var.get(), 1575.42, self.freq_entry, allow_blank=False, field_name="Frequency MHz")
            source_dbm = safe_float(self.source_var.get(), -85.0, self.source_entry, allow_blank=False, field_name="Source dBm")
            target_dbm = safe_float(self.target_var.get(), -100.0, self.target_entry, allow_blank=False, field_name="Target dBm")
            min_dbm = safe_float(self.min_var.get(), DEFAULT_RECEIVER_MIN_DBM, self.min_entry, allow_blank=False, field_name="Receiver minimum dBm")
            max_dbm = safe_float(self.max_var.get(), DEFAULT_RECEIVER_MAX_DBM, self.max_entry, allow_blank=False, field_name="Receiver maximum dBm")

            trunk_results, trunk_output, _trunk_gain = self.calculate_trunk(freq_mhz, source_dbm)
            trunk_dc_available = all(s.dc_pass for s in trunk_results)

            branch_results = [
                self.calculate_branch(card, trunk_output, trunk_results, freq_mhz, target_dbm, min_dbm, max_dbm, trunk_dc_available)
                for card in self.branch_cards.active_cards()
            ]
        except InputValidationHold as exc:
            self.show_validation_hold(str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Calculation Error", f"Calculation failed.\n\nDetail: {exc}")
            return

        self.current_freq_mhz = freq_mhz
        self.current_source_dbm = source_dbm
        self.trunk_results = trunk_results
        self.branch_results = branch_results

        self.global_warnings = []
        if freq_mhz < 1000.0 or freq_mhz > 1800.0:
            self.global_warnings.append(f"Frequency {freq_mhz:.1f} MHz is outside cable table range 1000 to 1800 MHz. Loss is extrapolated.")

        active_branches = [b for b in self.branch_results if b.enabled]
        pass_count = sum(1 for b in active_branches if b.status in ["PASS", "NEAR TARGET"])
        warning_count = sum(len(b.warnings) for b in active_branches) + len(self.global_warnings) + sum(len(s.warnings) for s in self.trunk_results)

        self.cards["Trunk Output"].set_value(f"{trunk_output:.2f} dBm")
        self.cards["Branches"].set_value(str(len(active_branches)))
        self.cards["Pass"].set_value(str(pass_count))
        self.cards["Warnings"].set_value(str(warning_count))
        if active_branches:
            self.cards["Worst Low"].set_value(f"{min(b.min_margin_db for b in active_branches):+.2f} dB")
            self.cards["Worst High"].set_value(f"{min(b.max_headroom_db for b in active_branches):+.2f} dB")
        else:
            self.cards["Worst Low"].set_value("N/A")
            self.cards["Worst High"].set_value("N/A")

        self.update_results()
        self.refresh_graph_builder()
        self.refresh_diagram()
        self.update_report()

    def show_validation_hold(self, message: str):
        if hasattr(self, "results_box"):
            self.results_box.configure(state="normal")
            self.results_box.delete("1.0", "end")
            self.results_box.insert(
                "end",
                "Calculation paused because one or more numeric inputs are incomplete or invalid.\n\n"
                f"{message}\n\n"
                "Finish typing the number, then press Calculate or wait for automatic recalculation.",
            )
            self.results_box.configure(state="disabled")

    def update_results(self):
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end", f"{self.scenario_var.get()}\n")
        self.results_box.insert("end", "=" * 118 + "\n")
        for warning in self.global_warnings:
            self.results_box.insert("end", f"Global Warning: {warning}\n")
        self.results_box.insert("end", f"{'Branch':<28} {'Final dBm':>12} {'Target':>10} {'Min Mar':>10} {'Max Head':>10} {'NF dB':>8} {'Rx':>4} {'DC':>8} {'Status':>16}\n")
        self.results_box.insert("end", "-" * 118 + "\n")
        for b in self.branch_results:
            dc_text = "OK" if b.dc_available else "Blocked"
            self.results_box.insert("end", f"{b.name[:28]:<28} {b.final_level_dbm:>12.2f} {b.target_margin_db:>+10.2f} {b.min_margin_db:>+10.2f} {b.max_headroom_db:>+10.2f} {b.system_nf_db:>8.2f} {b.receiver_count:>4} {dc_text:>8} {b.status:>16}\n")
            for warning in b.warnings:
                self.results_box.insert("end", f"    Warning: {warning}\n")

        trunk_warnings = [(s.name, w) for s in self.trunk_results for w in s.warnings]
        if trunk_warnings:
            self.results_box.insert("end", "\nTrunk Path Warnings:\n")
            for name, warning in trunk_warnings:
                self.results_box.insert("end", f"    {name}: {warning}\n")
        self.results_box.configure(state="disabled")

    def refresh_graph_builder(self):
        if hasattr(self, "graph_builder"):
            self.graph_builder.update_from_app()

    def refresh_diagram(self):
        if hasattr(self, "diagram"):
            self.diagram.draw_network(
                self.current_source_dbm,
                self.current_freq_mhz,
                self.scenario_var.get(),
                self.trunk_results,
                [b for b in self.branch_results if b.enabled],
            )

    def update_report(self):
        self.report_box.configure(state="normal")
        self.report_box.delete("1.0", "end")
        lines = [
            APP_TITLE,
            APP_BRAND,
            "",
            f"Scenario: {self.scenario_var.get()}",
            f"Schema version: {SCHEMA_VERSION}",
            f"Band: {self.band_var.get()}",
            f"Frequency: {self.current_freq_mhz:.3f} MHz",
            f"Source: {self.current_source_dbm:.2f} dBm",
        ]
        if self.global_warnings:
            lines.extend(["", "Global Warnings:"])
            lines.extend(f" - {w}" for w in self.global_warnings)

        lines.extend(["", "Common Trunk Path", "-" * 88])
        if not self.trunk_results:
            lines.append("No common trunk components.")
        for idx, st in enumerate(self.trunk_results, 1):
            lines.append(f"{idx}. {st.name} | {st.component_type} | {st.gain_db:+.2f} dB | Output {st.output_dbm:.2f} dBm | DC {'Pass' if st.dc_pass else 'Blocked'}")
            lines.append(f"   {st.detail}")
            for warning in st.warnings:
                lines.append(f"   Warning: {warning}")

        lines.extend(["", "Branch Results", "-" * 88])
        for b in self.branch_results:
            lines.append(f"{b.name}: {b.status}")
            lines.append(f"   Final level: {b.final_level_dbm:.2f} dBm")
            lines.append(f"   Target margin: {b.target_margin_db:+.2f} dB")
            lines.append(f"   Min margin: {b.min_margin_db:+.2f} dB")
            lines.append(f"   Max headroom: {b.max_headroom_db:+.2f} dB")
            lines.append(f"   System NF estimate: {b.system_nf_db:.2f} dB")
            lines.append(f"   Receivers fed by branch: {b.receiver_count}")
            lines.append(f"   DC required: {'Yes' if b.dc_required else 'No'}")
            lines.append(f"   DC available: {'Yes' if b.dc_available else 'No'}")
            for item in b.stage_lines:
                lines.append(f"      {item}")
            for warning in b.warnings:
                lines.append(f"      Warning: {warning}")
            lines.append("")

        lines.extend([
            "Engineering Notes",
            "-" * 88,
            "1. Cable values are planning approximations. Confirm final values with datasheet or measured VNA S21.",
            "2. Confirm DC pass path through splitters, DC blocks, and Bias-T locations.",
            "3. Amplifier compression warnings use a conservative 10 dB headroom check against P1dB.",
            "4. Noise figure is estimated using a Friis cascade model and passive insertion loss values.",
            "5. Export the CSV table and PNG diagram after final measured values are entered.",
        ])
        self.report_box.insert("end", "\n".join(lines))
        self.report_box.configure(state="disabled")

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
            "trunk_components": self.trunk_cards.to_list(),
            "branches": self.branch_cards.to_list(),
            "cable_library": CABLE_LOSS_DB_PER_100M,
            "graph_positions": self.graph_builder.node_positions if hasattr(self, "graph_builder") else {},
        }

    def load_project_dict(self, data: dict):
        self._is_loading = True
        try:
            self.scenario_var.set(str(data.get("scenario", "GNSS Building Distribution Network")))
            self.band_var.set(str(data.get("band", list(GNSS_BANDS_MHZ.keys())[0])))
            self.freq_var.set(str(data.get("frequency_mhz", "1575.42")))
            self.source_var.set(str(data.get("source_dbm", "-85")))

            preset = str(data.get("receiver_preset", "Custom"))
            self.receiver_preset_var.set(preset)
            self.min_var.set(str(data.get("receiver_min_dbm", DEFAULT_RECEIVER_MIN_DBM)))
            self.max_var.set(str(data.get("receiver_max_dbm", DEFAULT_RECEIVER_MAX_DBM)))
            self.target_var.set(str(data.get("target_dbm", DEFAULT_TARGET_DBM)))

            self.trunk_cards.from_list(data.get("trunk_components", []))
            self.branch_cards.from_list(data.get("branches", []))
            if hasattr(self, "graph_builder"):
                positions = data.get("graph_positions", {})
                if isinstance(positions, dict):
                    self.graph_builder.node_positions = {str(k): tuple(v) for k, v in positions.items() if isinstance(v, (list, tuple)) and len(v) == 2}
        finally:
            self._is_loading = False
        self.calculate_now()

    def save_json(self):
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Save GNSS Network Scenario", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.project_to_dict(), handle, indent=2)
            messagebox.showinfo("Saved", f"Scenario saved:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Save Failed", f"Permission denied while saving JSON.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Unable to save JSON file.\n\nDetail: {exc}")

    def load_json(self):
        path = filedialog.askopenfilename(title="Load GNSS Network Scenario", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise json.JSONDecodeError("Top-level JSON must be an object.", doc="", pos=0)
            self.load_project_dict(data)
            messagebox.showinfo("Loaded", f"Scenario loaded:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Load Failed", f"Permission denied while loading JSON.\n\nDetail: {exc}")
        except json.JSONDecodeError as exc:
            messagebox.showerror("Load Failed", f"Invalid JSON scenario file.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Load Failed", f"Unable to load JSON file.\n\nDetail: {exc}")
        except Exception as exc:
            messagebox.showerror("Load Failed", f"Scenario load failed.\n\nDetail: {exc}")

    def export_csv(self):
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Export Multi-Branch CSV Report", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([APP_TITLE])
                writer.writerow([APP_BRAND])
                writer.writerow(["Schema version", SCHEMA_VERSION])
                writer.writerow(["Scenario", self.scenario_var.get()])
                writer.writerow(["Band", self.band_var.get()])
                writer.writerow(["Frequency MHz", f"{self.current_freq_mhz:.3f}"])
                writer.writerow(["Source dBm", f"{self.current_source_dbm:.2f}"])
                writer.writerow([])
                writer.writerow(["Common trunk path"])
                writer.writerow(["No.", "Name", "Type", "Option", "Detail", "Gain dB", "NF dB", "Input dBm", "Output dBm", "Cumulative dB", "DC Pass", "P1dB dBm", "Warnings"])
                for idx, st in enumerate(self.trunk_results, 1):
                    writer.writerow([idx, st.name, st.component_type, st.option, st.detail, f"{st.gain_db:.2f}", f"{st.nf_db:.2f}", f"{st.input_dbm:.2f}", f"{st.output_dbm:.2f}", f"{st.cumulative_gain_db:.2f}", st.dc_pass, "" if st.p1db_dbm is None else f"{st.p1db_dbm:.2f}", " | ".join(st.warnings)])
                writer.writerow([])
                writer.writerow(["Branch results"])
                writer.writerow(["Branch", "Status", "Final dBm", "Target Margin dB", "Min Margin dB", "Max Headroom dB", "System NF dB", "Receiver Count", "DC Required", "DC Available", "Warnings"])
                for b in self.branch_results:
                    writer.writerow([b.name, b.status, f"{b.final_level_dbm:.2f}", f"{b.target_margin_db:.2f}", f"{b.min_margin_db:.2f}", f"{b.max_headroom_db:.2f}", f"{b.system_nf_db:.2f}", b.receiver_count, b.dc_required, b.dc_available, " | ".join(b.warnings)])
            messagebox.showinfo("Exported", f"CSV report exported:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Export Failed", f"Permission denied while exporting CSV.\n\nDetail: {exc}")
        except InputValidationHold as exc:
            messagebox.showerror("Export Failed", f"Cannot export while inputs are invalid.\n\nDetail: {exc}")
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Unable to export CSV file.\n\nDetail: {exc}")

    def export_png(self):
        if not HAS_PILLOW:
            messagebox.showerror("Pillow Missing", "PNG export requires Pillow. Install it with:\n\npip install pillow")
            return
        self.calculate_now()
        path = filedialog.asksaveasfilename(title="Export Multi-Branch Block Diagram PNG", defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if not path:
            return
        try:
            self.diagram.export_png(
                path,
                self.current_source_dbm,
                self.current_freq_mhz,
                self.scenario_var.get(),
                self.trunk_results,
                [b for b in self.branch_results if b.enabled],
            )
            messagebox.showinfo("Exported", f"Block diagram exported:\n{path}")
        except PermissionError as exc:
            messagebox.showerror("Export Failed", f"Permission denied while exporting PNG.\n\nDetail: {exc}")
        except Exception as exc:
            messagebox.showerror("Export Failed", f"PNG export failed.\n\nDetail: {exc}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
