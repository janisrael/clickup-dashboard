class DatePicker {
  constructor() {
    this.currentDate = new Date();
    this.init();
  }

  init() {
    this.picker = flatpickr("#datePicker", {
      dateFormat: "Y-m-d",
      defaultDate: this.currentDate,
      maxDate: "today",
      onChange: (selectedDates) => {
        this.currentDate = selectedDates[0];
        this.updateDateInfo();
        window.dashboard.loadData(this.getFormattedDate());
      },
    });

    document.getElementById("todayBtn").addEventListener("click", () => {
      this.currentDate = new Date();
      this.picker.setDate(this.currentDate);
      this.updateDateInfo();
      window.dashboard.loadData(this.getFormattedDate());
    });

    this.updateDateInfo();
  }

  updateDateInfo() {
    const dateInfo = document.getElementById("dateInfo");
    if (!dateInfo) return;

    const selectedDate = this.picker.formatDate(this.currentDate, "F j, Y");
    const apiDate = this.lastApiDate
      ? this.picker.formatDate(new Date(this.lastApiDate), "F j, Y")
      : "loading...";

    dateInfo.innerHTML = `
        <i class="fas fa-calendar-check"></i>
        <span>Selected: ${selectedDate} | Showing: ${apiDate}</span>
    `;
  }
  getFormattedDate() {
    // Ensure we're using UTC to avoid timezone issues
    return this.currentDate.toISOString().split("T")[0];
  }

  getFormattedDate() {
    return this.picker.formatDate(this.currentDate, "Y-m-d");
  }
}
