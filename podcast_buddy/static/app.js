const form = document.querySelector("#episodeForm");
const runStatus = document.querySelector("#runStatus");
const keyStatus = document.querySelector("#keyStatus");
const generateButton = document.querySelector("#generateButton");
const resultMeta = document.querySelector("#resultMeta");
const conversationOutput = document.querySelector("#conversationOutput");
const summaryOutput = document.querySelector("#summaryOutput");
const sourcesOutput = document.querySelector("#sourcesOutput");
const filesOutput = document.querySelector("#filesOutput");
const tabs = Array.from(document.querySelectorAll(".tab"));
const viewers = Array.from(document.querySelectorAll(".viewer"));

// Progress framework elements targeting
const progressContainer = document.querySelector("#progressContainer");
const progressBar = document.querySelector("#progressBar");
const progressText = document.querySelector("#progressText");
const progressPercentage = document.querySelector("#progressPercentage");

const fields = {
  topic: document.querySelector("#topic"),
  limit: document.querySelector("#limit"),
  gl: document.querySelector("#gl"),
  hl: document.querySelector("#hl"),
  maxSummaryWords: document.querySelector("#maxSummaryWords"),
  hostAName: document.querySelector("#hostAName"),
  hostBName: document.querySelector("#hostBName"),
  summaryModel: document.querySelector("#summaryModel"),
};

// ==========================================
// Canvas Multi-Line Audio Wave Loop Engine (image_438786.png)
// ==========================================
const canvas = document.getElementById("waveCanvas");
const ctx = canvas ? canvas.getContext("2d") : null;
const visualizerHeader = document.getElementById("visualizerHeader");

let phase = 0;
let targetAmplitude = 2; // Baseline flat line indicator
let currentAmplitude = 2;

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = canvas.offsetWidth * window.devicePixelRatio;
  canvas.height = canvas.offsetHeight * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
}
window.addEventListener('resize', resizeCanvas);
if (canvas) resizeCanvas();

function drawWave() {
  if (!canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Interpolation loop logic
  currentAmplitude += (targetAmplitude - currentAmplitude) * 0.1;
  phase += 0.05;

  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;
  const centerY = height / 2;

  // Exact 3 tracking layers simulation setup
  const waves = [
    { color: 'rgba(56, 189, 248, 0.45)', speed: 1.0, freq: 0.015, offset: 0 },
    { color: 'rgba(251, 191, 36, 0.4)', speed: 0.8, freq: 0.012, offset: Math.PI / 3 },
    { color: 'rgba(52, 211, 153, 0.35)', speed: 1.2, freq: 0.018, offset: Math.PI / 1.5 }
  ];

  waves.forEach(w => {
    ctx.beginPath();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = w.color;

    for (let x = 0; x < width; x++) {
      const angle = (x * w.freq) + (phase * w.speed) + w.offset;
      const y = centerY + Math.sin(angle) * currentAmplitude * Math.sin(x * Math.PI / width);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  });

  requestAnimationFrame(drawWave);
}
if (canvas) drawWave();

function setVisualizerState(state) {
  if (!visualizerHeader) return;
  if (state === 'active') {
    targetAmplitude = 14;
    visualizerHeader.textContent = "SIGNAL PROCESSING: ACTIVE";
    visualizerHeader.style.color = "#8b5cf6";
  } else if (state === 'listening') {
    targetAmplitude = 22;
    visualizerHeader.textContent = "LISTENING LIVE...";
    visualizerHeader.style.color = "#ef4444";
  } else {
    targetAmplitude = 2;
    visualizerHeader.textContent = "SIGNAL PROCESSING: IDLE";
    visualizerHeader.style.color = "#9ca3af";
  }
}

// ==========================================
// Native Tab Switcher Viewports Controller
// ==========================================
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    tabs.forEach((item) => {
      const active = item === tab;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    viewers.forEach((viewer) => {
      viewer.classList.toggle("hidden", viewer.dataset.view !== target);
    });
  });
});

