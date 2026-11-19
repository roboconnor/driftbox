"""Configuration models, validation and YAML loading for Driftbox.

Driftbox configurations describe either a repeating single audio file or a
set of independent generative layers. This module turns a YAML file into a
validated :class:`DriftboxConfig` object and performs checks that depend on
the selected playback mode.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError


class SingleLoopConfig(BaseModel):
    """Configuration for a single audio file that repeats indefinitely.

    Attributes:
        file: Path to the audio file, relative to ``audio_root``.
        gain: Playback gain, expressed as a value from ``0`` to ``1``.
    """

    file: str
    gain: float = Field(default=0.8, ge=0, le=1)


class LayerConfig(BaseModel):
    """Configuration for one independently scheduled soundscape layer.

    A layer repeatedly chooses an audio file from its folder, plays it, and
    waits for a random interval before choosing another file.

    Attributes:
        name: Human-readable layer name used in logs and status output.
        folder: Audio folder, relative to ``audio_root``.
        min_gap_seconds: Minimum delay before the next file is selected.
        max_gap_seconds: Maximum delay before the next file is selected.
        max_concurrent: Maximum number of sounds allowed to play at once.
        gain: Playback gain, expressed as a value from ``0`` to ``1``.
    """

    name: str
    folder: str
    min_gap_seconds: float = Field(default=5, ge=0)
    max_gap_seconds: float = Field(default=30, ge=0)
    max_concurrent: int = Field(default=1, ge=1)
    gain: float = Field(default=0.8, ge=0, le=1)


class DriftboxConfig(BaseModel):
    """Validated configuration for a Driftbox soundscape.

    A configuration must use either ``single_loop`` or ``layers`` mode. The
    mode determines which additional settings are required and which
    filesystem checks :meth:`validate_for_mode` performs.

    Attributes:
        soundscape: Human-readable name of the configured soundscape.
        audio_root: Directory containing all soundscape audio folders.
        mpv_binary: Name or path of the mpv executable.
        mode: Playback mode: a repeating file or generative layers.
        single_loop: Settings used when ``mode`` is ``single_loop``.
        layers: Layer definitions used when ``mode`` is ``layers``.
    """

    soundscape: str
    audio_root: Path = Path("audio")
    mpv_binary: str = "mpv"
    mode: Literal["single_loop", "layers"] = "layers"
    single_loop: SingleLoopConfig | None = None
    layers: list[LayerConfig] = Field(default_factory=list)

    def validate_for_mode(self) -> list[str]:
        """Validate settings that depend on the configured playback mode.

        This performs filesystem checks in addition to the structural checks
        performed by Pydantic. It is intended to catch usable but incomplete
        configurations before playback starts.

        Returns:
            A list of human-readable error messages. An empty list means the
            configuration is valid for its selected mode.

        Side effects:
            Reads the filesystem to verify that required audio files and
            layer folders exist.
        """
        errors: list[str] = []

        if self.mode == "single_loop":
            if not self.single_loop:
                errors.append("single_loop configuration is required")
            elif not (self.audio_root / self.single_loop.file).is_file():
                errors.append(
                    f"Missing single-loop file: {self.single_loop.file}"
                )

        if self.mode == "layers":
            if not self.layers:
                errors.append("At least one layer is required")

            for layer in self.layers:
                folder = self.audio_root / layer.folder

                if not folder.is_dir():
                    errors.append(f"Missing layer folder: {folder}")
                    continue

                if not any(
                    file.suffix.lower()
                    in {
                        ".mp3",
                        ".wav",
                        ".flac",
                        ".ogg",
                        ".m4a",
                        ".aiff",
                    }
                    for file in folder.iterdir()
                    if file.is_file()
                ):
                    errors.append(
                        f"No supported audio files found in: {folder}"
                    )

                if layer.min_gap_seconds > layer.max_gap_seconds:
                    errors.append(
                        f"Layer '{layer.name}': "
                        "min_gap_seconds exceeds max_gap_seconds"
                    )

        return errors


def load_config(path: str | Path) -> DriftboxConfig:
    """Load and validate a Driftbox YAML configuration file.

    Args:
        path: Path to a YAML configuration file.

    Returns:
        A validated :class:`DriftboxConfig`.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the YAML is not a mapping or cannot be validated
            against :class:`DriftboxConfig`.
    """
    config_path = Path(path)

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Configuration must be a YAML mapping: {config_path}"
        )

    try:
        return DriftboxConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration:\n{exc}") from exc