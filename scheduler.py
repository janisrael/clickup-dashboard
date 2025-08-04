from threading import Thread
import schedule
import time
from services.dashboard_service import update_dashboard_cache

def background_job():
    schedule.every(10).minutes.do(update_dashboard_cache)
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    update_dashboard_cache()  # Initial update
    Thread(target=background_job, daemon=True).start()
