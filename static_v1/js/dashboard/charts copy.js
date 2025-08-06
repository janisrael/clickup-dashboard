// Enhanced Charts module for task-level timeline - static_v1/js/dashboard/charts.js
window.charts = {
  instances: {},
  currentZoom: "day",

  init() {
    // Set chart defaults for modern look
    Chart.defaults.font.family =
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.color = "#cbd5e1";
    Chart.defaults.borderColor = "#334155";
    this.updateChartDefaults();
  },

  updateChartDefaults() {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    Chart.defaults.color = isDark ? "#cbd5e1" : "#6b7280";
    Chart.defaults.borderColor = isDark ? "#334155" : "#e5e7eb";
    Chart.defaults.plugins.legend.labels.color = isDark ? "#cbd5e1" : "#6b7280";
    Chart.defaults.scale.grid.color = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
    Chart.defaults.scale.grid.borderColor = isDark ? "#334155" : "#e5e7eb";
  },

  // Task-Level Timeline Creation
  createTaskTimeline(detailedData) {
    const container = document.getElementById("taskTimeline");
    if (!container) return;

    container.innerHTML = "";

    if (!detailedData || Object.keys(detailedData).length === 0) {
      container.innerHTML =
        '<div class="no-activity">No task data available for the selected date</div>';
      return;
    }

    Object.entries(detailedData).forEach(([memberName, memberData]) => {
      const memberSection = this.createMemberTaskSection(memberName, memberData);
      container.appendChild(memberSection);
    });
  },

  createMemberTaskSection(memberName, memberData) {
    const section = document.createElement("div");
    section.className = "member-section";

    // Calculate stats
    const totalTasks = memberData.task_details ? memberData.task_details.length : 0;
    const activeTasks = memberData.active_tasks || 0;
    const activeHours = memberData.total_active_hours || 0;
    const uniqueProjects = this.getUniqueProjects(memberData);

    section.innerHTML = `
          <div class="member-header">
              <div class="member-name">
                  <i class="fas fa-user"></i>
                  ${memberName}
              </div>
              <div class="member-stats">
                  <div class="stat-item">
                      <i class="fas fa-tasks"></i>
                      <span class="stat-value">${activeTasks}</span> active tasks
                  </div>
                  <div class="stat-item">
                      <i class="fas fa-clock"></i>
                      <span class="stat-value">${activeHours.toFixed(1)}h</span> active
                  </div>
                  <div class="stat-item">
                      <i class="fas fa-project-diagram"></i>
                      <span class="stat-value">${uniqueProjects}</span> projects
                  </div>
                  <div class="stat-item">
                      <i class="fas fa-list"></i>
                      <span class="stat-value">${totalTasks}</span> total tasks
                  </div>
              </div>
          </div>
          <div class="task-rows" id="tasks-${memberName.replace(/\s+/g, "_")}">
          </div>
      `;

    const taskRowsContainer = section.querySelector(`#tasks-${memberName.replace(/\s+/g, "_")}`);

    // Create individual task rows - this is the key enhancement
    if (memberData.in_progress_periods && memberData.in_progress_periods.length > 0) {
      // Group tasks by project for better organization
      const tasksByProject = this.groupTasksByProject(memberData.in_progress_periods);

      Object.entries(tasksByProject).forEach(([projectName, tasks]) => {
        tasks.forEach((task) => {
          const taskRow = this.createIndividualTaskRow(task, memberName);
          taskRowsContainer.appendChild(taskRow);
        });
      });
    } else if (memberData.task_details && memberData.task_details.length > 0) {
      // Show tasks even if no active periods (fallback)
      memberData.task_details.slice(0, 4).forEach((task) => {
        const mockPeriod = {
          task_name: task.name,
          project_name: task.project_name || "Unknown Project",
          list_name: task.list_name || "Unknown List",
          status: task.status || "active",
          start: this.getTodayDateTime("09:00"),
          end: this.getTodayDateTime("17:00"),
          duration_hours: 2.5, // Estimated
          task_id: task.id,
        };
        const taskRow = this.createIndividualTaskRow(mockPeriod, memberName);
        taskRowsContainer.appendChild(taskRow);
      });
    } else {
      taskRowsContainer.innerHTML = '<div class="no-activity">No active tasks</div>';
    }

    return section;
  },

  createIndividualTaskRow(taskPeriod, memberName) {
    const row = document.createElement("div");
    row.className = "task-row";
    row.setAttribute("data-task-id", taskPeriod.task_id || "");
    row.setAttribute("data-member", memberName);

    const startTime = new Date(taskPeriod.start);
    const endTime = new Date(taskPeriod.end);
    const duration = taskPeriod.duration_hours || 0;

    // Calculate timeline position (9 AM to 6 PM = 9 hours)
    const timelineData = this.calculateTimelinePosition(startTime, endTime);

    const statusClass = this.getStatusClass(taskPeriod.status);
    const statusColor = this.getStatusColor(taskPeriod.status);

    row.innerHTML = `
          <div class="task-info">
              <div class="task-name" title="${taskPeriod.task_name}">
                  ${this.truncateText(taskPeriod.task_name, 40)}
              </div>
              <div class="task-meta">
                  <span class="project-name">${taskPeriod.project_name || "Unknown Project"}</span>
                  <span>•</span>
                  <span>${taskPeriod.list_name || "Unknown List"}</span>
                  <span class="task-status ${statusClass}">${taskPeriod.status || "active"}</span>
              </div>
          </div>
          <div class="timeline-bar">
              <div class="time-ruler">
                  <span>9:00</span>
                  <span>12:00</span>
                  <span>15:00</span>
                  <span>18:00</span>
              </div>
              <div class="time-block active" 
                   style="left: ${timelineData.leftPercent}%; width: ${
      timelineData.widthPercent
    }%; background: ${statusColor};"
                   title="${taskPeriod.task_name} (${duration.toFixed(1)}h) - ${this.formatTime(
      startTime
    )} to ${this.formatTime(endTime)}"
                   onclick="window.charts.showTaskDetails('${
                     taskPeriod.task_id
                   }', '${memberName}')">
                  ${duration.toFixed(1)}h
              </div>
          </div>
      `;

    // Add hover effects
    row.addEventListener("mouseenter", () => {
      row.style.backgroundColor = "rgba(99, 102, 241, 0.1)";
    });

    row.addEventListener("mouseleave", () => {
      row.style.backgroundColor = "transparent";
    });

    return row;
  },

  // calculateTimelinePosition(startTime, endTime) {
  //   const workdayStart = 9; // 9 AM
  //   const workdayEnd = 17; // 5 PM
  //   const workdayHours = workdayEnd - workdayStart;

  //   const startHour = startTime.getHours() + startTime.getMinutes() / 60;
  //   const endHour = endTime.getHours() + endTime.getMinutes() / 60;

  //   // Clamp to workday hours
  //   const clampedStart = Math.max(workdayStart, Math.min(workdayEnd, startHour));
  //   const clampedEnd = Math.max(workdayStart, Math.min(workdayEnd, endHour));

  //   const leftPercent = ((clampedStart - workdayStart) / workdayHours) * 100;
  //   const widthPercent = ((clampedEnd - clampedStart) / workdayHours) * 100;

  //   return {
  //     leftPercent: Math.max(0, leftPercent),
  //     widthPercent: Math.max(5, widthPercent), // Minimum 5% width for visibility
  //   };
  // },

  // v2
  // calculateTimelinePosition(startTime, endTime) {
  //   const workdayStart = 9.5; // 9:30 AM
  //   const workdayEnd = 17; // 5:00 PM
  //   const breakStart = 12; // 12:00 PM
  //   const breakEnd = 12.5; // 12:30 PM

  //   const totalWorkHours = breakStart - workdayStart + (workdayEnd - breakEnd); // 7 hours

  //   const getEffectiveHour = (hour) => {
  //     if (hour < workdayStart) return 0;
  //     if (hour >= workdayStart && hour < breakStart) {
  //       return hour - workdayStart;
  //     }
  //     if (hour >= breakEnd && hour <= workdayEnd) {
  //       return breakStart - workdayStart + (hour - breakEnd);
  //     }
  //     if (hour >= breakStart && hour < breakEnd) {
  //       return breakStart - workdayStart; // during lunch
  //     }
  //     return totalWorkHours; // after work
  //   };

  //   const startHour = startTime.getHours() + startTime.getMinutes() / 60;
  //   const endHour = endTime.getHours() + endTime.getMinutes() / 60;

  //   const clampedStart = Math.max(workdayStart, Math.min(workdayEnd, startHour));
  //   const clampedEnd = Math.max(workdayStart, Math.min(workdayEnd, endHour));

  //   const effectiveStart = getEffectiveHour(clampedStart);
  //   const effectiveEnd = getEffectiveHour(clampedEnd);

  //   const leftPercent = (effectiveStart / totalWorkHours) * 100;
  //   const widthPercent = Math.max(5, ((effectiveEnd - effectiveStart) / totalWorkHours) * 100);

  //   return {
  //     leftPercent,
  //     widthPercent,
  //   };
  // },

  calculateTimelinePositionForZoom(startTime, endTime, zoomRange) {
    let rangeStart,
      rangeEnd,
      breakStart = 12,
      breakEnd = 12.5;

    switch (zoomRange) {
      case "morning":
        rangeStart = 9.5;
        rangeEnd = 12;
        break;
      case "afternoon":
        rangeStart = 12.5;
        rangeEnd = 17;
        break;
      default: // full day
        rangeStart = 9.5;
        rangeEnd = 17;
    }

    let startHour = startTime.getHours() + startTime.getMinutes() / 60;
    let endHour = endTime.getHours() + endTime.getMinutes() / 60;

    // Clamp start and end to workday range
    const clampedStart = Math.max(rangeStart, Math.min(rangeEnd, startHour));
    const clampedEnd = Math.max(rangeStart, Math.min(rangeEnd, endHour));

    // Adjust effective hours to skip lunch (only for full day view)
    const calculateEffective = (hour) => {
      if (zoomRange !== "day") return hour;
      if (hour <= breakStart) return hour;
      if (hour >= breakEnd) return hour - 0.5;
      return breakStart;
    };

    const effectiveStart = calculateEffective(clampedStart);
    const effectiveEnd = calculateEffective(clampedEnd);

    const rangeDuration = zoomRange === "day" ? 7 : rangeEnd - rangeStart;
    const leftPercent = ((effectiveStart - rangeStart) / rangeDuration) * 100;
    const widthPercent = Math.max(8, ((effectiveEnd - effectiveStart) / rangeDuration) * 100);

    return {
      leftPercent: Math.max(0, leftPercent),
      widthPercent,
    };
  },

  getStatusClass(status) {
    const statusLower = (status || "").toLowerCase();
    if (statusLower.includes("progress")) return "status-progress";
    if (statusLower.includes("staging")) return "status-staging";
    if (statusLower.includes("review")) return "status-review";
    return "status-progress";
  },

  getStatusColor(status) {
    const statusLower = (status || "").toLowerCase();
    if (statusLower.includes("progress")) return "linear-gradient(135deg, #10b981, #059669)";
    if (statusLower.includes("staging")) return "linear-gradient(135deg, #3b82f6, #1d4ed8)";
    if (statusLower.includes("review")) return "linear-gradient(135deg, #f59e0b, #d97706)";
    return "linear-gradient(135deg, #10b981, #059669)";
  },

  groupTasksByProject(tasks) {
    const grouped = {};
    tasks.forEach((task) => {
      const project = task.project_name || "Unknown Project";
      if (!grouped[project]) grouped[project] = [];
      grouped[project].push(task);
    });
    return grouped;
  },

  getUniqueProjects(memberData) {
    if (!memberData.task_details) return 0;
    const projects = new Set(memberData.task_details.map((task) => task.project_name || "Unknown"));
    return projects.size;
  },

  truncateText(text, maxLength) {
    if (!text) return "Unknown Task";
    return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
  },

  formatTime(date) {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  },

  getTodayDateTime(timeString) {
    const today = new Date().toISOString().split("T")[0];
    return `${today}T${timeString}:00`;
  },

  // Task details modal/popup
  showTaskDetails(taskId, memberName) {
    console.log(`Show details for task ${taskId} by ${memberName}`);
    // Could implement a modal here showing task details

    // For now, show a simple alert with task info
    const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
    if (taskElement) {
      const taskName = taskElement.querySelector(".task-name").textContent;
      const projectName = taskElement.querySelector(".project-name").textContent;

      alert(`Task: ${taskName}\nProject: ${projectName}\nAssigned to: ${memberName}`);
    }
  },

  // // Timeline zoom functionality
  // zoomTimeline(range) {
  //   this.currentZoom = range;

  //   // Update timeline display based on zoom level
  //   const timeRulers = document.querySelectorAll(".time-ruler");

  //   timeRulers.forEach((ruler) => {
  //     switch (range) {
  //       case "morning":
  //         ruler.innerHTML = `
  //                     <span>9:00</span>
  //                     <span>10:00</span>
  //                     <span>11:00</span>
  //                     <span>12:00</span>
  //                 `;
  //         break;
  //       case "afternoon":
  //         ruler.innerHTML = `
  //                     <span>13:00</span>
  //                     <span>14:30</span>
  //                     <span>16:00</span>
  //                     <span>17:30</span>
  //                 `;
  //         break;
  //       default: // day
  //         ruler.innerHTML = `
  //                     <span>9:00</span>
  //                     <span>12:00</span>
  //                     <span>15:00</span>
  //                     <span>18:00</span>
  //                 `;
  //     }
  //   });

  //   // Recalculate timeline positions for new zoom
  //   this.recalculateTimelinePositions(range);

  //   // Update button states
  //   document.querySelectorAll(".timeline-btn").forEach((btn) => {
  //     btn.classList.remove("active");
  //   });

  //   const activeBtn = document.querySelector(`[onclick*="${range}"]`);
  //   if (activeBtn) {
  //     activeBtn.classList.add("active");
  //   }
  // },

  // recalculateTimelinePositions(range) {
  //   const timeBlocks = document.querySelectorAll(".time-block");

  //   timeBlocks.forEach((block) => {
  //     const taskRow = block.closest(".task-row");
  //     if (!taskRow) return;

  //     // Get original time data from title or data attributes
  //     const title = block.getAttribute("title");
  //     const timeMatch = title.match(/(\d{2}:\d{2}) to (\d{2}:\d{2})/);

  //     if (timeMatch) {
  //       const [, startTimeStr, endTimeStr] = timeMatch;
  //       const today = new Date().toISOString().split("T")[0];
  //       const startTime = new Date(`${today}T${startTimeStr}:00`);
  //       const endTime = new Date(`${today}T${endTimeStr}:00`);

  //       const newPosition = this.calculateTimelinePositionForZoom(startTime, endTime, range);

  //       block.style.left = `${newPosition.leftPercent}%`;
  //       block.style.width = `${newPosition.widthPercent}%`;
  //     }
  //   });
  // },

  // calculateTimelinePositionForZoom(startTime, endTime, zoomRange) {
  //   let rangeStart, rangeEnd;

  //   switch (zoomRange) {
  //     case "morning":
  //       rangeStart = 9;
  //       rangeEnd = 12;
  //       break;
  //     case "afternoon":
  //       rangeStart = 13;
  //       rangeEnd = 17.5;
  //       break;
  //     default: // day
  //       rangeStart = 9;
  //       rangeEnd = 18;
  //   }

  //   const rangeHours = rangeEnd - rangeStart;
  //   const startHour = startTime.getHours() + startTime.getMinutes() / 60;
  //   const endHour = endTime.getHours() + endTime.getMinutes() / 60;

  //   // Clamp to zoom range
  //   const clampedStart = Math.max(rangeStart, Math.min(rangeEnd, startHour));
  //   const clampedEnd = Math.max(rangeStart, Math.min(rangeEnd, endHour));

  //   const leftPercent = ((clampedStart - rangeStart) / rangeHours) * 100;
  //   const widthPercent = ((clampedEnd - clampedStart) / rangeHours) * 100;

  //   return {
  //     leftPercent: Math.max(0, leftPercent),
  //     widthPercent: Math.max(8, widthPercent), // Minimum width for zoom
  //   };
  // },

  zoomTimeline(range) {
    this.currentZoom = range;

    const timeRulers = document.querySelectorAll(".time-ruler");

    timeRulers.forEach((ruler) => {
      switch (range) {
        case "morning":
          ruler.innerHTML = `
            <span>9:30</span>
            <span>10:30</span>
            <span>11:30</span>
          `;
          break;
        case "afternoon":
          ruler.innerHTML = `
            <span>12:30</span>
            <span>14:00</span>
            <span>15:30</span>
            <span>17:00</span>
          `;
          break;
        default: // full day
          ruler.innerHTML = `
            <span>9:30</span>
            <span>11:00</span>
            <span>13:30</span>
            <span>15:30</span>
            <span>17:00</span>
          `;
      }
    });

    this.recalculateTimelinePositions(range);

    document.querySelectorAll(".timeline-btn").forEach((btn) => {
      btn.classList.remove("active");
    });

    const activeBtn = document.querySelector(`[onclick*="${range}"]`);
    if (activeBtn) {
      activeBtn.classList.add("active");
    }
  },

  recalculateTimelinePositions(range) {
    const timeBlocks = document.querySelectorAll(".time-block");

    timeBlocks.forEach((block) => {
      const taskRow = block.closest(".task-row");
      if (!taskRow) return;

      const title = block.getAttribute("title");
      const timeMatch = title.match(/(\d{2}:\d{2}) to (\d{2}:\d{2})/);

      if (timeMatch) {
        const [, startTimeStr, endTimeStr] = timeMatch;
        const today = new Date().toISOString().split("T")[0];
        const startTime = new Date(`${today}T${startTimeStr}:00`);
        const endTime = new Date(`${today}T${endTimeStr}:00`);

        const newPosition = this.calculateTimelinePositionForZoom(startTime, endTime, range);
        block.style.left = `${newPosition.leftPercent}%`;
        block.style.width = `${newPosition.widthPercent}%`;
      }
    });
  },
  // Standard chart creation methods
  createActivityChart(metrics) {
    const ctx = document.getElementById("activityChart");
    if (!ctx) return;

    if (this.instances.activity) {
      this.instances.activity.destroy();
    }

    const activeHours = metrics.total_active_hours || 0;
    const expectedPerMember = 7.5; // 7.5 hours per member
    const totalMembers = metrics.members_analyzed || 2;
    const expectedTotal = expectedPerMember * totalMembers;
    const remainingHours = Math.max(0, expectedTotal - activeHours);

    this.instances.activity = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Active Hours", "Remaining Expected"],
        datasets: [
          {
            data: [activeHours, remainingHours],
            backgroundColor: ["#10b981", "#6b7280"],
            borderWidth: 2,
            borderColor: "#1e293b",
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
              color: "#cbd5e1",
              padding: 20,
              usePointStyle: true,
            },
          },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                const value = context.parsed || 0;
                const total = activeHours + remainingHours;
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return `${context.label}: ${value.toFixed(1)}h (${percentage}%)`;
              },
            },
          },
        },
        cutout: "60%",
      },
    });
  },

  createStatusChart(detailedData) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (this.instances.status) {
      this.instances.status.destroy();
    }

    const members = Object.keys(detailedData || {});
    if (members.length === 0) {
      ctx.parentElement.innerHTML = '<div class="no-activity">No status data available</div>';
      return;
    }

    let highlyActive = 0,
      active = 0,
      limited = 0,
      inactive = 0;

    members.forEach((member) => {
      const data = detailedData[member];
      const activeHours = data.total_active_hours || 0;
      const activeTasks = data.active_tasks || 0;

      if (activeTasks === 0) {
        inactive++;
      } else if (activeHours >= 6) {
        highlyActive++;
      } else if (activeHours >= 3) {
        active++;
      } else {
        limited++;
      }
    });

    this.instances.status = new Chart(ctx, {
      type: "pie",
      data: {
        labels: ["Highly Active (6h+)", "Active (3-6h)", "Limited Activity (<3h)", "Inactive"],
        datasets: [
          {
            data: [highlyActive, active, limited, inactive],
            backgroundColor: ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"],
            borderWidth: 2,
            borderColor: "#1e293b",
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
              color: "#cbd5e1",
              padding: 15,
              usePointStyle: true,
            },
          },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const value = context.raw;
                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                return `${context.label}: ${value} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  },

  createTaskChart(detailedData) {
    const ctx = document.getElementById("taskChart");
    if (!ctx) return;

    if (this.instances.task) {
      this.instances.task.destroy();
    }

    const members = Object.entries(detailedData).map(([name, data]) => ({
      name: name.length > 8 ? name.substring(0, 8) + "..." : name,
      activeTasks: data.active_tasks || 0,
      totalTasks: data.total_tasks || 0,
      inProgressTasks: data.in_progress_periods ? data.in_progress_periods.length : 0,
    }));

    if (members.length === 0) {
      ctx.parentElement.innerHTML = '<div class="no-activity">No task data available</div>';
      return;
    }

    members.sort((a, b) => b.totalTasks - a.totalTasks);

    this.instances.task = new Chart(ctx, {
      type: "bar",
      data: {
        labels: members.map((m) => m.name),
        datasets: [
          {
            label: "In Progress Tasks",
            data: members.map((m) => m.inProgressTasks),
            backgroundColor: "#10b981",
            borderRadius: 4,
          },
          {
            label: "Other Active Tasks",
            data: members.map((m) => Math.max(0, m.activeTasks - m.inProgressTasks)),
            backgroundColor: "#3b82f6",
            borderRadius: 4,
          },
          {
            label: "Total Tasks",
            data: members.map((m) => m.totalTasks),
            backgroundColor: "#6b7280",
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { color: "#cbd5e1" },
          },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#cbd5e1",
            borderColor: "#334155",
            borderWidth: 1,
          },
        },
        scales: {
          x: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "rgba(255, 255, 255, 0.06)" },
          },
          y: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "rgba(255, 255, 255, 0.06)" },
            beginAtZero: true,
            stepSize: 1,
          },
        },
        interaction: {
          intersect: false,
          mode: "index",
        },
      },
    });
  },

  // Update all charts with new data
  updateAll(data) {
    console.log("Updating all charts with data:", data);

    if (data.detailed_data) {
      this.createTaskTimeline(data.detailed_data);
      this.createStatusChart(data.detailed_data);
      this.createTaskChart(data.detailed_data);
    }

    if (data.team_metrics) {
      this.createActivityChart(data.team_metrics);
    }

    // Update timeline date
    this.updateTimelineDate(data.date);
  },

  updateTimelineDate(date) {
    const element = document.getElementById("timelineDate");
    if (element && date) {
      const dateObj = new Date(date);
      element.textContent = dateObj.toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    }
  },

  // Utility methods
  resize() {
    Object.values(this.instances).forEach((chart) => {
      if (chart && typeof chart.resize === "function") {
        chart.resize();
      }
    });
  },

  destroy() {
    Object.values(this.instances).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") {
        chart.destroy();
      }
    });
    this.instances = {};
  },

  // Task filtering and search
  filterTasksByProject(projectName) {
    const taskRows = document.querySelectorAll(".task-row");

    taskRows.forEach((row) => {
      const projectElement = row.querySelector(".project-name");
      if (projectElement) {
        const taskProject = projectElement.textContent.trim();
        if (projectName === "all" || taskProject === projectName) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      }
    });
  },

  searchTasks(searchTerm) {
    const taskRows = document.querySelectorAll(".task-row");
    const term = searchTerm.toLowerCase();

    taskRows.forEach((row) => {
      const taskName = row.querySelector(".task-name").textContent.toLowerCase();
      const projectName = row.querySelector(".project-name").textContent.toLowerCase();

      if (taskName.includes(term) || projectName.includes(term)) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  },

  // Export timeline data
  exportTimelineData() {
    const timelineData = [];
    const taskRows = document.querySelectorAll(".task-row");

    taskRows.forEach((row) => {
      const member = row.getAttribute("data-member");
      const taskId = row.getAttribute("data-task-id");
      const taskName = row.querySelector(".task-name").textContent;
      const projectName = row.querySelector(".project-name").textContent;
      const timeBlock = row.querySelector(".time-block");
      const duration = timeBlock ? timeBlock.textContent : "0h";

      timelineData.push({
        member,
        taskId,
        taskName,
        projectName,
        duration,
      });
    });

    return timelineData;
  },
};
