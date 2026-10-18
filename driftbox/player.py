import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import DriftboxConfig


@dataclass
class PlaybackProcess:
    layer_name: str
    file: Path
    process: subprocess.Popen
    started_at: float


@dataclass
class PlayerManager:
    config: DriftboxConfig
    processes: dict[str, PlaybackProcess] = field(default_factory=dict)

    def _resolve(self, relative_path: str) -> Path:
        path = (self.config.audio_root / relative_path).resolve()
        root = self.config.audio_root.resolve()

        if not path.is_relative_to(root):
            raise ValueError(f"Audio path escapes audio root: {relative_path}")

        return path

    def _base_command(self) -> list[str]:
        if shutil.which(self.config.mpv_binary) is None:
            raise RuntimeError(
                f"mpv not found: {self.config.mpv_binary}. Install mpv or set mpv_binary."
            )

        return [
            self.config.mpv_binary,
            "--no-video",
            "--really-quiet",
            "--no-terminal",
        ]

    def start_single_loop(self) -> None:
        if not self.config.single_loop:
            raise ValueError("No single_loop configuration")

        file_path = self._resolve(self.config.single_loop.file)

        command = self._base_command() + [
            "--loop-file=inf",
            f"--volume={int(self.config.single_loop.gain * 100)}",
            str(file_path),
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.processes["single_loop"] = PlaybackProcess(
            layer_name="single_loop",
            file=file_path,
            process=process,
            started_at=0,
        )

    def start_layer_file(
        self,
        layer_name: str,
        file_path: Path,
        gain: float,
    ) -> PlaybackProcess:
        command = self._base_command() + [
            f"--volume={int(gain * 100)}",
            str(file_path),
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        playback = PlaybackProcess(
            layer_name=layer_name,
            file=file_path,
            process=process,
            started_at=0,
        )

        key = f"{layer_name}:{process.pid}"
        self.processes[key] = playback
        return playback

    def stop_all(self) -> None:
        for playback in list(self.processes.values()):
            if playback.process.poll() is None:
                playback.process.terminate()

        for playback in self.processes.values():
            try:
                playback.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                playback.process.kill()

        self.processes.clear()

    def prune_finished(self) -> None:
        finished = [
            key
            for key, playback in self.processes.items()
            if playback.process.poll() is not None
        ]

        for key in finished:
            self.processes.pop(key, None)

    def active_count(self, layer_name: str) -> int:
        self.prune_finished()
        return sum(
            1
            for playback in self.processes.values()
            if playback.layer_name == layer_name
            and playback.process.poll() is None
        )