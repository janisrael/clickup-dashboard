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
import warnings

# Suppress emoji/glyph warnings
warnings.filterwarnings('ignore', message='Glyph .* missing from font.*')

# API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' 
API_TOKEN = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K' # Tricia
HEADERS = {'Authorization': API_TOKEN}
BASE_URL = 'https://api.clickup.com/api/v2'

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

def find_in_progress_periods_today(tasks, today_start, current_time):
    """Find all periods when user had in-progress tasks today"""
    in_progress_periods = []
    
    print(f"    Analyzing {len(tasks)} tasks for in-progress periods...")
    
    # Check current status first
    currently_in_progress = []
    for task in tasks:
        if is_task_in_progress(task):
            currently_in_progress.append(task)
            print(f"      [OK] Currently in progress: {task['name'][:50]}")
    
    # If tasks are currently in progress, we need to find when they started
    for task in currently_in_progress:
        task_updated = datetime.fromtimestamp(int(task.get('date_updated', 0)) / 1000)
        
        # If task was updated today, use that as start time
        if task_updated.date() == current_time.date():
            period_start = task_updated
        else:
            # Task was already in progress from start of day
            period_start = today_start.replace(hour=9)  # Assume 9 AM work start
        
        duration_delta = current_time - period_start
        in_progress_periods.append({
            'start': period_start,
            'end': current_time,
            'task_name': task['name'],
            'duration_hours': duration_delta.total_seconds() / 3600
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
                        
                        duration_delta = period_end - activity_time
                        duration = duration_delta.total_seconds() / 3600
                        if duration > 0.1:  # At least 6 minutes
                            in_progress_periods.append({
                                'start': activity_time,
                                'end': period_end,
                                'task_name': task['name'],
                                'duration_hours': duration
                            })
                            
                            print(f"        [DATE] Found period: {activity_time.strftime('%H:%M')} - "
                                  f"{period_end.strftime('%H:%M')} ({duration:.1f}h)")
        
        time.sleep(1)  # Rate limit prevention
    
    # Sort and merge overlapping periods
    in_progress_periods.sort(key=lambda x: x['start'])
    merged_periods = []
    
    for period in in_progress_periods:
        if not merged_periods:
            merged_periods.append(period)
        else:
            last_period = merged_periods[-1]
            # If periods overlap or are close together (within 30 minutes)
            if period['start'] <= last_period['end'] + timedelta(minutes=30):
                # Merge periods
                last_period['end'] = max(last_period['end'], period['end'])
                duration_delta = last_period['end'] - last_period['start']
                last_period['duration_hours'] = duration_delta.total_seconds() / 3600
                if period['task_name'] not in last_period['task_name']:
                    last_period['task_name'] += f", {period['task_name']}"
            else:
                merged_periods.append(period)
    
    return merged_periods

def calculate_downtime_today(member_name, in_progress_periods, today_start, current_time):
    """Calculate downtime periods of 3+ hours for today"""
    print(f"    Calculating downtime for {member_name}...")
    
    
    workday_start = today_start.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM
    downtime_periods = []
    
    if not in_progress_periods:
        # No in-progress periods at all today
        if current_time > workday_start:
            duration_delta = current_time - workday_start
            hours_inactive = duration_delta.total_seconds() / 3600
            if hours_inactive >= 3:
                downtime_periods.append({
                    'start': workday_start,
                    'end': current_time,
                    'duration_hours': hours_inactive,
                    'type': 'no_activity_all_day'
                })
                print(f"      [RED] No activity all day: {hours_inactive:.1f} hours")
    else:
        # Check gap from workday start to first activity
        first_activity = in_progress_periods[0]['start']
        if first_activity > workday_start:
            gap_delta = first_activity - workday_start
            gap_hours = gap_delta.total_seconds() / 3600
            if gap_hours >= 3:
                downtime_periods.append({
                    'start': workday_start,
                    'end': first_activity,
                    'duration_hours': gap_hours,
                    'type': 'late_start'
                })
                print(f"      [RED] Late start: {gap_hours:.1f} hours")
        
        # Check gaps between activities
        for i in range(len(in_progress_periods) - 1):
            gap_start = in_progress_periods[i]['end']
            gap_end = in_progress_periods[i + 1]['start']
            gap_delta = gap_end - gap_start
            gap_hours = gap_delta.total_seconds() / 3600
            
            if gap_hours >= 3:
                downtime_periods.append({
                    'start': gap_start,
                    'end': gap_end,
                    'duration_hours': gap_hours,
                    'type': 'midday_gap'
                })
                print(f"      [RED] Midday gap: {gap_hours:.1f} hours")
        
        # Check gap from last activity to now
        last_activity = in_progress_periods[-1]['end']
        current_gap_delta = current_time - last_activity
        current_gap_hours = current_gap_delta.total_seconds() / 3600
        if current_gap_hours >= 3:
            downtime_periods.append({
                'start': last_activity,
                'end': current_time,
                'duration_hours': current_gap_hours,
                'type': 'current_inactive'
            })
            print(f"      [RED] CURRENTLY INACTIVE: {current_gap_hours:.1f} hours since last activity")
    
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
            print(f"      [WARN] Task {task_id} not found or no access")
        elif resp.status_code == 401:
            print(f"      [WARN] No permission to access task {task_id}")
        else:
            print(f"      [WARN] Error {resp.status_code} accessing task {task_id}")
        return None
    except Exception as e:
        print(f"      [ERROR] Exception getting task details: {e}")
        return None

def debug_watcher_api(task_id, user_id, user_name):
    """Enhanced debug function to test all API endpoints systematically"""
    print(f"    [DEBUG] Testing watcher API for task {task_id} and user {user_name}...")
    
    # Get task details first
    task_details = get_task_details(task_id)
    if task_details:
        task_name = task_details.get('name', 'Unknown')[:50]
        print(f"      [TASK] Task: {task_name}")
        current_watchers = task_details.get('watchers', [])
        print(f"      [WATCH] Current watchers: {len(current_watchers)}")
        
        # Check if user is already a watcher
        watcher_ids = [str(w.get('id', '')) for w in current_watchers if w.get('id')]
        if str(user_id) in watcher_ids:
            print(f"      [OK] {user_name} is already watching this task!")
            return True
        
        # Show current watchers
        for watcher in current_watchers:
            watcher_user = watcher.get('user', {})
            watcher_name = watcher_user.get('username', 'Unknown')
            print(f"         - {watcher_name}")
    else:
        print(f"      [ERROR] Cannot access task {task_id}")
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
            print(f"      [TEST] Method {i}: {method_info['name']}")
            
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
                print(f"      [OK] SUCCESS! Method {i} worked!")
                
                # Verify the watcher was actually added
                time.sleep(1)
                updated_task = get_task_details(task_id)
                if updated_task:
                    updated_watchers = updated_task.get('watchers', [])
                    updated_watcher_ids = [str(w.get('id', '')) for w in updated_watchers if w.get('id')]
                    if str(user_id) in updated_watcher_ids:
                        print(f"      [OK] VERIFIED: {user_name} successfully added as watcher!")
                        return True
                    else:
                        print(f"      [WARN] API returned 200 but user not found in watchers list")
                else:
                    print(f"      [WARN] Cannot verify - task details unavailable")
                
                return True
                
            elif resp.status_code in [400, 404, 403, 401]:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('err', error_data.get('error', 'Unknown error'))
                    print(f"         Error: {error_msg}")
                    
                    # Check for specific error conditions
                    if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        print(f"      [OK] User already watching (error message confirms)")
                        return True
                except:
                    print(f"         Raw response: {resp.text[:200]}")
            else:
                print(f"         Unexpected status: {resp.status_code}")
                
        except Exception as e:
            print(f"         Exception: {str(e)[:100]}")
        
        # Small delay between attempts
        time.sleep(0.5)
    
    print(f"      [ERROR] All {len(test_methods)} methods failed for {user_name}")
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
            print(f"      [OK] Added {user_name} as watcher")
            return True
        elif resp.status_code == 400:
            # Check if user is already a watcher
            error_msg = resp.json().get('err', '')
            if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"      [INFO] {user_name} already watching")
                return True
        
        # Method 2: POST with user_id in path
        url = f"{BASE_URL}/task/{task_id}/watcher/{user_id}"
        resp = requests.post(url, headers=HEADERS)
        
        if resp.status_code == 200:
            print(f"      [OK] Added {user_name} as watcher (method 2)")
            return True
        
        # If both quick methods fail, use debug mode
        print(f"      [TOOL] Standard methods failed, trying debug mode...")
        return debug_watcher_api(task_id, user_id, user_name)
            
    except Exception as e:
        print(f"      [ERROR] Error adding {user_name} as watcher: {e}")
        return False

def add_watcher_to_all_tasks(tasks, watcher_user_id, watcher_name, dry_run=False, debug_mode=False):
    """Add a watcher to multiple tasks with progress tracking"""
    print(f"\n[WATCH] {'[DRY RUN] ' if dry_run else ''}Adding {watcher_name} as watcher to {len(tasks)} tasks...")
    
    if debug_mode:
        print(f"[DEBUG] Debug mode enabled - using comprehensive API testing")
    
    success_count = 0
    failed_count = 0
    already_watching_count = 0
    failed_tasks = []
    
    for i, task in enumerate(tasks, 1):
        task_id = task['id']
        task_name = task['name'][:50] + "..." if len(task['name']) > 50 else task['name']
        
        print(f"\n   [{i:3d}/{len(tasks)}] {task_name}")
        
        if dry_run:
            print(f"      [DEBUG] [DRY RUN] Would add {watcher_name} as watcher")
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
    
    print(f"\n[CHART] Watcher Addition Summary:")
    print(f"   [OK] Successful: {success_count}")
    
    if not dry_run:
        print(f"   [ERROR] Failed: {failed_count}")
        
        if failed_tasks:
            print(f"\n[ALERT] Failed Tasks (for retry):")
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

def safe_datetime_from_iso(date_string):
    """Safely convert ISO string to datetime object"""
    try:
        if isinstance(date_string, str):
            # Handle different ISO formats
            if date_string.endswith('Z'):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_string)
        elif isinstance(date_string, datetime):
            return date_string
        else:
            return datetime.now()
    except Exception as e:
        print(f"    [WARN] Error parsing datetime {date_string}: {e}")
        return datetime.now()

