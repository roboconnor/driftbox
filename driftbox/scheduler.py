import random
import threading
import time
from pathlib import Path

from .config import DriftboxConfig
from .logging_setup import configure_logging
from .player import PlayerManager


class Scheduler:
    def __init__(self, config: DriftboxConfig):
        self.config = config
        self.logger = configure_logging()
        self.player = PlayerManager(config)
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

    def start(self) -> None:
        self.stop_event.clear()

        if self.config.mode == "single_loop":
            self.player.start_single_loop()
            self.logger.info(
                "Started single loop: %s",
                self.config.single_loop.file,
            )
            return

        for layer in self.config.layers:
            thread = threading.Thread(
                target=self._run_layer,
                args=(layer,),
                name=f"layer-{layer.name}",
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()

    def _mp3_files(self, folder: str) -> list[Path]:
        path = self.config.audio_root / folder
        files = sorted(path.glob("*.mp3"))

        if not files:
            raise RuntimeError(f"No MP3 files in layer folder: {path}")

        return files

    def _run_layer(self, layer) -> None:
        files = self._mp3_files(layer.folder)
        self.logger.info(
            "Layer '%s' started with %d files",
            layer.name,
            len(files),
        )

        while not self.stop_event.is_set():
            try:
                while (
                    self.player.active_count(layer.name)
                    >= layer.max_concurrent
                    and not self.stop_event.is_set()
                ):
                    time.sleep(0.25)

                if self.stop_event.is_set():
                    break

                selected = random.choice(files)
                self.player.start_layer_file(
                    layer_name=layer.name,
                    file_path=selected,
                    gain=layer.gain,
                )

                self.logger.info(
                    "Layer '%s' playing: %s",
                    layer.name,
                    selected.name,
                )

                delay = random.uniform(
                    layer.min_gap_seconds,
                    layer.max_gap_seconds,
                )

                self.logger.info(
                    "Layer '%s' next selection in %.1fs",
                    layer.name,
                    delay,
                )

                self.stop_event.wait(delay)

            except Exception:
                self.logger.exception(
                    "Layer '%s' encountered an error",
                    layer.name,
                )
                self.stop_event.wait(5)

    def stop(self) -> None:
        self.stop_event.set()

        for thread in self.threads:
            thread.join(timeout=5)

        self.player.stop_all()
        self.threads.clear()
        self.logger.info("Driftbox playback stopped")

    def status(self) -> dict:
        self.player.prune_finished()

        return {
            "soundscape": self.config.soundscape,
            "mode": self.config.mode,
            "active_processes": len(self.player.processes),
            "processes": [
                {
                    "layer": playback.layer_name,
                    "file": str(playback.file),
                    "pid": playback.process.pid,
                    "running": playback.process.poll() is None,
                }
                for playback in self.player.processes.values()
            ],
        }