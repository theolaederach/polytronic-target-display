// Title : home page
// Description : Fill the home page template (stat tiles, charts, results table).
//               All the data below is PLACEHOLDER data, replace it with API calls.

// Placeholder data (TEMPLATE) ------------------------------------------------
const PLACEHOLDER_SCORES = [78, 82, 85, 80, 88, 91, 87, 93, 90, 95];
const PLACEHOLDER_DISTRIBUTION = {
  labels: ["10", "9", "8", "7", "<= 6"],
  values: [12, 25, 30, 18, 15],
};
const PLACEHOLDER_RESULTS = [
  { shooter: "Shooter A", targetType: "A10", score10: 91, score100: 912 },
  { shooter: "Shooter B", targetType: "A10", score10: 88, score100: 874 },
  { shooter: "Shooter C", targetType: "B4", score10: 85, score100: 851 },
];

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
 * Write a value in a stat tile.
 *
 * Args :
 *     elementId (string): id of the ".stat-value" element.
 *     value (string|number): the value to display.
 */
function setStat(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = value;
  }
}

/**
 * Draw the line chart "Score over time".
 *
 * Args :
 *     canvas (HTMLCanvasElement): the canvas to draw in.
 *     scores (number[]): one score per point, in chronological order.
 *
 * Return :
 *     The Chart.js instance (Chart), useful to update it later.
 */
function createScoreChart(canvas, scores) {
  // x axis labels are just the index of each score: 1, 2, 3...
  const labels = scores.map((_, index) => index + 1);

  return new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Score",
          data: scores,
          borderColor: getThemeColor("--accent"),
          backgroundColor: "rgba(56, 189, 248, 0.15)",
          fill: true,
          tension: 0.25,
        },
      ],
    },
    options: {
      maintainAspectRatio: false, // follow the height of .chart-box
      scales: { y: { beginAtZero: true } },
    },
  });
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
function createDistributionChart(canvas, distribution) {
  return new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: distribution.labels,
      datasets: [
        {
          data: distribution.values,
          backgroundColor: ["#38bdf8", "#0ea5e9", "#6366f1", "#f59e0b", "#64748b"],
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
 * Fill the "Latest results" table body.
 * Uses textContent (not innerHTML) so a shooter name can never inject HTML.
 *
 * Args :
 *     tbody (HTMLElement): the <tbody> to fill.
 *     results (object[]): rows with shooter, targetType, score10, score100.
 */
function fillResultsTable(tbody, results) {
  tbody.replaceChildren(); // remove the old rows

  results.forEach((result, index) => {
    const row = document.createElement("tr");

    // [text, is it a number column ?] for each cell of the row
    const cells = [
      [index + 1, false],
      [result.shooter, false],
      [result.targetType, false],
      [result.score10, true],
      [result.score100, true],
    ];

    cells.forEach(([text, isNumber]) => {
      const cell = document.createElement("td");
      cell.textContent = text;
      if (isNumber) {
        cell.className = "num"; // right-aligned, see style.css
      }
      row.appendChild(cell);
    });

    tbody.appendChild(row);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyChartTheme();

  // TEMPLATE: replace these placeholders with fetch() calls to your API
  setStat("stat_shooters", "12");
  setStat("stat_programs", "34");
  setStat("stat_shots", "560");
  setStat("stat_average", "87.4");

  createScoreChart(document.getElementById("home_line_chart"), PLACEHOLDER_SCORES);
  createDistributionChart(
    document.getElementById("home_doughnut_chart"),
    PLACEHOLDER_DISTRIBUTION,
  );
  fillResultsTable(
    document.getElementById("home_results_body"),
    PLACEHOLDER_RESULTS,
  );
});
