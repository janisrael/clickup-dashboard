// Date picker module
window.datePicker = {
  selectedDate: new Date().toISOString().split("T")[0],
  picker: null,

  init() {
    this.picker = flatpickr("#datePicker", {
      defaultDate: new Date(),
      dateFormat: "Y-m-d",
      maxDate: new Date(),
      onChange: (selectedDates, dateStr) => {
        this.selectedDate = dateStr;
        this.updateQuickButtons();
        window.dashboard.loadData(dateStr);
      },
    });

    this.setupQuickButtons();
    this.updateAnalysisDate();
  },

  setupQuickButtons() {
    const buttons = document.querySelectorAll(".quick-date-btn");
    buttons.forEach((button) => {
      button.addEventListener("click", (e) => {
        const days = parseInt(e.target.getAttribute("data-days"));
        this.setDateByDays(days);
      });
    });
  },

  setDateByDays(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    this.picker.setDate(date);
    this.selectedDate = date.toISOString().split("T")[0];
    this.updateQuickButtons();
  },

  updateQuickButtons() {
    const buttons = document.querySelectorAll(".quick-date-btn");
    const today = new Date().toISOString().split("T")[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

    buttons.forEach((button) => {
      button.classList.remove("active");
      const days = parseInt(button.getAttribute("data-days"));

      if (days === 0 && this.selectedDate === today) {
        button.classList.add("active");
      } else if (days === -1 && this.selectedDate === yesterday) {
        button.classList.add("active");
      }
    });
  },

  updateAnalysisDate() {
    const dateElement = document.getElementById("analysisDate");
    if (dateElement) {
      dateElement.textContent = utils.formatDate(this.selectedDate);
    }
  },

  getSelectedDate() {
    return this.selectedDate;
  },
};
