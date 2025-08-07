# import requests
# import time
# from datetime import datetime, timedelta

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     print(f"Team {team_id} not found or has no members.")
#     return []

# def get_unix_timestamps_for_last_week():
#     today = datetime.utcnow()
#     start = today - timedelta(days=today.weekday() + 7) 
#     end = start + timedelta(days=7) 
#     return int(start.timestamp() * 1000), int(end.timestamp() * 1000)

# def get_tasks_for_member(team_id, member_id, start_ts, end_ts):
#     tasks = []
#     page = 0
#     while True:
#         url = (f"{BASE_URL}/team/{team_id}/task"
#                f"?assignees[]={member_id}&date_created_gt={start_ts}"
#                f"&date_created_lt={end_ts}&page={page}")
#         resp = requests.get(url, headers=HEADERS)
#         resp.raise_for_status()
#         data = resp.json()
#         tasks.extend(data['tasks'])
#         if not data.get('tasks') or len(data['tasks']) < 100:
#             break
#         page += 1
#     return tasks

# def main():
#     team_id = get_team_id()
#     print(f"Team ID: {team_id}")
#     members = get_team_members(team_id)
#     start_ts, end_ts = get_unix_timestamps_for_last_week()
#     print(f"Fetching tasks from {datetime.utcfromtimestamp(start_ts/1000)} to {datetime.utcfromtimestamp(end_ts/1000)}")

#     for member in members:
#         user_id = member['user']['id']
#         user_name = member['user']['username']
#         print(f"\nTasks for {user_name} (ID: {user_id}):")
#         tasks = get_tasks_for_member(team_id, user_id, start_ts, end_ts)
#         for task in tasks:
#             print(f"- {task['name']} (Task ID: {task['id']})")

# if __name__ == "__main__":
#     main()



# import requests
# import time
# from datetime import datetime, timedelta
# import pandas as pd
# import plotly.express as px

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     print(f"Team {team_id} not found or has no members.")
#     return []

# def get_unix_timestamps_for_last_week():
#     today = datetime.utcnow()
#     start = today - timedelta(days=today.weekday() + 7) 
#     end = start + timedelta(days=7) 
#     return int(start.timestamp() * 1000), int(end.timestamp() * 1000)

# def convert_timestamp(ts):
#     if ts is None:
#         return None
#     # ClickUp timestamps are in milliseconds
#     return datetime.utcfromtimestamp(int(ts) / 1000)

# def get_tasks_for_member(team_id, member_id, start_ts, end_ts):
#     tasks = []
#     page = 0
#     while True:
#         url = (f"{BASE_URL}/team/{team_id}/task"
#                f"?assignees[]={member_id}&date_created_gt={start_ts}"
#                f"&date_created_lt={end_ts}&page={page}")
#         resp = requests.get(url, headers=HEADERS)
#         resp.raise_for_status()
#         data = resp.json()
#         tasks.extend(data['tasks'])
#         if not data.get('tasks') or len(data['tasks']) < 100:
#             break
#         page += 1
#     return tasks

# def main():
#     team_id = get_team_id()
#     print(f"Team ID: {team_id}")
#     members = get_team_members(team_id)
#     start_ts, end_ts = get_unix_timestamps_for_last_week()
#     print(f"Fetching tasks from {datetime.utcfromtimestamp(start_ts/1000)} to {datetime.utcfromtimestamp(end_ts/1000)}")

#     gantt_data = []
#     for member in members:
#         user_id = member['user']['id']
#         user_name = member['user']['username']
#         print(f"\nTasks for {user_name} (ID: {user_id}):")
#         tasks = get_tasks_for_member(team_id, user_id, start_ts, end_ts)
#         for task in tasks:
#             # Prefer start_date and due_date if available, fallback to created/closed
#             start = convert_timestamp(task.get('start_date') or task.get('date_created'))
#             end = convert_timestamp(task.get('due_date') or task.get('date_closed'))
#             if not start or not end:
#                 continue  # skip tasks without both dates
#             gantt_data.append({
#                 'Task': task['name'],
#                 'Assignee': user_name,
#                 'Start': start,
#                 'End': end
#             })
#             print(f"- {task['name']} (Task ID: {task['id']}, Start: {start}, End: {end})")

#     # Create Gantt chart if there is data
#     if gantt_data:
#         df = pd.DataFrame(gantt_data)
#         fig = px.timeline(
#             df,
#             x_start="Start",
#             x_end="End",
#             y="Assignee",
#             color="Task",
#             title="ClickUp Tasks Gantt Chart (Last Week)"
#         )
#         fig.update_yaxes(autorange="reversed")  # Gantt charts have earliest at the top
#         fig.show()
#     else:
#         print("No tasks with valid start and end dates for the selected period.")

        

# if __name__ == "__main__":
#     main() 
# import requests
# import time
# from datetime import datetime, timedelta
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     return []

# def get_date_range(days_back=7):
#     """Get date range for analysis - defaults to last 7 days"""
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=days_back)
    
#     # Convert to ClickUp timestamps (milliseconds)
#     start_ts = int(start_date.timestamp() * 1000)
#     end_ts = int(end_date.timestamp() * 1000)
    
#     return start_ts, end_ts, start_date, end_date

# def get_tasks_for_member_with_retry(team_id, member_id, start_ts, end_ts, max_retries=3):
#     """Get tasks with rate limit handling"""
#     all_tasks = []
    
#     # Use simpler query to avoid rate limits
#     url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=true"
    
#     for attempt in range(max_retries):
#         try:
#             print(f"  Fetching tasks (attempt {attempt + 1})...")
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60  # Wait 1 minute
#                 print(f"  Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             tasks = data.get('tasks', [])
            
#             # Filter tasks by date range (do it client-side to avoid complex API queries)
#             filtered_tasks = []
#             for task in tasks:
#                 task_updated = task.get('date_updated')
#                 task_created = task.get('date_created')
                
#                 if task_updated and int(task_updated) >= start_ts and int(task_updated) <= end_ts:
#                     filtered_tasks.append(task)
#                 elif task_created and int(task_created) >= start_ts and int(task_created) <= end_ts:
#                     filtered_tasks.append(task)
            
#             return filtered_tasks
            
#         except requests.exceptions.RequestException as e:
#             print(f"  Error on attempt {attempt + 1}: {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)  # Wait 30 seconds before retry
            
#     print("  Failed to fetch tasks after all retries")
#     return []

# def is_task_in_progress(task):
#     """Check if a task is currently in progress status"""
#     status = task.get('status', {})
#     if not status:
#         return False
    
#     status_name = status.get('status', '').lower()
    
#     # Common "in progress" status variations
#     progress_keywords = [
#         'progress', 'in progress', 'in-progress', 'inprogress',
#         'active', 'working', 'doing', 'current', 'ongoing',
#         'started', 'development', 'dev', 'implementing'
#     ]
    
#     return any(keyword in status_name for keyword in progress_keywords)

# def get_task_activity(task_id, max_retries=2):
#     """Get task activity including status changes"""
#     for attempt in range(max_retries):
#         try:
#             resp = requests.get(f"{BASE_URL}/task/{task_id}/activity", headers=HEADERS)
            
#             if resp.status_code == 429:
#                 time.sleep(30)
#                 continue
            
#             if resp.status_code == 404:
#                 print(f"    Task {task_id} not found or no access to activity")
#                 return []
                
#             resp.raise_for_status()
#             return resp.json().get('activity', [])
            
#         except Exception as e:
#             if attempt < max_retries - 1:
#                 time.sleep(10)
#             else:
#                 print(f"    Failed to get activity for task {task_id}: {e}")
    
#     return []

# def parse_status_change_from_activity(activity_item):
#     """Parse status change information from activity item"""
#     try:
#         # Look for status change activities
#         activity_type = activity_item.get('type')
#         comment = activity_item.get('comment', '')
        
#         # Check if this is a status change activity
#         if 'status' in comment.lower() or activity_type == 'statusChange':
#             # Try to extract "from X to Y" pattern
#             if 'from' in comment.lower() and 'to' in comment.lower():
#                 parts = comment.lower().split('from')
#                 if len(parts) > 1:
#                     from_to_part = parts[1].strip()
#                     if 'to' in from_to_part:
#                         from_status, to_status = from_to_part.split('to', 1)
#                         from_status = from_status.strip()
#                         to_status = to_status.strip()
                        
#                         return {
#                             'from_status': from_status,
#                             'to_status': to_status,
#                             'timestamp': activity_item.get('date'),
#                             'user': activity_item.get('user', {}).get('username', 'Unknown')
#                         }
        
#         return None
#     except Exception as e:
#         return None

# def analyze_member_downtime(member_name, tasks, start_date, end_date):
#     """Analyze when a member had no in-progress tasks for 3+ hours"""
#     print(f"\n🔍 Analyzing {member_name}...")
#     print(f"   Tasks to analyze: {len(tasks)}")
    
#     # Find all periods when member had tasks in progress
#     in_progress_periods = []
    
#     # Check current status of tasks
#     current_in_progress = []
#     for task in tasks:
#         if is_task_in_progress(task):
#             current_in_progress.append(task)
#             print(f"   ✅ Currently In Progress: {task['name']}")
    
#     # Get detailed activity for recent tasks to find status changes
#     all_status_changes = []
    
#     for task in tasks[:10]:  # Check activity for first 10 tasks to avoid rate limits
#         print(f"   📋 Checking activity for: {task['name'][:40]}...")
#         activity = get_task_activity(task['id'])
        
#         print(f"      Found {len(activity)} activity items")
        
#         # Parse status changes from activity
#         for activity_item in activity:
#             status_change = parse_status_change_from_activity(activity_item)
#             if status_change:
#                 activity_time = datetime.fromtimestamp(int(status_change['timestamp']) / 1000)
                
#                 # Only consider changes in our date range
#                 if start_date <= activity_time <= end_date:
#                     status_change['datetime'] = activity_time
#                     status_change['task_name'] = task['name']
#                     status_change['task_id'] = task['id']
#                     all_status_changes.append(status_change)
                    
#                     print(f"      📅 {activity_time.strftime('%m/%d %H:%M')}: "
#                           f"'{status_change['from_status']}' → '{status_change['to_status']}'")
        
#         time.sleep(2)  # Rate limit prevention
    
#     # Sort status changes by time
#     all_status_changes.sort(key=lambda x: x['datetime'])
    
#     print(f"   📊 Total status changes found: {len(all_status_changes)}")
    
#     # Build timeline of in-progress periods from status changes
#     for change in all_status_changes:
#         to_status = change['to_status']
        
#         # Check if this change moved task TO in-progress
#         if any(keyword in to_status for keyword in ['progress', 'active', 'working', 'doing', 'development']):
#             # This task became in-progress
#             period_start = change['datetime']
            
#             # Find when it stopped being in-progress (look for next status change for this task)
#             period_end = end_date  # Default to end of analysis period
            
#             for later_change in all_status_changes:
#                 if (later_change['task_id'] == change['task_id'] and 
#                     later_change['datetime'] > change['datetime']):
                    
#                     later_to_status = later_change['to_status']
#                     # If it changed to something that's NOT in-progress
#                     if not any(keyword in later_to_status for keyword in ['progress', 'active', 'working', 'doing', 'development']):
#                         period_end = later_change['datetime']
#                         break
            
#             in_progress_periods.append({
#                 'start': period_start,
#                 'end': period_end,
#                 'task_name': change['task_name'],
#                 'task_id': change['task_id']
#             })
            
#             print(f"   ⏱️ In Progress Period: {period_start.strftime('%m/%d %H:%M')} - "
#                   f"{period_end.strftime('%m/%d %H:%M')} ({change['task_name'][:30]})")
    
#     # Add current in-progress tasks (assume they've been in progress since last update)
#     for task in current_in_progress:
#         task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
#         # Only add if we don't already have a recent period for this task
#         already_tracked = any(
#             period['task_id'] == task['id'] and 
#             abs((period['start'] - task_updated).total_seconds()) < 3600  # Within 1 hour
#             for period in in_progress_periods
#         )
        
#         if not already_tracked:
#             period_start = max(task_updated, start_date)
#             in_progress_periods.append({
#                 'start': period_start,
#                 'end': end_date,
#                 'task_name': task['name'],
#                 'task_id': task['id']
#             })
            
#             print(f"   ⏱️ Current In Progress: {period_start.strftime('%m/%d %H:%M')} - "
#                   f"now ({task['name'][:30]})")
    
#     # Sort periods by start time and merge overlapping ones
#     in_progress_periods.sort(key=lambda x: x['start'])
#     merged_periods = []
    
#     for period in in_progress_periods:
#         if not merged_periods:
#             merged_periods.append(period)
#         else:
#             last_period = merged_periods[-1]
#             # If periods overlap (with 1-hour buffer for gaps)
#             if period['start'] <= last_period['end'] + timedelta(hours=1):
#                 # Overlapping periods - merge them
#                 last_period['end'] = max(last_period['end'], period['end'])
#                 if period['task_name'] not in last_period['task_name']:
#                     last_period['task_name'] += f", {period['task_name']}"
#             else:
#                 merged_periods.append(period)
    
#     print(f"   📊 Final active periods: {len(merged_periods)}")
    
#     # Find downtime gaps of 3+ hours
#     downtime_periods = []
    
#     if len(merged_periods) == 0:
#         # No activity at all - entire period is downtime
#         total_hours = (end_date - start_date).total_seconds() / 3600
#         downtime_periods.append({
#             'start': start_date,
#             'end': end_date,
#             'duration_hours': total_hours,
#             'type': 'no_activity'
#         })
#         print(f"   🔴 No activity detected - full {total_hours:.1f}h downtime")
#     else:
#         # Check gap before first activity
#         first_start = merged_periods[0]['start']
#         gap_hours = (first_start - start_date).total_seconds() / 3600
#         if gap_hours >= 3:
#             downtime_periods.append({
#                 'start': start_date,
#                 'end': first_start,
#                 'duration_hours': gap_hours,
#                 'type': 'before_first_activity'
#             })
#             print(f"   🔴 Downtime before first activity: {gap_hours:.1f}h")
        
#         # Check gaps between activities
#         for i in range(len(merged_periods) - 1):
#             gap_start = merged_periods[i]['end']
#             gap_end = merged_periods[i + 1]['start']
#             gap_duration = (gap_end - gap_start).total_seconds() / 3600
            
#             if gap_duration >= 3:
#                 downtime_periods.append({
#                     'start': gap_start,
#                     'end': gap_end,
#                     'duration_hours': gap_duration,
#                     'type': 'between_activities'
#                 })
#                 print(f"   🔴 Downtime gap: {gap_start.strftime('%m/%d %H:%M')} - "
#                       f"{gap_end.strftime('%m/%d %H:%M')} ({gap_duration:.1f}h)")
        
#         # Check gap after last activity
#         last_end = merged_periods[-1]['end']
#         gap_hours = (end_date - last_end).total_seconds() / 3600
#         if gap_hours >= 3:
#             downtime_periods.append({
#                 'start': last_end,
#                 'end': end_date,
#                 'duration_hours': gap_hours,
#                 'type': 'after_last_activity'
#             })
#             print(f"   🔴 Downtime after last activity: {gap_hours:.1f}h")
    
#     return merged_periods, downtime_periods

# def add_watcher_to_task(task_id, user_id, user_name="Unknown"):
#     """Add a user as a watcher to a specific task"""
#     try:
#         url = f"{BASE_URL}/task/{task_id}/watcher/{user_id}"
#         resp = requests.post(url, headers=HEADERS)
        
#         if resp.status_code == 200:
#             print(f"      ✅ Added {user_name} as watcher to task {task_id}")
#             return True
#         elif resp.status_code == 400:
#             # User might already be a watcher
#             print(f"      ℹ️ {user_name} might already be watching task {task_id}")
#             return True
#         else:
#             print(f"      ❌ Failed to add {user_name} as watcher: {resp.status_code}")
#             return False
            
#     except Exception as e:
#         print(f"      ❌ Error adding {user_name} as watcher: {e}")
#         return False

# def find_user_by_name(members, name):
#     """Find a user by their username or display name"""
#     name_lower = name.lower()
#     for member in members:
#         user = member.get('user', {})
#         username = user.get('username', '').lower()
#         email = user.get('email', '').lower()
        
#         if (name_lower in username or 
#             name_lower in email or 
#             username == name_lower):
#             return user
#     return None

# def add_watcher_to_all_tasks(tasks, watcher_user_id, watcher_name, dry_run=False):
#     """Add a watcher to multiple tasks"""
#     print(f"\n👁️ {'[DRY RUN] ' if dry_run else ''}Adding {watcher_name} as watcher to {len(tasks)} tasks...")
    
#     success_count = 0
#     failed_count = 0
    
#     for i, task in enumerate(tasks, 1):
#         task_id = task['id']
#         task_name = task['name'][:50] + "..." if len(task['name']) > 50 else task['name']
        
#         print(f"   {i}/{len(tasks)}: {task_name}")
        
#         if dry_run:
#             print(f"      🔍 [DRY RUN] Would add {watcher_name} as watcher")
#             success_count += 1
#         else:
#             if add_watcher_to_task(task_id, watcher_user_id, watcher_name):
#                 success_count += 1
#             else:
#                 failed_count += 1
            
#             # Rate limiting
#             time.sleep(1)
    
#     print(f"\n📊 Watcher Addition Summary:")
#     print(f"   ✅ Successful: {success_count}")
#     if not dry_run:
#         print(f"   ❌ Failed: {failed_count}")
    
#     return success_count, failed_count
#     """Create a timeline chart showing activity and downtime"""
#     fig = go.Figure()
    
#     y_pos = 0
#     colors = px.colors.qualitative.Set3
    
#     for member_name, (activity_periods, downtime_periods) in member_data.items():
        
#         # Add activity periods (green)
#         for period in activity_periods:
#             fig.add_trace(go.Scatter(
#                 x=[period['start'], period['end'], period['end'], period['start'], period['start']],
#                 y=[y_pos, y_pos, y_pos + 0.8, y_pos + 0.8, y_pos],
#                 fill='toself',
#                 fillcolor='rgba(0, 255, 0, 0.6)',
#                 line=dict(color='green'),
#                 name=f"{member_name} - Active",
#                 hovertemplate=f"<b>{member_name}</b><br>Active: {period['task_name']}<br>%{{x}}<extra></extra>",
#                 showlegend=False
#             ))
        
#         # Add downtime periods (red)
#         for period in downtime_periods:
#             fig.add_trace(go.Scatter(
#                 x=[period['start'], period['end'], period['end'], period['start'], period['start']],
#                 y=[y_pos, y_pos, y_pos + 0.8, y_pos + 0.8, y_pos],
#                 fill='toself',
#                 fillcolor='rgba(255, 0, 0, 0.6)',
#                 line=dict(color='red'),
#                 name=f"{member_name} - Downtime",
#                 hovertemplate=f"<b>{member_name}</b><br>Downtime: {period['duration_hours']:.1f}h<br>%{{x}}<extra></extra>",
#                 showlegend=False
#             ))
        
#         y_pos += 1
    
#     # Update layout
#     fig.update_layout(
#         title=f"Team Activity Timeline ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
#         xaxis_title="Time",
#         yaxis_title="Team Members",
#         yaxis=dict(
#             tickmode='array',
#             tickvals=list(range(len(member_data))),
#             ticktext=list(member_data.keys())
#         ),
#         height=max(400, len(member_data) * 60),
#         showlegend=False
#     )
    
#     return fig

# def main():
#     print("🚀 ClickUp Member Downtime Analysis & Watcher Management")
#     print("="*60)
    
#     # Get team info first
#     team_id = get_team_id()
#     members = get_team_members(team_id)
#     print(f"🏢 Team ID: {team_id}")
#     print(f"👥 Team members: {len(members)}")
    
#     # Interactive menu
#     print("\n🔧 What would you like to do?")
#     print("1. Analyze member downtime only")
#     print("2. Add Sean as watcher to all recent tasks")
#     print("3. Add custom person as watcher to tasks")
#     print("4. Both downtime analysis and add watchers")
    
#     choice = input("\nEnter your choice (1-4): ").strip()
    
#     # Get date range for analysis/tasks
#     days_back = 7
#     if choice in ['2', '3', '4']:
#         try:
#             days_back = int(input(f"How many days back to look for tasks? (default: 7): ").strip() or "7")
#         except:
#             days_back = 7
    
#     start_ts, end_ts, start_date, end_date = get_date_range(days_back=days_back)
#     print(f"📅 Working with period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
    
#     # Handle watcher functionality
#     if choice in ['2', '3', '4']:
#         # Find the person to add as watcher
#         if choice == '2':
#             watcher_name = 'sean'
#         else:
#             watcher_name = input("Enter the name/username of person to add as watcher: ").strip()
        
#         watcher_user = find_user_by_name(members, watcher_name)
#         if not watcher_user:
#             print(f"❌ Could not find user '{watcher_name}' in the team")
#             print("Available users:")
#             for member in members:
#                 user = member.get('user', {})
#                 print(f"   - {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
#             return
        
#         watcher_user_id = watcher_user['id']
#         watcher_username = watcher_user['username']
#         print(f"👁️ Found watcher: {watcher_username} (ID: {watcher_user_id})")
        
#         # Ask for dry run
#         dry_run_input = input("Do a dry run first? (y/n, default: y): ").strip().lower()
#         dry_run = dry_run_input != 'n'
        
#         # Collect all tasks from all members
#         all_tasks = []
#         print(f"\n📋 Collecting tasks from all team members...")
        
#         for i, member in enumerate(members):
#             user_id = member['user']['id']
#             user_name = member['user']['username']
#             print(f"   Getting tasks for {user_name}...")
            
#             tasks = get_tasks_for_member_with_retry(team_id, user_id, start_ts, end_ts)
#             all_tasks.extend(tasks)
            
#             if i < len(members) - 1:
#                 time.sleep(2)  # Rate limiting
        
#         # Remove duplicates (same task might be assigned to multiple people)
#         unique_tasks = {}
#         for task in all_tasks:
#             unique_tasks[task['id']] = task
        
#         unique_task_list = list(unique_tasks.values())
#         print(f"📊 Found {len(unique_task_list)} unique tasks")
        
#         # Add watcher to tasks
#         if len(unique_task_list) > 0:
#             add_watcher_to_all_tasks(unique_task_list, watcher_user_id, watcher_username, dry_run)
            
#             if dry_run:
#                 confirm = input(f"\n🤔 Proceed with actually adding {watcher_username} to {len(unique_task_list)} tasks? (y/n): ").strip().lower()
#                 if confirm == 'y':
#                     add_watcher_to_all_tasks(unique_task_list, watcher_user_id, watcher_username, dry_run=False)
#         else:
#             print("❌ No tasks found to add watchers to")
    
#     # Handle downtime analysis
#     if choice in ['1', '4']:
#         print(f"\n📊 Starting downtime analysis...")
        
#         member_data = {}
        
#         # Get fresh task data if we haven't already
#         if choice != '4':
#             # Analyze each member for downtime
#             for i, member in enumerate(members):
#                 user_id = member['user']['id']
#                 user_name = member['user']['username']
                
#                 print(f"\n{'='*50}")
#                 print(f"MEMBER {i+1}/{len(members)}: {user_name}")
#                 print('='*50)
                
#                 # Get tasks for this member
#                 tasks = get_tasks_for_member_with_retry(team_id, user_id, start_ts, end_ts)
                
#                 if len(tasks) == 0:
#                     print(f"   ⚠️ No tasks found for {user_name}")
#                     # Full downtime
#                     total_hours = (end_date - start_date).total_seconds() / 3600
#                     member_data[user_name] = ([], [{
#                         'start': start_date,
#                         'end': end_date,
#                         'duration_hours': total_hours,
#                         'type': 'no_tasks'
#                     }])
#                 else:
#                     activity_periods, downtime_periods = analyze_member_downtime(
#                         user_name, tasks, start_date, end_date
#                     )
#                     member_data[user_name] = (activity_periods, downtime_periods)
                
#                 # Rate limiting - wait between members
#                 if i < len(members) - 1:
#                     print("   ⏱️ Waiting to avoid rate limits...")
#                     time.sleep(5)
        
#         if member_data:
#             # Print downtime summary
#             print("\n" + "="*60)
#             print("📊 DOWNTIME SUMMARY (3+ Hour Gaps)")
#             print("="*60)
            
#             total_members_with_downtime = 0
            
#             for member_name, (activity_periods, downtime_periods) in member_data.items():
#                 if downtime_periods:
#                     total_members_with_downtime += 1
#                     total_downtime = sum(p['duration_hours'] for p in downtime_periods)
                    
#                     print(f"\n🔴 {member_name}:")
#                     print(f"   Total downtime: {total_downtime:.1f} hours")
#                     print(f"   Number of gaps: {len(downtime_periods)}")
                    
#                     for i, period in enumerate(downtime_periods, 1):
#                         day_name = period['start'].strftime('%A')
#                         print(f"   Gap {i}: {day_name} {period['start'].strftime('%m/%d %H:%M')} - "
#                               f"{period['end'].strftime('%m/%d %H:%M')} ({period['duration_hours']:.1f}h)")
            
#             if total_members_with_downtime == 0:
#                 print("✅ No significant downtime periods detected!")
            
#             # Create visualization
#             print(f"\n📈 Creating timeline visualization...")
#             try:
#                 fig = create_timeline_chart(member_data, start_date, end_date)
#                 fig.show()
#                 print("✅ Visualization created successfully!")
#             except Exception as e:
#                 print(f"❌ Error creating visualization: {e}")
    
#     print(f"\n🎯 Analysis complete!")


# def create_timeline_chart(member_data, start_date, end_date):
#     """Create a timeline chart showing activity and downtime"""
#     fig = go.Figure()
    
#     y_pos = 0
#     colors = px.colors.qualitative.Set3
    
