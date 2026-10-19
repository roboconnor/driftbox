# Driftbox — Complete Project Context

**Last updated:** 19 October 2026  
**Purpose:** Restore complete context for the Driftbox project after a context-window reduction. Reupload this file at the start of a future session and ask: “Here is the Driftbox context — bring yourself up to speed.”

---

## 1. Project summary

**Driftbox** is an offline-first, sample-based soundscape player for Raspberry Pi installations.

It plays prerecorded audio files in independent layers, using random selection and variable gaps to create an evolving soundscape. It does not synthesise audio; all sound material is prerecorded.

Driftbox was developed for **Spraoi**, a local arts group in Waterford, Ireland. Spraoi uses Raspberry Pi devices as playback computers for floats and art installations. The devices are small, low-power, headless-capable, and can be connected directly to a PA system.

The original project was called **Ambirithm**. It has been renamed **Driftbox**.

The old Ambirithm repository is:

https://github.com/roboconnor/ambirithm

The owner says it is public, but automated access attempts failed. Its contents have not been reviewed. The user is not attached to the old code and chose to rebuild from scratch.

---

## 2. Immediate goal

The immediate goal is a reliable Driftbox deployment for a **Spraoi Wicked Woods installation**.

The deadline is the end of the weekend beginning 17 October 2026. The work is part-time and compressed, so version 0.1 is deliberately minimal and reliability-focused.

The current version is:

> **Driftbox 0.1 — Wicked Woods build**

It is not called the “Halloween build”. Halloween is the immediate installation context, but the product version is Wicked Woods.

---

## 3. Core requirements

### Must have

- Entirely sample-based playback.
- No audio synthesis.
- Play prerecorded MP3, WAV, FLAC, OGG, M4A, and AIFF files.
- Run on Raspberry Pi, especially Raspberry Pi 3.
- Develop primarily on macOS.
- Deploy to Raspberry Pi once stable.
- Run headlessly at the installation.
- Work without Ethernet, Wi-Fi, internet, DNS, or a cloud service.
- Start automatically at boot.
- Continue playing for long periods without intervention.
- Be configurable through a local web interface.
- Support a single longer audio file played on repeat.
- Support multiple generative layers using local folders of audio files.
- Use local storage for configuration and audio.
- Log errors and playback activity locally.

### Deferred

The following are explicitly deferred beyond version 0.1:

- Musical tempo synchronisation.
- Sample-accurate multi-track scheduling.
- Beat/bar-aware musical clock.
- Docker or other containerisation.
- Multi-device remote monitoring dashboard.
- User accounts or authentication.
- Cloud synchronisation.
- Audio analysis, BPM detection, or automatic beat matching.
- Elaborate web UI.
- File upload through the web interface.

---

## 4. Playback model

Driftbox has two playback modes.

### Single-loop mode

One specified audio file plays repeatedly.

This preserves the original, dependable Ambirithm behaviour and provides a reliable fallback for installation work.

Example:

```yaml
mode: single_loop

single_loop:
  file: bed/atmosphere_01.mp3
  gain: 0.8
```

Implementation approach:

```bash
mpv --no-video --loop-file=inf --really-quiet /path/to/file.mp3
```

Driftbox should supervise the mpv process rather than simply launch it. It should record the process, detect unexpected exits, log them, and restart the process with a bounded retry policy.

### Generative layers mode

Several independent layers play sounds from configured local folders.

Each layer:

1. Selects an audio file at random from its folder.
2. Plays it.
3. Waits for a random interval between configured minimum and maximum gap values.
4. Selects another file.
5. Repeats.

Silence is produced by the scheduler, not by silent audio files. Silent MP3s are no longer needed for the core design.

Each layer can have:

- A folder of permitted audio files.
- Minimum and maximum gap between selections.
- Maximum number of concurrent sounds.
- Gain level.
- A human-readable name.

---

## 5. Wicked Woods 0.1 configuration

The production configuration is:

```text
config/wicked_woods_birds_wolves.yaml
```

