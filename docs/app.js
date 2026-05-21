/* ===================================================================
   Figurinhas da Prof Giu — app.js
   Vanilla JS: renders ALBUM_DATA (from data.js) into the page.
   =================================================================== */

(function () {
  "use strict";

  /* ── helpers ─────────────────────────────────────────────────── */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  function pctColor(pct) {
    if (pct === 100) return "fill-green";
    if (pct >= 60)  return "fill-yellow";
    if (pct >= 30)  return "fill-orange";
    return "fill-red";
  }

  function pctBadgeColor(pct) {
    if (pct === 100) return "#1a7a3c";
    if (pct >= 60)   return "#d69e2e";
    if (pct >= 30)   return "#dd6b20";
    return "#bf0000";
  }

  /* ── state ───────────────────────────────────────────────────── */
  let activeGroup = "ALL";
  let sortKey     = "group";   // "group" | "pct_asc" | "pct_desc" | "alpha"

  /* ── HERO ────────────────────────────────────────────────────── */
  function renderHero(meta) {
    $("#hero-title").textContent    = meta.title;
    $("#hero-subtitle").textContent = meta.album;
    $("#hero-counter").innerHTML    =
      `<strong>${meta.collected.toLocaleString("pt-BR")}</strong> de <strong>${meta.total.toLocaleString("pt-BR")}</strong> figurinhas coletadas`;
    const bar = $("#hero-bar");
    bar.style.width = "0%";
    setTimeout(() => { bar.style.width = meta.percent + "%"; }, 100);
    $("#hero-updated").textContent  = "Atualizado em " + formatDate(meta.updated);
  }

  function formatDate(iso) {
    const [y, m, d] = iso.split("-");
    return `${d}/${m}/${y}`;
  }

  /* ── STAT CARDS ──────────────────────────────────────────────── */
  function renderStats(meta) {
    $("#stat-collected").textContent  = meta.collected.toLocaleString("pt-BR");
    $("#stat-missing").textContent    = meta.missing.toLocaleString("pt-BR");
    $("#stat-percent").textContent    = meta.percent.toFixed(1) + "%";
    $("#stat-complete").textContent   = meta.completeTeams;
  }

  /* ── HIGHLIGHTS ──────────────────────────────────────────────── */
  function renderHighlights(teams) {
    const regular = teams.filter(t => t.group !== "–" && t.total > 0);
    const byPct   = [...regular].sort((a, b) => a.percent - b.percent);
    const critical = byPct.slice(0, 5);
    const complete = [...byPct].reverse().slice(0, 5);

    renderMiniList($("#critical-list"), critical, false);
    renderMiniList($("#complete-list"), complete, true);
  }

  function renderMiniList(container, teams, isComplete) {
    container.innerHTML = teams.map(t => {
      const color = isComplete ? "#1a7a3c" : "#bf0000";
      return `
        <div class="mini-team">
          <span class="flag-em">${t.flag}</span>
          <div class="info">
            <div class="tname">${t.name}</div>
            <div class="mini-progress">
              <div class="mini-progress-bar ${pctColor(t.percent)}"
                   style="width:${t.percent}%"></div>
            </div>
          </div>
          <span class="pct-badge" style="color:${color}">${t.percent.toFixed(0)}%</span>
        </div>`;
    }).join("");
  }

  /* ── FILTER PILLS ────────────────────────────────────────────── */
  function renderFilterBar() {
    const bar = $("#filter-bar");
    const groups = ["ALL", "A","B","C","D","E","F","G","H","I","J","K","L","–"];
    const labels = { "ALL": "Todos", "–": "Especiais" };

    bar.innerHTML = groups.map(g => {
      const lbl = labels[g] ?? `Grupo ${g}`;
      const active = g === activeGroup ? " active" : "";
      return `<button class="group-pill${active}" data-group="${g}">${lbl}</button>`;
    }).join("");

    $$(".group-pill", bar).forEach(btn => {
      btn.addEventListener("click", () => {
        activeGroup = btn.dataset.group;
        $$(".group-pill", bar).forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        renderTeams(ALBUM_DATA.teams);
      });
    });
  }

  /* ── SORT BUTTONS ────────────────────────────────────────────── */
  function initSortBtns() {
    $$(".sort-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        $$(".sort-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        sortKey = btn.dataset.sort;
        renderTeams(ALBUM_DATA.teams);
      });
    });
  }

  /* ── TEAM CARDS ──────────────────────────────────────────────── */
  function getSortedFiltered(teams) {
    let list = teams.filter(t => activeGroup === "ALL" || t.group === activeGroup);

    // Never show special sections (–) in the main grid unless filter = "–"
    if (activeGroup !== "–") {
      list = list.filter(t => t.group !== "–");
    }

    const groupOrder = (g) => "ABCDEFGHIJKL–".indexOf(g);

    switch (sortKey) {
      case "group":
        list.sort((a, b) => groupOrder(a.group) - groupOrder(b.group) || a.name.localeCompare(b.name, "pt"));
        break;
      case "pct_asc":
        list.sort((a, b) => a.percent - b.percent || a.name.localeCompare(b.name, "pt"));
        break;
      case "pct_desc":
        list.sort((a, b) => b.percent - a.percent || a.name.localeCompare(b.name, "pt"));
        break;
      case "alpha":
        list.sort((a, b) => a.name.localeCompare(b.name, "pt"));
        break;
    }
    return list;
  }

  function renderTeams(teams) {
    const grid = $("#teams-grid");
    const list = getSortedFiltered(teams);

    if (list.length === 0) {
      grid.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:2rem 0">
        Nenhum time encontrado.</p>`;
      return;
    }

    grid.innerHTML = list.map(t => buildTeamCard(t)).join("");

    // Attach expand toggle
    $$(".team-card", grid).forEach(card => {
      card.addEventListener("click", () => {
        card.classList.toggle("open");
        card.querySelector(".missing-panel").classList.toggle("open");
      });
    });
  }

  function buildTeamCard(t) {
    const fillClass = pctColor(t.percent);
    const missingChips = t.missing.length === 0
      ? `<span class="chip all-collected">✓ Todas coletadas!</span>`
      : t.missing.map(c => `<span class="chip">${c}</span>`).join("");

    const hostBadge  = t.isHost  ? `<span class="badge badge-host">🏠 Anfitrião</span>` : "";
    const groupBadge = t.group !== "–" ? `<span class="badge badge-group">${t.group}</span>` : "";
    const doneBadge  = t.percent === 100 ? `<span class="badge badge-done">✓ Completo</span>` : "";

    const missingLabel = t.missing.length > 0
      ? `Faltando ${t.missing.length} figurinha${t.missing.length > 1 ? "s" : ""}:`
      : "Status:";

    return `
      <article class="team-card" role="button" tabindex="0" aria-expanded="false">
        <div class="team-card-header">
          <span class="team-flag">${t.flag}</span>
          <div class="team-info">
            <div class="team-name">${t.name}</div>
            <div class="team-badges">${groupBadge}${hostBadge}${doneBadge}</div>
          </div>
          <div class="team-count"><strong>${t.collected}</strong>/${t.total}</div>
        </div>
        <div class="team-progress-wrap">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill ${fillClass}" style="width:${t.percent}%"></div>
          </div>
          <div class="progress-pct">${t.percent.toFixed(1)}%</div>
        </div>
        <div class="missing-panel">
          <div class="missing-title">${missingLabel}</div>
          <div class="missing-chips">${missingChips}</div>
        </div>
      </article>`;
  }

  /* ── SPECIAL SECTIONS ────────────────────────────────────────── */
  function renderSpecial(special) {
    const grid = $("#special-grid");
    grid.innerHTML = special.map(s => `
      <div class="special-card">
        <div class="s-flag">${s.flag}</div>
        <div class="s-name">${s.name}</div>
        <div class="progress-bar-bg" style="margin:0 auto .75rem;max-width:200px">
          <div class="progress-bar-fill ${pctColor(s.percent)}" style="width:${s.percent}%"></div>
        </div>
        <div class="s-count">${s.collected}<span class="s-of">/${s.total}</span></div>
        <div style="font-size:.72rem;color:var(--text-muted);margin-top:.2rem">${s.percent.toFixed(1)}% coletadas</div>
        ${s.missing.length > 0 ? `<div style="margin-top:.75rem;font-size:.7rem;color:#bf0000">
          Faltando: ${s.missing.join(", ")}</div>` : 
          `<div style="margin-top:.75rem;font-size:.75rem;color:#1a7a3c;font-weight:700">✓ Completo!</div>`}
      </div>`).join("");
  }

  /* ── FOOTER ──────────────────────────────────────────────────── */
  function renderFooter(meta) {
    const el = $("#footer-updated");
    if (el) el.textContent = formatDate(meta.updated);
  }

  /* ── KEYBOARD ACCESSIBILITY ──────────────────────────────────── */
  document.addEventListener("keydown", e => {
    if (e.key === "Enter" && e.target.classList.contains("team-card")) {
      e.target.click();
    }
  });

  /* ── INIT ────────────────────────────────────────────────────── */
  function init() {
    if (typeof ALBUM_DATA === "undefined") {
      document.body.innerHTML =
        `<p style="padding:2rem;color:red">Erro: data.js não encontrado. Execute generate_site_data.py primeiro.</p>`;
      return;
    }
    const { meta, teams, special } = ALBUM_DATA;
    renderHero(meta);
    renderStats(meta);
    renderHighlights(teams);
    renderFilterBar();
    initSortBtns();
    renderTeams(teams);
    renderSpecial(special);
    renderFooter(meta);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