#     for member_name, (activity_periods, downtime_periods) in member_data.items():
        
#         # Add activity periods (green)
#         for period in activity_periods:
#             fig.add_trace(go.Scatter(
#                 x=[period['start'], period['end'], period['end'], period['start'], period['start']],
#                 y=[y_pos, y_pos, y_pos + 0.8, y_pos + 0.8, y_pos],
#                 fill='toself',
#                 fillcolor='rgba(0, 255, 0, 0.6)',
#                 line=dict(color='green'),
#                 name=f"{member_name} - Active",
#                 hovertemplate=f"<b>{member_name}</b><br>Active: {period['task_name']}<br>%{{x}}<extra></extra>",
#                 showlegend=False
#             ))
        
#         # Add downtime periods (red)
#         for period in downtime_periods:
#             fig.add_trace(go.Scatter(
#                 x=[period['start'], period['end'], period['end'], period['start'], period['start']],
#                 y=[y_pos, y_pos, y_pos + 0.8, y_pos + 0.8, y_pos],
#                 fill='toself',
#                 fillcolor='rgba(255, 0, 0, 0.6)',
#                 line=dict(color='red'),
#                 name=f"{member_name} - Downtime",
#                 hovertemplate=f"<b>{member_name}</b><br>Downtime: {period['duration_hours']:.1f}h<br>%{{x}}<extra></extra>",
#                 showlegend=False
#             ))
        
#         y_pos += 1
    
#     # Update layout
#     fig.update_layout(
#         title=f"Team Activity Timeline ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
#         xaxis_title="Time",
#         yaxis_title="Team Members",
#         yaxis=dict(
#             tickmode='array',
#             tickvals=list(range(len(member_data))),
#             ticktext=list(member_data.keys())
#         ),
#         height=max(400, len(member_data) * 60),
#         showlegend=False
#     )
    
#     return fig

# def main():
#     print("🚀 ClickUp Member Downtime Analysis")
#     print("="*50)
    
#     # Get date range (last 7 days by default)
#     start_ts, end_ts, start_date, end_date = get_date_range(days_back=7)
#     print(f"📅 Analysis period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
    
#     # Get team info
#     team_id = get_team_id()
#     members = get_team_members(team_id)
#     print(f"🏢 Team ID: {team_id}")
#     print(f"👥 Team members: {len(members)}")
    
#     member_data = {}
    
#     # Analyze each member
#     for i, member in enumerate(members):
#         user_id = member['user']['id']
#         user_name = member['user']['username']
        
#         print(f"\n{'='*50}")
#         print(f"MEMBER {i+1}/{len(members)}: {user_name}")
#         print('='*50)
        
#         # Get tasks for this member
#         tasks = get_tasks_for_member_with_retry(team_id, user_id, start_ts, end_ts)
        
#         if len(tasks) == 0:
#             print(f"   ⚠️ No tasks found for {user_name}")
#             # Full downtime
#             total_hours = (end_date - start_date).total_seconds() / 3600
#             member_data[user_name] = ([], [{
#                 'start': start_date,
#                 'end': end_date,
#                 'duration_hours': total_hours,
#                 'type': 'no_tasks'
#             }])
#         else:
#             activity_periods, downtime_periods = analyze_member_downtime(
#                 user_name, tasks, start_date, end_date
#             )
#             member_data[user_name] = (activity_periods, downtime_periods)
        
#         # Rate limiting - wait between members
#         if i < len(members) - 1:
#             print("   ⏱️ Waiting to avoid rate limits...")
#             time.sleep(5)
    
#     # Print summary
#     print("\n" + "="*60)
#     print("📊 DOWNTIME SUMMARY (3+ Hour Gaps)")
#     print("="*60)
    
#     total_members_with_downtime = 0
    
#     for member_name, (activity_periods, downtime_periods) in member_data.items():
#         if downtime_periods:
#             total_members_with_downtime += 1
#             total_downtime = sum(p['duration_hours'] for p in downtime_periods)
            
#             print(f"\n🔴 {member_name}:")
#             print(f"   Total downtime: {total_downtime:.1f} hours")
#             print(f"   Number of gaps: {len(downtime_periods)}")
            
#             for i, period in enumerate(downtime_periods, 1):
#                 day_name = period['start'].strftime('%A')  # Get day name (Monday, Tuesday, etc.)
#                 print(f"   Gap {i}: {day_name} {period['start'].strftime('%m/%d %H:%M')} - "
#                       f"{period['end'].strftime('%m/%d %H:%M')} ({period['duration_hours']:.1f}h)")
    
#     if total_members_with_downtime == 0:
#         print("✅ No significant downtime periods detected!")
    
#     # Create visualization
#     print(f"\n📈 Creating timeline visualization...")
#     try:
#         fig = create_timeline_chart(member_data, start_date, end_date)
#         fig.show()
#         print("✅ Visualization created successfully!")
#     except Exception as e:
#         print(f"❌ Error creating visualization: {e}")
    
#     print(f"\n🎯 Analysis complete!")

# if __name__ == "__main__":
#     main()

    

# import requests
# import time
# from datetime import datetime, timedelta
# import json

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     """Get the team ID"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     """Get all team members"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     return []

# def get_today_timestamps():
#     """Get start and end timestamps for today"""
#     now = datetime.now()
#     start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
#     # Convert to ClickUp timestamps (milliseconds)
#     start_ts = int(start_of_day.timestamp() * 1000)
#     current_ts = int(now.timestamp() * 1000)
    
#     return start_ts, current_ts, start_of_day, now

# def get_member_tasks(team_id, member_id, max_retries=3):
#     """Get all open tasks for a team member"""
#     for attempt in range(max_retries):
#         try:
#             # Get open tasks only
#             url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60
#                 print(f"    Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('tasks', [])
            
#         except requests.exceptions.RequestException as e:
#             print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)
    
#     print("    Failed to fetch tasks after all retries")
#     return []

# def is_task_in_progress(task):
#     """Check if a task is currently in 'in progress' status"""
#     status = task.get('status', {})
#     if not status:
#         return False
    
#     status_name = status.get('status', '').lower()
    
#     # Common "in progress" status variations
#     progress_keywords = [
#         'progress', 'in progress', 'in-progress', 'inprogress',
#         'active', 'working', 'doing', 'current', 'ongoing',
#         'started', 'development', 'dev', 'implementing',
#         'in dev', 'in development'
#     ]
    
#     return any(keyword in status_name for keyword in progress_keywords)

# def get_task_activity_today(task_id, today_start):
#     """Get task activity for today only"""
#     try:
#         resp = requests.get(f"{BASE_URL}/task/{task_id}/activity", headers=HEADERS)
        
#         if resp.status_code == 429:
#             time.sleep(30)
#             return []
        
#         if resp.status_code == 404:
#             return []
            
#         resp.raise_for_status()
#         all_activity = resp.json().get('activity', [])
        
#         # Filter for today's activity only
#         today_activity = []
#         for activity in all_activity:
#             activity_timestamp = activity.get('date')
#             if activity_timestamp:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
#                 if activity_time.date() == today_start.date():
#                     today_activity.append(activity)
        
#         return today_activity
        
#     except Exception as e:
#         print(f"    Error getting activity for task {task_id}: {e}")
#         return []

# def find_in_progress_periods_today(tasks, today_start, current_time):
#     """Find all periods when user had in-progress tasks today"""
#     in_progress_periods = []
    
#     print(f"    Analyzing {len(tasks)} tasks for in-progress periods...")
    
#     # Check current status first
#     currently_in_progress = []
#     for task in tasks:
#         if is_task_in_progress(task):
#             currently_in_progress.append(task)
#             print(f"      ✅ Currently in progress: {task['name'][:50]}")
    
#     # If tasks are currently in progress, we need to find when they started
#     for task in currently_in_progress:
#         task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
#         # If task was updated today, use that as start time
#         if task_updated.date() == current_time.date():
#             period_start = task_updated
#         else:
#             # Task was already in progress from start of day
#             period_start = today_start.replace(hour=9)  # Assume 9 AM work start
        
#         in_progress_periods.append({
#             'start': period_start,
#             'end': current_time,
#             'task_name': task['name'],
#             'duration_hours': (current_time - period_start).total_seconds() / 3600
#         })
    
#     # Also check activity for status changes today (sample first 10 tasks to avoid rate limits)
#     for task in tasks[:10]:
#         print(f"      Checking activity for: {task['name'][:40]}...")
#         activity = get_task_activity_today(task['id'], today_start)
        
#         # Look for status changes to "in progress" today
#         for activity_item in activity:
#             comment = activity_item.get('comment', '').lower()
#             activity_timestamp = activity_item.get('date')
            
#             if activity_timestamp and 'status' in comment:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                
#                 # Check if status changed TO in-progress
#                 if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
#                     if 'to' in comment:
#                         # Find when this in-progress period ended (or is still ongoing)
#                         period_end = current_time
                        
#                         # Look for later status changes
#                         for later_activity in activity:
#                             later_timestamp = later_activity.get('date')
#                             if later_timestamp and int(later_timestamp) > int(activity_timestamp):
#                                 later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
#                                 later_comment = later_activity.get('comment', '').lower()
                                
#                                 if 'status' in later_comment and 'to' in later_comment:
#                                     # Check if it changed away from in-progress
#                                     if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
#                                         period_end = later_time
#                                         break
                        
#                         duration = (period_end - activity_time).total_seconds() / 3600
#                         if duration > 0.1:  # At least 6 minutes
#                             in_progress_periods.append({
#                                 'start': activity_time,
#                                 'end': period_end,
#                                 'task_name': task['name'],
#                                 'duration_hours': duration
#                             })
                            
#                             print(f"        📅 Found period: {activity_time.strftime('%H:%M')} - "
#                                   f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
        
#         time.sleep(1)  # Rate limit prevention
    
#     # Sort and merge overlapping periods
#     in_progress_periods.sort(key=lambda x: x['start'])
#     merged_periods = []
    
#     for period in in_progress_periods:
#         if not merged_periods:
#             merged_periods.append(period)
#         else:
#             last_period = merged_periods[-1]
#             # If periods overlap or are close together (within 30 minutes)
#             if period['start'] <= last_period['end'] + timedelta(minutes=30):
#                 # Merge periods
#                 last_period['end'] = max(last_period['end'], period['end'])
#                 last_period['duration_hours'] = (last_period['end'] - last_period['start']).total_seconds() / 3600
#                 if period['task_name'] not in last_period['task_name']:
#                     last_period['task_name'] += f", {period['task_name']}"
#             else:
#                 merged_periods.append(period)
    
#     return merged_periods

# def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
#     """Calculate downtime periods of 3+ hours for today"""
#     print(f"    Calculating downtime for {member_name}...")
    
#     workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
#     downtime_periods = []
    
#     if not in_progress_periods:
#         # No in-progress periods at all today
#         if current_time > workday_start:
#             hours_inactive = (current_time - workday_start).total_seconds() / 3600
#             if hours_inactive >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': current_time,
#                     'duration_hours': hours_inactive,
#                     'type': 'no_activity_all_day'
#                 })
#                 print(f"      🔴 No activity all day: {hours_inactive:.1f} hours")
#     else:
#         # Check gap from workday start to first activity
#         first_activity = in_progress_periods[0]['start']
#         if first_activity > workday_start:
#             gap_hours = (first_activity - workday_start).total_seconds() / 3600
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': first_activity,
#                     'duration_hours': gap_hours,
#                     'type': 'late_start'
#                 })
#                 print(f"      🔴 Late start: {gap_hours:.1f} hours")
        
#         # Check gaps between activities
#         for i in range(len(in_progress_periods) - 1):
#             gap_start = in_progress_periods[i]['end']
#             gap_end = in_progress_periods[i + 1]['start']
#             gap_hours = (gap_end - gap_start).total_seconds() / 3600
            
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': gap_start,
#                     'end': gap_end,
#                     'duration_hours': gap_hours,
#                     'type': 'midday_gap'
#                 })
#                 print(f"      🔴 Midday gap: {gap_hours:.1f} hours")
        
#         # Check gap from last activity to now
#         last_activity = in_progress_periods[-1]['end']
#         current_gap_hours = (current_time - last_activity).total_seconds() / 3600
#         if current_gap_hours >= 3:
#             downtime_periods.append({
#                 'start': last_activity,
#                 'end': current_time,
#                 'duration_hours': current_gap_hours,
#                 'type': 'current_inactive'
#             })
#             print(f"      🔴 CURRENTLY INACTIVE: {current_gap_hours:.1f} hours since last activity")
    
#     return downtime_periods

# def main():
#     print("🚀 ClickUp TODAY Downtime Detector")
#     print("=" * 50)
    
#     # Get today's timestamps
#     start_ts, current_ts, today_start, current_time = get_today_timestamps()
#     print(f"📅 Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
#     print(f"⏰ Current time: {current_time.strftime('%H:%M:%S')}")
#     print(f"🕘 Work day assumption: 9:00 AM - now")
    
#     # Get team info
#     try:
#         team_id = get_team_id()
#         members = get_team_members(team_id)
#         print(f"🏢 Team ID: {team_id}")
#         print(f"👥 Team members: {len(members)}")
#     except Exception as e:
#         print(f"❌ Error getting team info: {e}")
#         return
    
#     members_with_downtime = []
#     all_member_data = {}
    
#     # Analyze each team member
#     for i, member in enumerate(members):
#         user_id = member['user']['id']
#         user_name = member['user']['username']
        
#         print(f"\n{'=' * 50}")
#         print(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
#         print('=' * 50)
        
#         try:
#             # Get member's tasks
#             tasks = get_member_tasks(team_id, user_id)
#             print(f"  📋 Found {len(tasks)} open tasks")
            
#             if not tasks:
#                 # No tasks = full downtime if it's been 3+ hours since work started
#                 workday_start = today_start.replace(hour=9)
#                 if current_time > workday_start:
#                     hours_since_work = (current_time - workday_start).total_seconds() / 3600
#                     if hours_since_work >= 3:
#                         downtime_periods = [{
#                             'start': workday_start,
#                             'end': current_time,
#                             'duration_hours': hours_since_work,
#                             'type': 'no_tasks'
#                         }]
#                         members_with_downtime.append(user_name)
#                         all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': downtime_periods}
#                         print(f"  🔴 NO TASKS: {hours_since_work:.1f} hours of downtime")
#                     else:
#                         all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#                 else:
#                     all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#             else:
#                 # Find in-progress periods
#                 in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
#                 print(f"  📊 Found {len(in_progress_periods)} in-progress periods today")
                
#                 # Calculate downtime
#                 downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                
#                 all_member_data[user_name] = {
#                     'in_progress_periods': in_progress_periods,
#                     'downtime_periods': downtime_periods
#                 }
                
#                 if downtime_periods:
#                     members_with_downtime.append(user_name)
#                     total_downtime = sum(p['duration_hours'] for p in downtime_periods)
#                     print(f"  🔴 DOWNTIME DETECTED: {total_downtime:.1f} total hours")
#                 else:
#                     print(f"  ✅ No significant downtime (active day)")
                    
#         except Exception as e:
#             print(f"  ❌ Error analyzing {user_name}: {e}")
#             all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
        
#         # Rate limiting between members
#         if i < len(members) - 1:
#             print("  ⏱️ Rate limiting pause...")
#             time.sleep(3)
    
#     # Print final summary
#     print(f"\n{'='*60}")
#     print(f"📊 TODAY'S DOWNTIME SUMMARY ({current_time.strftime('%A, %B %d, %Y - %H:%M')})")
#     print('='*60)
    
#     if not members_with_downtime:
#         print("✅ ALL TEAM MEMBERS ARE ACTIVE!")
#         print("   No one has 3+ hours of downtime today.")
#     else:
#         print(f"🚨 {len(members_with_downtime)} MEMBER(S) WITH 3+ HOUR DOWNTIME:")
        
#         for member_name in members_with_downtime:
#             data = all_member_data[member_name]
#             downtime_periods = data['downtime_periods']
#             total_downtime = sum(p['duration_hours'] for p in downtime_periods)
            
#             print(f"\n🔴 {member_name.upper()}:")
#             print(f"   💀 Total downtime today: {total_downtime:.1f} hours")
            
#             # Show current status
#             current_downtime = None
#             for period in downtime_periods:
#                 if abs((period['end'] - current_time).total_seconds()) < 300:  # Within 5 minutes of now
#                     current_downtime = period
#                     break
            
#             if current_downtime:
#                 print(f"   🔥 STATUS: CURRENTLY INACTIVE (since {current_downtime['start'].strftime('%H:%M')})")
#             else:
#                 print(f"   ✅ STATUS: Currently active")
            
#             # List all downtime periods
#             for i, period in enumerate(downtime_periods, 1):
#                 start_time = period['start'].strftime('%H:%M')
#                 end_time = period['end'].strftime('%H:%M') if period['end'] != current_time else "NOW"
#                 duration = period['duration_hours']
#                 period_type = period['type']
                
#                 status_emoji = "🔥" if period['end'] == current_time else "⏸️"
#                 print(f"   {status_emoji} Period {i}: {start_time} - {end_time} ({duration:.1f}h) [{period_type}]")
    
#     # Final stats
#     print(f"\n📈 FINAL STATS:")
#     print(f"   🕐 Current time: {current_time.strftime('%H:%M')}")
#     print(f"   👥 Total members: {len(members)}")
#     print(f"   ✅ Active members: {len(members) - len(members_with_downtime)}")
#     print(f"   🔴 Members with 3+ hour downtime: {len(members_with_downtime)}")
    
#     if members_with_downtime:
#         print(f"\n⚠️  IMMEDIATE ATTENTION NEEDED:")
#         print(f"   {', '.join(members_with_downtime)}")
    
#     print(f"\n🎯 Today's monitoring complete!")
    
#     # Save results to file
#     results = {
#         'timestamp': current_time.isoformat(),
#         'date': current_time.strftime('%Y-%m-%d'),
#         'members_analyzed': len(members),
#         'members_with_downtime': len(members_with_downtime),
#         'downtime_members': members_with_downtime,
#         'detailed_data': all_member_data
#     }
    
#     filename = f"clickup_downtime_{current_time.strftime('%Y%m%d_%H%M')}.json"
#     try:
#         with open(filename, 'w') as f:
#             json.dump(results, f, indent=2, default=str)
#         print(f"💾 Results saved to: {filename}")
#     except Exception as e:
#         print(f"⚠️  Could not save results: {e}")

# if __name__ == "__main__":
#     main()



# import requests
# import time
# from datetime import datetime, timedelta
# import json

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     """Get the team ID"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     """Get all team members"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     return []

# def get_today_timestamps():
#     """Get start and end timestamps for today"""
#     now = datetime.now()
#     start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
#     # Convert to ClickUp timestamps (milliseconds)
#     start_ts = int(start_of_day.timestamp() * 1000)
#     current_ts = int(now.timestamp() * 1000)
    
#     return start_ts, current_ts, start_of_day, now

# def get_member_tasks(team_id, member_id, max_retries=3):
#     """Get all open tasks for a team member"""
#     for attempt in range(max_retries):
#         try:
#             # Get open tasks only
#             url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60
#                 print(f"    Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('tasks', [])
            
#         except requests.exceptions.RequestException as e:
#             print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)
    
#     print("    Failed to fetch tasks after all retries")
#     return []

# def is_task_in_progress(task):
#     """Check if a task is currently in 'in progress' status"""
#     status = task.get('status', {})
#     if not status:
#         return False
    
#     status_name = status.get('status', '').lower()
    
#     # Common "in progress" status variations
#     progress_keywords = [
#         'progress', 'in progress', 'in-progress', 'inprogress',
#         'active', 'working', 'doing', 'current', 'ongoing',
#         'started', 'development', 'dev', 'implementing',
#         'in dev', 'in development'
#     ]
    
#     return any(keyword in status_name for keyword in progress_keywords)

# def get_task_activity_today(task_id, today_start):
#     """Get task activity for today only"""
#     try:
#         resp = requests.get(f"{BASE_URL}/task/{task_id}/activity", headers=HEADERS)
        
#         if resp.status_code == 429:
#             time.sleep(30)
#             return []
        
#         if resp.status_code == 404:
#             return []
            
#         resp.raise_for_status()
#         all_activity = resp.json().get('activity', [])
        
#         # Filter for today's activity only
#         today_activity = []
#         for activity in all_activity:
#             activity_timestamp = activity.get('date')
#             if activity_timestamp:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
#                 if activity_time.date() == today_start.date():
#                     today_activity.append(activity)
        
#         return today_activity
        
#     except Exception as e:
#         print(f"    Error getting activity for task {task_id}: {e}")
#         return []

# def find_in_progress_periods_today(tasks, today_start, current_time):
#     """Find all periods when user had in-progress tasks today"""
#     in_progress_periods = []
    
#     print(f"    Analyzing {len(tasks)} tasks for in-progress periods...")
    
#     # Check current status first
#     currently_in_progress = []
#     for task in tasks:
#         if is_task_in_progress(task):
#             currently_in_progress.append(task)
#             print(f"      ✅ Currently in progress: {task['name'][:50]}")
    
#     # If tasks are currently in progress, we need to find when they started
#     for task in currently_in_progress:
#         task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
#         # If task was updated today, use that as start time
#         if task_updated.date() == current_time.date():
#             period_start = task_updated
#         else:
#             # Task was already in progress from start of day
#             period_start = today_start.replace(hour=9)  # Assume 9 AM work start
        
#         in_progress_periods.append({
#             'start': period_start,
#             'end': current_time,
#             'task_name': task['name'],
#             'duration_hours': (current_time - period_start).total_seconds() / 3600
#         })
    
#     # Also check activity for status changes today (sample first 10 tasks to avoid rate limits)
#     for task in tasks[:10]:
#         print(f"      Checking activity for: {task['name'][:40]}...")
#         activity = get_task_activity_today(task['id'], today_start)
        
#         # Look for status changes to "in progress" today
#         for activity_item in activity:
#             comment = activity_item.get('comment', '').lower()
#             activity_timestamp = activity_item.get('date')
            
#             if activity_timestamp and 'status' in comment:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                
#                 # Check if status changed TO in-progress
#                 if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
#                     if 'to' in comment:
#                         # Find when this in-progress period ended (or is still ongoing)
#                         period_end = current_time
                        
#                         # Look for later status changes
#                         for later_activity in activity:
#                             later_timestamp = later_activity.get('date')
#                             if later_timestamp and int(later_timestamp) > int(activity_timestamp):
#                                 later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
#                                 later_comment = later_activity.get('comment', '').lower()
                                
#                                 if 'status' in later_comment and 'to' in later_comment:
#                                     # Check if it changed away from in-progress
#                                     if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
#                                         period_end = later_time
#                                         break
                        
#                         duration = (period_end - activity_time).total_seconds() / 3600
#                         if duration > 0.1:  # At least 6 minutes
#                             in_progress_periods.append({
#                                 'start': activity_time,
#                                 'end': period_end,
#                                 'task_name': task['name'],
#                                 'duration_hours': duration
#                             })
                            
#                             print(f"        📅 Found period: {activity_time.strftime('%H:%M')} - "
#                                   f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
        
#         time.sleep(1)  # Rate limit prevention
    
#     # Sort and merge overlapping periods
#     in_progress_periods.sort(key=lambda x: x['start'])
#     merged_periods = []
    
#     for period in in_progress_periods:
#         if not merged_periods:
#             merged_periods.append(period)
#         else:
#             last_period = merged_periods[-1]
#             # If periods overlap or are close together (within 30 minutes)
#             if period['start'] <= last_period['end'] + timedelta(minutes=30):
#                 # Merge periods
#                 last_period['end'] = max(last_period['end'], period['end'])
#                 last_period['duration_hours'] = (last_period['end'] - last_period['start']).total_seconds() / 3600
#                 if period['task_name'] not in last_period['task_name']:
#                     last_period['task_name'] += f", {period['task_name']}"
#             else:
#                 merged_periods.append(period)
    
#     return merged_periods

# def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
#     """Calculate downtime periods of 3+ hours for today"""
#     print(f"    Calculating downtime for {member_name}...")
    
#     workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
#     downtime_periods = []
    
#     if not in_progress_periods:
#         # No in-progress periods at all today
#         if current_time > workday_start:
#             hours_inactive = (current_time - workday_start).total_seconds() / 3600
#             if hours_inactive >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': current_time,
#                     'duration_hours': hours_inactive,
#                     'type': 'no_activity_all_day'
#                 })
#                 print(f"      🔴 No activity all day: {hours_inactive:.1f} hours")
#     else:
#         # Check gap from workday start to first activity
#         first_activity = in_progress_periods[0]['start']
#         if first_activity > workday_start:
#             gap_hours = (first_activity - workday_start).total_seconds() / 3600
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': first_activity,
#                     'duration_hours': gap_hours,
#                     'type': 'late_start'
#                 })
#                 print(f"      🔴 Late start: {gap_hours:.1f} hours")
        
#         # Check gaps between activities
#         for i in range(len(in_progress_periods) - 1):
#             gap_start = in_progress_periods[i]['end']
#             gap_end = in_progress_periods[i + 1]['start']
#             gap_hours = (gap_end - gap_start).total_seconds() / 3600
            
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': gap_start,
#                     'end': gap_end,
#                     'duration_hours': gap_hours,
#                     'type': 'midday_gap'
#                 })
#                 print(f"      🔴 Midday gap: {gap_hours:.1f} hours")
        
#         # Check gap from last activity to now
#         last_activity = in_progress_periods[-1]['end']
#         current_gap_hours = (current_time - last_activity).total_seconds() / 3600
#         if current_gap_hours >= 3:
#             downtime_periods.append({
#                 'start': last_activity,
#                 'end': current_time,
#                 'duration_hours': current_gap_hours,
#                 'type': 'current_inactive'
#             })
#             print(f"      🔴 CURRENTLY INACTIVE: {current_gap_hours:.1f} hours since last activity")
    
