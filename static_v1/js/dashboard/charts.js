// Charts module for managing all chart instances
window.charts = {
  instances: {},

  init() {
    // Set chart defaults for modern look
    Chart.defaults.font.family =
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue(
      "--text-secondary"
    );
    Chart.defaults.borderColor = getComputedStyle(document.documentElement).getPropertyValue(
      "--border-color"
    );

    // Update defaults when theme changes
    this.updateChartDefaults();
  },

  updateChartDefaults() {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";

    Chart.defaults.color = isDark ? "#cbd5e1" : "#6b7280";
    Chart.defaults.borderColor = isDark ? "#334155" : "#e5e7eb";
    Chart.defaults.plugins.legend.labels.color = isDark ? "#cbd5e1" : "#6b7280";

    // Grid styling
    Chart.defaults.scale.grid.color = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
    Chart.defaults.scale.grid.borderColor = isDark ? "#334155" : "#e5e7eb";
  },

  createTimelineChart(data) {
    const ctx = document.getElementById("timelineChart");
    if (!ctx) return;

    if (this.instances.timeline) {
      this.instances.timeline.destroy();
    }

    const datasets = this.prepareTimelineData(data);

    // If no datasets, show a message
    if (datasets.length === 0) {
      ctx.parentElement.innerHTML =
        '<div class="no-data-message">No activity data available for the selected date</div>';
      return;
    }

    // Get the selected date for the scale
    const selectedDate = window.datePicker
      ? datePicker.getSelectedDate()
      : new Date().toISOString().split("T")[0];
    const minTime = new Date(`${selectedDate}T09:00:00`).getTime();
    const maxTime = new Date(`${selectedDate}T17:00:00`).getTime();

    // Validate time range
    if (isNaN(minTime) || isNaN(maxTime)) {
      console.error("Invalid date range for timeline chart");
      return;
    }

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
              usePointStyle: true,
              padding: 20,
              generateLabels: (chart) => {
                return [
                  {
                    text: "Active Period",
                    fillStyle: "#10b981",
                    strokeStyle: "#10b981",
                    lineWidth: 0,
                    pointStyle: "rect",
                  },
                  {
                    text: "Downtime",
                    fillStyle: "#ef4444",
                    strokeStyle: "#ef4444",
                    lineWidth: 0,
                    pointStyle: "rect",
                  },
                ];
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                if (!context.raw || !context.raw.x) return "";
                const duration = (context.raw.x[1] - context.raw.x[0]) / (1000 * 60 * 60);
                if (context.dataset.label && context.dataset.label.includes("Active")) {
                  return `Active: ${utils.formatDuration(duration)} - ${
                    context.raw.task || "Task"
                  }`;
                }
                return `Downtime: ${utils.formatDuration(duration)}`;
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "hour",
              displayFormats: { hour: "HH:mm" },
              stepSize: 2,
            },
            min: minTime,
            max: maxTime,
            grid: {
              display: true,
              drawBorder: false,
            },
            ticks: {
              maxRotation: 0,
              callback: function (value) {
                const date = new Date(value);
                return date.getHours() + ":00";
              },
            },
          },
          y: {
            grid: {
              display: false,
              drawBorder: false,
            },
            ticks: {
              padding: 8,
            },
          },
        },
      },
    });
  },

  prepareTimelineData(detailedData) {
    const datasets = [];
    const colors = {
      active: "#10b981",
      downtime: "#ef4444",
    };

    // Get all team members
    const allMembers = Object.keys(detailedData);

    // If no data, return empty datasets
    if (allMembers.length === 0) {
      return datasets;
    }

    // Get the selected date for default time range
    const selectedDate = window.datePicker
      ? datePicker.getSelectedDate()
      : new Date().toISOString().split("T")[0];
    const defaultStart = new Date(`${selectedDate}T09:00:00`).getTime();
    const defaultEnd = new Date(`${selectedDate}T17:00:00`).getTime();

    // Create datasets for each member
    allMembers.forEach((name) => {
      const data = detailedData[name] || { in_progress_periods: [], downtime_periods: [] };

      // Active periods
      if (data.in_progress_periods && data.in_progress_periods.length > 0) {
        const validPeriods = data.in_progress_periods.filter((period) => {
          const start = new Date(period.start).getTime();
          const end = new Date(period.end).getTime();
          return !isNaN(start) && !isNaN(end) && start > 0 && end > 0;
        });

        if (validPeriods.length > 0) {
          datasets.push({
            label: `${name} - Active`,
            data: validPeriods.map((period) => ({
              x: [new Date(period.start).getTime(), new Date(period.end).getTime()],
              y: name,
              task: period.task_name || "Task",
            })),
            backgroundColor: colors.active,
            borderColor: colors.active,
            borderWidth: 0,
            barThickness: 20,
          });
        }
      }

      // Downtime periods
      if (data.downtime_periods && data.downtime_periods.length > 0) {
        const validDowntime = data.downtime_periods.filter((period) => {
          const start = new Date(period.start).getTime();
          const end = new Date(period.end).getTime();
          return !isNaN(start) && !isNaN(end) && start > 0 && end > 0;
        });

        if (validDowntime.length > 0) {
          datasets.push({
            label: `${name} - Downtime`,
            data: validDowntime.map((period) => ({
              x: [new Date(period.start).getTime(), new Date(period.end).getTime()],
              y: name,
              duration: period.duration_hours || 0,
            })),
            backgroundColor: colors.downtime,
            borderColor: colors.downtime,
            borderWidth: 0,
            barThickness: 20,
          });
        }
      }

      // If no activity at all, create a placeholder
      if (
        (!data.in_progress_periods || data.in_progress_periods.length === 0) &&
        (!data.downtime_periods || data.downtime_periods.length === 0)
      ) {
        datasets.push({
          label: `${name} - No Activity`,
          data: [
            {
              x: [defaultStart, defaultStart],
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

  createActivityChart(metrics) {
    const ctx = document.getElementById("activityChart");
    if (!ctx) return;

    if (this.instances.activity) {
      this.instances.activity.destroy();
    }

    const activeHours = metrics.total_active_hours || 0;
    const downtimeHours = metrics.total_downtime_hours || 0;

    this.instances.activity = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Active Hours", "Downtime Hours"],
        datasets: [
          {
            data: [activeHours, downtimeHours],
            backgroundColor: ["#10b981", "#ef4444"],
            borderWidth: 0,
            borderRadius: 8,
            barThickness: 80,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const value = context.parsed.y || 0;
                const total = activeHours + downtimeHours;
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return `${context.label}: ${value.toFixed(1)}h (${percentage}%)`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              display: true,
              drawBorder: false,
            },
            ticks: {
              callback: (value) => `${value}h`,
            },
          },
          x: {
            grid: {
              display: false,
              drawBorder: false,
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
      this.createMemberStatusChart(data.detailed_data);
      this.createActivityTrendChart(data.detailed_data);
    }

    if (data.team_metrics) {
      this.createActivityChart(data.team_metrics);
    }
  },

  createMemberStatusChart(detailedData) {
    const ctx = document.getElementById("memberStatusChart");
    if (!ctx) return;

    if (this.instances.memberStatus) {
      this.instances.memberStatus.destroy();
    }

    // Prepare data for horizontal bar chart
    const members = Object.entries(detailedData).map(([name, data]) => ({
      name,
      downtime: data.total_downtime_hours || 0,
    }));

    // Sort by downtime
    members.sort((a, b) => b.downtime - a.downtime);

    this.instances.memberStatus = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members.map((m) => m.name),
        datasets: [
          {
            label: "Downtime Hours",
            data: members.map((m) => m.downtime),
            backgroundColor: (context) => {
              const value = context.parsed.x || context.parsed.y;
              if (value >= 6) return "#000000";
              if (value >= 4) return "#ef4444";
              if (value >= 3) return "#f59e0b";
              return "#22c55e";
            },
            borderWidth: 0,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                return `Downtime: ${utils.formatDuration(context.parsed.x)}`;
              },
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            max: 8,
            ticks: {
              callback: (value) => value + "h",
            },
            grid: {
              display: true,
            },
          },
          y: {
            grid: { display: false },
          },
        },
      },
    });
  },

  createActivityTrendChart(detailedData) {
    const ctx = document.getElementById("activityTrendChart");
    if (!ctx) return;

    if (this.instances.activityTrend) {
      this.instances.activityTrend.destroy();
    }

    // Create hourly distribution data
    const hourlyData = new Array(24).fill(0);

    Object.values(detailedData).forEach((member) => {
      if (member.in_progress_periods) {
        member.in_progress_periods.forEach((period) => {
          const startHour = new Date(period.start).getHours();
          const endHour = new Date(period.end).getHours();

          for (let h = startHour; h <= endHour && h < 24; h++) {
            hourlyData[h]++;
          }
        });
      }
    });

    // Focus on work hours (9-17)
    const workHours = hourlyData.slice(9, 18);
    const labels = Array.from({ length: 9 }, (_, i) => `${i + 9}:00`);

    this.instances.activityTrend = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Active Members",
            data: workHours,
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
            ticks: {
              stepSize: 1,
            },
          },
        },
      },
    });
  },

  resize() {
    Object.values(this.instances).forEach((chart) => {
      if (chart) chart.resize();
    });
  },
};
