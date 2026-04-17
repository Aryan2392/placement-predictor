/*
═══════════════════════════════════════════════════════════════════════════════
script.js  –  Smart Placement Intelligence System  (v2)
───────────────────────────────────────────────────────────────────────────────
SUBJECT : WT (DOM Manipulation, AJAX/fetch, JSON, Form Handling, Event Listeners)
          DSBDA (Chart.js Data Visualisation)

SECTIONS:
  1.  Tab switching
  2.  Slider sync (range ↔ value display)
  3.  Prediction submit → REST API call
  4.  Show prediction result (banner, bars, tags, charts)
  5.  Analytics stats loader
  6.  History loader (AJAX — fixes "history not showing" bug)
  7.  Resume upload & result display
  8.  Chatbot send / receive
  9.  Chart.js instances & helpers
  10. On-page-load init
═══════════════════════════════════════════════════════════════════════════════
*/

"use strict";

// ─── Chart instances (stored globally so we can destroy before redrawing) ────
let barChartInst, radarChartInst, pieChartInst, avgChartInst;

// ════════════════════════════════════════════════════════════════════════════
// 1. TAB SWITCHING
// ════════════════════════════════════════════════════════════════════════════

/**
 * switchTab(tabId, btn)
 * Hides all tab-content divs, shows the one matching tabId.
 * Updates active class on both desktop nav-tabs and mobile m-tabs.
 * When analytics tab opens → loads fresh stats.
 * When history tab opens   → loads fresh history.
 */
function switchTab(tabId, btn) {
  // Hide all tabs
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  document.getElementById("tab-" + tabId).classList.add("active");

  // Update nav tab buttons (desktop)
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".m-tab").forEach(t => t.classList.remove("active"));

  // Mark this button active
  if (btn) {
    btn.classList.add("active");
    // Also sync the matching mobile tab (same index position)
    const allNavTabs  = [...document.querySelectorAll(".nav-tab")];
    const allMobTabs  = [...document.querySelectorAll(".m-tab")];
    const idx = allNavTabs.indexOf(btn);
    if (idx >= 0 && allMobTabs[idx]) allMobTabs[idx].classList.add("active");
  }

  if (tabId === "analytics") loadStats();
  if (tabId === "history")   loadHistory();
}


// ════════════════════════════════════════════════════════════════════════════
// 2. SLIDER ↔ VALUE SYNC
// ════════════════════════════════════════════════════════════════════════════

/**
 * syncVal(id)
 * Called oninput on each range slider.
 * Updates the displayed value span and also updates the gradient fill on slider.
 */
function syncVal(id) {
  const slider = document.getElementById(id);
  if (!slider) return;

  const val  = parseFloat(slider.value);
  const min  = parseFloat(slider.min);
  const max  = parseFloat(slider.max);
  const pct  = ((val - min) / (max - min)) * 100;

  // Update displayed number
  const display = document.getElementById("v_" + id);
  if (display) display.textContent = val;

  // Update CSS gradient so filled portion shows purple
  slider.style.setProperty("--pct", pct + "%");
  slider.style.background = `linear-gradient(to right, var(--primary) 0%, var(--primary) ${pct}%, var(--border) ${pct}%)`;
}

// Initialise all sliders on page load
function initSliders() {
  ["cgpa","internships","projects","aptitude","communication"].forEach(syncVal);
}


// ════════════════════════════════════════════════════════════════════════════
// 3. PREDICTION SUBMIT
// ════════════════════════════════════════════════════════════════════════════

/**
 * submitPrediction()
 * 1. Reads slider values
 * 2. Builds FormData
 * 3. POST to /predict (REST API call — WT concept)
 * 4. Parses JSON response
 * 5. Calls showResult() to render everything
 */
