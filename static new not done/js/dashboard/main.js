// Main dashboard controller

const theme = {
  init() {
    const root = document.documentElement;
    const toggle = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("theme") || "light";

    root.classList.remove("light", "dark");
    root.classList.add(savedTheme);
    toggle.checked = savedTheme === "dark";

    toggle.addEventListener("change", () => {
      const newTheme = toggle.checked ? "dark" : "light";
      root.classList.remove("light", "dark");
      root.classList.add(newTheme);
      localStorage.setItem("theme", newTheme);
    });
  },
};

window.dashboard = {
  currentData: null,
  refreshInterval: null,

  init() {
    // Initialize modules
    theme.init();
    datePicker.init();
    charts.init();

    // Setup event listeners
    this.setupEventListeners();

    // Load initial data
    this.loadData(datePicker.getSelectedDate());

    // Setup auto-refresh
    this.startAutoRefresh();

    // Setup resize handler
    window.addEventListener(
      "resize",
      utils.debounce(() => {
        charts.resize();
      }, 250)
    );
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
      const data = await api.getDashboardData(date);
      this.currentData = data;

      if (data.is_weekend) {
        this.showWeekendMessage();
      } else {
        this.updateDashboard(data);
        this.loadAlerts(date);
      }

      this.updateLastUpdated();
    } catch (error) {
      this.showError("Failed to load dashboard data");
      console.error("Load data error:", error);
    } finally {
      this.showLoading(false);
    }
  },

  updateDashboard(data) {
    this.updateKPIs(data.team_metrics || {});
    charts.updateAll(data);
    this.updateMemberGrid(data.detailed_data || {});
    document.getElementById("clickupTab").style.display = "block";
  },

  updateKPIs(metrics) {
    document.getElementById("membersAnalyzed").textContent = metrics.members_analyzed || 0;
    document.getElementById("totalActiveHours").textContent = utils.formatDuration(
      metrics.total_active_hours || 0
    );
    document.getElementById("totalDowntime").textContent = utils.formatDuration(
      metrics.total_downtime_hours || 0
    );
    document.getElementById("teamEfficiency").textContent = `${(
      metrics.team_efficiency || 0
    ).toFixed(1)}%`;

    const efficiencyBar = document.getElementById("efficiencyProgress");
    if (efficiencyBar) {
      efficiencyBar.style.width = `${metrics.team_efficiency || 0}%`;
    }
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
                    <span class="stat-value">${utils.formatDuration(
                      data.total_downtime_hours
                    )}</span>
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
    if (!data.downtime_periods || data.downtime_periods.length === 0) return "";

    const periods = data.downtime_periods
      .slice(0, 3)
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
                ${periods}
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
    const container = document.getElementById("alertsContainer");
    if (!container) return;

    if (alerts.length === 0) {
      container.innerHTML = '<div class="no-alerts">No active alerts</div>';
      return;
    }

    container.innerHTML = alerts
      .map(
        (alert) => `
            <div class="alert alert-${alert.type}">
                <i class="fas fa-${this.getAlertIcon(alert.type)}"></i>
                <div class="alert-content">
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${utils.formatTime(alert.timestamp)}</div>
                </div>
                <button class="alert-dismiss" onclick="dashboard.dismissAlert(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `
      )
      .join("");
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
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((content) => content.classList.remove("active"));

    tabElement.classList.add("active");
    const tabId = tabElement.getAttribute("data-tab") + "Tab";
    document.getElementById(tabId).classList.add("active");

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

    document.querySelectorAll(".view-btn").forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");

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
    this.refreshInterval = setInterval(() => {
      this.loadData(datePicker.getSelectedDate());
    }, 5 * 60 * 1000);
  },

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },

  showAddProjectModal() {
    utils.showNotification("Add Project feature coming soon", "info");
  },

  showAddWebsiteModal() {
    utils.showNotification("Add Website feature coming soon", "info");
  },
};

document.addEventListener("DOMContentLoaded", () => {
  dashboard.init();
});
