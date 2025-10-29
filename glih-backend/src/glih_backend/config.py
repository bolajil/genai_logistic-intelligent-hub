import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

try:
    import tomllib as toml  # Python 3.11+
except Exception:  # Python 3.10 fallback
    import tomli as toml  # type: ignore
try:
    import tomli_w as toml_w  # writer
except Exception:  # pragma: no cover
    toml_w = None  # type: ignore

load_dotenv()

_DEF_PATH = os.path.abspath(os.path.join(os.getcwd(), "config", "glih.toml"))


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg_path = path or os.getenv("GLIH_CONFIG", _DEF_PATH)
    with open(cfg_path, "rb") as f:
        cfg = toml.load(f)
    return cfg


def get_config_path(path: Optional[str] = None) -> str:
    return path or os.getenv("GLIH_CONFIG", _DEF_PATH)


def save_config(cfg: Dict[str, Any], path: Optional[str] = None) -> None:
    """Persist the in-memory config to TOML. Requires tomli-w installed."""
    cfg_path = get_config_path(path)
    if toml_w is None:
        # Soft-fail: do nothing if writer is not present
        return
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "wb") as f:
        toml_w.dump(cfg, f)
