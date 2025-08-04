import requests
import time


CLICKUP_API_KEY = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
TEAM_ID = '9013605091'
SPACE_ID = '90132462540' 

# Fetch users in the team
def fetch_users_in_team():
    url = 'https://api.clickup.com/api/v2/team'
    headers = {'Authorization': CLICKUP_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        teams = response.json().get('teams', [])
        if teams:
            return teams[0].get('members', [])  # get users from first team
        else:
            print("No teams found.")
            return []
    else:
        print(f"Error fetching users: {response.status_code}")
        return []

# Get all list IDs from the Space (no folders)
def get_all_list_ids_from_space(space_id):
    headers = {'Authorization': CLICKUP_API_KEY}
    list_ids = []

    # Get lists directly from the space
    lists_url = f'https://api.clickup.com/api/v2/space/{space_id}/list'
    lists = requests.get(lists_url, headers=headers).json().get('lists', [])
    
    for lst in lists:
        list_ids.append(lst['id'])

    return list_ids

# Fetch tasks for a specific user from the lists
# Example update in fetch_user_tasks_from_lists
def fetch_user_tasks_from_lists(user_id, list_ids):
    headers = {'Authorization': CLICKUP_API_KEY}
    user_tasks = []

    # Define statuses to exclude
    excluded_statuses = ['complete', 'closed', 'archived','cancelled', 'done', 'resolved']

    for list_id in list_ids:
        print(f"Fetching tasks from list: {list_id} for user: {user_id}")
        url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
        params = {
            'archived': 'false',  # Only fetch non-archived tasks
            'subtasks': 'true'
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                for task in tasks:
                    # Check if task is assigned to the user and not in excluded statuses
                    assignee_ids = [a['id'] for a in task.get('assignees', [])]
                    task_status = task.get('status', {}).get('status', '').lower()  # Get the task status

                    # If task is assigned to the user and not in excluded status
                    if user_id in assignee_ids and task_status not in excluded_statuses:
                        user_tasks.append(task)
            else:
                print(f"Failed to fetch tasks from list {list_id}: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"Timeout fetching list {list_id}")
        except Exception as e:
            print(f"Error fetching list {list_id}: {e}")

        time.sleep(0.2)  # Prevent rate limiting

    return user_tasks


# Calculate workload (number of tasks assigned to each user)
def calculate_workload(users, list_ids):
    workload = {}
    for user in users:
        user_data = user.get('user', user)
        user_id = user_data['id']
        username = user_data.get('username', f"user_{user_id}")

        tasks = fetch_user_tasks_from_lists(user_id, list_ids)
        workload[username] = len(tasks)
    return workload

# Get all tasks workload
def get_calculate_workload():
    users = fetch_users_in_team()
    list_ids = get_all_list_ids_from_space(SPACE_ID)
    staff_list = []

    for user in users:
        user_data = user.get('user', user)
        user_id = user_data['id']
        username = user_data.get('username', f"user_{user_id}")

        tasks = fetch_user_tasks_from_lists(user_id, list_ids)
        load_balance = len(tasks)

        staff_list.append({
            "id": user_id,
            "name": username,
            "load_balance": load_balance
        })

    return staff_list