#     return downtime_periods

# def find_user_by_name(members, name):
#     """Find a user by their username or display name"""
#     name_lower = name.lower()
#     for member in members:
#         user = member.get('user', {})
#         username = user.get('username', '').lower()
#         email = user.get('email', '').lower()
        
#         if (name_lower in username or 
#             name_lower in email or 
#             username == name_lower):
#             return user
#     return None

# def add_watcher_to_task(task_id, user_id, user_name="Unknown"):
#     """Add a user as a watcher to a specific task"""
#     try:
#         url = f"{BASE_URL}/task/{task_id}/watcher/{user_id}"
#         resp = requests.post(url, headers=HEADERS)
        
#         if resp.status_code == 200:
#             print(f"      ✅ Added {user_name} as watcher to task {task_id}")
#             return True
#         elif resp.status_code == 400:
#             # User might already be a watcher
#             print(f"      ℹ️ {user_name} might already be watching task {task_id}")
#             return True
#         else:
#             print(f"      ❌ Failed to add {user_name} as watcher: {resp.status_code}")
#             return False
            
#     except Exception as e:
#         print(f"      ❌ Error adding {user_name} as watcher: {e}")
#         return False

# def add_watcher_to_all_tasks(tasks, watcher_user_id, watcher_name, dry_run=False):
#     """Add a watcher to multiple tasks"""
#     print(f"\n👁️ {'[DRY RUN] ' if dry_run else ''}Adding {watcher_name} as watcher to {len(tasks)} tasks...")
    
#     success_count = 0
#     failed_count = 0
    
#     for i, task in enumerate(tasks, 1):
#         task_id = task['id']
#         task_name = task['name'][:50] + "..." if len(task['name']) > 50 else task['name']
        
#         print(f"   {i}/{len(tasks)}: {task_name}")
        
#         if dry_run:
#             print(f"      🔍 [DRY RUN] Would add {watcher_name} as watcher")
#             success_count += 1
#         else:
#             if add_watcher_to_task(task_id, watcher_user_id, watcher_name):
#                 success_count += 1
#             else:
#                 failed_count += 1
            
#             # Rate limiting
#             time.sleep(1)
    
#     print(f"\n📊 Watcher Addition Summary:")
#     print(f"   ✅ Successful: {success_count}")
#     if not dry_run:
#         print(f"   ❌ Failed: {failed_count}")
    
#     return success_count, failed_count

# def get_member_tasks_with_date_range(team_id, member_id, days_back=7, max_retries=3):
#     """Get tasks for a member within a date range"""
#     for attempt in range(max_retries):
#         try:
#             # Calculate date range
#             end_date = datetime.now()
#             start_date = end_date - timedelta(days=days_back)
            
#             start_ts = int(start_date.timestamp() * 1000)
#             end_ts = int(end_date.timestamp() * 1000)
            
#             # Get tasks updated within date range
#             url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false&date_updated_gt={start_ts}&date_updated_lt={end_ts}"
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60
#                 print(f"    Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('tasks', [])
            
#         except requests.exceptions.RequestException as e:
#             print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)
    
#     print("    Failed to fetch tasks after all retries")
#     return []

# def main():
#     print("🚀 ClickUp Member Downtime Analysis & Watcher Management")
#     print("=" * 60)
    
#     # Get team info
#     try:
#         team_id = get_team_id()
#         members = get_team_members(team_id)
#         print(f"🏢 Team ID: {team_id}")
#         print(f"👥 Team members: {len(members)}")
#     except Exception as e:
#         print(f"❌ Error getting team info: {e}")
#         return
    
#     # Interactive menu
#     print(f"\n🔧 What would you like to do?")
#     print("1. Analyze member downtime only")
#     print("2. Add Sean as watcher to all recent tasks")
#     print("3. Add custom person as watcher to tasks")
#     print("4. Both downtime analysis and add watchers")
    
#     choice = input("\nEnter your choice (1-4): ").strip()
    
#     if choice not in ['1', '2', '3', '4']:
#         print("❌ Invalid choice. Please run again and select 1-4.")
#         return
    
#     # Handle watcher functionality
#     if choice in ['2', '3', '4']:
#         # Get date range for tasks
#         days_back_input = input("How many days back to look for tasks? (default: 7): ").strip()
#         try:
#             days_back = int(days_back_input) if days_back_input else 7
#         except ValueError:
#             days_back = 7
        
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=days_back)
#         print(f"📅 Working with period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
#         # Find watcher user
#         if choice == '2':
#             watcher_name = 'sean'
#         else:
#             watcher_name = input("Enter the name/username of person to add as watcher: ").strip()
        
#         watcher_user = find_user_by_name(members, watcher_name)
#         if not watcher_user:
#             print(f"❌ Could not find user '{watcher_name}' in the team")
#             print("Available users:")
#             for member in members:
#                 user = member.get('user', {})
#                 print(f"   - {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
#             return
        
#         watcher_user_id = watcher_user['id']
#         watcher_username = watcher_user['username']
#         print(f"👁️ Found watcher: {watcher_username} (ID: {watcher_user_id})")
        
#         # Ask for dry run
#         dry_run_input = input("Do a dry run first? (y/n, default: y): ").strip().lower()
#         dry_run = dry_run_input != 'n'
        
#         # Collect all tasks from all members
#         all_tasks = []
#         print(f"\n📋 Collecting tasks from all team members...")
        
#         for i, member in enumerate(members):
#             user_id = member['user']['id']
#             user_name = member['user']['username']
#             print(f"   Getting tasks for {user_name}...")
            
#             tasks = get_member_tasks_with_date_range(team_id, user_id, days_back)
#             all_tasks.extend(tasks)
            
#             if i < len(members) - 1:
#                 time.sleep(2)  # Rate limiting
        
#         # Remove duplicates (same task might be assigned to multiple people)
#         unique_tasks = {}
#         for task in all_tasks:
#             unique_tasks[task['id']] = task
        
#         unique_task_list = list(unique_tasks.values())
#         print(f"📊 Found {len(unique_task_list)} unique tasks")
        
#         # Add watcher to tasks
#         if len(unique_task_list) > 0:
#             add_watcher_to_all_tasks(unique_task_list, watcher_user_id, watcher_username, dry_run)
            
#             if dry_run:
#                 confirm = input(f"\n🤔 Proceed with actually adding {watcher_username} to {len(unique_task_list)} tasks? (y/n): ").strip().lower()
#                 if confirm == 'y':
#                     add_watcher_to_all_tasks(unique_task_list, watcher_user_id, watcher_username, dry_run=False)
#         else:
#             print("❌ No tasks found to add watchers to")
    
#     # Handle downtime analysis  
#     if choice in ['1', '4']:
#         print(f"\n📊 Starting TODAY's downtime analysis...")
        
#         # Get today's timestamps
#         start_ts, current_ts, today_start, current_time = get_today_timestamps()
#         print(f"📅 Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
#         print(f"⏰ Current time: {current_time.strftime('%H:%M:%S')}")
#         print(f"🕘 Work day assumption: 9:00 AM - now")
    
        
#         members_with_downtime = []
#         all_member_data = {}
        
#         # Analyze each team member
#         for i, member in enumerate(members):
#             user_id = member['user']['id']
#             user_name = member['user']['username']
            
#             print(f"\n{'=' * 50}")
#             print(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
#             print('=' * 50)
            
#             try:
#                 # Get member's tasks
#                 tasks = get_member_tasks(team_id, user_id)
#                 print(f"  📋 Found {len(tasks)} open tasks")
                
#                 if not tasks:
#                     # No tasks = full downtime if it's been 3+ hours since work started
#                     workday_start = today_start.replace(hour=9)
#                     if current_time > workday_start:
#                         hours_since_work = (current_time - workday_start).total_seconds() / 3600
#                         if hours_since_work >= 3:
#                             downtime_periods = [{
#                                 'start': workday_start,
#                                 'end': current_time,
#                                 'duration_hours': hours_since_work,
#                                 'type': 'no_tasks'
#                             }]
#                             members_with_downtime.append(user_name)
#                             all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': downtime_periods}
#                             print(f"  🔴 NO TASKS: {hours_since_work:.1f} hours of downtime")
#                         else:
#                             all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#                     else:
#                         all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#                 else:
#                     # Find in-progress periods
#                     in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
#                     print(f"  📊 Found {len(in_progress_periods)} in-progress periods today")
                    
#                     # Calculate downtime
#                     downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
#                     all_member_data[user_name] = {
#                         'in_progress_periods': in_progress_periods,
#                         'downtime_periods': downtime_periods
#                     }
                    
#                     if downtime_periods:
#                         members_with_downtime.append(user_name)
#                         total_downtime = sum(p['duration_hours'] for p in downtime_periods)
#                         print(f"  🔴 DOWNTIME DETECTED: {total_downtime:.1f} total hours")
#                     else:
#                         print(f"  ✅ No significant downtime (active day)")
                        
#             except Exception as e:
#                 print(f"  ❌ Error analyzing {user_name}: {e}")
#                 all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
            
#             # Rate limiting between members
#             if i < len(members) - 1:
#                 print("  ⏱️ Rate limiting pause...")
#                 time.sleep(3)
        
#         # Print final summary
#         print(f"\n{'='*60}")
#         print(f"📊 TODAY'S DOWNTIME SUMMARY ({current_time.strftime('%A, %B %d, %Y - %H:%M')})")
#         print('='*60)
        
#         if not members_with_downtime:
#             print("✅ ALL TEAM MEMBERS ARE ACTIVE!")
#             print("   No one has 3+ hours of downtime today.")
#         else:
#             print(f"🚨 {len(members_with_downtime)} MEMBER(S) WITH 3+ HOUR DOWNTIME:")
            
#             for member_name in members_with_downtime:
#                 data = all_member_data[member_name]
#                 downtime_periods = data['downtime_periods']
#                 total_downtime = sum(p['duration_hours'] for p in downtime_periods)
                
#                 print(f"\n🔴 {member_name.upper()}:")
#                 print(f"   💀 Total downtime today: {total_downtime:.1f} hours")
                
#                 # Show current status
#                 current_downtime = None
#                 for period in downtime_periods:
#                     if abs((period['end'] - current_time).total_seconds()) < 300:  # Within 5 minutes of now
#                         current_downtime = period
#                         break
                
#                 if current_downtime:
#                     print(f"   🔥 STATUS: CURRENTLY INACTIVE (since {current_downtime['start'].strftime('%H:%M')})")
#                 else:
#                     print(f"   ✅ STATUS: Currently active")
                
#                 # List all downtime periods
#                 for i, period in enumerate(downtime_periods, 1):
#                     start_time = period['start'].strftime('%H:%M')
#                     end_time = period['end'].strftime('%H:%M') if period['end'] != current_time else "NOW"
#                     duration = period['duration_hours']
#                     period_type = period['type']
                    
#                     status_emoji = "🔥" if period['end'] == current_time else "⏸️"
#                     print(f"   {status_emoji} Period {i}: {start_time} - {end_time} ({duration:.1f}h) [{period_type}]")
        
#         # Final stats
#         print(f"\n📈 FINAL STATS:")
#         print(f"   🕐 Current time: {current_time.strftime('%H:%M')}")
#         print(f"   👥 Total members: {len(members)}")
#         print(f"   ✅ Active members: {len(members) - len(members_with_downtime)}")
#         print(f"   🔴 Members with 3+ hour downtime: {len(members_with_downtime)}")
        
#         if members_with_downtime:
#             print(f"\n⚠️  IMMEDIATE ATTENTION NEEDED:")
#             print(f"   {', '.join(members_with_downtime)}")
        
#         print(f"\n🎯 Today's monitoring complete!")
        
#         # Save results to file
#         if 'all_member_data' in locals():
#             results = {
#                 'timestamp': current_time.isoformat(),
#                 'date': current_time.strftime('%Y-%m-%d'),
#                 'members_analyzed': len(members),
#                 'members_with_downtime': len(members_with_downtime),
#                 'downtime_members': members_with_downtime,
#                 'detailed_data': all_member_data
#             }
            
#             filename = f"clickup_downtime_{current_time.strftime('%Y%m%d_%H%M')}.json"
#             try:
#                 with open(filename, 'w') as f:
#                     json.dump(results, f, indent=2, default=str)
#                 print(f"💾 Results saved to: {filename}")
#             except Exception as e:
#                 print(f"⚠️  Could not save results: {e}")
    
#     print(f"\n🎯 Analysis complete!")

# if __name__ == "__main__":
#     main()


# import requests
# import time
# from datetime import datetime, timedelta
# import json
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# from matplotlib.patches import Rectangle
# import pandas as pd
# import seaborn as sns
# import numpy as np

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
# HEADERS = {'Authorization': API_TOKEN}
# BASE_URL = 'https://api.clickup.com/api/v2'

# def get_team_id():
#     """Get the team ID"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()['teams'][0]['id']

# def get_team_members(team_id):
#     """Get all team members"""
#     resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
#     resp.raise_for_status()
#     teams = resp.json().get('teams', [])
#     for team in teams:
#         if team.get('id') == str(team_id):
#             return team.get('members', [])
#     return []

# def get_today_timestamps():
#     """Get start and end timestamps for today"""
#     now = datetime.now()
#     start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
#     # Convert to ClickUp timestamps (milliseconds)
#     start_ts = int(start_of_day.timestamp() * 1000)
#     current_ts = int(now.timestamp() * 1000)
    
#     return start_ts, current_ts, start_of_day, now

# def get_member_tasks(team_id, member_id, max_retries=3):
#     """Get all open tasks for a team member"""
#     for attempt in range(max_retries):
#         try:
#             # Get open tasks only
#             url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60
#                 print(f"    Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('tasks', [])
            
#         except requests.exceptions.RequestException as e:
#             print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)
    
#     print("    Failed to fetch tasks after all retries")
#     return []

# def is_task_in_progress(task):
#     """Check if a task is currently in 'in progress' status"""
#     status = task.get('status', {})
#     if not status:
#         return False
    
#     status_name = status.get('status', '').lower()
    
#     # Common "in progress" status variations
#     progress_keywords = [
#         'progress', 'in progress', 'in-progress', 'inprogress',
#         'active', 'working', 'doing', 'current', 'ongoing',
#         'started', 'development', 'dev', 'implementing',
#         'in dev', 'in development'
#     ]
    
#     return any(keyword in status_name for keyword in progress_keywords)

# def get_task_activity_today(task_id, today_start):
#     """Get task activity for today only"""
#     try:
#         resp = requests.get(f"{BASE_URL}/task/{task_id}/activity", headers=HEADERS)
        
#         if resp.status_code == 429:
#             time.sleep(30)
#             return []
        
#         if resp.status_code == 404:
#             return []
            
#         resp.raise_for_status()
#         all_activity = resp.json().get('activity', [])
        
#         # Filter for today's activity only
#         today_activity = []
#         for activity in all_activity:
#             activity_timestamp = activity.get('date')
#             if activity_timestamp:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
#                 if activity_time.date() == today_start.date():
#                     today_activity.append(activity)
        
#         return today_activity
        
#     except Exception as e:
#         print(f"    Error getting activity for task {task_id}: {e}")
#         return []

# def find_in_progress_periods_today(tasks, today_start, current_time):
#     """Find all periods when user had in-progress tasks today"""
#     in_progress_periods = []
    
#     print(f"    Analyzing {len(tasks)} tasks for in-progress periods...")
    
#     # Check current status first
#     currently_in_progress = []
#     for task in tasks:
#         if is_task_in_progress(task):
#             currently_in_progress.append(task)
#             print(f"      ✅ Currently in progress: {task['name'][:50]}")
    
#     # If tasks are currently in progress, we need to find when they started
#     for task in currently_in_progress:
#         task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
#         # If task was updated today, use that as start time
#         if task_updated.date() == current_time.date():
#             period_start = task_updated
#         else:
#             # Task was already in progress from start of day
#             period_start = today_start.replace(hour=9)  # Assume 9 AM work start
        
#         in_progress_periods.append({
#             'start': period_start,
#             'end': current_time,
#             'task_name': task['name'],
#             'duration_hours': (current_time - period_start).total_seconds() / 3600
#         })
    
#     # Also check activity for status changes today (sample first 10 tasks to avoid rate limits)
#     for task in tasks[:10]:
#         print(f"      Checking activity for: {task['name'][:40]}...")
#         activity = get_task_activity_today(task['id'], today_start)
        
#         # Look for status changes to "in progress" today
#         for activity_item in activity:
#             comment = activity_item.get('comment', '').lower()
#             activity_timestamp = activity_item.get('date')
            
#             if activity_timestamp and 'status' in comment:
#                 activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                
#                 # Check if status changed TO in-progress
#                 if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
#                     if 'to' in comment:
#                         # Find when this in-progress period ended (or is still ongoing)
#                         period_end = current_time
                        
#                         # Look for later status changes
#                         for later_activity in activity:
#                             later_timestamp = later_activity.get('date')
#                             if later_timestamp and int(later_timestamp) > int(activity_timestamp):
#                                 later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
#                                 later_comment = later_activity.get('comment', '').lower()
                                
#                                 if 'status' in later_comment and 'to' in later_comment:
#                                     # Check if it changed away from in-progress
#                                     if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
#                                         period_end = later_time
#                                         break
                        
#                         duration = (period_end - activity_time).total_seconds() / 3600
#                         if duration > 0.1:  # At least 6 minutes
#                             in_progress_periods.append({
#                                 'start': activity_time,
#                                 'end': period_end,
#                                 'task_name': task['name'],
#                                 'duration_hours': duration
#                             })
                            
#                             print(f"        📅 Found period: {activity_time.strftime('%H:%M')} - "
#                                   f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
        
#         time.sleep(1)  # Rate limit prevention
    
#     # Sort and merge overlapping periods
#     in_progress_periods.sort(key=lambda x: x['start'])
#     merged_periods = []
    
#     for period in in_progress_periods:
#         if not merged_periods:
#             merged_periods.append(period)
#         else:
#             last_period = merged_periods[-1]
#             # If periods overlap or are close together (within 30 minutes)
#             if period['start'] <= last_period['end'] + timedelta(minutes=30):
#                 # Merge periods
#                 last_period['end'] = max(last_period['end'], period['end'])
#                 last_period['duration_hours'] = (last_period['end'] - last_period['start']).total_seconds() / 3600
#                 if period['task_name'] not in last_period['task_name']:
#                     last_period['task_name'] += f", {period['task_name']}"
#             else:
#                 merged_periods.append(period)
    
#     return merged_periods

# def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
#     """Calculate downtime periods of 3+ hours for today"""
#     print(f"    Calculating downtime for {member_name}...")
    
#     workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
#     downtime_periods = []
    
#     if not in_progress_periods:
#         # No in-progress periods at all today
#         if current_time > workday_start:
#             hours_inactive = (current_time - workday_start).total_seconds() / 3600
#             if hours_inactive >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': current_time,
#                     'duration_hours': hours_inactive,
#                     'type': 'no_activity_all_day'
#                 })
#                 print(f"      🔴 No activity all day: {hours_inactive:.1f} hours")
#     else:
#         # Check gap from workday start to first activity
#         first_activity = in_progress_periods[0]['start']
#         if first_activity > workday_start:
#             gap_hours = (first_activity - workday_start).total_seconds() / 3600
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': workday_start,
#                     'end': first_activity,
#                     'duration_hours': gap_hours,
#                     'type': 'late_start'
#                 })
#                 print(f"      🔴 Late start: {gap_hours:.1f} hours")
        
#         # Check gaps between activities
#         for i in range(len(in_progress_periods) - 1):
#             gap_start = in_progress_periods[i]['end']
#             gap_end = in_progress_periods[i + 1]['start']
#             gap_hours = (gap_end - gap_start).total_seconds() / 3600
            
#             if gap_hours >= 3:
#                 downtime_periods.append({
#                     'start': gap_start,
#                     'end': gap_end,
#                     'duration_hours': gap_hours,
#                     'type': 'midday_gap'
#                 })
#                 print(f"      🔴 Midday gap: {gap_hours:.1f} hours")
        
#         # Check gap from last activity to now
#         last_activity = in_progress_periods[-1]['end']
#         current_gap_hours = (current_time - last_activity).total_seconds() / 3600
#         if current_gap_hours >= 3:
#             downtime_periods.append({
#                 'start': last_activity,
#                 'end': current_time,
#                 'duration_hours': current_gap_hours,
#                 'type': 'current_inactive'
#             })
#             print(f"      🔴 CURRENTLY INACTIVE: {current_gap_hours:.1f} hours since last activity")
    
#     return downtime_periods

# def find_user_by_name(members, name):
#     """Find a user by their username or display name"""
#     name_lower = name.lower()
#     for member in members:
#         user = member.get('user', {})
#         username = user.get('username', '').lower()
#         email = user.get('email', '').lower()
        
#         if (name_lower in username or 
#             name_lower in email or 
#             username == name_lower):
#             return user
#     return None

# def get_task_details(task_id):
#     """Get detailed task information including watchers"""
#     try:
#         resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=HEADERS)
#         if resp.status_code == 200:
#             return resp.json()
#         elif resp.status_code == 404:
#             print(f"      ⚠️ Task {task_id} not found or no access")
#         elif resp.status_code == 401:
#             print(f"      ⚠️ No permission to access task {task_id}")
#         else:
#             print(f"      ⚠️ Error {resp.status_code} accessing task {task_id}")
#         return None
#     except Exception as e:
#         print(f"      ❌ Exception getting task details: {e}")
#         return None

# def debug_watcher_api(task_id, user_id, user_name):
#     """Enhanced debug function to test all API endpoints systematically"""
#     print(f"    🔍 [DEBUG] Testing watcher API for task {task_id} and user {user_name}...")
    
#     # Get task details first
#     task_details = get_task_details(task_id)
#     if task_details:
#         task_name = task_details.get('name', 'Unknown')[:50]
#         print(f"      📋 Task: {task_name}")
#         current_watchers = task_details.get('watchers', [])
#         print(f"      👁️ Current watchers: {len(current_watchers)}")
        
#         # Check if user is already a watcher
#         watcher_ids = [str(w.get('id', '')) for w in current_watchers if w.get('id')]
#         if str(user_id) in watcher_ids:
#             print(f"      ✅ {user_name} is already watching this task!")
#             return True
        
#         # Show current watchers
#         for watcher in current_watchers:
#             watcher_user = watcher.get('user', {})
#             watcher_name = watcher_user.get('username', 'Unknown')
#             print(f"         - {watcher_name}")
#     else:
#         print(f"      ❌ Cannot access task {task_id}")
#         return False
    
#     # Test different API endpoints systematically
#     test_methods = [
#         {
#             'name': 'PUT /task/{id}/watcher (watchers.add array)',
#             'method': 'PUT',
#             'url': f"{BASE_URL}/task/{task_id}/watcher",
#             'payload': {"watchers": {"add": [user_id]}},
#             'headers': {**HEADERS, 'Content-Type': 'application/json'}
#         },
#         {
#             'name': 'PUT /task/{id}/watcher (single watcher)',
#             'method': 'PUT', 
#             'url': f"{BASE_URL}/task/{task_id}/watcher",
#             'payload': {"watcher": user_id},
#             'headers': {**HEADERS, 'Content-Type': 'application/json'}
#         },
#         {
#             'name': 'POST /task/{id}/watcher/{user_id}',
#             'method': 'POST',
#             'url': f"{BASE_URL}/task/{task_id}/watcher/{user_id}",
#             'payload': None,
#             'headers': HEADERS
#         },
#         {
#             'name': 'POST /task/{id}/watcher',
#             'method': 'POST',
#             'url': f"{BASE_URL}/task/{task_id}/watcher",
#             'payload': {"watcher": user_id},
#             'headers': {**HEADERS, 'Content-Type': 'application/json'}
#         },
#         {
#             'name': 'PUT /task/{id} (update task)',
#             'method': 'PUT',
#             'url': f"{BASE_URL}/task/{task_id}",
#             'payload': {"watchers": {"add": [user_id]}},
#             'headers': {**HEADERS, 'Content-Type': 'application/json'}
#         }
#     ]
    
#     for i, method_info in enumerate(test_methods, 1):
#         try:
#             print(f"      🧪 Method {i}: {method_info['name']}")
            
#             if method_info['method'] == 'PUT':
#                 resp = requests.put(
#                     method_info['url'], 
#                     headers=method_info['headers'],
#                     json=method_info['payload'] if method_info['payload'] else None
#                 )
#             elif method_info['method'] == 'POST':
#                 if method_info['payload']:
#                     resp = requests.post(
#                         method_info['url'],
#                         headers=method_info['headers'],
#                         json=method_info['payload']
#                     )
#                 else:
#                     resp = requests.post(method_info['url'], headers=method_info['headers'])
            
#             print(f"         Status: {resp.status_code}")
            
#             if resp.status_code == 200:
#                 print(f"      ✅ SUCCESS! Method {i} worked!")
                
#                 # Verify the watcher was actually added
#                 time.sleep(1)
#                 updated_task = get_task_details(task_id)
#                 if updated_task:
#                     updated_watchers = updated_task.get('watchers', [])
#                     updated_watcher_ids = [str(w.get('id', '')) for w in updated_watchers if w.get('id')]
#                     if str(user_id) in updated_watcher_ids:
#                         print(f"      ✅ VERIFIED: {user_name} successfully added as watcher!")
#                         return True
#                     else:
#                         print(f"      ⚠️ API returned 200 but user not found in watchers list")
#                 else:
#                     print(f"      ⚠️ Cannot verify - task details unavailable")
                
#                 return True
                
#             elif resp.status_code in [400, 404, 403, 401]:
#                 try:
#                     error_data = resp.json()
#                     error_msg = error_data.get('err', error_data.get('error', 'Unknown error'))
#                     print(f"         Error: {error_msg}")
                    
