import threading

from .config import DriftboxConfig
from .scheduler import Scheduler


class DriftboxService:
    def __init__(self, config: DriftboxConfig):
        self._config = config
        self._scheduler: Scheduler | None = None
        self._lock = threading.Lock()

    @property
    def config(self) -> DriftboxConfig:
        return self._config

    def start(self) -> None:
        with self._lock:
            if self._scheduler is not None:
                return

            scheduler = Scheduler(self._config)
            scheduler.start()
            self._scheduler = scheduler

    def stop(self) -> None:
        with self._lock:
            if self._scheduler is None:
                return

            self._scheduler.stop()
            self._scheduler = None

    def restart(self) -> None:
        self.stop()
        self.start()

    def replace_config(self, config: DriftboxConfig) -> None:
        with self._lock:
            self._config = config

            if self._scheduler is not None:
                self._scheduler.stop()
                scheduler = Scheduler(config)
                scheduler.start()
                self._scheduler = scheduler

    def status(self) -> dict:
        if self._scheduler is None:
            return {
                "running": False,
                "soundscape": self._config.soundscape,
                "mode": self._config.mode,
                "active_processes": 0,
                "processes": [],
            }

        status = self._scheduler.status()
        status["running"] = True
        return status