The exact configuration tested overnight is:

```yaml
soundscape: wicked_woods_birds_wolves
audio_root: audio
mpv_binary: mpv


mode: layers


layers:
  - name: atmosphere
    folder: bed
    min_gap_seconds: 2
    max_gap_seconds: 15
    max_concurrent: 2
    gain: 0.8


  - name: bowed_piano
    folder: bowed
    min_gap_seconds: 40
    max_gap_seconds: 140
    max_concurrent: 1
    gain: 0.5


  - name: freaky_piano
    folder: piano
    min_gap_seconds: 20
    max_gap_seconds: 80
    max_concurrent: 1
    gain: 0.65

  - name: birds
    folder: birds
    min_gap_seconds: 6
    max_gap_seconds: 25
    max_concurrent: 1
    gain: 0.7

  - name: wolves
    folder: wolves
    min_gap_seconds: 5
    max_gap_seconds: 35
    max_concurrent: 1
    gain: 0.7
```

### Artistic intention

- **Atmosphere** is the most active layer and may overlap with itself.
- **Bowed piano** provides longer haunting textures.
- **Freaky piano** appears as a more regular musical event.
- **Birds** establish the outdoor environment.
- **Wolves** are intentionally very frequent, creating a persistent unsettling presence.

The user explicitly wants the wolf howls to remain that frequent. They may adjust the frequency later, but the current 5–35 second wolf gap is intentional.

### Important folder name

The birds folder is named:

```text
audio/birds
```

not:

```text
audio/bird
```

Earlier documentation incorrectly used `bird`. The actual configuration uses `birds`.

---

## 6. Recommended architecture

Driftbox is a Python service with a local web configuration interface.

```text
Driftbox Python service
├── Configuration loader and validator
├── Audio scheduler
├── mpv process manager
├── FastAPI API
├── Minimal web UI
└── Local rotating logs
```

### Technology choices

| Component | Choice | Reason |
|---|---|---|
| Language | Python | Cross-platform, suitable for Raspberry Pi |
| Web framework | FastAPI | Simple API and static-file serving |
| Web server | Uvicorn | Runs FastAPI; no need for Apache or Nginx |
| Audio playback | mpv child processes | Reliable command-line playback; easy process supervision |
| Configuration | YAML | Human-readable and easy to edit |
| Validation | Pydantic | Validates configuration before playback |
| Logging | Python `RotatingFileHandler` | Prevents logs filling the SD card |
| Service startup | systemd | Robust boot and automatic restart |
| Discovery | Avahi/mDNS | Enables `driftbox.local` when network is available |

---

## 7. Project structure

```text
driftbox/
  pyproject.toml
  README.md
  .gitignore
  config/
    development.yaml
    wicked_woods_birds_wolves.yaml
  audio/
    bed/
    bowed/
    piano/
    birds/
    wolves/
  driftbox/
    __init__.py
    config.py
    logging_setup.py
    player.py
    scheduler.py
    service.py
    api.py
    main.py
  web/
    index.html
    app.js
    style.css
  systemd/
    driftbox.service
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Load, model, and validate YAML configuration |
| `logging_setup.py` | Configure console and rotating file logging |
| `player.py` | Start, stop, supervise, and inspect mpv processes |
| `scheduler.py` | Run single-loop or generative-layer scheduling |
| `service.py` | Start, stop, restart, and reconfigure the scheduler |
| `api.py` | FastAPI endpoints and static web UI |
| `main.py` | Command-line entry point and Uvicorn startup |

---

## 8. Important bug fixes

### Configuration file was ignored

The original `api.py` hard-coded:

```python
CONFIG_PATH = Path("config/development.yaml")
```

This meant that running:

```bash
python -m driftbox.main --config config/wicked_woods_birds_wolves.yaml
```

still loaded `development.yaml`.

The fix is to pass the selected configuration path through an environment variable.

In `main.py`:

```python
os.environ["DRIFTBOX_CONFIG"] = str(args.config)
```

In `api.py`:

```python
CONFIG_PATH = Path(
    os.getenv("DRIFTBOX_CONFIG", "config/development.yaml")
)
```

The working command is now:

```bash
python -m driftbox.main --config config/wicked_woods_birds_wolves.yaml
```

### WAV files were ignored

The original scheduler only searched for:

```python
path.glob("*.mp3")
```

So WAV wolf sounds were not played.

The scheduler now uses:

```python
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aiff",
}
```

And scans files with:

```python
files = sorted(
    file
    for file in path.iterdir()
    if file.is_file()
    and file.suffix.lower() in AUDIO_EXTENSIONS
)
```

`AUDIO_EXTENSIONS` must be defined at module level in `scheduler.py`, before the `Scheduler` class uses it.

### Duplicate playback

At one point, each sound appeared to play twice. The likely causes were:

- An older Driftbox or mpv process still running.
- The scheduler being started more than once.
- Uvicorn reload creating or leaving an additional process.

The fix was to:

- Stop all Driftbox and mpv processes.
- Start only one instance.
- Move scheduler startup and shutdown into FastAPI’s lifespan handler.
- Ensure `DriftboxService.start()` refuses to create a second scheduler.

The relevant `api.py` pattern is:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    service.start()
    yield
    service.stop()
```