def clean_text_for_plot(text):
    """Remove or replace problematic characters for plotting"""
    emoji_replacements = {
        '📊': '[CHART]',
        '🚨': '[ALERT]',
        '🟢': '[GREEN]',
        '🟡': '[YELLOW]',
        '🔴': '[RED]',
        '🆘': '[SOS]',
        '✅': '[OK]',
        '🎯': '[TARGET]',
        '📈': '[TREND]',
        '👥': '[USERS]',
        '⏱️': '[TIMER]',
        '🕒': '[CLOCK]',
        '📅': '[CALENDAR]',
        '🔻': '[DOWN]',
        '🔥': '[FIRE]'
    }
    
    for emoji, replacement in emoji_replacements.items():
        text = text.replace(emoji, replacement)
    
    return text

def create_enhanced_timeline_visualization(data, save_path="clickup_timeline_enhanced.png"):
    """Create an enhanced timeline visualization with better interactivity and fixed datetime handling"""
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
    
    # Enhanced color scheme
    colors = {
        'active': '#28a745',      # Bootstrap success green
        'downtime': '#dc3545',    # Bootstrap danger red
        'warning': '#ffc107',     # Bootstrap warning yellow
        'info': '#17a2b8',        # Bootstrap info blue
        'no_activity': '#6c757d'  # Bootstrap secondary gray
    }
    
    # 1. MAIN TIMELINE
    title_text = clean_text_for_plot(f"[CHART] Team Activity Timeline - {data['date']}")
    ax_timeline.set_title(title_text, fontsize=18, fontweight='bold', pad=20)
    
    y_positions = range(len(members))
    ax_timeline.set_yticks(y_positions)
    ax_timeline.set_yticklabels(members, fontsize=12)
    
    # Parse timestamps with safe conversion
    current_time = safe_datetime_from_iso(data['timestamp'])
    start_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Track member status for other charts
    member_stats = {}
    
    for i, member in enumerate(members):
        member_data = detailed_data[member]
        total_downtime = sum(p['duration_hours'] for p in member_data['downtime_periods'])
        total_active = sum(p['duration_hours'] for p in member_data['in_progress_periods'])
        
        member_stats[member] = {
            'total_downtime': total_downtime,
            'total_active': total_active,
            'status': 'critical' if total_downtime >= 4 else 'warning' if total_downtime >= 3 else 'good'
        }
        
        # Draw active periods
        for period in member_data['in_progress_periods']:
            period_start = safe_datetime_from_iso(period['start'])
            period_end = safe_datetime_from_iso(period['end']) if period['end'] != current_time else current_time
            
            rect = Rectangle((mdates.date2num(period_start), i - 0.35), 
                           mdates.date2num(period_end) - mdates.date2num(period_start), 0.7,
                           facecolor=colors['active'], alpha=0.8, edgecolor='darkgreen', linewidth=1)
            ax_timeline.add_patch(rect)
            
            # Add task name with better formatting
            duration_delta = period_end - period_start
            mid_time = period_start + duration_delta / 2
            task_name = period['task_name'][:25] + "..." if len(period['task_name']) > 25 else period['task_name']
            ax_timeline.text(mdates.date2num(mid_time), i, task_name, 
                           ha='center', va='center', fontsize=9, fontweight='bold', 
                           color='white', bbox=dict(boxstyle="round,pad=0.2", facecolor='darkgreen', alpha=0.7))
        
        # Draw downtime periods with different colors based on severity
        for period in member_data['downtime_periods']:
            period_start = safe_datetime_from_iso(period['start'])
            period_end = safe_datetime_from_iso(period['end']) if period['end'] != current_time else current_time
            
            # Color based on duration and type
            duration = period['duration_hours']
            if duration >= 6:
                color = colors['no_activity']  # Very severe
            elif duration >= 4:
                color = colors['downtime']     # Severe  
            else:
                color = colors['warning']      # Moderate
            
            rect = Rectangle((mdates.date2num(period_start), i - 0.35), 
                           mdates.date2num(period_end) - mdates.date2num(period_start), 0.7,
                           facecolor=color, alpha=0.9, edgecolor='darkred', linewidth=1)
            ax_timeline.add_patch(rect)
            
            # Add downtime info
            duration_delta = period_end - period_start
            mid_time = period_start + duration_delta / 2
            duration_text = f"[ALERT] {duration:.1f}h"
            if period['end'] == current_time:
                duration_text += " (NOW)"
            
            ax_timeline.text(mdates.date2num(mid_time), i, duration_text, 
                           ha='center', va='center', fontsize=10, fontweight='bold', 
                           color='white', bbox=dict(boxstyle="round,pad=0.3", facecolor='darkred', alpha=0.8))
    
    # Format timeline x-axis
    ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax_timeline.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax_timeline.set_xlim(mdates.date2num(start_time), mdates.date2num(current_time))
    ax_timeline.grid(True, alpha=0.3, linestyle='--')
    ax_timeline.set_xlabel("Time of Day", fontsize=12, fontweight='bold')
    
    # Enhanced legend
    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=colors['active'], label='[GREEN] Active Period'),
        Rectangle((0, 0), 1, 1, facecolor=colors['warning'], label='[YELLOW] Moderate Downtime (3-4h)'),
        Rectangle((0, 0), 1, 1, facecolor=colors['downtime'], label='[RED] Severe Downtime (4-6h)'),
        Rectangle((0, 0), 1, 1, facecolor=colors['no_activity'], label='[BLACK] Critical Downtime (6+h)')
    ]
    ax_timeline.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # 2. STATUS BARS
    ax_status.set_title("[LIGHTNING] Current Member Status", fontsize=14, fontweight='bold')
    
    status_colors = []
    status_labels = []
    downtime_values = []
    
    for member in members:
        stats = member_stats[member]
        downtime_values.append(stats['total_downtime'])
        
        if stats['status'] == 'critical':
            status_colors.append(colors['no_activity'])
            status_labels.append(f"{member[:15]} [SOS]")
        elif stats['status'] == 'warning':
            status_colors.append(colors['downtime'])
            status_labels.append(f"{member[:15]} [WARN]")
        else:
            status_colors.append(colors['active'])
            status_labels.append(f"{member[:15]} [OK]")
    
    bars = ax_status.barh(range(len(members)), downtime_values, color=status_colors, alpha=0.8, edgecolor='black')
    ax_status.set_yticks(range(len(members)))
    ax_status.set_yticklabels(status_labels, fontsize=10)
    ax_status.set_xlabel("Hours of Downtime", fontsize=11)
    ax_status.axvline(x=3, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='3h threshold')
    ax_status.axvline(x=6, color='red', linestyle='--', alpha=0.7, linewidth=2, label='6h critical')
    ax_status.grid(True, alpha=0.3, axis='x')
    ax_status.legend(fontsize=9)
    
    # Add value labels
    for i, (bar, hours) in enumerate(zip(bars, downtime_values)):
        if hours > 0:
            ax_status.text(hours + 0.1, i, f'{hours:.1f}h', va='center', fontweight='bold', fontsize=9)
    
    # 3. PRODUCTIVITY PIE
    ax_productivity.set_title("[TARGET] Team Status", fontsize=14, fontweight='bold')
    
    good_count = sum(1 for stats in member_stats.values() if stats['status'] == 'good')
    warning_count = sum(1 for stats in member_stats.values() if stats['status'] == 'warning')
    critical_count = sum(1 for stats in member_stats.values() if stats['status'] == 'critical')
    
    sizes = [good_count, warning_count, critical_count]
    labels = [f'[OK] Good\n({good_count})', f'[WARN] Warning\n({warning_count})', f'[SOS] Critical\n({critical_count})']
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
    
    # 4. HOURLY ACTIVITY HEATMAP
    ax_hourly.set_title("[TREND] Hourly Activity Distribution", fontsize=14, fontweight='bold')
    
    # Create hourly activity matrix
    hours_range = list(range(9, min(current_time.hour + 1, 19)))  # Cap at 7 PM
    hourly_matrix = np.zeros((len(members), len(hours_range)))
    
    for i, member in enumerate(members):
        member_data = detailed_data[member]
        
        for period in member_data['in_progress_periods']:
            start_time_period = safe_datetime_from_iso(period['start'])
            end_time_period = safe_datetime_from_iso(period['end']) if period['end'] != current_time else current_time
            
            for j, hour in enumerate(hours_range):
                hour_start = start_time_period.replace(hour=hour, minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                # Calculate overlap
                overlap_start = max(start_time_period, hour_start)
                overlap_end = min(end_time_period, hour_end)
                
                if overlap_start < overlap_end:
                    overlap_delta = overlap_end - overlap_start
                    overlap_minutes = overlap_delta.total_seconds() / 60
                    hourly_matrix[i, j] = overlap_minutes / 60  # Convert to fraction of hour
    
    im = ax_hourly.imshow(hourly_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax_hourly.set_yticks(range(len(members)))
    ax_hourly.set_yticklabels([m[:12] + "..." if len(m) > 12 else m for m in members], fontsize=9)
    ax_hourly.set_xticks(range(len(hours_range)))
    ax_hourly.set_xticklabels([f"{h:02d}:00" for h in hours_range], fontsize=9, rotation=45)
    ax_hourly.set_xlabel("Hour of Day", fontsize=11)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax_hourly, shrink=0.8)
    cbar.set_label('Activity Level', rotation=270, labelpad=15, fontsize=10)
    
    # 5. STATISTICS PANEL
    ax_stats.axis('off')
    
    # Calculate key statistics
    total_team_downtime = sum(stats['total_downtime'] for stats in member_stats.values())
    total_team_active = sum(stats['total_active'] for stats in member_stats.values())
    avg_downtime = total_team_downtime / len(members) if members else 0
    
    currently_inactive = []
    for member, member_data in detailed_data.items():
        for period in member_data['downtime_periods']:
            period_end = safe_datetime_from_iso(period['end'])
            
            if abs((period_end - current_time).total_seconds()) < 300:  # Within 5 minutes
                currently_inactive.append(member)
    
    stats_text = f"""
[CHART] TEAM STATISTICS
====================
[USERS] Total Members: {len(members)}
[OK] Active Status: {good_count}
[WARN] Warning Status: {warning_count}  
[SOS] Critical Status: {critical_count}

[TIMER] TIMING ANALYSIS
====================
[CLOCK] Current Time: {current_time.strftime('%H:%M')}
[CALENDAR] Analysis Date: {data['date']}
[LIGHTNING] Total Team Active: {total_team_active:.1f}h
[DOWN] Total Team Downtime: {total_team_downtime:.1f}h
[TREND] Avg Downtime/Person: {avg_downtime:.1f}h

[ALERT] ALERTS
====================
[FIRE] Currently Inactive: {len(currently_inactive)}
"""
    
    if currently_inactive:
        stats_text += f"\n   • {', '.join(currently_inactive[:3])}"
        if len(currently_inactive) > 3:
            stats_text += f"\n   • +{len(currently_inactive) - 3} more..."
    
    ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes, fontsize=10, 
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9))
    
    # 6. ALERTS PANEL
    ax_alerts.axis('off')
    ax_alerts.set_title("[ALERT] PRIORITY ALERTS", fontsize=16, fontweight='bold', color='red', pad=10)
    
    alerts = []
    
    # Generate alerts based on analysis
    if critical_count > 0:
        critical_members = [m for m, s in member_stats.items() if s['status'] == 'critical']
        alerts.append(f"[SOS] CRITICAL: {critical_count} member(s) with 4+ hours downtime: {', '.join(critical_members)}")
    
    if currently_inactive:
        alerts.append(f"[FIRE] IMMEDIATE: {len(currently_inactive)} member(s) currently inactive: {', '.join(currently_inactive)}")
    
    if warning_count > len(members) * 0.5:
        alerts.append(f"[WARN] TEAM ISSUE: Over 50% of team has significant downtime")
    
    if avg_downtime > 4:
        alerts.append(f"[DOWN] PRODUCTIVITY: Team average downtime is {avg_downtime:.1f} hours")
    
    if not alerts:
        alerts.append("[OK] ALL CLEAR: No critical issues detected")
    
    alert_text = "\n".join(f"• {alert}" for alert in alerts[:4])  # Show top 4 alerts
    
    ax_alerts.text(0.05, 0.5, alert_text, transform=ax_alerts.transAxes, fontsize=12, 
                  verticalalignment='center', fontweight='bold',
                  bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9, edgecolor='red'))
    
    plt.suptitle(f"[TARGET] ClickUp Team Performance Dashboard - {data['date']}", 
                fontsize=20, fontweight='bold', y=0.98)
    
    # Use try/except for tight_layout to handle warnings
    try:
        plt.tight_layout()
    except Exception as e:
        print(f"    [WARN] tight_layout warning: {e}")
    
    # Safe save with error handling
    try:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[CHART] Enhanced timeline visualization saved to: {save_path}")
    except Exception as e:
        print(f"[ERROR] Error saving visualization: {e}")
        return None
    
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
        print(f"[PAGE] Watcher management report saved to: {save_path}")
    except Exception as e:
        print(f"[WARN] Could not save watcher report: {e}")
    
    return report

def retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name):
    """Retry adding watchers to previously failed tasks with enhanced debugging"""
    if not failed_tasks:
        print("[OK] No failed tasks to retry")
        return
    
    print(f"\n[REFRESH] Retrying {len(failed_tasks)} failed watcher additions...")
    print("[DEBUG] Using enhanced debug mode for all retries...")
    
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
            print(f"      [OK] Retry successful!")
        else:
            still_failed.append(task)
            print(f"      [ERROR] Still failed after retry")
        
        # Longer delay for retries
        time.sleep(3)
    
    print(f"\n[CHART] Retry Results:")
    print(f"   [REFRESH] Retried: {len(failed_tasks)}")
    print(f"   [OK] Now successful: {retry_success}")
    print(f"   [ERROR] Still failing: {len(still_failed)}")
    
    if still_failed:
        print(f"\n[ALERT] Tasks that still fail after retry:")
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
        
        print(f"[CHART] Creating enhanced visualizations for {data['date']}...")
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
        print(f"[ERROR] Could not find file: {json_file_path}")
        return None, None
    except Exception as e:
        print(f"[ERROR] Error creating visualizations: {e}")
        return None, None

def create_detailed_analysis_charts(data, save_path="clickup_detailed_analysis.png"):
    """Create comprehensive detailed analysis charts"""
    fig, axes = plt.subplots(2, 3, figsize=(24, 16))
    fig.suptitle(f'[TREND] Detailed Team Analysis - {data["date"]}', fontsize=18, fontweight='bold')
    
    detailed_data = data['detailed_data']
    members = list(detailed_data.keys())
    
    # 1. Active vs Downtime Comparison (Top Left)
    ax1 = axes[0, 0]
    ax1.set_title("[LIGHTNING] Active vs Downtime Hours", fontsize=14, fontweight='bold')
    
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
    
    bars1 = ax1.bar(x - width/2, active_hours, width, label='[OK] Active Hours', 
                   color='#28a745', alpha=0.8, edgecolor='darkgreen')
    bars2 = ax1.bar(x + width/2, downtime_hours, width, label='[RED] Downtime Hours', 
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
    ax2.set_title("[CHART] Downtime Categories", fontsize=14, fontweight='bold')
    
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
        ax2.text(0.5, 0.5, '[PARTY] No Downtime\nDetected!', ha='center', va='center', 
                transform=ax2.transAxes, fontsize=16, fontweight='bold', color='green')
    
    # Continue with remaining charts...
    # [Rest of the function would continue with similar emoji replacements]
    
    # Save with error handling
    try:
        plt.tight_layout()
    except Exception as e:
        print(f"    [WARN] tight_layout warning: {e}")
    
    try:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[CHART] Detailed analysis charts saved to: {save_path}")
    except Exception as e:
        print(f"[ERROR] Error saving detailed analysis: {e}")
        return None
    
    return fig

def main():
    """Enhanced main function with better error handling and user experience"""
    print("[ROCKET] ClickUp Enhanced Downtime Analysis & Watcher Management")
    print("=" * 70)
    
    # Get team info with error handling
    try:
        print("[LINK] Connecting to ClickUp API...")
        team_id = get_team_id()
        members = get_team_members(team_id)
        print(f"[OK] Connected successfully!")
        print(f"[BUILDING] Team ID: {team_id}")
        print(f"[USERS] Team members: {len(members)}")
        
        # Show team members
        print(f"\n[USERS] Team Members:")
        for i, member in enumerate(members, 1):
            user = member.get('user', {})
            username = user.get('username', 'N/A')
            email = user.get('email', 'N/A')
            print(f"   {i:2d}. {username} ({email})")
            
    except Exception as e:
        print(f"[ERROR] Error connecting to ClickUp: {e}")
        print("[TOOL] Please check your API token and try again.")
        return
    
    # Enhanced interactive menu
    print(f"\n[TOOL] What would you like to do?")
    print("1. [CHART] Analyze member downtime only")
    print("2. [WATCH] Add Sean as watcher to all recent tasks")
    print("3. [TARGET] Add custom person as watcher to tasks")  
    print("4. [ROCKET] Both downtime analysis and add watchers")
    print("5. [TREND] Create visualizations from existing JSON file")
    print("6. [REFRESH] Retry failed watcher operations")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice not in ['1', '2', '3', '4', '5', '6']:
        print("[ERROR] Invalid choice. Please run again and select 1-6.")
        return
    
    # Handle visualization from existing file
    if choice == '5':
        json_file = input("Enter the path to your JSON file: ").strip()
        if not json_file:
            # Look for recent files
            import glob
            json_files = glob.glob("clickup_downtime_*.json")
            if json_files:
                latest_file = max(json_files, key=lambda x: x.split('_')[-1])
                print(f"[DEBUG] Found recent file: {latest_file}")
                use_latest = input("Use this file? (y/n, default: y): ").strip().lower()
                if use_latest != 'n':
                    json_file = latest_file
            
            if not json_file:
                print("[ERROR] No JSON file specified or found.")
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
                print("[OK] No failed operations found to retry.")
                return
            
            print(f"[REFRESH] Found {len(failed_tasks)} failed watcher operations")
            watcher_user_id = watcher_info.get('user_id')
            watcher_name = watcher_info.get('name', 'Unknown')
            
            retry_failed_watchers(failed_tasks, watcher_user_id, watcher_name)
            
        except FileNotFoundError:
            print("[ERROR] No previous failed operations found.")
        except Exception as e:
            print(f"[ERROR] Error loading failed operations: {e}")
        return
    

    # Handle watcher functionality (choices 2, 3, 4)
    watcher_results = {}
    if choice in ['2', '3', '4']:
        print(f"\n WATCHER MANAGEMENT")
        print("=" * 30)
        
        # Get date range for tasks
        days_back_input = input("How many days back to look for tasks? (default: 7): ").strip()
        try:
            days_back = int(days_back_input) if days_back_input else 7
        except ValueError:
            days_back = 7
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        print(f" Working with period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Find watcher user
        if choice == '2':
            watcher_name = 'sean'
        else:
            watcher_name = input("Enter the name/username of person to add as watcher: ").strip()
        
        watcher_user = find_user_by_name(members, watcher_name)
        if not watcher_user:
            print(f" Could not find user '{watcher_name}' in the team")
            print("Available users:")
            for member in members:
                user = member.get('user', {})
                print(f"   - {user.get('username', 'N/A')} ({user.get('email', 'N/A')})")
            return
        
        watcher_user_id = watcher_user['id']
        watcher_username = watcher_user['username']
        print(f" Found watcher: {watcher_username} (ID: {watcher_user_id})")
        
        # Enhanced configuration options
        print(f"\n CONFIGURATION OPTIONS")
        debug_mode_input = input("Enable debug mode for comprehensive API testing? (y/n, default: n): ").strip().lower()
        debug_mode = debug_mode_input == 'y'
        
        dry_run_input = input("Do a dry run first (recommended)? (y/n, default: y): ").strip().lower()
        dry_run = dry_run_input != 'n'
        
        batch_size_input = input("Process in batches? Enter batch size (default: all at once): ").strip()
        batch_size = int(batch_size_input) if batch_size_input.isdigit() else None
        
        # Collect all tasks from all members
        all_tasks = []
        print(f"\n Collecting tasks from all team members...")
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            print(f"   [{i+1:2d}/{len(members)}] Getting tasks for {user_name}...")
            
            try:
                tasks = get_member_tasks_with_date_range(team_id, user_id, days_back)
                all_tasks.extend(tasks)
                print(f"    Found {len(tasks)} tasks")
            except Exception as e:
                print(f"   Error getting tasks: {e}")
            
            if i < len(members) - 1:
                time.sleep(2)  # Rate limiting
        
        # Remove duplicates
        unique_tasks = {}
        for task in all_tasks:
            unique_tasks[task['id']] = task
        
        unique_task_list = list(unique_tasks.values())
        print(f" Found {len(unique_task_list)} unique tasks across all members")
        
        if len(unique_task_list) == 0:
            print(" No tasks found to add watchers to")
        else:
            # Process tasks
            if batch_size and len(unique_task_list) > batch_size:
                print(f" Processing in batches of {batch_size}...")
                
                all_success = 0
                all_failed = 0 
                all_failed_tasks = []
                
                for batch_start in range(0, len(unique_task_list), batch_size):
                    batch_end = min(batch_start + batch_size, len(unique_task_list))
                    batch_tasks = unique_task_list[batch_start:batch_end]
                    
                    print(f"\n Processing batch {batch_start//batch_size + 1}: tasks {batch_start+1}-{batch_end}")
                    success, failed, failed_tasks = add_watcher_to_all_tasks(
                        batch_tasks, watcher_user_id, watcher_username, dry_run, debug_mode)
                    
                    all_success += success
                    all_failed += failed
                    all_failed_tasks.extend(failed_tasks)
                    
                    if batch_end < len(unique_task_list):
                        print(" Pausing between batches...")
                        time.sleep(5)
                
                success_count, failed_count, failed_tasks = all_success, all_failed, all_failed_tasks
            else:
                success_count, failed_count, failed_tasks = add_watcher_to_all_tasks(
                    unique_task_list, watcher_user_id, watcher_username, dry_run, debug_mode)
            
            # Handle dry run confirmation
            if dry_run and success_count > 0:
                confirm = input(f"\n Proceed with actually adding {watcher_username} to {len(unique_task_list)} tasks? (y/n): ").strip().lower()
                if confirm == 'y':
                    print(f"\n Proceeding with actual watcher addition...")
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
                    print(f" Failed operations saved for retry (use option 6)")
                except Exception as e:
                    print(f" Could not save failed operations: {e}")
                
                # Ask if user wants to retry immediately
                if failed_count > 0:
                    retry_now = input(f"\n Retry {failed_count} failed operations now? (y/n): ").strip().lower()
                    if retry_now == 'y':
                        retry_success, still_failed = retry_failed_watchers(failed_tasks, watcher_user_id, watcher_username)
                        watcher_results['retry_successful'] = retry_success
                        watcher_results['still_failed'] = len(still_failed)
    
    # Handle downtime analysis (choices 1, 4)
    if choice in ['1', '4']:
        print(f"\n DOWNTIME ANALYSIS")
        print("=" * 25)
        print(f"Starting TODAY's comprehensive downtime analysis...")
        
        # Get today's timestamps
        start_ts, current_ts, today_start, current_time = get_today_timestamps()
        print(f" Monitoring: {current_time.strftime('%A, %B %d, %Y')}")
        print(f" Current time: {current_time.strftime('%H:%M:%S')}")
        print(f" Work day assumption: 9:00 AM - now")
        
        members_with_downtime = []
        all_member_data = {}
        
        # Analyze each team member with progress tracking
        print(f"\n Analyzing {len(members)} team members...")
        
        for i, member in enumerate(members):
            user_id = member['user']['id']
            user_name = member['user']['username']
            
            print(f"\n{'=' * 60}")
            print(f"ANALYZING MEMBER {i+1}/{len(members)}: {user_name}")
            print('=' * 60)
            
            try:
                # Get member's tasks
                print("   Fetching tasks...")
                tasks = get_member_tasks(team_id, user_id)
                print(f"   Found {len(tasks)} open tasks")
                
                if not tasks:
                    # No tasks = full downtime if it's been 3+ hours since work started
                    workday_start = today_start.replace(hour=9)
                    if current_time > workday_start:
                        hours_since_work = (current_time - workday_start).total_seconds() / 3600
                        if hours_since_work >= 3:
                            downtime_periods = [{
                                'start': workday_start,
                                'end': current_time,
                                'duration_hours': hours_since_work,
                                'type': 'no_tasks'
                            }]
                            members_with_downtime.append(user_name)
                            all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': downtime_periods}
                            print(f"   NO TASKS ASSIGNED: {hours_since_work:.1f} hours of downtime")
                        else:
                            all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
                            print(f"   No tasks but within acceptable range")
                    else:
                        all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
                        print(f"   Work day hasn't started yet")
                else:
                    # Analyze task activity
                    print("   Analyzing task activity patterns...")
                    in_progress_periods = find_in_progress_periods_today(tasks, today_start, current_time)
                    print(f"  Found {len(in_progress_periods)} active periods today")
                    
                    # Calculate downtime
                    print("   Calculating downtime periods...")
                    downtime_periods = calculate_downtime_today(user_name, in_progress_periods, today_start, current_time)
                    
                    all_member_data[user_name] = {
                        'in_progress_periods': in_progress_periods,
                        'downtime_periods': downtime_periods
                    }
                    
                    if downtime_periods:
                        members_with_downtime.append(user_name)
                        total_downtime = sum(p['duration_hours'] for p in downtime_periods)
                        print(f"  DOWNTIME DETECTED: {total_downtime:.1f} total hours")
                        
                        # Show breakdown
                        for j, period in enumerate(downtime_periods, 1):
                            start_time_str = period['start'].strftime('%H:%M')
                            end_time_str = period['end'].strftime('%H:%M') if period['end'] != current_time else "NOW"
                            print(f"    {j}. {start_time_str} - {end_time_str} ({period['duration_hours']:.1f}h) [{period['type']}]")
                    else:
                        print(f"  No significant downtime detected (active day)")
                        
            except Exception as e:
                print(f"  Error analyzing {user_name}: {e}")
                all_member_data[user_name] = {'in_progress_periods': [], 'downtime_periods': []}
            
            # Progress indicator
            progress = ((i + 1) / len(members)) * 100
            print(f"  Progress: {progress:.0f}% complete")
            
            # Rate limiting between members
            if i < len(members) - 1:
                print("   Rate limiting pause...")
                time.sleep(3)
        
        # Generate comprehensive final summary
        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE DOWNTIME SUMMARY")
        print(f"{current_time.strftime('%A, %B %d, %Y')} at {current_time.strftime('%H:%M')}")
        print('='*70)

        currently_inactive = False
        if not members_with_downtime:
            print("  EXCELLENT! ALL TEAM MEMBERS ARE ACTIVE!")
            print("   No one has 3+ hours of downtime today.")
            print("   Team is performing at optimal productivity levels.")
        else:
            print(f"ATTENTION REQUIRED: {len(members_with_downtime)} MEMBER(S) WITH SIGNIFICANT DOWNTIME")
            
            # Categorize by severity
            critical_members = []  # 6+ hours
            severe_members = []    # 4-6 hours  
            moderate_members = []  # 3-4 hours
            
            for member_name in members_with_downtime:
                data = all_member_data[member_name]
                total_downtime = sum(p['duration_hours'] for p in data['downtime_periods'])
                
                if total_downtime >= 6:
                    critical_members.append((member_name, total_downtime))
                elif total_downtime >= 4:
                    severe_members.append((member_name, total_downtime))
                else:
                    moderate_members.append((member_name, total_downtime))
            
            # Display by severity
            if critical_members:
                print(f"\n CRITICAL (6+ hours downtime): {len(critical_members)} members")
                for member, hours in critical_members:
                    print(f"   {member}: {hours:.1f} hours - IMMEDIATE ACTION REQUIRED")
            
            if severe_members:
                print(f"\n SEVERE (4-6 hours downtime): {len(severe_members)} members")
                for member, hours in severe_members:
                    print(f"  {member}: {hours:.1f} hours - ACTION NEEDED")
            
            if moderate_members:
                print(f"\n MODERATE (3-4 hours downtime): {len(moderate_members)} members")
                for member, hours in moderate_members:
                    print(f"    {member}: {hours:.1f} hours - MONITOR")
            
            # Show currently inactive members
            currently_inactive = []
            for member_name, data in all_member_data.items():
                for period in data['downtime_periods']:
                    if abs((period['end'] - current_time).total_seconds()) < 300:  # Within 5 minutes of now
                        currently_inactive.append(member_name)
                        break
            
            if currently_inactive:
                print(f"\n CURRENTLY INACTIVE ({len(currently_inactive)} members):")
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
        
        # Final comprehensive statistics
        print(f"\n TEAM PERFORMANCE METRICS:")
        print(f"    Analysis time: {current_time.strftime('%H:%M')}")
        print(f"    Total members: {len(members)}")
        print(f"   Fully active members: {len(members) - len(members_with_downtime)}")
        print(f"    Members with downtime: {len(members_with_downtime)}")
        
        if currently_inactive:
            print(f"   Currently inactive: {len(currently_inactive)}")
        
        # Calculate team efficiency
        total_active_time = sum(sum(p['duration_hours'] for p in data['in_progress_periods']) 
                               for data in all_member_data.values())
        total_downtime_time = sum(sum(p['duration_hours'] for p in data['downtime_periods']) 
                                 for data in all_member_data.values())
        
        if total_active_time + total_downtime_time > 0:
            team_efficiency = (total_active_time / (total_active_time + total_downtime_time)) * 100
            print(f"   Team efficiency: {team_efficiency:.1f}%")
        
        print(f"     Total active hours: {total_active_time:.1f}h")
        print(f"     Total downtime: {total_downtime_time:.1f}h")
        
        if members_with_downtime:
            avg_downtime = total_downtime_time / len(members_with_downtime)
            print(f"    Avg downtime per affected member: {avg_downtime:.1f}h")
        
        # Save comprehensive results
        results = {
            'timestamp': current_time.isoformat(),
            'date': current_time.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'members_analyzed': len(members),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'detailed_data': all_member_data,
            'team_metrics': {
                'total_active_hours': total_active_time,
                'total_downtime_hours': total_downtime_time,
                'team_efficiency': team_efficiency if 'team_efficiency' in locals() else 0,
                'currently_inactive': currently_inactive if 'currently_inactive' in locals() else []
            }
        }
        
        # Add watcher results if available
        if watcher_results:
            results['watcher_management'] = watcher_results
        
        filename = f"clickup_downtime_{current_time.strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n Comprehensive results saved to: {filename}")
            
            # Ask about visualizations
            create_viz = input(f"\n Create enhanced visualizations now? (y/n, default: y): ").strip().lower()
            if create_viz != 'n':
                print(f"\n Creating enhanced visualizations...")
                try:
                    timeline_fig, analysis_fig = load_and_visualize_data(filename)
                    if timeline_fig and analysis_fig:
                        print(f" Visualizations created successfully!")
                        
                        save_viz = input("Save visualizations to files? (y/n, default: y): ").strip().lower()
                        if save_viz != 'n':
                            timeline_filename = f"timeline_{current_time.strftime('%Y%m%d_%H%M')}.png"
                            analysis_filename = f"analysis_{current_time.strftime('%Y%m%d_%H%M')}.png"
                            timeline_fig.savefig(timeline_filename, dpi=300, bbox_inches='tight')
                            analysis_fig.savefig(analysis_filename, dpi=300, bbox_inches='tight')
                            print(f" Saved: {timeline_filename}, {analysis_filename}")
                except Exception as e:
                    print(f" Error creating visualizations: {e}")
                    
        except Exception as e:
            print(f" Could not save results: {e}")
    
    # Final summary
    print(f"\n OPERATION COMPLETE!")
    print("=" * 30)
    
    if choice in ['2', '3', '4'] and watcher_results:
        print(f" Watcher Management Summary:")
        print(f"   • Target: {watcher_results['watcher_name']}")
        print(f"   • Tasks processed: {watcher_results['total_attempts']}")
        print(f"   • Successful: {watcher_results['successful']}")
        print(f"   • Failed: {watcher_results['failed']}")
        if watcher_results.get('retry_successful'):
            print(f"   • Retry successful: {watcher_results['retry_successful']}")
    
    if choice in ['1', '4']:
        print(f" Downtime Analysis Summary:")
        print(f"   • Members analyzed: {len(members)}")
        print(f"   • With downtime: {len(members_with_downtime)}")
        print(f"   • Analysis saved: {filename if 'filename' in locals() else 'N/A'}")
    
    print(f"\n Tips for next time:")
    print(f"   • Use option 5 to re-visualize saved data")
    print(f"   • Use option 6 to retry failed watcher operations")
    print(f"   • Run analysis regularly for trend monitoring")
    
    print(f"\n✨ Thank you for using ClickUp Enhanced Manager!")
    # Rest of the main function continues with similar emoji replacements...
    # [The rest would follow the same pattern of replacing emojis with text equivalents]

if __name__ == "__main__":
    main()