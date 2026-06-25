// Sidebar shell: theme toggle, collapse, mobile drawer. CSP-safe external file.
(function () {
  "use strict";
  const KEY = "ecallisto-theme";

  // --- theme toggle (nebula/supernova) ---
  const current = localStorage.getItem(KEY) || "nebula";
  const nebula = document.getElementById("btn-nebula");
  const supernova = document.getElementById("btn-supernova");
  if (nebula && supernova) {
    nebula.classList.toggle("active", current === "nebula");
    supernova.classList.toggle("active", current === "supernova");
    const set = (theme) => {
      if (theme === (localStorage.getItem(KEY) || "nebula")) return;
      localStorage.setItem(KEY, theme);
      document.documentElement.setAttribute("data-theme", theme);
      location.reload(); // canvases (waterfall) pick up the new palette
    };
    nebula.addEventListener("click", () => set("nebula"));
    supernova.addEventListener("click", () => set("supernova"));
  }

  // --- collapse (desktop) ---
  const sidebar = document.getElementById("sidebar");
  const header = document.getElementById("sidebar-header");
  if (sidebar && localStorage.getItem("ecallisto-sidebar") === "1") {
    sidebar.classList.add("collapsed");
  }
  if (header && sidebar) {
    header.addEventListener("click", () => {
      if (window.innerWidth <= 840) return; // mobile uses the drawer
      sidebar.classList.toggle("collapsed");
      localStorage.setItem(
        "ecallisto-sidebar",
        sidebar.classList.contains("collapsed") ? "1" : "0"
      );
    });
  }

  // --- mobile drawer ---
  const fab = document.getElementById("mobile-fab");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (fab && sidebar && backdrop) {
    const open = () => {
      sidebar.classList.add("mobile-open");
      backdrop.classList.add("open");
    };
    const close = () => {
      sidebar.classList.remove("mobile-open");
      backdrop.classList.remove("open");
    };
    fab.addEventListener("click", () =>
      sidebar.classList.contains("mobile-open") ? close() : open()
    );
    backdrop.addEventListener("click", close);
  }
})();