---

## 9. PipeWire warning

The Pi log showed:

```text
pw.conf: can't load config client.conf: No such file or directory
```

This is a PipeWire client-configuration warning from mpv. It is generally harmless if audio is audible.

The user confirmed that Driftbox was playing on the Pi despite the warning.

The preferred Halloween solution is to force mpv to use ALSA directly.

In `driftbox/player.py`, `_base_command()` should include:

```python
"--ao=alsa",
```

For example:

```python
return [
    self.config.mpv_binary,
    "--no-video",
    "--really-quiet",
    "--no-terminal",
    "--ao=alsa",
]
```

This avoids mpv’s PipeWire client-config lookup. For a headless installation, the simpler audio path is:

```text
Driftbox → mpv → ALSA → PA
```

An alternative is to install PipeWire client libraries:

```bash
sudo apt install -y pipewire-audio-client-libraries
```

But direct ALSA is the preferred Halloween approach.

---

## 10. Current working state

As of 19 October 2026:

- Driftbox works on the Mac.
- Driftbox works on the Raspberry Pi.
- The Wicked Woods configuration plays correctly on the Pi.
- The user left it running overnight.
- It was still running the following morning.
- The wolf howls are intentionally frequent.
- The project has been pushed to GitHub.
- The README documents the Wicked Woods build and configuration.
- The current priority is deployment hardening and final installation testing.

### Completed

- [x] Project renamed from Ambirithm to Driftbox.
- [x] Rebuilt from scratch rather than reviving old code.
- [x] Mac development environment established.
- [x] Single-loop playback implemented.
- [x] Generative multi-layer playback implemented.
- [x] mpv process management implemented.
- [x] FastAPI web interface implemented.
- [x] Configuration loading and validation implemented.
- [x] WAV, FLAC, OGG, M4A, and AIFF support added.
- [x] Configuration path bug fixed.
- [x] Duplicate scheduler issue addressed.
- [x] Raspberry Pi OS Lite 64-bit installed.
- [x] mpv, Avahi, Python, and project dependencies installed.
- [x] Driftbox manually tested on Pi.
- [x] Wicked Woods configuration deployed to Pi.
- [x] PipeWire warning investigated.
- [x] Overnight soak test passed.
- [x] README updated for Wicked Woods 0.1.
- [x] Project pushed to GitHub.

### Still to do

- [ ] Verify another reboot with Wicked Woods configuration.
- [ ] Verify offline boot with Ethernet and Wi-Fi disconnected.
- [ ] Confirm browser Stop button works.
- [ ] Verify rotating logs do not fill the SD card.
- [ ] Add Wi-Fi service hotspot.
- [ ] Add pre-flight configuration and audio validation.
- [ ] Create deployment bundle with checksums and test report.
- [ ] Longer soak test before installation.
- [ ] Later: musical synchronisation.
- [ ] Later: sample-accurate mixer.
- [ ] Later: containerisation.