async function submitPrediction() {
  const btn     = document.getElementById("predictBtn");
  const btnText = document.getElementById("predictBtnText");

  // Read values
  const cgpa          = document.getElementById("cgpa").value;
  const internships   = document.getElementById("internships").value;
  const projects      = document.getElementById("projects").value;
  const aptitude      = document.getElementById("aptitude").value;
  const communication = document.getElementById("communication").value;

  // Loading state
  btn.disabled        = true;
  btnText.textContent = "⏳ Predicting…";

  const fd = new FormData();
  fd.append("cgpa", cgpa);
  fd.append("internships", internships);
  fd.append("projects", projects);
  fd.append("aptitude", aptitude);
  fd.append("communication", communication);

  try {
    const res  = await fetch("/predict", { method: "POST", body: fd });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
    } else {
      showResult(data);
    }
  } catch (err) {
    alert("Network error. Make sure Flask server is running.");
    console.error(err);
  } finally {
    btn.disabled        = false;
    btnText.textContent = "🔮 Predict My Placement";
  }
}


// ════════════════════════════════════════════════════════════════════════════
// 4. SHOW PREDICTION RESULT
// ════════════════════════════════════════════════════════════════════════════

function showResult(data) {
  const placed = data.result === "Placed";

  // Hide default state, show result block
  document.getElementById("defaultState").style.display  = "none";
  const block = document.getElementById("resultBlock");
  block.classList.remove("hidden");

  // ── Banner ─────────────────────────────────────────────────────────────
  const banner = document.getElementById("resultBanner");
  banner.className = "result-banner " + (placed ? "banner-placed" : "banner-not-placed");
  document.getElementById("resultEmoji").textContent = placed ? "🎉" : "😟";
  document.getElementById("resultText").textContent  = data.result;
  document.getElementById("roleText").textContent    = "Recommended Role: " + data.role;
  document.getElementById("confBadge").textContent   = data.confidence + "% sure";

  // ── Probability bars ───────────────────────────────────────────────────
  setTimeout(() => {
    document.getElementById("placedBar").style.width = data.placed_prob + "%";
    document.getElementById("notBar").style.width    = data.not_placed_prob + "%";
  }, 100);
  document.getElementById("placedPct").textContent = data.placed_prob + "%";
  document.getElementById("notPct").textContent    = data.not_placed_prob + "%";

  // ── Skill Gap ──────────────────────────────────────────────────────────
  const gapSection = document.getElementById("skillGapSection");
  const gapContent = document.getElementById("skillGapContent");
  if (data.skill_gap_list && data.skill_gap_list.length > 0) {
    gapContent.innerHTML = data.skill_gap_list
      .map(g => `<span class="tag-gap">⚠ ${g}</span>`).join("") +
      `<span class="tag-ok" style="margin-left:8px">✅ ${5 - data.skill_gap_list.length} areas strong</span>`;
  } else {
    gapContent.innerHTML = '<span class="tag-ok">✅ No major skill gaps found! Excellent profile.</span>';
  }

  // ── Suggestions ────────────────────────────────────────────────────────
  const sugContent = document.getElementById("suggestionsContent");
  if (data.suggestions_list) {
    sugContent.innerHTML = data.suggestions_list.map(s =>
      `<div class="suggestion-item"><span class="sug-dot">▸</span><span>${s}</span></div>`
    ).join("");
  }

  // ── Draw inline charts ─────────────────────────────────────────────────
  drawBarChart(data.input);
  drawRadarChart(data.input);
}


// ════════════════════════════════════════════════════════════════════════════
// 5. ANALYTICS STATS
// ════════════════════════════════════════════════════════════════════════════

/**
 * loadStats()
 * GET /api/stats → JSON → render stat cards + pie + avg charts
 * DSBDA concept: aggregate queries visualised with Chart.js
 */
