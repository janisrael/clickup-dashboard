class ChartManager {
  constructor() {
    this.charts = {};
  }

  renderAll(data) {
    this.renderTimelineChart(data);
    this.renderActivityChart(data);
    this.renderStatusChart(data);
    this.renderTaskAgeChart(data);
    this.renderMilestoneChart(data);
  }

  renderTimelineChart(data) {
    const ctx = document.getElementById("timelineChart");
    if (!ctx) return;

    if (this.charts.timeline) {
      this.charts.timeline.destroy();
    }

    const members = Object.keys(data.detailed_data || {});
    if (members.length === 0) {
      this.drawNoDataMessage(ctx, "No timeline data available");
      return;
    }

    const datasets = [];

    members.forEach((member, index) => {
      const memberData = data.detailed_data[member];

      // Active periods
      (memberData.in_progress_periods || []).forEach((period) => {
        const start = new Date(period.start);
        const end = new Date(period.end);

        datasets.push({
          label: `${member} - Active`,
          data: [
            {
              x: start.getTime(),
              y: index,
              x2: end.getTime(),
              duration: period.duration_hours,
              task: period.task_name,
              taskAge: period.task_age,
              isMilestone: period.is_milestone,
            },
          ],
          backgroundColor: window.dashboard.colors.success,
          borderColor: window.dashboard.colors.success,
          borderWidth: 6,
          pointRadius: 0,
          showLine: false,
        });
      });

      // Downtime periods
      (memberData.downtime_periods || []).forEach((period) => {
        const start = new Date(period.start);
        const end = new Date(period.end);

        datasets.push({
          label: `${member} - Downtime`,
          data: [
            {
              x: start.getTime(),
              y: index,
              x2: end.getTime(),
              duration: period.duration_hours,
              type: period.type,
            },
          ],
          backgroundColor: window.dashboard.colors.danger,
          borderColor: window.dashboard.colors.danger,
          borderWidth: 6,
          pointRadius: 0,
          showLine: false,
        });
      });
    });

    this.charts.timeline = new Chart(ctx, {
      type: "scatter",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "time",
            time: {
              unit: "hour",
              displayFormats: {
                hour: "HH:mm",
              },
            },
            title: {
              display: true,
              text: "Time of Day",
            },
            min: new Date(data.date + "T08:00:00").getTime(),
            max: new Date(data.date + "T18:00:00").getTime(),
          },
          y: {
            type: "linear",
            position: "left",
            min: -0.5,
            max: members.length - 0.5,
            ticks: {
              callback: function (value) {
                return members[Math.round(value)] || "";
              },
              stepSize: 1,
            },
            title: {
              display: true,
              text: "Team Members",
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              title: function (context) {
                return context[0].dataset.label;
              },
              label: function (context) {
                const data = context.raw;
                let label = `Duration: ${data.duration?.toFixed(1) || 0} hours`;

                if (data.task) {
                  label += `\nTask: ${data.task}`;
                  if (data.taskAge) {
                    label += `\nAge: ${data.taskAge} days`;
                  }
                  if (data.isMilestone) {
                    label += `\nMilestone Task`;
                  }
                }
                if (data.type) {
                  label += `\nType: ${data.type}`;
                }
                return label;
              },
            },
          },
        },
      },
    });
  }

  renderActivityChart(data) {
    const ctx = document.getElementById("activityChart");
    if (!ctx) return;

    if (this.charts.activity) {
      this.charts.activity.destroy();
    }

    const members = Object.keys(data.detailed_data || {});
    if (members.length === 0) {
      this.drawNoDataMessage(ctx, "No activity data available");
      return;
    }

    const activeHours = members.map((member) => {
      const memberData = data.detailed_data[member];
      return (memberData.in_progress_periods || []).reduce((sum, period) => {
        let duration = period.duration_hours;

        if (duration === undefined && period.start && period.end) {
          const start = new Date(period.start);
          const end = new Date(period.end);
          duration = (end - start) / (1000 * 60 * 60);
        }

        return sum + Math.abs(duration || 0);
      }, 0);
    });

    const downtimeHours = members.map((member) => {
      const memberData = data.detailed_data[member];
      return (memberData.downtime_periods || []).reduce(
        (sum, period) => sum + (period.duration_hours || 0),
        0
      );
    });

    this.charts.activity = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members,
        datasets: [
          {
            label: "Active Hours",
            data: activeHours,
            backgroundColor: window.dashboard.colors.success,
            borderColor: window.dashboard.colors.success,
            borderWidth: 1,
          },
          {
            label: "Downtime Hours",
            data: downtimeHours,
            backgroundColor: window.dashboard.colors.danger,
            borderColor: window.dashboard.colors.danger,
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: false,
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Hours",
            },
          },
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `${context.dataset.label}: ${context.raw.toFixed(1)} hours`;
              },
            },
          },
        },
      },
    });
  }

  renderStatusChart(data) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (this.charts.status) {
      this.charts.status.destroy();
    }

    const members = Object.keys(data.detailed_data || {});
    if (members.length === 0) {
      this.drawNoDataMessage(ctx, "No status data available");
      return;
    }

    let goodCount = 0,
      warningCount = 0,
      criticalCount = 0;

    members.forEach((member) => {
      const memberData = data.detailed_data[member];
      const totalDowntime = (memberData.downtime_periods || []).reduce(
        (sum, period) => sum + (period.duration_hours || 0),
        0
      );

      if (totalDowntime >= 4) criticalCount++;
      else if (totalDowntime >= 3) warningCount++;
      else goodCount++;
    });

    ctx.style.height = "400px";
    ctx.height = 400;

    this.charts.status = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Good", "Warning", "Critical"],
        datasets: [
          {
            data: [goodCount, warningCount, criticalCount],
            backgroundColor: [
              window.dashboard.colors.success,
              window.dashboard.colors.warning,
              window.dashboard.colors.danger,
            ],
            borderWidth: 2,
            borderColor: ctx.style.backgroundColor || "#fff",
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
              boxWidth: 12,
            },
          },
        },
        layout: {
          padding: {
            top: 20,
            bottom: 20,
            left: 20,
            right: 20,
          },
        },
      },
    });
  }

  renderTaskAgeChart(data) {
    const ctx = document.getElementById("taskAgeChart");
    if (!ctx) return;

    if (this.charts.taskAge) {
      this.charts.taskAge.destroy();
    }

    const members = Object.keys(data.detailed_data || {});
    if (members.length === 0) {
      this.drawNoDataMessage(ctx, "No task data available");
      return;
    }

    let veryOld = 0,
      old = 0,
      moderate = 0,
      newTasks = 0;

    members.forEach((member) => {
      const memberData = data.detailed_data[member];
      veryOld += memberData.task_metrics?.tasks_by_age?.very_old || 0;
      old += memberData.task_metrics?.tasks_by_age?.old || 0;
      moderate += memberData.task_metrics?.tasks_by_age?.moderate || 0;
      newTasks += memberData.task_metrics?.tasks_by_age?.new || 0;
    });

    this.charts.taskAge = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Very Old (14+ days)", "Old (7-14 days)", "Moderate (3-7 days)", "New (<3 days)"],
        datasets: [
          {
            data: [veryOld, old, moderate, newTasks],
            backgroundColor: [
              window.dashboard.colors.veryOld,
              window.dashboard.colors.old,
              window.dashboard.colors.moderate,
              window.dashboard.colors.new,
            ],
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Number of Tasks",
            },
          },
          x: {
            grid: {
              display: false,
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });

    const taskAgeList = document.getElementById("taskAgeList");
    taskAgeList.innerHTML = `
            <div class="task-age-item">
                <div class="task-age-label">
                    <span class="task-age-badge badge-very-old"></span>
                    <span>Very Old Tasks</span>
                </div>
                <span>${veryOld}</span>
            </div>
            <div class="task-age-item">
                <div class="task-age-label">
                    <span class="task-age-badge badge-old"></span>
                    <span>Old Tasks</span>
                </div>
                <span>${old}</span>
            </div>
            <div class="task-age-item">
                <div class="task-age-label">
                    <span class="task-age-badge badge-moderate"></span>
                    <span>Moderate Tasks</span>
                </div>
                <span>${moderate}</span>
            </div>
            <div class="task-age-item">
                <div class="task-age-label">
                    <span class="task-age-badge badge-new"></span>
                    <span>New Tasks</span>
                </div>
                <span>${newTasks}</span>
            </div>
        `;
  }

  renderMilestoneChart(data) {
    const ctx = document.getElementById("milestoneChart");
    if (!ctx) return;

    if (this.charts.milestone) {
      this.charts.milestone.destroy();
    }

    const members = Object.keys(data.detailed_data || {});
    if (members.length === 0) {
      this.drawNoDataMessage(ctx, "No milestone data available");
      return;
    }

    let milestoneTasks = 0;
    let totalTasks = 0;

    members.forEach((member) => {
      const memberData = data.detailed_data[member];
      milestoneTasks += memberData.task_metrics?.milestone_tasks || 0;
      totalTasks += memberData.task_metrics?.total_tasks || 0;
    });

    this.charts.milestone = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Milestone Tasks", "Regular Tasks"],
        datasets: [
          {
            data: [milestoneTasks, totalTasks - milestoneTasks],
            backgroundColor: [window.dashboard.colors.milestone, "#e5e7eb"],
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
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

    const milestoneStats = document.getElementById("milestoneStats");
    if (milestoneTasks > 0) {
      milestoneStats.innerHTML = `
                <div style="font-size: 0.9rem;">
                    <strong>${milestoneTasks}</strong> milestone tasks out of <strong>${totalTasks}</strong> total tasks
                </div>
            `;
    } else {
      milestoneStats.innerHTML = `
                <div style="font-size: 0.9rem; color: #6b7280;">
                    No milestone tasks found
                </div>
            `;
    }
  }

  updateTheme() {
    Object.values(this.charts).forEach((chart) => {
      if (chart && chart.options?.scales) {
        const gridColor =
          document.documentElement.getAttribute("data-theme") === "dark"
            ? "rgba(255, 255, 255, 0.1)"
            : "rgba(0, 0, 0, 0.1)";

        if (chart.options.scales.x) chart.options.scales.x.grid.color = gridColor;
        if (chart.options.scales.y) chart.options.scales.y.grid.color = gridColor;
        chart.update();
      }
    });
  }

  resizeAll() {
    Object.values(this.charts).forEach((chart) => {
      if (chart) chart.resize();
    });
  }

  drawNoDataMessage(canvas, message) {
    const ctx = canvas.getContext("2d");
    ctx.font = "16px Arial";
    ctx.textAlign = "center";
    ctx.fillStyle =
      document.documentElement.getAttribute("data-theme") === "dark" ? "#ffffff" : "#666666";
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
  }
}