#                     # Check for specific error conditions
#                     if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
#                         print(f"      ✅ User already watching (error message confirms)")
#                         return True
#                 except:
#                     print(f"         Raw response: {resp.text[:200]}")
#             else:
#                 print(f"         Unexpected status: {resp.status_code}")
                
#         except Exception as e:
#             print(f"         Exception: {str(e)[:100]}")
        
#         # Small delay between attempts
#         time.sleep(0.5)
    
#     print(f"      ❌ All {len(test_methods)} methods failed for {user_name}")
#     return False

# def add_watcher_to_task(task_id, user_id, user_name="Unknown", use_debug=False):
#     """Add a user as a watcher to a specific task with enhanced error handling"""
#     if use_debug:
#         return debug_watcher_api(task_id, user_id, user_name)
    
#     try:
#         # Quick method 1: Standard PUT with watchers array
#         url = f"{BASE_URL}/task/{task_id}/watcher"
#         payload = {"watchers": {"add": [user_id]}}
        
#         resp = requests.put(url, headers={**HEADERS, 'Content-Type': 'application/json'}, 
#                            json=payload)
        
#         if resp.status_code == 200:
#             print(f"      ✅ Added {user_name} as watcher")
#             return True
#         elif resp.status_code == 400:
#             # Check if user is already a watcher
#             error_msg = resp.json().get('err', '')
#             if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
#                 print(f"      ℹ️ {user_name} already watching")
#                 return True
        
#         # Method 2: POST with user_id in path
#         url = f"{BASE_URL}/task/{task_id}/watcher/{user_id}"
#         resp = requests.post(url, headers=HEADERS)
        
#         if resp.status_code == 200:
#             print(f"      ✅ Added {user_name} as watcher (method 2)")
#             return True
        
#         # If both quick methods fail, use debug mode
#         print(f"      🔧 Standard methods failed, trying debug mode...")
#         return debug_watcher_api(task_id, user_id, user_name)
            
#     except Exception as e:
#         print(f"      ❌ Error adding {user_name} as watcher: {e}")
#         return False

# def add_watcher_to_all_tasks(tasks, watcher_user_id, watcher_name, dry_run=False, debug_mode=False):
#     """Add a watcher to multiple tasks with progress tracking"""
#     print(f"\n👁️ {'[DRY RUN] ' if dry_run else ''}Adding {watcher_name} as watcher to {len(tasks)} tasks...")
    
#     if debug_mode:
#         print(f"🔍 Debug mode enabled - using comprehensive API testing")
    
#     success_count = 0
#     failed_count = 0
#     already_watching_count = 0
#     failed_tasks = []
    
#     for i, task in enumerate(tasks, 1):
#         task_id = task['id']
#         task_name = task['name'][:50] + "..." if len(task['name']) > 50 else task['name']
        
#         print(f"\n   [{i:3d}/{len(tasks)}] {task_name}")
        
#         if dry_run:
#             print(f"      🔍 [DRY RUN] Would add {watcher_name} as watcher")
#             success_count += 1
#         else:
#             # Use debug mode for first few tasks or if specifically requested
#             use_debug = debug_mode or (i <= 3 and failed_count > 0)
#             result = add_watcher_to_task(task_id, watcher_user_id, watcher_name, use_debug)
            
#             if result:
#                 success_count += 1
#             else:
#                 failed_count += 1
#                 failed_tasks.append({'id': task_id, 'name': task_name})
            
#             # Progressive rate limiting - slower if we're having failures
#             if failed_count > success_count:
#                 time.sleep(3)  # Slower when having issues
#             else:
#                 time.sleep(1.5)  # Normal rate
    
#     print(f"\n📊 Watcher Addition Summary:")
#     print(f"   ✅ Successful: {success_count}")
    
#     if not dry_run:
#         print(f"   ❌ Failed: {failed_count}")
        
#         if failed_tasks:
#             print(f"\n🚨 Failed Tasks (for retry):")
#             for task in failed_tasks[:5]:  # Show first 5 failures
#                 print(f"   - {task['name']} (ID: {task['id']})")
#             if len(failed_tasks) > 5:
#                 print(f"   ... and {len(failed_tasks) - 5} more")
    
#     return success_count, failed_count, failed_tasks

# def get_member_tasks_with_date_range(team_id, member_id, days_back=7, max_retries=3):
#     """Get tasks for a member within a date range"""
#     for attempt in range(max_retries):
#         try:
#             # Calculate date range
#             end_date = datetime.now()
#             start_date = end_date - timedelta(days=days_back)
            
#             start_ts = int(start_date.timestamp() * 1000)
#             end_ts = int(end_date.timestamp() * 1000)
            
#             # Get tasks updated within date range
#             url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false&date_updated_gt={start_ts}&date_updated_lt={end_ts}"
#             resp = requests.get(url, headers=HEADERS)
            
#             if resp.status_code == 429:  # Rate limited
#                 wait_time = 60
#                 print(f"    Rate limited. Waiting {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 continue
                
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('tasks', [])
            
#         except requests.exceptions.RequestException as e:
#             print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
#             if attempt < max_retries - 1:
#                 time.sleep(30)
    
#     print("    Failed to fetch tasks after all retries")
#     return []

# def create_enhanced_timeline_visualization(data, save_path="clickup_timeline_enhanced.png"):
#     """Create an enhanced timeline visualization with better interactivity"""
#     fig = plt.figure(figsize=(20, 14))
    
#     # Create grid for different chart sections
#     gs = fig.add_gridspec(4, 2, height_ratios=[3, 1, 1, 1], width_ratios=[3, 1], hspace=0.3, wspace=0.2)
    
#     # Main timeline (top left, spanning 2 columns)
#     ax_timeline = fig.add_subplot(gs[0, :])
    
#     # Status bars (middle left)
#     ax_status = fig.add_subplot(gs[1, 0])
    
#     # Productivity pie (middle right)
#     ax_productivity = fig.add_subplot(gs[1, 1])
    
#     # Hourly activity (bottom left)
#     ax_hourly = fig.add_subplot(gs[2, 0])
    
#     # Statistics panel (bottom right)
#     ax_stats = fig.add_subplot(gs[2, 1])
    
#     # Alert panel (very bottom, spanning both)
#     ax_alerts = fig.add_subplot(gs[3, :])
    
#     # Parse the data
#     detailed_data = data['detailed_data']
#     members = list(detailed_data.keys())
    
#     # Enhanced color scheme
#     colors = {
#         'active': '#28a745',      # Bootstrap success green
#         'downtime': '#dc3545',    # Bootstrap danger red
#         'warning': '#ffc107',     # Bootstrap warning yellow
#         'info': '#17a2b8',        # Bootstrap info blue
#         'no_activity': '#6c757d'  # Bootstrap secondary gray
#     }
    
#     # 1. MAIN TIMELINE
#     ax_timeline.set_title(f"📊 Team Activity Timeline - {data['date']}", 
#                          fontsize=18, fontweight='bold', pad=20)
    
#     y_positions = range(len(members))
#     ax_timeline.set_yticks(y_positions)
#     ax_timeline.set_yticklabels(members, fontsize=12)
    
#     # Parse timestamps
#     current_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
#     start_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
    
#     # Track member status for other charts
#     member_stats = {}
    
#     for i, member in enumerate(members):
#         member_data = detailed_data[member]
#         total_downtime = sum(p['duration_hours'] for p in member_data['downtime_periods'])
#         total_active = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
        
#         member_stats[member] = {
#             'total_downtime': total_downtime,
#             'total_active': total_active,
#             'status': 'critical' if total_downtime >= 4 else 'warning' if total_downtime >= 3 else 'good'
#         }
        
#         # Draw active periods
#         for period in member_data['in_progress_periods']:
#             if isinstance(period['start'], str):
#                 period_start = datetime.fromisoformat(period['start'])
#                 period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
#             else:
#                 period_start = period['start']
#                 period_end = period['end']
            
#             rect = Rectangle((mdates.date2num(period_start), i - 0.35), 
#                            mdates.date2num(period_end) - mdates.date2num(period_start), 0.7,
#                            facecolor=colors['active'], alpha=0.8, edgecolor='darkgreen', linewidth=1)
#             ax_timeline.add_patch(rect)
            
#             # Add task name with better formatting
#             mid_time = period_start + (period_end - period_start) / 2
#             task_name = period['task_name'][:25] + "..." if len(period['task_name']) > 25 else period['task_name']
#             ax_timeline.text(mdates.date2num(mid_time), i, task_name, 
#                            ha='center', va='center', fontsize=9, fontweight='bold', 
#                            color='white', bbox=dict(boxstyle="round,pad=0.2", facecolor='darkgreen', alpha=0.7))
        
#         # Draw downtime periods with different colors based on severity
#         for period in member_data['downtime_periods']:
#             if isinstance(period['start'], str):
#                 period_start = datetime.fromisoformat(period['start'])
#                 period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
#             else:
#                 period_start = period['start']
#                 period_end = period['end']
            
#             # Color based on duration and type
#             duration = period['duration_hours']
#             if duration >= 6:
#                 color = colors['no_activity']  # Very severe
#             elif duration >= 4:
#                 color = colors['downtime']     # Severe  
#             else:
#                 color = colors['warning']      # Moderate
            
#             rect = Rectangle((mdates.date2num(period_start), i - 0.35), 
#                            mdates.date2num(period_end) - mdates.date2num(period_start), 0.7,
#                            facecolor=color, alpha=0.9, edgecolor='darkred', linewidth=1)
#             ax_timeline.add_patch(rect)
            
#             # Add downtime info
#             mid_time = period_start + (period_end - period_start) / 2
#             duration_text = f"🚨 {duration:.1f}h"
#             if period['end'] == current_time:
#                 duration_text += " (NOW)"
            
#             ax_timeline.text(mdates.date2num(mid_time), i, duration_text, 
#                            ha='center', va='center', fontsize=10, fontweight='bold', 
#                            color='white', bbox=dict(boxstyle="round,pad=0.3", facecolor='darkred', alpha=0.8))
    
#     # Format timeline x-axis
#     ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
#     ax_timeline.xaxis.set_major_locator(mdates.HourLocator(interval=1))
#     ax_timeline.set_xlim(mdates.date2num(start_time), mdates.date2num(current_time))
#     ax_timeline.grid(True, alpha=0.3, linestyle='--')
#     ax_timeline.set_xlabel("Time of Day", fontsize=12, fontweight='bold')
    
#     # Enhanced legend
#     legend_elements = [
#         Rectangle((0, 0), 1, 1, facecolor=colors['active'], label='🟢 Active Period'),
#         Rectangle((0, 0), 1, 1, facecolor=colors['warning'], label='🟡 Moderate Downtime (3-4h)'),
#         Rectangle((0, 0), 1, 1, facecolor=colors['downtime'], label='🔴 Severe Downtime (4-6h)'),
#         Rectangle((0, 0), 1, 1, facecolor=colors['no_activity'], label='⚫ Critical Downtime (6+h)')
#     ]
#     ax_timeline.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
#     # 2. STATUS BARS
#     ax_status.set_title("⚡ Current Member Status", fontsize=14, fontweight='bold')
    
#     status_colors = []
#     status_labels = []
#     downtime_values = []
    
#     for member in members:
#         stats = member_stats[member]
#         downtime_values.append(stats['total_downtime'])
        
#         if stats['status'] == 'critical':
#             status_colors.append(colors['no_activity'])
#             status_labels.append(f"{member[:15]} 🆘")
#         elif stats['status'] == 'warning':
#             status_colors.append(colors['downtime'])
#             status_labels.append(f"{member[:15]} ⚠️")
#         else:
#             status_colors.append(colors['active'])
#             status_labels.append(f"{member[:15]} ✅")
    
#     bars = ax_status.barh(range(len(members)), downtime_values, color=status_colors, alpha=0.8, edgecolor='black')
#     ax_status.set_yticks(range(len(members)))
#     ax_status.set_yticklabels(status_labels, fontsize=10)
#     ax_status.set_xlabel("Hours of Downtime", fontsize=11)
#     ax_status.axvline(x=3, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='3h threshold')
#     ax_status.axvline(x=6, color='red', linestyle='--', alpha=0.7, linewidth=2, label='6h critical')
#     ax_status.grid(True, alpha=0.3, axis='x')
#     ax_status.legend(fontsize=9)
    
#     # Add value labels
#     for i, (bar, hours) in enumerate(zip(bars, downtime_values)):
#         if hours > 0:
#             ax_status.text(hours + 0.1, i, f'{hours:.1f}h', va='center', fontweight='bold', fontsize=9)
    
#     # 3. PRODUCTIVITY PIE
#     ax_productivity.set_title("🎯 Team Status", fontsize=14, fontweight='bold')
    
#     good_count = sum(1 for stats in member_stats.values() if stats['status'] == 'good')
#     warning_count = sum(1 for stats in member_stats.values() if stats['status'] == 'warning')
#     critical_count = sum(1 for stats in member_stats.values() if stats['status'] == 'critical')
    
#     sizes = [good_count, warning_count, critical_count]
#     labels = [f'✅ Good\n({good_count})', f'⚠️ Warning\n({warning_count})', f'🆘 Critical\n({critical_count})']
#     colors_pie = [colors['active'], colors['warning'], colors['downtime']]
#     explode = (0.05, 0.1, 0.15)
    
#     # Only show non-zero categories
#     non_zero_sizes = [(size, label, color, exp) for size, label, color, exp in zip(sizes, labels, colors_pie, explode) if size > 0]
    
#     if non_zero_sizes:
#         sizes_nz, labels_nz, colors_nz, explode_nz = zip(*non_zero_sizes)
#         wedges, texts, autotexts = ax_productivity.pie(sizes_nz, labels=labels_nz, colors=colors_nz, 
#                                                       explode=explode_nz, autopct='%1.1f%%', 
#                                                       startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
#     else:
#         ax_productivity.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_productivity.transAxes)
    
#     # 4. HOURLY ACTIVITY HEATMAP
#     ax_hourly.set_title("📈 Hourly Activity Distribution", fontsize=14, fontweight='bold')
    
#     # Create hourly activity matrix
#     hours_range = list(range(9, min(current_time.hour + 1, 19)))  # Cap at 7 PM
#     hourly_matrix = np.zeros((len(members), len(hours_range)))
    
#     for i, member in enumerate(members):
#         member_data = detailed_data[member]
        
#         for period in member_data['in_progress_periods']:
#             if isinstance(period['start'], str):
#                 start_time_period = datetime.fromisoformat(period['start'])
#                 end_time_period = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
#             else:
#                 start_time_period = period['start']
#                 end_time_period = period['end']
            
#             for j, hour in enumerate(hours_range):
#                 hour_start = start_time_period.replace(hour=hour, minute=0, second=0, microsecond=0)
#                 hour_end = hour_start + timedelta(hours=1)
                
#                 # Calculate overlap
#                 overlap_start = max(start_time_period, hour_start)
#                 overlap_end = min(end_time_period, hour_end)
                
#                 if overlap_start < overlap_end:
#                     overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
#                     hourly_matrix[i, j] = overlap_minutes / 60  # Convert to fraction of hour
    
#     im = ax_hourly.imshow(hourly_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
#     ax_hourly.set_yticks(range(len(members)))
#     ax_hourly.set_yticklabels([m[:12] + "..." if len(m) > 12 else m for m in members], fontsize=9)
#     ax_hourly.set_xticks(range(len(hours_range)))
#     ax_hourly.set_xticklabels([f"{h:02d}:00" for h in hours_range], fontsize=9, rotation=45)
#     ax_hourly.set_xlabel("Hour of Day", fontsize=11)
    
#     # Add colorbar
#     cbar = plt.colorbar(im, ax=ax_hourly, shrink=0.8)
#     cbar.set_label('Activity Level', rotation=270, labelpad=15, fontsize=10)
    
#     # 5. STATISTICS PANEL
#     ax_stats.axis('off')
    
#     # Calculate key statistics
#     total_team_downtime = sum(stats['total_downtime'] for stats in member_stats.values())
#     total_team_active = sum(stats['total_active'] for stats in member_stats.values())
#     avg_downtime = total_team_downtime / len(members) if members else 0
    
#     currently_inactive = []
#     for member, member_data in detailed_data.items():
#         for period in member_data['downtime_periods']:
#             if isinstance(period['end'], str):
#                 period_end = datetime.fromisoformat(period['end'])
#             else:
#                 period_end = period['end']
            
#             if abs((period_end - current_time).total_seconds()) < 300:  # Within 5 minutes
#                 currently_inactive.append(member)
    
#     stats_text = f"""
# 📊 TEAM STATISTICS
# ━━━━━━━━━━━━━━━━━━━━
# 👥 Total Members: {len(members)}
# ✅ Active Status: {good_count}
# ⚠️  Warning Status: {warning_count}  
# 🆘 Critical Status: {critical_count}

# ⏱️  TIMING ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━
# 🕒 Current Time: {current_time.strftime('%H:%M')}
# 📅 Analysis Date: {data['date']}
# ⚡ Total Team Active: {total_team_active:.1f}h
# 🔻 Total Team Downtime: {total_team_downtime:.1f}h
# 📈 Avg Downtime/Person: {avg_downtime:.1f}h

# 🚨 ALERTS
# ━━━━━━━━━━━━━━━━━━━━
# 🔥 Currently Inactive: {len(currently_inactive)}
# """
    
#     if currently_inactive:
#         stats_text += f"\n   • {', '.join(currently_inactive[:3])}"
#         if len(currently_inactive) > 3:
#             stats_text += f"\n   • +{len(currently_inactive) - 3} more..."
    
#     ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes, fontsize=10, 
#                  verticalalignment='top', fontfamily='monospace',
#                  bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9))
    
#     # 6. ALERTS PANEL
#     ax_alerts.axis('off')
#     ax_alerts.set_title("🚨 PRIORITY ALERTS", fontsize=16, fontweight='bold', color='red', pad=10)
    
#     alerts = []
    
#     # Generate alerts based on analysis
#     if critical_count > 0:
#         critical_members = [m for m, s in member_stats.items() if s['status'] == 'critical']
#         alerts.append(f"🆘 CRITICAL: {critical_count} member(s) with 4+ hours downtime: {', '.join(critical_members)}")
    
#     if currently_inactive:
#         alerts.append(f"🔥 IMMEDIATE: {len(currently_inactive)} member(s) currently inactive: {', '.join(currently_inactive)}")
    
#     if warning_count > len(members) * 0.5:
#         alerts.append(f"⚠️  TEAM ISSUE: Over 50% of team has significant downtime")
    
#     if avg_downtime > 4:
#         alerts.append(f"📉 PRODUCTIVITY: Team average downtime is {avg_downtime:.1f} hours")
    
#     if not alerts:
#         alerts.append("✅ ALL CLEAR: No critical issues detected")
    
#     alert_text = "\n".join(f"• {alert}" for alert in alerts[:4])  # Show top 4 alerts
    
#     ax_alerts.text(0.05, 0.5, alert_text, transform=ax_alerts.transAxes, fontsize=12, 
#                   verticalalignment='center', fontweight='bold',
#                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9, edgecolor='red'))
    
#     plt.suptitle(f"🎯 ClickUp Team Performance Dashboard - {data['date']}", 
#                 fontsize=20, fontweight='bold', y=0.98)
    
#     plt.tight_layout()
#     plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
#     print(f"📊 Enhanced timeline visualization saved to: {save_path}")
    
#     return fig

# def create_watcher_management_report(watcher_results, save_path="watcher_report.json"):
#     """Create a detailed report of watcher management results"""
#     report = {
#         'timestamp': datetime.now().isoformat(),
#         'watcher_operations': watcher_results,
#         'summary': {
#             'total_attempts': watcher_results.get('total_attempts', 0),
#             'successful': watcher_results.get('successful', 0),
#             'failed': watcher_results.get('failed', 0),
#             'success_rate': 0
#         }
#     }
    
#     if report['summary']['total_attempts'] > 0:
#         report['summary']['success_rate'] = (report['summary']['successful'] / 
#                                            report['summary']['total_attempts']) * 100
    
#     try:
#         with open(save_path, 'w') as f:
#             json.dump(report, f, indent=2, default=str)
#         print(f"📄 Watcher management report saved to: {save_path}")
#     except Exception as e:
#         print(f"⚠️ Could not save watcher report: {e}")
    
#     return report

# def retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name):
#     """Retry adding watchers to previously failed tasks with enhanced debugging"""
#     if not failed_tasks:
#         print("✅ No failed tasks to retry")
#         return
    
#     print(f"\n🔄 Retrying {len(failed_tasks)} failed watcher additions...")
#     print("🔍 Using enhanced debug mode for all retries...")
    
#     retry_success = 0
#     still_failed = []
    
#     for i, task in enumerate(failed_tasks, 1):
#         task_id = task['id']
#         task_name = task['name']
        
#         print(f"\n   [RETRY {i}/{len(failed_tasks)}] {task_name}")
        
#         # Use full debug mode for retries
#         result = debug_watcher_api(task_id, watcher_user_id, watcher_name)
        
#         if result:
#             retry_success += 1
#             print(f"      ✅ Retry successful!")
#         else:
#             still_failed.append(task)
#             print(f"      ❌ Still failed after retry")
        
#         # Longer delay for retries
#         time.sleep(3)
    
#     print(f"\n📊 Retry Results:")
#     print(f"   🔄 Retried: {len(failed_tasks)}")
#     print(f"   ✅ Now successful: {retry_success}")
#     print(f"   ❌ Still failing: {len(still_failed)}")
    
#     if still_failed:
#         print(f"\n🚨 Tasks that still fail after retry:")
#         for task in still_failed[:3]:
#             print(f"   - {task['name']} (ID: {task['id']})")
#         if len(still_failed) > 3:
#             print(f"   ... and {len(still_failed) - 3} more")
    
#     return retry_success, still_failed

# def load_and_visualize_data(json_file_path):
#     """Load JSON data and create enhanced visualizations"""
#     try:
#         with open(json_file_path, 'r') as f:
#             data = json.load(f)
        
#         print(f"📊 Creating enhanced visualizations for {data['date']}...")
#         print(f"   Members analyzed: {data['members_analyzed']}")
#         print(f"   Members with downtime: {data['members_with_downtime']}")
        
#         # Create enhanced timeline visualization
#         timeline_fig = create_enhanced_timeline_visualization(data)
        
#         # Create additional analysis if needed
#         analysis_fig = create_detailed_analysis_charts(data)
        
#         # Show plots
#         plt.show()
        
#         return timeline_fig, analysis_fig
        
#     except FileNotFoundError:
#         print(f"❌ Could not find file: {json_file_path}")
#         return None, None
#     except Exception as e:
#         print(f"❌ Error creating visualizations: {e}")
#         return None, None

# def create_detailed_analysis_charts(data, save_path="clickup_detailed_analysis.png"):
#     """Create comprehensive detailed analysis charts"""
#     fig, axes = plt.subplots(2, 3, figsize=(24, 16))
#     fig.suptitle(f'📈 Detailed Team Analysis - {data["date"]}', fontsize=18, fontweight='bold')
    
#     detailed_data = data['detailed_data']
#     members = list(detailed_data.keys())
    
#     # 1. Active vs Downtime Comparison (Top Left)
#     ax1 = axes[0, 0]
#     ax1.set_title("⚡ Active vs Downtime Hours", fontsize=14, fontweight='bold')
    
#     active_hours = []
#     downtime_hours = []
    
#     for member in members:
#         member_data = detailed_data[member]
#         active_time = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
#         downtime_time = sum(p['duration_hours'] for p in member_data['downtime_periods'])
        
#         active_hours.append(active_time)
#         downtime_hours.append(downtime_time)
    
#     x = np.arange(len(members))
#     width = 0.35
    
#     bars1 = ax1.bar(x - width/2, active_hours, width, label='✅ Active Hours', 
#                    color='#28a745', alpha=0.8, edgecolor='darkgreen')
#     bars2 = ax1.bar(x + width/2, downtime_hours, width, label='🔴 Downtime Hours', 
#                    color='#dc3545', alpha=0.8, edgecolor='darkred')
    
#     ax1.set_xlabel('Team Members', fontweight='bold')
#     ax1.set_ylabel('Hours', fontweight='bold')
#     ax1.set_xticks(x)
#     ax1.set_xticklabels([m[:8] + "..." if len(m) > 8 else m for m in members], rotation=45, ha='right')
#     ax1.legend()
#     ax1.grid(True, alpha=0.3, axis='y')
    
#     # Add value labels
#     for bars in [bars1, bars2]:
#         for bar in bars:
#             height = bar.get_height()
#             if height > 0:
#                 ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05, f'{height:.1f}h',
#                         ha='center', va='bottom', fontsize=9, fontweight='bold')
    
#     # 2. Downtime Categories Breakdown (Top Middle)
#     ax2 = axes[0, 1]
#     ax2.set_title("📊 Downtime Categories", fontsize=14, fontweight='bold')
    
#     downtime_types = {}
#     for member_data in detailed_data.values():
#         for period in member_data['downtime_periods']:
#             period_type = period['type']
#             if period_type not in downtime_types:
#                 downtime_types[period_type] = 0
#             downtime_types[period_type] += period['duration_hours']
    
#     if downtime_types:
#         readable_labels = {
#             'no_activity_all_day': 'No Activity All Day',
#             'no_tasks': 'No Tasks Assigned',
#             'late_start': 'Late Start',
#             'midday_gap': 'Midday Gap',
#             'current_inactive': 'Currently Inactive'
#         }
        
#         labels = [readable_labels.get(t, t.replace('_', ' ').title()) for t in downtime_types.keys()]
#         values = list(downtime_types.values())
        
