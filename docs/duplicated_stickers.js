(function () {
  "use strict";

  const STORAGE_KEY = "duplicate-stickers-status";
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  let duplicateSearchQuery = "";
  const openTeams = {};

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

  function normalizeText(text) {
    return text
      .toString()
      .normalize("NFD")
      .replace(/ /g, "")
      .toLowerCase();
  }

  function normalizeTextOnly(text) {
    return normalizeText(text);
  }

  function normalizeCode(code) {
    return code.toString().trim().toLowerCase().replace(/ /g, "");
  }

  function matchesSearchQuery(team, query) {
    const normalizedQuery = normalizeTextOnly(query);
    const normalizedName = normalizeTextOnly(team.name);
    const normalizedCode = normalizeCode(team.code);
    return normalizedName.includes(normalizedQuery) || normalizedCode.includes(normalizedQuery);
  }

  function renderList() {
    const status = loadStatus();
    const container = $("#duplicate-list");
    const query = duplicateSearchQuery.trim();
    const teams = query
      ? ALBUM_DUPLICATE_DATA.teams.filter(team => matchesSearchQuery(team, query))
      : ALBUM_DUPLICATE_DATA.teams;

    if (query && teams.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); padding: 2rem 0; text-align: center;">Nenhum time encontrado para "${query}".</p>`;
      return;
    }

    container.innerHTML = teams.map(team => {
      const stickers = team.stickers || [];
      const markedCount = stickers.reduce((acc, code) => acc + (!!status[normalizeCode(code)] ? 1 : 0), 0);
      const isOpen = !!openTeams[team.code];
      const items = stickers.length > 0
        ? stickers.map(code => {
            const normalized = normalizeCode(code);
            const marked = !!status[normalized];
            return `
              <button class="duplicate-sticker-item${marked ? " marked" : ""}" data-code="${normalized}" type="button" aria-pressed="${marked}">
                <span class="duplicate-marker-btn">${marked ? "✅" : "❌"}</span>
                <span class="duplicate-sticker-code">${code}</span>
              </button>`;
          }).join("")
        : `<div class="no-duplicates">Nenhuma figurinha</div>`;

      return `
        <section class="duplicate-team-section" data-team="${team.code}">
          <button class="duplicate-team-summary" type="button" data-team="${team.code}" aria-expanded="${isOpen}">
            <div class="duplicate-team-heading">
              <div class="team-flag">${team.flag}</div>
              <div>
                <div class="duplicate-team-name">${team.name}<span class="duplicate-team-code">${team.code}</span></div>
                <div class="duplicate-team-subtitle">${team.group === "–" ? "Especial" : `Grupo ${team.group}`}</div>
              </div>
              <div class="duplicate-team-summary-right">
                <span class="duplicate-team-stats">${stickers.length} figurinhas · ${markedCount} marcadas</span>
                <span class="duplicate-toggle-icon">${isOpen ? "▲" : "▼"}</span>
              </div>
            </div>
          </button>
          <div class="duplicate-sticker-row${isOpen ? "" : " collapsed"}">
            ${items}
          </div>
        </section>`;
    }).join("");

    container.querySelectorAll(".duplicate-team-summary").forEach(btn => {
      btn.addEventListener("click", () => {
        const code = btn.dataset.team;
        openTeams[code] = !openTeams[code];
        renderList();
      });
    });

    container.querySelectorAll(".duplicate-sticker-item").forEach(item => {
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
    return ALBUM_DUPLICATE_DATA.teams.map(team => {
      const header = `# ${team.name} (${team.code})`;
      const rows = (team.stickers || []).map(code => {
        const normalized = normalizeCode(code);
        const marked = !!status[normalized];
        if (filter === "marked" && !marked) return null;
        if (filter === "unmarked" && marked) return null;
        return `${marked ? "✅" : "❌"} ${code}`;
      }).filter(Boolean);

      if (rows.length === 0) {
        return null;
      }
      return header + String.fromCharCode(10) + rows.join(String.fromCharCode(10));
    }).filter(Boolean).join(String.fromCharCode(10) + String.fromCharCode(10));
  }

  function copyList() {
    copyText(buildCopyText(), "Lista copiada para a área de transferência.");
  }

  function copyMarked() {
    copyText(buildCopyText("marked"), "Lista de marcadas copiada.");
  }

  function copyUnmarked() {
    copyText(buildCopyText("unmarked"), "Lista de não marcadas copiada.");
  }

  function copyText(text, message) {
    navigator.clipboard.writeText(text).then(() => {
      const status = $("#dup-copy-status");
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

  function initSearchInput() {
    const input = $("#duplicate-search");
    if (!input) return;

    input.addEventListener("input", () => {
      duplicateSearchQuery = input.value;
      renderList();
    });
  }

  function init() {
    if (typeof ALBUM_DUPLICATE_DATA === "undefined") {
      document.body.innerHTML = `<p style="padding:2rem;color:red">Erro: duplicate_data.js não encontrado. Execute generate_site_data.py primeiro.</p>`;
      return;
    }

    $("#dup-copy-list").addEventListener("click", copyList);
    $("#dup-copy-marked").addEventListener("click", copyMarked);
    $("#dup-copy-unmarked").addEventListener("click", copyUnmarked);
    $("#dup-reset-markers").addEventListener("click", resetMarkers);
    const backButton = $("#dup-back-button");
    if (backButton) {
      backButton.addEventListener("click", () => {
        if (window.history.length > 1) {
          window.history.back();
        } else {
          window.location.href = "index.html";
        }
      });
    }
    initSearchInput();
    renderList();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