---

## 11. Web interface and API

The web UI is intentionally minimal.

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

The web UI must not be required for playback. If the web service fails, the core audio service should continue playing.

---

## 12. Raspberry Pi deployment

### Operating system

Use:

```text
Raspberry Pi OS Lite (64-bit), Bookworm
```

The Pi 3 has 1 GB RAM, so avoid the desktop image. The Pi 3’s Cortex-A53 CPU supports 64-bit AArch64.

After first boot:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y mpv avahi-daemon avahi-utils git python3-venv python3-pip
sudo systemctl enable --now avahi-daemon
```

Confirm architecture:

```bash
uname -m
```

Expected:

```text
aarch64
```

### systemd service

Create:

```bash
sudo nano /etc/systemd/system/driftbox.service
```

Use:

```ini
[Unit]
Description=Driftbox soundscape player
After=multi-user.target

[Service]
Type=simple
User=driftbox
WorkingDirectory=/home/driftbox/driftbox
ExecStart=/home/driftbox/driftbox/.venv/bin/python -m driftbox.main --config /home/driftbox/driftbox/config/wicked_woods_birds_wolves.yaml --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now driftbox
```

Check:

```bash
systemctl status driftbox --no-pager
journalctl -u driftbox -n 100 --no-pager
pgrep -fl mpv
```

### Service commands

```bash
# Start
sudo systemctl start driftbox

# Stop
sudo systemctl stop driftbox
pkill mpv

# Restart
sudo systemctl restart driftbox

# Status
systemctl status driftbox --no-pager

# Recent logs
journalctl -u driftbox -n 100 --no-pager

# Follow logs
journalctl -u driftbox -f
```

---

## 13. Offline-first design

Driftbox must boot and play without:

- Ethernet
- Wi-Fi
- Internet
- DNS
- A browser
- A cloud service

Network access is optional and used only for configuration, monitoring, and remote access.

When a network is available, the Pi can be reached as:

```text
http://driftbox.local:8000
```

For on-site monitoring without venue network infrastructure, the planned fallback is a Pi-generated Wi-Fi hotspot:

```text
SSID: driftbox-01
Password: spraoi-driftbox
Address: http://192.168.4.1
```

This has not yet been implemented.

---

## 14. Audio formats

Driftbox can play:

- MP3
- WAV
- FLAC
- OGG
- M4A
- AIFF

For version 0.1, MP3 and WAV are both acceptable.

For future musical synchronisation:

- Use WAV or FLAC for rhythmic and musical material.
- Use MP3 for long ambient beds and non-rhythmic textures.
- Stream long files rather than loading them fully into RAM.
- Use 48 kHz sample rate where possible.
- Avoid relying on MP3 for sample-accurate alignment.

A Raspberry Pi 3 has 1 GB RAM. WAV files are not inherently a RAM problem if the application streams them in small blocks rather than loading whole files into memory.

Approximate stereo file sizes at 48 kHz:

| Format | Approximate size per minute |
|---|---:|
| 16-bit WAV | About 11.5 MB |
| 24-bit WAV | About 17.3 MB |
| FLAC | Usually much smaller than WAV |
| MP3 | Usually a few MB, depending on bitrate |

---

## 15. Future musical synchronisation

A later version may allow musical pieces to play in time with one another.

mpv can start multiple files approximately together, but separate mpv processes do not provide a shared sample-accurate transport clock. It is suitable for ambient overlap, but not strict tempo-locked musical layering.

The likely future path is:

| Version | Playback approach | Synchronisation |
|---|---|---|
| 0.1 | Python scheduler plus mpv processes | None |
| 0.2 | Coordinated mpv starts | Loose synchronisation |
| 0.3 | Python `sounddevice` and `soundfile` mixer | Sample-accurate scheduling |
| 0.4 | Musical clock, BPM, bars, loop points | Tempo-aware entry and exit |
| 0.5 | Offline audio analysis | Tempo and beat detection |

The future mixer should use one continuous audio output stream, with each active voice contributing to a shared mix buffer. This allows entries to be scheduled on exact sample boundaries.

---

## 16. GitHub backup

The Driftbox source code should be backed up to GitHub.

The intended repository is:

https://github.com/roboconnor/driftbox

The `.gitignore` should be committed. It contains no secrets; it tells Git which files should not be tracked.

Recommended `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Logs
logs/
*.log

