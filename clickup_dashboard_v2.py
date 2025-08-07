from flask import Flask, render_template, request, jsonify
import logging
import json
import os
from datetime import datetime, timedelta
import threading
import time

# Working hours configuration
WORKDAY_START_HOUR = 9
WORKDAY_END_HOUR = 17
LUNCH_BREAK_START = 12
LUNCH_BREAK_END = 12.5
WORKING_HOURS_PER_DAY = 7.5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.template_folder = 'template_v2'
app.static_folder = 'static_v2'

def is_working_day(date_obj):
    """Check if the date is a working day (Monday-Friday)"""
    return date_obj.weekday() < 5  # 0-4 are Monday-Friday

def is_working_time(time_obj):
    """Check if the time is within working hours"""
    hour_float = time_obj.hour + time_obj.minute / 60.0
    
    # Check if within working hours but not during lunch
    if WORKDAY_START_HOUR <= hour_float < LUNCH_BREAK_START:
        return True
    elif LUNCH_BREAK_END <= hour_float < WORKDAY_END_HOUR:
        return True
    else:
        return False

def get_working_time_ranges(date_obj):
    """Get working time ranges for a given date"""
    if not is_working_day(date_obj):
        return []
    
    morning_start = date_obj.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    morning_end = date_obj.replace(hour=int(LUNCH_BREAK_START), 
                                  minute=int((LUNCH_BREAK_START % 1) * 60), 
                                  second=0, microsecond=0)
    
    afternoon_start = date_obj.replace(hour=int(LUNCH_BREAK_END), 
                                      minute=int((LUNCH_BREAK_END % 1) * 60), 
                                      second=0, microsecond=0)
    afternoon_end = date_obj.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    
    return [
        (morning_start, morning_end),      # 9:00 - 12:00
        (afternoon_start, afternoon_end)   # 12:30 - 17:00
    ]

def calculate_working_hours_overlap(start_time, end_time):
    """Calculate how many working hours overlap with the given time period"""
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    # Get the date for working time calculation
    date_obj = start_time.date()
    working_ranges = get_working_time_ranges(datetime.combine(date_obj, datetime.min.time()))
    
    total_overlap = 0
    
    for work_start, work_end in working_ranges:
        # Calculate overlap between activity period and working period
        overlap_start = max(start_time, work_start)
        overlap_end = min(end_time, work_end)
        
        if overlap_start < overlap_end:
            overlap_duration = (overlap_end - overlap_start).total_seconds() / 3600  # Convert to hours
            total_overlap += overlap_duration
    
    return total_overlap

def filter_working_time_data(detailed_data):
    """Filter data to only include working time periods"""
    filtered_data = {}
    
    for member, member_data in detailed_data.items():
        filtered_member = {
            'username': member_data.get('username', member),
            'total_tasks': member_data.get('total_tasks', 0),
            'active_tasks': member_data.get('active_tasks', 0),
            'in_progress_periods': [],
            'downtime_periods': [],
            'task_details': member_data.get('task_details', [])
        }
        
        # Filter and recalculate active periods
        total_working_active = 0
        for period in member_data.get('in_progress_periods', []):
            start_time = period.get('start')
            end_time = period.get('end')
            
            if start_time and end_time:
                working_hours = calculate_working_hours_overlap(start_time, end_time)
                if working_hours > 0:
                    # Only include periods that have working time overlap
                    filtered_period = period.copy()
                    filtered_period['working_hours'] = working_hours
                    filtered_member['in_progress_periods'].append(filtered_period)
                    total_working_active += working_hours
        
        # Calculate downtime during working hours
        working_time_downtime = []
        current_date = datetime.now().date()
        working_ranges = get_working_time_ranges(datetime.combine(current_date, datetime.min.time()))
        
        # For each working time range, check if there are gaps
        for work_start, work_end in working_ranges:
            # Find all active periods that overlap with this working range
            overlapping_periods = []
            for period in filtered_member['in_progress_periods']:
                period_start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                period_end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                
                if period_start < work_end and period_end > work_start:
                    overlapping_periods.append((
                        max(period_start, work_start),
                        min(period_end, work_end)
                    ))
            
            # Sort overlapping periods and find gaps
            overlapping_periods.sort()
            current_time = work_start
            
            for period_start, period_end in overlapping_periods:
                if current_time < period_start:
                    # There's a gap - this is downtime
                    downtime_duration = (period_start - current_time).total_seconds() / 3600
                    if downtime_duration > 0.1:  # Only count gaps longer than 6 minutes
                        working_time_downtime.append({
                            'start': current_time.isoformat(),
                            'end': period_start.isoformat(),
                            'duration_hours': downtime_duration,
                            'reason': 'No activity during working hours'
                        })
                current_time = max(current_time, period_end)
            
            # Check for downtime at the end of the working period
            if current_time < work_end:
                downtime_duration = (work_end - current_time).total_seconds() / 3600
                if downtime_duration > 0.1:
                    working_time_downtime.append({
                        'start': current_time.isoformat(),
                        'end': work_end.isoformat(),
                        'duration_hours': downtime_duration,
                        'reason': 'No activity during working hours'
                    })
        
        filtered_member['downtime_periods'] = working_time_downtime
        filtered_member['total_active_hours'] = total_working_active
        filtered_member['total_downtime_hours'] = sum(p['duration_hours'] for p in working_time_downtime)
        
        filtered_data[member] = filtered_member
    
    return filtered_data

