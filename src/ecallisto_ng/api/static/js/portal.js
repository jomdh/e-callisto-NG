// Portal client behavior (no inline handlers; CSP-friendly).
(function () {
  "use strict";
  const toggle = document.querySelector("[data-action='toggle-theme']");
  if (toggle) {
    toggle.addEventListener("click", function () {
      const root = document.documentElement;
      const next =
        root.getAttribute("data-theme") === "nebula" ? "supernova" : "nebula";
      root.setAttribute("data-theme", next);
      localStorage.setItem("ecallisto-theme", next);
    });
  }
})();
