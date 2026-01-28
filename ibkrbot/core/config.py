from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

from .paths import resource_path, user_data_dir

def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out

def default_config_path() -> Path:
    return resource_path("config.default.json")

def user_config_path() -> Path:
    return (user_data_dir() / "config.json").resolve()

def load_config() -> Dict[str, Any]:
    default_cfg = json.loads(default_config_path().read_text(encoding="utf-8"))
    user_p = user_config_path()
    if user_p.exists():
        try:
            user_cfg = json.loads(user_p.read_text(encoding="utf-8"))
        except Exception:
            user_cfg = {}
    else:
        user_cfg = {}
    return _deep_merge(default_cfg, user_cfg)

def save_user_config(cfg: Dict[str, Any]) -> None:
    user_config_path().write_text(json.dumps(cfg, indent=2), encoding="utf-8")
