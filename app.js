(() => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const forgeBar = document.getElementById("forge-bar");
  const forgeFill = document.getElementById("forge-bar-fill");
  const forgeStatus = document.getElementById("forge-status");
  const uploadError = document.getElementById("upload-error");

  const hero = document.getElementById("hero");
  const dashboard = document.getElementById("dashboard");
  const datasetName = document.getElementById("dataset-name");
  const statGrid = document.getElementById("stat-grid");
  const insightsList = document.getElementById("insights-list");
  const aiSummaryEl = document.getElementById("ai-summary");
  const columnsTableBody = document.querySelector("#columns-table tbody");
  const chartsGrid = document.getElementById("charts-grid");
  const newUploadBtn = document.getElementById("new-upload-btn");
  const buildBtn = document.getElementById("build-notebook-btn");
  const downloadBtn = document.getElementById("download-btn");

  let currentSessionId = null;

  // ---------- dropzone interactions ----------
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
  });
  ["dragenter", "dragover"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
  );
  ["dragleave", "drop"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag-over"); })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  function showError(msg) {
    uploadError.textContent = msg;
    uploadError.hidden = false;
  }
  function clearError() { uploadError.hidden = true; }

  function setForgeProgress(pct, label, hot = false) {
    forgeBar.hidden = false;
    forgeFill.style.width = `${pct}%`;
    forgeStatus.textContent = label;
    forgeFill.classList.toggle("hot", hot);
  }

  async function handleFile(file) {
    clearError();
    setForgeProgress(12, `Reading ${file.name}…`);

    const formData = new FormData();
    formData.append("file", file);

    try {
      setForgeProgress(30, "Uploading…");
      const uploadRes = await fetch("/api/upload", { method: "POST", body: formData });
      const uploadData = await uploadRes.json();
      if (!uploadRes.ok) throw new Error(uploadData.detail || "Upload failed.");

      currentSessionId = uploadData.session_id;
      setForgeProgress(55, `Parsed ${uploadData.rows.toLocaleString()} rows × ${uploadData.columns} columns — analyzing…`);

      const analyzeRes = await fetch(`/api/analyze/${currentSessionId}`, { method: "POST" });
      const analysis = await analyzeRes.json();
      if (!analyzeRes.ok) throw new Error(analysis.detail || "Analysis failed.");

      setForgeProgress(100, "Ready.", true);
      setTimeout(() => renderDashboard(analysis), 350);
    } catch (err) {
      showError(err.message || "Something went wrong.");
      forgeBar.hidden = true;
    }
  }

  // ---------- dashboard rendering ----------
  function renderDashboard(data) {
    hero.hidden = true;
    dashboard.hidden = false;
    forgeBar.hidden = true;
    datasetName.textContent = data.filename;

    const o = data.overview;
    const stats = [
      { label: "Rows", value: o.rows.toLocaleString() },
      { label: "Columns", value: o.columns },
      { label: "Missing cells", value: `${o.missing_pct}%`, cls: o.missing_pct > 15 ? "warn" : "ok" },
      { label: "Duplicate rows", value: o.duplicate_rows, cls: o.duplicate_rows > 0 ? "warn" : "ok" },
      { label: "Numeric columns", value: o.numeric_columns.length },
      { label: "Categorical columns", value: o.categorical_columns.length },
    ];
    statGrid.innerHTML = stats.map(s => `
      <div class="stat-card ${s.cls || ""}">
        <p class="stat-label">${s.label}</p>
        <p class="stat-value">${s.value}</p>
      </div>
    `).join("");

    insightsList.innerHTML = data.insights.map(note => `<li>${escapeHtml(note)}</li>`).join("");
    if (data.ai_summary) {
      aiSummaryEl.hidden = false;
      aiSummaryEl.textContent = data.ai_summary;
    } else {
      aiSummaryEl.hidden = true;
    }

    columnsTableBody.innerHTML = data.columns.map(c => `
      <tr>
        <td class="col-name">${escapeHtml(c.name)}</td>
        <td class="mono">${escapeHtml(c.dtype)}</td>
        <td>${c.missing} <span class="mono">(${c.missing_pct}%)</span></td>
        <td>${c.unique}</td>
      </tr>
    `).join("");

    chartsGrid.innerHTML = data.charts.map(chart => `
      <div class="chart-card">
        <img src="data:image/png;base64,${chart.image}" alt="${escapeHtml(chart.title)}" loading="lazy" />
        <div class="chart-title">${escapeHtml(chart.title)}</div>
      </div>
    `).join("");

    // reset the cast panel for a fresh dataset
    buildBtn.hidden = false;
    buildBtn.disabled = false;
    buildBtn.querySelector(".cast-btn-label").textContent = "Build notebook";
    downloadBtn.hidden = true;

    dashboard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
  }

  // ---------- notebook build & download ----------
  buildBtn.addEventListener("click", async () => {
    if (!currentSessionId) return;
    buildBtn.disabled = true;
    buildBtn.querySelector(".cast-btn-label").textContent = "Casting…";

    try {
      const res = await fetch(`/api/build-notebook/${currentSessionId}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not build notebook.");

      downloadBtn.href = `/api/download-notebook/${currentSessionId}`;
      downloadBtn.setAttribute("download", data.notebook_filename);
      downloadBtn.hidden = false;
      buildBtn.hidden = true;
    } catch (err) {
      buildBtn.disabled = false;
      buildBtn.querySelector(".cast-btn-label").textContent = "Build notebook";
      alert(err.message);
    }
  });

  // ---------- reset flow ----------
  newUploadBtn.addEventListener("click", () => {
    currentSessionId = null;
    fileInput.value = "";
    dashboard.hidden = true;
    hero.hidden = false;
    forgeBar.hidden = true;
    clearError();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();