#         colors_donut = plt.cm.Set3(np.linspace(0, 1, len(labels)))
#         wedges, texts, autotexts = ax2.pie(values, labels=labels, autopct='%1.1f%%',
#                                           colors=colors_donut, startangle=90)
        
#         for autotext in autotexts:
#             autotext.set_fontweight('bold')
#             autotext.set_fontsize(10)
#     else:
#         ax2.text(0.5, 0.5, '🎉 No Downtime\nDetected!', ha='center', va='center', 
#                 transform=ax2.transAxes, fontsize=16, fontweight='bold', color='green')
    
#     # 3. Member Productivity Ranking (Top Right)  
#     ax3 = axes[0, 2]
#     ax3.set_title("🏆 Productivity Ranking", fontsize=14, fontweight='bold')
    
#     productivity_scores = []
#     for member in members:
#         member_data = detailed_data[member]
#         total_active = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
#         total_downtime = sum(p['duration_hours'] for p in member_data['downtime_periods'])
        
#         if total_active + total_downtime > 0:
#             productivity = (total_active / (total_active + total_downtime)) * 100
#         else:
#             productivity = 100 if total_active > 0 else 0
            
#         productivity_scores.append(productivity)
    
#     # Sort by productivity
#     sorted_data = sorted(zip(members, productivity_scores), key=lambda x: x[1], reverse=True)
#     sorted_members, sorted_scores = zip(*sorted_data)
    
#     # Color bars based on score
#     colors = ['#28a745' if score >= 80 else '#ffc107' if score >= 60 else '#dc3545' 
#               for score in sorted_scores]
    
#     bars = ax3.barh(range(len(sorted_members)), sorted_scores, color=colors, alpha=0.8, edgecolor='black')
#     ax3.set_yticks(range(len(sorted_members)))
#     ax3.set_yticklabels([m[:12] + "..." if len(m) > 12 else m for m in sorted_members])
#     ax3.set_xlabel('Productivity Score (%)', fontweight='bold')
#     ax3.set_xlim(0, 100)
#     ax3.grid(True, alpha=0.3, axis='x')
    
#     # Add score labels
#     for i, (bar, score) in enumerate(zip(bars, sorted_scores)):
#         ax3.text(score + 1, i, f'{score:.0f}%', va='center', fontweight='bold')
    
#     # 4. Timeline Heatmap (Bottom Left)
#     ax4 = axes[1, 0]
#     ax4.set_title("🕒 Activity Timeline Heatmap", fontsize=14, fontweight='bold')
    
#     # Create 15-minute interval heatmap
#     current_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
#     start_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
    
#     # 15-minute intervals from 9 AM to current time
#     intervals = []
#     current_interval = start_time
#     while current_interval <= current_time:
#         intervals.append(current_interval)
#         current_interval += timedelta(minutes=15)
    
#     heatmap_data = np.zeros((len(members), len(intervals)))
    
#     for i, member in enumerate(members):
#         member_data = detailed_data[member]
        
#         for period in member_data['in_progress_periods']:
#             if isinstance(period['start'], str):
#                 period_start = datetime.fromisoformat(period['start'])
#                 period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
#             else:
#                 period_start = period['start']
#                 period_end = period['end']
            
#             for j, interval_start in enumerate(intervals):
#                 interval_end = interval_start + timedelta(minutes=15)
                
#                 # Check overlap
#                 if period_start < interval_end and period_end > interval_start:
#                     heatmap_data[i, j] = 1
    
#     im = ax4.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', interpolation='nearest')
#     ax4.set_yticks(range(len(members)))
#     ax4.set_yticklabels([m[:10] + "..." if len(m) > 10 else m for m in members], fontsize=9)
    
#     # Show every hour on x-axis
#     hour_indices = [i for i, interval in enumerate(intervals) if interval.minute == 0]
#     ax4.set_xticks(hour_indices)
#     ax4.set_xticklabels([intervals[i].strftime('%H:%M') for i in hour_indices], rotation=45)
#     ax4.set_xlabel('Time (15-min intervals)', fontweight='bold')
    
#     # 5. Trend Analysis (Bottom Middle)
#     ax5 = axes[1, 1]
#     ax5.set_title("📈 Hourly Activity Trend", fontsize=14, fontweight='bold')
    
#     # Calculate hourly activity levels
#     hours = list(range(9, min(current_time.hour + 1, 19)))
#     active_counts = []
    
#     for hour in hours:
#         active_in_hour = 0
#         for member_data in detailed_data.values():
#             for period in member_data['in_progress_periods']:
#                 if isinstance(period['start'], str):
#                     period_start = datetime.fromisoformat(period['start'])
#                     period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
#                 else:
#                     period_start = period['start']
#                     period_end = period['end']
                
#                 hour_start = period_start.replace(hour=hour, minute=0, second=0, microsecond=0)
#                 hour_end = hour_start + timedelta(hours=1)
                
#                 if period_start < hour_end and period_end > hour_start:
#                     active_in_hour += 1
        
#         active_counts.append(active_in_hour)
    
#     ax5.plot(hours, active_counts, marker='o', linewidth=3, markersize=8, color='#17a2b8')
#     ax5.fill_between(hours, active_counts, alpha=0.3, color='#17a2b8')
#     ax5.set_xlabel('Hour of Day', fontweight='bold')
#     ax5.set_ylabel('Active Members', fontweight='bold')
#     ax5.set_xticks(hours)
#     ax5.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
#     ax5.grid(True, alpha=0.3)
#     ax5.set_ylim(0, len(members) + 1)
    
#     # Add trend line
#     if len(hours) > 1:
#         z = np.polyfit(hours, active_counts, 1)
#         p = np.poly1d(z)
#         ax5.plot(hours, p(hours), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend (slope: {z[0]:.2f})')
#         ax5.legend()
    
#     # 6. Summary Statistics (Bottom Right)
#     ax6 = axes[1, 2]
#     ax6.axis('off')
#     ax6.set_title("📋 Key Metrics", fontsize=14, fontweight='bold')
    
#     # Calculate comprehensive statistics
#     total_members = len(members)
#     members_with_downtime = sum(1 for member_data in detailed_data.values() 
#                                if member_data['downtime_periods'])
    
#     total_active_hours = sum(sum(p['duration_hours'] for p in member_data['in_progress_periods'])
#                             for member_data in detailed_data.values())
#     total_downtime_hours = sum(sum(p['duration_hours'] for p in member_data['downtime_periods'])
#                               for member_data in detailed_data.values())
    
#     avg_active = total_active_hours / total_members if total_members > 0 else 0
#     avg_downtime = total_downtime_hours / total_members if total_members > 0 else 0
    
#     # Find most/least productive
#     if productivity_scores:
#         most_productive = sorted_data[0]
#         least_productive = sorted_data[-1]
#     else:
#         most_productive = ("N/A", 0)
#         least_productive = ("N/A", 0)
    
#     # Current status
#     currently_inactive = sum(1 for member_data in detailed_data.values()
#                            for period in member_data['downtime_periods']
#                            if abs((datetime.fromisoformat(period['end']) if isinstance(period['end'], str) 
#                                   else period['end'] - current_time).total_seconds()) < 300)
    
#     stats_text = f"""
# KEY PERFORMANCE METRICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━

# 👥 TEAM OVERVIEW
#    Total Members: {total_members}
#    With Downtime: {members_with_downtime}
#    Currently Inactive: {currently_inactive}

# ⏱️ TIME ANALYSIS  
#    Total Active Hours: {total_active_hours:.1f}h
#    Total Downtime: {total_downtime_hours:.1f}h
#    Avg Active/Person: {avg_active:.1f}h
#    Avg Downtime/Person: {avg_downtime:.1f}h

# 🏆 PERFORMANCE LEADERS
#    Most Productive: 
#    {most_productive[0][:15]} ({most_productive[1]:.0f}%)
   
#    Needs Attention:
#    {least_productive[0][:15]} ({least_productive[1]:.0f}%)

# 📊 EFFICIENCY METRICS
#    Team Efficiency: {(total_active_hours/(total_active_hours + total_downtime_hours)*100) if (total_active_hours + total_downtime_hours) > 0 else 0:.1f}%
#    Active Members: {total_members - members_with_downtime}/{total_members}
   
# ⚠️ ALERTS
#    Critical Issues: {sum(1 for member_data in detailed_data.values() if sum(p['duration_hours'] for p in member_data['downtime_periods']) >= 4)}
#    """
    
#     ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, fontsize=11, 
#              verticalalignment='top', fontfamily='monospace',
#              bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
#     plt.tight_layout()
#     plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
#     print(f"📊 Detailed analysis charts saved to: {save_path}")
    
#     return fig

# def main():
#     """Enhanced main function with better error handling and user experience"""
#     print("🚀 ClickUp Enhanced Downtime Analysis & Watcher Management")
#     print("=" * 70)
    
#     # Get team info with error handling
#     try:
#         print("🔗 Connecting to ClickUp API...")
#         team_id = get_team_id()
#         members = get_team_members(team_id)
#         print(f"✅ Connected successfully!")
#         print(f"🏢 Team ID: {team_id}")
#         print(f"👥 Team members: {len(members)}")
        
#         # Show team members
#         print(f"\n👥 Team Members:")
#         for i, member in enumerate(members, 1):
#             user = member.get('user', {})
#             username = user.get('username', 'N/A')
#             email = user.get('email', 'N/A')
#             print(f"   {i:2d}. {username} ({email})")
            
#     except Exception as e:
#         print(f"❌ Error connecting to ClickUp: {e}")
#         print("🔧 Please check your API token and try again.")
#         return
    
#     # Enhanced interactive menu
#     print(f"\n🔧 What would you like to do?")
#     print("1. 📊 Analyze member downtime only")
#     print("2. 👁️  Add Sean as watcher to all recent tasks")
#     print("3. 🎯 Add custom person as watcher to tasks")
#     print("4. 🚀 Both downtime analysis and add watchers")
#     print("5. 📈 Create visualizations from existing JSON file")
#     print("6. 🔄 Retry failed watcher operations")
    
#     choice = input("\nEnter your choice (1-6): ").strip()
    
#     if choice not in ['1', '2', '3', '4', '5', '6']:
#         print("❌ Invalid choice. Please run again and select 1-6.")
#         return
    
#     # Handle visualization from existing file
#     if choice == '5':
#         json_file = input("Enter the path to your JSON file: ").strip()
#         if not json_file:
#             # Look for recent files
#             import glob
#             json_files = glob.glob("clickup_downtime_*.json")
#             if json_files:
#                 latest_file = max(json_files, key=lambda x: x.split('_')[-1])
#                 print(f"🔍 Found recent file: {latest_file}")
#                 use_latest = input("Use this file? (y/n, default: y): ").strip().lower()
#                 if use_latest != 'n':
#                     json_file = latest_file
            
#             if not json_file:
#                 print("❌ No JSON file specified or found.")
#                 return
        
#         load_and_visualize_data(json_file)
#         return
    
#     # Handle retry operations
#     if choice == '6':
#         # Load previous failed operations
#         try:
#             with open('failed_watcher_operations.json', 'r') as f:
#                 failed_data = json.load(f)
#             failed_tasks = failed_data.get('failed_tasks', [])
#             watcher_info = failed_data.get('watcher_info', {})
            
#             if not failed_tasks:
#                 print("✅ No failed operations found to retry.")
#                 return
            
#             print(f"🔄 Found {len(failed_tasks)} failed watcher operations")
#             watcher_user_id = watcher_info.get('user_id')
#             watcher_name = watcher_info.get('name', 'Unknown')
            
#             retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name)
            
#         except FileNotFoundError:
#             print("❌ No previous failed operations found.")
#         except Exception as e:
#             print(f"❌ Error loading failed operations: {e}")
#         return
    
#     # Handle watcher functionality (choices 2, 3, 4)
#     watcher_results = {}
#     if choice in ['2', '3', '4']:
#         print(f"\n👁️ WATCHER MANAGEMENT")
#         print("=" * 30)
        
#         # Get date range for tasks
#         days_back_input = input("How many days back to look for tasks? (default: 7): ").strip()
#         try:
#             days_back = int(days_back_input) if days_back_input else 7
#         except ValueError:
#             days_back = 7
        
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=days_back)
#         print(f"📅 Working with period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
#         # Find watcher user
#         if choice == '2':
#             watcher_name = 'sean'
#         else:
#             watcher_name = input("Enter the name/username of person to add as watcher: ").strip()
        
#         watcher_user = find_user_by_name(members, watcher_name)
#         if not watcher_user:
#             print(f"❌ Could not find user '{watcher_name}' in the team")
#             print("Available users:")
#             for member in members:
#                 user = member.get('user', {})
#                 print(f"   - {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
#             return
        
#         watcher_user_id = watcher_user['id']
#         watcher_username = watcher_user['username']
#         print(f"👁️ Found watcher: {watcher_username} (ID: {watcher_user_id})")
        
#         # Enhanced configuration options
#         print(f"\n🔧 CONFIGURATION OPTIONS")
#         debug_mode_input = input("Enable debug mode for comprehensive API testing? (y/n, default: n): ").strip().lower()
#         debug_mode = debug_mode_input == 'y'
        
#         dry_run_input = input("Do a dry run first (recommended)? (y/n, default: y): ").strip().lower()
#         dry_run = dry_run_input != 'n'
        
#         batch_size_input = input("Process in batches? Enter batch size (default: all at once): ").strip()
#         batch_size = int(batch_size_input) if batch_size_input.isdigit() else None
        
#         # Collect all tasks from all members
#         all_tasks = []
#         print(f"\n📋 Collecting tasks from all team members...")
        
#         for i, member in enumerate(members):
#             user_id = member['user']['id']
#             user_name = member['user']['username']
#             print(f"   [{i+1:2d}/{len(members)}] Getting tasks for {user_name}...")
            
#             try:
#                 tasks = get_member_tasks_with_date_range(team_id, user_id, days_back)
#                 all_tasks.extend(tasks)
#                 print(f"      📋 Found {len(tasks)} tasks")
#             except Exception as e:
#                 print(f"      ❌ Error getting tasks: {e}")
            
#             if i < len(members) - 1:
#                 time.sleep(2)  # Rate limiting
        
#         # Remove duplicates
#         unique_tasks = {}
#         for task in all_tasks:
#             unique_tasks[task['id']] = task
        
#         unique_task_list = list(unique_tasks.values())
#         print(f"📊 Found {len(unique_task_list)} unique tasks across all members")
        
#         if len(unique_task_list) == 0:
#             print("❌ No tasks found to add watchers to")
#         else:
#             # Process tasks
#             if batch_size and len(unique_task_list) > batch_size:
#                 print(f"🔄 Processing in batches of {batch_size}...")
                
#                 all_success = 0
#                 all_failed = 0 
#                 all_failed_tasks = []
                
#                 for batch_start in range(0, len(unique_task_list), batch_size):
#                     batch_end = min(batch_start + batch_size, len(unique_task_list))
#                     batch_tasks = unique_task_list[batch_start:batch_end]
                    
#                     print(f"\n📦 Processing batch {batch_start//batch_size + 1}: tasks {batch_start+1}-{batch_end}")
#                     success, failed, failed_tasks = add_watcher_to_all_tasks(
#                         batch_tasks, watcher_user_id, watcher_username, dry_run, debug_mode)
                    
#                     all_success += success
#                     all_failed += failed
#                     all_failed_tasks.extend(failed_tasks)
                    
#                     if batch_end < len(unique_task_list):
#                         print("⏳ Pausing between batches...")
#                         time.sleep(5)
                
#                 success_count, failed_count, failed_tasks = all_success, all_failed, all_failed_tasks
#             else:
#                 success_count, failed_count, failed_tasks = add_watcher_to_all_tasks(
#                     unique_task_list, watcher_user_id, watcher_username, dry_run, debug_mode)
            
#             # Handle dry run confirmation
#             if dry_run and success_count > 0:
#                 confirm = input(f"\n🤔 Proceed with actually adding {watcher_username} to {len(unique_task_list)} tasks? (y/n): ").strip().lower()
#                 if confirm == 'y':
#                     print(f"\n🚀 Proceeding with actual watcher addition...")
#                     success_count, failed_count, failed_tasks = add_watcher_to_all_tasks(
#                         unique_task_list, watcher_user_id, watcher_username, dry_run=False, debug_mode=debug_mode)
            
#             # Store results and save failed tasks for retry
#             watcher_results = {
#                 'watcher_name': watcher_username,
#                 'watcher_user_id': watcher_user_id,
#                 'total_attempts': len(unique_task_list),
#                 'successful': success_count,
#                 'failed': failed_count,
#                 'failed_tasks': failed_tasks
#             }
            
#             if failed_tasks:
#                 # Save failed tasks for potential retry
#                 failed_data = {
#                     'failed_tasks': failed_tasks,
#                     'watcher_info': {
#                         'user_id': watcher_user_id,
#                         'name': watcher_username
#                     },
#                     'timestamp': datetime.now().isoformat()
#                 }
                
#                 try:
#                     with open('failed_watcher_operations.json', 'w') as f:
#                         json.dump(failed_data, f, indent=2, default=str)
#                     print(f"💾 Failed operations saved for retry (use option 6)")
#                 except Exception as e:
#                     print(f"⚠️ Could not save failed operations: {e}")
                
#                 # Ask if user wants to retry immediately
#                 if failed_count > 0:
#                     retry_now = input(f"\n🔄 Retry {failed_count} failed operations now? (y/n): ").strip().lower()
#                     if retry_now == 'y':
#                         retry_success, still_failed = retry_failed_watchers(failed_tasks, watcher_user_id, watcher_username)
#                         watcher_results['retry_successful'] = retry_success
#                         watcher_results['still_failed'] = len(still_failed)
    
#     # Handle downtime analysis (choices 1, 4)
#     if choice in ['1', '4']:
#         print(f"\n📊 DOWNTIME ANALYSIS")
#         print("=" * 25)
#         print(f"Starting TODAY's comprehensive downtime analysis...")
        
#         # Get today's timestamps
#         start_ts, current_ts, today_start, current_time = get_today_timestamps()
#         print(f"📅 Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
#         print(f"⏰ Current time: {current_time.strftime('%H:%M:%S')}")
#         print(f"🕘 Work day assumption: 9:00 AM - now")
        
#         members_with_downtime = []
#         all_member_data = {}
        
#         # Analyze each team member with progress tracking
#         print(f"\n🔍 Analyzing {len(members)} team members...")
        
#         for i, member in enumerate(members):
#             user_id = member['user']['id']
#             user_name = member['user']['username']
            
#             print(f"\n{'=' * 60}")
#             print(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
#             print('=' * 60)
            
#             try:
#                 # Get member's tasks
#                 print("  📋 Fetching tasks...")
#                 tasks = get_member_tasks(team_id, user_id)
#                 print(f"  ✅ Found {len(tasks)} open tasks")
                
#                 if not tasks:
#                     # No tasks = full downtime if it's been 3+ hours since work started
#                     workday_start = today_start.replace(hour=9)
#                     if current_time > workday_start:
#                         hours_since_work = (current_time - workday_start).total_seconds() / 3600
#                         if hours_since_work >= 3:
#                             downtime_periods = [{
#                                 'start': workday_start,
#                                 'end': current_time,
#                                 'duration_hours': hours_since_work,
#                                 'type': 'no_tasks'
#                             }]
#                             members_with_downtime.append(user_name)
#                             all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': downtime_periods}
#                             print(f"  🔴 NO TASKS ASSIGNED: {hours_since_work:.1f} hours of downtime")
#                         else:
#                             all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#                             print(f"  ✅ No tasks but within acceptable range")
#                     else:
#                         all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
#                         print(f"  ✅ Work day hasn't started yet")
#                 else:
#                     # Analyze task activity
#                     print("  🔍 Analyzing task activity patterns...")
#                     in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
#                     print(f"  📊 Found {len(in_progress_periods)} active periods today")
                    
#                     # Calculate downtime
#                     print("  ⏱️  Calculating downtime periods...")
#                     downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
#                     all_member_data[user_name] = {
#                         'in_progress_periods': in_progress_periods,
#                         'downtime_periods': downtime_periods
#                     }
                    
#                     if downtime_periods:
#                         members_with_downtime.append(user_name)
#                         total_downtime = sum(p['duration_hours'] for p in downtime_periods)
#                         print(f"  🔴 DOWNTIME DETECTED: {total_downtime:.1f} total hours")
                        
#                         # Show breakdown
#                         for j, period in enumerate(downtime_periods, 1):
#                             start_time_str = period['start'].strftime('%H:%M')
#                             end_time_str = period['end'].strftime('%H:%M') if period['end'] != current_time else "NOW"
#                             print(f"    {j}. {start_time_str} - {end_time_str} ({period['duration_hours']:.1f}h) [{period['type']}]")
#                     else:
#                         print(f"  ✅ No significant downtime detected (active day)")
                        
#             except Exception as e:
#                 print(f"  ❌ Error analyzing {user_name}: {e}")
#                 all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
            
#             # Progress indicator
#             progress = ((i + 1) / len(members)) * 100
#             print(f"  📈 Progress: {progress:.0f}% complete")
            
#             # Rate limiting between members
#             if i < len(members) - 1:
#                 print("  ⏱️ Rate limiting pause...")
#                 time.sleep(3)
        
#         # Generate comprehensive final summary
#         print(f"\n{'='*70}")
#         print(f"📊 COMPREHENSIVE DOWNTIME SUMMARY")
#         print(f"📅 {current_time.strftime('%A, %B %d, %Y')} at {current_time.strftime('%H:%M')}")
#         print('='*70)
        
#         if not members_with_downtime:
#             print("🎉 EXCELLENT! ALL TEAM MEMBERS ARE ACTIVE!")
#             print("   ✅ No one has 3+ hours of downtime today.")
#             print("   🏆 Team is performing at optimal productivity levels.")
#         else:
#             print(f"🚨 ATTENTION REQUIRED: {len(members_with_downtime)} MEMBER(S) WITH SIGNIFICANT DOWNTIME")
            
#             # Categorize by severity
#             critical_members = []  # 6+ hours
#             severe_members = []    # 4-6 hours  
#             moderate_members = []  # 3-4 hours
            
#             for member_name in members_with_downtime:
#                 data = all_member_data[member_name]
#                 total_downtime = sum(p['duration_hours'] for p in data['downtime_periods'])
                
#                 if total_downtime >= 6:
#                     critical_members.append((member_name, total_downtime))
#                 elif total_downtime >= 4:
#                     severe_members.append((member_name, total_downtime))
#                 else:
#                     moderate_members.append((member_name, total_downtime))
            
#             # Display by severity
#             if critical_members:
#                 print(f"\n🆘 CRITICAL (6+ hours downtime): {len(critical_members)} members")
#                 for member, hours in critical_members:
#                     print(f"   💀 {member}: {hours:.1f} hours - IMMEDIATE ACTION REQUIRED")
            
#             if severe_members:
#                 print(f"\n🔴 SEVERE (4-6 hours downtime): {len(severe_members)} members")
#                 for member, hours in severe_members:
#                     print(f"   ⚠️  {member}: {hours:.1f} hours - ACTION NEEDED")
            
#             if moderate_members:
#                 print(f"\n MODERATE (3-4 hours downtime): {len(moderate_members)} members")
#                 for member, hours in moderate_members:
#                     print(f"    {member}: {hours:.1f} hours - MONITOR")
            
#             # Show currently inactive members
#             currently_inactive = []
#             for member_name, data in all_member_data.items():
#                 for period in data['downtime_periods']:
#                     if abs((period['end'] - current_time).total_seconds()) < 300:  # Within 5 minutes of now
#                         currently_inactive.append(member_name)
#                         break
            
#             if currently_inactive:
#                 print(f"\n CURRENTLY INACTIVE ({len(currently_inactive)} members):")
#                 for member in currently_inactive:
#                     data = all_member_data[member]
#                     current_period = None
#                     for period in data['downtime_periods']:
#                         if abs((period['end'] - current_time).total_seconds()) < 300:
#                             current_period = period
#                             break
                    
#                     if current_period:
#                         inactive_duration = (current_time - current_period['start']).total_seconds() / 3600
#                         print(f"    {member}: inactive for {inactive_duration:.1f} hours (since {current_period['start'].strftime('%H:%M')})")
        
#         # Final comprehensive statistics
#         print(f"\n TEAM PERFORMANCE METRICS:")
#         print(f"    Analysis time: {current_time.strftime('%H:%M')}")
#         print(f"    Total members: {len(members)}")
#         print(f"   Fully active members: {len(members) - len(members_with_downtime)}")
#         print(f"    Members with downtime: {len(members_with_downtime)}")
        
#         if currently_inactive:
#             print(f"   Currently inactive: {len(currently_inactive)}")
        
#         # Calculate team efficiency
#         total_active_time = sum(sum(p['duration_hours'] for p in data['in_progress_periods']) 
#                                for data in all_member_data.values())
#         total_downtime_time = sum(sum(p['duration_hours'] for p in data['downtime_periods']) 
#                                  for data in all_member_data.values())
        
#         if total_active_time + total_downtime_time > 0:
#             team_efficiency = (total_active_time / (total_active_time + total_downtime_time)) * 100
#             print(f"   Team efficiency: {team_efficiency:.1f}%")
        
#         print(f"     Total active hours: {total_active_time:.1f}h")
#         print(f"     Total downtime: {total_downtime_time:.1f}h")
        
#         if members_with_downtime:
#             avg_downtime = total_downtime_time / len(members_with_downtime)
#             print(f"    Avg downtime per affected member: {avg_downtime:.1f}h")
        
