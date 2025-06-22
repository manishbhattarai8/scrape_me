#!/usr/bin/env python3
"""
Check the status of the vegetable price scheduler
"""

import sys
import json
import psutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import config

def main():
    print("=== Vegetable Price Scheduler Status ===\n")
    
    # Check status file
    status_file = config.DATA_DIR / "scheduler_status.json"
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            print(f"Status File: {status_file}")
            print(f"Last Updated: {status.get('last_updated', 'Unknown')}")
            print(f"Schedule Type: {status.get('schedule_type', 'Unknown')}")
            print(f"Status: {status.get('status', 'Unknown')}")
            
            if status.get('last_successful_run'):
                print(f"Last Successful Run: {status['last_successful_run']}")
                if status.get('last_run_duration'):
                    print(f"Last Run Duration: {status['last_run_duration']:.2f} seconds")
            
            if status.get('last_failed_run'):
                print(f"Last Failed Run: {status['last_failed_run']}")
                print(f"Last Error: {status.get('last_error', 'Unknown')}")
            
        except Exception as e:
            print(f"Error reading status file: {e}")
    else:
        print("No status file found. Scheduler may not have been started yet.")
    
    print()
    
    # Check for running process
    print("=== Process Status ===")
    scheduler_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'scheduler.py' in ' '.join(cmdline):
                create_time = datetime.fromtimestamp(proc.info['create_time'])
                print(f"Scheduler Process Found:")
                print(f"  PID: {proc.info['pid']}")
                print(f"  Started: {create_time}")
                print(f"  Command: {' '.join(cmdline)}")
                scheduler_running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not scheduler_running:
        print("No scheduler process currently running.")
    
    print()
    
    # Check recent data
    print("=== Recent Data ===")
    data_file = config.OUTPUT_FILE
    if data_file.exists():
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            if data:
                latest = data[-1]
                print(f"Last Scrape: {latest.get('scrape_timestamp', 'Unknown')}")
                print(f"Vegetables Scraped: {latest.get('vegetables_count', 0)}")
            else:
                print("No scraping data found.")
        except Exception as e:
            print(f"Error reading data file: {e}")
    else:
        print("No data file found.")

if __name__ == "__main__":
    main()