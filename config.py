import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Rate limiting
    MAX_API_CALLS_PER_MINUTE = 25
    
    # Cache settings
    CACHE_TIMEOUT_MINUTES = 5
    
    # Analysis settings
    WORK_START_HOUR = 9  # 9 AM
    DOWNTIME_THRESHOLD_HOURS = 3
    CRITICAL_DOWNTIME_HOURS = 4
    
    # Auto-refresh interval (minutes)
    AUTO_REFRESH_INTERVAL = 5