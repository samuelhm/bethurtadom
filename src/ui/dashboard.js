const form = document.getElementById("link-form");
const winamaxSelect = document.getElementById("winamax-match");
const bet365Select = document.getElementById("bet365-match");
const statusEl = document.getElementById("link-status");
const refreshStateEl = document.getElementById("refresh-state");
const linkedPanelEl = document.getElementById("linked-panel");
const pendingPanelEl = document.getElementById("pending-panel");

const refreshSeconds = Number.parseInt(
  document.body?.dataset?.refreshSeconds ?? "1",
  10,
);
const viewMode = (document.body?.dataset?.viewMode || "all").toLowerCase();
const canLink = viewMode !== "linked";
const linkApiUrl = form?.getAttribute("action") || "/api/link";

let isSubmitting = false;
let isUserInteracting = false;
let reloadTimeoutId = null;

function parseEmbeddedMatches(elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`No se encontró el bloque JSON '${elementId}'`);
    return [];
  }

  try {
    return JSON.parse(element.textContent || "[]");
  } catch (error) {
    console.error(`JSON inválido en '${elementId}'`, error);
    return [];
  }
}

const winamaxMatches = parseEmbeddedMatches("winamax-matches-data");
const bet365Matches = parseEmbeddedMatches("bet365-matches-data");

function setVisible(element, isVisible) {
  if (!element) {
    return;
  }
  element.hidden = !isVisible;
}

function applyViewMode() {
  if (viewMode === "linked") {
    setVisible(linkedPanelEl, true);
    setVisible(form, false);
    setVisible(refreshStateEl, false);
    setVisible(pendingPanelEl, false);
    return;
  }

  if (viewMode === "linker") {
    setVisible(linkedPanelEl, false);
    setVisible(form, true);
    setVisible(refreshStateEl, true);
    setVisible(pendingPanelEl, true);
    return;
  }

  setVisible(linkedPanelEl, true);
  setVisible(form, true);
  setVisible(refreshStateEl, true);
  setVisible(pendingPanelEl, true);
}

function setStatus(message, isError = false) {
  if (!statusEl) {
    return;
  }
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#fca5a5" : "#38bdf8";
}

function isInteracting() {
  return isUserInteracting;
}

function updateRefreshState() {
  if (!refreshStateEl) {
    return;
  }

  if (isSubmitting) {
    refreshStateEl.textContent = "Auto-refresh pausado: guardando enlace...";
    return;
  }

  if (isInteracting()) {
    refreshStateEl.textContent = "Auto-refresh pausado: seleccionando partido...";
    return;
  }

  refreshStateEl.textContent = `Auto-refresh activo: ${refreshSeconds}s`;
}

function scheduleAutoRefresh() {
  if (!Number.isFinite(refreshSeconds) || refreshSeconds <= 0) {
    return;
  }

  if (reloadTimeoutId) {
    window.clearTimeout(reloadTimeoutId);
  }

  reloadTimeoutId = window.setTimeout(() => {
    if (isSubmitting || isInteracting() || document.visibilityState === "hidden") {
      scheduleAutoRefresh();
      updateRefreshState();
      return;
    }

    window.location.reload();
  }, refreshSeconds * 1000);
}

function beginInteraction() {
  isUserInteracting = true;
  updateRefreshState();
  scheduleAutoRefresh();
}

function endInteraction() {
  isUserInteracting = false;
  updateRefreshState();
  scheduleAutoRefresh();
}

async function parseJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

if (canLink && form && winamaxSelect && bet365Select) {
  [winamaxSelect, bet365Select].forEach((selectEl) => {
    selectEl.addEventListener("mousedown", beginInteraction);
  });

  form.addEventListener("focusin", beginInteraction);
  form.addEventListener("focusout", () => {
    window.setTimeout(() => {
      if (!form.contains(document.activeElement)) {
        endInteraction();
      }
    }, 0);
  });
}

document.addEventListener("visibilitychange", () => {
  updateRefreshState();
  scheduleAutoRefresh();
});

if (canLink && form && winamaxSelect && bet365Select) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    endInteraction();
    isSubmitting = true;
    updateRefreshState();

    const winamaxIndex = Number.parseInt(winamaxSelect.value, 10);
    const bet365Index = Number.parseInt(bet365Select.value, 10);

    if (Number.isNaN(winamaxIndex) || Number.isNaN(bet365Index)) {
      isSubmitting = false;
      updateRefreshState();
      scheduleAutoRefresh();
      setStatus("Selecciona ambos partidos antes de enlazar.", true);
      return;
    }

    const winamaxMatch = winamaxMatches[winamaxIndex];
    const bet365Match = bet365Matches[bet365Index];
    if (!winamaxMatch || !bet365Match) {
      isSubmitting = false;
      updateRefreshState();
      scheduleAutoRefresh();
      setStatus("No se pudieron leer los partidos seleccionados.", true);
      return;
    }

    setStatus("Guardando enlace...");

    try {
      const response = await fetch(linkApiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          winamax_match: winamaxMatch,
          bet365_match: bet365Match,
        }),
      });

      const payload = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(payload?.message || "No se pudo guardar el enlace.");
      }

      isSubmitting = false;
      updateRefreshState();
      scheduleAutoRefresh();
      setStatus(
        payload?.message || "Enlace guardado. Se reflejará en la próxima actualización.",
      );
    } catch (error) {
      isSubmitting = false;
      endInteraction();
      updateRefreshState();
      scheduleAutoRefresh();
      const message = error instanceof Error ? error.message : "Error inesperado";
      setStatus(message, true);
    }
  });
}

applyViewMode();
updateRefreshState();
scheduleAutoRefresh();