def load_latest_json_data():
    """Load the most recent JSON data file generated by get_reports.py"""
    try:
        logger.info("Looking for JSON data files...")
        
        # Get current working directory
        current_dir = os.getcwd()
        logger.info(f"Searching in directory: {current_dir}")
        
        # List all files to help debug
        all_files = os.listdir('.')
        logger.info(f"All files in directory: {[f for f in all_files if f.endswith('.json')]}")
        
        # Look for JSON files with multiple possible patterns
        json_files = []
        patterns = [
            'clickup_downtime_analysis_',  # Original expected pattern
            'clickup_downtime_',           # Your actual file pattern
            'clickup_timeline_',
            'clickup_',
        ]
        
        # Look for JSON files with multiple possible patterns
        json_files = []
        patterns = [
            'clickup_downtime_analysis_',  # Original expected pattern
            'clickup_downtime_',           # Your actual file pattern
            'clickup_timeline_',
            'clickup_',
        ]
        
        logger.info(f"Looking for files matching patterns: {patterns}")
        
        for file in all_files:
            if file.endswith('.json'):
                logger.info(f"Checking JSON file: {file}")
                # Check if file matches any pattern
                for pattern in patterns:
                    if file.startswith(pattern):
                        json_files.append(file)
                        logger.info(f"✅ Found matching JSON file: {file} (matches pattern: {pattern})")
                        break
                else:
                    logger.info(f"❌ File {file} doesn't match any pattern")
                    # If no pattern matches, include any JSON file that might be relevant
                    if 'clickup' in file.lower() or 'downtime' in file.lower() or 'analysis' in file.lower():
                        json_files.append(file)
                        logger.info(f"✅ Added as potential ClickUp file: {file}")
        
        logger.info(f"Final list of JSON files to consider: {json_files}")
        
        # Remove duplicates
        json_files = list(set(json_files))
        
        if not json_files:
            logger.warning("No JSON data files found with expected patterns")
            # List all JSON files for debugging
            all_json = [f for f in all_files if f.endswith('.json')]
            logger.info(f"All JSON files in directory: {all_json}")
            
            # If there are any JSON files, try the first one
            if all_json:
                logger.info(f"Attempting to use first available JSON file: {all_json[0]}")
                json_files = [all_json[0]]
            else:
                logger.warning("No JSON files found at all. Please run get_reports.py first.")
                return None
            
        # Sort by modification time and get the latest
        latest_file = max(json_files, key=lambda f: os.path.getmtime(f))
        logger.info(f"Using latest file: {latest_file}")
        
        # Try to load the file
        with open(latest_file, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded data from {latest_file}")
            logger.info(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Validate that it has the expected structure
            if isinstance(data, dict) and 'detailed_data' in data:
                logger.info("File has expected ClickUp data structure")
                return data
            else:
                logger.warning(f"File {latest_file} doesn't have expected structure, trying sample data")
                return None
            
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}", exc_info=True)
        all_json = [f for f in all_files if f.endswith('.json')]
        logger.info(f"All JSON files in directory: {all_json}")
        logger.info(f"All JSON files in directory: {all_files}")
        return None
        
        # Sort by modification time and get the latest
        latest_file = max(json_files, key=os.path.getmtime)
        logger.info(f"Using latest file: {latest_file}")
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded data from {latest_file}")
            logger.info(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return data
            
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}", exc_info=True)
        return None

def calculate_dashboard_metrics(data):
    """Calculate metrics for the dashboard using working hours"""
    if not data or 'detailed_data' not in data:
        return None
        
    # Filter data to working hours only
    detailed_data = filter_working_time_data(data['detailed_data'])
    members = list(detailed_data.keys())
    
    # Calculate member status based on working hours
    member_stats = {}
    good_count = 0
    warning_count = 0
    critical_count = 0
    
    total_team_downtime = 0
    total_team_active = 0
    currently_inactive = []
    
    current_time = datetime.now()
    
    # Define thresholds based on working hours (7.5h per day)
    warning_threshold = 2.0    # 2+ hours of downtime in working day
    critical_threshold = 4.0   # 4+ hours of downtime in working day
    
    for member in members:
        member_data = detailed_data[member]
        total_downtime = member_data['total_downtime_hours']
        total_active = member_data['total_active_hours']
        
        # Determine status based on working hour thresholds
        if total_downtime >= critical_threshold:
            status = 'critical'
            critical_count += 1
        elif total_downtime >= warning_threshold:
            status = 'warning'
            warning_count += 1
        else:
            status = 'good'
            good_count += 1
            
        # Calculate efficiency (active hours / expected working hours)
        efficiency = (total_active / WORKING_HOURS_PER_DAY * 100) if WORKING_HOURS_PER_DAY > 0 else 0
        
        member_stats[member] = {
            'total_downtime': total_downtime,
            'total_active': total_active,
            'efficiency': efficiency,
            'status': status
        }
        
        total_team_downtime += total_downtime
        total_team_active += total_active
        
        # Check if currently inactive during working hours
        if is_working_day(current_time) and is_working_time(current_time):
            for period in member_data['downtime_periods']:
                if isinstance(period.get('end'), str):
                    try:
                        period_end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                        if abs((period_end - current_time).total_seconds()) < 300:  # Within 5 minutes
                            currently_inactive.append(member)
                            break
                    except:
                        pass
    
    # Calculate hourly activity matrix (working hours only)
    working_hours_range = []
    # Morning hours: 9-12
    working_hours_range.extend(list(range(WORKDAY_START_HOUR, int(LUNCH_BREAK_START))))
    # Afternoon hours: 12:30-17 (represented as 13-17 for simplicity)
    working_hours_range.extend(list(range(int(LUNCH_BREAK_END) + 1, WORKDAY_END_HOUR + 1)))
    
    hourly_matrix = {}
    
    for member in members:
        member_data = detailed_data[member]
        hourly_matrix[member] = [0] * len(working_hours_range)
        
        for period in member_data['in_progress_periods']:
            try:
                if isinstance(period['start'], str):
                    start_time = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(period['end'].replace('Z', '+00:00')) if isinstance(period['end'], str) else current_time
                else:
                    start_time = period['start']
                    end_time = period['end']
                
                for j, hour in enumerate(working_hours_range):
                    hour_start = start_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                    hour_end = hour_start + timedelta(hours=1)
                    
                    # Skip lunch hour
                    if int(LUNCH_BREAK_START) <= hour < int(LUNCH_BREAK_END) + 1:
                        continue
                    
                    overlap_start = max(start_time, hour_start)
                    overlap_end = min(end_time, hour_end)
                    
                    if overlap_start < overlap_end:
                        overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                        hourly_matrix[member][j] = overlap_minutes / 60
            except:
                continue
    
    # Generate alerts based on working hours
    alerts = []
    if critical_count > 0:
        critical_members = [m for m, s in member_stats.items() if s['status'] == 'critical']
        alerts.append({
            'type': 'critical',
            'message': f"🆘 CRITICAL: {critical_count} member(s) with {critical_threshold}+ hours downtime during working hours: {', '.join(critical_members)}"
        })
    
    if currently_inactive and is_working_day(current_time) and is_working_time(current_time):
        alerts.append({
            'type': 'immediate',
            'message': f"🔥 IMMEDIATE: {len(currently_inactive)} member(s) currently inactive during working hours: {', '.join(currently_inactive)}"
        })
    
    if warning_count > len(members) * 0.5:
        alerts.append({
            'type': 'warning',
            'message': f"⚠️ TEAM ISSUE: Over 50% of team has significant downtime during working hours"
        })
    
    avg_downtime = total_team_downtime / len(members) if members else 0
    avg_efficiency = (total_team_active / (len(members) * WORKING_HOURS_PER_DAY) * 100) if members and WORKING_HOURS_PER_DAY > 0 else 0
    
    if avg_efficiency < 60:
        alerts.append({
            'type': 'productivity',
            'message': f"📉 PRODUCTIVITY: Team efficiency is {avg_efficiency:.1f}% (below 60% target)"
        })
    
    # Weekend check
    if not is_working_day(current_time):
        alerts = [{
            'type': 'info',
            'message': f"📅 WEEKEND: Today is {current_time.strftime('%A')} - no working hour analysis"
        }]
    elif not is_working_time(current_time):
        alerts.append({
            'type': 'info', 
            'message': f"⏰ OUTSIDE HOURS: Current time ({current_time.strftime('%H:%M')}) is outside working hours ({WORKDAY_START_HOUR}:00-{WORKDAY_END_HOUR}:00)"
        })
    
    if not alerts:
        alerts.append({
            'type': 'success',
            'message': "✅ ALL CLEAR: No critical issues detected during working hours"
        })
    
    return {
        'member_stats': member_stats,
        'team_summary': {
            'good_count': good_count,
            'warning_count': warning_count,
            'critical_count': critical_count,
            'total_members': len(members),
            'total_team_downtime': total_team_downtime,
            'total_team_active': total_team_active,
            'avg_downtime': avg_downtime,
            'avg_efficiency': avg_efficiency,
            'currently_inactive': currently_inactive,
            'expected_daily_hours': WORKING_HOURS_PER_DAY,
            'is_working_day': is_working_day(current_time),
            'is_working_time': is_working_time(current_time)
        },
        'hourly_matrix': hourly_matrix,
        'hours_range': working_hours_range,
        'alerts': alerts,
        'working_config': {
            'start_hour': WORKDAY_START_HOUR,
            'end_hour': WORKDAY_END_HOUR,
            'lunch_start': LUNCH_BREAK_START,
            'lunch_end': LUNCH_BREAK_END,
            'daily_hours': WORKING_HOURS_PER_DAY
        }
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

def generate_sample_data():
    """Generate sample data for testing when no JSON files exist - respects working hours"""
    current_time = datetime.now()
    
    # If it's weekend, use last Friday
    if not is_working_day(current_time):
        days_back = current_time.weekday() - 4  # Friday is 4
        if days_back <= 0:
            days_back += 7
        current_time = current_time - timedelta(days=days_back)
    
    # Set to working day start
    work_start = current_time.replace(hour=WORKDAY_START_HOUR, minute=0, second=0, microsecond=0)
    lunch_start = current_time.replace(hour=int(LUNCH_BREAK_START), minute=int((LUNCH_BREAK_START % 1) * 60), second=0, microsecond=0)
    lunch_end = current_time.replace(hour=int(LUNCH_BREAK_END), minute=int((LUNCH_BREAK_END % 1) * 60), second=0, microsecond=0)
    work_end = current_time.replace(hour=WORKDAY_END_HOUR, minute=0, second=0, microsecond=0)
    
    sample_data = {
        "date": current_time.strftime('%Y-%m-%d'),
        "timestamp": current_time.isoformat(),
        "members_analyzed": 3,
        "members_with_downtime": 2,
        "detailed_data": {
            "John Doe": {
                "username": "John Doe",
                "total_tasks": 3,
                "active_tasks": 3,
                "total_active_hours": 6.0,
                "total_downtime_hours": 1.5,
                "in_progress_periods": [
                    {
                        "start": work_start.isoformat(),
                        "end": (work_start + timedelta(hours=2.5)).isoformat(),
                        "task_name": "Frontend Development",
                        "task_id": "task_001",
                        "duration_hours": 2.5,
                        "status": "in progress"
                    },
                    {
                        "start": lunch_end.isoformat(),
                        "end": (lunch_end + timedelta(hours=2.5)).isoformat(),
                        "task_name": "Code Review",
                        "task_id": "task_002",
                        "duration_hours": 2.5,
                        "status": "in progress"
                    },
                    {
                        "start": (work_end - timedelta(hours=1)).isoformat(),
                        "end": work_end.isoformat(),
                        "task_name": "Team Meeting",
                        "task_id": "task_003",
                        "duration_hours": 1.0,
                        "status": "completed"
                    }
                ],
                "downtime_periods": [
                    {
                        "start": (work_start + timedelta(hours=2.5)).isoformat(),
                        "end": lunch_start.isoformat(),
                        "duration_hours": 1.0,
                        "reason": "Extended break"
                    },
                    {
                        "start": (lunch_end + timedelta(hours=2.5)).isoformat(),
                        "end": (work_end - timedelta(hours=1)).isoformat(),
                        "duration_hours": 0.5,
                        "reason": "Short break"
                    }
                ],
                "task_details": []
            },
            "Jane Smith": {
                "username": "Jane Smith",
                "total_tasks": 2,
                "active_tasks": 2,
                "total_active_hours": 7.0,
                "total_downtime_hours": 0.5,
                "in_progress_periods": [
                    {
                        "start": work_start.isoformat(),
                        "end": lunch_start.isoformat(),
                        "task_name": "API Development",
                        "task_id": "task_004",
                        "duration_hours": 3.0,
                        "status": "in progress"
                    },
                    {
                        "start": lunch_end.isoformat(),
                        "end": work_end.isoformat(),
                        "task_name": "Documentation",
                        "task_id": "task_005",
                        "duration_hours": 4.0,
                        "status": "in progress"
                    }
                ],
                "downtime_periods": [
                    {
                        "start": (work_end - timedelta(hours=0.5)).isoformat(),
                        "end": work_end.isoformat(),
                        "duration_hours": 0.5,
                        "reason": "End of day wrap-up"
                    }
                ],
                "task_details": []
            },
            "Bob Wilson": {
                "username": "Bob Wilson", 
                "total_tasks": 1,
                "active_tasks": 1,
                "total_active_hours": 2.5,
                "total_downtime_hours": 5.0,
                "in_progress_periods": [
                    {
                        "start": work_start.isoformat(),
                        "end": (work_start + timedelta(hours=1.5)).isoformat(),
                        "task_name": "Bug Investigation",
                        "task_id": "task_006",
                        "duration_hours": 1.5,
                        "status": "blocked"
                    },
                    {
                        "start": (work_end - timedelta(hours=1)).isoformat(),
                        "end": work_end.isoformat(),
                        "task_name": "Status Update",
                        "task_id": "task_007",
                        "duration_hours": 1.0,
                        "status": "completed"
                    }
                ],
                "downtime_periods": [
                    {
                        "start": (work_start + timedelta(hours=1.5)).isoformat(),
                        "end": lunch_start.isoformat(),
                        "duration_hours": 1.5,
                        "reason": "Waiting for clarification"
                    },
                    {
                        "start": lunch_end.isoformat(),
                        "end": (work_end - timedelta(hours=1)).isoformat(),
                        "duration_hours": 3.5,
                        "reason": "Blocked on external dependency"
                    }
                ],
                "task_details": []
            }
        }
    }
    
    return sample_data

@app.route('/api/sample-data')
def api_sample_data():
    """Get sample data for testing"""
    try:
        raw_data = generate_sample_data()
        metrics = calculate_dashboard_metrics(raw_data)
        
        response_data = {
            'date': raw_data.get('date'),
            'timestamp': raw_data.get('timestamp'),
            'detailed_data': raw_data.get('detailed_data', {}),
            'metrics': metrics,
            'raw_summary': {
                'members_analyzed': raw_data.get('members_analyzed', 0),
                'members_with_downtime': raw_data.get('members_with_downtime', 0)
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate sample data'}), 500

@app.route('/api/test')
def api_test():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'ok',
        'message': 'API is working',
        'timestamp': datetime.now().isoformat(),
        'working_directory': os.getcwd(),
        'json_files': [f for f in os.listdir('.') if f.endswith('.json')]
    })

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Get enhanced dashboard data"""
    try:
        logger.info("API dashboard-data endpoint called")
        
        # Load the latest JSON data
        raw_data = load_latest_json_data()
        if not raw_data:
            logger.warning("No JSON data files found, using sample data")
            raw_data = generate_sample_data()
        
        logger.info(f"Loaded raw data with keys: {list(raw_data.keys())}")
        
        # Calculate enhanced metrics
        metrics = calculate_dashboard_metrics(raw_data)
        if not metrics:
            logger.error("Failed to calculate metrics")
            return jsonify({'error': 'Failed to process data'}), 500
        
        # Prepare response data
        response_data = {
            'date': raw_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'timestamp': raw_data.get('timestamp', datetime.now().isoformat()),
            'detailed_data': raw_data.get('detailed_data', {}),
            'metrics': metrics,
            'raw_summary': {
                'members_analyzed': raw_data.get('members_analyzed', 0),
                'members_with_downtime': raw_data.get('members_with_downtime', 0)
            }
        }
        
        logger.info("Successfully prepared response data")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve dashboard data', 'details': str(e)}), 500

@app.route('/api/refresh')
def api_refresh():
    """Trigger a data refresh"""
    try:
        # In a real implementation, this would trigger get_reports.py
        # For now, just reload the existing data
        data = load_latest_json_data()
        if data:
            return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'No data available'}), 404
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'status': 'error', 'message': 'Refresh failed'}), 500

@app.route('/api/export')
def api_export():
    """Export current data"""
    try:
        data = load_latest_json_data()
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': 'Export failed'}), 500

if __name__ == '__main__':
    print("🚀 Starting ClickUp Enhanced Dashboard v2...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    print("💡 Make sure you have JSON data files from get_reports.py")
    app.run(debug=True, host='0.0.0.0', port=5001)