from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from .paths import ensure_subdirs

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def plan_dir() -> Path:
    return ensure_subdirs()["plans"]

def save_plan(plan: Dict[str, Any], kind: str) -> Path:
    # kind: 'draft' or 'placed'
    sym = plan.get("symbol", "UNKNOWN")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = plan_dir() / f"{sym}_{kind}_{ts}.json"
    p.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return p

def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))

def latest_plan(symbol: str, kind: str) -> Optional[Path]:
    files = sorted(plan_dir().glob(f"{symbol}_{kind}_*.json"), reverse=True)
    return files[0] if files else None
