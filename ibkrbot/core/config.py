from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict

from .paths import resource_path, user_data_dir

_log = logging.getLogger(__name__)

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
        except Exception as e:
            _log.warning(f"Failed to load user config, using defaults: {e}")
            user_cfg = {}
    else:
        user_cfg = {}
    return _deep_merge(default_cfg, user_cfg)

def save_user_config(cfg: Dict[str, Any]) -> None:
    user_config_path().write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def validate_config(cfg: Dict[str, Any]) -> list[str]:
    """Validate config values and return list of warnings/errors."""
    warnings = []

    # IBKR settings
    ibkr = cfg.get("ibkr", {})
    port = ibkr.get("port", 0)
    if not isinstance(port, int) or port < 1 or port > 65535:
        warnings.append(f"Invalid port: {port}. Must be 1-65535.")

    client_id = ibkr.get("client_id", 0)
    if not isinstance(client_id, int) or client_id < 0:
        warnings.append(f"Invalid client_id: {client_id}. Must be non-negative integer.")

    # Risk settings
    risk = cfg.get("risk", {})
    max_notional_pct = risk.get("max_notional_pct", 0)
    if not isinstance(max_notional_pct, (int, float)) or max_notional_pct <= 0 or max_notional_pct > 1:
        warnings.append(f"max_notional_pct should be between 0 and 1 (got {max_notional_pct})")

    max_loss_pct = risk.get("max_loss_pct", 0)
    if not isinstance(max_loss_pct, (int, float)) or max_loss_pct <= 0 or max_loss_pct > 0.1:
        warnings.append(f"max_loss_pct should be between 0 and 0.1 (got {max_loss_pct})")

    r_multiple = risk.get("r_multiple_take", 0)
    if not isinstance(r_multiple, (int, float)) or r_multiple <= 0:
        warnings.append(f"r_multiple_take should be positive (got {r_multiple})")

    # Strategy settings
    strategy = cfg.get("strategy", {})
    atr_period = strategy.get("atr_period", 0)
    if not isinstance(atr_period, int) or atr_period < 1:
        warnings.append(f"atr_period should be positive integer (got {atr_period})")

    lookback = strategy.get("lookback_days", 0)
    if not isinstance(lookback, int) or lookback < 1:
        warnings.append(f"lookback_days should be positive integer (got {lookback})")

    return warnings


def get_safe_config_value(cfg: Dict[str, Any], path: str, default: Any, expected_type: type) -> Any:
    """Safely get a config value with type checking."""
    keys = path.split(".")
    value = cfg
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        if value is None:
            return default

    if not isinstance(value, expected_type):
        _log.warning(f"Config {path} has wrong type {type(value).__name__}, expected {expected_type.__name__}")
        return default
    return value