# macOS
.DS_Store

# Editors
.vscode/
.idea/

# Audio media
audio/**/*.mp3
audio/**/*.wav
audio/**/*.flac
audio/**/*.aiff
audio/**/*.m4a

# Local secrets or environment files
.env
*.local.yaml
```

Do not ignore:

- `README.md`
- `pyproject.toml`
- `driftbox/`
- `web/`
- `config/development.yaml`
- `systemd/driftbox.service`

Those are part of the project and should be version-controlled.

---

## 17. Deployment workflow

Use the Mac repository as the source of truth.

From the Mac, in the project root:

```bash
rsync -avz \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude 'logs/' \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  ./ driftbox@driftbox.local:~/driftbox/
```

Then SSH into the Pi:

```bash
ssh driftbox@driftbox.local
```

Restart Driftbox:

```bash
sudo systemctl restart driftbox
```

Check:

```bash
systemctl status driftbox --no-pager
journalctl -u driftbox -n 100 --no-pager
pgrep -fl mpv
```

---

## 18. Design principles

1. **Offline first.** Playback must never depend on a network.
2. **Local configuration.** All settings and audio must exist on the Pi.
3. **Simple over clever.** A reliable looping MP3 is better than an ambitious system that fails.
4. **Separate playback from UI.** The web interface must not be required for audio.
5. **Supervise processes.** Detect and recover from mpv failures.
6. **Log locally.** Make post-event diagnosis possible.
7. **Design for future musical sync.** Keep scheduler, player, and configuration modular.
8. **Avoid silent MP3s.** Use scheduler gaps instead.
9. **Test the real deployment condition.** Headless, offline, rebooted, and running for hours.
10. **Keep version 0.1 small.** Add sophistication only after the installation is safe.

---

## 19. Immediate next steps

1. Reboot the Pi and confirm Wicked Woods starts automatically.
2. Disconnect Ethernet and Wi-Fi, reboot, and confirm offline playback.
3. Verify the browser Stop control works.
4. Check rotating logs do not fill the SD card.
5. Leave Driftbox running for a longer soak test.
6. Prepare a deployment bundle with configuration, audio, checksums, and test report.
7. After the Spraoi installation, consider musical synchronisation and containerisation.

---

## 20. Key terminology

| Term | Meaning |
|---|---|
| **Driftbox** | Current name for the soundscape player |
| **Ambirithm** | Earlier name and predecessor project |
| **Spraoi** | Local arts group for whom the installation is being built |
| **Wicked Woods** | The version 0.1 soundscape and build |
| **Single-loop mode** | One audio file repeats continuously |
| **Generative layers** | Multiple folders of audio files scheduled with random gaps |
| **Layer** | An independent stream of related sounds |
| **Bed** | Continuous or frequently present background sound |
| **Atmosphere** | The `bed` layer in Wicked Woods |
| **Birds** | The `birds` layer in Wicked Woods |
| **Bowed piano** | The `bowed` layer in Wicked Woods |
| **Freaky piano** | The `piano` layer in Wicked Woods |
| **Wolves** | The `wolves` layer in Wicked Woods |
| **Pre-flight check** | Validation that configuration and audio are ready |
| **Deployment bundle** | Self-contained configuration, audio, checksums, and test report |
| **Service hotspot** | Pi-generated Wi-Fi network for on-site configuration |
