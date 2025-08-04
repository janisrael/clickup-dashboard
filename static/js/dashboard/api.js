class DashboardAPI {
  async fetchData(date) {
    const dateParam = date ? `?date=${date.toISOString().split("T")[0]}` : "";
    const response = await fetch(`/api/dashboard-data${dateParam}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async refreshData() {
    const response = await fetch("/api/refresh");
    if (!response.ok) {
      throw new Error("Failed to refresh data");
    }
    return await response.json();
  }
}
