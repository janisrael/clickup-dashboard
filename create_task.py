import requests
from datetime import datetime, timedelta
import math

# ------------------ Configuration ------------------ #
CLICKUP_API_KEY = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
SPACE_ID = '90132462540'  # Folderless space
TASKS = ['Initial design', 'Design review', 'Development', 'Testing', 'Deployment']

# Only the specific staff to consider
STAFF = [
    {"id": "staff_member_1", "name": "Arif", "load_balance": 5},
    {"id": "staff_member_2", "name": "Wiktor", "load_balance": 3},
    {"id": "staff_member_3", "name": "Jan", "load_balance": 7},
]

# ------------------ Headers ------------------ #
headers = {
    'Authorization': CLICKUP_API_KEY,
    'Content-Type': 'application/json'
}

# ------------------ Helpers ------------------ #
def add_weekdays(start_date, num_days):
    current_date = start_date
    while num_days > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday to Friday
            num_days -= 1
    return current_date

def format_currency(value):
    return "${:,.2f}".format(value)

# ------------------ API Functions ------------------ #
def create_clickup_project(project_name, space_id, end_date):
    url = f'https://api.clickup.com/api/v2/space/{space_id}/list'
    data = {
        "name": project_name,
        "due_date": int(end_date.timestamp() * 1000)
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] Failed to create project: {response.status_code}")
        print(response.text)
        return None

def create_tasks_in_project(list_id, tasks, staff_member, end_date):
    url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
    task_responses = []

    for task_name in tasks:
        task_data = {
            "name": task_name,
            "due_date": int(end_date.timestamp() * 1000),
            "assignees": [staff_member["id"]]
        }

        response = requests.post(url, headers=headers, json=task_data)
        if response.status_code == 200:
            print(f"[✓] Task '{task_name}' assigned to {staff_member['name']}")
            task_responses.append(response.json())
        else:
            print(f"[ERROR] Failed to create task '{task_name}': {response.status_code}")
            print(response.text)

        staff_member['load_balance'] += 1

    return task_responses

# ------------------ Automation Entrypoint ------------------ #
def start_project_automation(staff_list, start_date_str, original_budget, margin_profit, labor_per_hour, client_name):
    print("🚀 Starting project automation...")

    # Parse start date
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

    # Budget & Profit calculations
    profit = original_budget * margin_profit
    budget_after_profit_margin = original_budget - profit
    labor_cost_per_day = labor_per_hour * 8
    labor_days = math.ceil(budget_after_profit_margin / labor_cost_per_day)
    project_end_date = add_weekdays(start_date, labor_days)

    # Prepare project name
    project_name = f'Web Design - {labor_days} days - {client_name}'

    # Filter and sort staff
    staff_filtered = [staff for staff in staff_list if staff["name"] in ["Arif", "Wiktor", "Jan"]]
    staff_sorted = sorted(staff_filtered, key=lambda x: x['load_balance'])

    # Create project
    project = create_clickup_project(project_name, SPACE_ID, project_end_date)

    if project and 'id' in project:
        list_id = project['id']
        create_tasks_in_project(list_id, TASKS, staff_sorted[0], project_end_date)  # Assign all tasks to least loaded staff
        return {
            "status": "success",
            "message": "Project and tasks created successfully!",
            "assigned_staff": staff_sorted[0],
            "project": project_name,
            "estimated_duration": f"{labor_days} days",
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": project_end_date.strftime('%Y-%m-%d'),
            "original_budget": format_currency(original_budget),
            "adjusted_budget_exclude_profit": format_currency(budget_after_profit_margin),
            "margin": f"{margin_profit:.0%}",  # e.g. "30%"
            "profit": format_currency(profit),
            "labor_cost_per_day": format_currency(labor_cost_per_day),
            "excluded_weekends": True,
            "tasks": TASKS
        }
    else:
        return {
            "status": "error",
            "message": "Project creation failed.",
            "raw_response": project
        }
