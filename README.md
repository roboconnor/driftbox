# Driftbox

Driftbox is an offline-first, sample-based soundscape player for Raspberry Pi installations.

It plays prerecorded MP3 files in configurable layers, using random selection and variable gaps to create an evolving soundscape without relying on audio synthesis. It can also play a single MP3 on repeat.

## Why Driftbox?

Driftbox was developed for unattended sound installations, where a Raspberry Pi may run for days with no monitor, keyboard, or network connection.

It is designed to:

- Play prerecorded MP3 material only
- Create evolving soundscapes from a finite library of sounds
- Run headlessly on a Raspberry Pi
- Start automatically at boot
- Continue playing without an internet connection
- Be configured through a simple local web interface
- Recover from playback-process failures

## Current status

**Version 0.1 — Halloween build**

Driftbox currently supports:

- Single-loop playback of one MP3
- Generative playback from multiple folders
- Random file selection
- Random gaps between sounds
- Per-layer gain and concurrency limits
- A minimal FastAPI web interface
- Status reporting through `/api/status`
- Configuration reloading and playback restart

Not yet implemented:

- Musical tempo synchronisation
- Sample-accurate multi-track scheduling
- Wi-Fi service hotspot
- Docker deployment
- Multi-device monitoring
- File upload through the web interface

## Requirements

- Python 3.10 or later
- [mpv](https://mpv.io/)
- Raspberry Pi OS Lite, macOS, or Linux
- Local MP3 files

On macOS, install mpv with Homebrew:

```bash
brew install mpv
```

On Raspberry Pi OS or Debian:

```bash
sudo apt update
sudo apt install -y mpv
```

## Installation

Clone the repository:

```bash
git clone [https://github.com/roboconnor/driftbox.git](https://github.com/roboconnor/driftbox.git)
cd driftbox
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Driftbox:

```bash
pip install -e .
```

## Add audio

Place MP3 files in folders beneath `audio/`.

For example:

```text
audio/
  bed/
    wind_01.mp3
    wind_02.mp3
    rumble_01.mp3
  events/
    creak_01.mp3
    footstep_01.mp3
    whisper_01.mp3
```

Audio files are not stored in this repository. Copy them into the local `audio/` directory before running Driftbox.

## Configuration

Driftbox uses a YAML configuration file.

The development configuration is:

```text
config/development.yaml
```

### Single-loop mode

To repeat one MP3 continuously:

```yaml
soundscape: halloween_test
audio_root: audio
mpv_binary: mpv

mode: single_loop

single_loop:
  file: bed/bed_01.mp3
  gain: 0.8
```

The `file` path is relative to `audio_root`.

### Generative layers

To play evolving layers:

```yaml
soundscape: halloween_test
audio_root: audio
mpv_binary: mpv

mode: layers

layers:
  - name: bed
    folder: bed
    min_gap_seconds: 2
    max_gap_seconds: 10
    max_concurrent: 1
    gain: 0.5

  - name: events
    folder: events
    min_gap_seconds: 30
    max_gap_seconds: 180
    max_concurrent: 2
    gain: 0.75
```

Each layer independently:

1. Selects an MP3 at random from its folder.
2. Plays it.
3. Waits for a random interval between `min_gap_seconds` and `max_gap_seconds`.
4. Selects another MP3.
5. Repeats.

Silence is created by the scheduler, not by silent MP3 files.

## Run locally

From the project root:

```bash
source .venv/bin/activate
driftbox --config config/development.yaml --reload
```

Or:

```bash
python -m driftbox.main --config config/development.yaml --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Web interface

The web interface is intentionally minimal.

It provides:

- Current playback status
- Active mpv processes
- Configuration editing
- Save and apply
- Restart playback
- Stop playback

API endpoints:

```text
GET  /api/status
GET  /api/config
POST /api/config
POST /api/restart
POST /api/stop
```

Example:

```bash
curl http://127.0.0.1:8000/api/status
```

## Raspberry Pi deployment

Driftbox is intended to run as a systemd service on a headless Raspberry Pi.

A typical production deployment uses:

- Raspberry Pi OS Lite
- A local user account, for example `driftbox`
- The project installed at `/home/driftbox/driftbox`
- A virtual environment at `/home/driftbox/driftbox/.venv`
- A production configuration at `config/deployment.yaml`
- mpv installed through APT
- Avahi enabled for `driftbox.local` discovery when a network is available

Example systemd service:

```ini
[Unit]
Description=Driftbox soundscape player
After=multi-user.target

[Service]
Type=simple
User=driftbox
WorkingDirectory=/home/driftbox/driftbox
ExecStart=/home/driftbox/driftbox/.venv/bin/python -m driftbox.main --config /home/driftbox/driftbox/config/deployment.yaml --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Install and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now driftbox
```

Check its status:

```bash
systemctl status driftbox --no-pager
```

## Offline-first design

Driftbox must be able to boot and play without:

- Ethernet
- Wi-Fi
- Internet access
- DNS
- A connected browser
- A cloud service

Network access is optional and used only for configuration, monitoring, and remote access.

When a network is available, the Pi can be reached as:

```text
http://driftbox.local:8000
```

## Development workflow

Develop and test on macOS or another local machine, then deploy the same code to a Raspberry Pi.

A typical deployment command is:

```bash
rsync -av \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude 'logs' \
  ./ driftbox@driftbox.local:~/driftbox/
```

Then restart the service on the Pi:

```bash
ssh driftbox@driftbox.local
sudo systemctl restart driftbox
```

## Project structure

```text
driftbox/
  config/           YAML configuration files
  audio/            Local MP3 library, not committed to Git
  driftbox/         Python application
  web/              Minimal web interface
  systemd/          systemd service template
  logs/             Local rotating logs, not committed to Git
```

## Roadmap

- [x] Single-loop MP3 playback
- [x] Generative multi-layer playback
- [x] FastAPI web interface
- [x] Raspberry Pi deployment
- [ ] Production configuration validation
- [ ] Wi-Fi service hotspot
- [ ] Improved status and diagnostics
- [ ] Musical synchronisation
- [ ] Sample-accurate mixer
- [ ] Containerised deployment

## Licence

To be decided.