"""
Treasury HUB - Configuration Settings
=====================================
All configuration settings for the Treasury HUB application
"""

import os
from pathlib import Path

# ==============================================================================
# PROJECT STRUCTURE
# ==============================================================================

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_FOLDER = PROJECT_ROOT / "data"
LOGS_FOLDER = PROJECT_ROOT / "logs"
BACKUPS_FOLDER = PROJECT_ROOT / "backups"
EXPORTS_FOLDER = PROJECT_ROOT / "exports"

# Create folders if they don't exist
DATA_FOLDER.mkdir(exist_ok=True)
LOGS_FOLDER.mkdir(exist_ok=True)
BACKUPS_FOLDER.mkdir(exist_ok=True)
EXPORTS_FOLDER.mkdir(exist_ok=True)

# ==============================================================================
# FILE PATHS
# ==============================================================================

# Main files
EXCEL_FILE_PATH = DATA_FOLDER / "TREASURY DASHBOARD.xlsx"
DATABASE_PATH = DATA_FOLDER / "treasury_hub.db"
LOG_FILE_PATH = LOGS_FOLDER / "treasury_sync.log"

# Backup settings
BACKUP_RETENTION_DAYS = 30
AUTO_BACKUP_ENABLED = True

# ==============================================================================
# SYNC SETTINGS
# ==============================================================================

# Automatic sync configuration
SYNC_INTERVAL_MINUTES = 30  # Sync every 30 minutes
DAILY_SYNC_TIMES = ["09:00", "17:00"]  # Additional daily syncs at 9 AM and 5 PM

# Sync behavior
SYNC_ON_STARTUP = True
SYNC_RETRY_ATTEMPTS = 3
SYNC_RETRY_DELAY_SECONDS = 60

# ==============================================================================
# APP SETTINGS
# ==============================================================================

# Streamlit app configuration
APP_TITLE = "Treasury HUB"
APP_ICON = "🏦"
APP_LAYOUT = "wide"
DEBUG_MODE = True

# Page settings
DEFAULT_PAGE = "home"
ENABLE_SIDEBAR = True

# ==============================================================================
# DATABASE SETTINGS
# ==============================================================================

# Database configuration
DB_TIMEOUT = 30  # seconds
DB_CHECK_SAME_THREAD = False

# Data retention
KEEP_HISTORICAL_DATA = True
DATA_RETENTION_MONTHS = 24  # Keep 2 years of data

# ==============================================================================
# FX DEALS SETTINGS
# ==============================================================================

# Supported currencies
SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CHF", 
    "CAD", "AUD", "NOK", "SEK", "DKK"
]

# FX deal validation
MIN_DEAL_AMOUNT = 1000
MAX_DEAL_AMOUNT = 50000000
RATE_DECIMAL_PLACES = 6

# ==============================================================================
# LOGGING SETTINGS
# ==============================================================================

# Logging configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file settings
LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 5
LOG_ROTATION_ENABLED = True

# ==============================================================================
# NOTIFICATIONS SETTINGS (Future feature)
# ==============================================================================

# Email notifications
EMAIL_NOTIFICATIONS_ENABLED = False
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = "treasury@yourcompany.com"
NOTIFICATION_RECIPIENTS = ["treasury.manager@yourcompany.com"]

# Notification triggers
NOTIFY_ON_SYNC_FAILURE = True
NOTIFY_ON_LARGE_FX_DEALS = True
LARGE_FX_DEAL_THRESHOLD = 1000000  # 1M EUR

# ==============================================================================
# SECURITY SETTINGS (Future feature)
# ==============================================================================

# Authentication
REQUIRE_AUTHENTICATION = False
SESSION_TIMEOUT_MINUTES = 480  # 8 hours
PASSWORD_MIN_LENGTH = 8

# Access control
ADMIN_USERS = ["admin", "treasury.manager"]
READ_ONLY_USERS = ["treasury.viewer"]

