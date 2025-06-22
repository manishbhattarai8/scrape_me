#!/usr/bin/env python3
"""
Start the vegetable price scheduler
Usage: python scripts/start_scheduler.py [--schedule SCHEDULE_TYPE]
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scheduler import VegetablePriceScheduler
from scheduler_config import get_config

def main():
    parser = argparse.ArgumentParser(description='Start Vegetable Price Scheduler')
    parser.add_argument('--schedule', '-s', 
                       choices=list(get_config().SCHEDULES.keys()),
                       default='daily_morning',
                       help='Schedule type to use')
    parser.add_argument('--background', '-b',
                       action='store_true',
                       help='Run in background (daemon mode)')
    
    args = parser.parse_args()
    
    print(f"Starting vegetable price scheduler with schedule: {args.schedule}")
    
    scheduler = VegetablePriceScheduler(args.schedule)
    
    if args.background:
        # TODO: Implement daemon mode for background running
        print("Background mode not yet implemented. Running in foreground.")
    
    try:
        next_run = scheduler.get_next_run_time()
        if next_run:
            print(f"Next scheduled run: {next_run}")
        
        print("Press Ctrl+C to stop the scheduler")
        scheduler.start()
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()