function create_line_charts(chart_canva, data) {
  if (data) {
    labels = [];
    for (let i = 1; i < data.length + 1; i++) {
      labels.push(i);
    }
    console.log(labels);
    console.log(data);
    new Chart(chart_canva, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "shots",
            data: data,
            fill: false,
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }
}
