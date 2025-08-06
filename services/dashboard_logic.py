import os, time, requests, logging, pytz
import warnings
from datetime import datetime, timedelta
from functools import wraps
from config import Config

# Setup
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', message='Glyph .* missing from font.*')

HEADERS = {'Authorization': Config.CLICKUP_API_TOKEN}
BASE_URL = Config.BASE_URL
TIMEZONE = Config.TIMEZONE
TARGET_MEMBERS = Config.TARGET_MEMBERS

# Working hours configuration
WORKDAY_START_HOUR = 9
WORKDAY_END_HOUR = 18
LUNCH_BREAK_START = 13
LUNCH_BREAK_END = 14
WORKING_HOURS_PER_DAY = 8

def rate_limit(max_calls_per_minute=20):
    """Rate limiting decorator"""
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if call > now - 60]
            
            if len(calls) >= max_calls_per_minute:
                time.sleep(60 - (now - calls[0]))
                
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_date():
    """Get current date"""
    return datetime.now(TIMEZONE).date()

@rate_limit(max_calls_per_minute=15)
def make_clickup_request(url, method='GET', data=None, max_retries=3):
    """Make rate-limited requests to ClickUp API with proper error handling"""
    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"Resource not found (404): {url}")
                return None
                
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ClickUp API request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
    
    logger.error("Failed to fetch data after all retries")
    return None

def get_team_id():
    """Get the team ID"""
    data = make_clickup_request(f"{BASE_URL}/team")
    if data and 'teams' in data:
        return data['teams'][0]['id']
    return None

def get_team_members(team_id):
    """Get all team members"""
    data = make_clickup_request(f"{BASE_URL}/team")
    if data and 'teams' in data:
        for team in data['teams']:
            if team.get('id') == str(team_id):
                return team.get('members', [])
    return []

def get_all_task_lists(team_id):
    """Get all lists where tasks can be found - using the working method from debug"""
    all_lists = []
    
    # Get all spaces
    spaces_data = make_clickup_request(f"{BASE_URL}/team/{team_id}/space?archived=false")
    if not spaces_data:
        return []
    
    spaces = spaces_data.get('spaces', [])
    logger.info(f"Found {len(spaces)} spaces")
    
    for space in spaces:
        space_id = space['id']
        space_name = space['name']
        logger.debug(f"Processing space: {space_name}")
        
        # Get lists directly in space
        lists_data = make_clickup_request(f"{BASE_URL}/space/{space_id}/list?archived=false")
        if lists_data:
            lists = lists_data.get('lists', [])
            all_lists.extend(lists)
            logger.debug(f"  Found {len(lists)} direct lists in space")
        
        # Get folders and their lists
        folders_data = make_clickup_request(f"{BASE_URL}/space/{space_id}/folder?archived=false")
        if folders_data:
            folders = folders_data.get('folders', [])
            for folder in folders:
                folder_id = folder['id']
                folder_lists_data = make_clickup_request(f"{BASE_URL}/folder/{folder_id}/list?archived=false")
                if folder_lists_data:
                    folder_lists = folder_lists_data.get('lists', [])
                    all_lists.extend(folder_lists)
                    logger.debug(f"  Found {len(folder_lists)} lists in folder {folder['name']}")
        
        time.sleep(1)  # Rate limiting between spaces
    
    logger.info(f"Total lists found: {len(all_lists)}")
    return all_lists

def get_member_tasks_comprehensive(team_id, member_id, username):
    """Get all tasks for a member from all lists - using the working method from debug"""
    all_tasks = []
    
    # Get all lists in the team
    task_lists = get_all_task_lists(team_id)
    logger.info(f"Searching {len(task_lists)} lists for {username} tasks...")
    
    for task_list in task_lists:
        try:
            list_id = task_list['id']
            list_name = task_list['name']
            
            # Get tasks from this list
            tasks_data = make_clickup_request(f"{BASE_URL}/list/{list_id}/task?archived=false&include_closed=true&subtasks=true")
            if not tasks_data:
                continue
            
            tasks = tasks_data.get('tasks', [])
            
            # Filter tasks assigned to this member
            member_tasks = []
            for task in tasks:
                assignees = task.get('assignees', [])
                if any(str(assignee.get('id')) == str(member_id) for assignee in assignees):
                    member_tasks.append(task)
            
            if member_tasks:
                logger.debug(f"  Found {len(member_tasks)} tasks in {list_name}")
                all_tasks.extend(member_tasks)
                
        except Exception as e:
            logger.warning(f"Error getting tasks from list {task_list.get('name', 'unknown')}: {e}")
            continue
        
        time.sleep(0.5)  # Rate limiting between lists
    
    logger.info(f"Total tasks found for {username}: {len(all_tasks)}")
    return all_tasks

