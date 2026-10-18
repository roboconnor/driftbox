# Driftbox — Project Briefing

**Date of briefing:** 16 October 2026  
**Purpose:** Restore full context for developing Driftbox, an offline-first, sample-based soundscape player for Raspberry Pi installations.

---

## 1. Project origin

Driftbox is the revived and renamed version of an earlier project called **Ambirithm**.

The original Ambirithm was created for sound design and music composition work with **Spraoi**, a local arts group in Waterford, Ireland. Spraoi uses Raspberry Pi 3 devices as playback computers for floats and art installations. These devices are useful because they are small, low-power, headless-capable, and can be connected directly to a PA system.

The original system evolved through several stages:

1. A Bash script that played one MP3 on repeat.
2. A Bash script that played overlapping MP3s from multiple folders, creating an evolving soundscape.
3. A Python version intended to be more robust, though it occasionally stopped playing, possibly because of a caching issue.

The original approach used silent MP3 files of varying lengths to introduce gaps and variation. The important quality was that the resulting soundscape changed continuously, but remained confined to a curated set of prerecorded sounds.

The old GitHub repository is:

https://github.com/roboconnor/ambirithm

The owner states that the repository is public, but automated access attempts failed. The repository contents have not yet been reviewed. The user is not attached to the old code and prefers to rebuild from scratch.

---

## 2. What Driftbox is

**Driftbox** is an offline-first, sample-based soundscape player.

It plays prerecorded audio files — primarily MP3s — in ways that create an evolving but controlled listening experience. It is not an audio synthesiser and does not generate sound algorithmically.

Its core principle is:

> Use a finite set of prerecorded sounds, but schedule them with variation so that the overall soundscape does not become a recognisable short loop.

Driftbox is intended for unattended installation playback, especially on Raspberry Pi hardware.

---

## 3. Immediate goal

The immediate goal is a **robust working version for Spraoi’s Halloween installation**, due by the end of the coming weekend.

The development period is approximately **3–4 days, part-time**. Therefore, the first version must be deliberately minimal and reliability-focused.

The working name is now **Driftbox**, not Ambirithm.

---

## 4. Core requirements

### Must have

- Entirely sample-based playback.
- No audio synthesis.
- Support prerecorded MP3 files.
- Run on Raspberry Pi, especially Raspberry Pi 3.
- Develop primarily on macOS.
- Deploy to Raspberry Pi once stable.
- Run headlessly at the installation.
- Work without a network or internet connection.
- Start automatically at boot.
- Continue playing for long periods without intervention.
- Be configurable through a local web interface.
- Support a single longer MP3 played on repeat.
- Support multiple generative layers using local folders of MP3s.
- Use local storage for configuration and audio.
- Log errors and playback activity locally.

### Deferred

The following are explicitly deferred beyond the Halloween version:

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

## 5. Playback modes

Driftbox 0.1 should support two modes.

### Single-loop mode

One specified MP3 file plays repeatedly.

This preserves the original, dependable Ambirithm behaviour and provides a reliable fallback for installation work.

Example configuration:

```yaml
mode: single_loop

single_loop:
  file: audio/main_bed.mp3
  gain: 0.8
```

Implementation approach:

```bash
mpv --no-video --loop-file=inf --really-quiet /path/to/file.mp3
```

The application should supervise the mpv process rather than simply launch it. It should record the process, detect unexpected exits, log them, and restart the process with a bounded retry policy.

### Generative layers mode

Several independent layers play sounds from configured local folders.

Each layer:

- Selects an MP3 at random from its folder.
- Plays it.
- Waits for a random interval between configured minimum and maximum gap values.
- Selects another file.
- Repeats indefinitely.

Layers may have:

- A folder of permitted MP3s.
- Minimum and maximum gap between selections.
- Maximum number of concurrent sounds.
- Gain level.
- Optional fade-in and fade-out durations.
- A human-readable name.

Example:

```yaml
mode: layers

layers:
  - name: bed
    folder: audio/bed
    min_gap_seconds: 2
    max_gap_seconds: 10
    max_concurrent: 1
    gain: 0.5

  - name: events
    folder: audio/events
    min_gap_seconds: 30
    max_gap_seconds: 180
    max_concurrent: 2
    gain: 0.75
```

Silence should be implemented as a scheduling property, not as silent MP3 files. Silent MP3s are no longer needed for the core design.

---

## 6. Recommended architecture

Driftbox should be a Python service with a local web configuration interface.

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
| Language | Python | Cross-platform, familiar, suitable for Raspberry Pi |
| Web framework | FastAPI | Simple API and static-file serving |
| Web server | Uvicorn | Runs FastAPI; no need for Apache or Nginx |
| Audio playback | mpv child processes | Reliable command-line MP3 playback; easy process supervision |
| Configuration | YAML | Human-readable and easy to edit |
| Validation | Pydantic | Validates configuration before playback |
| Logging | Python `RotatingFileHandler` | Prevents logs filling the SD card |
| Service startup | systemd | Robust boot and automatic restart |
| Discovery | Avahi/mDNS | Enables `driftbox.local` when network is available |

