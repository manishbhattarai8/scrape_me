import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Scraping configuration
URL = "https://nepalipatro.com.np/vegetables"
HEADLESS = False  # Set to True for production
WAIT_TIME = 10  # seconds to wait for page load
IMPLICIT_WAIT = 5  # seconds for element finding

# Browser configuration (Arc browser compatible)
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
]

# Data storage
OUTPUT_FILE = DATA_DIR / "vegetables_data.json"
LOG_FILE = LOGS_DIR / "scraper.log"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)