// ==========================================
// Form Generation Request (EventStream Logic)
// ==========================================
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const topic = fields.topic.value.trim();
  if (!topic) return;

  generateButton.disabled = true;
  generateButton.textContent = "Generating...";
  runStatus.textContent = "Connecting stream pipeline...";
  setVisualizerState('active');

  if (progressContainer) progressContainer.style.display = "block";

  const queryParams = new URLSearchParams({
    topic,
    limit: fields.limit.value,
    gl: fields.gl.value.trim() || "us",
    hl: fields.hl.value.trim() || "en",
    maxSummaryWords: fields.maxSummaryWords.value,
    hostAName: fields.hostAName.value.trim() || "Aarav",
    hostBName: fields.hostBName.value.trim() || "Meera",
    summaryModel: fields.summaryModel.value.trim(),
    summarizer: document.querySelector('input[name="summarizer"]:checked').value,
  });

  const eventSource = new EventSource(`/api/episodes/stream?${queryParams.toString()}`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.status === "progress") {
      runStatus.textContent = data.message;
      if (progressText) progressText.textContent = data.message;
      if (progressPercentage) progressPercentage.textContent = `${data.percentage}%`;
      if (progressBar) progressBar.style.width = `${data.percentage}%`;
    }
    else if (data.status === "completed") {
      renderEpisode(data.payload);
      runStatus.textContent = "Ready";
      if (progressText) progressText.textContent = "Generation Complete!";
      if (progressBar) progressBar.style.width = "100%";
      if (progressPercentage) progressPercentage.textContent = "100%";

      eventSource.close();
      generateButton.disabled = false;
      generateButton.textContent = "Generate episode";
      setVisualizerState('idle');

      setTimeout(() => {
        if (progressContainer) progressContainer.style.display = "none";
      }, 3000);
    }
  };

  eventSource.onerror = () => {
    runStatus.textContent = "Stream decoupled unexpectedly.";
    generateButton.disabled = false;
    generateButton.textContent = "Generate episode";
    setVisualizerState('idle');
    eventSource.close();
  };
});

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    if (data.serpapiKeyConfigured) {
      keyStatus.textContent = "SerpAPI Key Configured";
      keyStatus.className = "status-pill ok";
    } else {
      keyStatus.textContent = "SerpAPI Key Missing";
      keyStatus.className = "status-pill warn";
    }
    if (data.defaultModel && fields.summaryModel) {
      fields.summaryModel.value = data.defaultModel;
    }
  } catch {
    keyStatus.textContent = "Server Offline";
    keyStatus.className = "status-pill warn";
  }
}

function renderEpisode(data) {
  conversationOutput.textContent = data.conversation || "";
  summaryOutput.textContent = data.summary || "";

  resultMeta.innerHTML = `
    <span>Summarizer: ${data.summarizer || "auto"}</span>
    <span>Model: ${data.model || "default"}</span>
  `;

  renderSources(data.sources || []);
  renderFiles(data.files || {});
}

function renderSources(sources) {
  sourcesOutput.innerHTML = "";
  if (!sources.length) {
    sourcesOutput.innerHTML = "<div style='padding:14px;'>No sources evaluated.</div>";
    return;
  }
  sources.forEach((source, idx) => {
    const row = document.createElement("div");
    row.className = "source-row";
    row.innerHTML = `
      <div class="source-meta">#${idx + 1}</div>
      <div>
        <strong>${source.title || "Untitled Document"}</strong>
        ${source.link ? `<a href="${source.link}" target="_blank">${source.link}</a>` : ""}
      </div>
      <div class="source-meta">${source.source || "Web Node"}</div>
    `;
    sourcesOutput.append(row);
  });
}

function renderFiles(files) {
  filesOutput.innerHTML = "";
  Object.entries(files).forEach(([label, path]) => {
    const wrap = document.createElement("div");
    wrap.innerHTML = `<dt>${label.toUpperCase()}</dt><dd>${path}</dd>`;
    filesOutput.append(wrap);
  });
}

// ==========================================
// Podcast Voice synthesis Engine (Player System)
// ==========================================
const playBtn = document.getElementById("playPodcast");
const pauseBtn = document.getElementById("pausePodcast");
const stopBtn = document.getElementById("stopPodcast");
const voiceStatus = document.getElementById("voiceStatus");
const micButton = document.getElementById("micButton");

