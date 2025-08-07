// Enhanced Dashboard v2 JavaScript - With D3.js Timeline
window.dashboardV2 = {
  currentData: null,
  charts: {},
  refreshInterval: null,
  workingConfig: null,
  timelineSVG: null,
  timelineScales: null,
  timelineMargins: { top: 40, right: 100, bottom: 40, left: 150 },

  // Color scheme
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
    console.log("Dashboard v2 initializing with D3.js timeline...");
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

    // Destroy existing charts (except D3 timeline)
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

  createTimelineChart(data) {
    // Clear existing timeline
    d3.select("#timeline").selectAll("*").remove();

    // Set up dimensions
    const container = document.querySelector("#timeline").parentElement;
    const width = container.clientWidth - this.timelineMargins.left - this.timelineMargins.right;
    const height = 400 - this.timelineMargins.top - this.timelineMargins.bottom;

    // Create SVG
    const svg = d3
      .select("#timeline")
      .attr("width", width + this.timelineMargins.left + this.timelineMargins.right)
      .attr("height", height + this.timelineMargins.top + this.timelineMargins.bottom)
      .append("g")
      .attr("transform", `translate(${this.timelineMargins.left},${this.timelineMargins.top})`);

    // Parse the date/time
    const parseTime = d3.timeParse("%Y-%m-%dT%H:%M:%S.%LZ");

    // Extract members
    const members = Object.keys(data.detailed_data || {});
    const config = this.workingConfig;

    // Create scales
    const today = new Date();
    const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0);
    const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59);

    const x = d3.scaleTime().domain([startTime, endTime]).range([0, width]);

    const y = d3.scaleBand().domain(members).range([0, height]).padding(0.1);

    // Store scales for zoom functions
    this.timelineScales = { x, y };
    this.timelineSVG = svg;

    // Add working hours background
    const workStart = new Date(startTime);
    workStart.setHours(config.start_hour, 0, 0, 0);
    const workEnd = new Date(startTime);
    workEnd.setHours(config.end_hour, 0, 0, 0);

    svg
      .append("rect")
      .attr("class", "working-hours-bg")
      .attr("x", x(workStart))
      .attr("y", 0)
      .attr("width", x(workEnd) - x(workStart))
      .attr("height", height)
      .attr("fill", "rgba(40, 167, 69, 0.05)");

    // Add grid lines
    // Horizontal grid lines
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
    // X-axis (time)
    const xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%H:%M")).ticks(d3.timeHour.every(1));

    svg
      .append("g")
      .attr("class", "time-axis")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis);

    // Y-axis (members)
    const yAxis = d3.axisLeft(y);
    svg.append("g").attr("class", "y-axis").call(yAxis);

    // Style member labels
    svg.selectAll(".y-axis text").attr("class", "member-label");

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
      .attr("width", x(lunchEnd) - x(lunchStart))
      .attr("height", y.bandwidth())
      .on("mouseover", (event, d) => {
        this.showTimelineTooltip(event, {
          title: `${d} - Lunch Break`,
          content: `${config.lunch_start}:${String(
            Math.floor((config.lunch_start % 1) * 60)
          ).padStart(2, "0")} - ${config.lunch_end}:${String(
            Math.floor((config.lunch_end % 1) * 60)
          ).padStart(2, "0")}`,
        });
      })
      .on("mouseout", () => this.hideTimelineTooltip());

    // Add active periods and downtime
    members.forEach((member) => {
      const memberData = data.detailed_data[member];
      const yPos = y(member);
      const barHeight = y.bandwidth();

      // Active periods
      if (memberData.in_progress_periods) {
        memberData.in_progress_periods.forEach((period) => {
          const start = parseTime(period.start);
          let end = period.end ? parseTime(period.end) : new Date();
          end = end > workEnd ? workEnd : end;

          svg
            .append("rect")
            .attr("class", "timeline-bar active-bar")
            .attr("x", x(start))
            .attr("y", yPos)
            .attr("width", x(end) - x(start))
            .attr("height", barHeight * 0.7)
            .on("mouseover", (event) => {
              const duration = (end - start) / (1000 * 60 * 60);
              this.showTimelineTooltip(event, {
                title: `${member} - Active`,
                content: `Task: ${period.task_name}<br>
                                       ${start.toLocaleTimeString()} - ${end.toLocaleTimeString()}<br>
                                       Duration: ${duration.toFixed(1)}h`,
              });
            })
            .on("mouseout", () => this.hideTimelineTooltip());
        });
      }

      // Downtime periods
      if (memberData.downtime_periods) {
        memberData.downtime_periods.forEach((period) => {
          const start = parseTime(period.start);
          let end = period.end ? parseTime(period.end) : new Date();
          end = end > workEnd ? workEnd : end;
          const duration = period.duration_hours || 0;

          let className = "timeline-bar warning-bar";
          if (duration >= 3) className = "timeline-bar downtime-bar";

          svg
            .append("rect")
            .attr("class", className)
            .attr("x", x(start))
            .attr("y", yPos + barHeight * 0.7)
            .attr("width", x(end) - x(start))
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
      }
    });
  },

  showTimelineTooltip(event, data) {
    const tooltip = d3.select("#tooltip");
    tooltip
      .style("display", "block")
      .style("left", event.pageX + 10 + "px")
      .style("top", event.pageY - 10 + "px")
      .html(`<div class="tooltip-title">${data.title}</div><div>${data.content}</div>`);
  },

  hideTimelineTooltip() {
    d3.select("#tooltip").style("display", "none");
  },

  zoomToWorkingHours() {
    if (!this.timelineScales || !this.timelineSVG) return;

    const config = this.workingConfig;
    const today = new Date();
    const workStart = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      config.start_hour - 1,
      0
    );
    const workEnd = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      config.end_hour + 1,
      0
    );

    // Update x-scale domain
    this.timelineScales.x.domain([workStart, workEnd]);

    // Update x-axis
    const xAxis = d3
      .axisBottom(this.timelineScales.x)
      .tickFormat(d3.timeFormat("%H:%M"))
      .ticks(d3.timeHour.every(1));

    this.timelineSVG.select(".time-axis").transition().duration(750).call(xAxis);

    // Since we're not using data binding for bars, we don't need to update them here
    // The bars will automatically adjust to the new scale
  },

  zoomToFullDay() {
    if (!this.timelineScales || !this.timelineSVG) return;

    const today = new Date();
    const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0);
    const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59);

    // Update x-scale domain
    this.timelineScales.x.domain([startTime, endTime]);

    // Update x-axis
    const xAxis = d3
      .axisBottom(this.timelineScales.x)
      .tickFormat(d3.timeFormat("%H:%M"))
      .ticks(d3.timeHour.every(1));

    this.timelineSVG.select(".time-axis").transition().duration(750).call(xAxis);

    // Since we're not using data binding for bars, we don't need to update them here
    // The bars will automatically adjust to the new scale
  },
  // zoomToFullDay() {
  //   if (!this.timelineScales || !this.timelineSVG) return;

  //   const today = new Date();
  //   const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0);
  //   const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59);

  //   // Update x-scale domain
  //   this.timelineScales.x.domain([startTime, endTime]);

  //   // Update x-axis
  //   const xAxis = d3
  //     .axisBottom(this.timelineScales.x)
  //     .tickFormat(d3.timeFormat("%H:%M"))
  //     .ticks(d3.timeHour.every(1));

  //   this.timelineSVG.select(".time-axis").transition().duration(750).call(xAxis);

  //   // Update all bars
  //   this.timelineSVG
  //     .selectAll(".timeline-bar")
  //     .transition()
  //     .duration(750)
  //     .attr("x", (d) => this.timelineScales.x(d.start || startTime))
  //     .attr("width", (d) => {
  //       const start = d.start || startTime;
  //       const end = d.end || new Date();
  //       return this.timelineScales.x(end) - this.timelineScales.x(start);
  //     });
  // },

  // Keep all your other existing methods exactly as they were
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
                              (teamSummary && teamSummary.total_members) || 0
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
