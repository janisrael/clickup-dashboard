# run_analysis.py
from services.dashboard_logic import analyze_team_performance

def main():
    print("🚀 Starting ClickUp Team Analysis...")
    
    results = analyze_team_performance()
    
    if results:
        print("✅ Analysis completed!")
        print(f"📊 Total tasks: {results['team_metrics']['total_tasks']}")
        return results
    else:
        print("❌ Analysis failed")
        return None

if __name__ == "__main__":
    results = main()