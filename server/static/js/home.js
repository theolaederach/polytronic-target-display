/**
 * Read a CSS variable of the theme (defined in style.css).
 *
 * Args :
 *     name (string): the variable name, for example "--accent".
 *
 * Return :
 *     The value of the variable (string).
 */
function getThemeColor(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

/**
 * Set the global Chart.js style so every chart matches the dark theme.
 * Must be called once, before creating any chart.
 */
function applyChartTheme() {
  Chart.defaults.color = getThemeColor("--text-muted");
  Chart.defaults.borderColor = getThemeColor("--border");
  Chart.defaults.font.family = "system-ui, sans-serif";
  // smaller legend swatches (the default boxes are very wide)
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.boxHeight = 12;
}

/**
 * Draw the doughnut chart "Score distribution".
 *
 * Args :
 *     canvas (HTMLCanvasElement): the canvas to draw in.
 *     distribution (object): { labels: string[], values: number[] }.
 *
 * Return :
 *     The Chart.js instance (Chart).
 */
function createWeaponsChart(canvas, distribution) {
  return new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: distribution.labels,
      datasets: [
        {
          data: distribution.values,
          backgroundColor: ["#F26963", "#6366F1", "#63F297", "#F2D763"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
    },
  });
}

/**
 * Draw the grouped bar chart "Programms per target".
 *
 * Args :
 *     canvas (HTMLCanvasElement): the canvas to draw in.
 *     data (object): { labels: string[], datasets: [{ label: string, data: number[] }] }.
 *
 * Return :
 *     The Chart.js instance (Chart).
 */
function createProgrammChart(canvas, data) {
  const colors = ["#F26963", "#6366F1", "#63F297", "#F2D763", "#11A1E1"];
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels: data.labels,
      // give a color to each target (the datasets come from the server)
      datasets: data.datasets.map((dataset, i) => ({
        ...dataset,
        backgroundColor: colors[i % colors.length],
      })),
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        // a number of programms is always an integer
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
      plugins: { legend: { position: "bottom" } },
    },
  });
}
