"""Bounded presentation-only adjustments; no arbitrary TeX or content edits."""
from pathlib import Path
import math
import yaml

DEFAULTS = {"figure_width": 0.82, "textfloatsep_pt": 14, "floatsep_pt": 12}
BOUNDS = {"figure_width": (0.6, 1.0), "textfloatsep_pt": (10, 20), "floatsep_pt": (8, 18)}


def settings(experiment: Path) -> dict:
    path = experiment / "spec/LAYOUT_TUNING.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if not isinstance(data, dict) or set(data) - DEFAULTS.keys():
        raise ValueError("LAYOUT_TUNING: only figure_width, textfloatsep_pt and floatsep_pt are allowed")
    for key, value in data.items():
        low, high = BOUNDS[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"LAYOUT_TUNING: {key} must be between {low} and {high}")
    return DEFAULTS | data


def tex(experiment: Path, mode: str) -> str:
    configured = settings(experiment)
    values = DEFAULTS if mode == "skeleton" else configured
    result = rf"\providecommand{{\ReportFigureWidth}}{{{values['figure_width']}\linewidth}}" + "\n"
    if mode != "skeleton" and (experiment / "spec/LAYOUT_TUNING.yaml").is_file():
        for key, command in (("textfloatsep_pt", "textfloatsep"), ("floatsep_pt", "floatsep")):
            result += rf"\setlength{{\{command}}}{{{values[key]}pt}}" + "\n"
    return result
