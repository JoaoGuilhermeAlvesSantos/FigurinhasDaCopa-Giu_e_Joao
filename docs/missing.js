(function () {
  "use strict";

  const STORAGE_KEY = "missing-stickers-status";
  const $ = (sel, ctx = document) => ctx.querySelector(sel);

  function loadStatus() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") || {};
    } catch (err) {
      return {};
    }
  }

  function saveStatus(status) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(status));
  }

  function normalizeCode(code) {
    return code.toString().trim().toUpperCase().replace(/\s+/g, "");
  }

  function renderList() {
    const status = loadStatus();
    const container = $("#missing-list");
    container.innerHTML = ALBUM_DATA.teams.map(team => {
      const missing = team.missing || [];
      const items = missing.length > 0
        ? missing.map(code => {
            const normalized = normalizeCode(code);
            const found = !!status[normalized];
            return `
              <button class="sticker-item${found ? " found" : ""}" data-code="${normalized}" type="button" aria-pressed="${found}">
                <span class="marker-btn">${found ? "✅" : "❌"}</span>
                <span class="sticker-code">${code}</span>
              </button>`;
          }).join("")
        : `<div class="no-missing">Todas completas</div>`;

      return `
        <section class="team-section" data-team="${team.code}">
          <div class="team-heading">
            <div class="team-flag">${team.flag}</div>
            <div>
              <div class="team-name">${team.name}<span class="team-code">${team.code}</span></div>
              <div class="team-subtitle">${team.group === "–" ? "Especial" : `Grupo ${team.group}`}</div>
            </div>
          </div>
          <div class="sticker-row">
            ${items}
          </div>
        </section>`;
    }).join("");

    container.querySelectorAll(".sticker-item").forEach(item => {
      item.addEventListener("click", () => {
        const code = item.dataset.code;
        const current = !!status[code];
        if (current) {
          delete status[code];
        } else {
          status[code] = true;
        }
        saveStatus(status);
        renderList();
      });
    });
  }

  function buildCopyText(filter) {
    const status = loadStatus();
    return ALBUM_DATA.teams.map(team => {
      const missing = team.missing || [];
      const header = `# ${team.name} (${team.code})`;
      if (missing.length === 0) {
        return `${header}\nTodas completas\n`;
      }
      const rows = missing.map(code => {
        const normalized = normalizeCode(code);
        const found = !!status[normalized];
        if (filter === "found" && !found) return null;
        if (filter === "missing" && found) return null;
        return `${found ? "✅" : "❌"} ${code}`;
      }).filter(Boolean);
      if (rows.length === 0) {
        return null;
      }
      return `${header}\n${rows.join("\n")}`;
    }).filter(Boolean).join("\n\n");
  }

  function copyList() {
    const text = buildCopyText();
    copyText(text, "Lista copiada para a área de transferência.");
  }

  function copyFound() {
    const text = buildCopyText("found");
    copyText(text, "Lista de encontradas copiada.");
  }

  function copyMissing() {
    const text = buildCopyText("missing");
    copyText(text, "Lista de faltantes copiada.");
  }

  function copyText(text, message) {
    navigator.clipboard.writeText(text).then(() => {
      const status = $("#copy-status");
      if (status) {
        status.textContent = message;
        setTimeout(() => { status.textContent = ""; }, 2400);
      }
    });
  }

  function resetMarkers() {
    localStorage.removeItem(STORAGE_KEY);
    renderList();
  }

  function init() {
    if (typeof ALBUM_DATA === "undefined") {
      document.body.innerHTML = `<p style="padding:2rem;color:red">Erro: data.js não encontrado. Execute generate_site_data.py primeiro.</p>`;
      return;
    }

    $("#copy-list").addEventListener("click", copyList);
    $("#copy-found").addEventListener("click", copyFound);
    $("#copy-missing").addEventListener("click", copyMissing);
    $("#reset-markers").addEventListener("click", resetMarkers);
    const backButton = $("#back-button");
    if (backButton) {
      backButton.addEventListener("click", () => {
        if (window.history.length > 1) {
          window.history.back();
        } else {
          window.location.href = "index.html";
        }
      });
    }
    renderList();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
