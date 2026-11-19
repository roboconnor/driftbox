"""Manage mpv playback processes for Driftbox.

This module starts, tracks, inspects and stops the external mpv processes
used to play soundscape audio. It is designed for use by multiple scheduler
threads, so access to the shared process registry is protected by a lock.
"""

import logging
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .config import DriftboxConfig


logger = logging.getLogger(__name__)


@dataclass
class PlaybackProcess:
    """A single mpv playback process and its identifying metadata.

    Attributes:
        layer_name: Name of the soundscape layer that started the process.
        file: Absolute path to the audio file being played.
        process: The underlying mpv subprocess.
        started_at: Unix timestamp at which playback was started.
    """

    layer_name: str
    file: Path
    process: subprocess.Popen
    started_at: float


@dataclass
class PlayerManager:
    """Start and supervise mpv playback processes.

    The manager keeps a registry of active mpv processes. Scheduler threads
    may start sounds concurrently, so every read, write and removal from
    ``processes`` must use ``_processes_lock``.

    Attributes:
        config: Validated Driftbox configuration.
        processes: Active playback processes, keyed by layer and process ID.
        _processes_lock: Lock protecting the shared process registry.
    """

    config: DriftboxConfig
    processes: dict[str, PlaybackProcess] = field(default_factory=dict)
    _processes_lock: threading.Lock = field(default_factory=threading.Lock)

    def _resolve(self, relative_path: str) -> Path:
        """Resolve an audio path within the configured audio root.

        Args:
            relative_path: Audio path relative to ``config.audio_root``.

        Returns:
            An absolute, resolved path to the requested audio file.

        Raises:
            ValueError: If the resolved path escapes the configured audio
                root.
        """
        path = (self.config.audio_root / relative_path).resolve()
        root = self.config.audio_root.resolve()

        if not path.is_relative_to(root):
            raise ValueError(
                f"Audio path escapes audio root: {relative_path}"
            )

        return path

    def _base_command(self) -> list[str]:
        """Build the common mpv command-line arguments.

        Returns:
            Arguments that disable video, suppress terminal output and run
            mpv quietly.

        Raises:
            RuntimeError: If the configured mpv executable cannot be found.
        """
        if shutil.which(self.config.mpv_binary) is None:
            raise RuntimeError(
                f"mpv not found: {self.config.mpv_binary}. "
                "Install mpv or set mpv_binary."
            )

        return [
            self.config.mpv_binary,
            "--no-video",
            "--really-quiet",
            "--no-terminal",
            # Leave audio-output selection to mpv so the same code works on
            # macOS and Raspberry Pi OS. Do not force ALSA on macOS.
            # "--ao=alsa",
        ]

    def start_single_loop(self) -> None:
        """Start an endlessly repeating mpv process for single-loop mode.

        Raises:
            ValueError: If the configuration does not define a single-loop
                file.
        """
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

        playback = PlaybackProcess(
            layer_name="single_loop",
            file=file_path,
            process=process,
            started_at=0,
        )

        with self._processes_lock:
            self.processes["single_loop"] = playback

    def start_layer_file(
        self,
        layer_name: str,
        file_path: Path,
        gain: float,
    ) -> PlaybackProcess:
        """Start one mpv process for a generative soundscape layer.

        Args:
            layer_name: Name of the layer requesting playback.
            file_path: Absolute path to the audio file to play.
            gain: Playback gain, expressed as a value from ``0`` to ``1``.

        Returns:
            The newly registered :class:`PlaybackProcess`.

        Side effects:
            Starts an mpv subprocess and adds it to the shared process
            registry.
        """
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

        with self._processes_lock:
            self.processes[key] = playback

        return playback

    def stop_all(self) -> None:
        """Stop every tracked mpv process and clear the process registry.

        Running processes are asked to terminate. If a process does not exit
        within three seconds, it is killed.

        Side effects:
            Terminates or kills mpv processes and empties ``processes``.
        """
        with self._processes_lock:
            playbacks = list(self.processes.values())

        for playback in playbacks:
            if playback.process.poll() is None:
                playback.process.terminate()

        for playback in playbacks:
            try:
                playback.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                playback.process.kill()

        with self._processes_lock:
            self.processes.clear()

    def prune_finished(self) -> None:
        """Remove completed mpv processes from the shared registry.

        A process is considered finished when its ``poll()`` result is not
        ``None``. Errors while checking a process are logged, and the affected
        process is removed so that one failed process cannot permanently block
        a layer.

        Side effects:
            Removes completed or unusable entries from ``processes``.
        """
        with self._processes_lock:
            finished_keys = []

            # Iterate over a snapshot: another scheduler thread may add or
            # remove a process while this method is running.
            for key, playback in list(self.processes.items()):
                process = playback.process

                try:
                    if process.poll() is not None:
                        finished_keys.append(key)
                except Exception as exc:
                    logger.warning(
                        "Error checking mpv process %s: %s",
                        key,
                        exc,
                    )
                    finished_keys.append(key)

            for key in finished_keys:
                self.processes.pop(key, None)

    def active_count(self, layer_name: str) -> int:
        """Count the running playback processes belonging to a layer.
it
        Completed processes are removed before counting.

        Args:
            layer_name: Name of the soundscape layer to inspect.

        Returns:
            The number of registered processes in the layer that are still
            running.
        """
        self.prune_finished()

        with self._processes_lock:
            return sum(
                1
                for playback in self.processes.values()
                if playback.layer_name == layer_name
                and playback.process.poll() is None
            )