async function loadStats() {
  try {
    const res  = await fetch("/api/stats");
    const data = await res.json();
    if (data.error) return;

    const total      = data.placed + data.not_placed;
    const placedPct  = total > 0 ? Math.round((data.placed / total) * 100) : 0;

    document.getElementById("statsGrid").innerHTML = `
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-val">${total}</div>
        <div class="stat-lbl">Total Predictions</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-val" style="color:var(--success)">${data.placed}</div>
        <div class="stat-lbl">Placed</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-val" style="color:var(--danger)">${data.not_placed}</div>
        <div class="stat-lbl">Not Placed</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-val" style="color:var(--primary)">${placedPct}%</div>
        <div class="stat-lbl">Success Rate</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🎓</div>
        <div class="stat-val">${data.avg_cgpa}</div>
        <div class="stat-lbl">Avg CGPA</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-val">${data.total_users}</div>
        <div class="stat-lbl">Total Users</div>
      </div>
    `;

    // Pie chart
    if (pieChartInst) pieChartInst.destroy();
    pieChartInst = new Chart(document.getElementById("pieChart"), {
      type: "doughnut",
      data: {
        labels: ["Placed", "Not Placed"],
        datasets: [{
          data: [data.placed, data.not_placed],
          backgroundColor: ["#1d9e75", "#e24b4a"],
          borderWidth: 3, borderColor: "#fff",
          hoverOffset: 6
        }]
      },
      options: {
        cutout: "65%",
        plugins: {
          legend: { position: "bottom" },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} (${Math.round(ctx.parsed / (total||1) * 100)}%)` } }
        }
      }
    });

    // Avg scores bar
    if (avgChartInst) avgChartInst.destroy();
    avgChartInst = new Chart(document.getElementById("avgChart"), {
      type: "bar",
      data: {
        labels: ["Avg CGPA ×10", "Avg Aptitude", "Avg Communication", "Avg Confidence"],
        datasets: [{
          label: "Average Score (out of 100)",
          data: [data.avg_cgpa * 10, data.avg_aptitude, data.avg_comm, data.avg_confidence],
          backgroundColor: ["#6c63ff","#1d9e75","#0ea5e9","#f59e0b"],
          borderRadius: 8, borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, max: 100 } }
      }
    });

  } catch (err) { console.error("Stats error:", err); }
}


// ════════════════════════════════════════════════════════════════════════════
// 6. HISTORY LOADER  (FIX for "history not showing" bug)
// ════════════════════════════════════════════════════════════════════════════

/**
 * loadHistory()
 * GET /api/history → JSON array of predictions → build HTML table
 * This is AJAX-driven (not server-side Jinja template), so it:
 *   - Always loads fresh data
 *   - Works after new predictions without page reload
 *   - Handles empty state gracefully
 */
async function loadHistory() {
  const container = document.getElementById("historyContainer");
  container.innerHTML = '<div class="loading-msg">⏳ Loading your predictions…</div>';

  try {
    const res  = await fetch("/api/history");
    const rows = await res.json();

    if (rows.error) {
      container.innerHTML = `<div class="loading-msg">Error: ${rows.error}</div>`;
      return;
    }

    if (!rows.length) {
      container.innerHTML = `
        <div class="history-card">
          <div class="loading-msg">
            🎯 No predictions yet!<br>
            <small style="color:var(--text-light)">Go to the Predict tab and make your first prediction.</small>
          </div>
        </div>`;
      return;
    }

    const tableRows = rows.map(r => `
      <tr>
        <td class="td-num">${r.cgpa}</td>
        <td class="td-num">${r.internships}</td>
        <td class="td-num">${r.projects}</td>
        <td class="td-num">${r.aptitude}</td>
        <td class="td-num">${r.communication}</td>
        <td>
          <span class="badge ${r.result === 'Placed' ? 'badge-placed' : 'badge-not'}">
            ${r.result === "Placed" ? "✅" : "❌"} ${r.result}
          </span>
          <br>
          <small style="color:var(--text-light)">${r.confidence}% conf.</small>
        </td>
        <td><span class="badge badge-role">${r.role_rec || "—"}</span></td>
        <td class="td-sugg">${(r.suggestion || "").split("|")[0]}</td>
        <td class="td-date">${r.created_at}</td>
      </tr>`
    ).join("");

    container.innerHTML = `
      <div class="history-card">
        <h3 style="margin-bottom:1rem">🕐 Last ${rows.length} Predictions</h3>
        <div class="table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>CGPA</th><th>Int.</th><th>Proj.</th>
                <th>Apt.</th><th>Comm.</th><th>Result</th>
                <th>Recommended Role</th><th>Top Suggestion</th><th>Date</th>
              </tr>
            </thead>
            <tbody>${tableRows}</tbody>
          </table>
        </div>
      </div>`;

  } catch (err) {
    container.innerHTML = `<div class="loading-msg">❌ Failed to load. Check server is running.</div>`;
    console.error(err);
  }
}


// ════════════════════════════════════════════════════════════════════════════
// 7. RESUME UPLOAD & RESULT
// ════════════════════════════════════════════════════════════════════════════

function onFileSelect(input) {
  const file = input.files[0];
  if (!file) return;

  const info    = document.getElementById("fileInfo");
  const btn     = document.getElementById("analyzeBtn");
  const zone    = document.getElementById("uploadZone");

  info.textContent = `📄 Selected: ${file.name}  (${(file.size/1024).toFixed(1)} KB)`;
  info.classList.remove("hidden");
  btn.disabled     = false;
  zone.querySelector(".uz-title").textContent = file.name;

  // Drag-drop visual feedback
  document.getElementById("uploadZone").querySelector(".uz-sub").textContent = "File ready — click Analyze";
}

async function uploadResume() {
  const fileInput = document.getElementById("resumeFile");
  const btn       = document.getElementById("analyzeBtn");

  if (!fileInput.files[0]) {
    alert("Please select a .txt file first.");
    return;
  }

  btn.disabled          = true;
  btn.querySelector("span").textContent = "⏳ Analyzing…";

  const fd = new FormData();
  fd.append("resume", fileInput.files[0]);

  try {
    const res  = await fetch("/resume", { method: "POST", body: fd });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
    } else {
      showResumeResult(data);
    }
  } catch (err) {
    alert("Upload failed. Check server.");
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.querySelector("span").textContent = "🔍 Analyze Resume";
  }
}

function showResumeResult(data) {
  const panel = document.getElementById("resumeResultPanel");

  const gradeColor = {
    "Excellent": "var(--success)", "Good": "#0ea5e9",
    "Average": "var(--warn)", "Needs Work": "var(--danger)"
  };
  const color = gradeColor[data.grade] || "var(--primary)";

  // Category breakdown rows
  const catRows = Object.entries(data.category_scores || {}).map(([cat, info]) =>
    `<div class="cat-row">
       <div>
         <div class="cat-name">${cat}</div>
         <div class="cat-skills">${info.found.length ? info.found.slice(0,4).join(", ") + (info.found.length > 4 ? "…" : "") : "None found"}</div>
       </div>
       <div class="cat-count">${info.count} / ${info.total}</div>
     </div>`
  ).join("");

  // Section checks
  const checks = Object.entries(data.sections_found || {}).map(([sec, found]) =>
    `<span class="sc-item ${found ? 'sc-yes' : 'sc-no'}">${found ? "✅" : "❌"} ${sec}</span>`
  ).join("");

  // Suggestions
  const suggHtml = (data.suggestions || []).map(s =>
    `<div class="suggestion-item"><span class="sug-dot">▸</span><span>${s}</span></div>`
  ).join("");

  panel.innerHTML = `
    <div class="resume-score-ring">
      <div class="score-circle" style="border-color:${color}">
        <span class="score-num" style="color:${color}">${data.score}</span>
        <span class="score-total">/100</span>
      </div>
      <div class="score-grade" style="color:${color}">${data.grade}</div>
    </div>

    <div class="info-section">
      <h4>📋 Sections Detected</h4>
      <div class="section-check">${checks}</div>
    </div>

    <div class="info-section">
      <h4>💻 Skills by Category (${data.skill_count} found)</h4>
      ${catRows}
    </div>

    <div class="info-section">
      <h4>💡 Suggestions to Improve</h4>
      ${suggHtml}
    </div>
  `;
}

// Drag-and-drop support
function initDragDrop() {
  const zone = document.getElementById("uploadZone");
  if (!zone) return;
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const dt = e.dataTransfer;
    if (dt.files.length) {
      document.getElementById("resumeFile").files = dt.files;
      onFileSelect(document.getElementById("resumeFile"));
    }
  });
}


// ════════════════════════════════════════════════════════════════════════════
// 8. CHATBOT
// ════════════════════════════════════════════════════════════════════════════

/**
 * sendMessage()  &  sendQuick(text)
 * POST /chat with JSON body {message: "..."}
 * Adds user bubble, typing indicator, then bot response to chat window.
 * Saves to DB via Flask route (WT + DSBDA).
 */
async function sendMessage() {
  const input = document.getElementById("chatInput");
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = "";
  appendMsg("user", msg);
  const typingId = appendTyping();

  try {
    const res  = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    removeTyping(typingId);
    appendMsg("bot", data.response || "Sorry, something went wrong.");
  } catch (err) {
    removeTyping(typingId);
    appendMsg("bot", "❌ Could not connect to server. Check Flask is running.");
    console.error(err);
  }
}

function sendQuick(text) {
  document.getElementById("chatInput").value = text;
  sendMessage();
}

function appendMsg(role, text) {
  const box = document.getElementById("chatMessages");
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const div = document.createElement("div");
  div.className = "chat-msg " + role;
  div.innerHTML = `
    <div class="msg-bubble">${text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")}</div>
    <div class="msg-time">${now}</div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendTyping() {
  const box = document.getElementById("chatMessages");
  const id  = "typing_" + Date.now();
  const div = document.createElement("div");
  div.className = "chat-msg bot typing-indicator";
  div.id = id;
  div.innerHTML = `<div class="msg-bubble"><div class="dot-anim"><span></span><span></span><span></span></div></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}


// ════════════════════════════════════════════════════════════════════════════
// 9. CHART HELPERS
// ════════════════════════════════════════════════════════════════════════════

function drawBarChart(inp) {
  if (barChartInst) barChartInst.destroy();
  barChartInst = new Chart(document.getElementById("barChart"), {
    type: "bar",
    data: {
      labels: ["CGPA (×10)", "Aptitude", "Communication"],
      datasets: [
        {
          label: "Your Score",
          data: [inp.cgpa * 10, inp.aptitude, inp.communication],
          backgroundColor: ["#6c63ff", "#1d9e75", "#0ea5e9"],
          borderRadius: 6, borderSkipped: false
        },
        {
          label: "Benchmark",
          data: [75, 70, 70],
          backgroundColor: ["rgba(108,99,255,0.18)", "rgba(29,158,117,0.18)", "rgba(14,165,233,0.18)"],
          borderRadius: 6, borderSkipped: false
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "top", labels: { boxWidth: 10, font: { size: 10 } } } },
      scales: { y: { beginAtZero: true, max: 100, ticks: { font: { size: 10 } } },
                x: { ticks: { font: { size: 10 } } } }
    }
  });
}

function drawRadarChart(inp) {
  if (radarChartInst) radarChartInst.destroy();
  radarChartInst = new Chart(document.getElementById("radarChart"), {
    type: "radar",
    data: {
      labels: ["CGPA", "Aptitude", "Communication", "Internships", "Projects"],
      datasets: [{
        label: "Your Profile",
        data: [
          inp.cgpa * 10,
          inp.aptitude,
          inp.communication,
          Math.min(inp.internships * 20, 100),
          Math.min(inp.projects * 15, 100)
        ],
        fill: true,
        backgroundColor: "rgba(108,99,255,0.15)",
        borderColor: "#6c63ff",
        pointBackgroundColor: "#6c63ff",
        pointRadius: 4
      }]
    },
    options: {
      scales: {
        r: {
          min: 0, max: 100,
          ticks: { stepSize: 25, font: { size: 9 } },
          pointLabels: { font: { size: 10 } }
        }
      },
      plugins: { legend: { display: false } }
    }
  });
}


// ════════════════════════════════════════════════════════════════════════════
// 10. INIT ON PAGE LOAD
// ════════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  initSliders();
  initDragDrop();

  // Enter key on chat input
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  }

  // Initial pie chart placeholder on analytics tab so it renders on first open
  const pieCanvas = document.getElementById("pieChart");
  if (pieCanvas) {
    pieChartInst = new Chart(pieCanvas, {
      type: "doughnut",
      data: {
        labels: ["Placed", "Not Placed"],
        datasets: [{ data: [1, 1], backgroundColor: ["#1d9e75","#e24b4a"], borderWidth: 2 }]
      },
      options: { cutout: "65%", plugins: { legend: { position: "bottom" } } }
    });
  }
});