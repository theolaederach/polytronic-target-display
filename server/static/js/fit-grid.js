// Choisit le nombre de colonnes qui donne les plus grandes cibles possibles
// pour la taille actuelle de la fenêtre, quel que soit le nombre de cibles.
(function () {
    const container = document.querySelector(".target-container");
    if (!container) return;

    function fit() {
        const items = container.querySelectorAll(".element");
        const n = items.length;
        if (n === 0) return;

        const style = getComputedStyle(container);
        const gap = parseFloat(style.columnGap) || 0;
        const W = container.clientWidth;
        const H = container.clientHeight;

        // hauteur occupée par le titre h2 de chaque cible
        const h2 = items[0].querySelector("h2");
        let titleH = 0;
        if (h2) {
            const s = getComputedStyle(h2);
            titleH =
                h2.offsetHeight +
                parseFloat(s.marginTop) +
                parseFloat(s.marginBottom);
        }

        // grilles "pleines" uniquement (1x6, 2x3, 3x2, 6x1...),
        // sauf si n est premier : on autorise alors toutes les colonnes
        let candidates = [];
        for (let c = 1; c <= n; c++) if (n % c === 0) candidates.push(c);
        if (candidates.length === 2 && n > 3) {
            candidates = Array.from({ length: n }, (_, i) => i + 1);
        }

        let best = 1;
        let bestSize = -1;
        for (const cols of candidates) {
            const rows = Math.ceil(n / cols);
            const cellW = (W - gap * (cols - 1)) / cols;
            const cellH = (H - gap * (rows - 1)) / rows - titleH;
            const size = Math.min(cellW, cellH); // la cible est carrée
            if (size > bestSize) {
                bestSize = size;
                best = cols;
            }
        }

        container.style.setProperty("--cols", best);
        container.style.setProperty("--rows", Math.ceil(n / best));
    }

    new ResizeObserver(fit).observe(container);
    window.addEventListener("resize", fit);
    fit();
})();
