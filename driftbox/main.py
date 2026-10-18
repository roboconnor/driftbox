import argparse

import uvicorn

from .api import app
from .config import load_config
from .logging_setup import configure_logging


def run() -> None:
    parser = argparse.ArgumentParser(description="Driftbox soundscape player")
    parser.add_argument(
        "--config",
        default="config/development.yaml",
        help="Path to Driftbox configuration file",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")

    args = parser.parse_args()

    configure_logging()
    load_config(args.config)

    uvicorn.run(
        "driftbox.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    run()