def is_task_in_progress(task):
    """Check if a task is currently in 'in progress' status"""
    status = task.get('status', {})
    if not status:
        return False
    
    status_name = status.get('status', '').lower()
    
    # Based on your debug output, these are the actual status names
    progress_keywords = [
        'in progress', 'progress', 'staging'  # From your debug output
    ]
    
    return any(keyword in status_name for keyword in progress_keywords)

def analyze_member_activity(member, team_id, current_time):
    """Analyze a team member's activity - simplified but working approach"""
    user = member.get('user', {})
    user_id = user.get('id')
    username = user.get('username', 'Unknown')
    
    logger.info(f"Analyzing {username}...")
    
    # Get all tasks for this member
    tasks = get_member_tasks_comprehensive(team_id, user_id, username)
    
    in_progress_periods = []
    task_details = []
    
    # Find currently in-progress tasks
    in_progress_tasks = []
    for task in tasks:
        task_name = task['name']
        task_status = task.get('status', {}).get('status', '')
        
        # Store task details
        task_details.append({
            'id': task['id'],
            'name': task_name,
            'status': task_status,
            'url': task.get('url', ''),
            'date_created': task.get('date_created'),
            'date_updated': task.get('date_updated'),
            'priority': task.get('priority'),
            'assignees': [a.get('username') for a in task.get('assignees', [])],
            'is_in_progress': is_task_in_progress(task)
        })
        
        # Check if task is in progress
        if is_task_in_progress(task):
            in_progress_tasks.append(task)
            logger.info(f"  ✅ In-progress task: {task_name} ({task_status})")
    
    # For in-progress tasks, create periods based on typical work day
    if in_progress_tasks:
        # Estimate work periods based on tasks
        workday_start = current_time.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
        
        # Create periods for active tasks (simplified approach)
        for i, task in enumerate(in_progress_tasks):
            # Estimate start time (spread tasks throughout the day)
            hour_offset = i * 2  # Space tasks 2 hours apart
            period_start = workday_start + timedelta(hours=hour_offset)
            
            # If start time is in the future, use current time
            if period_start > current_time:
                period_start = current_time - timedelta(hours=1)
            
            # Period ends at current time (task is ongoing)
            period_end = current_time
            
            duration_hours = (period_end - period_start).total_seconds() / 3600
            
            if duration_hours > 0:
                in_progress_periods.append({
                    'start': period_start,
                    'end': period_end,
                    'task_name': task['name'],
                    'task_id': task['id'],
                    'duration_hours': duration_hours,
                    'status': 'currently_active'
                })
    
    # Calculate downtime periods
    downtime_periods = calculate_downtime_periods(in_progress_periods, current_time)
    
    # Calculate totals
    total_active_hours = sum(p['duration_hours'] for p in in_progress_periods)
    total_downtime_hours = sum(p['duration_hours'] for p in downtime_periods)
    
    logger.info(f"  {username}: {len(tasks)} tasks, {len(in_progress_tasks)} active, {total_active_hours:.1f}h active, {total_downtime_hours:.1f}h downtime")
    
    return {
        'username': username,
        'user_id': user_id,
        'total_tasks': len(tasks),
        'active_tasks': len(in_progress_tasks),
        'total_active_hours': total_active_hours,
        'total_downtime_hours': total_downtime_hours,
        'in_progress_periods': in_progress_periods,
        'downtime_periods': downtime_periods,
        'task_details': task_details
    }