---

## 7. Development environment

Development happens primarily on the user’s Mac.

The same code should run locally on macOS and later on Raspberry Pi OS.

### Mac development

Use a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install mpv locally:

```bash
brew install mpv
```

Run Driftbox locally:

```bash
driftbox --config config/development.yaml --reload
```

Then open:

```text
http://127.0.0.1:8000
```

### Raspberry Pi deployment

For deployment, use Raspberry Pi OS Lite, headless setup, SSH enabled during imaging, and systemd services.

The production command should bind to all interfaces:

```bash
uvicorn driftbox.api:app --host 0.0.0.0 --port 80
```

Port 80 allows users to visit:

```text
http://driftbox.local
```

without specifying a port.

---

## 8. Project skeleton

The agreed initial project structure is:

```text
driftbox/
  pyproject.toml
  README.md
  .gitignore
  config/
    development.yaml
  audio/
    bed/
    events/
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

### Main modules

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

## 9. Configuration design

The configuration should distinguish between:

- `single_loop` mode
- `layers` mode

A looping MP3 may also be treated as one type of layer, allowing a music bed to loop underneath generative foreground sounds.

Example combined future configuration:

```yaml
soundscape: halloween_yard
audio_root: audio
mpv_binary: mpv

mode: layers

layers:
  - name: music_bed
    type: single_loop
    file: music/halloween_bed.mp3
    gain: 0.5
    fade_in_seconds: 5
    fade_out_seconds: 5

  - name: events
    type: generative
    folder: events
    min_gap_seconds: 30
    max_gap_seconds: 180
    max_concurrent: 2
    gain: 0.75
```

For version 0.1, it is acceptable to keep `single_loop` and `layers` as separate top-level modes.

---

## 10. Web interface

The web UI should be extremely simple for version 0.1.

It needs:

- Current status.
- Active mpv processes.
- Current mode.
- Configuration form.
- Save and apply action.
- Restart playback action.
- Error display.

Useful API endpoints:

```text
GET  /api/status
GET  /api/config
POST /api/config
POST /api/restart
```

The UI should not be required for playback. If the web service fails, the core audio service should continue playing.

---

## 11. Raspberry Pi deployment

### Installation mode

The default mode must be offline installation playback.

At boot, Driftbox should:

1. Load local configuration.
2. Validate audio files.
3. Start mpv playback.
4. Begin the scheduler.
5. Write logs locally.
6. Optionally start network services.

It must not require:

- Ethernet.
- Wi-Fi.
- Internet.
- DNS.
- A browser.
- A connected phone or laptop.
- A cloud service.

### Wired network discovery

When Ethernet is available, the Pi should advertise itself as:

```text
http://driftbox.local
```

This requires:

- Hostname set to `driftbox`.
- Avahi daemon installed and enabled.
- Uvicorn listening on `0.0.0.0:80`.

Setup commands:

```bash
sudo apt update
sudo apt install avahi-daemon avahi-utils
sudo systemctl enable --now avahi-daemon
sudo hostnamectl set-hostname driftbox
```

Add to `/etc/hosts`:

```text
127.0.1.1       driftbox
```

### Offline service access

For on-site monitoring without venue network infrastructure, use one of these fallbacks:

#### Wi-Fi access point fallback

The Pi can broadcast its own Wi-Fi network:

```text
SSID: driftbox-01
Password: spraoi-driftbox
Address: http://192.168.4.1
```

A phone or laptop connects directly to that network to access the Driftbox web UI.

#### USB service mode

USB Ethernet gadget mode can provide a direct Pi-to-laptop network connection over USB. This may be useful for diagnosis, but Wi-Fi access point mode is likely the more practical default for Spraoi.

---

## 12. Reliability requirements

For an installation that may run for days:

- Run the core service under systemd.
- Use `Restart=always` and a sensible `RestartSec`.
- Keep audio files local.
- Avoid dependence on network shares.
- Validate all MP3 paths at startup.
- Detect and restart failed mpv processes.
- Use rotating logs.
- Monitor disk space.
- Test an offline reboot before deployment.
- Prefer wired Ethernet during setup, but do not require it during playback.
- Use a reserved IP address as a fallback if possible.

Example systemd service:

```ini
[Unit]
Description=Driftbox soundscape player
After=multi-user.target

[Service]
Type=simple
User=driftbox
WorkingDirectory=/opt/driftbox
ExecStart=/opt/driftbox/.venv/bin/python -m driftbox.main --config /opt/driftbox/config/deployment.yaml --host 0.0.0.0 --port 80
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 13. Audio format considerations

For version 0.1, MP3 is acceptable for all material.

For future musical synchronisation:

- Use WAV or FLAC for rhythmic and musical material.
- Use MP3 for long ambient beds and non-rhythmic textures.
- Stream long files rather than loading them fully into RAM.
- Use 48 kHz sample rate where possible.
- Avoid relying on MP3 for sample-accurate alignment because decoder delay and encoder padding can introduce small offsets.

