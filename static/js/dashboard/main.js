class Dashboard {
  constructor() {
    this.datePicker = new DatePicker();
    this.api = new DashboardAPI();
    this.charts = new ChartManager();
    this.currentDate = new Date();
    this.colors = {
      primary: "#4f46e5",
      success: "#10b981",
      warning: "#f59e0b",
      danger: "#ef4444",
      info: "#3b82f6",
      veryOld: "#ef4444",
      old: "#f59e0b",
      moderate: "#3b82f6",
      new: "#10b981",
      milestone: "#8b5cf6",
    };
    this.init();
  }

  init() {
    this.initTheme();
    this.initTabs();
    // this.loadData();
    this.setupEventListeners();
  }

  setupEventListeners() {
    window.addEventListener("resize", () => {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => {
        this.charts.resizeAll();
      }, 250);
    });

    // Fetch Data button - forces refresh
    document.getElementById("fetchDataBtn").addEventListener("click", () => {
      const selectedDate = document.getElementById("datePicker").value;
      this.loadData(selectedDate, true); // true forces refresh
    });

    // Today button - also forces refresh
    document.getElementById("todayBtn").addEventListener("click", () => {
      const today = new Date().toISOString().split("T")[0];
      document.getElementById("datePicker").value = today;
      this.loadData(today, true); // true forces refresh
    });
  }

  async loadData(date, forceRefresh = false) {
    showLoading();
    try {
      // Build the URL with optional date and refresh parameters
      let url = "/api/dashboard-data";
      const params = new URLSearchParams();

      if (date) {
        params.append("date", date);
      }
      if (forceRefresh) {
        params.append("refresh", "true");
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.renderDashboard(data);
    } catch (error) {
      showError(error.message);
      setTimeout(() => {
        this.renderDashboard(this.getSampleData());
      }, 1000);
    } finally {
      hideLoading();
    }
  }

  renderDashboard(data) {
    this.charts.renderAll(data);
    updateKPIs(data);
    renderDataStatus(data.analysis_context || {});
    updateAlerts(data);
    updateMemberStatus(data);
    updateDateInfo(data);
  }

  async refreshData() {
    showLoading();
    document.getElementById("loadingScreen").innerHTML = `
            <div class="spinner"></div>
            <p>Refreshing data...</p>
        `;

    try {
      await this.api.refreshData();
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await this.loadData();
    } catch (error) {
      showError("Refresh failed - showing possibly stale data");
    }
  }

  exportData() {
    // In a real implementation, this would export the current dashboard data
    alert("Export functionality would be implemented here");
  }

  initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    this.setTheme(savedTheme);

    document.getElementById("themeToggle").addEventListener("change", (e) => {
      const newTheme = e.target.checked ? "dark" : "light";
      this.setTheme(newTheme);
      localStorage.setItem("theme", newTheme);
    });
  }

  setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    this.charts.updateTheme();
  }

  initTabs() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        // Remove active class from all tabs and content
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

        // Add active class to clicked tab and corresponding content
        tab.classList.add("active");
        const tabId = tab.getAttribute("data-tab");
        document.getElementById(`${tabId}Tab`).classList.add("active");
      });
    });
  }
  getSampleData() {
    const now = new Date();
    const dateStr = now.toISOString().split("T")[0];
    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const dayOfWeek = days[now.getDay()];

    return {
      date: dateStr,
      day_of_week: dayOfWeek,
      is_weekend: [0, 6].includes(now.getDay()),
      timestamp: now.toISOString(),
      members_analyzed: 3,
      team_metrics: {
        total_active_hours: 24.5,
        total_downtime_hours: 3.2,
        team_efficiency: 75.3,
        expected_working_hours: 32,
        currently_inactive: ["Jan"],
        total_old_tasks: 5,
      },
      detailed_data: {
        Arif: {
          in_progress_periods: [
            {
              start: `${dateStr}T09:00:00`,
              end: `${dateStr}T12:30:00`,
              duration_hours: 3.5,
              task_name: "Implement payment gateway",
              task_age: 2,
              is_milestone: true,
            },
            {
              start: `${dateStr}T13:30:00`,
              end: `${dateStr}T17:00:00`,
              duration_hours: 3.5,
              task_name: "Fix checkout bugs",
              task_age: 5,
            },
          ],
          downtime_periods: [
            {
              start: `${dateStr}T12:30:00`,
              end: `${dateStr}T13:30:00`,
              duration_hours: 1,
              type: "Lunch",
            },
          ],
          task_metrics: {
            total_tasks: 12,
            milestone_tasks: 3,
            tasks_by_age: {
              very_old: 1,
              old: 2,
              moderate: 4,
              new: 5,
            },
          },
        },
        Jan: {
          in_progress_periods: [
            {
              start: `${dateStr}T10:00:00`,
              end: `${dateStr}T12:00:00`,
              duration_hours: 2,
              task_name: "Design new UI components",
              task_age: 1,
            },
          ],
          downtime_periods: [
            {
              start: `${dateStr}T12:00:00`,
              end: `${dateStr}T13:00:00`,
              duration_hours: 1,
              type: "Lunch",
            },
            {
              start: `${dateStr}T14:00:00`,
              end: `${dateStr}T17:00:00`,
              duration_hours: 3,
              type: "Meeting",
            },
          ],
          task_metrics: {
            total_tasks: 8,
            milestone_tasks: 1,
            tasks_by_age: {
              very_old: 2,
              old: 1,
              moderate: 3,
              new: 2,
            },
          },
        },
        Wiktor: {
          in_progress_periods: [
            {
              start: `${dateStr}T08:00:00`,
              end: `${dateStr}T12:00:00`,
              duration_hours: 4,
              task_name: "Database optimization",
              task_age: 10,
              is_milestone: true,
            },
            {
              start: `${dateStr}T13:00:00`,
              end: `${dateStr}T18:00:00`,
              duration_hours: 5,
              task_name: "API documentation",
              task_age: 3,
            },
          ],
          downtime_periods: [
            {
              start: `${dateStr}T12:00:00`,
              end: `${dateStr}T13:00:00`,
              duration_hours: 1,
              type: "Lunch",
            },
          ],
          task_metrics: {
            total_tasks: 15,
            milestone_tasks: 2,
            tasks_by_age: {
              very_old: 3,
              old: 4,
              moderate: 5,
              new: 3,
            },
          },
        },
      },
    };
  }
}

// Initialize when ready
document.addEventListener("DOMContentLoaded", () => {
  window.dashboard = new Dashboard();

  // Auto-refresh every 5 minutes
  //   setInterval(() => {
  //     window.dashboard.loadData();
  //   }, 5 * 60 * 1000);
});
