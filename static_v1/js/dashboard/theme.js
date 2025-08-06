// Theme management module
window.theme = {
  currentTheme: "light",

  init() {
    // Check for saved theme preference or default to light
    const savedTheme = localStorage.getItem("theme") || "light";
    this.setTheme(savedTheme);

    // Setup theme toggle button
    const toggleButton = document.getElementById("themeToggle");
    if (toggleButton) {
      toggleButton.addEventListener("click", () => this.toggle());
    }
  },

  setTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);

    // Update icon
    const icon = document.getElementById("themeIcon");
    if (icon) {
      icon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
    }

    // Update theme toggle button title
    const toggleButton = document.getElementById("themeToggle");
    if (toggleButton) {
      toggleButton.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }

    // Update Chart.js theme
    this.updateChartTheme(theme);
  },

  toggle() {
    const newTheme = this.currentTheme === "light" ? "dark" : "light";
    this.setTheme(newTheme);

    // Animate the transition
    this.animateTransition();
  },

  animateTransition() {
    const button = document.getElementById("themeToggle");
    if (button) {
      button.style.transform = "rotate(360deg)";
      setTimeout(() => {
        button.style.transform = "rotate(0deg)";
      }, 300);
    }
  },

  updateChartTheme(theme) {
    if (typeof Chart === "undefined") return;

    // Update chart defaults
    if (window.charts && window.charts.updateChartDefaults) {
      window.charts.updateChartDefaults();
    }

    // Update all existing charts
    if (window.charts && window.charts.instances) {
      Object.values(window.charts.instances).forEach((chart) => {
        if (chart) {
          chart.update("none"); // Update without animation
        }
      });
    }
  },

  getTheme() {
    return this.currentTheme;
  },

  isDark() {
    return this.currentTheme === "dark";
  },
};
