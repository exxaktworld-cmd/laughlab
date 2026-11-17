import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load_config():
    with (ROOT / "config/settings.yaml").open(encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    with (ROOT / "config/sources.yaml").open(encoding="utf-8") as f:
        sources = yaml.safe_load(f)
    settings["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    settings["gemini_model"] = os.getenv("GEMINI_MODEL") or settings["gemini_model_default"]
    settings["root"] = ROOT
    return settings, sources