#         # Save comprehensive results
#         results = {
#             'timestamp': current_time.isoformat(),
#             'date': current_time.strftime('%Y-%m-%d'),
#             'analysis_time': current_time.strftime('%H:%M:%S'),
#             'members_analyzed': len(members),
#             'members_with_downtime': len(members_with_downtime),
#             'downtime_members': members_with_downtime,
#             'detailed_data': all_member_data,
#             'team_metrics': {
#                 'total_active_hours': total_active_time,
#                 'total_downtime_hours': total_downtime_time,
#                 'team_efficiency': team_efficiency if 'team_efficiency' in locals() else 0,
#                 'currently_inactive': currently_inactive if 'currently_inactive' in locals() else []
#             }
#         }
        
#         # Add watcher results if available
#         if watcher_results:
#             results['watcher_management'] = watcher_results
        
#         filename = f"clickup_downtime_{current_time.strftime('%Y%m%d_%H%M')}.json"
#         try:
#             with open(filename, 'w') as f:
#                 json.dump(results, f, indent=2, default=str)
#             print(f"\n Comprehensive results saved to: {filename}")
            
#             # Ask about visualizations
#             create_viz = input(f"\n Create enhanced visualizations now? (y/n, default: y): ").strip().lower()
#             if create_viz != 'n':
#                 print(f"\n🎨 Creating enhanced visualizations...")
#                 try:
#                     timeline_fig, analysis_fig = load_and_visualize_data(filename)
#                     if timeline_fig and analysis_fig:
#                         print(f" Visualizations created successfully!")
                        
#                         save_viz = input("Save visualizations to files? (y/n, default: y): ").strip().lower()
#                         if save_viz != 'n':
#                             timeline_filename = f"timeline_{current_time.strftime('%Y%m%d_%H%M')}.png"
#                             analysis_filename = f"analysis_{current_time.strftime('%Y%m%d_%H%M')}.png"
#                             timeline_fig.savefig(timeline_filename, dpi=300, bbox_inches='tight')
#                             analysis_fig.savefig(analysis_filename, dpi=300, bbox_inches='tight')
#                             print(f" Saved: {timeline_filename}, {analysis_filename}")
#                 except Exception as e:
#                     print(f" Error creating visualizations: {e}")
                    
#         except Exception as e:
#             print(f" Could not save results: {e}")
    
#     # Final summary
#     print(f"\n🎯 OPERATION COMPLETE!")
#     print("=" * 30)
    
#     if choice in ['2', '3', '4'] and watcher_results:
#         print(f" Watcher Management Summary:")
#         print(f"   • Target: {watcher_results['watcher_name']}")
#         print(f"   • Tasks processed: {watcher_results['total_attempts']}")
#         print(f"   • Successful: {watcher_results['successful']}")
#         print(f"   • Failed: {watcher_results['failed']}")
#         if watcher_results.get('retry_successful'):
#             print(f"   • Retry successful: {watcher_results['retry_successful']}")
    
#     if choice in ['1', '4']:
#         print(f" Downtime Analysis Summary:")
#         print(f"   • Members analyzed: {len(members)}")
#         print(f"   • With downtime: {len(members_with_downtime)}")
#         print(f"   • Analysis saved: {filename if 'filename' in locals() else 'N/A'}")
    
#     print(f"\n Tips for next time:")
#     print(f"   • Use option 5 to re-visualize saved data")
#     print(f"   • Use option 6 to retry failed watcher operations")
#     print(f"   • Run analysis regularly for trend monitoring")
    
#     print(f"\n✨ Thank you for using ClickUp Enhanced Manager!")

# if __name__ == "__main__":
#     main()


import requests
import time
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import seaborn as sns
import numpy as np

API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'

# Working hours configuration - ADDED
WORKDAY_START_HOUR = 9
WORKDAY_END_HOUR = 17
LUNCH_BREAK_START = 12
LUNCH_BREAK_END = 12.5
WORKING_HOURS_PER_DAY = 7.5

def get_team_id():
    """Get the team ID"""
    resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()['teams'][0]['id']

def get_team_members(team_id):
    """Get all team members"""
    resp = requests.get(f"{BASE_URL}/team", headers=HEADERS)
    resp.raise_for_status()
    teams = resp.json().get('teams', [])
    for team in teams:
        if team.get('id') == str(team_id):
            return team.get('members', [])
    return []

def get_today_timestamps():
    """Get start and end timestamps for today"""
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert to ClickUp timestamps (milliseconds)
    start_ts = int(start_of_day.timestamp() * 1000)
    current_ts = int(now.timestamp() * 1000)
    
    return start_ts, current_ts, start_of_day, now

def get_member_tasks(team_id, member_id, max_retries=3):
    """Get all open tasks for a team member"""
    for attempt in range(max_retries):
        try:
            # Get open tasks only
            url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false"
            resp = requests.get(url, headers=HEADERS)
            
            if resp.status_code == 429:  # Rate limited
                wait_time = 60
                print(f"    Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            data = resp.json()
            return data.get('tasks', [])
            
        except requests.exceptions.RequestException as e:
            print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(30)
    
    print("    Failed to fetch tasks after all retries")
    return []

def is_task_in_progress(task):
    """Check if a task is currently in 'in progress' status"""
    status = task.get('status', {})
    if not status:
        return False
    
    status_name = status.get('status', '').lower()
    
    # Common "in progress" status variations
    progress_keywords = [
        'progress', 'in progress', 'in-progress', 'inprogress',
        'active', 'working', 'doing', 'current', 'ongoing',
        'started', 'development', 'dev', 'implementing',
        'in dev', 'in development'
    ]
    
    return any(keyword in status_name for keyword in progress_keywords)

# ADDED - Working hours filtering functions
def is_within_working_hours(timestamp):
    """Check if a timestamp is within working hours"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    
    hour = timestamp.hour + timestamp.minute / 60.0  # Convert to decimal hours
    
    # Check if within workday hours
    if hour < WORKDAY_START_HOUR or hour >= WORKDAY_END_HOUR:
        return False
    
    # Check if during lunch break
    if LUNCH_BREAK_START <= hour < LUNCH_BREAK_END:
        return False
    
    return True

def filter_periods_to_working_hours(periods):
    """Filter and clip periods to only include working hours"""
    filtered_periods = []
    
    for period in periods:
        start_time = period['start'] if isinstance(period['start'], datetime) else datetime.fromisoformat(period['start'])
        end_time = period['end'] if isinstance(period['end'], datetime) else datetime.fromisoformat(period['end'])
        
        # Get the working day boundaries for this date
        date = start_time.date()
        workday_start = datetime.combine(date, datetime.min.time()).replace(hour=WORKDAY_START_HOUR)
        workday_end = datetime.combine(date, datetime.min.time()).replace(hour=WORKDAY_END_HOUR)
        lunch_start = datetime.combine(date, datetime.min.time()).replace(hour=LUNCH_BREAK_START, minute=0)
        lunch_end = datetime.combine(date, datetime.min.time()).replace(hour=LUNCH_BREAK_START, minute=30)
        
        # Clip to working hours
        clipped_start = max(start_time, workday_start)
        clipped_end = min(end_time, workday_end)
        
        # Skip if period is outside working hours
        if clipped_start >= clipped_end:
            continue
        
        # Handle lunch break - split period if it spans lunch
        if clipped_start < lunch_start and clipped_end > lunch_end:
            # Period spans lunch break - create two periods
            # Morning period
            morning_period = period.copy()
            morning_period['start'] = clipped_start
            morning_period['end'] = lunch_start
            morning_period['duration_hours'] = (lunch_start - clipped_start).total_seconds() / 3600
            filtered_periods.append(morning_period)
            
            # Afternoon period
            afternoon_period = period.copy()
            afternoon_period['start'] = lunch_end
            afternoon_period['end'] = clipped_end
            afternoon_period['duration_hours'] = (clipped_end - lunch_end).total_seconds() / 3600
            filtered_periods.append(afternoon_period)
            
        elif clipped_end <= lunch_start or clipped_start >= lunch_end:
            # Period doesn't overlap with lunch break
            filtered_period = period.copy()
            filtered_period['start'] = clipped_start
            filtered_period['end'] = clipped_end
            filtered_period['duration_hours'] = (clipped_end - clipped_start).total_seconds() / 3600
            filtered_periods.append(filtered_period)
        
        elif clipped_start < lunch_start and clipped_end <= lunch_end:
            # Period ends during lunch break
            filtered_period = period.copy()
            filtered_period['start'] = clipped_start
            filtered_period['end'] = lunch_start
            filtered_period['duration_hours'] = (lunch_start - clipped_start).total_seconds() / 3600
            if filtered_period['duration_hours'] > 0:
                filtered_periods.append(filtered_period)
        
        elif clipped_start >= lunch_start and clipped_end > lunch_end:
            # Period starts during lunch break
            filtered_period = period.copy()
            filtered_period['start'] = lunch_end
            filtered_period['end'] = clipped_end
            filtered_period['duration_hours'] = (clipped_end - lunch_end).total_seconds() / 3600
            if filtered_period['duration_hours'] > 0:
                filtered_periods.append(filtered_period)
    
    return filtered_periods

def get_task_activity_today(task_id, today_start):
    """Get task activity for today only"""
    try:
        resp = requests.get(f"{BASE_URL}/task/{task_id}/activity", headers=HEADERS)
        
        if resp.status_code == 429:
            time.sleep(30)
            return []
        
        if resp.status_code == 404:
            return []
            
        resp.raise_for_status()
        all_activity = resp.json().get('activity', [])
        
        # Filter for today's activity only
        today_activity = []
        for activity in all_activity:
            activity_timestamp = activity.get('date')
            if activity_timestamp:
                activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                if activity_time.date() == today_start.date():
                    today_activity.append(activity)
        
        return today_activity
        
    except Exception as e:
        print(f"    Error getting activity for task {task_id}: {e}")
        return []

# MODIFIED - Don't merge overlapping tasks for stacking
def find_in_progress_periods_today(tasks, today_start, current_time):
    """Find all periods when user had in-progress tasks today - DON'T merge for stacking"""
    in_progress_periods = []
    
    print(f"    Analyzing {len(tasks)} tasks for in-progress periods...")
    
    # Check current status first
    currently_in_progress = []
    for task in tasks:
        if is_task_in_progress(task):
            currently_in_progress.append(task)
            print(f"      ✅ Currently in progress: {task['name'][:50]}")
    
    # If tasks are currently in progress, we need to find when they started
    for task in currently_in_progress:
        task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
        # If task was updated today, use that as start time
        if task_updated.date() == current_time.date():
            period_start = task_updated
        else:
            # Task was already in progress from start of day
            period_start = today_start.replace(hour=WORKDAY_START_HOUR)  # Use working hours
        
        in_progress_periods.append({
            'start': period_start,
            'end': current_time,
            'task_name': task['name'],
            'task_id': task['id'],  # Added task_id for tracking
            'duration_hours': (current_time - period_start).total_seconds() / 3600
        })
    
    # Also check activity for status changes today (sample first 10 tasks to avoid rate limits)
    for task in tasks[:10]:
        print(f"      Checking activity for: {task['name'][:40]}...")
        activity = get_task_activity_today(task['id'], today_start)
        
        # Look for status changes to "in progress" today
        for activity_item in activity:
            comment = activity_item.get('comment', '').lower()
            activity_timestamp = activity_item.get('date')
            
            if activity_timestamp and 'status' in comment:
                activity_time = datetime.fromtimestamp(int(activity_timestamp) / 1000)
                
                # Check if status changed TO in-progress
                if any(keyword in comment for keyword in ['progress', 'development', 'active', 'working']):
                    if 'to' in comment:
                        # Find when this in-progress period ended (or is still ongoing)
                        period_end = current_time
                        
                        # Look for later status changes
                        for later_activity in activity:
                            later_timestamp = later_activity.get('date')
                            if later_timestamp and int(later_timestamp) > int(activity_timestamp):
                                later_time = datetime.fromtimestamp(int(later_timestamp) / 1000)
                                later_comment = later_activity.get('comment', '').lower()
                                
                                if 'status' in later_comment and 'to' in later_comment:
                                    # Check if it changed away from in-progress
                                    if not any(keyword in later_comment for keyword in ['progress', 'development', 'active', 'working']):
                                        period_end = later_time
                                        break
                        
                        duration = (period_end - activity_time).total_seconds() / 3600
                        if duration > 0.1:  # At least 6 minutes
                            in_progress_periods.append({
                                'start': activity_time,
                                'end': period_end,
                                'task_name': task['name'],
                                'task_id': task['id'],
                                'duration_hours': duration
                            })
                            
                            print(f"        📅 Found period: {activity_time.strftime('%H:%M')} - "
                                  f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
        
        time.sleep(1)  # Rate limit prevention
    
    # Sort by start time but DON'T merge - we want to show overlapping tasks as stacked
    in_progress_periods.sort(key=lambda x: x['start'])
    
    # REMOVED the merging logic - return all periods separately for stacking
    return in_progress_periods

# MODIFIED - Working hours aware downtime calculation
def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
    """Calculate downtime periods during working hours only"""
    print(f"    Calculating downtime for {member_name} (working hours only)...")
    
    workday_start = today_start.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    workday_end = today_start.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    lunch_start = today_start.replace(hour=LUNCH_BREAK_START, minute=0, second=0, microsecond=0)
    lunch_end = today_start.replace(hour=LUNCH_BREAK_START, minute=30, second=0, microsecond=0)
    
    # Limit current time to working hours
    analysis_end_time = min(current_time, workday_end)
    if analysis_end_time < workday_start:
        return []  # Haven't started work yet
    
    downtime_periods = []
    
    # Filter in_progress_periods to working hours
    filtered_periods = filter_periods_to_working_hours(in_progress_periods)
    
    if not filtered_periods:
        # No in-progress periods during working hours
        if analysis_end_time > workday_start:
            # Calculate total working time until now (excluding lunch if passed)
            if analysis_end_time <= lunch_start:
                # Haven't reached lunch yet
                hours_inactive = (analysis_end_time - workday_start).total_seconds() / 3600
                downtime_periods.append({
                    'start': workday_start,
                    'end': analysis_end_time,
                    'duration_hours': hours_inactive,
                    'type': 'no_activity_all_day'
                })
            elif workday_start < lunch_start and analysis_end_time > lunch_end:
                # Spans lunch break - split into two periods
                # Morning downtime
                morning_hours = (lunch_start - workday_start).total_seconds() / 3600
                downtime_periods.append({
                    'start': workday_start,
                    'end': lunch_start,
                    'duration_hours': morning_hours,
                    'type': 'no_activity_morning'
                })
                # Afternoon downtime
                afternoon_hours = (analysis_end_time - lunch_end).total_seconds() / 3600
                downtime_periods.append({
                    'start': lunch_end,
                    'end': analysis_end_time,
                    'duration_hours': afternoon_hours,
                    'type': 'no_activity_afternoon'
                })
            
            print(f"      🔴 No activity during working hours")
    else:
        # Sort periods by start time
        filtered_periods.sort(key=lambda x: x['start'])
        
        # Check gap from workday start to first activity
        first_activity = filtered_periods[0]['start']
        if first_activity > workday_start:
            gap_end = min(first_activity, lunch_start) if first_activity > lunch_start else first_activity
            gap_hours = (gap_end - workday_start).total_seconds() / 3600
            if gap_hours >= 1:  # Reduced threshold for working hours
                downtime_periods.append({
                    'start': workday_start,
                    'end': gap_end,
                    'duration_hours': gap_hours,
                    'type': 'late_start'
                })
                print(f"      🔴 Late start: {gap_hours:.1f} hours")
        
        # Check gaps between activities (considering lunch break)
        for i in range(len(filtered_periods) - 1):
            gap_start = filtered_periods[i]['end']
            gap_end = filtered_periods[i + 1]['start']
            
            # Skip if gap is during lunch break
            if gap_start <= lunch_start and gap_end >= lunch_end:
                continue
                
            gap_hours = (gap_end - gap_start).total_seconds() / 3600
            
            if gap_hours >= 1:  # Reduced threshold for working hours
                downtime_periods.append({
                    'start': gap_start,
                    'end': gap_end,
                    'duration_hours': gap_hours,
                    'type': 'midday_gap'
                })
                print(f"      🔴 Midday gap: {gap_hours:.1f} hours")
        
        # Check gap from last activity to now
        last_activity_end = filtered_periods[-1]['end']
        if analysis_end_time > last_activity_end:
            gap_hours = (analysis_end_time - last_activity_end).total_seconds() / 3600
            if gap_hours >= 1:  # Reduced threshold for working hours
                downtime_periods.append({
                    'start': last_activity_end,
                    'end': analysis_end_time,
                    'duration_hours': gap_hours,
                    'type': 'current_inactive'
                })
                print(f"      🔴 CURRENTLY INACTIVE: {gap_hours:.1f} hours since last activity")
    
    return downtime_periods

def find_user_by_name(members, name):
    """Find a user by their username or display name"""
    name_lower = name.lower()
    for member in members:
        user = member.get('user', {})
        username = user.get('username', '').lower()
        email = user.get('email', '').lower()
        
        if (name_lower in username or 
            name_lower in email or 
            username == name_lower):
            return user
    return None

def get_task_details(task_id):
    """Get detailed task information including watchers"""
    try:
        resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            print(f"      ⚠️ Task {task_id} not found or no access")
        elif resp.status_code == 401:
            print(f"      ⚠️ No permission to access task {task_id}")
        else:
            print(f"      ⚠️ Error {resp.status_code} accessing task {task_id}")
        return None
    except Exception as e:
        print(f"      ❌ Exception getting task details: {e}")
        return None

def debug_watcher_api(task_id, user_id, user_name):
    """Enhanced debug function to test all API endpoints systematically"""
    print(f"    🔍 [DEBUG] Testing watcher API for task {task_id} and user {user_name}...")
    
    # Get task details first
    task_details = get_task_details(task_id)
    if task_details:
        task_name = task_details.get('name', 'Unknown')[:50]
        print(f"      📋 Task: {task_name}")
        current_watchers = task_details.get('watchers', [])
        print(f"      👁️ Current watchers: {len(current_watchers)}")
        
        # Check if user is already a watcher
        watcher_ids = [str(w.get('id', '')) for w in current_watchers if w.get('id')]
        if str(user_id) in watcher_ids:
            print(f"      ✅ {user_name} is already watching this task!")
            return True
        
        # Show current watchers
        for watcher in current_watchers:
            watcher_user = watcher.get('user', {})
            watcher_name = watcher_user.get('username', 'Unknown')
            print(f"         - {watcher_name}")
    else:
        print(f"      ❌ Cannot access task {task_id}")
        return False
    
    # Test different API endpoints systematically
    test_methods = [
        {
            'name': 'PUT /task/{id}/watcher (watchers.add array)',
            'method': 'PUT',
            'url': f"{BASE_URL}/task/{task_id}/watcher",
            'payload': {"watchers": {"add": [user_id]}},
            'headers': {**HEADERS, 'Content-Type': 'application/json'}
        },
        {
            'name': 'PUT /task/{id}/watcher (single watcher)',
            'method': 'PUT', 
            'url': f"{BASE_URL}/task/{task_id}/watcher",
            'payload': {"watcher": user_id},
            'headers': {**HEADERS, 'Content-Type': 'application/json'}
        },
        {
            'name': 'POST /task/{id}/watcher/{user_id}',
            'method': 'POST',
            'url': f"{BASE_URL}/task/{task_id}/watcher/{user_id}",
            'payload': None,
            'headers': HEADERS
        },
        {
            'name': 'POST /task/{id}/watcher',
            'method': 'POST',
            'url': f"{BASE_URL}/task/{task_id}/watcher",
            'payload': {"watcher": user_id},
            'headers': {**HEADERS, 'Content-Type': 'application/json'}
        },
        {
            'name': 'PUT /task/{id} (update task)',
            'method': 'PUT',
            'url': f"{BASE_URL}/task/{task_id}",
            'payload': {"watchers": {"add": [user_id]}},
            'headers': {**HEADERS, 'Content-Type': 'application/json'}
        }
    ]
    
    for i, method_info in enumerate(test_methods, 1):
        try:
            print(f"      🧪 Method {i}: {method_info['name']}")
            
            if method_info['method'] == 'PUT':
                resp = requests.put(
                    method_info['url'], 
                    headers=method_info['headers'],
                    json=method_info['payload'] if method_info['payload'] else None
                )
            elif method_info['method'] == 'POST':
                if method_info['payload']:
                    resp = requests.post(
                        method_info['url'],
                        headers=method_info['headers'],
                        json=method_info['payload']
                    )
                else:
                    resp = requests.post(method_info['url'], headers=method_info['headers'])
            
            print(f"         Status: {resp.status_code}")
            
            if resp.status_code == 200:
                print(f"      ✅ SUCCESS! Method {i} worked!")
                
                # Verify the watcher was actually added
                time.sleep(1)
                updated_task = get_task_details(task_id)
                if updated_task:
                    updated_watchers = updated_task.get('watchers', [])
                    updated_watcher_ids = [str(w.get('id', '')) for w in updated_watchers if w.get('id')]
                    if str(user_id) in updated_watcher_ids:
                        print(f"      ✅ VERIFIED: {user_name} successfully added as watcher!")
                        return True
                    else:
                        print(f"      ⚠️ API returned 200 but user not found in watchers list")
                else:
                    print(f"      ⚠️ Cannot verify - task details unavailable")
                
                return True
                
            elif resp.status_code in [400, 404, 403, 401]:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('err', error_data.get('error', 'Unknown error'))
                    print(f"         Error: {error_msg}")
                    
                    # Check for specific error conditions
                    if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        print(f"      ✅ User already watching (error message confirms)")
                        return True
                except:
                    print(f"         Raw response: {resp.text[:200]}")
            else:
                print(f"         Unexpected status: {resp.status_code}")
                
        except Exception as e:
            print(f"         Exception: {str(e)[:100]}")
        
        # Small delay between attempts
        time.sleep(0.5)
    
    print(f"      ❌ All {len(test_methods)} methods failed for {user_name}")
    return False

def add_watcher_to_task(task_id, user_id, user_name="Unknown", use_debug=False):
    """Add a user as a watcher to a specific task with enhanced error handling"""
    if use_debug:
        return debug_watcher_api(task_id, user_id, user_name)
    
    try:
        # Quick method 1: Standard PUT with watchers array
        url = f"{BASE_URL}/task/{task_id}/watcher"
        payload = {"watchers": {"add": [user_id]}}
        
        resp = requests.put(url, headers={**HEADERS, 'Content-Type': 'application/json'}, 
                           json=payload)
        
        if resp.status_code == 200:
            print(f"      ✅ Added {user_name} as watcher")
            return True
        elif resp.status_code == 400:
            # Check if user is already a watcher
            error_msg = resp.json().get('err', '')
            if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"      ℹ️ {user_name} already watching")
                return True
        
        # Method 2: POST with user_id in path
        url = f"{BASE_URL}/task/{task_id}/watcher/{user_id}"
        resp = requests.post(url, headers=HEADERS)
        
        if resp.status_code == 200:
            print(f"      ✅ Added {user_name} as watcher (method 2)")
            return True
        
        # If both quick methods fail, use debug mode
        print(f"      🔧 Standard methods failed, trying debug mode...")
        return debug_watcher_api(task_id, user_id, user_name)
            
    except Exception as e:
        print(f"      ❌ Error adding {user_name} as watcher: {e}")
        return False

def add_watcher_to_all_tasks(tasks, watcher_user_id, watcher_name, dry_run=False, debug_mode=False):
    """Add a watcher to multiple tasks with progress tracking"""
    print(f"\n👁️ {'[DRY RUN] ' if dry_run else ''}Adding {watcher_name} as watcher to {len(tasks)} tasks...")
    
    if debug_mode:
        print(f"🔍 Debug mode enabled - using comprehensive API testing")
    
    success_count = 0
    failed_count = 0
    already_watching_count = 0
    failed_tasks = []
    
    for i, task in enumerate(tasks, 1):
        task_id = task['id']
        task_name = task['name'][:50] + "..." if len(task['name']) > 50 else task['name']
        
        print(f"\n   [{i:3d}/{len(tasks)}] {task_name}")
        
        if dry_run:
            print(f"      🔍 [DRY RUN] Would add {watcher_name} as watcher")
            success_count += 1
        else:
            # Use debug mode for first few tasks or if specifically requested
            use_debug = debug_mode or (i <= 3 and failed_count > 0)
            result = add_watcher_to_task(task_id, watcher_user_id, watcher_name, use_debug)
            
            if result:
                success_count += 1
            else:
                failed_count += 1
                failed_tasks.append({'id': task_id, 'name': task_name})
            
            # Progressive rate limiting - slower if we're having failures
            if failed_count > success_count:
                time.sleep(3)  # Slower when having issues
            else:
                time.sleep(1.5)  # Normal rate
    
    print(f"\n📊 Watcher Addition Summary:")
    print(f"   ✅ Successful: {success_count}")
    
    if not dry_run:
        print(f"   ❌ Failed: {failed_count}")
        
        if failed_tasks:
            print(f"\n🚨 Failed Tasks (for retry):")
            for task in failed_tasks[:5]:  # Show first 5 failures
                print(f"   - {task['name']} (ID: {task['id']})")
            if len(failed_tasks) > 5:
                print(f"   ... and {len(failed_tasks) - 5} more")
    
    return success_count, failed_count, failed_tasks

def get_member_tasks_with_date_range(team_id, member_id, days_back=7, max_retries=3):
    """Get tasks for a member within a date range"""
    for attempt in range(max_retries):
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            # Get tasks updated within date range
            url = f"{BASE_URL}/team/{team_id}/task?assignees[]={member_id}&include_closed=false&date_updated_gt={start_ts}&date_updated_lt={end_ts}"
            resp = requests.get(url, headers=HEADERS)
            
            if resp.status_code == 429:  # Rate limited
                wait_time = 60
                print(f"    Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            data = resp.json()
            return data.get('tasks', [])
            
        except requests.exceptions.RequestException as e:
            print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(30)
    
    print("    Failed to fetch tasks after all retries")
    return []

# MODIFIED - Stacked timeline visualization  
def create_enhanced_timeline_visualization(data, save_path="clickup_timeline_enhanced.png"):
    """Create an enhanced timeline visualization with stacked tasks and working hours"""
    fig = plt.figure(figsize=(20, 14))
    
    # Create grid for different chart sections
    gs = fig.add_gridspec(4, 2, height_ratios=[3, 1, 1, 1], width_ratios=[3, 1], hspace=0.3, wspace=0.2)
    
    # Main timeline (top left, spanning 2 columns)
    ax_timeline = fig.add_subplot(gs[0, :])
    
    # Status bars (middle left)
    ax_status = fig.add_subplot(gs[1, 0])
    
    # Productivity pie (middle right)
    ax_productivity = fig.add_subplot(gs[1, 1])
    
    # Hourly activity (bottom left)
    ax_hourly = fig.add_subplot(gs[2, 0])
    
    # Statistics panel (bottom right)
    ax_stats = fig.add_subplot(gs[2, 1])
    
    # Alert panel (very bottom, spanning both)
    ax_alerts = fig.add_subplot(gs[3, :])
    
    # Parse the data
    detailed_data = data['detailed_data']
    members = list(detailed_data.keys())
    
    # Enhanced color scheme for different tasks
    task_colors = plt.cm.Set3(np.linspace(0, 1, 20))  # More colors for different tasks
    colors = {
        'active': '#28a745',      # Bootstrap success green
        'downtime': '#dc3545',    # Bootstrap danger red
        'warning': '#ffc107',     # Bootstrap warning yellow
        'info': '#17a2b8',        # Bootstrap info blue
        'no_activity': '#6c757d'  # Bootstrap secondary gray
    }
    
    # 1. MAIN TIMELINE WITH STACKED TASKS
    ax_timeline.set_title(f"📊 Team Activity Timeline (Working Hours Only) - {data['date']}", 
                         fontsize=18, fontweight='bold', pad=20)
    
    # Calculate member positions with space for stacking
    member_height = 0.8
    stack_height = 0.15  # Height of each task stack
    max_concurrent_tasks = 5  # Maximum tasks to show stacked
    
    y_positions = range(len(members))
    ax_timeline.set_yticks(y_positions)
    ax_timeline.set_yticklabels(members, fontsize=12)
    
    # Parse timestamps and set working hours boundaries
    current_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    start_time = current_time.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    end_time = current_time.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    lunch_start = current_time.replace(hour=LUNCH_BREAK_START, minute=0, second=0, microsecond=0)
    lunch_end = current_time.replace(hour=LUNCH_BREAK_START, minute=30, second=0, microsecond=0)
    
    # Add lunch break indicator
    lunch_height = len(members)
    lunch_rect = Rectangle((mdates.date2num(lunch_start), -0.5), 
                          mdates.date2num(lunch_end) - mdates.date2num(lunch_start), lunch_height + 1,
                          facecolor='lightgray', alpha=0.3, edgecolor='gray', linewidth=1)
    ax_timeline.add_patch(lunch_rect)
    ax_timeline.text(mdates.date2num(lunch_start) + (mdates.date2num(lunch_end) - mdates.date2num(lunch_start))/2, 
                    len(members)/2, 'LUNCH\nBREAK', ha='center', va='center', 
                    fontsize=10, fontweight='bold', alpha=0.7)
    
    # Track member status for other charts
    member_stats = {}
    task_color_map = {}  # Map task names to colors
    color_index = 0
    
    for i, member in enumerate(members):
        member_data = detailed_data[member]
        
        # Filter periods to working hours only
        filtered_active_periods = filter_periods_to_working_hours(member_data['in_progress_periods'])
        filtered_downtime_periods = filter_periods_to_working_hours(member_data['downtime_periods'])
        
        total_downtime = sum(p['duration_hours'] for p in filtered_downtime_periods)
        total_active = sum(p['duration_hours'] for p in filtered_active_periods)
        
        member_stats[member] = {
            'total_downtime': total_downtime,
            'total_active': total_active,
            'status': 'critical' if total_downtime >= 3 else 'warning' if total_downtime >= 1 else 'good'  # Adjusted thresholds
        }
        
        # Process active periods - stack overlapping tasks
        active_periods_by_time = {}
        
        for period in filtered_active_periods:
            period_start = period['start'] if isinstance(period['start'], datetime) else datetime.fromisoformat(period['start'])
            period_end = period['end'] if isinstance(period['end'], datetime) else datetime.fromisoformat(period['end'])
            
            # Find overlapping periods for stacking
            stack_level = 0
            for existing_period in filtered_active_periods:
                if existing_period == period:
                    continue
                existing_start = existing_period['start'] if isinstance(existing_period['start'], datetime) else datetime.fromisoformat(existing_period['start'])
                existing_end = existing_period['end'] if isinstance(existing_period['end'], datetime) else datetime.fromisoformat(existing_period['end'])
                
                # Check if periods overlap
                if (period_start < existing_end and period_end > existing_start):
                    stack_level += 1
                    if stack_level >= max_concurrent_tasks:
                        break
            
            # Calculate stack position
            stack_y = i - member_height/2 + (stack_level * stack_height)
            
            # Assign color to task
            task_name = period['task_name']
            if task_name not in task_color_map:
                task_color_map[task_name] = task_colors[color_index % len(task_colors)]
                color_index += 1
            
            task_color = task_color_map[task_name]
            
            # Draw task rectangle
            rect = Rectangle((mdates.date2num(period_start), stack_y), 
                           mdates.date2num(period_end) - mdates.date2num(period_start), stack_height,
                           facecolor=task_color, alpha=0.8, edgecolor='darkgreen', linewidth=1)
            ax_timeline.add_patch(rect)
            
            # Add task name with better formatting (only for longer tasks)
            duration_minutes = (period_end - period_start).total_seconds() / 60
            if duration_minutes > 30:  # Only label tasks longer than 30 minutes
                mid_time = period_start + (period_end - period_start) / 2
                task_name_short = task_name[:20] + "..." if len(task_name) > 20 else task_name
                ax_timeline.text(mdates.date2num(mid_time), stack_y + stack_height/2, task_name_short, 
                               ha='center', va='center', fontsize=8, fontweight='bold', 
                               color='white', bbox=dict(boxstyle="round,pad=0.1", facecolor='darkgreen', alpha=0.7))
        
        # Draw downtime periods
        for period in filtered_downtime_periods:
            period_start = period['start'] if isinstance(period['start'], datetime) else datetime.fromisoformat(period['start'])
            period_end = period['end'] if isinstance(period['end'], datetime) else datetime.fromisoformat(period['end'])
            
            # Color based on duration and type
            duration = period['duration_hours']
            if duration >= 3:
                color = colors['no_activity']  # Very severe
            elif duration >= 1:
                color = colors['downtime']     # Severe  
            else:
                color = colors['warning']      # Moderate
            
            rect = Rectangle((mdates.date2num(period_start), i - member_height/2), 
                           mdates.date2num(period_end) - mdates.date2num(period_start), member_height,
                           facecolor=color, alpha=0.6, edgecolor='darkred', linewidth=1)
            ax_timeline.add_patch(rect)
            
            # Add downtime info for significant gaps
            if duration >= 1:  # Only label downtime >= 1 hour
                mid_time = period_start + (period_end - period_start) / 2
                duration_text = f"🚨 {duration:.1f}h"
                if abs((period['end'] - current_time).total_seconds()) < 300:
                    duration_text += " (NOW)"
                
                ax_timeline.text(mdates.date2num(mid_time), i, duration_text, 
                               ha='center', va='center', fontsize=10, fontweight='bold', 
                               color='white', bbox=dict(boxstyle="round,pad=0.3", facecolor='darkred', alpha=0.8))
    
    # Format timeline x-axis for working hours
    ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax_timeline.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    
    # Set limits to working hours only
    display_start = min(start_time, current_time.replace(hour=WORKDAY_START_HOUR, minute=0))
    display_end = min(end_time, current_time) if current_time.hour < WORKDAY_END_HOUR else end_time
    ax_timeline.set_xlim(mdates.date2num(display_start), mdates.date2num(display_end))
    
    ax_timeline.grid(True, alpha=0.3, linestyle='--')
    ax_timeline.set_xlabel("Time of Day (Working Hours: 9 AM - 5 PM, Lunch: 12:00-12:30)", fontsize=12, fontweight='bold')
    
    # Enhanced legend for stacked view
    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=colors['warning'], label='🟡 Moderate Downtime (1-3h)'),
        Rectangle((0, 0), 1, 1, facecolor=colors['downtime'], label='🔴 Severe Downtime (1-3h)'),
        Rectangle((0, 0), 1, 1, facecolor=colors['no_activity'], label='⚫ Critical Downtime (3+h)'),
        Rectangle((0, 0), 1, 1, facecolor='lightgray', alpha=0.3, label='🍽️ Lunch Break'),
        plt.Line2D([0], [0], color='white', linewidth=10, label='Tasks are stacked when concurrent')
    ]
    ax_timeline.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # 2. STATUS BARS (Updated for working hours)
    ax_status.set_title("⚡ Current Member Status (Working Hours)", fontsize=14, fontweight='bold')
    
    status_colors = []
    status_labels = []
    downtime_values = []
    
    for member in members:
        stats = member_stats[member]
        downtime_values.append(stats['total_downtime'])
        
        if stats['status'] == 'critical':
            status_colors.append(colors['no_activity'])
            status_labels.append(f"{member[:15]} 🆘")
        elif stats['status'] == 'warning':
            status_colors.append(colors['downtime'])
            status_labels.append(f"{member[:15]} ⚠️")
        else:
            status_colors.append(colors['active'])
            status_labels.append(f"{member[:15]} ✅")
    
    bars = ax_status.barh(range(len(members)), downtime_values, color=status_colors, alpha=0.8, edgecolor='black')
    ax_status.set_yticks(range(len(members)))
    ax_status.set_yticklabels(status_labels, fontsize=10)
    ax_status.set_xlabel("Hours of Downtime (Working Hours)", fontsize=11)
    ax_status.axvline(x=1, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='1h threshold')
    ax_status.axvline(x=3, color='red', linestyle='--', alpha=0.7, linewidth=2, label='3h critical')
    ax_status.grid(True, alpha=0.3, axis='x')
    ax_status.legend(fontsize=9)
    
    # Add value labels
    for i, (bar, hours) in enumerate(zip(bars, downtime_values)):
        if hours > 0:
            ax_status.text(hours + 0.1, i, f'{hours:.1f}h', va='center', fontweight='bold', fontsize=9)
    
    # 3. PRODUCTIVITY PIE (Updated)
    ax_productivity.set_title("🎯 Team Status (Working Hours)", fontsize=14, fontweight='bold')
    
    good_count = sum(1 for stats in member_stats.values() if stats['status'] == 'good')
    warning_count = sum(1 for stats in member_stats.values() if stats['status'] == 'warning')
    critical_count = sum(1 for stats in member_stats.values() if stats['status'] == 'critical')
    
    sizes = [good_count, warning_count, critical_count]
    labels = [f'✅ Good\n({good_count})', f'⚠️ Warning\n({warning_count})', f'🆘 Critical\n({critical_count})']
    colors_pie = [colors['active'], colors['warning'], colors['downtime']]
    explode = (0.05, 0.1, 0.15)
    
    # Only show non-zero categories
    non_zero_sizes = [(size, label, color, exp) for size, label, color, exp in zip(sizes, labels, colors_pie, explode) if size > 0]
    
    if non_zero_sizes:
        sizes_nz, labels_nz, colors_nz, explode_nz = zip(*non_zero_sizes)
        wedges, texts, autotexts = ax_productivity.pie(sizes_nz, labels=labels_nz, colors=colors_nz, 
                                                      explode=explode_nz, autopct='%1.1f%%', 
                                                      startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
    else:
        ax_productivity.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_productivity.transAxes)
    
    # 4. HOURLY ACTIVITY HEATMAP (Working hours focused)
    ax_hourly.set_title("📈 Hourly Activity Distribution", fontsize=14, fontweight='bold')
    
    # Create hourly activity matrix for working hours only
    work_hours = list(range(WORKDAY_START_HOUR, WORKDAY_END_HOUR))
    hourly_matrix = np.zeros((len(members), len(work_hours)))
    
    for i, member in enumerate(members):
        member_data = detailed_data[member]
        filtered_periods = filter_periods_to_working_hours(member_data['in_progress_periods'])
        
        for period in filtered_periods:
            start_time_period = period['start'] if isinstance(period['start'], datetime) else datetime.fromisoformat(period['start'])
            end_time_period = period['end'] if isinstance(period['end'], datetime) else datetime.fromisoformat(period['end'])
            
            for j, hour in enumerate(work_hours):
                # Skip lunch hour
                if hour == LUNCH_BREAK_START:
                    continue
                    
                hour_start = start_time_period.replace(hour=hour, minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                # Calculate overlap
                overlap_start = max(start_time_period, hour_start)
                overlap_end = min(end_time_period, hour_end)
                
                if overlap_start < overlap_end:
                    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                    hourly_matrix[i, j] = overlap_minutes / 60  # Convert to fraction of hour
    
    im = ax_hourly.imshow(hourly_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax_hourly.set_yticks(range(len(members)))
    ax_hourly.set_yticklabels([m[:12] + "..." if len(m) > 12 else m for m in members], fontsize=9)
    ax_hourly.set_xticks(range(len(work_hours)))
    ax_hourly.set_xticklabels([f"{h:02d}:00" if h != LUNCH_BREAK_START else "LUNCH" for h in work_hours], fontsize=9, rotation=45)
    ax_hourly.set_xlabel("Hour of Day (Working Hours)", fontsize=11)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax_hourly, shrink=0.8)
    cbar.set_label('Activity Level', rotation=270, labelpad=15, fontsize=10)
    
    # 5. STATISTICS PANEL (Updated for working hours)
    ax_stats.axis('off')
    
    # Calculate key statistics for working hours
    total_team_downtime = sum(stats['total_downtime'] for stats in member_stats.values())
    total_team_active = sum(stats['total_active'] for stats in member_stats.values())
    avg_downtime = total_team_downtime / len(members) if members else 0
    
    currently_inactive = []
    for member, member_data in detailed_data.items():
        for period in member_data['downtime_periods']:
            if isinstance(period['end'], str):
                period_end = datetime.fromisoformat(period['end'])
            else:
                period_end = period['end']
            
            if abs((period_end - current_time).total_seconds()) < 300:  # Within 5 minutes
                currently_inactive.append(member)
                break
    
    stats_text = f"""
📊 TEAM STATISTICS (WORKING HOURS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Total Members: {len(members)}
✅ Good Status: {good_count}
⚠️  Warning Status: {warning_count}  
🆘 Critical Status: {critical_count}

⏱️  TIMING ANALYSIS  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕒 Current Time: {current_time.strftime('%H:%M')}
📅 Analysis Date: {data['date']}
🏢 Working Hours: {WORKDAY_START_HOUR}:00 AM - {WORKDAY_END_HOUR}:00 PM
🍽️ Lunch Break: {LUNCH_BREAK_START}:00 - {LUNCH_BREAK_END}:30
⚡ Total Team Active: {total_team_active:.1f}h
🔻 Total Team Downtime: {total_team_downtime:.1f}h
📊 Max Daily Hours: {WORKING_HOURS_PER_DAY * len(members):.1f}h

🚨 ALERTS (WORKING HOURS ONLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 Currently Inactive: {len(currently_inactive)}
"""
    
    if currently_inactive:
        stats_text += f"\n   • {', '.join(currently_inactive[:3])}"
        if len(currently_inactive) > 3:
            stats_text += f"\n   • +{len(currently_inactive) - 3} more..."
    
    ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes, fontsize=10, 
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9))
    
    # 6. ALERTS PANEL (Updated for working hours)
    ax_alerts.axis('off')
    ax_alerts.set_title("🚨 PRIORITY ALERTS", fontsize=16, fontweight='bold', color='red', pad=10)
    
    alerts = []
    
    # Generate alerts based on analysis
    if critical_count > 0:
        critical_members = [m for m, s in member_stats.items() if s['status'] == 'critical']
        alerts.append(f"🆘 CRITICAL: {critical_count} member(s) with 3+ hours downtime: {', '.join(critical_members)}")
    
    if currently_inactive:
        alerts.append(f"🔥 IMMEDIATE: {len(currently_inactive)} member(s) currently inactive: {', '.join(currently_inactive)}")
    
    if warning_count > len(members) * 0.5:
        alerts.append(f"⚠️  TEAM ISSUE: Over 50% of team has significant downtime")
    
    if avg_downtime > 2:
        alerts.append(f"📉 PRODUCTIVITY: Team average downtime is {avg_downtime:.1f} hours")
    
    if not alerts:
        alerts.append("✅ ALL CLEAR: No critical issues detected during working hours")
    
    alert_text = "\n".join(f"• {alert}" for alert in alerts[:4])  # Show top 4 alerts
    
    ax_alerts.text(0.05, 0.5, alert_text, transform=ax_alerts.transAxes, fontsize=12, 
                  verticalalignment='center', fontweight='bold',
                  bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9, edgecolor='red'))
    
    plt.suptitle(f"🎯 ClickUp Team Performance Dashboard (Working Hours) - {data['date']}", 
                fontsize=20, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Enhanced stacked timeline visualization saved to: {save_path}")
    
    return fig

def create_watcher_management_report(watcher_results, save_path="watcher_report.json"):
    """Create a detailed report of watcher management results"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'watcher_operations': watcher_results,
        'summary': {
            'total_attempts': watcher_results.get('total_attempts', 0),
            'successful': watcher_results.get('successful', 0),
            'failed': watcher_results.get('failed', 0),
            'success_rate': 0
        }
    }
    
    if report['summary']['total_attempts'] > 0:
        report['summary']['success_rate'] = (report['summary']['successful'] / 
                                           report['summary']['total_attempts']) * 100
    
    try:
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"📄 Watcher management report saved to: {save_path}")
    except Exception as e:
        print(f"⚠️ Could not save watcher report: {e}")
    
    return report

def retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name):
    """Retry adding watchers to previously failed tasks with enhanced debugging"""
    if not failed_tasks:
        print("✅ No failed tasks to retry")
        return
    
    print(f"\n🔄 Retrying {len(failed_tasks)} failed watcher additions...")
    print("🔍 Using enhanced debug mode for all retries...")
    
    retry_success = 0
    still_failed = []
    
    for i, task in enumerate(failed_tasks, 1):
        task_id = task['id']
        task_name = task['name']
        
        print(f"\n   [RETRY {i}/{len(failed_tasks)}] {task_name}")
        
        # Use full debug mode for retries
        result = debug_watcher_api(task_id, watcher_user_id, watcher_name)
        
        if result:
            retry_success += 1
            print(f"      ✅ Retry successful!")
        else:
            still_failed.append(task)
            print(f"      ❌ Still failed after retry")
        
        # Longer delay for retries
        time.sleep(3)
    
    print(f"\n📊 Retry Results:")
    print(f"   🔄 Retried: {len(failed_tasks)}")
    print(f"   ✅ Now successful: {retry_success}")
    print(f"   ❌ Still failing: {len(still_failed)}")
    
    if still_failed:
        print(f"\n🚨 Tasks that still fail after retry:")
        for task in still_failed[:3]:
            print(f"   - {task['name']} (ID: {task['id']})")
        if len(still_failed) > 3:
            print(f"   ... and {len(still_failed) - 3} more")
    
    return retry_success, still_failed

def load_and_visualize_data(json_file_path):
    """Load JSON data and create enhanced visualizations"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Creating enhanced visualizations for {data['date']}...")
        print(f"   Members analyzed: {data['members_analyzed']}")
        print(f"   Members with downtime: {data['members_with_downtime']}")
        
        # Create enhanced timeline visualization
        timeline_fig = create_enhanced_timeline_visualization(data)
        
        # Create additional analysis if needed
        analysis_fig = create_detailed_analysis_charts(data)
        
        # Show plots
        plt.show()
        
        return timeline_fig, analysis_fig
        
    except FileNotFoundError:
        print(f"❌ Could not find file: {json_file_path}")
        return None, None
    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")
        return None, None