def calculate_downtime_periods(in_progress_periods, current_time):
    """Calculate downtime periods between active work"""
    downtime_periods = []
    
    workday_start = current_time.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    workday_end = current_time.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    lunch_start = current_time.replace(hour=LUNCH_BREAK_START, minute=0, second=0, microsecond=0)
    lunch_end = current_time.replace(hour=LUNCH_BREAK_END, minute=0, second=0, microsecond=0)
    
    analysis_end = min(current_time, workday_end)
    
    if not in_progress_periods:
        # No activity all day
        if analysis_end > workday_start:
            duration_hours = (analysis_end - workday_start).total_seconds() / 3600
            downtime_periods.append({
                'start': workday_start,
                'end': analysis_end,
                'duration_hours': duration_hours,
                'type': 'no_activity_all_day'
            })
        return downtime_periods
    
    # Sort periods by start time
    sorted_periods = sorted(in_progress_periods, key=lambda x: x['start'])
    
    # Check gap from workday start to first activity
    first_activity = sorted_periods[0]['start']
    if first_activity > workday_start:
        gap_hours = (first_activity - workday_start).total_seconds() / 3600
        if gap_hours >= 1:
            downtime_periods.append({
                'start': workday_start,
                'end': first_activity,
                'duration_hours': gap_hours,
                'type': 'late_start'
            })
    
    # Check gaps between activities
    for i in range(len(sorted_periods) - 1):
        gap_start = sorted_periods[i]['end']
        gap_end = sorted_periods[i + 1]['start']
        gap_hours = (gap_end - gap_start).total_seconds() / 3600
        
        if gap_hours >= 1:
            downtime_periods.append({
                'start': gap_start,
                'end': gap_end,
                'duration_hours': gap_hours,
                'type': 'midday_gap'
            })
    
    # Check gap from last activity to current time
    last_activity = sorted_periods[-1]['end']
    if last_activity < analysis_end:
        gap_hours = (analysis_end - last_activity).total_seconds() / 3600
        if gap_hours >= 1:
            gap_type = 'current_inactive' if analysis_end == current_time else 'end_of_day'
            downtime_periods.append({
                'start': last_activity,
                'end': analysis_end,
                'duration_hours': gap_hours,
                'type': gap_type
            })
    
    return downtime_periods

