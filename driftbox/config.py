from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError


class SingleLoopConfig(BaseModel):
    file: str
    gain: float = Field(default=0.8, ge=0, le=1)


class LayerConfig(BaseModel):
    name: str
    folder: str
    min_gap_seconds: float = Field(default=5, ge=0)
    max_gap_seconds: float = Field(default=30, ge=0)
    max_concurrent: int = Field(default=1, ge=1)
    gain: float = Field(default=0.8, ge=0, le=1)


class DriftboxConfig(BaseModel):
    soundscape: str
    audio_root: Path = Path("audio")
    mpv_binary: str = "mpv"
    mode: Literal["single_loop", "layers"] = "layers"
    single_loop: SingleLoopConfig | None = None
    layers: list[LayerConfig] = Field(default_factory=list)

    def validate_for_mode(self) -> list[str]:
        errors: list[str] = []

        if self.mode == "single_loop":
            if not self.single_loop:
                errors.append("single_loop configuration is required")
            elif not (self.audio_root / self.single_loop.file).is_file():
                errors.append(f"Missing single-loop file: {self.single_loop.file}")

        if self.mode == "layers":
            if not self.layers:
                errors.append("At least one layer is required")

            for layer in self.layers:
                folder = self.audio_root / layer.folder
                if not folder.is_dir():
                    errors.append(f"Missing layer folder: {folder}")
                elif not any(folder.glob("*.mp3")):
                    errors.append(f"No MP3 files found in: {folder}")

                if layer.min_gap_seconds > layer.max_gap_seconds:
                    errors.append(
                        f"Layer '{layer.name}': min_gap_seconds exceeds max_gap_seconds"
                    )

        return errors


def load_config(path: str | Path) -> DriftboxConfig:
    config_path = Path(path)

    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {config_path}")

    try:
        return DriftboxConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration:\n{exc}") from exc