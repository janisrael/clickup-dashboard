// Enhanced Main dashboard controller - static_v1/js/dashboard/main.js
window.dashboard = {
  currentData: null,
  refreshInterval: null,

  init() {
    console.log("Enhanced Dashboard init started...");

    // Initialize modules
    this.initializeModules();

    // Setup event listeners
    this.setupEventListeners();

    // Load initial data
    // this.loadData();

    // Setup auto-refresh
    // this.startAutoRefresh();

    // Setup resize handler
    this.setupResizeHandler();

    console.log("Enhanced Dashboard initialized successfully");
  },

  initializeModules() {
    // Initialize charts module
    if (window.charts && typeof window.charts.init === "function") {
      charts.init();
    } else {
      console.warn("Charts module not available");
    }

    // Initialize date picker
    if (window.datePicker && typeof window.datePicker.init === "function") {
      datePicker.init();
    } else {
      this.setupFallbackDatePicker();
    }

    // Initialize theme (if available)
    if (window.theme && typeof window.theme.init === "function") {
      theme.init();
    } else {
      // Set default dark theme
      document.documentElement.setAttribute("data-theme", "dark");
    }
  },

  setupFallbackDatePicker() {
    // Fallback date picker setup if flatpickr is not available
    const dateInput = document.getElementById("datePicker");
    if (dateInput) {
      dateInput.type = "date";
      dateInput.value = new Date().toISOString().split("T")[0];
      dateInput.max = new Date().toISOString().split("T")[0];

      dateInput.addEventListener("change", (e) => {
        this.loadData(e.target.value);
        this.updateQuickButtons(e.target.value);
      });
    }
  },

  setupEventListeners() {
    // Tab switching
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", (e) => this.switchTab(e.target));
    });

    // Quick date buttons
    document.querySelectorAll(".quick-date-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const days = parseInt(e.target.getAttribute("data-days"));
        this.setDateByDays(days);
      });
    });

    // Timeline zoom buttons
    document.querySelectorAll(".timeline-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const range = this.extractZoomRange(e.target);
        if (range && window.charts && window.charts.zoomTimeline) {
          charts.zoomTimeline(range);
        }
      });
    });

    // Search functionality (if search input exists)
    const searchInput = document.getElementById("taskSearch");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        if (window.charts && window.charts.searchTasks) {
          charts.searchTasks(e.target.value);
        }
      });
    }
  },

  setupResizeHandler() {
    if (window.utils && window.utils.debounce) {
      window.addEventListener(
        "resize",
        utils.debounce(() => {
          if (window.charts && window.charts.resize) {
            charts.resize();
          }
        }, 250)
      );
    } else {
      // Fallback without debounce
      window.addEventListener("resize", () => {
        setTimeout(() => {
          if (window.charts && window.charts.resize) {
            charts.resize();
          }
        }, 250);
      });
    }
  },

  async loadData(date = null) {
    this.showLoading(true);

    try {
      const selectedDate = date || this.getCurrentDate();
      console.log(`Loading data for date: ${selectedDate}`);

      // Try to fetch from API first
      const data = await this.fetchDashboardData(selectedDate);

      this.currentData = data;
      this.updateDashboard(data);
      this.updateLastUpdated();
    } catch (error) {
      console.error("Load data error:", error);
      this.showError("Failed to load dashboard data");

      // Fallback to sample data for demo
      this.loadSampleData();
    } finally {
      this.showLoading(false);
    }
  },

  async fetchDashboardData(date) {
    try {
      const response = await fetch(`/api/dashboard-data?date=${date}`);

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.warn("API fetch failed, using sample data:", error);
      throw error;
    }
  },

  loadSampleData() {
    console.log("Loading sample data for demo...");

    // Enhanced sample data with proper task-level breakdown
    const sampleData = {
      timestamp: new Date().toISOString(),
      date: new Date().toISOString().split("T")[0],
      members_analyzed: 2,
      team_metrics: {
        total_active_hours: 15.0,
        total_downtime_hours: 0.0,
        expected_working_hours: 15.0,
        team_efficiency: 100.0,
        currently_inactive: [],
        total_tasks: 8,
        total_active_tasks: 8,
      },
      detailed_data: {
        Arif: {
          username: "Arif",
          total_tasks: 4,
          active_tasks: 4,
          total_active_hours: 7.5,
          total_downtime_hours: 0.0,
          in_progress_periods: [
            {
              start: this.getTodayDateTime("09:00"),
              end: this.getTodayDateTime("11:30"),
              task_name: "create responsive content sizes",
              task_id: "task_001",
              duration_hours: 2.5,
              status: "in progress",
              project_name: "Web Development",
              list_name: "Frontend Tasks",
            },
            {
              start: this.getTodayDateTime("13:30"),
              end: this.getTodayDateTime("16:00"),
              task_name: "Design And Implementation",
              task_id: "task_002",
              duration_hours: 2.5,
              status: "in progress",
              project_name: "UI/UX Design",
              list_name: "Development",
            },
            {
              start: this.getTodayDateTime("16:30"),
              end: this.getTodayDateTime("18:00"),
              task_name: "Content Integration",
              task_id: "task_003",
              duration_hours: 1.5,
              status: "in progress",
              project_name: "CMS Setup",
              list_name: "Backend Tasks",
            },
            {
              start: this.getTodayDateTime("11:45"),
              end: this.getTodayDateTime("13:00"),
              task_name: "create __pre variables and values",
              task_id: "task_004",
              duration_hours: 1.25,
              status: "staging",
              project_name: "Frontend Framework",
              list_name: "Testing",
            },
          ],
          downtime_periods: [],
          task_details: [
            {
              id: "task_001",
              name: "create responsive content sizes",
              status: "in progress",
              project_name: "Web Development",
              list_name: "Frontend Tasks",
            },
            {
              id: "task_002",
              name: "Design And Implementation",
              status: "in progress",
              project_name: "UI/UX Design",
              list_name: "Development",
            },
            {
              id: "task_003",
              name: "Content Integration",
              status: "in progress",
              project_name: "CMS Setup",
              list_name: "Backend Tasks",
            },
            {
              id: "task_004",
              name: "create __pre variables and values",
              status: "staging",
              project_name: "Frontend Framework",
              list_name: "Testing",
            },
          ],
        },
        Jan: {
          username: "Jan",
          total_tasks: 4,
          active_tasks: 4,
          total_active_hours: 7.5,
          total_downtime_hours: 0.0,
          in_progress_periods: [
            {
              start: this.getTodayDateTime("09:00"),
              end: this.getTodayDateTime("11:00"),
              task_name: "Organization payment system",
              task_id: "task_005",
              duration_hours: 2.0,
              status: "in progress",
              project_name: "Payment Integration",
              list_name: "Backend Features",
            },
            {
              start: this.getTodayDateTime("11:30"),
              end: this.getTodayDateTime("14:00"),
              task_name: "MileStone(Organizer side)",
              task_id: "task_006",
              duration_hours: 2.5,
              status: "in progress",
              project_name: "Event Management",
              list_name: "Core Features",
            },
            {
              start: this.getTodayDateTime("14:30"),
              end: this.getTodayDateTime("16:30"),
              task_name: "Add Delete ticket capability",
              task_id: "task_007",
              duration_hours: 2.0,
              status: "in progress",
              project_name: "Ticketing System",
              list_name: "User Management",
            },
            {
              start: this.getTodayDateTime("16:45"),
              end: this.getTodayDateTime("17:45"),
              task_name: "MileStone(P1 MVP)",
              task_id: "task_008",
              duration_hours: 1.0,
              status: "in progress",
              project_name: "MVP Development",
              list_name: "Milestones",
            },
          ],
          downtime_periods: [],
          task_details: [
            {
              id: "task_005",
              name: "Organization payment system",
              status: "in progress",
              project_name: "Payment Integration",
              list_name: "Backend Features",
            },
            {
              id: "task_006",
              name: "MileStone(Organizer side)",
              status: "in progress",
              project_name: "Event Management",
              list_name: "Core Features",
            },
            {
              id: "task_007",
              name: "Add Delete ticket capability",
              status: "in progress",
              project_name: "Ticketing System",
              list_name: "User Management",
            },
            {
              id: "task_008",
              name: "MileStone(P1 MVP)",
              status: "in progress",
              project_name: "MVP Development",
              list_name: "Milestones",
            },
          ],
        },
      },
    };

    this.currentData = sampleData;
    this.updateDashboard(sampleData);
  },

  updateDashboard(data) {
    console.log("Updating dashboard with data:", data);

    // Update KPIs
    this.updateKPIs(data.team_metrics || {});

    // Update charts and timeline
    if (window.charts && window.charts.updateAll) {
      charts.updateAll(data);
    } else {
      console.warn("Charts module updateAll method not available");
    }

    // Update member grid
    this.updateMemberGrid(data.detailed_data || {});

    // Show main content
    const clickupTab = document.getElementById("clickupTab");
    if (clickupTab) {
      clickupTab.style.display = "block";
    }
  },

  updateKPIs(metrics) {
    const updates = {
      membersAnalyzed: metrics.members_analyzed || 0,
      totalActiveHours: `${(metrics.total_active_hours || 0).toFixed(1)}h`,
      totalDowntime: `${(metrics.total_downtime_hours || 0).toFixed(1)}h`,
      activeTasks: metrics.total_active_tasks || 0,
      teamEfficiency: `${(metrics.team_efficiency || 0).toFixed(1)}%`,
    };

    Object.entries(updates).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) {
        element.textContent = value;
      }
    });
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
    const card = document.createElement("div");
    card.className = "member-card";

    const status = this.getMemberStatus(data);
    const uniqueProjects = this.getUniqueProjects(data);

    card.innerHTML = `
          <div class="member-card-header">
              <div class="member-card-name">${name}</div>
              <div class="member-status ${status.class}">${status.text}</div>
          </div>
          <div class="member-card-stats">
              <div class="member-stat">
                  <span class="member-stat-label">Active</span>
                  <span class="member-stat-value">${(data.total_active_hours || 0).toFixed(
                    1
                  )}h</span>
              </div>
              <div class="member-stat">
                  <span class="member-stat-label">Tasks</span>
                  <span class="member-stat-value">${data.active_tasks || 0}</span>
              </div>
              <div class="member-stat">
                  <span class="member-stat-label">Projects</span>
                  <span class="member-stat-value">${uniqueProjects}</span>
              </div>
          </div>
      `;

    return card;
  },

  getMemberStatus(data) {
    const activeHours = data.total_active_hours || 0;
    const activeTasks = data.active_tasks || 0;

    if (activeTasks === 0) {
      return { text: "Inactive", class: "status-danger" };
    } else if (activeHours >= 6) {
      return { text: "Highly Active", class: "status-active" };
    } else if (activeHours >= 3) {
      return { text: "Active", class: "status-active" };
    } else {
      return { text: "Limited Activity", class: "status-warning" };
    }
  },

  getUniqueProjects(data) {
    if (!data.task_details) return 0;
    const projects = new Set(data.task_details.map((task) => task.project_name || "Unknown"));
    return projects.size;
  },

  switchTab(tabElement) {
    // Update active states
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((content) => content.classList.remove("active"));

    tabElement.classList.add("active");
    const tabId = tabElement.getAttribute("data-tab") + "Tab";
    const tabContent = document.getElementById(tabId);
    if (tabContent) {
      tabContent.classList.add("active");
    }

    // Load tab-specific data if needed
    const tabName = tabElement.getAttribute("data-tab");
    this.loadTabData(tabName);
  },

  async loadTabData(tabName) {
    console.log(`Loading data for tab: ${tabName}`);

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

  setDateByDays(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    const dateString = date.toISOString().split("T")[0];

    // Update date picker
    const dateInput = document.getElementById("datePicker");
    if (dateInput) {
      dateInput.value = dateString;
    }

    // Load data for new date
    this.loadData(dateString);
    this.updateQuickButtons(dateString);
  },

  updateQuickButtons(selectedDate = null) {
    const today = new Date().toISOString().split("T")[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];
    const current = selectedDate || this.getCurrentDate();

    document.querySelectorAll(".quick-date-btn").forEach((btn) => {
      btn.classList.remove("active");
      const days = parseInt(btn.getAttribute("data-days"));

      if (days === 0 && current === today) {
        btn.classList.add("active");
      } else if (days === -1 && current === yesterday) {
        btn.classList.add("active");
      } else if (days === -7) {
        const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0];
        if (current === weekAgo) {
          btn.classList.add("active");
        }
      }
    });
  },

  extractZoomRange(button) {
    const onclick = button.getAttribute("onclick");
    if (onclick) {
      const match = onclick.match(/zoomTimeline\(['"]([^'"]+)['"]\)/);
      return match ? match[1] : null;
    }
    return null;
  },

  getCurrentDate() {
    const dateInput = document.getElementById("datePicker");
    if (dateInput && dateInput.value) {
      return dateInput.value;
    }
    return new Date().toISOString().split("T")[0];
  },

  getTodayDateTime(timeString) {
    const today = new Date().toISOString().split("T")[0];
    return `${today}T${timeString}:00`;
  },

  updateLastUpdated() {
    const element = document.getElementById("lastUpdated");
    if (element) {
      const now = new Date();
      element.textContent = `Last updated: ${now.toLocaleDateString()} at ${now.toLocaleTimeString()}`;
    }
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

    // Also show a notification if utils is available
    if (window.utils && window.utils.showNotification) {
      utils.showNotification(message, "error");
    }
  },

  refreshData() {
    console.log("Refreshing dashboard data...");
    this.loadData();

    if (window.utils && window.utils.showNotification) {
      utils.showNotification("Dashboard refreshed", "success");
    }
  },

  async exportData() {
    try {
      console.log("Exporting dashboard data...");

      // Prepare export data
      const exportData = {
        timestamp: new Date().toISOString(),
        date: this.getCurrentDate(),
        dashboard_data: this.currentData,
        timeline_data:
          window.charts && window.charts.exportTimelineData ? charts.exportTimelineData() : null,
      };

      // Create and download file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `clickup-dashboard-${this.getCurrentDate()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      if (window.utils && window.utils.showNotification) {
        utils.showNotification("Data exported successfully", "success");
      }
    } catch (error) {
      console.error("Export error:", error);
      this.showError("Failed to export data");
    }
  },

  startAutoRefresh() {
    // Refresh every 5 minutes
    this.refreshInterval = setInterval(() => {
      console.log("Auto-refreshing dashboard...");
      this.loadData();
    }, 5 * 60 * 1000);
  },

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  },

  // Task management functions
  filterTasksByMember(memberName) {
    const memberSections = document.querySelectorAll(".member-section");

    memberSections.forEach((section) => {
      const header = section.querySelector(".member-name");
      if (header) {
        const sectionMember = header.textContent.trim();
        if (memberName === "all" || sectionMember.includes(memberName)) {
          section.style.display = "";
        } else {
          section.style.display = "none";
        }
      }
    });
  },

  filterTasksByStatus(status) {
    const taskRows = document.querySelectorAll(".task-row");

    taskRows.forEach((row) => {
      const statusElement = row.querySelector(".task-status");
      if (statusElement) {
        const taskStatus = statusElement.textContent.trim().toLowerCase();
        if (status === "all" || taskStatus.includes(status.toLowerCase())) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      }
    });
  },

  highlightLongRunningTasks(hoursThreshold = 4) {
    const timeBlocks = document.querySelectorAll(".time-block");

    timeBlocks.forEach((block) => {
      const title = block.getAttribute("title");
      const durationMatch = title.match(/\((\d+\.?\d*)h\)/);

      if (durationMatch) {
        const duration = parseFloat(durationMatch[1]);
        if (duration >= hoursThreshold) {
          block.classList.add("long-running");
          block.style.border = "2px solid #f59e0b";
          block.style.boxShadow = "0 0 10px rgba(245, 158, 11, 0.5)";
        }
      }
    });
  },

  // Analytics and insights
  generateInsights() {
    if (!this.currentData || !this.currentData.detailed_data) {
      return [];
    }

    const insights = [];
    const members = Object.entries(this.currentData.detailed_data);

    // Most productive member
    let mostProductiveMember = null;
    let maxHours = 0;

    members.forEach(([name, data]) => {
      const hours = data.total_active_hours || 0;
      if (hours > maxHours) {
        maxHours = hours;
        mostProductiveMember = name;
      }
    });

    if (mostProductiveMember) {
      insights.push({
        type: "positive",
        title: "Most Productive Today",
        message: `${mostProductiveMember} with ${maxHours.toFixed(1)} hours of active work`,
      });
    }

    // Project diversity analysis
    const allProjects = new Set();
    members.forEach(([name, data]) => {
      if (data.task_details) {
        data.task_details.forEach((task) => {
          if (task.project_name) {
            allProjects.add(task.project_name);
          }
        });
      }
    });

    insights.push({
      type: "info",
      title: "Project Diversity",
      message: `Team is working on ${allProjects.size} different projects today`,
    });

    // Task completion rate estimate
    const totalTasks = this.currentData.team_metrics?.total_tasks || 0;
    const activeTasks = this.currentData.team_metrics?.total_active_tasks || 0;

    if (totalTasks > 0) {
      const activePercent = ((activeTasks / totalTasks) * 100).toFixed(1);
      insights.push({
        type: "metric",
        title: "Task Activity Rate",
        message: `${activePercent}% of tasks are currently active`,
      });
    }

    return insights;
  },

  displayInsights() {
    const insights = this.generateInsights();
    const container = document.getElementById("insightsContainer");

    if (!container || insights.length === 0) return;

    container.innerHTML = insights
      .map(
        (insight) => `
          <div class="insight-item insight-${insight.type}">
              <h4>${insight.title}</h4>
              <p>${insight.message}</p>
          </div>
      `
      )
      .join("");
  },

  // Cleanup and destroy
  destroy() {
    this.stopAutoRefresh();

    if (window.charts && window.charts.destroy) {
      charts.destroy();
    }

    // Remove event listeners
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.removeEventListener("click", this.switchTab);
    });

    console.log("Dashboard destroyed");
  },
};

// Global functions for button interactions
function refreshData() {
  if (window.dashboard) {
    window.dashboard.refreshData();
  }
}

function exportData() {
  if (window.dashboard) {
    window.dashboard.exportData();
  }
}

function zoomTimeline(range) {
  if (window.charts && window.charts.zoomTimeline) {
    charts.zoomTimeline(range);
  }
}

function toggleMemberView(viewType) {
  console.log("Toggle member view:", viewType);
  // Implementation for member view toggle
}

// Initialize dashboard when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing dashboard...");

  // Wait a bit for all scripts to load
  setTimeout(() => {
    if (window.dashboard) {
      dashboard.init();
    } else {
      console.error("Dashboard module not properly loaded");
    }
  }, 100);
});

// Handle page unload
window.addEventListener("beforeunload", () => {
  if (window.dashboard && window.dashboard.destroy) {
    dashboard.destroy();
  }
});
