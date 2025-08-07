// Enhanced Dashboard v2 JavaScript - With Working Hours Support
window.dashboardV2 = {
  // Core properties
  currentData: null,
  charts: {},
  refreshInterval: null,
  workingConfig: {
    start_hour: 9,
    end_hour: 17,
    lunch_start: 12,
    lunch_end: 12.5,
    daily_hours: 7.5,
  },

  // Visual settings
  colors: {
    active: "#28a745",
    downtime: "#dc3545",
    warning: "#ffc107",
    info: "#17a2b8",
    critical: "#6c757d",
    primary: "#007bff",
    lunch: "#1E1E1E",
  },

  // Layout metrics
  timelineMargins: {
    top: 20,
    right: 30,
    bottom: 30,
    left: 60,
  },

  // Main initialization
  init() {
    try {
      console.log("1. Initialization started");
      this.setupEventListeners();
      console.log("2. Setting up data load");
      this.loadData().catch((error) => {
        console.error("Load data failed:", error);
      });
      console.log("3. Initialization complete");
    } catch (error) {
      console.error("Initialization error:", error);
    }
  },

  setup() {
    this.setupEventListeners();
    this.loadData();
    this.startAutoRefresh();
  },

  // Helper methods
  safeParseTime(timeString, fallback = new Date()) {
    try {
      if (!timeString) return fallback;
      const parsed = new Date(timeString);
      return isNaN(parsed.getTime()) ? fallback : parsed;
    } catch {
      return fallback;
    }
  },

  validateContainer(id) {
    const element = document.getElementById(id);
    if (!element) {
      console.error(`Container #${id} not found`);
      return false;
    }
    return true;
  },

  showTimelineTooltip(event, data) {
    try {
      const tooltip = document.getElementById("tooltip");
      if (!tooltip) return;

      tooltip.style.display = "block";
      tooltip.style.left = `${event.pageX + 10}px`;
      tooltip.style.top = `${event.pageY - 10}px`;
      tooltip.innerHTML = `
          <div class="tooltip-title">${data.title || "Unknown"}</div>
          <div>${data.content || "No details"}</div>
        `;
    } catch (error) {
      console.error("Tooltip error:", error);
    }
  },

  hideTimelineTooltip() {
    const tooltip = document.getElementById("tooltip");
    if (tooltip) tooltip.style.display = "none";
  },

  setupEventListeners() {
    // Safe event listener setup
    const addListener = (id, event, fn) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener(event, fn);
    };

    addListener("refreshBtn", "click", () => this.loadData());
    addListener("exportBtn", "click", () => this.exportData());
    addListener("retryBtn", "click", () => this.loadData());
  },

  async loadData() {
    this.showLoading();

    try {
      console.log("Loading data from /api/dashboard-data");
      const response = await fetch("/api/dashboard-data");

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText || "No details"}`);
      }

      const data = await response.json();

      // Validate response structure
      if (!data || typeof data !== "object") {
        throw new Error("Invalid data format received");
      }

      // Ensure required fields exist
      if (!data.detailed_data || !data.metrics) {
        throw new Error("Incomplete data: missing required fields");
      }

      this.currentData = data;
      this.updateHeader(data);

      // Update working config if provided
      if (data.metrics?.working_config) {
        this.workingConfig = data.metrics.working_config;
      }

      this.createAllCharts(data);
      this.showDashboard();
    } catch (error) {
      console.error("Data loading failed:", error);
      this.showError(error.message || "Failed to load dashboard data");
      this.resetChartsToEmptyState();
    }
  },

  resetChartsToEmptyState() {
    const containers = [
      "timeline",
      "statusChart",
      "productivityChart",
      "heatmapGrid",
      "statsPanel",
      "alertsPanel",
    ];

    containers.forEach((id) => {
      const container = document.getElementById(id);
      if (container) {
        container.innerHTML = `<div class="chart-placeholder">Data unavailable</div>`;
      }
    });
  },

  updateHeader(data) {
    const setText = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    };

    setText("currentDate", `📅 ${data.date || "N/A"}`);
    setText("lastUpdate", `Last updated: ${new Date().toLocaleTimeString()}`);
  },

  createAllCharts(data) {
    if (!data) {
      console.error("No data provided for charts");
      return;
    }

    // Verify container elements exist
    const requiredContainers = [
      "timeline",
      "statusChart",
      "productivityChart",
      "heatmapGrid",
      "statsPanel",
      "alertsPanel",
    ];

    requiredContainers.forEach((id) => {
      if (!this.validateContainer(id)) return;
    });

    try {
      this.createTimelineChart(data);
      this.createStatusChart(data);
      this.createProductivityChart(data);
      this.createHeatmapGrid(data);
      this.populateStatsPanel(data);
      this.populateAlertsPanel(data);
    } catch (error) {
      console.error("Chart creation failed:", error);
      this.showError("Failed to render visualizations");
    }
  },

  createTimelineChart(data) {
    if (!this.validateContainer("timeline")) return;

    try {
      // Clear existing timeline
      const timelineElement = document.getElementById("timeline");
      d3.select("#timeline").selectAll("*").remove();

      // Set up dimensions
      const container = document.querySelector("#timeline").parentElement;
      if (!container) {
        console.error("Timeline container not found");
        return;
      }

      const margins = this.timelineMargins;
      const width = container.clientWidth - margins.left - margins.right;
      const height = 400 - margins.top - margins.bottom;

      // Create SVG
      const svg = d3
        .select("#timeline")
        .attr("width", width + margins.left + margins.right)
        .attr("height", height + margins.top + margins.bottom)
        .append("g")
        .attr("transform", `translate(${margins.left},${margins.top})`);

      // Extract members with validation
      const members = Object.keys(data.detailed_data || {});
      if (members.length === 0) {
        console.warn("No member data available for timeline");
        return;
      }

      const config = this.workingConfig;

      // Create scales with protected date creation
      const today = new Date();
      const startTime = new Date(today.setHours(0, 0, 0, 0));
      const endTime = new Date(today.setHours(23, 59, 0, 0));

      const x = d3.scaleTime().domain([startTime, endTime]).range([0, width]).clamp(true);

      const y = d3.scaleBand().domain(members).range([0, height]).padding(0.1);

      // Store scales for zoom functions
      this.timelineScales = { x, y };
      this.timelineSVG = svg;

      // Safe working hours calculation
      const workStart = new Date(startTime);
      workStart.setHours(config.start_hour, 0, 0, 0);
      const workEnd = new Date(startTime);
      workEnd.setHours(config.end_hour, 0, 0, 0);

      // Add working hours background with protected width
      svg
        .append("rect")
        .attr("class", "working-hours-bg")
        .attr("x", x(workStart))
        .attr("y", 0)
        .attr("width", Math.max(0, x(workEnd) - x(workStart)))
        .attr("height", height)
        .attr("fill", "rgba(40, 167, 69, 0.05)");

      // Add grid lines
      svg
        .selectAll(".grid-line-horizontal")
        .data(members)
        .enter()
        .append("line")
        .attr("class", "grid-line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", (d) => y(d) + y.bandwidth() / 2)
        .attr("y2", (d) => y(d) + y.bandwidth() / 2);

      // Vertical hour lines
      for (let hour = 0; hour <= 23; hour++) {
        const time = new Date(startTime);
        time.setHours(hour, 0, 0, 0);
        svg
          .append("line")
          .attr("class", "grid-line")
          .attr("x1", x(time))
          .attr("x2", x(time))
          .attr("y1", 0)
          .attr("y2", height);
      }

      // Add axes
      const xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%H:%M")).ticks(d3.timeHour.every(1));

      svg
        .append("g")
        .attr("class", "time-axis")
        .attr("transform", `translate(0,${height})`)
        .call(xAxis);

      const yAxis = d3.axisLeft(y);
      svg.append("g").attr("class", "y-axis").call(yAxis);

      // Add lunch breaks
      const lunchStart = new Date(startTime);
      lunchStart.setHours(Math.floor(config.lunch_start), (config.lunch_start % 1) * 60, 0, 0);
      const lunchEnd = new Date(startTime);
      lunchEnd.setHours(Math.floor(config.lunch_end), (config.lunch_end % 1) * 60, 0, 0);

      svg
        .selectAll(".lunch-bar")
        .data(members)
        .enter()
        .append("rect")
        .attr("class", "timeline-bar lunch-bar")
        .attr("x", x(lunchStart))
        .attr("y", (d) => y(d))
        .attr("width", Math.max(0, x(lunchEnd) - x(lunchStart)))
        .attr("height", y.bandwidth())
        .on("mouseover", (event, d) => {
          const formatTime = (time) => {
            const hours = Math.floor(time);
            const minutes = Math.floor((time % 1) * 60);
            return `${hours}:${String(minutes).padStart(2, "0")}`;
          };

          this.showTimelineTooltip(event, {
            title: `${d} - Lunch Break`,
            content: `${formatTime(config.lunch_start)} - ${formatTime(config.lunch_end)}`,
          });
        })
        .on("mouseout", () => this.hideTimelineTooltip());

      // Process member data
      members.forEach((member) => {
        const memberData = data.detailed_data[member] || {};
        const yPos = y(member);
        const barHeight = y.bandwidth();

        // Active periods
        (memberData.in_progress_periods || []).forEach((period) => {
          const start = this.safeParseTime(period.start);
          let end = period.end ? this.safeParseTime(period.end) : new Date();
          end = end > workEnd ? workEnd : end;

          svg
            .append("rect")
            .attr("class", "timeline-bar active-bar")
            .attr("x", x(start))
            .attr("y", yPos)
            .attr("width", Math.max(0, x(end) - x(start)))
            .attr("height", barHeight * 0.7)
            .on("mouseover", (event) => {
              const duration = (end - start) / (1000 * 60 * 60);
              this.showTimelineTooltip(event, {
                title: `${member} - Active`,
                content: `Task: ${period.task_name || "Unknown"}<br>
                           ${start.toLocaleTimeString()} - ${end.toLocaleTimeString()}<br>
                           Duration: ${duration.toFixed(1)}h`,
              });
            })
            .on("mouseout", () => this.hideTimelineTooltip());
        });

        // Downtime periods
        (memberData.downtime_periods || []).forEach((period) => {
          const start = this.safeParseTime(period.start);
          let end = period.end ? this.safeParseTime(period.end) : new Date();
          end = end > workEnd ? workEnd : end;
          const duration = period.duration_hours || 0;

          let className = "timeline-bar warning-bar";
          if (duration >= 3) className = "timeline-bar downtime-bar";

          svg
            .append("rect")
            .attr("class", className)
            .attr("x", x(start))
            .attr("y", yPos + barHeight * 0.7)
            .attr("width", Math.max(0, x(end) - x(start)))
            .attr("height", barHeight * 0.3)
            .on("mouseover", (event) => {
              this.showTimelineTooltip(event, {
                title: `${member} - Downtime`,
                content: `${start.toLocaleTimeString()} - ${end.toLocaleTimeString()}<br>
                           Duration: ${duration.toFixed(1)} hours<br>
                           Status: ${duration >= 3 ? "Critical" : "Warning"}`,
              });
            })
            .on("mouseout", () => this.hideTimelineTooltip());
        });
      });
    } catch (error) {
      console.error("Error in createTimelineChart:", error);
      const timelineElement = document.getElementById("timeline");
      if (timelineElement) {
        timelineElement.innerHTML = '<div class="chart-error">Timeline unavailable</div>';
      }
    }
  },

  createStatusChart(data) {
    const canvas = document.getElementById("statusChart");
    if (!canvas) {
      console.error("Status chart canvas missing");
      return;
    }

    try {
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Couldn't get 2D context");

      // Clear previous chart if exists
      if (this.charts.status) {
        this.charts.status.destroy();
      }

      const metrics = data.metrics || {};
      const memberStats = metrics.member_stats || {};
      const members = Object.keys(memberStats);

      if (members.length === 0) {
        canvas.parentElement.innerHTML = '<div class="no-data">No member data</div>';
        return;
      }

      // Safely extract data with defaults
      const downtimeHours = members.map((member) => memberStats[member]?.total_downtime || 0);

      this.charts.status = new Chart(ctx, {
        type: "bar",
        data: {
          labels: members.map((m) => (m.length > 15 ? `${m.substring(0, 12)}...` : m)),
          datasets: [
            {
              label: "Downtime Hours",
              data: downtimeHours,
              backgroundColor: members.map((member) => {
                const status = memberStats[member]?.status;
                return this.colors[status] || this.colors.info;
              }),
              borderColor: "#333",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `${ctx.parsed.x?.toFixed(1) || 0} hours downtime`,
              },
            },
          },
          scales: {
            x: {
              beginAtZero: true,
              title: { display: true, text: "Hours of Downtime" },
            },
          },
        },
      });
    } catch (error) {
      console.error("Status chart error:", error);
      canvas.parentElement.innerHTML = '<div class="chart-error">Status chart failed</div>';
    }
  },

  createProductivityChart(data) {
    const canvas = document.getElementById("productivityChart");
    if (!canvas) return;

    try {
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("No 2D context");

      // Clear previous instance
      if (this.charts.productivity) {
        this.charts.productivity.destroy();
      }

      const metrics = data.metrics || {};
      const teamSummary = metrics.team_summary || {};

      const chartData = [];
      const labels = [];
      const colors = [];

      // Safe data extraction
      const goodCount = teamSummary.good_count || 0;
      const warningCount = teamSummary.warning_count || 0;
      const criticalCount = teamSummary.critical_count || 0;

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

      if (chartData.length === 0) {
        canvas.parentElement.innerHTML = '<div class="no-data">No productivity data</div>';
        return;
      }

      this.charts.productivity = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: labels,
          datasets: [
            {
              data: chartData,
              backgroundColor: colors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          cutout: "70%",
          plugins: {
            legend: { position: "bottom" },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  const percent = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                  return `${ctx.label}: ${percent}%`;
                },
              },
            },
          },
        },
      });
    } catch (error) {
      console.error("Productivity chart error:", error);
      canvas.parentElement.innerHTML = '<div class="chart-error">Productivity chart failed</div>';
    }
  },

  createHeatmapGrid(data) {
    const container = document.getElementById("heatmapGrid");
    if (!container) return;

    try {
      const metrics = data.metrics || {};
      const hourlyMatrix = metrics.hourly_matrix || {};
      const hoursRange = metrics.hours_range || [];

      if (Object.keys(hourlyMatrix).length === 0) {
        container.innerHTML = '<div class="no-data">No hourly data available</div>';
        return;
      }

      const members = Object.keys(hourlyMatrix);

      // Setup grid template
      container.style.gridTemplateColumns = `150px repeat(${hoursRange.length}, 1fr)`;
      container.style.gridTemplateRows = `30px repeat(${members.length}, 1fr)`;
      container.innerHTML = "";

      // Empty top-left cell
      container.appendChild(document.createElement("div"));

      // Hour labels (top row)
      hoursRange.forEach((hour) => {
        const hourLabel = document.createElement("div");
        hourLabel.className = "heatmap-col-label";
        hourLabel.textContent = `${hour.toString().padStart(2, "0")}:00`;
        container.appendChild(hourLabel);
      });

      // Member rows
      members.forEach((member) => {
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
            backgroundColor = "#28a745";
          } else if (intensity >= 0.5) {
            backgroundColor = "#ffc107";
          } else if (intensity >= 0.2) {
            backgroundColor = "#fd7e14";
          } else if (intensity > 0) {
            backgroundColor = "#dc3545";
          } else {
            backgroundColor = "#6c757d";
          }

          cell.style.backgroundColor = backgroundColor;
          cell.style.opacity = Math.max(0.3, intensity);
          cell.title = `${member} at ${hour}:00 - ${(intensity * 100).toFixed(0)}% active`;
          container.appendChild(cell);
        });
      });
    } catch (error) {
      console.error("Heatmap error:", error);
      container.innerHTML = '<div class="chart-error">Heatmap unavailable</div>';
    }
  },

  populateStatsPanel(data) {
    if (!this.validateContainer("statsPanel")) return;

    try {
      const panel = document.getElementById("statsPanel");
      const metrics = data.metrics || {};
      const teamSummary = metrics.team_summary || {};
      const config = this.workingConfig;

      // Format lunch times safely
      const formatLunchTime = (time) => {
        const hours = Math.floor(time);
        const minutes = Math.round((time % 1) * 60);
        return `${hours}:${minutes.toString().padStart(2, "0")}`;
      };

      const currentTime = new Date().toLocaleTimeString();
      const now = new Date();
      const dayName = now.toLocaleDateString("en-US", { weekday: "long" });

      panel.innerHTML = `
          <div class="stats-grid">
            <div class="stats-card">
              <h3>Team Overview</h3>
              <div class="stat-row">
                <span>Total Members:</span>
                <span>${teamSummary.total_members || 0}</span>
              </div>
              <div class="stat-row">
                <span>Good Status:</span>
                <span class="stat-value success">${teamSummary.good_count || 0}</span>
              </div>
              <div class="stat-row">
                <span>Warning Status:</span>
                <span class="stat-value warning">${teamSummary.warning_count || 0}</span>
              </div>
              <div class="stat-row">
                <span>Critical Status:</span>
                <span class="stat-value danger">${teamSummary.critical_count || 0}</span>
              </div>
            </div>
  
            <div class="stats-card">
              <h3>Working Hours</h3>
              <div class="stat-row">
                <span>Work Day:</span>
                <span>${config.start_hour}:00 - ${config.end_hour}:00</span>
              </div>
              <div class="stat-row">
                <span>Lunch:</span>
                <span>${formatLunchTime(config.lunch_start)} - ${formatLunchTime(
        config.lunch_end
      )}</span>
              </div>
              <div class="stat-row">
                <span>Expected/Day:</span>
                <span>${config.daily_hours}h</span>
              </div>
            </div>
  
            <div class="stats-card">
              <h3>Current Status</h3>
              <div class="stat-row">
                <span>Time:</span>
                <span>${currentTime}</span>
              </div>
              <div class="stat-row">
                <span>Day:</span>
                <span>${dayName}</span>
              </div>
            </div>
          </div>
        `;
    } catch (error) {
      console.error("Failed to populate stats panel:", error);
      document.getElementById("statsPanel").innerHTML = `
          <div class="panel-error">
            Could not load statistics
          </div>
        `;
    }
  },

  populateAlertsPanel(data) {
    const panel = document.getElementById("alertsPanel");
    if (!panel) return;

    const metrics = data.metrics || {};
    const alerts = metrics.alerts || [];

    if (alerts.length === 0) {
      panel.innerHTML = '<div class="alert-item success">✅ No critical issues</div>';
      return;
    }

    panel.innerHTML = alerts
      .map((alert) => `<div class="alert-item ${alert.type}">${alert.message}</div>`)
      .join("");
  },

  async exportData() {
    try {
      const response = await fetch("/api/export");
      const data = await response.json();

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dashboard_export_${new Date()
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
    const loading = document.getElementById("loadingState");
    const error = document.getElementById("errorState");
    const dashboard = document.getElementById("dashboardGrid");

    if (loading) loading.style.display = "flex";
    if (error) error.style.display = "none";
    if (dashboard) dashboard.style.display = "none";
  },

  showError(message) {
    const loading = document.getElementById("loadingState");
    const error = document.getElementById("errorState");
    const dashboard = document.getElementById("dashboardGrid");
    const errorMsg = document.getElementById("errorMessage");

    if (errorMsg) errorMsg.textContent = message;
    if (loading) loading.style.display = "none";
    if (error) error.style.display = "flex";
    if (dashboard) dashboard.style.display = "none";
  },

  showDashboard() {
    const loading = document.getElementById("loadingState");
    const error = document.getElementById("errorState");
    const dashboard = document.getElementById("dashboardGrid");

    if (loading) loading.style.display = "none";
    if (error) error.style.display = "none";
    if (dashboard) dashboard.style.display = "grid";
  },

  startAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(() => {
      console.log("Auto-refreshing dashboard data...");
      this.loadData();
    }, 5 * 60 * 1000); // 5 minutes
  },

  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    // Safely destroy all charts
    Object.keys(this.charts).forEach((chartKey) => {
      const chart = this.charts[chartKey];
      if (chart && typeof chart.destroy === "function") {
        try {
          chart.destroy();
        } catch (error) {
          console.warn(`Error destroying chart ${chartKey}:`, error);
        }
      }
    });

    this.charts = {};
    this.currentData = null;
  },
};

// Initialize dashboard when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  window.dashboardV2.init();
});
