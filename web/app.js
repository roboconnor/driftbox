const statusOutput = document.getElementById("status-output");
const form = document.getElementById("config-form");

async function refreshStatus() {
  const response = await fetch("/api/status");
  const status = await response.json();
  statusOutput.textContent = JSON.stringify(status, null, 2);
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();

  form.soundscape.value = config.soundscape;
  form.mode.value = config.mode;

  form.single_loop_file.value = config.single_loop?.file ?? "";
  form.single_loop_gain.value = config.single_loop?.gain ?? 0.8;

  const layer = config.layers?.[0];

  form.layer_folder.value = layer?.folder ?? "";
  form.layer_min_gap.value = layer?.min_gap_seconds ?? 5;
  form.layer_max_gap.value = layer?.max_gap_seconds ?? 30;
  form.layer_gain.value = layer?.gain ?? 0.8;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const mode = form.mode.value;

  const config = {
    soundscape: form.soundscape.value,
    audio_root: "audio",
    mpv_binary: "mpv",
    mode,
    single_loop: {
      file: form.single_loop_file.value,
      gain: Number(form.single_loop_gain.value),
    },
    layers: [
      {
        name: "layer_1",
        folder: form.layer_folder.value,
        min_gap_seconds: Number(form.layer_min_gap.value),
        max_gap_seconds: Number(form.layer_max_gap.value),
        max_concurrent: 1,
        gain: Number(form.layer_gain.value),
      },
    ],
  };

  const response = await fetch("/api/config", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json();
    alert(JSON.stringify(error, null, 2));
    return;
  }

  await refreshStatus();
});

document.getElementById("refresh").addEventListener("click", refreshStatus);

document.getElementById("restart").addEventListener("click", async () => {
  await fetch("/api/restart", {method: "POST"});
  await refreshStatus();
});

refreshStatus();
loadConfig();