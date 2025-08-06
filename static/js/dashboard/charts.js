// Enhanced Charts module for managing all chart instances with ClickUp timeline support
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
    Chart.defaults.scale.grid.color = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
    Chart.defaults.scale.grid.borderColor = isDark ? "#334155" : "#e5e7eb";
  },

  createTimelineChart(data) {
    const ctx = document.getElementById("timelineChart");
    if (!ctx) return;

    if (this.instances.timeline) {
      this.instances.timeline.destroy();
    }

    console.log("Creating timeline chart with data:", data);

    // Prepare timeline data
    const datasets = this.prepareTimelineData(data);
    console.log("Timeline datasets:", datasets);

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
    const minTime = new Date(`${selectedDate}T09:00:00`);
    const maxTime = new Date(`${selectedDate}T18:00:00`);

    // Validate time range
    if (isNaN(minTime.getTime()) || isNaN(maxTime.getTime())) {
      console.error("Invalid date range for timeline chart");
      return;
    }

    this.instances.timeline = new Chart(ctx, {
      type: "scatter",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
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
              title: function (context) {
                const point = context[0];
                return point.dataset.memberName || "Unknown Member";
              },
              label: function (context) {
                const data = context.raw;
                if (!data) return "";

                const start = new Date(data.x);
                const end = new Date(data.x2);
                const duration = (data.x2 - data.x) / (1000 * 60 * 60); // Convert to hours

                let label = `Duration: ${utils.formatDuration(duration)}`;
                if (data.task) {
                  label += `\nTask: ${data.task}`;
                }
                if (data.type) {
                  label += `\nType: ${data.type}`;
                }
                label += `\nTime: ${utils.formatTime(start)} - ${utils.formatTime(end)}`;

                return label;
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "hour",
              displayFormats: {
                hour: "HH:mm",
              },
              stepSize: 1,
            },
            min: minTime.getTime(),
            max: maxTime.getTime(),
            grid: {
              display: true,
              drawBorder: false,
            },
            ticks: {
              maxRotation: 0,
              callback: function (value) {
                const date = new Date(value);
                return date.getHours().toString().padStart(2, "0") + ":00";
              },
            },
            title: {
              display: true,
              text: "Time of Day",
            },
          },
          y: {
            type: "category",
            labels: this.getMemberNames(data),
            grid: {
              display: false,
              drawBorder: false,
            },
            ticks: {
              padding: 8,
            },
            title: {
              display: true,
              text: "Team Members",
            },
          },
        },
        onHover: (event, activeElements) => {
          event.native.target.style.cursor = activeElements.length > 0 ? "pointer" : "default";
        },
      },
    });
  },

  getMemberNames(detailedData) {
    return Object.keys(detailedData || {});
  },

  prepareTimelineData(detailedData) {
    const datasets = [];
    const colors = {
      active: "#10b981",
      downtime: "#ef4444",
      warning: "#f59e0b",
    };

    // Get all team members
    const members = Object.keys(detailedData || {});
    console.log("Processing members:", members);

    if (members.length === 0) {
      return datasets;
    }

    members.forEach((memberName, memberIndex) => {
      const memberData = detailedData[memberName];
      console.log(`Processing ${memberName}:`, memberData);

      // Active periods
      if (memberData.in_progress_periods && memberData.in_progress_periods.length > 0) {
        const activeData = [];

        memberData.in_progress_periods.forEach((period) => {
          try {
            const startTime = new Date(period.start);
            const endTime = new Date(period.end);

            if (!isNaN(startTime.getTime()) && !isNaN(endTime.getTime())) {
              activeData.push({
                x: startTime.getTime(),
                y: memberName,
                x2: endTime.getTime(),
                task: period.task_name || "Task",
                duration: period.duration_hours || 0,
                status: period.status || "active",
              });
            }
          } catch (error) {
            console.warn(`Error processing active period for ${memberName}:`, error, period);
          }
        });

        if (activeData.length > 0) {
          datasets.push({
            label: `${memberName} - Active`,
            memberName: memberName,
            data: activeData,
            backgroundColor: colors.active,
            borderColor: colors.active,
            borderWidth: 0,
            pointRadius: (context) => {
              const data = context.raw;
              const duration = (data.x2 - data.x) / (1000 * 60 * 60); // hours
              return Math.max(8, Math.min(20, duration * 3)); // Scale point size with duration
            },
            pointHoverRadius: (context) => {
              const data = context.raw;
              const duration = (data.x2 - data.x) / (1000 * 60 * 60);
              return Math.max(10, Math.min(25, duration * 3 + 2));
            },
            showLine: false,
          });
        }
      }

      // Downtime periods
      if (memberData.downtime_periods && memberData.downtime_periods.length > 0) {
        const downtimeData = [];

        memberData.downtime_periods.forEach((period) => {
          try {
            const startTime = new Date(period.start);
            const endTime = new Date(period.end);

            if (!isNaN(startTime.getTime()) && !isNaN(endTime.getTime())) {
              // Choose color based on duration
              let color = colors.downtime;
              if (period.duration_hours < 2) {
                color = colors.warning;
              }

              downtimeData.push({
                x: startTime.getTime(),
                y: memberName,
                x2: endTime.getTime(),
                duration: period.duration_hours || 0,
                type: period.type || "downtime",
                color: color,
              });
            }
          } catch (error) {
            console.warn(`Error processing downtime period for ${memberName}:`, error, period);
          }
        });

        if (downtimeData.length > 0) {
          datasets.push({
            label: `${memberName} - Downtime`,
            memberName: memberName,
            data: downtimeData,
            backgroundColor: (context) => {
              return context.raw?.color || colors.downtime;
            },
            borderColor: colors.downtime,
            borderWidth: 0,
            pointRadius: (context) => {
              const data = context.raw;
              const duration = (data.x2 - data.x) / (1000 * 60 * 60);
              return Math.max(6, Math.min(18, duration * 2));
            },
            pointHoverRadius: (context) => {
              const data = context.raw;
              const duration = (data.x2 - data.x) / (1000 * 60 * 60);
              return Math.max(8, Math.min(22, duration * 2 + 2));
            },
            showLine: false,
          });
        }
      }

      // If no activity at all, show a placeholder
      const hasActivity =
        (memberData.in_progress_periods && memberData.in_progress_periods.length > 0) ||
        (memberData.downtime_periods && memberData.downtime_periods.length > 0);

      if (!hasActivity) {
        const selectedDate = window.datePicker
          ? datePicker.getSelectedDate()
          : new Date().toISOString().split("T")[0];
        const dayStart = new Date(`${selectedDate}T09:00:00`).getTime();

        datasets.push({
          label: `${memberName} - No Data`,
          memberName: memberName,
          data: [
            {
              x: dayStart,
              y: memberName,
              x2: dayStart,
              type: "no_data",
            },
          ],
          backgroundColor: "#9ca3af",
          borderColor: "#9ca3af",
          borderWidth: 0,
          pointRadius: 4,
          showLine: false,
        });
      }
    });

    console.log("Final datasets:", datasets);
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
    const expectedHours = metrics.expected_working_hours || 0;

    console.log("Activity chart data:", { activeHours, downtimeHours, expectedHours });

    // Create a doughnut chart showing active vs downtime vs remaining expected
    const remainingHours = Math.max(0, expectedHours - activeHours - downtimeHours);

    this.instances.activity = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Active Hours", "Downtime Hours", "Remaining Expected"],
        datasets: [
          {
            data: [activeHours, downtimeHours, remainingHours],
            backgroundColor: ["#10b981", "#ef4444", "#6b7280"],
            borderWidth: 2,
            borderColor: "#ffffff",
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
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const value = context.parsed || 0;
                const total = activeHours + downtimeHours + remainingHours;
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return `${context.label}: ${value.toFixed(1)}h (${percentage}%)`;
              },
            },
          },
        },
        cutout: "60%",
      },
    });
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
      active: data.total_active_hours || 0,
      downtime: data.total_downtime_hours || 0,
      tasks: data.total_tasks || 0,
    }));

    // Sort by total activity (active hours - downtime hours)
    members.sort((a, b) => b.active - b.downtime - (a.active - a.downtime));

    this.instances.memberStatus = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members.map((m) => m.name),
        datasets: [
          {
            label: "Active Hours",
            data: members.map((m) => m.active),
            backgroundColor: "#10b981",
            borderRadius: 4,
          },
          {
            label: "Downtime Hours",
            data: members.map((m) => m.downtime),
            backgroundColor: "#ef4444",
            borderRadius: 4,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
          tooltip: {
            callbacks: {
              afterBody: (context) => {
                const memberIndex = context[0].dataIndex;
                const member = members[memberIndex];
                return `Tasks: ${member.tasks}`;
              },
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            stacked: false,
            ticks: {
              callback: (value) => value + "h",
            },
            grid: {
              display: true,
            },
          },
          y: {
            stacked: false,
            grid: {
              display: false,
            },
          },
        },
      },
    });
  },

  createStatusChart(detailedData) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (this.instances.status) {
      this.instances.status.destroy();
    }

    const members = Object.keys(detailedData || {});
    if (members.length === 0) {
      ctx.parentElement.innerHTML = '<div class="no-data-message">No status data available</div>';
      return;
    }

    let goodCount = 0,
      warningCount = 0,
      criticalCount = 0;

    members.forEach((member) => {
      const memberData = detailedData[member];
      const totalDowntime = memberData.total_downtime_hours || 0;

      if (totalDowntime >= 4) {
        criticalCount++;
      } else if (totalDowntime >= 2) {
        warningCount++;
      } else {
        goodCount++;
      }
    });

    this.instances.status = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Good (< 2h downtime)", "Warning (2-4h downtime)", "Critical (4h+ downtime)"],
        datasets: [
          {
            data: [goodCount, warningCount, criticalCount],
            backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
            borderWidth: 2,
            borderColor: "#ffffff",
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
              padding: 15,
              usePointStyle: true,
            },
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const value = context.raw;
                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                return `${context.label}: ${value} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  },

  createTaskDistributionChart(detailedData) {
    const ctx = document.getElementById("taskDistributionChart");
    if (!ctx) return;

    if (this.instances.taskDistribution) {
      this.instances.taskDistribution.destroy();
    }

    const members = Object.entries(detailedData).map(([name, data]) => ({
      name,
      activeTasks: data.active_tasks || 0,
      totalTasks: data.total_tasks || 0,
    }));

    members.sort((a, b) => b.totalTasks - a.totalTasks);

    this.instances.taskDistribution = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members.map((m) => m.name),
        datasets: [
          {
            label: "Active Tasks",
            data: members.map((m) => m.activeTasks),
            backgroundColor: "#3b82f6",
            borderRadius: 4,
          },
          {
            label: "Total Tasks",
            data: members.map((m) => m.totalTasks),
            backgroundColor: "#e5e7eb",
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
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

  updateAll(data) {
    console.log("Updating all charts with data:", data);

    if (data.detailed_data) {
      this.createTimelineChart(data.detailed_data);
      this.createStatusChart(data.detailed_data);
      this.createMemberStatusChart(data.detailed_data);
      this.createTaskDistributionChart(data.detailed_data);
    }

    if (data.team_metrics) {
      this.createActivityChart(data.team_metrics);
    }
  },

  zoomTimeline(range) {
    if (!this.instances.timeline) return;

    const chart = this.instances.timeline;
    const selectedDate = window.datePicker
      ? datePicker.getSelectedDate()
      : new Date().toISOString().split("T")[0];
    let min, max;

    switch (range) {
      case "hour":
        const now = new Date();
        min = new Date(
          `${selectedDate}T${(now.getHours() - 1).toString().padStart(2, "0")}:00:00`
        ).getTime();
        max = new Date(
          `${selectedDate}T${now.getHours().toString().padStart(2, "0")}:59:59`
        ).getTime();
        break;
      case "morning":
        min = new Date(`${selectedDate}T09:00:00`).getTime();
        max = new Date(`${selectedDate}T12:00:00`).getTime();
        break;
      case "afternoon":
        min = new Date(`${selectedDate}T13:00:00`).getTime();
        max = new Date(`${selectedDate}T18:00:00`).getTime();
        break;
      default:
        min = new Date(`${selectedDate}T09:00:00`).getTime();
        max = new Date(`${selectedDate}T18:00:00`).getTime();
    }

    chart.options.scales.x.min = min;
    chart.options.scales.x.max = max;
    chart.update();

    // Update button states
    document.querySelectorAll(".chart-actions .chart-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    if (event && event.target) {
      event.target.classList.add("active");
    }
  },

  resize() {
    Object.values(this.instances).forEach((chart) => {
      if (chart) chart.resize();
    });
  },

  destroy() {
    Object.values(this.instances).forEach((chart) => {
      if (chart) chart.destroy();
    });
    this.instances = {};
  },
};