let lines = [];
let currentLineIndex = 0;
let isPlaying = false;

function speakNext() {
  if (currentLineIndex >= lines.length) {
    isPlaying = false;
    if (voiceStatus) voiceStatus.textContent = "Ready";
    setVisualizerState('idle');
    return;
  }
  if (!isPlaying) return;

  const rawLine = lines[currentLineIndex].trim();
  currentLineIndex++;

  if (!rawLine) { speakNext(); return; }

  const voices = speechSynthesis.getVoices();
  const maleVoice = voices.find(v => v.name.toLowerCase().includes("david")) || voices.find(v => v.name.toLowerCase().includes("male")) || voices[0];
  const femaleVoice = voices.find(v => v.name.toLowerCase().includes("zira")) || voices.find(v => v.name.toLowerCase().includes("female")) || voices[0];

  const cleanLine = rawLine.replace(/^.*?:/, "").trim();
  const utterance = new SpeechSynthesisUtterance(cleanLine);

  const hostA = fields.hostAName.value || "Aarav";
  if (rawLine.toLowerCase().includes(hostA.toLowerCase())) {
    utterance.voice = maleVoice;
  } else {
    utterance.voice = femaleVoice;
  }

  utterance.onend = () => speakNext();
  utterance.onerror = () => speakNext();

  speechSynthesis.speak(utterance);
}

if (playBtn) {
  playBtn.addEventListener("click", () => {
    if (speechSynthesis.paused) {
      speechSynthesis.resume();
      if (voiceStatus) voiceStatus.textContent = "Playing";
      setVisualizerState('active');
      return;
    }

    const textContent = conversationOutput.textContent;
    if (!textContent.trim() || textContent.includes("Generate an episode to preview")) {
      alert("Please generate an episode script first.");
      return;
    }

    speechSynthesis.cancel();
    lines = textContent.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#") && !l.startsWith("Generated:"));
    currentLineIndex = 0;
    isPlaying = true;
    if (voiceStatus) voiceStatus.textContent = "Playing";
    setVisualizerState('active');
    speakNext();
  });
}

if (pauseBtn) {
  pauseBtn.addEventListener("click", () => {
    if (speechSynthesis.speaking && !speechSynthesis.paused) {
      speechSynthesis.pause();
      if (voiceStatus) voiceStatus.textContent = "Paused";
      setVisualizerState('idle');
    }
  });
}

if (stopBtn) {
  stopBtn.addEventListener("click", () => {
    isPlaying = false;
    currentLineIndex = 0;
    speechSynthesis.cancel();
    if (voiceStatus) voiceStatus.textContent = "Ready";
    setVisualizerState('idle');
  });
}

// ==========================================
// Speech Recognition Control (Doubt System Endpoint)
// ==========================================
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";

  if (micButton) {
    micButton.onclick = () => {
      if (speechSynthesis.speaking) {
        speechSynthesis.cancel();
      }
      isPlaying = false;
      if (voiceStatus) voiceStatus.textContent = "Listening...";
      setVisualizerState('listening');
      recognition.start();
    };
  }

  recognition.onend = () => {
    if (voiceStatus && voiceStatus.textContent === "Listening...") {
      voiceStatus.textContent = "Processing Doubt Response...";
      setVisualizerState('active');
    }
  };

  recognition.onresult = async (e) => {
    const speechResult = e.results[0][0].transcript.trim();
    runStatus.textContent = `Prompt: "${speechResult}"`;

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: speechResult }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Upstream query failure");

      runStatus.textContent = `Answer: ${data.answer}`;
      if (voiceStatus) voiceStatus.textContent = "Answering...";
      setVisualizerState('active');

      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(data.answer);
      utterance.onend = () => {
        setVisualizerState('idle');
        if (voiceStatus) voiceStatus.textContent = "Ready";
      };
      speechSynthesis.speak(utterance);

    } catch (error) {
      console.error(error);
      runStatus.textContent = "Error communicating with endpoint service.";
      setVisualizerState('idle');
    }
  };
}

loadStatus();