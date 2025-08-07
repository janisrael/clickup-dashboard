// Enhanced Project Tracker Module
const projectTracker = {
  currentView: "grid",
  timelineChart: null,
  projects: [],

  // Initialize the project tracker
  init() {
    this.loadProjects();
    this.initializeEventListeners();
    this.createTimelineChart();
    this.updateAlertCards();
  },

  // Load projects data
  async loadProjects() {
    try {
      // In real implementation, this would fetch from your API
      // For now, using sample data that matches your ClickUp structure
      const response = await fetch("/api/dashboard-data");
      const data = await response.json();

      // Extract project data from ClickUp data
      this.projects = this.extractProjectsFromData(data);
      this.renderProjects();
      this.updateAlertCards();
      this.updateTimelineChart();
    } catch (error) {
      console.error("Error loading projects:", error);
      this.projects = this.generateSampleProjects();
      this.renderProjects();
      this.updateAlertCards();
      this.updateTimelineChart();
    }
  },

  // Extract projects from ClickUp data
  extractProjectsFromData(data) {
    const projects = [];
    const detailedData = data.detailed_data || {};
    const projectMap = new Map();

    // Extract unique projects from task data
    Object.values(detailedData).forEach((memberData) => {
      if (memberData.task_details) {
        memberData.task_details.forEach((task) => {
          const projectName = task.project_name || "Unknown Project";
          if (!projectMap.has(projectName)) {
            projectMap.set(projectName, {
              id: projectName.toLowerCase().replace(/\s+/g, "-"),
              name: projectName,
              client: "Internal",
              status: "active",
              startDate: this.getProjectStartDate(task),
              deadline: this.getProjectDeadline(task),
              assignees: [],
              tasks: [],
              progress: 0,
            });
          }

          const project = projectMap.get(projectName);
          project.tasks.push({
            id: task.id,
            name: task.name,
            status: task.status,
            assignee: memberData.username,
            startDate: task.start_date,
            dueDate: task.due_date,
            completed: task.status === "completed",
          });

          if (!project.assignees.includes(memberData.username)) {
            project.assignees.push(memberData.username);
          }
        });
      }
    });

    // Calculate progress for each project
    projectMap.forEach((project) => {
      const completedTasks = project.tasks.filter((task) => task.completed).length;
      project.progress =
        project.tasks.length > 0 ? (completedTasks / project.tasks.length) * 100 : 0;
    });

    return Array.from(projectMap.values());
  },

  // Generate sample projects for demonstration
  generateSampleProjects() {
    const today = new Date();
    const oneWeekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const oneMonthLater = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
    const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

    return [
      {
        id: "web-development",
        name: "Web Development",
        client: "TechCorp",
        status: "active",
        startDate: oneWeekAgo.toISOString().split("T")[0],
        deadline: tomorrow.toISOString().split("T")[0], // Due tomorrow
        assignees: ["Arif", "John"],
        progress: 75,
        tasks: [
          {
            id: "task-1",
            name: "Create responsive content sizes",
            status: "in progress",
            assignee: "Arif",
            dueDate: tomorrow.toISOString().split("T")[0],
            completed: false,
          },
          {
            id: "task-2",
            name: "Setup frontend framework",
            status: "completed",
            assignee: "John",
            completed: true,
          },
        ],
      },
      {
        id: "ui-ux-design",
        name: "UI/UX Design",
        client: "StartupXYZ",
        status: "active",
        startDate: oneWeekAgo.toISOString().split("T")[0],
        deadline: today.toISOString().split("T")[0], // Due today
        assignees: ["Arif"],
        progress: 60,
        tasks: [
          {
            id: "task-3",
            name: "Design And Implementation",
            status: "in progress",
            assignee: "Arif",
            dueDate: today.toISOString().split("T")[0],
            completed: false,
          },
        ],
      },
      {
        id: "cms-setup",
        name: "CMS Setup",
        client: "Enterprise Ltd",
        status: "active",
        startDate: today.toISOString().split("T")[0],
        deadline: oneMonthLater.toISOString().split("T")[0],
        assignees: ["Arif"],
        progress: 25,
        tasks: [
          {
            id: "task-4",
            name: "Content Integration",
            status: "in progress",
            assignee: "Arif",
            dueDate: nextWeek.toISOString().split("T")[0],
            completed: false,
          },
        ],
      },
      {
        id: "legacy-maintenance",
        name: "Legacy System Maintenance",
        client: "OldTech Inc",
        status: "active",
        startDate: oneWeekAgo.toISOString().split("T")[0],
        deadline: null, // No deadline
        assignees: ["Team"],
        progress: 40,
        tasks: [],
      },
    ];
  },

  // Helper functions for date extraction
  getProjectStartDate(task) {
    // Extract start date from task or use current date
    return task.start_date || new Date().toISOString().split("T")[0];
  },

  getProjectDeadline(task) {
    // Extract deadline from task if available
    return task.due_date || null;
  },

  // Render projects in the container
  renderProjects() {
    const container = document.getElementById("projectsContainer");
    if (!container) return;

    container.innerHTML = "";
    container.className = `projects-container ${this.currentView}-view`;

    this.projects.forEach((project) => {
      const projectCard = this.createProjectCard(project);
      container.appendChild(projectCard);
    });
  },

  // Create individual project card
  createProjectCard(project) {
    const card = document.createElement("div");
    card.className = `project-card ${this.getDeadlineClass(project.deadline)}`;
    card.onclick = () => this.showProjectDetails(project);

    const deadlineText = project.deadline
      ? `Deadline: ${this.formatDate(project.deadline)}`
      : "No deadline set";

    card.innerHTML = `
            <div class="project-header">
                <div class="project-title">
                    ${project.name}
                    <span class="project-status status-${project.status}">${project.status}</span>
                </div>
                <div class="project-meta">
                    <span><i class="fas fa-user"></i> ${project.client}</span>
                    <span><i class="fas fa-users"></i> ${project.assignees.length}</span>
                    <span><i class="fas fa-tasks"></i> ${project.tasks.length}</span>
                </div>
            </div>
            <div class="project-body">
                <div class="project-timeline">
                    <div class="timeline-bar">
                        <div class="timeline-progress" style="width: ${project.progress}%"></div>
                    </div>
                    <div class="timeline-dates">
                        <span>Started: ${this.formatDate(project.startDate)}</span>
                        <span>${deadlineText}</span>
                    </div>
                </div>
                <div class="project-stats">
                    <div class="stat-item">
                        <span class="stat-value">${Math.round(project.progress)}%</span>
                        <span class="stat-label">Complete</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${
                          project.tasks.filter((t) => t.completed).length
                        }</span>
                        <span class="stat-label">Done</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${
                          project.tasks.filter((t) => !t.completed).length
                        }</span>
                        <span class="stat-label">Pending</span>
                    </div>
                </div>
                <div class="project-accordion">
                    <div class="accordion-header" onclick="event.stopPropagation(); projectTracker.toggleAccordion(event)">
                        <span class="accordion-title">Tasks (${project.tasks.length})</span>
                        <i class="fas fa-chevron-down accordion-icon"></i>
                    </div>
                    <div class="accordion-content">
                        <div class="accordion-body">
                            <div class="task-list">
                                ${this.renderTaskList(project.tasks)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

    return card;
  },

  // Render task list for accordion
  renderTaskList(tasks) {
    if (tasks.length === 0) {
      return '<p class="text-secondary">No tasks assigned yet</p>';
    }

    return tasks
      .map(
        (task) => `
            <div class="task-item">
                <div class="task-checkbox ${task.completed ? "completed" : ""}" 
                     onclick="event.stopPropagation(); projectTracker.toggleTask('${
                       task.id
                     }')"></div>
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        <span class="task-assignee">${task.assignee}</span>
                        ${
                          task.dueDate
                            ? `<span class="task-due ${
                                this.isOverdue(task.dueDate) ? "overdue" : ""
                              }">
                            ${this.formatDate(task.dueDate)}
                        </span>`
                            : ""
                        }
                        <span class="project-status status-${task.status}">${task.status}</span>
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  },

  // Get deadline-based CSS class
  getDeadlineClass(deadline) {
    if (!deadline) return "no-deadline";

    const today = new Date();
    const deadlineDate = new Date(deadline);
    const diffTime = deadlineDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return "deadline-critical"; // Overdue
    if (diffDays <= 1) return "deadline-critical"; // Due today/tomorrow
    if (diffDays <= 7) return "deadline-warning"; // Due this week
    if (diffDays <= 30) return "deadline-upcoming"; // Due this month
    return "no-deadline";
  },

  // Check if date is overdue
  isOverdue(date) {
    const today = new Date();
    const checkDate = new Date(date);
    return checkDate < today;
  },

  // Format date for display
  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  },

  // Update alert cards with current data
  updateAlertCards() {
    const today = new Date().toISOString().split("T")[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T")[0];
    const nextWeek = new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0];

    let overdueTasks = [];
    let dueTasks = [];
    let upcomingTasks = [];

    this.projects.forEach((project) => {
      project.tasks.forEach((task) => {
        if (task.dueDate && !task.completed) {
          if (task.dueDate < today) {
            overdueTasks.push({ ...task, projectName: project.name });
          } else if (task.dueDate === today) {
            dueTasks.push({ ...task, projectName: project.name });
          } else if (task.dueDate <= nextWeek) {
            upcomingTasks.push({ ...task, projectName: project.name });
          }
        }
      });
    });

    // Update overdue card
    this.updateAlertCard(
      "overdue",
      overdueTasks.length,
      overdueTasks.map((task) => `${task.name} (${task.projectName})`)
    );

    // Update due today card
    this.updateAlertCard(
      "due",
      dueTasks.length,
      dueTasks.map((task) => `${task.name} (${task.projectName})`)
    );

    // Update upcoming card
    this.updateAlertCard(
      "upcoming",
      upcomingTasks.length,
      upcomingTasks.map(
        (task) => `${task.name} - ${this.formatDate(task.dueDate)} (${task.projectName})`
      )
    );
  },

  // Update individual alert card
  updateAlertCard(type, count, items) {
    const countElement = document.getElementById(`${type}Count`);
    const detailsElement = document.getElementById(`${type}Details`);

    if (countElement) countElement.textContent = count;
    if (detailsElement) {
      if (count === 0) {
        detailsElement.innerHTML = `<p>No ${type} tasks</p>`;
      } else {
        detailsElement.innerHTML =
          items
            .slice(0, 3)
            .map((item) => `<p>• ${item}</p>`)
            .join("") + (items.length > 3 ? `<p>... and ${items.length - 3} more</p>` : "");
      }
    }
  },

  // Create timeline chart
  createTimelineChart() {
    const ctx = document.getElementById("projectTimelineChart");
    if (!ctx) return;

    // Destroy existing chart
    if (this.timelineChart) {
      this.timelineChart.destroy();
    }

    // Prepare timeline data
    const timelineData = this.prepareTimelineData();

    this.timelineChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: timelineData.labels,
        datasets: timelineData.datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: {
          title: {
            display: true,
            text: "Project Timeline",
            color: "#f1f5f9",
          },
          legend: {
            display: true,
            labels: {
              color: "#f1f5f9",
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: "week",
            },
            ticks: {
              color: "#94a3b8",
            },
            grid: {
              color: "#334155",
            },
          },
          y: {
            ticks: {
              color: "#94a3b8",
            },
            grid: {
              color: "#334155",
            },
          },
        },
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const dataIndex = elements[0].index;
            const project = this.projects[dataIndex];
            if (project) {
              this.showProjectDetails(project);
            }
          }
        },
      },
    });
  },

  // Prepare data for timeline chart
  prepareTimelineData() {
    const labels = this.projects.map((project) => project.name);
    const startDates = this.projects.map((project) => new Date(project.startDate));
    const endDates = this.projects.map((project) =>
      project.deadline ? new Date(project.deadline) : new Date(Date.now() + 30 * 86400000)
    );

    return {
      labels: labels,
      datasets: [
        {
          label: "Project Duration",
          data: this.projects.map((project, index) => ({
            x: [startDates[index], endDates[index]],
            y: project.name,
          })),
          backgroundColor: this.projects.map((project) => {
            switch (this.getDeadlineClass(project.deadline)) {
              case "deadline-critical":
                return "#ef4444";
              case "deadline-warning":
                return "#f59e0b";
              case "deadline-upcoming":
                return "#3b82f6";
              default:
                return "#6366f1";
            }
          }),
          borderColor: "#1e293b",
          borderWidth: 1,
        },
      ],
    };
  },

  // Update timeline chart
  updateTimelineChart() {
    if (this.timelineChart) {
      const timelineData = this.prepareTimelineData();
      this.timelineChart.data = timelineData;
      this.timelineChart.update();
    }
  },

  // Timeline zoom functionality
  zoomTimeline(range) {
    // Update active button
    document.querySelectorAll(".timeline-controls .chart-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    event.target.classList.add("active");

    // Update chart time scale
    if (this.timelineChart) {
      let unit = "day";
      switch (range) {
        case "1w":
          unit = "day";
          break;
        case "1m":
          unit = "week";
          break;
        case "3m":
          unit = "week";
          break;
        case "6m":
          unit = "month";
          break;
      }

      this.timelineChart.options.scales.x.time.unit = unit;
      this.timelineChart.update();
    }
  },

  // Toggle accordion
  toggleAccordion(event) {
    const header = event.currentTarget;
    const content = header.nextElementSibling;
    const icon = header.querySelector(".accordion-icon");

    header.classList.toggle("active");
    content.classList.toggle("active");

    if (content.classList.contains("active")) {
      content.style.maxHeight = content.scrollHeight + "px";
    } else {
      content.style.maxHeight = "0";
    }
  },

  // Toggle task completion
  toggleTask(taskId) {
    this.projects.forEach((project) => {
      const task = project.tasks.find((t) => t.id === taskId);
      if (task) {
        task.completed = !task.completed;
        task.status = task.completed ? "completed" : "in progress";

        // Recalculate project progress
        const completedTasks = project.tasks.filter((t) => t.completed).length;
        project.progress =
          project.tasks.length > 0 ? (completedTasks / project.tasks.length) * 100 : 0;
      }
    });

    this.renderProjects();
    this.updateAlertCards();
    this.updateTimelineChart();
  },

  // Toggle view between grid and list
  toggleView(view) {
    this.currentView = view;
    this.renderProjects();

    // Update active button
    document.querySelectorAll(".project-actions .chart-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    event.target.classList.add("active");
  },

  // Show project details modal
  showProjectDetails(project) {
    const modal = document.getElementById("projectDetailsModal");
    const title = document.getElementById("modalProjectTitle");
    const body = document.getElementById("modalProjectBody");

    if (!modal || !title || !body) return;

    title.textContent = project.name;
    body.innerHTML = `
            <div class="project-details">
                <div class="detail-section">
                    <h3>Project Information</h3>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>Client:</label>
                            <span>${project.client}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="project-status status-${project.status}">${
      project.status
    }</span>
                        </div>
                        <div class="detail-item">
                            <label>Start Date:</label>
                            <span>${this.formatDate(project.startDate)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Deadline:</label>
                            <span>${
                              project.deadline ? this.formatDate(project.deadline) : "Not set"
                            }</span>
                        </div>
                        <div class="detail-item">
                            <label>Progress:</label>
                            <span>${Math.round(project.progress)}%</span>
                        </div>
                        <div class="detail-item">
                            <label>Assignees:</label>
                            <span>${project.assignees.join(", ")}</span>
                        </div>
                    </div>
                </div>
                <div class="detail-section">
                    <h3>Tasks (${project.tasks.length})</h3>
                    <div class="task-list">
                        ${this.renderTaskList(project.tasks)}
                    </div>
                </div>
            </div>
        `;

    modal.classList.add("active");
  },

  // Close modal
  closeModal() {
    const modal = document.getElementById("projectDetailsModal");
    if (modal) {
      modal.classList.remove("active");
    }
  },

  // Show add project modal
  showAddProjectModal() {
    // Implement add project functionality
    console.log("Add project modal - to be implemented");
  },

  // Initialize event listeners
  initializeEventListeners() {
    // Close modal when clicking outside
    document.addEventListener("click", (e) => {
      const modal = document.getElementById("projectDetailsModal");
      if (modal && e.target === modal) {
        this.closeModal();
      }
    });

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.closeModal();
      }
    });
  },
};

// Auto-initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("projectsTab")) {
    projectTracker.init();
  }
});

// Export for global access
window.projectTracker = projectTracker;
