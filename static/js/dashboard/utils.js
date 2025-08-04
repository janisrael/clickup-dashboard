function showLoading() {
  document.getElementById("loadingScreen").style.display = "block";
  document.getElementById("errorMessage").style.display = "none";
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.style.display = "none";
  });
}

function hideLoading() {
  document.getElementById("loadingScreen").style.display = "none";
}

function showError(message = "Failed to load dashboard data") {
  document.getElementById("errorText").textContent = message;
  document.getElementById("errorMessage").style.display = "flex";
}

function updateKPIs(data) {
  try {
    if (!data) {
      console.error("No data provided to updateKPIs");
      return;
    }

    // Calculate fixed active hours by summing absolute values
    let fixedActiveHours = 0;
    if (data.detailed_data) {
      Object.values(data.detailed_data).forEach((memberData) => {
        fixedActiveHours += (memberData.in_progress_periods || []).reduce(
          (sum, period) => sum + Math.abs(period.duration_hours || 0),
          0
        );
      });
    }

    document.getElementById("totalMembers").textContent = data.members_analyzed || 0;
    document.getElementById("activeHours").textContent = `${fixedActiveHours.toFixed(1)}h`;
    document.getElementById("downtimeHours").textContent = `${
      data.team_metrics?.total_downtime_hours?.toFixed(1) || 0
    }h`;
    document.getElementById("oldTasks").textContent = data.team_metrics?.total_old_tasks || 0;
    document.getElementById("efficiency").textContent = `${
      data.team_metrics?.team_efficiency?.toFixed(1) || 0
    }%`;
    document.getElementById("expectedHours").textContent = `of ${
      data.team_metrics?.expected_working_hours || 0
    }h expected`;
  } catch (error) {
    console.error("Error updating KPIs:", error);
  }
}

function updateDateInfo(data) {
  try {
    const dateInfo = document.getElementById("dateInfo");
    if (data.date && data.day_of_week) {
      const isWeekend = data.is_weekend ? " (Weekend)" : "";
      dateInfo.querySelector("span").textContent = `${data.day_of_week}, ${data.date}${isWeekend}`;
    }

    const lastUpdated = document.getElementById("lastUpdated");
    if (data.timestamp) {
      const updateTime = new Date(data.timestamp);
      lastUpdated.textContent = `Last updated: ${updateTime.toLocaleTimeString()}`;
    }
  } catch (error) {
    console.error("Error updating date info:", error);
  }
}

function renderDataStatus(context, isLoading = false) {
  const statusElement = document.getElementById("data-status");
  if (!statusElement) return;

  // Default fallback message

  if (isLoading) {
    statusElement.innerHTML = `
            <span style="color: var(--gray)">●</span> 
            <span class="loading-dots">Loading status</span>
        `;
    return;
  }

  let statusHTML = '<span style="color: var(--gray)">●</span> Data status not available';

  if (context && context.data_status) {
    if (context.data_status === "LIVE") {
      statusHTML = `<span style="color: var(--success)">●</span> Live data`;
    } else if (context.next_expected_update) {
      statusHTML = `
                <span style="color: var(--warning)">●</span> 
                Outside working hours | Next update: ${context.next_expected_update}
            `;
    }
  }

  statusElement.innerHTML = statusHTML;
}

function updateAlerts(data) {
  try {
    const alertsContainer = document.getElementById("alertsContainer");
    alertsContainer.innerHTML = "";

    if (!data || !data.team_metrics) {
      alertsContainer.innerHTML = `
                <div class="alert-item alert-info">
                    <i class="fas fa-info-circle"></i>
                    <span>No alert data available</span>
                </div>
            `;
      return;
    }

    const alerts = [];

    // 1. Check for currently inactive members
    if (data.team_metrics.currently_inactive?.length > 0) {
      alerts.push({
        type: "critical",
        message: `🚨 ${
          data.team_metrics.currently_inactive.length
        } member(s) currently inactive: ${data.team_metrics.currently_inactive.join(", ")}`,
      });
    }

    // 2. Check for high downtime
    if (data.team_metrics.total_downtime_hours >= 4) {
      alerts.push({
        type: "warning",
        message: `⚠️ High total downtime: ${data.team_metrics.total_downtime_hours.toFixed(
          1
        )} hours detected`,
      });
    }

    // 3. Check for old tasks
    if (data.team_metrics.total_old_tasks > 0) {
      alerts.push({
        type: "warning",
        message: `⚠️ ${data.team_metrics.total_old_tasks} old tasks (7+ days) detected`,
      });
    }

    // 4. Check for low efficiency
    if (data.team_metrics.team_efficiency < 50) {
      alerts.push({
        type: "warning",
        message: `📉 Low team efficiency: ${data.team_metrics.team_efficiency.toFixed(1)}%`,
      });
    }

    // 5. Check for weekend work
    if (data.is_weekend && data.team_metrics.total_active_hours > 0) {
      alerts.push({
        type: "info",
        message: `ℹ️ Weekend activity detected: ${data.team_metrics.total_active_hours.toFixed(
          1
        )} hours`,
      });
    }

    if (alerts.length === 0) {
      alertsContainer.innerHTML = `
                <div class="alert-item alert-success">
                    <i class="fas fa-check-circle"></i>
                    <span>✅ All Clear: No critical issues detected</span>
                </div>
            `;
      return;
    }

    // Sort alerts by priority (critical first)
    alerts.sort((a, b) => {
      const priority = { critical: 1, warning: 2, info: 3 };
      return priority[a.type] - priority[b.type];
    });

    alerts.forEach((alert) => {
      const alertElement = document.createElement("div");
      alertElement.className = `alert-item alert-${alert.type}`;

      const iconClass =
        {
          critical: "fas fa-exclamation-circle",
          warning: "fas fa-exclamation-triangle",
          success: "fas fa-check-circle",
          info: "fas fa-info-circle",
        }[alert.type] || "fas fa-info-circle";

      alertElement.innerHTML = `
                <i class="${iconClass}"></i>
                <span>${alert.message}</span>
            `;

      alertsContainer.appendChild(alertElement);
    });
  } catch (error) {
    console.error("Error updating alerts:", error);
  }
}

