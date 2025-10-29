from __future__ import annotations
import os
import sys
import uvicorn


def main() -> None:
    host = os.getenv("GLIH_BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("GLIH_BACKEND_PORT", "8000"))
    reload = os.getenv("GLIH_BACKEND_RELOAD", "1") not in {"0", "false", "False"}

    # Run by module path to avoid path issues
    uvicorn.run(
        "glih_backend.api.main:app",
        host=host,
        port=port,
        reload=reload,
        # Ensure the project root is watched; optional but safe
        # reload_dirs=[os.getcwd()],
        # Use the current interpreter for the reloader
        # (uvicorn uses sys.executable internally)
    )


if __name__ == "__main__":
    main()