# ==============================================================================
# API SETTINGS (Future feature)
# ==============================================================================

# External API integration
ENABLE_MARKET_DATA_API = False
FX_RATES_API_KEY = ""
FX_RATES_PROVIDER = "exchangerate-api.com"

# SharePoint integration
SHAREPOINT_INTEGRATION_ENABLED = False
SHAREPOINT_SITE_URL = ""
SHAREPOINT_CLIENT_ID = ""
SHAREPOINT_CLIENT_SECRET = ""

# ==============================================================================
# PERFORMANCE SETTINGS
# ==============================================================================

# Caching
ENABLE_DATA_CACHING = True
CACHE_TIMEOUT_MINUTES = 15

# Chart settings
CHART_MAX_DATA_POINTS = 1000
CHART_DEFAULT_HEIGHT = 400
CHART_THEME = "plotly_white"

# ==============================================================================
# DEVELOPMENT SETTINGS
# ==============================================================================

# Development mode
DEVELOPMENT_MODE = True
SHOW_DEBUG_INFO = True
ENABLE_PROFILING = False

# Test data
CREATE_SAMPLE_DATA = False
SAMPLE_DATA_RECORDS = 100

# ==============================================================================
# EXPORT SETTINGS
# ==============================================================================

# Excel export settings
EXCEL_EXPORT_FORMAT = "xlsx"
INCLUDE_CHARTS_IN_EXPORT = True
EXPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Report settings
DEFAULT_REPORT_PERIOD = "monthly"
REPORT_CURRENCY = "EUR"

# ==============================================================================
# ERROR HANDLING
# ==============================================================================

# Error handling
GRACEFUL_ERROR_HANDLING = True
SHOW_ERROR_DETAILS = DEBUG_MODE
ERROR_RETRY_ATTEMPTS = 3

# Data validation
STRICT_DATA_VALIDATION = True
VALIDATE_EXCEL_STRUCTURE = True

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_excel_file_path():
    """Get the Excel file path, checking if it exists"""
    if EXCEL_FILE_PATH.exists():
        return str(EXCEL_FILE_PATH)
    else:
        return None

def get_database_path():
    """Get the database path"""
    return str(DATABASE_PATH)

def get_log_file_path():
    """Get the log file path"""
    return str(LOG_FILE_PATH)

def create_backup_path():
    """Create a backup file path with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return BACKUPS_FOLDER / f"treasury_hub_backup_{timestamp}.db"

def get_export_path(filename):
    """Get export file path"""
    return EXPORTS_FOLDER / filename

def print_config():
    """Print current configuration for debugging"""
    print("🏦 Treasury HUB Configuration")
    print("=" * 40)
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📄 Excel File: {EXCEL_FILE_PATH}")
    print(f"🗄️ Database: {DATABASE_PATH}")
    print(f"📋 Log File: {LOG_FILE_PATH}")
    print(f"🔄 Sync Interval: {SYNC_INTERVAL_MINUTES} minutes")
    print(f"🐛 Debug Mode: {DEBUG_MODE}")
    print(f"📊 App Title: {APP_TITLE}")
    print("=" * 40)

# ==============================================================================
# ENVIRONMENT VARIABLES (Optional)
# ==============================================================================

# Override settings with environment variables if they exist
if os.getenv("TREASURY_EXCEL_PATH"):
    EXCEL_FILE_PATH = Path(os.getenv("TREASURY_EXCEL_PATH"))

if os.getenv("TREASURY_DB_PATH"):
    DATABASE_PATH = Path(os.getenv("TREASURY_DB_PATH"))

if os.getenv("TREASURY_SYNC_INTERVAL"):
    SYNC_INTERVAL_MINUTES = int(os.getenv("TREASURY_SYNC_INTERVAL"))

if os.getenv("TREASURY_DEBUG"):
    DEBUG_MODE = os.getenv("TREASURY_DEBUG").lower() == "true"
