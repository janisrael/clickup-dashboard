// Enhanced Dashboard v2 JavaScript - With Working Hours Support

window.dashboardV2 = {
  currentData: null,
  charts: {},
  refreshInterval: null,
  workingConfig: null,

  // Color scheme matching the PNG
  colors: {
    active: "#28a745",
    downtime: "#dc3545",
    warning: "#ffc107",
    info: "#17a2b8",
    critical: "#6c757d",
    primary: "#007bff",
    lunch: "#1E1E1E",
  },

  init() {
    console.log("Dashboard v2 initializing with working hours support...");
    this.setupEventListeners();
    this.loadData();
    this.startAutoRefresh();
  },

  setupEventListeners() {
    // Refresh button
    document.getElementById("refreshBtn").addEventListener("click", () => {
      this.loadData();
    });

    // Export button
    document.getElementById("exportBtn").addEventListener("click", () => {
      this.exportData();
    });

    // Retry button (in error state)
    document.getElementById("retryBtn").addEventListener("click", () => {
      this.loadData();
    });
  },

  async loadData() {
    this.showLoading();

    try {
      console.log("Attempting to load data from /api/dashboard-data");
      const response = await fetch("/api/dashboard-data");

      if (!response.ok) {
        // Try to get more details from the error response
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.details) {
            errorMessage += ` - ${errorData.details}`;
          }
        } catch (e) {
          // If we can't parse the error response, just use the status
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("Received data:", data);
      this.currentData = data;

      // Update header info
      this.updateHeader(data);

      // Create all visualizations
      this.createAllCharts(data);

      this.showDashboard();
      console.log("Dashboard data loaded successfully");
    } catch (error) {
      console.error("Error loading data:", error);
      this.showError(error.message);
    }
  },

  updateHeader(data) {
    document.getElementById("currentDate").textContent = `📅 ${data.date || "N/A"}`;
    document.getElementById(
      "lastUpdate"
    ).textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  },

  createAllCharts(data) {
    console.log("Creating charts with working hours data:", data);

    // Store working configuration
    this.workingConfig = data.metrics?.working_config || {
      start_hour: 9,
      end_hour: 17,
      lunch_start: 12,
      lunch_end: 12.5,
      daily_hours: 7.5,
    };

    // Destroy existing charts
    Object.values(this.charts).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") {
        chart.destroy();
      }
    });
    this.charts = {};

    // Create all visualizations
    this.createTimelineChart(data);
    this.createStatusChart(data);
    this.createProductivityChart(data);
    this.createHeatmapGrid(data);
    this.populateStatsPanel(data);
    this.populateAlertsPanel(data);
  },

  //   createTimelineChart(data) {
  //     const ctx = document.getElementById("timelineChart").getContext("2d");
  //     const detailedData = data.detailed_data || {};
  //     const members = Object.keys(detailedData);
  //     const config = this.workingConfig;

  //     // Simplify to use one lane per member for better alignment
  //     const datasets = [];

  //     // Working hours boundaries
  //     const workStart = new Date();
  //     workStart.setHours(config.start_hour, 0, 0, 0);
  //     const lunchStart = new Date();
  //     lunchStart.setHours(Math.floor(config.lunch_start), (config.lunch_start % 1) * 60, 0, 0);
  //     const lunchEnd = new Date();
  //     lunchEnd.setHours(Math.floor(config.lunch_end), (config.lunch_end % 1) * 60, 0, 0);
  //     const workEnd = new Date();
  //     // workEnd.setHours(config.end_hour, 0, 0, 0);
  //     workEnd.setHours(17, 0, 0, 0);

  //     // Add lunch break indicators for all members (background layer)
  //     members.forEach((member, memberIndex) => {
  //       datasets.push({
  //         label: `Lunch Break`,
  //         data: [
  //           {
  //             x: [lunchStart, lunchEnd],
  //             y: memberIndex,
  //           },
  //         ],
  //         backgroundColor: this.colors.lunch,
  //         borderColor: "#1E1E1E",
  //         borderWidth: 1,
  //         barThickness: 40,
  //         categoryPercentage: 0.8,
  //         type: "bar",
  //         order: 3, // Behind other bars
  //       });
  //     });

  //     // Add tasks with offset positioning for multiple tasks
  //     members.forEach((member, memberIndex) => {
  //       const memberData = detailedData[member];
  //       let taskOffset = 0; // Vertical offset for multiple tasks

  //       // Active periods (green bars) - stack them with small offsets
  //       if (memberData.in_progress_periods) {
  //         memberData.in_progress_periods.forEach((period, taskIndex) => {
  //           const startTime = new Date(period.start);

  //           const now = new Date();
  //           const workEnd2 = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 17, 0, 0, 0);
  //           const endTime = workEnd2;

  //           // Calculate y position with small offset for visual separation
  //           const yPosition = memberIndex + taskIndex * 0.3;
  //           //   const yPosition = memberIndex + taskIndex * 0.2 - 0.1;
  //           datasets.push({
  //             label: `${member} - ${period.task_name}`,
  //             data: [
  //               {
  //                 x: [startTime, endTime],
  //                 y: yPosition,
  //               },
  //             ],
  //             backgroundColor: this.colors.active,
  //             borderColor: "darkgreen",
  //             borderWidth: 1,
  //             barThickness: 12, // Thinner bars for stacking
  //             categoryPercentage: 0.9,
  //             type: "bar",
  //             order: 1, // On top
  //           });
  //         });
  //       }

  //       // Downtime periods (red/yellow bars) - stack below active tasks
  //       if (memberData.downtime_periods) {
  //         memberData.downtime_periods.forEach((period, downtimeIndex) => {
  //           const startTime = new Date(period.start);
  //           const now = new Date();
  //           const workEnd2 = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 17, 0, 0, 0);
  //           //   const endTime = new Date(period.end);
  //           const endTime = workEnd2;
  //           const duration = period.duration_hours;

  //           let color = this.colors.warning;
  //           if (duration >= 3) color = this.colors.critical;
  //           else if (duration >= 2) color = this.colors.downtime;

  //           // Position downtime below active tasks
  //           const activeTaskCount = memberData.in_progress_periods
  //             ? memberData.in_progress_periods.length
  //             : 0;
  //           //   const yPosition = memberIndex + (activeTaskCount + downtimeIndex) * 0.2 + 0.1;
  //           const yPosition = memberIndex + downtimeIndex - -0.4;

  //           datasets.push({
  //             label: `${member} - Downtime (${duration.toFixed(1)}h)`,
  //             data: [
  //               {
  //                 x: [startTime, endTime],
  //                 y: yPosition,
  //               },
  //             ],
  //             backgroundColor: color,
  //             borderColor: "darkred",
  //             borderWidth: 1,
  //             barThickness: 12,
  //             categoryPercentage: 0.9,
  //             type: "bar",
  //             order: 2, // Middle layer
  //           });
  //         });
  //       }
  //     });

  //     this.charts.timeline = new Chart(ctx, {
  //       type: "bar",
  //       data: { datasets },
  //       options: {
  //         indexAxis: "y",
  //         responsive: true,
  //         maintainAspectRatio: false,
  //         plugins: {
  //           legend: { display: false },
  //           tooltip: {
  //             callbacks: {
  //               title: function (context) {
  //                 return context[0].dataset.label;
  //               },
  //               label: function (context) {
  //                 const data = context.raw;
  //                 const start = new Date(data.x[0]).toLocaleTimeString([], {
  //                   hour: "2-digit",
  //                   minute: "2-digit",
  //                 });
  //                 const end = new Date(data.x[1]).toLocaleTimeString([], {
  //                   hour: "2-digit",
  //                   minute: "2-digit",
  //                 });
  //                 return `${start} - ${end}`;
  //               },
  //             },
  //           },
  //         },
  //         scales: {
  //           x: {
  //             type: "time",
  //             time: {
  //               unit: "hour",
  //               displayFormats: {
  //                 hour: "HH:mm",
  //               },
  //               min: workStart,
  //               max: workEnd,
  //             },
  //             title: {
  //               display: true,
  //               text: `Working Hours (${config.start_hour}:00 - ${config.end_hour}:00, Lunch: ${
  //                 config.lunch_start
  //               }:${String(Math.floor((config.lunch_start % 1) * 60)).padStart(2, "0")} - ${
  //                 config.lunch_end
  //               }:${String(Math.floor((config.lunch_end % 1) * 60)).padStart(2, "0")})`,
  //               color: "#f0f6fc",
  //             },
  //             grid: {
  //               color: "rgba(255, 255, 255, 0.1)",
  //             },
  //             ticks: {
  //               color: "#8b949e",
  //             },
  //           },
  //           y: {
  //             type: "linear",
  //             title: {
  //               display: true,
  //               text: "Team Members",
  //               color: "#f0f6fc",
  //             },
  //             grid: {
  //               color: "rgba(255, 255, 255, 0.1)",
  //             },
  //             ticks: {
  //               color: "#8b949e",
  //               stepSize: 1,
  //               callback: function (value) {
  //                 // Only show member names at integer positions
  //                 const memberIndex = Math.floor(value);
  //                 return memberIndex >= 0 && memberIndex < members.length ? members[memberIndex] : "";
  //               },
  //             },
  //             min: -0.5,
  //             max: members.length - 0.5,
  //           },
  //         },
  //       },
  //     });

  //     console.log("Timeline chart created with proper member alignment");
  //   },

  createStatusChart(data) {
    const ctx = document.getElementById("statusChart").getContext("2d");
    const metrics = data.metrics || {};
    const memberStats = metrics.member_stats || {};

    const members = Object.keys(memberStats);
    const downtimeHours = members.map((member) => memberStats[member].total_downtime);
    const backgroundColors = members.map((member) => {
      const status = memberStats[member].status;
      if (status === "critical") return this.colors.critical;
      if (status === "warning") return this.colors.downtime;
      return this.colors.active;
    });

    this.charts.status = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members.map((m) => (m.length > 15 ? m.substring(0, 15) + "..." : m)),
        datasets: [
          {
            label: "Downtime Hours",
            data: downtimeHours,
            backgroundColor: backgroundColors,
            borderColor: "rgba(0, 0, 0, 0.8)",
            borderWidth: 1,
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
              label: function (context) {
                return `${context.parsed.x.toFixed(1)} hours downtime`;
              },
            },
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Hours of Downtime",
              color: "#f0f6fc",
            },
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
            },
            ticks: {
              color: "#8b949e",
            },
          },
          y: {
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
            },
            ticks: {
              color: "#8b949e",
            },
          },
        },
      },
    });
  },

  createProductivityChart(data) {
    const ctx = document.getElementById("productivityChart").getContext("2d");
    const metrics = data.metrics || {};
    const teamSummary = metrics.team_summary || {};

    const goodCount = teamSummary.good_count || 0;
    const warningCount = teamSummary.warning_count || 0;
    const criticalCount = teamSummary.critical_count || 0;

    const chartData = [];
    const labels = [];
    const colors = [];

    if (goodCount > 0) {
      chartData.push(goodCount);
      labels.push(`✅ Good (${goodCount})`);
      colors.push(this.colors.active);
    }
    if (warningCount > 0) {
      chartData.push(warningCount);
      labels.push(`⚠️ Warning (${warningCount})`);
      colors.push(this.colors.warning);
    }
    if (criticalCount > 0) {
      chartData.push(criticalCount);
      labels.push(`🆘 Critical (${criticalCount})`);
      colors.push(this.colors.downtime);
    }

    this.charts.productivity = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: chartData,
            backgroundColor: colors,
            borderColor: colors.map((c) => c),
            borderWidth: 2,
            hoverOffset: 10,
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
              color: "#f0f6fc",
              padding: 15,
              usePointStyle: true,
              font: {
                size: 11,
                weight: "bold",
              },
            },
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return `${context.label}: ${percentage}%`;
              },
            },
          },
        },
      },
    });
  },

  createHeatmapGrid(data) {
    const container = document.getElementById("heatmapGrid");
    const metrics = data.metrics || {};
    const hourlyMatrix = metrics.hourly_matrix || {};
    const hoursRange = metrics.hours_range || [];

    if (Object.keys(hourlyMatrix).length === 0) {
      container.innerHTML = '<div class="no-data">No hourly activity data available</div>';
      return;
    }

    const members = Object.keys(hourlyMatrix);

    // Setup grid template
    const gridCols = hoursRange.length + 1; // +1 for member names
    const gridRows = members.length + 1; // +1 for hour labels

    container.style.gridTemplateColumns = `150px repeat(${hoursRange.length}, 1fr)`;
    container.style.gridTemplateRows = `30px repeat(${members.length}, 1fr)`;
    container.innerHTML = "";

    // Empty top-left cell
    const emptyCell = document.createElement("div");
    container.appendChild(emptyCell);

    // Hour labels (top row)
    hoursRange.forEach((hour) => {
      const hourLabel = document.createElement("div");
      hourLabel.className = "heatmap-col-label";
      hourLabel.textContent = `${hour.toString().padStart(2, "0")}:00`;
      container.appendChild(hourLabel);
    });

    // Member rows
    members.forEach((member, memberIndex) => {
      // Member name (left column)
      const memberLabel = document.createElement("div");
      memberLabel.className = "heatmap-row-label";
      memberLabel.textContent = member.length > 12 ? member.substring(0, 12) + "..." : member;
      container.appendChild(memberLabel);

      // Activity cells
      const memberData = hourlyMatrix[member] || [];
      hoursRange.forEach((hour, hourIndex) => {
        const activityLevel = memberData[hourIndex] || 0;
        const cell = document.createElement("div");
        cell.className = "heatmap-cell";

        // Color based on activity level
        const intensity = Math.min(activityLevel, 1.0);
        let backgroundColor;
        if (intensity >= 0.8) {
          backgroundColor = "#28a745"; // High activity - green
        } else if (intensity >= 0.5) {
          backgroundColor = "#ffc107"; // Medium activity - yellow
        } else if (intensity >= 0.2) {
          backgroundColor = "#fd7e14"; // Low activity - orange
        } else if (intensity > 0) {
          backgroundColor = "#dc3545"; // Very low activity - red
        } else {
          backgroundColor = "#6c757d"; // No activity - gray
        }

        cell.style.backgroundColor = backgroundColor;
        cell.style.opacity = Math.max(0.3, intensity);

        // Tooltip info
        cell.title = `${member} at ${hour}:00 - ${(intensity * 100).toFixed(0)}% active`;

        container.appendChild(cell);
      });
    });
  },

  populateStatsPanel(data) {
    const panel = document.getElementById("statsPanel");
    const metrics = data.metrics || {};
    const teamSummary = metrics.team_summary || {};
    const config = this.workingConfig;
    const currentTime = new Date().toLocaleTimeString();

    // Determine current working status
    const now = new Date();
    const isWorkingDay = teamSummary.is_working_day;
    const isWorkingTime = teamSummary.is_working_time;
    const dayName = now.toLocaleDateString("en-US", { weekday: "long" });

    const statsHTML = `
            <div class="stats-grid">
                <div class="stats-card team-overview">
                    <div class="stats-card-header">
                        <span class="stats-icon">👥</span>
                        <span class="stats-card-title">Team Overview</span>
                    </div>
                    <div class="stats-card-body">
                        <div class="stat-row">
                            <span class="stat-label">Total Members</span>
                            <span class="stat-value primary">${
                              teamSummary.total_members || 0
                            }</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Good Status</span>
                            <span class="stat-value success">${teamSummary.good_count || 0}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Warning Status</span>
                            <span class="stat-value warning">${
                              teamSummary.warning_count || 0
                            }</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Critical Status</span>
                            <span class="stat-value danger">${
                              teamSummary.critical_count || 0
                            }</span>
                        </div>
                    </div>
                </div>

                <div class="stats-card working-hours">
                    <div class="stats-card-header">
                        <span class="stats-icon">⏰</span>
                        <span class="stats-card-title">Working Hours</span>
                    </div>
                    <div class="stats-card-body">
                        <div class="stat-row">
                            <span class="stat-label">Work Day</span>
                            <span class="stat-value">${config.start_hour}:00 - ${
      config.end_hour
    }:00</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Lunch Break</span>
                            <span class="stat-value">${config.lunch_start}:${String(
      Math.floor((config.lunch_start % 1) * 60)
    ).padStart(2, "0")} - ${config.lunch_end}:${String(
      Math.floor((config.lunch_end % 1) * 60)
    ).padStart(2, "0")}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Expected/Day</span>
                            <span class="stat-value primary">${config.daily_hours}h</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Working Days</span>
                            <span class="stat-value">Mon-Fri</span>
                        </div>
                    </div>
                </div>

                <div class="stats-card productivity">
                    <div class="stats-card-header">
                        <span class="stats-icon">📈</span>
                        <span class="stats-card-title">Productivity</span>
                    </div>
                    <div class="stats-card-body">
                        <div class="stat-row">
                            <span class="stat-label">Team Active</span>
                            <span class="stat-value success">${(
                              teamSummary.total_team_active || 0
                            ).toFixed(1)}h</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Team Downtime</span>
                            <span class="stat-value ${
                              teamSummary.total_team_downtime > 10 ? "danger" : "warning"
                            }">${(teamSummary.total_team_downtime || 0).toFixed(1)}h</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Team Efficiency</span>
                            <span class="stat-value ${
                              (teamSummary.avg_efficiency || 0) >= 70
                                ? "success"
                                : (teamSummary.avg_efficiency || 0) >= 50
                                ? "warning"
                                : "danger"
                            }">${(teamSummary.avg_efficiency || 0).toFixed(1)}%</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Avg Downtime</span>
                            <span class="stat-value">${(teamSummary.avg_downtime || 0).toFixed(
                              1
                            )}h</span>
                        </div>
                    </div>
                </div>

                <div class="stats-card current-status">
                    <div class="stats-card-header">
                        <span class="stats-icon">🕒</span>
                        <span class="stats-card-title">Current Status</span>
                    </div>
                    <div class="stats-card-body">
                        <div class="stat-row">
                            <span class="stat-label">Today</span>
                            <span class="stat-value">${dayName}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Current Time</span>
                            <span class="stat-value">${currentTime}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Working Day</span>
                            <span class="stat-value ${isWorkingDay ? "success" : "danger"}">${
      isWorkingDay ? "✅ Yes" : "❌ Weekend"
    }</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Working Hours</span>
                            <span class="stat-value ${isWorkingTime ? "success" : "warning"}">${
      isWorkingTime ? "✅ Yes" : "⏰ Outside"
    }</span>
                        </div>
                        ${
                          (teamSummary.currently_inactive || []).length > 0
                            ? `
                            <div class="stat-row inactive-alert">
                                <span class="stat-label">🔥 Currently Inactive</span>
                                <span class="stat-value danger">${
                                  (teamSummary.currently_inactive || []).length
                                }</span>
                            </div>
                        `
                            : ""
                        }
                    </div>
                    ${
                      (teamSummary.currently_inactive || []).length > 0 &&
                      isWorkingDay &&
                      isWorkingTime
                        ? `
                        <div class="inactive-members">
                            <div class="inactive-title">Inactive Members:</div>
                            ${(teamSummary.currently_inactive || [])
                              .slice(0, 3)
                              .map((member) => `<div class="inactive-member">• ${member}</div>`)
                              .join("")}
                            ${
                              (teamSummary.currently_inactive || []).length > 3
                                ? `<div class="inactive-member">• +${
                                    (teamSummary.currently_inactive || []).length - 3
                                  } more...</div>`
                                : ""
                            }
                        </div>
                    `
                        : ""
                    }
                </div>
            </div>
        `;

    panel.innerHTML = statsHTML;
  },

  populateAlertsPanel(data) {
    const panel = document.getElementById("alertsPanel");
    const metrics = data.metrics || {};
    const alerts = metrics.alerts || [];

    if (alerts.length === 0) {
      panel.innerHTML =
        '<div class="alert-item success">✅ ALL CLEAR: No critical issues detected</div>';
      return;
    }

    const alertsHTML = alerts
      .map((alert) => `<div class="alert-item ${alert.type}">${alert.message}</div>`)
      .join("");

    panel.innerHTML = alertsHTML;
  },

  async exportData() {
    try {
      const response = await fetch("/api/export");
      const data = await response.json();

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `clickup_dashboard_export_${new Date()
        .toISOString()
        .slice(0, 19)
        .replace(/:/g, "-")}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log("Data exported successfully");
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Please try again.");
    }
  },

  showLoading() {
    document.getElementById("loadingState").style.display = "flex";
    document.getElementById("errorState").style.display = "none";
    document.getElementById("dashboardGrid").style.display = "none";
  },

  showError(message) {
    document.getElementById("errorMessage").textContent = message;
    document.getElementById("loadingState").style.display = "none";
    document.getElementById("errorState").style.display = "flex";
    document.getElementById("dashboardGrid").style.display = "none";
  },

  showDashboard() {
    document.getElementById("loadingState").style.display = "none";
    document.getElementById("errorState").style.display = "none";
    document.getElementById("dashboardGrid").style.display = "grid";
  },

  startAutoRefresh() {
    // Refresh every 5 minutes
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(() => {
      console.log("Auto-refreshing dashboard data...");
      this.loadData();
    }, 10 * 60 * 1000);
  },

  destroy() {
    // Cleanup method
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    Object.values(this.charts).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") {
        chart.destroy();
      }
    });

    this.charts = {};
    this.currentData = null;
  },
};

// Enhanced Dashboard v2 JavaScript - With Working Hours Support

// Enhanced Dashboard v2 JavaScript - With Working Hours Support

// window.dashboardV2 = {
//   currentData: null,
//   charts: {},
//   refreshInterval: null,
//   workingConfig: null,

//   // Color scheme matching the PNG
//   colors: {
//     active: "#28a745",
//     downtime: "#dc3545",
//     warning: "#ffc107",
//     info: "#17a2b8",
//     critical: "#6c757d",
//     primary: "#007bff",
//     lunch: "#f8f9fa",
//   },

//   init() {
//     console.log("Dashboard v2 initializing with working hours support...");

//     // Initialize charts object
//     this.charts = {};

//     this.setupEventListeners();
//     this.loadData();
//     this.startAutoRefresh();
//   },

//   setupEventListeners() {
//     // Refresh button
//     document.getElementById("refreshBtn").addEventListener("click", () => {
//       this.loadData();
//     });

//     // Export button
//     document.getElementById("exportBtn").addEventListener("click", () => {
//       this.exportData();
//     });

//     // Retry button (in error state)
//     document.getElementById("retryBtn").addEventListener("click", () => {
//       this.loadData();
//     });
//   },

//   async loadData() {
//     this.showLoading();

//     try {
//       console.log("Attempting to load data from /api/dashboard-data");
//       const response = await fetch("/api/dashboard-data");

//       if (!response.ok) {
//         // Try to get more details from the error response
//         let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
//         try {
//           const errorData = await response.json();
//           if (errorData.details) {
//             errorMessage += ` - ${errorData.details}`;
//           }
//         } catch (e) {
//           // If we can't parse the error response, just use the status
//         }
//         throw new Error(errorMessage);
//       }

//       const data = await response.json();
//       console.log("Received data:", data);
//       this.currentData = data;

//       // Update header info
//       this.updateHeader(data);

//       // Create all visualizations
//       this.createAllCharts(data);

//       this.showDashboard();
//       console.log("Dashboard data loaded successfully");
//     } catch (error) {
//       console.error("Error loading data:", error);
//       this.showError(error.message);
//     }
//   },

//   updateHeader(data) {
//     document.getElementById("currentDate").textContent = `📅 ${data.date || "N/A"}`;
//     document.getElementById(
//       "lastUpdate"
//     ).textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
//   },

//   createAllCharts(data) {
//     console.log("Creating charts with working hours data:", data);

//     // Store working configuration
//     this.workingConfig = data.metrics?.working_config || {
//       start_hour: 9,
//       end_hour: 17,
//       lunch_start: 12,
//       lunch_end: 12.5,
//       daily_hours: 7.5,
//     };

//     // Destroy existing charts properly
//     if (this.charts.timeline) {
//       this.charts.timeline.destroy();
//       delete this.charts.timeline;
//     }
//     if (this.charts.status) {
//       this.charts.status.destroy();
//       delete this.charts.status;
//     }
//     if (this.charts.productivity) {
//       this.charts.productivity.destroy();
//       delete this.charts.productivity;
//     }

//     // Create all visualizations with error handling
//     try {
//       this.createTimelineChart(data);
//     } catch (error) {
//       console.error("Error creating timeline chart:", error);
//     }

//     try {
//       this.createStatusChart(data);
//     } catch (error) {
//       console.error("Error creating status chart:", error);
//     }

//     try {
//       this.createProductivityChart(data);
//     } catch (error) {
//       console.error("Error creating productivity chart:", error);
//     }

//     this.createHeatmapGrid(data);
//     this.populateStatsPanel(data);
//     this.populateAlertsPanel(data);
//   },

//   createTimelineChart(data) {
//     const ctx = document.getElementById("timelineChart").getContext("2d");
//     const detailedData = data.detailed_data || {};
//     const members = Object.keys(detailedData);

//     if (members.length === 0) {
//       ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
//       return;
//     }

//     // Simple approach - use linear scale instead of time scale
//     const datasets = [];

//     // Create simple hour-based data (0-8 representing 9AM-5PM)
//     members.forEach((member, memberIndex) => {
//       const memberData = detailedData[member];

//       // Active periods
//       if (memberData.in_progress_periods) {
//         memberData.in_progress_periods.forEach((period, taskIndex) => {
//           datasets.push({
//             label: `${member} - ${period.task_name || "Task"}`,
//             data: [
//               {
//                 x: 1, // Start time placeholder
//                 y: memberIndex,
//               },
//             ],
//             backgroundColor: this.colors.active,
//             borderColor: "darkgreen",
//             borderWidth: 1,
//             barThickness: 20,
//             type: "bar",
//             order: 1,
//           });
//         });
//       }

//       // Downtime periods
//       if (memberData.downtime_periods) {
//         memberData.downtime_periods.forEach((period) => {
//           const duration = period.duration_hours || 0;
//           let color = this.colors.warning;
//           if (duration >= 3) color = this.colors.critical;
//           else if (duration >= 2) color = this.colors.downtime;

//           datasets.push({
//             label: `${member} - Downtime (${duration.toFixed(1)}h)`,
//             data: [
//               {
//                 x: 5, // Different position
//                 y: memberIndex,
//               },
//             ],
//             backgroundColor: color,
//             borderColor: "darkred",
//             borderWidth: 1,
//             barThickness: 20,
//             type: "bar",
//             order: 2,
//           });
//         });
//       }
//     });

//     this.charts.timeline = new Chart(ctx, {
//       type: "bar",
//       data: {
//         labels: members,
//         datasets: datasets,
//       },
//       options: {
//         indexAxis: "y",
//         responsive: true,
//         maintainAspectRatio: false,
//         plugins: {
//           legend: { display: false },
//           tooltip: {
//             callbacks: {
//               title: function (context) {
//                 return context[0].dataset.label;
//               },
//             },
//           },
//         },
//         scales: {
//           x: {
//             type: "linear",
//             min: 0,
//             max: 8,
//             title: {
//               display: true,
//               text: "Working Hours (9:00-17:00)",
//               color: "#f0f6fc",
//             },
//             grid: {
//               color: "rgba(255, 255, 255, 0.1)",
//             },
//             ticks: {
//               color: "#8b949e",
//               callback: function (value) {
//                 return value + 9 + ":00";
//               },
//             },
//           },
//           y: {
//             type: "category",
//             labels: members,
//             title: {
//               display: true,
//               text: "Team Members",
//               color: "#f0f6fc",
//             },
//             grid: {
//               color: "rgba(255, 255, 255, 0.1)",
//             },
//             ticks: {
//               color: "#8b949e",
//             },
//           },
//         },
//       },
//     });

//     console.log("Simplified timeline chart created successfully");
//   },

//   createStatusChart(data) {
//     const ctx = document.getElementById("statusChart").getContext("2d");
//     const metrics = data.metrics || {};
//     const memberStats = metrics.member_stats || {};

//     const members = Object.keys(memberStats);
//     const downtimeHours = members.map((member) => memberStats[member].total_downtime);
//     const backgroundColors = members.map((member) => {
//       const status = memberStats[member].status;
//       if (status === "critical") return this.colors.critical;
//       if (status === "warning") return this.colors.downtime;
//       return this.colors.active;
//     });

//     this.charts.status = new Chart(ctx, {
//       type: "bar",
//       data: {
//         labels: members.map((m) => (m.length > 15 ? m.substring(0, 15) + "..." : m)),
//         datasets: [
//           {
//             label: "Downtime Hours",
//             data: downtimeHours,
//             backgroundColor: backgroundColors,
//             borderColor: "rgba(0, 0, 0, 0.8)",
//             borderWidth: 1,
//           },
//         ],
//       },
//       options: {
//         indexAxis: "y",
//         responsive: true,
//         maintainAspectRatio: false,
//         plugins: {
//           legend: { display: false },
//           tooltip: {
//             callbacks: {
//               label: function (context) {
//                 return `${context.parsed.x.toFixed(1)} hours downtime`;
//               },
//             },
//           },
//         },
//         scales: {
//           x: {
//             title: {
//               display: true,
//               text: "Hours of Downtime",
//               color: "#f0f6fc",
//             },
//             grid: {
//               color: "rgba(255, 255, 255, 0.1)",
//             },
//             ticks: {
//               color: "#8b949e",
//             },
//           },
//           y: {
//             grid: {
//               color: "rgba(255, 255, 255, 0.1)",
//             },
//             ticks: {
//               color: "#8b949e",
//             },
//           },
//         },
//       },
//     });
//   },

//   createProductivityChart(data) {
//     const ctx = document.getElementById("productivityChart").getContext("2d");
//     const metrics = data.metrics || {};
//     const teamSummary = metrics.team_summary || {};

//     const goodCount = teamSummary.good_count || 0;
//     const warningCount = teamSummary.warning_count || 0;
//     const criticalCount = teamSummary.critical_count || 0;

//     const chartData = [];
//     const labels = [];
//     const colors = [];

//     if (goodCount > 0) {
//       chartData.push(goodCount);
//       labels.push(`✅ Good (${goodCount})`);
//       colors.push(this.colors.active);
//     }
//     if (warningCount > 0) {
//       chartData.push(warningCount);
//       labels.push(`⚠️ Warning (${warningCount})`);
//       colors.push(this.colors.warning);
//     }
//     if (criticalCount > 0) {
//       chartData.push(criticalCount);
//       labels.push(`🆘 Critical (${criticalCount})`);
//       colors.push(this.colors.downtime);
//     }

//     this.charts.productivity = new Chart(ctx, {
//       type: "doughnut",
//       data: {
//         labels: labels,
//         datasets: [
//           {
//             data: chartData,
//             backgroundColor: colors,
//             borderColor: colors.map((c) => c),
//             borderWidth: 2,
//             hoverOffset: 10,
//           },
//         ],
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//         plugins: {
//           legend: {
//             position: "bottom",
//             labels: {
//               color: "#f0f6fc",
//               padding: 15,
//               usePointStyle: true,
//               font: {
//                 size: 11,
//                 weight: "bold",
//               },
//             },
//           },
//           tooltip: {
//             callbacks: {
//               label: function (context) {
//                 const total = context.dataset.data.reduce((a, b) => a + b, 0);
//                 const percentage = ((context.parsed / total) * 100).toFixed(1);
//                 return `${context.label}: ${percentage}%`;
//               },
//             },
//           },
//         },
//       },
//     });
//   },

//   createHeatmapGrid(data) {
//     const container = document.getElementById("heatmapGrid");
//     const metrics = data.metrics || {};
//     const hourlyMatrix = metrics.hourly_matrix || {};
//     const hoursRange = metrics.hours_range || [];

//     if (Object.keys(hourlyMatrix).length === 0) {
//       container.innerHTML = '<div class="no-data">No hourly activity data available</div>';
//       return;
//     }

//     const members = Object.keys(hourlyMatrix);

//     // Setup grid template
//     const gridCols = hoursRange.length + 1; // +1 for member names
//     const gridRows = members.length + 1; // +1 for hour labels

//     container.style.gridTemplateColumns = `150px repeat(${hoursRange.length}, 1fr)`;
//     container.style.gridTemplateRows = `30px repeat(${members.length}, 1fr)`;
//     container.innerHTML = "";

//     // Empty top-left cell
//     const emptyCell = document.createElement("div");
//     container.appendChild(emptyCell);

//     // Hour labels (top row)
//     hoursRange.forEach((hour) => {
//       const hourLabel = document.createElement("div");
//       hourLabel.className = "heatmap-col-label";
//       hourLabel.textContent = `${hour.toString().padStart(2, "0")}:00`;
//       container.appendChild(hourLabel);
//     });

//     // Member rows
//     members.forEach((member, memberIndex) => {
//       // Member name (left column)
//       const memberLabel = document.createElement("div");
//       memberLabel.className = "heatmap-row-label";
//       memberLabel.textContent = member.length > 12 ? member.substring(0, 12) + "..." : member;
//       container.appendChild(memberLabel);

//       // Activity cells
//       const memberData = hourlyMatrix[member] || [];
//       hoursRange.forEach((hour, hourIndex) => {
//         const activityLevel = memberData[hourIndex] || 0;
//         const cell = document.createElement("div");
//         cell.className = "heatmap-cell";

//         // Color based on activity level
//         const intensity = Math.min(activityLevel, 1.0);
//         let backgroundColor;
//         if (intensity >= 0.8) {
//           backgroundColor = "#28a745"; // High activity - green
//         } else if (intensity >= 0.5) {
//           backgroundColor = "#ffc107"; // Medium activity - yellow
//         } else if (intensity >= 0.2) {
//           backgroundColor = "#fd7e14"; // Low activity - orange
//         } else if (intensity > 0) {
//           backgroundColor = "#dc3545"; // Very low activity - red
//         } else {
//           backgroundColor = "#6c757d"; // No activity - gray
//         }

//         cell.style.backgroundColor = backgroundColor;
//         cell.style.opacity = Math.max(0.3, intensity);

//         // Tooltip info
//         cell.title = `${member} at ${hour}:00 - ${(intensity * 100).toFixed(0)}% active`;

//         container.appendChild(cell);
//       });
//     });
//   },

//   populateStatsPanel(data) {
//     const panel = document.getElementById("statsPanel");
//     const metrics = data.metrics || {};
//     const teamSummary = metrics.team_summary || {};
//     const config = this.workingConfig;
//     const currentTime = new Date().toLocaleTimeString();

//     // Determine current working status
//     const now = new Date();
//     const isWorkingDay = teamSummary.is_working_day;
//     const isWorkingTime = teamSummary.is_working_time;
//     const dayName = now.toLocaleDateString("en-US", { weekday: "long" });

//     const statsHTML = `
//             <div class="stats-grid">
//                 <div class="stats-card team-overview">
//                     <div class="stats-card-header">
//                         <span class="stats-icon">👥</span>
//                         <span class="stats-card-title">Team Overview</span>
//                     </div>
//                     <div class="stats-card-body">
//                         <div class="stat-row">
//                             <span class="stat-label">Total Members</span>
//                             <span class="stat-value primary">${
//                               teamSummary.total_members || 0
//                             }</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Good Status</span>
//                             <span class="stat-value success">${teamSummary.good_count || 0}</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Warning Status</span>
//                             <span class="stat-value warning">${
//                               teamSummary.warning_count || 0
//                             }</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Critical Status</span>
//                             <span class="stat-value danger">${
//                               teamSummary.critical_count || 0
//                             }</span>
//                         </div>
//                     </div>
//                 </div>

//                 <div class="stats-card working-hours">
//                     <div class="stats-card-header">
//                         <span class="stats-icon">⏰</span>
//                         <span class="stats-card-title">Working Hours</span>
//                     </div>
//                     <div class="stats-card-body">
//                         <div class="stat-row">
//                             <span class="stat-label">Work Day</span>
//                             <span class="stat-value">${config.start_hour}:00 - ${
//       config.end_hour
//     }:00</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Lunch Break</span>
//                             <span class="stat-value">${config.lunch_start}:${String(
//       Math.floor((config.lunch_start % 1) * 60)
//     ).padStart(2, "0")} - ${config.lunch_end}:${String(
//       Math.floor((config.lunch_end % 1) * 60)
//     ).padStart(2, "0")}</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Expected/Day</span>
//                             <span class="stat-value primary">${config.daily_hours}h</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Working Days</span>
//                             <span class="stat-value">Mon-Fri</span>
//                         </div>
//                     </div>
//                 </div>

//                 <div class="stats-card productivity">
//                     <div class="stats-card-header">
//                         <span class="stats-icon">📈</span>
//                         <span class="stats-card-title">Productivity</span>
//                     </div>
//                     <div class="stats-card-body">
//                         <div class="stat-row">
//                             <span class="stat-label">Team Active</span>
//                             <span class="stat-value success">${(
//                               teamSummary.total_team_active || 0
//                             ).toFixed(1)}h</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Team Downtime</span>
//                             <span class="stat-value ${
//                               teamSummary.total_team_downtime > 10 ? "danger" : "warning"
//                             }">${(teamSummary.total_team_downtime || 0).toFixed(1)}h</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Team Efficiency</span>
//                             <span class="stat-value ${
//                               (teamSummary.avg_efficiency || 0) >= 70
//                                 ? "success"
//                                 : (teamSummary.avg_efficiency || 0) >= 50
//                                 ? "warning"
//                                 : "danger"
//                             }">${(teamSummary.avg_efficiency || 0).toFixed(1)}%</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Avg Downtime</span>
//                             <span class="stat-value">${(teamSummary.avg_downtime || 0).toFixed(
//                               1
//                             )}h</span>
//                         </div>
//                     </div>
//                 </div>

//                 <div class="stats-card current-status">
//                     <div class="stats-card-header">
//                         <span class="stats-icon">🕒</span>
//                         <span class="stats-card-title">Current Status</span>
//                     </div>
//                     <div class="stats-card-body">
//                         <div class="stat-row">
//                             <span class="stat-label">Today</span>
//                             <span class="stat-value">${dayName}</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Current Time</span>
//                             <span class="stat-value">${currentTime}</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Working Day</span>
//                             <span class="stat-value ${isWorkingDay ? "success" : "danger"}">${
//       isWorkingDay ? "✅ Yes" : "❌ Weekend"
//     }</span>
//                         </div>
//                         <div class="stat-row">
//                             <span class="stat-label">Working Hours</span>
//                             <span class="stat-value ${isWorkingTime ? "success" : "warning"}">${
//       isWorkingTime ? "✅ Yes" : "⏰ Outside"
//     }</span>
//                         </div>
//                         ${
//                           (teamSummary.currently_inactive || []).length > 0
//                             ? `
//                             <div class="stat-row inactive-alert">
//                                 <span class="stat-label">🔥 Currently Inactive</span>
//                                 <span class="stat-value danger">${
//                                   (teamSummary.currently_inactive || []).length
//                                 }</span>
//                             </div>
//                         `
//                             : ""
//                         }
//                     </div>
//                     ${
//                       (teamSummary.currently_inactive || []).length > 0 &&
//                       isWorkingDay &&
//                       isWorkingTime
//                         ? `
//                         <div class="inactive-members">
//                             <div class="inactive-title">Inactive Members:</div>
//                             ${(teamSummary.currently_inactive || [])
//                               .slice(0, 3)
//                               .map((member) => `<div class="inactive-member">• ${member}</div>`)
//                               .join("")}
//                             ${
//                               (teamSummary.currently_inactive || []).length > 3
//                                 ? `<div class="inactive-member">• +${
//                                     (teamSummary.currently_inactive || []).length - 3
//                                   } more...</div>`
//                                 : ""
//                             }
//                         </div>
//                     `
//                         : ""
//                     }
//                 </div>
//             </div>
//         `;

//     panel.innerHTML = statsHTML;
//   },

//   populateAlertsPanel(data) {
//     const panel = document.getElementById("alertsPanel");
//     const metrics = data.metrics || {};
//     const alerts = metrics.alerts || [];

//     if (alerts.length === 0) {
//       panel.innerHTML =
//         '<div class="alert-item success">✅ ALL CLEAR: No critical issues detected</div>';
//       return;
//     }

//     const alertsHTML = alerts
//       .map((alert) => `<div class="alert-item ${alert.type}">${alert.message}</div>`)
//       .join("");

//     panel.innerHTML = alertsHTML;
//   },

//   async exportData() {
//     try {
//       const response = await fetch("/api/export");
//       const data = await response.json();

//       const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
//       const url = URL.createObjectURL(blob);
//       const a = document.createElement("a");
//       a.href = url;
//       a.download = `clickup_dashboard_export_${new Date()
//         .toISOString()
//         .slice(0, 19)
//         .replace(/:/g, "-")}.json`;
//       document.body.appendChild(a);
//       a.click();
//       document.body.removeChild(a);
//       URL.revokeObjectURL(url);

//       console.log("Data exported successfully");
//     } catch (error) {
//       console.error("Export failed:", error);
//       alert("Export failed. Please try again.");
//     }
//   },

//   showLoading() {
//     document.getElementById("loadingState").style.display = "flex";
//     document.getElementById("errorState").style.display = "none";
//     document.getElementById("dashboardGrid").style.display = "none";
//   },

//   showError(message) {
//     document.getElementById("errorMessage").textContent = message;
//     document.getElementById("loadingState").style.display = "none";
//     document.getElementById("errorState").style.display = "flex";
//     document.getElementById("dashboardGrid").style.display = "none";
//   },

//   showDashboard() {
//     document.getElementById("loadingState").style.display = "none";
//     document.getElementById("errorState").style.display = "none";
//     document.getElementById("dashboardGrid").style.display = "grid";
//   },

//   startAutoRefresh() {
//     // Refresh every 5 minutes
//     if (this.refreshInterval) {
//       clearInterval(this.refreshInterval);
//     }

//     this.refreshInterval = setInterval(() => {
//       console.log("Auto-refreshing dashboard data...");
//       this.loadData();
//     }, 5 * 60 * 1000);
//   },

//   destroy() {
//     // Cleanup method with better error handling
//     if (this.refreshInterval) {
//       clearInterval(this.refreshInterval);
//     }

//     // Destroy all charts safely
//     Object.keys(this.charts).forEach((chartKey) => {
//       const chart = this.charts[chartKey];
//       if (chart && typeof chart.destroy === "function") {
//         try {
//           chart.destroy();
//         } catch (error) {
//           console.warn(`Error destroying chart ${chartKey}:`, error);
//         }
//       }
//     });

//     this.charts = {};
//     this.currentData = null;
//     this.workingConfig = null;
//   },
// };
