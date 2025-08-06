// Main dashboard controller
window.dashboard = {
  currentData: null,
  refreshInterval: null,

  init() {
    console.log("Dashboard init started...");
    console.log("Available modules:", {
      theme: !!window.theme,
      datePicker: !!window.datePicker,
      charts: !!window.charts,
      utils: !!window.utils,
      api: !!window.api,
    });

    // Initialize modules if available
    if (window.theme && typeof window.theme.init === "function") {
      theme.init();
    } else {
      console.warn("Theme module not available, using default theme");
      // Set a default theme
      document.documentElement.setAttribute("data-theme", "dark");
    }

    if (window.datePicker && typeof window.datePicker.init === "function") {
      datePicker.init();
    } else {
      console.warn("DatePicker module not available");
    }

    if (window.charts && typeof window.charts.init === "function") {
      charts.init();
    } else {
      console.warn("Charts module not available");
    }

    // Setup event listeners
    this.setupEventListeners();

    // Load initial data
    const selectedDate = window.datePicker
      ? datePicker.getSelectedDate()
      : new Date().toISOString().split("T")[0];
    this.loadData(selectedDate);

    // Setup auto-refresh
    this.startAutoRefresh();

    // Setup resize handler
    if (window.utils && window.utils.debounce) {
      window.addEventListener(
        "resize",
        utils.debounce(() => {
          if (window.charts && window.charts.resize) {
            charts.resize();
          }
        }, 250)
      );
    }
  },

  setupEventListeners() {
    // Tab switching
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", (e) => this.switchTab(e.target));
    });

    // View toggle for member grid
    document.querySelectorAll(".view-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => this.toggleView(e.target));
    });
  },

  async loadData(date) {
    this.showLoading(true);

    try {
      // Fetch dashboard data
      const data = await api.getDashboardData(date);
      this.currentData = data;

      if (data.is_weekend) {
        this.showWeekendMessage();
      } else {
        this.updateDashboard(data);
        this.loadAlerts(date);
      }

      // Update last updated time
      this.updateLastUpdated();
    } catch (error) {
      this.showError("Failed to load dashboard data");
      console.error("Load data error:", error);
    } finally {
      this.showLoading(false);
    }
  },

  updateDashboard(data) {
    // Update KPIs
    this.updateKPIs(data.team_metrics || {});

    // Update charts
    charts.updateAll(data);

    // Update member grid
    this.updateMemberGrid(data.detailed_data || {});

    // Update detailed statistics
    this.updateDetailedStats(data);

    // Update timeline date
    const timelineDate = document.getElementById("timelineDate");
    if (timelineDate) {
      timelineDate.textContent = utils.formatDate(datePicker.getSelectedDate());
    }

    // Show main content
    document.getElementById("clickupTab").style.display = "block";
  },

  updateKPIs(metrics) {
    // Update values
    document.getElementById("membersAnalyzed").textContent = metrics.members_analyzed || 0;
    document.getElementById("totalActiveHours").textContent = `${(
      metrics.total_active_hours || 0
    ).toFixed(1)}h`;
    document.getElementById("totalDowntime").textContent = `${(
      metrics.total_downtime_hours || 0
    ).toFixed(1)}h`;
    document.getElementById("teamEfficiency").textContent = `${(
      metrics.team_efficiency || 0
    ).toFixed(1)}%`;

    // Update old tasks count
    document.getElementById("oldTasks").textContent = metrics.old_tasks || 0;

    // Update subtexts
    const expectedHours = (metrics.members_analyzed || 0) * 8; // 8 hours per member
    document.getElementById("activeHoursSubtext").textContent = `of ${expectedHours}h expected`;

    const inactivePeriods = metrics.members_with_downtime || 0;
    document.getElementById(
      "downtimeSubtext"
    ).textContent = `${inactivePeriods}+ hour inactive periods`;

    document.getElementById("oldTasksSubtext").textContent = "Tasks older than 7 days";
    document.getElementById("efficiencySubtext").textContent = "Active vs total working time";

    // Update members subtext based on current status
    const currentlyActive =
      (metrics.members_analyzed || 0) -
      (metrics.currently_inactive ? metrics.currently_inactive.length : 0);
    document.getElementById("membersSubtext").textContent = `Currently being tracked`;
  },

  // updateDetailedStats(data) {
  //   const metrics = data.team_metrics || {};
  //   const detailedData = data.detailed_data || {};

  //   // Update timing analysis
  //   document.getElementById("currentTime").textContent = utils.formatTime(new Date());
  //   document.getElementById("analysisDateDetail").textContent = utils.formatDate(data.date);
  //   document.getElementById("totalActiveTime").textContent = utils.formatDuration(
  //     metrics.total_active_hours || 0
  //   );
  //   document.getElementById("totalDowntimeDetail").textContent = utils.formatDuration(
  //     metrics.total_downtime_hours || 0
  //   );

  //   // Calculate average downtime
  //   const avgDowntime =
  //     metrics.members_analyzed > 0 ? metrics.total_downtime_hours / metrics.members_analyzed : 0;
  //   document.getElementById("avgDowntime").textContent = utils.formatDuration(avgDowntime);

  //   // Update team statistics
  //   document.getElementById("totalMembers").textContent = metrics.members_analyzed || 0;

  //   // Count member statuses
  //   let activeCount = 0;
  //   let warningCount = 0;
  //   let criticalCount = 0;

  //   Object.values(detailedData).forEach((member) => {
  //     if (member.total_downtime_hours >= 4) {
  //       criticalCount++;
  //     } else if (member.total_downtime_hours >= 2) {
  //       warningCount++;
  //     } else if (member.total_active_hours > 0) {
  //       activeCount++;
  //     }
  //   });

  //   document.getElementById("activeMembers").textContent = activeCount;
  //   document.getElementById("warningMembers").textContent = warningCount;
  //   document.getElementById("criticalMembers").textContent = criticalCount;
  //   document.getElementById("inactiveCount").textContent = metrics.currently_inactive
  //     ? metrics.currently_inactive.length
  //     : 0;

  //   // Update member status list
  //   this.updateMemberStatusList(detailedData);
  // },
  updateDetailedStats(data) {
    const metrics = data.team_metrics || {};
    const detailedData = data.detailed_data || {};

    // Helper function to safely set text content
    const setText = (id, value) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    };

    // Update timing analysis
    setText("currentTime", utils.formatTime(new Date()));
    setText("analysisDateDetail", utils.formatDate(data.date));
    setText("totalActiveTime", utils.formatDuration(metrics.total_active_hours || 0));
    setText("totalDowntimeDetail", utils.formatDuration(metrics.total_downtime_hours || 0));

    // Calculate average downtime
    const avgDowntime =
      metrics.members_analyzed > 0 ? metrics.total_downtime_hours / metrics.members_analyzed : 0;
    setText("avgDowntime", utils.formatDuration(avgDowntime));

    // Update team statistics
    setText("totalMembers", metrics.members_analyzed || 0);

    // Count member statuses
    let activeCount = 0;
    let warningCount = 0;
    let criticalCount = 0;

    Object.values(detailedData).forEach((member) => {
      if (member.total_downtime_hours >= 4) {
        criticalCount++;
      } else if (member.total_downtime_hours >= 2) {
        warningCount++;
      } else if (member.total_active_hours > 0) {
        activeCount++;
      }
    });

    setText("activeMembers", activeCount);
    setText("warningMembers", warningCount);
    setText("criticalMembers", criticalCount);
    setText("inactiveCount", metrics.currently_inactive ? metrics.currently_inactive.length : 0);

    // Update member status list
    this.updateMemberStatusList(detailedData);
  },

  updateMemberStatusList(detailedData) {
    const statusList = document.getElementById("memberStatusList");
    if (!statusList) return;

    const members = Object.entries(detailedData).map(([name, data]) => ({
      name,
      downtime: data.total_downtime_hours || 0,
      active: data.total_active_hours || 0,
      status:
        data.total_downtime_hours >= 4
          ? "critical"
          : data.total_downtime_hours >= 2
          ? "warning"
          : "good",
    }));

    // Sort by downtime (highest first)
    members.sort((a, b) => b.downtime - a.downtime);

    statusList.innerHTML = members
      .map(
        (member) => `
          <div class="member-status-item ${member.status}">
              <span class="member-name">${member.name}</span>
              <span class="member-downtime">${utils.formatDuration(member.downtime)}</span>
          </div>
      `
      )
      .join("");
  },

  updateMemberGrid(detailedData) {
    const grid = document.getElementById("memberGrid");
    if (!grid) return;

    grid.innerHTML = "";

    Object.entries(detailedData).forEach(([member, data]) => {
      const card = this.createMemberCard(member, data);
      grid.appendChild(card);
    });
  },

  createMemberCard(name, data) {
    const status = this.getMemberStatus(data);
    const card = document.createElement("div");
    card.className = "member-card";

    card.innerHTML = `
          <div class="member-header">
              <h3 class="member-name">${name}</h3>
              <span class="member-status ${status.class}">${status.text}</span>
          </div>
          <div class="member-stats">
              <div class="stat">
                  <span class="stat-label">Active</span>
                  <span class="stat-value">${utils.formatDuration(data.total_active_hours)}</span>
              </div>
              <div class="stat">
                  <span class="stat-label">Downtime</span>
                  <span class="stat-value">${utils.formatDuration(data.total_downtime_hours)}</span>
              </div>
              <div class="stat">
                  <span class="stat-label">Tasks</span>
                  <span class="stat-value">${data.task_count || 0}</span>
              </div>
          </div>
          ${this.createMemberDetails(data)}
      `;

    return card;
  },

  getMemberStatus(data) {
    if (data.total_downtime_hours > 3) {
      return { text: "High Downtime", class: "status-danger" };
    } else if (data.total_downtime_hours > 2) {
      return { text: "Warning", class: "status-warning" };
    } else if (data.total_active_hours > 0) {
      return { text: "Active", class: "status-active" };
    } else {
      return { text: "Inactive", class: "status-inactive" };
    }
  },

  createMemberDetails(data) {
    if (!data.downtime_periods || data.downtime_periods.length === 0) {
      return "";
    }

    const periods = data.downtime_periods.slice(0, 3);
    const details = periods
      .map((period) => {
        const start = utils.formatTime(period.start);
        const end = utils.formatTime(period.end);
        return `<div class="downtime-period">${start} - ${end} (${utils.formatDuration(
          period.duration_hours
        )})</div>`;
      })
      .join("");

    return `
          <div class="member-details">
              <div class="details-title">Recent Downtime:</div>
              ${details}
              ${
                data.downtime_periods.length > 3
                  ? `<div class="more-periods">+${data.downtime_periods.length - 3} more</div>`
                  : ""
              }
          </div>
      `;
  },

  async loadAlerts(date) {
    try {
      const response = await api.getAlerts(date);
      this.updateAlerts(response.alerts || []);
    } catch (error) {
      console.error("Failed to load alerts:", error);
    }
  },

  updateAlerts(alerts) {
    // Update priority alerts
    const criticalMembers = [];
    const downtimeInfo = [];

    if (this.currentData && this.currentData.detailed_data) {
      Object.entries(this.currentData.detailed_data).forEach(([member, data]) => {
        if (data.total_downtime_hours >= 4) {
          criticalMembers.push(member);
        }
        if (data.downtime_periods && data.downtime_periods.length > 0) {
          const totalDowntime = data.total_downtime_hours;
          downtimeInfo.push({
            member: member,
            hours: totalDowntime,
            periods: data.downtime_periods.length,
          });
        }
      });
    }

    // Update critical alert
    const criticalDetails = document.getElementById("criticalAlertDetails");
    if (criticalDetails) {
      if (criticalMembers.length > 0) {
        criticalDetails.innerHTML = `${
          criticalMembers.length
        } member(s) with 4+ hours downtime: <strong>${criticalMembers.join(", ")}</strong>`;
      } else {
        criticalDetails.innerHTML = "No critical downtime detected";
      }
    }

    // Update productivity alert
    const productivityDetails = document.getElementById("productivityAlertDetails");
    if (productivityDetails) {
      if (downtimeInfo.length > 0) {
        const avgDowntime =
          downtimeInfo.reduce((sum, info) => sum + info.hours, 0) / downtimeInfo.length;
        productivityDetails.innerHTML = `Team average downtime is ${avgDowntime.toFixed(1)} hours`;
      } else {
        productivityDetails.innerHTML = "Team productivity is optimal";
      }
    }

    // Update individual alerts list
    const alertsList = document.getElementById("alertsList");
    if (alertsList && alerts.length > 0) {
      alertsList.innerHTML = `
              <div class="alerts-subsection">
                  <h4>[ALERT] ALERTS</h4>
                  ${alerts
                    .map(
                      (alert) => `
                      <div class="alert-item ${alert.type}">
                          <span class="alert-time">[${utils.formatTime(alert.timestamp)}]</span>
                          <span class="alert-text">${alert.message}</span>
                      </div>
                  `
                    )
                    .join("")}
              </div>
          `;
    }
  },

  getAlertIcon(type) {
    const icons = {
      danger: "exclamation-circle",
      warning: "exclamation-triangle",
      info: "info-circle",
      success: "check-circle",
    };
    return icons[type] || "bell";
  },

  dismissAlert(button) {
    const alert = button.closest(".alert");
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 300);
  },

  clearAlerts() {
    const container = document.getElementById("alertsContainer");
    if (container) {
      container.innerHTML = '<div class="no-alerts">No active alerts</div>';
    }
  },

  switchTab(tabElement) {
    // Update active states
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((content) => content.classList.remove("active"));

    tabElement.classList.add("active");
    const tabId = tabElement.getAttribute("data-tab") + "Tab";
    document.getElementById(tabId).classList.add("active");

    // Load tab-specific data if needed
    const tabName = tabElement.getAttribute("data-tab");
    this.loadTabData(tabName);
  },

  async loadTabData(tabName) {
    switch (tabName) {
      case "projects":
        // Load projects data
        break;
      case "websites":
        // Load websites data
        break;
      case "calendar":
        // Load calendar data
        break;
    }
  },

  toggleView(button) {
    const view = button.getAttribute("data-view");
    const grid = document.getElementById("memberGrid");

    // Update button states
    document.querySelectorAll(".view-btn").forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");

    // Update grid class
    if (view === "list") {
      grid.classList.add("list-view");
    } else {
      grid.classList.remove("list-view");
    }
  },

  showWeekendMessage() {
    const container = document.getElementById("clickupTab");
    container.innerHTML = `
          <div class="weekend-message">
              <i class="fas fa-calendar-week"></i>
              <h2>Weekend Day</h2>
              <p>Limited analysis available for weekends. Select a weekday for full team analytics.</p>
              <button class="btn-primary" onclick="datePicker.setDateByDays(-1)">
                  Go to Last Weekday
              </button>
          </div>
      `;
  },

  showLoading(show) {
    const loading = document.getElementById("loadingScreen");
    if (loading) {
      loading.style.display = show ? "flex" : "none";
    }
  },

  showError(message) {
    const errorElement = document.getElementById("errorText");
    const errorContainer = document.getElementById("errorMessage");

    if (errorElement && errorContainer) {
      errorElement.textContent = message;
      errorContainer.style.display = "block";

      setTimeout(() => {
        errorContainer.style.display = "none";
      }, 5000);
    }

    utils.showNotification(message, "error");
  },

  updateLastUpdated() {
    const element = document.getElementById("lastUpdated");
    if (element) {
      element.textContent = utils.formatTime(new Date());
    }
  },

  refreshData() {
    this.loadData(datePicker.getSelectedDate());
    utils.showNotification("Dashboard refreshed", "success");
  },

  async exportData() {
    try {
      const startDate = datePicker.getSelectedDate();
      const endDate = datePicker.getSelectedDate();
      await api.exportData(startDate, endDate, "csv");
      utils.showNotification("Data exported successfully", "success");
    } catch (error) {
      utils.showNotification("Failed to export data", "error");
    }
  },

  startAutoRefresh() {
    // Refresh every 5 minutes
    this.refreshInterval = setInterval(() => {
      this.loadData(datePicker.getSelectedDate());
    }, 5 * 60 * 1000);
  },

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },

  // Modal handlers (placeholders)
  showAddProjectModal() {
    utils.showNotification("Add Project feature coming soon", "info");
  },

  showAddWebsiteModal() {
    utils.showNotification("Add Website feature coming soon", "info");
  },
};

// Initialize dashboard when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  // Wait a bit for all scripts to load
  setTimeout(() => {
    if (window.dashboard) {
      dashboard.init();
    } else {
      console.error("Dashboard module not properly loaded");
    }
  }, 100);
});
