import requests
import json
from datetime import datetime
import pytz

# Your ClickUp Configuration
API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'
TIMEZONE = pytz.timezone('America/Edmonton')

def debug_clickup_access():
    """Debug ClickUp API access step by step"""
    print("🔍 DEBUGGING CLICKUP API ACCESS")
    print("=" * 50)
    
    # Step 1: Test API token
    print("\n1. Testing API Token...")
    try:
        response = requests.get(f"{BASE_URL}/team", headers=HEADERS)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            teams = response.json().get('teams', [])
            if teams:
                team_id = teams[0]['id']
                print(f"   ✅ Team ID: {team_id}")
                print(f"   ✅ Team Name: {teams[0]['name']}")
            else:
                print("   ❌ No teams found")
                return None
        else:
            print(f"   ❌ API Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None
    
    # Step 2: Get team members
    print("\n2. Getting Team Members...")
    try:
        members = teams[0].get('members', [])
        print(f"   Found {len(members)} members:")
        target_users = {}
        for member in members:
            user = member.get('user', {})
            username = user.get('username', 'Unknown')
            user_id = user.get('id')
            print(f"   - {username} (ID: {user_id})")
            if username in ['Jan', 'Arif']:
                target_users[username] = user_id
        
        if not target_users:
            print("   ❌ Target users (Jan, Arif) not found in team!")
            return None
        print(f"   ✅ Target users found: {target_users}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None
    
    # Step 3: Get spaces
    print("\n3. Getting Spaces...")
    try:
        response = requests.get(f"{BASE_URL}/team/{team_id}/space?archived=false", headers=HEADERS)
        if response.status_code == 200:
            spaces = response.json().get('spaces', [])
            print(f"   Found {len(spaces)} spaces:")
            for space in spaces:
                print(f"   - {space['name']} (ID: {space['id']})")
        else:
            print(f"   ❌ Error getting spaces: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None
    
    # Step 4: Get all lists from all spaces
    print("\n4. Getting All Task Lists...")
    all_lists = []
    try:
        for space in spaces:
            space_id = space['id']
            space_name = space['name']
            print(f"\n   Processing space: {space_name}")
            
            # Get lists directly in space
            response = requests.get(f"{BASE_URL}/space/{space_id}/list?archived=false", headers=HEADERS)
            if response.status_code == 200:
                lists = response.json().get('lists', [])
                for lst in lists:
                    all_lists.append(lst)
                    print(f"     - List: {lst['name']} (ID: {lst['id']})")
            
            # Get folders and their lists
            response = requests.get(f"{BASE_URL}/space/{space_id}/folder?archived=false", headers=HEADERS)
            if response.status_code == 200:
                folders = response.json().get('folders', [])
                for folder in folders:
                    print(f"     - Folder: {folder['name']}")
                    folder_response = requests.get(f"{BASE_URL}/folder/{folder['id']}/list?archived=false", headers=HEADERS)
                    if folder_response.status_code == 200:
                        folder_lists = folder_response.json().get('lists', [])
                        for lst in folder_lists:
                            all_lists.append(lst)
                            print(f"       - List: {lst['name']} (ID: {lst['id']})")
        
        print(f"\n   ✅ Total lists found: {len(all_lists)}")
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None
    
    # Step 5: Search for tasks in each list for target users
    print("\n5. Searching for Tasks...")
    total_tasks_found = 0
    
    for username, user_id in target_users.items():
        print(f"\n   Searching tasks for {username} (ID: {user_id}):")
        user_tasks = []
        
        for lst in all_lists:
            try:
                list_id = lst['id']
                list_name = lst['name']
                
                # Get tasks from this list
                response = requests.get(f"{BASE_URL}/list/{list_id}/task?archived=false&include_closed=true&subtasks=true", headers=HEADERS)
                if response.status_code == 200:
                    tasks = response.json().get('tasks', [])
                    
                    # Filter tasks assigned to this user
                    user_list_tasks = []
                    for task in tasks:
                        assignees = task.get('assignees', [])
                        if any(str(assignee.get('id')) == str(user_id) for assignee in assignees):
                            user_list_tasks.append(task)
                    
                    if user_list_tasks:
                        print(f"     - {list_name}: {len(user_list_tasks)} tasks")
                        for task in user_list_tasks:
                            status = task.get('status', {}).get('status', 'No Status')
                            print(f"       * {task['name'][:50]}... (Status: {status})")
                            user_tasks.append(task)
                
            except Exception as e:
                print(f"     ❌ Error checking list {list_name}: {e}")
                continue
        
        print(f"   📊 Total tasks for {username}: {len(user_tasks)}")
        total_tasks_found += len(user_tasks)
        
        # Check for in-progress tasks
        in_progress_tasks = []
        for task in user_tasks:
            status = task.get('status', {}).get('status', '').lower()
            if any(keyword in status for keyword in ['progress', 'active', 'working', 'doing', 'development']):
                in_progress_tasks.append(task)
        
        if in_progress_tasks:
            print(f"   🟢 In-progress tasks for {username}: {len(in_progress_tasks)}")
            for task in in_progress_tasks:
                print(f"     - {task['name'][:40]}... ({task.get('status', {}).get('status')})")
        else:
            print(f"   🔴 No in-progress tasks found for {username}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total tasks found across all users: {total_tasks_found}")
    print(f"   Total lists searched: {len(all_lists)}")
    
    if total_tasks_found == 0:
        print("\n⚠️  NO TASKS FOUND - POSSIBLE ISSUES:")
        print("   1. Users might not be assigned to any tasks")
        print("   2. All tasks might be in folders/spaces not accessible by API token")
        print("   3. Tasks might be archived or in closed status")
        print("   4. API token might not have permission to see tasks")
        print("   5. Tasks might be assigned to different user IDs")
        
        print(f"\n🔧 MANUAL VERIFICATION STEPS:")
        print(f"   1. Go to ClickUp web interface")
        print(f"   2. Check if Jan and Arif have tasks assigned to them")
        print(f"   3. Note which Space/Folder/List their tasks are in")
        print(f"   4. Check if your API token has access to those spaces")
        print(f"   5. Verify the usernames are exactly 'Jan' and 'Arif' in ClickUp")
    
    return {
        'team_id': team_id,
        'target_users': target_users,
        'total_lists': len(all_lists),
        'total_tasks': total_tasks_found,
        'spaces': [s['name'] for s in spaces]
    }

if __name__ == "__main__":
    result = debug_clickup_access()
    
    if result:
        print(f"\n💾 Debug results saved for reference:")
        print(f"   Team ID: {result['team_id']}")
        print(f"   Target Users: {result['target_users']}")
        print(f"   Spaces Available: {', '.join(result['spaces'])}")
        print(f"   Total Lists: {result['total_lists']}")
        print(f"   Total Tasks: {result['total_tasks']}")