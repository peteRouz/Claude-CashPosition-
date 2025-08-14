#!/usr/bin/env python3
"""
Treasury HUB - Database Sync Script
==================================
Standalone script to sync Excel data to database
Can be run manually or as scheduled task

Usage:
    python database_sync.py           # Run once
    python database_sync.py --auto    # Run with auto-scheduler
    python database_sync.py --help    # Show help
"""

import sys
import os
import time
import argparse
import logging
import sqlite3
import pandas as pd
import numpy as np
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import configuration
try:
    from config import *
except ImportError:
    print("❌ Error: config.py not found!")
    print("📁 Make sure config.py is in the same folder as this script")
    sys.exit(1)

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    LOGS_FOLDER.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# ==============================================================================
# DATABASE SETUP
# ==============================================================================

class TreasuryDatabase:
    """Database management for Treasury HUB"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DATABASE_PATH)
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            
            # Cash positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    amount REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # Cash flow forecast table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_flow_forecast (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    inflow REAL DEFAULT 0,
                    outflow REAL DEFAULT 0,
                    net_flow REAL DEFAULT 0,
                    forecast_type TEXT DEFAULT 'FORECAST',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # FX deals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fx_deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id TEXT UNIQUE,
                    deal_type TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    rate REAL NOT NULL,
                    counterpart TEXT,
                    value_date TEXT,
                    deal_date TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    profit_loss REAL DEFAULT 0,
                    notes TEXT,
                    created_by TEXT DEFAULT 'System',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            # Data sync log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT,
                    file_modified_time TIMESTAMP,
                    status TEXT NOT NULL,
                    records_processed INTEGER DEFAULT 0,
                    error_message TEXT,
                    sync_duration_seconds REAL,
                    sync_type TEXT DEFAULT 'MANUAL'
                )
            ''')
            
            # Key metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT UNIQUE NOT NULL,
                    metric_value REAL,
                    metric_change REAL DEFAULT 0,
                    metric_change_percent REAL DEFAULT 0,
                    calculation_date DATE DEFAULT CURRENT_DATE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fx_deals_date ON fx_deals(deal_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_positions_bank ON cash_positions(bank_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp ON sync_log(sync_timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Database initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {str(e)}")
            raise

# ==============================================================================
# EXCEL DATA EXTRACTOR
# ==============================================================================

class ExcelDataExtractor:
    """Extracts data from Excel and syncs to database"""
    
    def __init__(self, excel_file_path, db_instance):
        self.excel_file = Path(excel_file_path)
        self.db = db_instance
        self.logger = logging.getLogger(__name__)
    
    def extract_and_sync(self, sync_type='MANUAL'):
        """Main sync function - extracts data from Excel and updates database"""
        start_time = datetime.now()
        
        try:
            # Check if Excel file exists
            if not self.excel_file.exists():
                raise FileNotFoundError(f"Excel file not found: {self.excel_file}")
            
            # Get file modification time
            file_modified_time = datetime.fromtimestamp(self.excel_file.stat().st_mtime)
            
            self.logger.info(f"🔄 Starting {sync_type} sync from {self.excel_file}")
            self.logger.info(f"📅 File last modified: {file_modified_time}")
            
            # Load Excel sheets with error handling
            try:
                self.logger.info("📖 Reading Excel sheets...")
                dash_sheet = pd.read_excel(self.excel_file, sheet_name="Information to feed dash", header=None)
                sheet7 = pd.read_excel(self.excel_file, sheet_name="Sheet7", header=None)
                self.logger.info("✅ Excel sheets loaded successfully")
            except Exception as e:
                raise Exception(f"Failed to read Excel sheets: {str(e)}")
            
            records_processed = 0
            
            # Extract and update each data type
            self.logger.info("💰 Syncing cash positions...")
            records_processed += self.sync_cash_positions(sheet7)
            
            self.logger.info("📈 Syncing cash flow forecast...")
            records_processed += self.sync_cash_flow_forecast(dash_sheet)
            
            self.logger.info("📊 Syncing key metrics...")
            records_processed += self.sync_key_metrics(dash_sheet, sheet7)
            
            # Calculate sync duration
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            # Log successful sync
            self.log_sync_status("SUCCESS", records_processed, None, file_modified_time, sync_duration, sync_type)
            
            self.logger.info(f"✅ {sync_type} sync completed successfully!")
            self.logger.info(f"📊 Processed {records_processed} records in {sync_duration:.2f} seconds")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            sync_duration = (datetime.now() - start_time).total_seconds()
            self.log_sync_status("ERROR", 0, error_msg, None, sync_duration, sync_type)
            self.logger.error(f"❌ {sync_type} sync failed: {error_msg}")
            return False
    
    def sync_cash_positions(self, sheet7):
        """Extract and sync cash positions by bank"""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=DB_TIMEOUT)
            
            # Clear existing cash positions for today
            today = datetime.now().date()
            conn.execute("DELETE FROM cash_positions WHERE DATE(last_updated) = ?", (today,))
            
            # Extract net cash per bank (from original code structure)
            net_cash_df = sheet7.iloc[77:91, [1, 2]].copy()
            net_cash_df.columns = ["bank_name", "amount"]
            net_cash_df.dropna(inplace=True)
            net_cash_df = net_cash_df[net_cash_df['bank_name'].notna()]
            net_cash_df = net_cash_df[net_cash_df['amount'].notna()]
            
            # Convert amount to numeric
            net_cash_df['amount'] = pd.to_numeric(net_cash_df['amount'], errors='coerce')
            net_cash_df.dropna(subset=['amount'], inplace=True)
            
            # Insert into database
            for _, row in net_cash_df.iterrows():
                conn.execute('''
                    INSERT INTO cash_positions (bank_name, currency, amount)
                    VALUES (?, ?, ?)
                ''', (str(row['bank_name']).strip(), 'EUR', float(row['amount'])))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"💰 Synced {len(net_cash_df)} cash positions")
            return len(net_cash_df)
            
        except Exception as e:
            self.logger.error(f"Error syncing cash positions: {e}")
            return 0
    
    def sync_cash_flow_forecast(self, dash_sheet):
        """Extract and sync cash flow forecast data"""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=DB_TIMEOUT)
            
            # Clear existing forecasts for today's sync
            today = datetime.now().date()
            conn.execute("DELETE FROM cash_flow_forecast WHERE DATE(last_updated) = ?", (today,))
            
            records = 0
            
            try:
                # 2025 data (columns 1-12)
                if dash_sheet.shape[1] > 12:
                    m25 = dash_sheet.iloc[2, 1:13].astype(str).tolist()
                    i25 = pd.to_numeric(dash_sheet.iloc[5, 1:13], errors='coerce').fillna(0).tolist()
                    o25 = pd.to_numeric(dash_sheet.iloc[6, 1:13], errors='coerce').fillna(0).tolist()
                    n25 = pd.to_numeric(dash_sheet.iloc[4, 1:13], errors='coerce').fillna(0).tolist()
                    
                    # Insert 2025 data
                    for month, inflow, outflow, net in zip(m25, i25, o25, n25):
                        if month and month != 'nan':
                            conn.execute('''
                                INSERT INTO cash_flow_forecast 
                                (month, year, inflow, outflow, net_flow, forecast_type)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (str(month), 2025, float(inflow), float(outflow), float(net), 'FORECAST'))
                            records += 1
                
                # 2024 data (columns 15-26)
                if dash_sheet.shape[1] > 26:
                    m24 = dash_sheet.iloc[2, 15:27].astype(str).tolist()
                    i24 = pd.to_numeric(dash_sheet.iloc[5, 15:27], errors='coerce').fillna(0).tolist()
                    o24 = pd.to_numeric(dash_sheet.iloc[6, 15:27], errors='coerce').fillna(0).tolist()
                    n24 = pd.to_numeric(dash_sheet.iloc[4, 15:27], errors='coerce').fillna(0).tolist()
                    
                    # Insert 2024 data
                    for month, inflow, outflow, net in zip(m24, i24, o24, n24):
                        if month and month != 'nan':
                            conn.execute('''
                                INSERT INTO cash_flow_forecast 
                                (month, year, inflow, outflow, net_flow, forecast_type)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (str(month), 2024, float(inflow), float(outflow), float(net), 'HISTORICAL'))
                            records += 1
                            
            except Exception as e:
                self.logger.warning(f"Partial cash flow data extraction: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📈 Synced {records} cash flow forecast records")
            return records
            
        except Exception as e:
            self.logger.error(f"Error syncing cash flow forecast: {e}")
            return 0
    
    def sync_key_metrics(self, dash_sheet, sheet7):
        """Extract and sync key performance metrics"""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=DB_TIMEOUT)
            
            # Calculate key metrics from cash positions
            try:
                total_balance = pd.to_numeric(sheet7.iloc[77:91, 2], errors='coerce').sum()
                if pd.isna(total_balance):
                    total_balance = 0
            except:
                total_balance = 0
            
            # Calculate derived metrics
            liquid_assets = total_balance * 0.8
            investment_grade = total_balance * 0.2
            
            # Mock changes for demo (in production, calculate from historical data)
            import random
            balance_change = random.uniform(-0.05, 0.05) * total_balance
            balance_change_pct = random.uniform(-2.5, 2.5)
            
            metrics = [
                ('total_balance', total_balance, balance_change, balance_change_pct),
                ('liquid_assets', liquid_assets, balance_change * 0.8, balance_change_pct * 0.8),
                ('investment_grade', investment_grade, balance_change * 0.2, balance_change_pct * 0.2)
            ]
            
            # Clear and insert metrics
            today = datetime.now().date()
            conn.execute("DELETE FROM key_metrics WHERE DATE(last_updated) = ?", (today,))
            
            for metric_name, value, change, change_pct in metrics:
                conn.execute('''
                    INSERT OR REPLACE INTO key_metrics 
                    (metric_name, metric_value, metric_change, metric_change_percent)
                    VALUES (?, ?, ?, ?)
                ''', (metric_name, float(value), float(change), float(change_pct)))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📊 Synced {len(metrics)} key metrics")
            return len(metrics)
            
        except Exception as e:
            self.logger.error(f"Error syncing key metrics: {e}")
            return 0
    
    def log_sync_status(self, status, records, error_msg, file_modified_time, sync_duration, sync_type):
        """Log sync operation status"""
        try:
            conn = sqlite3.connect(self.db.db_path, timeout=DB_TIMEOUT)
            conn.execute('''
                INSERT INTO sync_log 
                (file_path, file_modified_time, status, records_processed, error_message, sync_duration_seconds, sync_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(self.excel_file), file_modified_time, status, records, error_msg, sync_duration, sync_type))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log sync status: {e}")

# ==============================================================================
# AUTOMATED SCHEDULER
# ==============================================================================

class AutoSyncScheduler:
    """Automated sync scheduler with background operation"""
    
    def __init__(self, excel_file_path, db_instance, sync_interval_minutes=SYNC_INTERVAL_MINUTES):
        self.excel_file = excel_file_path
        self.db = db_instance
        self.extractor = ExcelDataExtractor(excel_file_path, db_instance)
        self.sync_interval = sync_interval_minutes
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
    def start_scheduler(self):
        """Start the automated sync scheduler"""
        try:
            # Clear any existing schedules
            schedule.clear()
            
            # Schedule regular sync
            schedule.every(self.sync_interval).minutes.do(
                lambda: self.extractor.extract_and_sync('AUTO'))
            
            # Schedule daily syncs at specific times
            for sync_time in DAILY_SYNC_TIMES:
                schedule.every().day.at(sync_time).do(
                    lambda: self.extractor.extract_and_sync('SCHEDULED'))
            
            self.logger.info(f"📅 Scheduler started!")
            self.logger.info(f"🔄 Auto-sync every {self.sync_interval} minutes")
            self.logger.info(f"⏰ Daily syncs at: {', '.join(DAILY_SYNC_TIMES)}")
            
            # Run initial sync
            if SYNC_ON_STARTUP:
                self.logger.info("🚀 Running initial sync...")
                self.extractor.extract_and_sync('STARTUP')
            
            self.is_running = True
            
            # Keep scheduler running
            self.logger.info("🔄 Scheduler is now running... (Press Ctrl+C to stop)")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Scheduler stopped by user")
            self.stop_scheduler()
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")
            self.stop_scheduler()
    
    def start_background_scheduler(self):
        """Start scheduler in background thread"""
        def run_scheduler():
            self.start_scheduler()
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("🔄 Background scheduler started!")
        return scheduler_thread
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        self.logger.info("⏹️ Scheduler stopped")

# ==============================================================================
# DATA READER FOR VERIFICATION
# ==============================================================================

class DataReader:
    """Fast data reader for verification and testing"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DATABASE_PATH)
        self.logger = logging.getLogger(__name__)
    
    def get_sync_status(self):
        """Get last sync information"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
            df = pd.read_sql_query("""
                SELECT sync_timestamp, status, records_processed, sync_duration_seconds, sync_type
                FROM sync_log 
                ORDER BY sync_timestamp DESC 
                LIMIT 1
            """, conn)
            conn.close()
            return df
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return pd.DataFrame()
    
    def get_data_summary(self):
        """Get summary of all data in database"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
            
            # Count records in each table
            tables = ['cash_positions', 'cash_flow_forecast', 'fx_deals', 'key_metrics', 'sync_log']
            summary = {}
            
            for table in tables:
                try:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    summary[table] = result[0] if result else 0
                except:
                    summary[table] = 0
            
            conn.close()
            return summary
        except Exception as e:
            self.logger.error(f"Error getting data summary: {e}")
            return {}

# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

def create_sample_log_file():
    """Create a sample log file with initial entry"""
    try:
        # Ensure logs directory exists
        LOGS_FOLDER.mkdir(exist_ok=True)
        
        # Create initial log entry if file doesn't exist
        if not LOG_FILE_PATH.exists():
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Treasury HUB initialized\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Log file created successfully\n")
            print(f"📋 Created log file: {LOG_FILE_PATH}")
        else:
            print(f"📋 Log file already exists: {LOG_FILE_PATH}")
            
    except Exception as e:
        print(f"❌ Error creating log file: {e}")

def print_banner():
    """Print application banner"""
    print("\n" + "="*60)
    print("🏦 TREASURY HUB - DATABASE SYNC SCRIPT")
    print("="*60)
    print(f"📁 Project: {PROJECT_ROOT}")
    print(f"📄 Excel File: {EXCEL_FILE_PATH}")
    print(f"🗄️ Database: {DATABASE_PATH}")
    print(f"📋 Log File: {LOG_FILE_PATH}")
    print("="*60 + "\n")

def check_prerequisites():
    """Check if all prerequisites are met"""
    issues = []
    
    # Check if Excel file exists
    if not EXCEL_FILE_PATH.exists():
        issues.append(f"📄 Excel file not found: {EXCEL_FILE_PATH}")
    
    # Check if data folder exists
    if not DATA_FOLDER.exists():
        issues.append(f"📁 Data folder not found: {DATA_FOLDER}")
    
    # Check if we can create database
    try:
        test_db = sqlite3.connect(":memory:")
        test_db.close()
    except Exception as e:
        issues.append(f"🗄️ Cannot create database: {e}")
    
    return issues