A Raspberry Pi 3 has 1 GB RAM. WAV files are not inherently a RAM problem if the application streams them in small blocks rather than loading whole files into memory.

Approximate stereo file sizes at 48 kHz:

| Format | Approximate size per minute |
|---|---:|
| 16-bit WAV | About 11.5 MB |
| 24-bit WAV | About 17.3 MB |
| FLAC | Usually substantially smaller than WAV |
| MP3 | Usually a few MB, depending on bitrate |

---

## 14. Future musical synchronisation

A later version may allow musical pieces to play in time with one another.

mpv can start multiple files approximately together, but separate mpv processes do not provide a shared sample-accurate transport clock. It is therefore suitable for ambient overlap, but not ideal for strict tempo-locked musical layering.

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

## 15. Halloween delivery plan

Because the deadline is only a few days away, use this compressed plan.

### Day 1 — Core playback

Goal: reliable single-loop playback.

- Create project and virtual environment.
- Implement YAML configuration loading.
- Implement mpv single-loop playback.
- Add process supervision and restart.
- Test locally on Mac.

Target:

```bash
python -m driftbox
```

plays a configured MP3 repeatedly.

### Day 2 — Generative layers

Goal: evolving multi-layer playback.

- Implement layer scheduler.
- Select random MP3s from folders.
- Apply random gaps.
- Enforce per-layer concurrency.
- Add status information.
- Test with several short MP3s.

Target: multiple layers play with changing files and gaps.

### Day 3 — Web UI and Pi deployment

Goal: browser configuration and headless Pi operation.

- Add FastAPI endpoints.
- Add minimal single-page web UI.
- Deploy to Pi.
- Install mpv, Avahi, and systemd service.
- Test reboot and `driftbox.local`.

Target: Pi boots headless and plays; web UI is reachable on wired network.

### Day 4 — Hardening

Goal: deployment confidence.

- Disconnect network and test offline boot.
- Verify automatic restart.
- Add rotating logs.
- Add configuration and audio pre-flight checks.
- Soak-test for several hours.
- Prepare final deployment bundle.

Target: a Pi that can be installed and left running.

---

## 16. Deployment bundle

Each deployed Pi should have a self-contained local bundle:

```text
driftbox-deployment/
  config/deployment.yaml
  audio/
  checksums.sha256
  version.txt
  deployment-report.json
```

The deployment report should record:

- Pi hostname or serial number.
- Soundscape name and version.
- Audio file count and total duration.
- Configuration validation result.
- Offline boot test result.
- Soak-test duration.
- Date and operator.

---

## 17. Design principles

1. **Offline first.** Playback must never depend on a network.
2. **Local configuration.** All settings and audio must exist on the Pi.
3. **Simple over clever.** A reliable looping MP3 is better than an ambitious system that fails.
4. **Separate playback from UI.** The web interface must not be required for audio.
5. **Supervise processes.** Detect and recover from mpv failures.
6. **Log locally.** Make post-event diagnosis possible.
7. **Design for future musical sync.** Keep scheduler, player, and configuration modular.
8. **Avoid silent MP3s.** Use scheduler gaps instead.
9. **Test the real deployment condition.** Headless, offline, rebooted, and running for hours.
10. **Keep the Halloween version small.** Add sophistication only after the installation is safe.

---

## 18. Current status

As of 16 October 2026:

- The project has been renamed from Ambirithm to Driftbox.
- The user intends to rebuild from scratch rather than revive the old code.
- A complete project skeleton has been provided for local Mac development.
- The skeleton includes configuration, mpv playback, scheduler, FastAPI API, minimal web UI, and systemd deployment structure.
- The immediate priority is a reliable Halloween-ready version.
- Containerisation is a later goal.
- Musical synchronisation is a later goal.

---

## 19. Next actions

1. Create the skeleton locally on the Mac.
2. Add a few test MP3s to `audio/bed/` and `audio/events/`.
3. Run Driftbox in `single_loop` mode.
4. Confirm looping works reliably.
5. Switch to `layers` mode.
6. Confirm random selection and gaps work.
7. Deploy the simplest working version to a Raspberry Pi.
8. Test headless offline boot.
9. Add systemd, logging, and restart behaviour.
10. Only then refine the web UI or add more scheduler features.

---

## 20. Key terminology

| Term | Meaning |
|---|---|
| **Driftbox** | The current name for the soundscape player |
| **Ambirithm** | The earlier name and predecessor project |
| **Spraoi** | The local arts group for whom the installation is being built |
| **Single-loop mode** | One MP3 repeats continuously |
| **Generative layers** | Multiple folders of MP3s scheduled with random gaps |
| **Layer** | An independent stream of related sounds |
| **Bed** | A continuous or frequently present background sound |
| **Event** | An occasional foreground sound |
| **Pre-flight check** | Validation that configuration and audio are ready |
| **Deployment bundle** | Self-contained configuration, audio, checksums, and test report |
| **Service hotspot** | Pi-generated Wi-Fi network for on-site configuration |