def analyze_team_performance():
    """Main function to analyze team performance - simplified working version"""
    logger.info("Starting ClickUp team performance analysis...")
    
    try:
        # Get team and members
        team_id = get_team_id()
        if not team_id:
            logger.error("Could not get team ID")
            return None
            
        members = get_team_members(team_id)
        if not members:
            logger.error("Could not get team members")
            return None
        
        current_time = datetime.now(tz=TIMEZONE)
        target_date = current_time.date()
        
        logger.info(f"Analyzing team performance for {target_date}")
        logger.info(f"Found {len(members)} team members")
        
        # Filter members if TARGET_MEMBERS is specified
        if TARGET_MEMBERS:
            filtered_members = [m for m in members if m.get('user', {}).get('username') in TARGET_MEMBERS]
            logger.info(f"Filtering to {len(filtered_members)} target members: {TARGET_MEMBERS}")
            members = filtered_members
        
        if not members:
            logger.error("No target members found!")
            return None
        
        members_with_downtime = []
        all_member_data = {}
        
        # Analyze each member
        for i, member in enumerate(members):
            username = member.get('user', {}).get('username', 'Unknown')
            logger.info(f"=== Analyzing member {i+1}/{len(members)}: {username} ===")
            
            try:
                member_analysis = analyze_member_activity(member, team_id, current_time)
                
                # Convert datetime objects to ISO strings for JSON serialization
                for period in member_analysis['in_progress_periods']:
                    if isinstance(period['start'], datetime):
                        period['start'] = period['start'].isoformat()
                    if isinstance(period['end'], datetime):
                        period['end'] = period['end'].isoformat()
                
                for period in member_analysis['downtime_periods']:
                    if isinstance(period['start'], datetime):
                        period['start'] = period['start'].isoformat()
                    if isinstance(period['end'], datetime):
                        period['end'] = period['end'].isoformat()
                
                all_member_data[username] = member_analysis
                
                if member_analysis['downtime_periods']:
                    members_with_downtime.append(username)
                
            except Exception as e:
                logger.error(f"Error analyzing {username}: {e}")
                # Create empty data structure for failed analysis
                all_member_data[username] = {
                    'username': username,
                    'user_id': member.get('user', {}).get('id'),
                    'total_tasks': 0,
                    'active_tasks': 0,
                    'total_active_hours': 0,
                    'total_downtime_hours': 0,
                    'in_progress_periods': [],
                    'downtime_periods': [],
                    'task_details': [],
                    'error': str(e)
                }
            
            # Rate limiting between members
            time.sleep(3)
        
        # Calculate team metrics
        total_active_time = sum(data['total_active_hours'] for data in all_member_data.values())
        total_downtime_time = sum(data['total_downtime_hours'] for data in all_member_data.values())
        total_tasks = sum(data['total_tasks'] for data in all_member_data.values())
        total_active_tasks = sum(data['active_tasks'] for data in all_member_data.values())
        
        # Calculate expected working hours
        current_hour = current_time.hour + current_time.minute/60
        if target_date.weekday() >= 5:  # Weekend
            expected_hours = 0
        else:
            if current_hour < WORKDAY_START_HOUR:
                expected_hours = 0
            elif current_hour < LUNCH_BREAK_START:
                expected_hours = (current_hour - WORKDAY_START_HOUR) * len(members)
            elif current_hour < LUNCH_BREAK_END:
                expected_hours = (LUNCH_BREAK_START - WORKDAY_START_HOUR) * len(members)
            elif current_hour < WORKDAY_END_HOUR:
                expected_hours = ((LUNCH_BREAK_START - WORKDAY_START_HOUR) + (current_hour - LUNCH_BREAK_END)) * len(members)
            else:
                expected_hours = WORKING_HOURS_PER_DAY * len(members)
        
        team_efficiency = 0
        if total_active_time + total_downtime_time > 0:
            team_efficiency = (total_active_time / (total_active_time + total_downtime_time)) * 100
        
        # Find currently inactive members
        currently_inactive = []
        for member_name, data in all_member_data.items():
            if data['active_tasks'] == 0:  # No active tasks = currently inactive
                currently_inactive.append(member_name)
        
        results = {
            'timestamp': current_time.isoformat(),
            'date': target_date.strftime('%Y-%m-%d'),
            'analysis_time': current_time.strftime('%H:%M:%S'),
            'day_of_week': target_date.strftime('%A'),
            'is_weekend': target_date.weekday() >= 5,
            'members_analyzed': len(members),
            'members_with_downtime': len(members_with_downtime),
            'downtime_members': members_with_downtime,
            'detailed_data': all_member_data,
            'team_metrics': {
                'total_active_hours': round(total_active_time, 1),
                'total_downtime_hours': round(total_downtime_time, 1),
                'expected_working_hours': round(expected_hours, 1),
                'team_efficiency': round(team_efficiency, 1),
                'currently_inactive': currently_inactive,
                'total_tasks': total_tasks,
                'total_active_tasks': total_active_tasks
            }
        }
        
        logger.info("=== ANALYSIS SUMMARY ===")
        logger.info(f"Members analyzed: {len(members)}")
        logger.info(f"Total tasks found: {total_tasks}")
        logger.info(f"Total active tasks: {total_active_tasks}")
        logger.info(f"Total active hours: {total_active_time:.1f}")
        logger.info(f"Total downtime hours: {total_downtime_time:.1f}")
        logger.info(f"Team efficiency: {team_efficiency:.1f}%")
        logger.info(f"Members with downtime: {len(members_with_downtime)}")
        if currently_inactive:
            logger.info(f"Currently inactive: {', '.join(currently_inactive)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during team analysis: {e}")
        return None

def get_analysis_context(data):
    """Enhanced to handle both regular and fallback data"""
    try:
        timestamp = data.get('timestamp') or data.get('analysis_time')
        if not timestamp:
            return {'error': 'No timestamp in data'}
            
        analysis_time = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        current_hour = analysis_time.hour + analysis_time.minute/60
        
        is_weekend = data.get('is_weekend', False)
        is_working_hours = (
            not is_weekend and 
            WORKDAY_START_HOUR <= current_hour < WORKDAY_END_HOUR
        )
        return {
            'data_status': 'LIVE' if is_working_hours else 'OUTSIDE_WORKING_HOURS',
            'next_expected_update': next_working_day(data.get('date')),
            'current_analysis_time': timestamp,
            'working_hours': f"{WORKDAY_START_HOUR}:00-{WORKDAY_END_HOUR}:00",
            'is_weekend': is_weekend
        }
    except Exception as e:
        logger.error(f"Error generating analysis context: {str(e)}")
        return {'error': 'Could not generate context'}

def next_working_day(date_str):
    """Calculates the next working day (skips weekends)"""
    if not date_str:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Increment until we find a weekday (0-4 = Monday-Friday)
    while True:
        date += timedelta(days=1)
        if date.weekday() < 5:  # 0-4 = Monday-Friday
            return date.strftime("%Y-%m-%d")