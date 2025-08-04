// Charts module for managing all chart instances
window.charts = {
  instances: {},

  init() {
    Chart.defaults.font.family =
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = "#374151";
  },

  createTimelineChart(data) {
    const ctx = document.getElementById("timelineChart");
    if (!ctx) return;

    if (this.instances.timeline) {
      this.instances.timeline.destroy();
    }

    const datasets = this.prepareTimelineData(data);

    this.instances.timeline = new Chart(ctx, {
      type: "bar",
      data: { datasets },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              generateLabels: (chart) => {
                return [
                  {
                    text: "[GREEN] Active Period",
                    fillStyle: "#22c55e",
                    strokeStyle: "#22c55e",
                    lineWidth: 2,
                  },
                  {
                    text: "[YELLOW] Moderate Downtime (3-4h)",
                    fillStyle: "#fbbf24",
                    strokeStyle: "#fbbf24",
                    lineWidth: 2,
                  },
                  {
                    text: "[RED] Severe Downtime (4-6h)",
                    fillStyle: "#ef4444",
                    strokeStyle: "#ef4444",
                    lineWidth: 2,
                  },
                  {
                    text: "[BLACK] Critical Downtime (6+h)",
                    fillStyle: "#000000",
                    strokeStyle: "#000000",
                    lineWidth: 2,
                  },
                ];
              },
            },
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const duration = (context.raw.x[1] - context.raw.x[0]) / (1000 * 60 * 60);
                if (context.dataset.label.includes("Active")) {
                  return `Active: ${utils.formatDuration(duration)} - ${context.raw.task}`;
                }
                const alertType = duration >= 6 ? "CRITICAL" : duration >= 4 ? "SEVERE" : "ALERT";
                return `[${alertType}] Downtime: ${utils.formatDuration(duration)}`;
              },
            },
          },
          annotation: {
            annotations: this.createTimelineAnnotations(data),
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "hour",
              displayFormats: { hour: "HH:mm" },
              stepSize: 1,
            },
            min: new Date(`${datePicker.getSelectedDate()}T09:00:00`).getTime(),
            max: new Date(`${datePicker.getSelectedDate()}T17:00:00`).getTime(),
            ticks: {
              callback: function (value) {
                const date = new Date(value);
                return date.getHours() + ":00";
              },
            },
            grid: {
              color: "rgba(0, 0, 0, 0.1)",
            },
          },
          y: {
            stacked: false,
            grid: { display: false },
            ticks: {
              autoSkip: false,
            },
          },
        },
      },
    });
  },

  prepareTimelineData(detailedData) {
    const datasets = [];
    const colors = {
      active: "#22c55e",
      downtime: {
        low: "#fbbf24", // Yellow: 3-4h
        medium: "#ef4444", // Red: 4-6h
        high: "#000000", // Black: 6+h
      },
    };

    // Get all team members and ensure they all appear
    const allMembers = [
      "Jan",
      "Wiktor",
      "Arif",
      "Sean Coulombe",
      "Calum Sproat-Panabaker",
      "Tricia Kennedy",
      "Kendra Richards",
      "Rick Schmaltz",
    ];

    // Create datasets for each member
    allMembers.forEach((name) => {
      const data = detailedData[name] || { in_progress_periods: [], downtime_periods: [] };

      // Active periods
      if (data.in_progress_periods && data.in_progress_periods.length > 0) {
        datasets.push({
          label: `${name} - Active`,
          data: data.in_progress_periods.map((period) => ({
            x: [new Date(period.start).getTime(), new Date(period.end).getTime()],
            y: name,
            task: period.task_name,
          })),
          backgroundColor: colors.active,
          borderColor: colors.active,
          borderWidth: 2,
          barThickness: 20,
        });
      }

      // Downtime periods with color coding
      if (data.downtime_periods && data.downtime_periods.length > 0) {
        const downtimeData = data.downtime_periods.map((period) => {
          const duration = period.duration_hours;
          let color = colors.downtime.low;
          let label = "[ALERT]";

          if (duration >= 6) {
            color = colors.downtime.high;
            label = "[CRITICAL]";
          } else if (duration >= 4) {
            color = colors.downtime.medium;
            label = "[SEVERE]";
          }

          return {
            x: [new Date(period.start).getTime(), new Date(period.end).getTime()],
            y: name,
            duration: duration,
            backgroundColor: color,
            label: label,
          };
        });

        // Add downtime bars with labels
        downtimeData.forEach((bar) => {
          datasets.push({
            label: `${name} - Downtime`,
            data: [bar],
            backgroundColor: bar.backgroundColor,
            borderColor: "#374151",
            borderWidth: 1,
            barThickness: 20,
            datalabels: {
              display: true,
              color: "white",
              font: {
                weight: "bold",
                size: 10,
              },
              formatter: () => `${bar.label} ${utils.formatDuration(bar.duration)}`,
            },
          });
        });
      }

      // If no activity at all, show empty bar
      if (
        (!data.in_progress_periods || data.in_progress_periods.length === 0) &&
        (!data.downtime_periods || data.downtime_periods.length === 0)
      ) {
        datasets.push({
          label: `${name} - No Activity`,
          data: [
            {
              x: [
                new Date(`${datePicker.getSelectedDate()}T09:00:00`).getTime(),
                new Date(`${datePicker.getSelectedDate()}T09:00:00`).getTime(),
              ],
              y: name,
            },
          ],
          backgroundColor: "transparent",
          borderWidth: 0,
          barThickness: 20,
        });
      }
    });

    return datasets;
  },

  createTimelineAnnotations(data) {
    const annotations = {};

    // Add threshold lines
    const thresholds = [
      { hours: 3, label: "3h threshold", color: "rgba(251, 191, 36, 0.5)" },
      { hours: 4, label: "4h critical", color: "rgba(239, 68, 68, 0.5)" },
      { hours: 6, label: "6h critical", color: "rgba(0, 0, 0, 0.5)" },
    ];

    return annotations;
  },

  createActivityChart(metrics) {
    const ctx = document.getElementById("activityChart");
    if (!ctx) return;

    if (this.instances.activity) {
      this.instances.activity.destroy();
    }

    this.instances.activity = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Active Time", "Downtime"],
        datasets: [
          {
            data: [metrics.total_active_hours || 0, metrics.total_downtime_hours || 0],
            backgroundColor: ["#22c55e", "#ef4444"],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 20,
              usePointStyle: true,
            },
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || "";
                const value = context.parsed || 0;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${utils.formatDuration(value)} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  },

  createTaskAgeChart(taskData) {
    const ctx = document.getElementById("taskAgeChart");
    if (!ctx) return;

    if (this.instances.taskAge) {
      this.instances.taskAge.destroy();
    }

    // Group tasks by age
    const ageGroups = {
      "0-24h": 0,
      "1-3 days": 0,
      "3-7 days": 0,
      "7+ days": 0,
    };

    // Process task data here...

    this.instances.taskAge = new Chart(ctx, {
      type: "bar",
      data: {
        labels: Object.keys(ageGroups),
        datasets: [
          {
            label: "Tasks",
            data: Object.values(ageGroups),
            backgroundColor: "#4f46e5",
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
          },
        },
      },
    });
  },

  createStatusChart(teamData) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (this.instances.status) {
      this.instances.status.destroy();
    }

    const statusCounts = {
      active: 0,
      inactive: 0,
      downtime: 0,
    };

    // Count statuses
    Object.values(teamData).forEach((member) => {
      if (member.total_active_hours > 0) {
        statusCounts.active++;
      } else {
        statusCounts.inactive++;
      }
      if (member.total_downtime_hours > 2) {
        statusCounts.downtime++;
      }
    });

    this.instances.status = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Active", "Inactive", "High Downtime"],
        datasets: [
          {
            data: Object.values(statusCounts),
            backgroundColor: ["#22c55e", "#6b7280", "#ef4444"],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: {
              padding: 10,
              usePointStyle: true,
            },
          },
        },
      },
    });
  },

  createPerformanceChart(performanceData) {
    const ctx = document.getElementById("performanceChart");
    if (!ctx) return;

    if (this.instances.performance) {
      this.instances.performance.destroy();
    }

    // Sample data - replace with actual performance metrics
    const labels = ["Mon", "Tue", "Wed", "Thu", "Fri"];
    const efficiency = [85, 78, 82, 88, 75];

    this.instances.performance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Efficiency %",
            data: efficiency,
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79, 70, 229, 0.1)",
            tension: 0.3,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: (value) => value + "%",
            },
          },
        },
      },
    });
  },

  zoomTimeline(range) {
    if (!this.instances.timeline) return;

    const chart = this.instances.timeline;
    const selectedDate = datePicker.getSelectedDate();
    let min, max;

    switch (range) {
      case "1h":
        const now = new Date();
        min = new Date(selectedDate + "T" + (now.getHours() - 1) + ":00:00").getTime();
        max = new Date(selectedDate + "T" + now.getHours() + ":00:00").getTime();
        break;
      case "4h":
        const currentHour = new Date().getHours();
        min = new Date(selectedDate + "T" + Math.max(9, currentHour - 4) + ":00:00").getTime();
        max = new Date(selectedDate + "T" + Math.min(17, currentHour + 1) + ":00:00").getTime();
        break;
      default:
        min = new Date(selectedDate + "T09:00:00").getTime();
        max = new Date(selectedDate + "T17:00:00").getTime();
    }

    chart.options.scales.x.min = min;
    chart.options.scales.x.max = max;
    chart.update();

    // Update button states
    document.querySelectorAll(".chart-actions .chart-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    event.target.classList.add("active");
  },

  updateAll(data) {
    if (data.detailed_data) {
      this.createTimelineChart(data.detailed_data);
      this.createStatusChart(data.detailed_data);
    }

    if (data.team_metrics) {
      this.createActivityChart(data.team_metrics);
    }

    // Create other charts with available data
    this.createTaskAgeChart(data);
    this.createPerformanceChart(data);
  },

  resize() {
    Object.values(this.instances).forEach((chart) => {
      if (chart) chart.resize();
    });
  },
};
