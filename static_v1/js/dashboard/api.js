// API module for handling all backend communications
window.api = {
  // Base configuration
  baseURL: "",

  // Fetch wrapper with error handling
  async fetch(url, options = {}) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  },

  // Dashboard data
  async getDashboardData(date) {
    return this.fetch(`/api/dashboard-data?date=${date}`);
  },

  // Alerts
  async getAlerts(date) {
    return this.fetch(`/api/alerts?date=${date}`);
  },

  // Projects
  async getProjects() {
    return this.fetch("/api/projects");
  },

  async createProject(project) {
    return this.fetch("/api/projects", {
      method: "POST",
      body: JSON.stringify(project),
    });
  },

  async updateProject(id, project) {
    return this.fetch(`/api/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(project),
    });
  },

  async deleteProject(id) {
    return this.fetch(`/api/projects/${id}`, {
      method: "DELETE",
    });
  },

  // Websites
  async getWebsites() {
    return this.fetch("/api/websites");
  },

  async createWebsite(website) {
    return this.fetch("/api/websites", {
      method: "POST",
      body: JSON.stringify(website),
    });
  },

  async updateWebsite(id, website) {
    return this.fetch(`/api/websites/${id}`, {
      method: "PUT",
      body: JSON.stringify(website),
    });
  },

  async deleteWebsite(id) {
    return this.fetch(`/api/websites/${id}`, {
      method: "DELETE",
    });
  },

  // Calendar events
  async getCalendarEvents(month, year) {
    return this.fetch(`/api/calendar?month=${month}&year=${year}`);
  },

  // Team members
  async getTeamMembers() {
    return this.fetch("/api/team-members");
  },

  // Export data
  async exportData(startDate, endDate, format = "csv") {
    const params = new URLSearchParams({
      start: startDate,
      end: endDate,
      format: format,
    });

    const response = await fetch(`/api/export?${params}`);
    const blob = await response.blob();

    // Download the file
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dashboard-export-${startDate}-to-${endDate}.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
  },
};
