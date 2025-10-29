from __future__ import annotations
import copy
from typing import Any, Dict

_REDACT_KEYS = ("key", "secret", "token", "password", "credential")


def sanitize_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    def _sanitize(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if any(x in k.lower() for x in _REDACT_KEYS):
                    out[k] = "***redacted***" if isinstance(v, str) else v
                else:
                    out[k] = _sanitize(v)
            return out
        elif isinstance(obj, list):
            return [_sanitize(x) for x in obj]
        return obj

    return _sanitize(copy.deepcopy(cfg))