def main():
    """Main function with command line interface"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Treasury HUB Database Sync Script")
    parser.add_argument("--auto", action="store_true", help="Start automatic scheduler")
    parser.add_argument("--test", action="store_true", help="Test mode - verify setup only")
    parser.add_argument("--status", action="store_true", help="Show sync status and exit")
    parser.add_argument("--config", action="store_true", help="Show configuration and exit")
    parser.add_argument("--create-log", action="store_true", help="Create sample log file")
    args = parser.parse_args()
    
    # Create sample log file if requested
    if args.create_log:
        create_sample_log_file()
        return
    
    # Setup logging
    logger = setup_logging()
    
    # Print banner
    print_banner()
    
    # Show configuration if requested
    if args.config:
        print_config()
        return
    
    # Check prerequisites
    issues = check_prerequisites()
    if issues:
        print("❌ Prerequisites not met:")
        for issue in issues:
            print(f"   {issue}")
        
        if not EXCEL_FILE_PATH.exists():
            print(f"\n📥 SOLUTION:")
            print(f"   1. Download 'TREASURY DASHBOARD.xlsx' from SharePoint")
            print(f"   2. Place it in: {DATA_FOLDER}")
            print(f"   3. Run this script again")
        return
    
    try:
        # Initialize database
        print("🔧 Initializing database...")
        db = TreasuryDatabase(str(DATABASE_PATH))
        
        # Test mode - just verify setup
        if args.test:
            print("🧪 Test mode - verifying setup...")
            
            reader = DataReader(str(DATABASE_PATH))
            summary = reader.get_data_summary()
            
            print("\n📊 Database Summary:")
            for table, count in summary.items():
                print(f"   {table}: {count} records")
            
            print("\n✅ Test completed successfully!")
            return
        
        # Status mode - show last sync info
        if args.status:
            reader = DataReader(str(DATABASE_PATH))
            status_df = reader.get_sync_status()
            
            if not status_df.empty:
                print("📊 Last Sync Status:")
                print(status_df.to_string(index=False))
            else:
                print("📊 No sync history found")
            
            summary = reader.get_data_summary()
            print("\n📋 Current Data:")
            for table, count in summary.items():
                print(f"   {table}: {count} records")
            return
        
        # Auto mode - start scheduler
        if args.auto:
            print("🤖 Starting automatic sync scheduler...")
            scheduler = AutoSyncScheduler(str(EXCEL_FILE_PATH), db, SYNC_INTERVAL_MINUTES)
            scheduler.start_scheduler()  # This will run continuously
            return
        
        # Default mode - run single sync
        print("🔄 Running single sync operation...")
        extractor = ExcelDataExtractor(str(EXCEL_FILE_PATH), db)
        
        if extractor.extract_and_sync('MANUAL'):
            print("\n✅ Sync completed successfully!")
            
            # Show summary
            reader = DataReader(str(DATABASE_PATH))
            summary = reader.get_data_summary()
            
            print("\n📊 Updated Data Summary:")
            for table, count in summary.items():
                print(f"   {table}: {count} records")
            
            # Ask if user wants to start auto-sync
            try:
                response = input("\n🤖 Start automatic sync scheduler? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    print("🚀 Starting auto-sync scheduler...")
                    scheduler = AutoSyncScheduler(str(EXCEL_FILE_PATH), db, SYNC_INTERVAL_MINUTES)
                    scheduler.start_scheduler()
                else:
                    print("👋 Single sync completed. Run with --auto to start scheduler.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
        else:
            print("\n❌ Sync failed - check logs for details")
            print(f"📋 Log file: {LOG_FILE_PATH}")
    
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"\n❌ Error: {e}")
        print(f"📋 Check log file for details: {LOG_FILE_PATH}")

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def create_sample_data():
    """Create sample data for testing (when Excel file is not available)"""
    try:
        print("🧪 Creating sample data for testing...")
        
        db = TreasuryDatabase(str(DATABASE_PATH))
        conn = sqlite3.connect(str(DATABASE_PATH), timeout=DB_TIMEOUT)
        
        # Sample cash positions
        sample_banks = [
            ("Bank A", "EUR", 1500000),
            ("Bank B", "EUR", 2300000),
            ("Bank C", "USD", 1800000),
            ("Bank D", "GBP", 900000)
        ]
        
        for bank, currency, amount in sample_banks:
            conn.execute('''
                INSERT INTO cash_positions (bank_name, currency, amount)
                VALUES (?, ?, ?)
            ''', (bank, currency, amount))
        
        # Sample FX deals
        sample_fx = [
            ("FX001", "SELL", "USD", 100000, 1.0850, "Bank X", "2025-01-20"),
            ("FX002", "BUY", "GBP", 50000, 0.8650, "Bank Y", "2025-01-21"),
            ("FX003", "SELL", "EUR", 200000, 1.0000, "Bank Z", "2025-01-22")
        ]
        
        for deal_id, deal_type, currency, amount, rate, counterpart, deal_date in sample_fx:
            conn.execute('''
                INSERT INTO fx_deals (deal_id, deal_type, currency, amount, rate, counterpart, deal_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (deal_id, deal_type, currency, amount, rate, counterpart, deal_date))
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

if __name__ == "__main__":
    main()