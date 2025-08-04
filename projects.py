import requests
from datetime import datetime
import json
from typing import List, Dict, Optional
from flask import Flask
import time


app = Flask(__name__)



# Configuration - replace with your actual values
API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'


RATE_LIMIT_DELAY = 0.5  # Delay between requests in seconds
MAX_RETRIES = 3  # Max retries for failed requests

def make_request(url: str) -> Optional[Dict]:
    """Make API request with rate limiting and retries"""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 10))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            time.sleep(RATE_LIMIT_DELAY)  # Add delay between requests
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url} (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return None

def get_team_id() -> str:
    """Get the primary team ID"""
    data = make_request(f"{BASE_URL}/team")
    return data['teams'][0]['id'] if data else None

def get_all_spaces(team_id: str) -> List[Dict]:
    """Get all spaces for a team"""
    data = make_request(f"{BASE_URL}/team/{team_id}/space?archived=false")
    return data.get('spaces', []) if data else []

def get_folders_in_space(space_id: str) -> List[Dict]:
    """Get all folders in a space"""
    data = make_request(f"{BASE_URL}/space/{space_id}/folder?archived=false")
    return data.get('folders', []) if data else []

def get_lists_in_folder(folder_id: str) -> List[Dict]:
    """Get all lists in a folder"""
    data = make_request(f"{BASE_URL}/folder/{folder_id}/list?archived=false")
    return data.get('lists', []) if data else []

def get_lists_in_space(space_id: str) -> List[Dict]:
    """Get lists directly in a space"""
    data = make_request(f"{BASE_URL}/space/{space_id}/list?archived=false")
    return data.get('lists', []) if data else []

def get_tasks_in_list(list_id: str) -> List[Dict]:
    """Get tasks in a list with basic info (no detailed task calls)"""
    data = make_request(f"{BASE_URL}/list/{list_id}/task?archived=false&include_closed=true&subtasks=true")
    if not data:
        return []
    
    tasks = data.get('tasks', [])
    
    # Simplified task data to reduce API calls
    simplified_tasks = []
    for task in tasks:
        simplified_tasks.append({
            'id': task['id'],
            'name': task['name'],
            'status': task.get('status', {}).get('status'),
            'assignees': [{
                'id': a.get('id'),
                'username': a.get('username'),
                'email': a.get('email')
            } for a in task.get('assignees', [])],
            'due_date': task.get('due_date'),
            'start_date': task.get('start_date'),
            'priority': task.get('priority')
        })
    
    return simplified_tasks

def get_projects_hierarchy() -> Dict:
    """Get complete ClickUp hierarchy with rate limiting"""
    print("Fetching team information...")
    team_id = get_team_id()
    if not team_id:
        print("Failed to get team ID")
        return {}
    
    print("Fetching spaces...")
    spaces = get_all_spaces(team_id)
    
    result = {}
    
    for space in spaces:
        space_id = space['id']
        print(f"\nProcessing space: {space['name']} (ID: {space_id})")
        
        space_data = {
            "name": space['name'],
            "folders": [],
            "lists": []
        }
        
        # Get folders in this space
        folders = get_folders_in_space(space_id)
        for folder in folders:
            folder_id = folder['id']
            print(f"  Processing folder: {folder['name']} (ID: {folder_id})")
            
            folder_data = {
                "id": folder_id,
                "name": folder['name'],
                "lists": []
            }
            
            # Get lists in this folder
            lists = get_lists_in_folder(folder_id)
            for lst in lists:
                list_id = lst['id']
                print(f"    Processing list: {lst['name']} (ID: {list_id})")
                
                list_data = {
                    "id": list_id,
                    "name": lst['name'],
                    "status": lst.get('status', 'active'),
                    "tasks": []
                }
                
                # Get tasks in this list
                tasks = get_tasks_in_list(list_id)
                list_data["tasks"] = tasks
                
                folder_data["lists"].append(list_data)
            
            space_data["folders"].append(folder_data)
        
        # Get lists directly in space
        lists_in_space = get_lists_in_space(space_id)
        for lst in lists_in_space:
            list_id = lst['id']
            print(f"  Processing direct list: {lst['name']} (ID: {list_id})")
            
            list_data = {
                "id": list_id,
                "name": lst['name'],
                "status": lst.get('status', 'active'),
                "tasks": []
            }
            
            # Get tasks in this list
            tasks = get_tasks_in_list(list_id)
            list_data["tasks"] = tasks
            
            space_data["lists"].append(list_data)
        
        result[space_id] = space_data
    
    return result

def save_to_json(data: Dict, filename: str = None) -> str:
    """Save data to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clickup_hierarchy_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

def main():
    """Main function with error handling"""
    try:
        print("Starting ClickUp export with rate limiting...")
        start_time = time.time()
        
        hierarchy_data = get_projects_hierarchy()
        
        if hierarchy_data:
            output_file = save_to_json(hierarchy_data)
            print(f"\nData saved to: {output_file}")
            
            # Calculate statistics
            total_spaces = len(hierarchy_data)
            total_folders = sum(len(space['folders']) for space in hierarchy_data.values())
            total_lists = sum(len(space['folders']) + len(space['lists']) for space in hierarchy_data.values())
            total_tasks = sum(
                sum(len(lst['tasks']) for folder in space['folders'] for lst in folder['lists']) +
                sum(len(lst['tasks']) for lst in space['lists'])
                for space in hierarchy_data.values()
            )
            
            print("\n=== SUMMARY ===")
            print(f"Spaces: {total_spaces}")
            print(f"Folders: {total_folders}")
            print(f"Lists: {total_lists}")
            print(f"Tasks: {total_tasks}")
            print(f"Time taken: {time.time() - start_time:.2f} seconds")
        else:
            print("Failed to retrieve data")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")



if __name__ == "__main__":
    main()
    app.run(debug=True, host='0.0.0.0', port=5015, use_reloader=False)