def create_detailed_analysis_charts(data, save_path="clickup_detailed_analysis.png"):
    """Create comprehensive detailed analysis charts"""
    fig, axes = plt.subplots(2, 3, figsize=(24, 16))
    fig.suptitle(f'📈 Detailed Team Analysis - {data["date"]}', fontsize=18, fontweight='bold')
    
    detailed_data = data['detailed_data']
    members = list(detailed_data.keys())
    
    # 1. Active vs Downtime Comparison (Top Left)
    ax1 = axes[0, 0]
    ax1.set_title("⚡ Active vs Downtime Hours", fontsize=14, fontweight='bold')
    
    active_hours = []
    downtime_hours = []
    
    for member in members:
        member_data = detailed_data[member]
        active_time = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
        downtime_time = sum(p['duration_hours'] for p in member_data['downtime_periods'])
        
        active_hours.append(active_time)
        downtime_hours.append(downtime_time)
    
    x = np.arange(len(members))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, active_hours, width, label='✅ Active Hours', 
                   color='#28a745', alpha=0.8, edgecolor='darkgreen')
    bars2 = ax1.bar(x + width/2, downtime_hours, width, label='🔴 Downtime Hours', 
                   color='#dc3545', alpha=0.8, edgecolor='darkred')
    
    ax1.set_xlabel('Team Members', fontweight='bold')
    ax1.set_ylabel('Hours', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([m[:8] + "..." if len(m) > 8 else m for m in members], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05, f'{height:.1f}h',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 2. Downtime Categories Breakdown (Top Middle)
    ax2 = axes[0, 1]
    ax2.set_title("📊 Downtime Categories", fontsize=14, fontweight='bold')
    
    downtime_types = {}
    for member_data in detailed_data.values():
        for period in member_data['downtime_periods']:
            period_type = period['type']
            if period_type not in downtime_types:
                downtime_types[period_type] = 0
            downtime_types[period_type] += period['duration_hours']
    
    if downtime_types:
        readable_labels = {
            'no_activity_all_day': 'No Activity All Day',
            'no_activity_morning': 'No Morning Activity',
            'no_activity_afternoon': 'No Afternoon Activity',
            'no_tasks': 'No Tasks Assigned',
            'late_start': 'Late Start',
            'midday_gap': 'Midday Gap',
            'current_inactive': 'Currently Inactive'
        }
        
        labels = [readable_labels.get(t, t.replace('_', ' ').title()) for t in downtime_types.keys()]
        values = list(downtime_types.values())
        
        colors_donut = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = ax2.pie(values, labels=labels, autopct='%1.1f%%',
                                          colors=colors_donut, startangle=90)
        
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
    else:
        ax2.text(0.5, 0.5, '🎉 No Downtime\nDetected!', ha='center', va='center', 
                transform=ax2.transAxes, fontsize=16, fontweight='bold', color='green')
    
    # 3. Member Productivity Ranking (Top Right)  
    ax3 = axes[0, 2]
    ax3.set_title("🏆 Productivity Ranking", fontsize=14, fontweight='bold')
    
    productivity_scores = []
    for member in members:
        member_data = detailed_data[member]
        total_active = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
        total_downtime = sum(p['duration_hours'] for p in member_data['downtime_periods'])
        
        if total_active + total_downtime > 0:
            productivity = (total_active / (total_active + total_downtime)) * 100
        else:
            productivity = 100 if total_active > 0 else 0
            
        productivity_scores.append(productivity)
    
    # Sort by productivity
    sorted_data = sorted(zip(members, productivity_scores), key=lambda x: x[1], reverse=True)
    sorted_members, sorted_scores = zip(*sorted_data)
    
    # Color bars based on score
    colors = ['#28a745' if score >= 80 else '#ffc107' if score >= 60 else '#dc3545' 
              for score in sorted_scores]
    
    bars = ax3.barh(range(len(sorted_members)), sorted_scores, color=colors, alpha=0.8, edgecolor='black')
    ax3.set_yticks(range(len(sorted_members)))
    ax3.set_yticklabels([m[:12] + "..." if len(m) > 12 else m for m in sorted_members])
    ax3.set_xlabel('Productivity Score (%)', fontweight='bold')
    ax3.set_xlim(0, 100)
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Add score labels
    for i, (bar, score) in enumerate(zip(bars, sorted_scores)):
        ax3.text(score + 1, i, f'{score:.0f}%', va='center', fontweight='bold')
    
    # 4. Timeline Heatmap (Bottom Left)
    ax4 = axes[1, 0]
    ax4.set_title("🕒 Activity Timeline Heatmap", fontsize=14, fontweight='bold')
    
    # Create 15-minute interval heatmap
    current_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    start_time = current_time.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    
    # 15-minute intervals from working hours start to current time
    intervals = []
    current_interval = start_time
    end_time = min(current_time, current_time.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0))
    while current_interval <= end_time:
        intervals.append(current_interval)
        current_interval += timedelta(minutes=15)
    
    heatmap_data = np.zeros((len(members), len(intervals)))
    
    for i, member in enumerate(members):
        member_data = detailed_data[member]
        
        for period in member_data['in_progress_periods']:
            if isinstance(period['start'], str):
                period_start = datetime.fromisoformat(period['start'])
                period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
            else:
                period_start = period['start']
                period_end = period['end']
            
            for j, interval_start in enumerate(intervals):
                interval_end = interval_start + timedelta(minutes=15)
                
                # Check overlap
                if period_start < interval_end and period_end > interval_start:
                    heatmap_data[i, j] = 1
    
    im = ax4.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', interpolation='nearest')
    ax4.set_yticks(range(len(members)))
    ax4.set_yticklabels([m[:10] + "..." if len(m) > 10 else m for m in members], fontsize=9)
    
    # Show every hour on x-axis
    hour_indices = [i for i, interval in enumerate(intervals) if interval.minute == 0]
    ax4.set_xticks(hour_indices)
    ax4.set_xticklabels([intervals[i].strftime('%H:%M') for i in hour_indices], rotation=45)
    ax4.set_xlabel('Time (15-min intervals)', fontweight='bold')
    
    # 5. Trend Analysis (Bottom Middle)
    ax5 = axes[1, 1]
    ax5.set_title("📈 Hourly Activity Trend", fontsize=14, fontweight='bold')
    
    # Calculate hourly activity levels for working hours
    hours = list(range(WORKDAY_START_HOUR, min(current_time.hour + 1, WORKDAY_END_HOUR + 1)))
    active_counts = []
    
    for hour in hours:
        active_in_hour = 0
        for member_data in detailed_data.values():
            for period in member_data['in_progress_periods']:
                if isinstance(period['start'], str):
                    period_start = datetime.fromisoformat(period['start'])
                    period_end = datetime.fromisoformat(period['end']) if isinstance(period['end'], str) else current_time
                else:
                    period_start = period['start']
                    period_end = period['end']
                
                hour_start = period_start.replace(hour=hour, minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                if period_start < hour_end and period_end > hour_start:
                    active_in_hour += 1
        
        active_counts.append(active_in_hour)
    
    ax5.plot(hours, active_counts, marker='o', linewidth=3, markersize=8, color='#17a2b8')
    ax5.fill_between(hours, active_counts, alpha=0.3, color='#17a2b8')
    ax5.set_xlabel('Hour of Day', fontweight='bold')
    ax5.set_ylabel('Active Members', fontweight='bold')
    ax5.set_xticks(hours)
    ax5.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45)
    ax5.grid(True, alpha=0.3)
    ax5.set_ylim(0, len(members) + 1)
    
    # Add trend line
    if len(hours) > 1:
        z = np.polyfit(hours, active_counts, 1)
        p = np.poly1d(z)
        ax5.plot(hours, p(hours), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend (slope: {z[0]:.2f})')
        ax5.legend()
    
    # 6. Summary Statistics (Bottom Right)
    ax6 = axes[1, 2]
    ax6.axis('off')
    ax6.set_title("📋 Key Metrics", fontsize=14, fontweight='bold')
    
    # Calculate comprehensive statistics
    total_members = len(members)
    members_with_downtime = sum(1 for member_data in detailed_data.values() 
                               if member_data['downtime_periods'])
    
    total_active_hours = sum(sum(p['duration_hours'] for p in member_data['in_progress_periods'])
                            for member_data in detailed_data.values())
    total_downtime_hours = sum(sum(p['duration_hours'] for p in member_data['downtime_periods'])
                              for member_data in detailed_data.values())
    
    avg_active = total_active_hours / total_members if total_members > 0 else 0
    avg_downtime = total_downtime_hours / total_members if total_members > 0 else 0
    
    # Find most/least productive
    if productivity_scores:
        most_productive = sorted_data[0]
        least_productive = sorted_data[-1]
    else:
        most_productive = ("N/A", 0)
        least_productive = ("N/A", 0)
    
    # Current status
    currently_inactive = sum(1 for member_data in detailed_data.values()
                           for period in member_data['downtime_periods']
                           if abs((datetime.fromisoformat(period['end']) if isinstance(period['end'], str) 
                                  else period['end'] - current_time).total_seconds()) < 300)
    
    stats_text = f"""
KEY PERFORMANCE METRICS (WORKING HOURS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 TEAM OVERVIEW
   Total Members: {total_members}
   With Downtime: {members_with_downtime}
   Currently Inactive: {currently_inactive}

⏱️ TIME ANALYSIS  
   Total Active Hours: {total_active_hours:.1f}h
   Total Downtime: {total_downtime_hours:.1f}h
   Avg Active/Person: {avg_active:.1f}h
   Avg Downtime/Person: {avg_downtime:.1f}h

🏆 PERFORMANCE LEADERS
   Most Productive: 
   {most_productive[0][:15]} ({most_productive[1]:.0f}%)
   
   Needs Attention:
   {least_productive[0][:15]} ({least_productive[1]:.0f}%)

📊 EFFICIENCY METRICS
   Team Efficiency: {(total_active_hours/(total_active_hours + total_downtime_hours)*100) if (total_active_hours + total_downtime_hours) > 0 else 0:.1f}%
   Active Members: {total_members - members_with_downtime}/{total_members}
   Working Hours: {WORKDAY_START_HOUR}:00-{WORKDAY_END_HOUR}:00
   
⚠️ ALERTS
   Critical Issues: {sum(1 for member_data in detailed_data.values() if sum(p['duration_hours'] for p in member_data['downtime_periods']) >= 3)}
   """
    
    ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, fontsize=11, 
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"📊 Detailed analysis charts saved to: {save_path}")
    
    return fig

# MODIFIED main function to integrate working hours analysis
def main():
    """Enhanced main function with better error handling and user experience"""
    print("🚀 ClickUp Enhanced Downtime Analysis & Watcher Management")
    print("=" * 70)
    
    # Get team info with error handling
    try:
        print("🔗 Connecting to ClickUp API...")
        team_id = get_team_id()
        members = get_team_members(team_id)
        print(f"✅ Connected successfully!")
        print(f"🏢 Team ID: {team_id}")
        print(f"👥 Team members: {len(members)}")
        
        # Show team members
        print(f"\n👥 Team Members:")
        for i, member in enumerate(members, 1):
            user = member.get('user', {})
            username = user.get('username', 'N/A')
            email = user.get('email', 'N/A')
            print(f"   {i:2d}. {username} ({email})")
            
    except Exception as e:
        print(f"❌ Error connecting to ClickUp: {e}")
        print("🔧 Please check your API token and try again.")
        return
    
    # Enhanced interactive menu
    print(f"\n🔧 What would you like to do?")
    print("1. 📊 Analyze member downtime (working hours only)")
    print("2. 👁️  Add Sean as watcher to all recent tasks")
    print("3. 🎯 Add custom person as watcher to tasks")
    print("4. 🚀 Both downtime analysis and add watchers")
    print("5. 📈 Create visualizations from existing JSON file")
    print("6. 🔄 Retry failed watcher operations")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice not in ['1', '2', '3', '4', '5', '6']:
        print("❌ Invalid choice. Please run again and select 1-6.")
        return
    
    # Handle visualization from existing file
    if choice == '5':
        json_file = input("Enter the path to your JSON file: ").strip()
        if not json_file:
            # Look for recent files
            import glob
            json_files = glob.glob("clickup_*.json")
            if json_files:
                latest_file = max(json_files, key=lambda x: x.split('_')[-1])
                print(f"🔍 Found recent file: {latest_file}")
                use_latest = input("Use this file? (y/n, default: y): ").strip().lower()
                if use_latest != 'n':
                    json_file = latest_file
            
            if not json_file:
                print("❌ No JSON file specified or found.")
                return
        
        load_and_visualize_data(json_file)
        return
    
    # Handle retry operations
    if choice == '6':
        # Load previous failed operations
        try:
            with open('failed_watcher_operations.json', 'r') as f:
                failed_data = json.load(f)
            failed_tasks = failed_data.get('failed_tasks', [])
            watcher_info = failed_data.get('watcher_info', {})
            
            if not failed_tasks:
                print("✅ No failed operations found to retry.")
                return
            
            print(f"🔄 Found {len(failed_tasks)} failed watcher operations")
            watcher_user_id = watcher_info.get('user_id')
            watcher_name = watcher_info.get('name', 'Unknown')
            
            retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name)
            
        except FileNotFoundError:
            print("❌ No previous failed operations found.")
        except Exception as e:
            print(f"❌ Error loading failed operations: {e}")
        return
    
    # Handle watcher functionality (choices 2, 3, 4)
    watcher_results = {}
    if choice in ['2', '3', '4']:
        print(f"\n👁️ WATCHER MANAGEMENT")
        print("=" * 30)
        
        # Get date range for tasks
        days_back_input = input("How many days back to look for tasks? (default: 7): ").strip()
        try:
            days_back = int(days_back_input) if days_back_input else 7
        except ValueError:
            days_back = 7
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        print(f"📅 Working with period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Find watcher user
        if choice == '2':
            watcher_name = 'sean'
        else:
            watcher_name = input("Enter the name/username of person to add as watcher: ").strip()
        
        watcher_user = find_user_by_name(members, watcher_name)
        if not watcher_user:
            print(f"❌ Could not find user '{watcher_name}' in the team")
            print("Available users:")
            for member in members:
                user = member.get('user', {})
                print(f"   - {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
            return
        
        watcher_user_id = watcher_user['id']
        watcher_username = watcher_user['username']
        print(f"👁️ Found watcher: {watcher_username} (ID: {watcher_user_id})")
        
        # Enhanced configuration options
        print(f"\n🔧 CONFIGURATION OPTIONS")
        debug_mode_input = input("Enable debug mode for comprehensive API testing? (y/n, default: n): ").strip().lower()
        debug_mode = debug_mode_input == 'y'
        
        dry_run_input = input("Do a dry run first (recommended)? (y/n, default: y): ").strip().lower()
        dry_run = dry_run_input != 'n'
        
        batch_size_input = input("Process in batches? Enter batch size (default: all at once): ").strip()
        batch_size = int(batch_size_input) if batch_size_input.isdigit() else None
        
        # Collect all tasks from all members
        all_tasks = []
        print(f"\n📋 Collecting tasks from all team members...")
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            print(f"   [{i+1:2d}/{len(members)}] Getting tasks for {user_name}...")
            
            try:
                tasks = get_member_tasks_with_date_range(team_id, user_id, days_back)
                all_tasks.extend(tasks)
                print(f"      📋 Found {len(tasks)} tasks")
            except Exception as e:
                print(f"      ❌ Error getting tasks: {e}")
            
            if i < len(members) - 1:
                time.sleep(2)  # Rate limiting
        
        # Remove duplicates
        unique_tasks = {}
        for task in all_tasks:
            unique_tasks[task['id']] = task
        
        unique_task_list = list(unique_tasks.values())
        print(f"📊 Found {len(unique_task_list)} unique tasks across all members")
        
        if len(unique_task_list) == 0:
            print("❌ No tasks found to add watchers to")
        else:
            # Process tasks
            if batch_size and len(unique_task_list) > batch_size:
                print(f"🔄 Processing in batches of {batch_size}...")
                
                all_success = 0
                all_failed = 0 
                all_failed_tasks = []
                
                for batch_start in range(0, len(unique_task_list), batch_size):
                    batch_end = min(batch_start + batch_size, len(unique_task_list))
                    batch_tasks = unique_task_list[batch_start:batch_end]
                    
                    print(f"\n📦 Processing batch {batch_start//batch_size + 1}: tasks {batch_start+1}-{batch_end}")
                    success, failed, failed_tasks = add_watcher_to_all_tasks(
                        batch_tasks, watcher_user_id, watcher_username, dry_run, debug_mode)
                    
                    all_success += success
                    all_failed += failed
                    all_failed_tasks.extend(failed_tasks)
                    
                    if batch_end < len(unique_task_list):
                        print("⏳ Pausing between batches...")
                        time.sleep(5)
                
                success_count, failed_count, failed_tasks = all_success, all_failed, all_failed_tasks
            else:
                success_count, failed_count, failed_tasks = add_watcher_to_all_tasks(
                    unique_task_list, watcher_user_id, watcher_username, dry_run, debug_mode)
            
            # Handle dry run confirmation
            if dry_run and success_count > 0:
                confirm = input(f"\n🤔 Proceed with actually adding {watcher_username} to {len(unique_task_list)} tasks? (y/n): ").strip().lower()
                if confirm == 'y':
                    print(f"\n🚀 Proceeding with actual watcher addition...")
                    success_count, failed_count, failed_tasks = add_watcher_to_all_tasks(
                        unique_task_list, watcher_user_id, watcher_username, dry_run=False, debug_mode=debug_mode)
            
            # Store results and save failed tasks for retry
            watcher_results = {
                'watcher_name': watcher_username,
                'watcher_user_id': watcher_user_id,
                'total_attempts': len(unique_task_list),
                'successful': success_count,
                'failed': failed_count,
                'failed_tasks': failed_tasks
            }
            
            if failed_tasks:
                # Save failed tasks for potential retry
                failed_data = {
                    'failed_tasks': failed_tasks,
                    'watcher_info': {
                        'user_id': watcher_user_id,
                        'name': watcher_username
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    with open('failed_watcher_operations.json', 'w') as f:
                        json.dump(failed_data, f, indent=2, default=str)
                    print(f"💾 Failed operations saved for retry (use option 6)")
                except Exception as e:
                    print(f"⚠️ Could not save failed operations: {e}")
                
                # Ask if user wants to retry immediately
                if failed_count > 0:
                    retry_now = input(f"\n🔄 Retry {failed_count} failed operations now? (y/n): ").strip().lower()
                    if retry_now == 'y':
                        retry_success, still_failed = retry_failed_watchers(failed_tasks, watcher_user_id, watcher_username)
                        watcher_results['retry_successful'] = retry_success
                        watcher_results['still_failed'] = len(still_failed)
    
    # Handle downtime analysis (choices 1, 4) - MODIFIED FOR WORKING HOURS
    if choice in ['1', '4']:
        print(f"\n📊 DOWNTIME ANALYSIS (WORKING HOURS ONLY)")
        print("=" * 50)
        print(f"🕘 Working Hours: {WORKDAY_START_HOUR}:00 AM - {WORKDAY_END_HOUR}:00 PM")
        print(f"🍽️ Lunch Break: {LUNCH_BREAK_START}:00 - {LUNCH_BREAK_END}:30")
        print(f"⏱️  Daily Working Hours: {WORKING_HOURS_PER_DAY} hours")
        
        # Get today's timestamps
        start_ts, current_ts, today_start, current_time = get_today_timestamps()
        print(f"📅 Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
        print(f"⏰ Current time: {current_time.strftime('%H:%M:%S')}")
        
        # Check if we're currently in working hours
        current_hour = current_time.hour + current_time.minute / 60.0
        if current_hour < WORKDAY_START_HOUR:
            print(f"⏰ Work hasn't started yet (starts at {WORKDAY_START_HOUR}:00 AM)")
        elif current_hour >= WORKDAY_END_HOUR:
            print(f"⏰ Work day has ended (ended at {WORKDAY_END_HOUR}:00 PM)")
        elif LUNCH_BREAK_START <= current_hour < LUNCH_BREAK_END:
            print(f"🍽️ Currently in lunch break ({LUNCH_BREAK_START}:00 - {LUNCH_BREAK_END}:30)")
        else:
            print(f"✅ Currently in working hours")
        
        members_with_downtime = []
        all_member_data = {}
        
        # Analyze each team member with progress tracking
        print(f"\n🔍 Analyzing {len(members)} team members (working hours only)...")
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            
            print(f"\n{'=' * 60}")
            print(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
            print('=' * 60)
            
            try:
                # Get member's tasks
                print("  📋 Fetching tasks...")
                tasks = get_member_tasks(team_id, user_id)
                print(f"  ✅ Found {len(tasks)} open tasks")
                
                if not tasks:
                    # No tasks = full downtime if it's been 1+ hours since work started (reduced threshold)
                    workday_start = today_start.replace(hour=WORKDAY_START_HOUR)
                    workday_end = today_start.replace(hour=WORKDAY_END_HOUR)
                    analysis_time = min(current_time, workday_end)
                    
                    if analysis_time > workday_start:
                        # Calculate working hours missed (excluding lunch)
                        total_work_minutes = 0
                        
                        # Morning work (9 AM - 12 PM)
                        morning_end = min(analysis_time, today_start.replace(hour=LUNCH_BREAK_START))
                        if morning_end > workday_start:
                            total_work_minutes += (morning_end - workday_start).total_seconds() / 60
                        
                        # Afternoon work (12:30 PM - current time)
                        if analysis_time > today_start.replace(hour=LUNCH_BREAK_START, minute=30):
                            afternoon_start = today_start.replace(hour=LUNCH_BREAK_START, minute=30)
                            afternoon_end = analysis_time
                            total_work_minutes += (afternoon_end - afternoon_start).total_seconds() / 60
                        
                        hours_missed = total_work_minutes / 60
                        
                        if hours_missed >= 1:  # Reduced threshold for working hours
                            downtime_periods = [{
                                'start': workday_start,
                                'end': analysis_time,
                                'duration_hours': hours_missed,
                                'type': 'no_tasks'
                            }]
                            members_with_downtime.append(user_name)
                            all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': downtime_periods}
                            print(f"  🔴 NO TASKS ASSIGNED: {hours_missed:.1f} hours of downtime")
                        else:
                            all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
                            print(f"  ✅ No tasks but within acceptable range")
                    else:
                        all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
                        print(f"  ✅ Work day hasn't started yet")
                else:
                    # Analyze task activity
                    print("  🔍 Analyzing task activity patterns...")
                    in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
                    print(f"  📊 Found {len(in_progress_periods)} active periods today")
                    
                    # Calculate downtime during working hours
                    print("  ⏱️  Calculating downtime periods (working hours)...")
                    downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
                    all_member_data[user_name] = {
                        'in_progress_periods': in_progress_periods,
                        'downtime_periods': downtime_periods
                    }
                    
                    if downtime_periods:
                        members_with_downtime.append(user_name)
                        total_downtime = sum(p['duration_hours'] for p in downtime_periods)
                        print(f"  🔴 DOWNTIME DETECTED: {total_downtime:.1f} total hours")
                        
                        # Show breakdown
                        for j, period in enumerate(downtime_periods, 1):
                            start_time_str = period['start'].strftime('%H:%M')
                            end_time_str = period['end'].strftime('%H:%M') if period['end'] != current_time else "NOW"
                            print(f"    {j}. {start_time_str} - {end_time_str} ({period['duration_hours']:.1f}h) [{period['type']}]")
                    else:
                        print(f"  ✅ No significant downtime detected (active day)")
                        
            except Exception as e:
                print(f"  ❌ Error analyzing {user_name}: {e}")
                all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
            
            # Progress indicator
            progress = ((i + 1) / len(members)) * 100
            print(f"  📈 Progress: {progress:.0f}% complete")
            
            # Rate limiting between members
            if i < len(members) - 1:
                print("  ⏱️ Rate limiting pause...")
                time.sleep(3)
        
        # Generate comprehensive final summary (working hours focused)
        print(f"\n{'='*70}")
        print(f"📊 WORKING HOURS DOWNTIME SUMMARY")
        print(f"📅 {current_time.strftime('%A, %B %d, %Y')} at {current_time.strftime('%H:%M')}")
        print(f"🕘 Working Hours: {WORKDAY_START_HOUR}:00 AM - {WORKDAY_END_HOUR}:00 PM (excluding lunch)")
        print('='*70)
        
        if not members_with_downtime:
            print("🎉 EXCELLENT! ALL TEAM MEMBERS ARE PRODUCTIVE!")
            print("   ✅ No significant downtime during working hours.")
            print("   🏆 Team is performing optimally within business hours.")
        else:
            print(f"🚨 ATTENTION: {len(members_with_downtime)} MEMBER(S) WITH WORKING HOURS DOWNTIME")
            
            # Categorize by severity (adjusted for working hours)
            critical_members = []  # 3+ hours
            moderate_members = []  # 1-3 hours
            
            for member_name in members_with_downtime:
                data = all_member_data[member_name]
                total_downtime = sum(p['duration_hours'] for p in data['downtime_periods'])
                
                if total_downtime >= 3:
                    critical_members.append((member_name, total_downtime))
                else:
                    moderate_members.append((member_name, total_downtime))
            
            # Display by severity
            if critical_members:
                print(f"\n🆘 CRITICAL (3+ hours downtime): {len(critical_members)} members")
                for member, hours in critical_members:
                    percentage = (hours / WORKING_HOURS_PER_DAY) * 100
                    print(f"   💀 {member}: {hours:.1f}h ({percentage:.0f}% of work day) - IMMEDIATE ACTION REQUIRED")
            
            if moderate_members:
                print(f"\n⚠️ MODERATE (1-3 hours downtime): {len(moderate_members)} members")
                for member, hours in moderate_members:
                    percentage = (hours / WORKING_HOURS_PER_DAY) * 100
                    print(f"   ⚠️ {member}: {hours:.1f}h ({percentage:.0f}% of work day) - MONITOR CLOSELY")
            
            # Show currently inactive members
            currently_inactive = []
            for member_name, data in all_member_data.items():
                for period in data['downtime_periods']:
                    if abs((period['end'] - current_time).total_seconds()) < 300:  # Within 5 minutes of now
                        currently_inactive.append(member_name)
                        break
            
            if currently_inactive:
                print(f"\n🔥 CURRENTLY INACTIVE ({len(currently_inactive)} members):")
                for member in currently_inactive:
                    data = all_member_data[member]
                    current_period = None
                    for period in data['downtime_periods']:
                        if abs((period['end'] - current_time).total_seconds()) < 300:
                            current_period = period
                            break
                    
                    if current_period:
                        inactive_duration = (current_time - current_period['start']).total_seconds() / 3600
                        print(f"    {member}: inactive for {inactive_duration:.1f} hours (since {current_period['start'].strftime('%H:%M')})")
        
        # Working hours statistics
        total_possible_hours = len(members) * WORKING_HOURS_PER_DAY
        total_active_time = sum(sum(p['duration_hours'] for p in data['in_progress_periods']) 
                               for data in all_member_data.values())
        total_downtime_time = sum(sum(p['duration_hours'] for p in data['downtime_periods']) 
                                 for data in all_member_data.values())
        
        team_utilization = (total_active_time / total_possible_hours) * 100 if total_possible_hours > 0 else 0
        
        print(f"\n📊 WORKING HOURS TEAM METRICS:")
        print(f"   ⏰ Analysis time: {current_time.strftime('%H:%M')}")
        print(f"   👥 Total members: {len(members)}")
        print(f"   ✅ Productive members: {len(members) - len(members_with_downtime)}")
        print(f"   ⚠️ Members with downtime: {len(members_with_downtime)}")
        print(f"   📈 Team utilization: {team_utilization:.1f}%")
        print(f"   ⚡ Total active hours: {total_active_time:.1f}h")
        print(f"   🔻 Total downtime: {total_downtime_time:.1f}h")
        print(f"   🎯 Possible work hours today: {total_possible_hours:.1f}h")
        
        # Save results with working hours focus
        results = {
            'timestamp': current_time.isoformat(),
            'date': current_time.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'working_hours_config': {
                'start_hour': WORKDAY_START_HOUR,
                'end_hour': WORKDAY_END_HOUR,
                'lunch_start': LUNCH_BREAK_START,
                'lunch_end': LUNCH_BREAK_END,
                'daily_hours': WORKING_HOURS_PER_DAY
            },
            'members_analyzed': len(members),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'detailed_data': all_member_data,
            'team_metrics': {
                'total_active_hours': total_active_time,
                'total_downtime_hours': total_downtime_time,
                'team_utilization': team_utilization,
                'total_possible_hours': total_possible_hours,
                'currently_inactive': currently_inactive if 'currently_inactive' in locals() else []
            }
        }
        
        # Add watcher results if available
        if watcher_results:
            results['watcher_management'] = watcher_results
        
        filename = f"clickup_working_hours_{current_time.strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Working hours analysis saved to: {filename}")
            
            # Ask about visualizations
            create_viz = input(f"\n🎨 Create stacked timeline visualization? (y/n, default: y): ").strip().lower()
            if create_viz != 'n':
                print(f"\n📊 Creating stacked timeline visualization for working hours...")
                try:
                    timeline_fig = create_enhanced_timeline_visualization(results)
                    analysis_fig = create_detailed_analysis_charts(results)
                    plt.show()
                    print(f"✅ Stacked visualization created successfully!")
                    
                    save_viz = input("💾 Save visualizations to files? (y/n, default: y): ").strip().lower()
                    if save_viz != 'n':
                        timeline_filename = f"timeline_stacked_{current_time.strftime('%Y%m%d_%H%M')}.png"
                        analysis_filename = f"analysis_{current_time.strftime('%Y%m%d_%H%M')}.png"
                        timeline_fig.savefig(timeline_filename, dpi=300, bbox_inches='tight')
                        analysis_fig.savefig(analysis_filename, dpi=300, bbox_inches='tight')
                        print(f"📊 Saved: {timeline_filename}, {analysis_filename}")
                        
                except Exception as e:
                    print(f"❌ Error creating stacked visualization: {e}")
                    
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    # Final summary
    print(f"\n🎯 OPERATION COMPLETE!")
    print("=" * 30)
    
    if choice in ['2', '3', '4'] and watcher_results:
        print(f"👁️ Watcher Management Summary:")
        print(f"   • Target: {watcher_results['watcher_name']}")
        print(f"   • Tasks processed: {watcher_results['total_attempts']}")
        print(f"   • Successful: {watcher_results['successful']}")
        print(f"   • Failed: {watcher_results['failed']}")
        if watcher_results.get('retry_successful'):
            print(f"   • Retry successful: {watcher_results['retry_successful']}")
    
    if choice in ['1', '4']:
        print(f"📊 Downtime Analysis Summary:")
        print(f"   • Members analyzed: {len(members)}")
        print(f"   • With downtime: {len(members_with_downtime)}")
        print(f"   • Analysis saved: {filename if 'filename' in locals() else 'N/A'}")
    
    print(f"\n💡 Tips for next time:")
    print(f"   • Run analysis regularly for trend monitoring")
    print(f"   • Focus on working hours for accurate productivity metrics")
    print(f"   • Use stacked timeline to see task overlap patterns")
    
    print(f"\n✨ Thank you for using ClickUp Enhanced Manager!")

if __name__ == "__main__":
    main()