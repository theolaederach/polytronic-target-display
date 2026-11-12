// Responsive sidebar: opens/closes the navigation on small screens.
// The layout itself (overlay on tablets, bottom panel on phones) is handled
// by CSS in style.css; this script only toggles the "nav-open" state.
(function () {
  const toggle = document.querySelector(".nav-toggle");
  const backdrop = document.querySelector(".nav-backdrop");
  if (!toggle) return;

  // Same breakpoints as the CSS media queries
  const breakpoints = [
    window.matchMedia("(max-width: 900px)"),
    window.matchMedia("(max-width: 600px)"),
  ];

  /**
   * Open or close the sidebar.
   *
   * Args :
   *     open (boolean): true to open the sidebar, false to close it.
   *
   * Return :
   *     Nothing (void)
   */
  function setOpen(open) {
    // CSS reads this class to show/hide the sidebar
    document.body.classList.toggle("nav-open", open);
    // keep assistive technologies in sync
    toggle.setAttribute("aria-expanded", String(open));
  }

  /**
   * Tell whether the sidebar is currently open.
   *
   * Return :
   *     True if the sidebar is open (boolean)
   */
  function isOpen() {
    return toggle.getAttribute("aria-expanded") === "true";
  }

  toggle.addEventListener("click", () => setOpen(!isOpen()));

  // Clicking outside the overlay closes it
  if (backdrop) backdrop.addEventListener("click", () => setOpen(false));

  // Escape closes the sidebar and gives the focus back to the button
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isOpen()) {
      setOpen(false);
      toggle.focus();
    }
  });

  // Reset the state when the window crosses a breakpoint (e.g. rotation)
  for (const query of breakpoints) {
    query.addEventListener("change", () => setOpen(false));
  }
})();
