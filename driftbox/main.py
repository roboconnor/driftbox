import argparse
import os

import uvicorn

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

    # Validate the chosen configuration before starting Uvicorn.
    config = load_config(args.config)
    print(f"Using configuration: {args.config}")
    print(f"Soundscape: {config.soundscape}")
    print(f"Mode: {config.mode}")

    # Make the selected configuration available to driftbox.api.
    os.environ["DRIFTBOX_CONFIG"] = str(args.config)

    uvicorn.run(
        "driftbox.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    run()