function updateMemberStatus(data) {
  try {
    const memberStatusGrid = document.getElementById("memberStatusGrid");
    memberStatusGrid.innerHTML = "";

    if (!data || !data.detailed_data) {
      memberStatusGrid.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-user-slash"></i>
                    <p>No team member data available</p>
                </div>
            `;
      return;
    }

    const members = Object.keys(data.detailed_data);

    if (members.length === 0) {
      memberStatusGrid.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-user-slash"></i>
                    <p>No team members found</p>
                </div>
            `;
      return;
    }

    members.forEach((member) => {
      const memberData = data.detailed_data[member];
      const totalActive = (memberData.in_progress_periods || []).reduce(
        (sum, period) => sum + (period.duration_hours || 0),
        0
      );
      const totalDowntime = (memberData.downtime_periods || []).reduce(
        (sum, period) => sum + (period.duration_hours || 0),
        0
      );
      const taskMetrics = memberData.task_metrics || {};

      let status = "good";
      let statusText = "Good";
      let statusIcon = "fas fa-check-circle";

      if (totalDowntime >= 4) {
        status = "critical";
        statusText = "Critical";
        statusIcon = "fas fa-exclamation-circle";
      } else if (totalDowntime >= 3) {
        status = "warning";
        statusText = "Warning";
        statusIcon = "fas fa-exclamation-triangle";
      }

      const isCurrentlyInactive = (data.team_metrics?.currently_inactive || []).includes(member);
      const hasOldTasks =
        (taskMetrics.tasks_by_age?.very_old || 0) + (taskMetrics.tasks_by_age?.old || 0) > 0;
      const hasMilestones = taskMetrics.milestone_tasks > 0;

      const memberCard = document.createElement("div");
      memberCard.className = `member-card status-${status}`;

      memberCard.innerHTML = `
                <div class="member-header">
                    <div class="member-name">
                        <i class="${statusIcon}"></i>
                        ${member}
                    </div>
                    <div class="member-status status-${status}">${statusText}</div>
                </div>
                
                <div class="member-stats">
                    <div class="stat-item">
                        <div class="stat-label">Active</div>
                        <div class="stat-number">${totalActive.toFixed(1)}h</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Downtime</div>
                        <div class="stat-number">${totalDowntime.toFixed(1)}h</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Tasks</div>
                        <div class="stat-number">${taskMetrics.total_tasks || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Old Tasks</div>
                        <div class="stat-number">${
                          (taskMetrics.tasks_by_age?.very_old || 0) +
                          (taskMetrics.tasks_by_age?.old || 0)
                        }</div>
                    </div>
                </div>
                
                ${
                  isCurrentlyInactive
                    ? `<div style="margin-top: 12px; color: ${window.dashboard.colors.danger}; font-size: 0.8rem;">
                        <i class="fas fa-exclamation-circle"></i> Currently Inactive
                    </div>`
                    : ""
                }
                
                ${
                  hasOldTasks
                    ? `<div style="margin-top: 8px; color: ${window.dashboard.colors.warning}; font-size: 0.8rem;">
                        <i class="fas fa-hourglass-half"></i> Has old tasks
                    </div>`
                    : ""
                }
                
                ${
                  hasMilestones
                    ? `<div style="margin-top: 8px; color: ${window.dashboard.colors.milestone}; font-size: 0.8rem;">
                        <i class="fas fa-flag-checkered"></i> Has milestone tasks
                    </div>`
                    : ""
                }
            `;

      memberStatusGrid.appendChild(memberCard);
    });
  } catch (error) {
    console.error("Error updating member status:", error);
  }
}

function togglePassword(element) {
  element.classList.toggle("show");
}

function showAddProjectModal() {
  alert("Add Project functionality would be implemented here");
}

function showAddWebsiteModal() {
  alert("Add Website functionality would be implemented here");
}
