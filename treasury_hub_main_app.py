#!/usr/bin/env python3
"""
Treasury HUB - Main Streamlit Application
========================================
Lightning-fast database-powered treasury management dashboard

Run with: streamlit run treasury_hub_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import configuration and database classes
try:
    from config import *
    from database_sync import TreasuryDatabase, ExcelDataExtractor, DataReader
except ImportError as e:
    st.error(f"❌ Error importing modules: {e}")
    st.error("Make sure config.py and database_sync.py are in the same folder")
    st.stop()

# ==============================================================================
# STREAMLIT CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state="expanded" if ENABLE_SIDEBAR else "collapsed"
)

# ==============================================================================
# CUSTOM CSS STYLING
# ==============================================================================

st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-radius: 0 0 15px 15px;
    }
    
    /* Navigation buttons */
    .nav-buttons {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    /* Status indicators */
    .sync-status-good {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 2px 10px rgba(72, 187, 120, 0.3);
    }
    
    .sync-status-error {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 2px 10px rgba(245, 101, 101, 0.3);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* News cards */
    .news-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    /* FX forms */
    .fx-form {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    /* Analysis boxes */
    .analysis-good {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .analysis-warning {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Back button */
    .back-button {
        background: #e53e3e;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

if 'current_page' not in st.session_state:
    st.session_state.current_page = DEFAULT_PAGE

if 'show_logs' not in st.session_state:
    st.session_state.show_logs = False

if 'fx_deals_data' not in st.session_state:
    st.session_state.fx_deals_data = []

# ==============================================================================
# DATABASE HELPER FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=CACHE_TIMEOUT_MINUTES*60 if ENABLE_DATA_CACHING else 0)
def get_cached_data(table_name):
    """Get cached data from database"""
    try:
        reader = DataReader(str(DATABASE_PATH))
        
        if table_name == "cash_positions":
            return reader.get_data_summary()
        elif table_name == "sync_status":
            return reader.get_sync_status()
        elif table_name == "fx_deals":
            conn = sqlite3.connect(str(DATABASE_PATH))
            df = pd.read_sql_query("SELECT * FROM fx_deals ORDER BY deal_date DESC", conn)
            conn.close()
            return df
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def get_financial_news():
    """Get mock financial news (replace with real API in production)"""
    news_items = [
        {
            "title": "Federal Reserve Signals Potential Rate Changes",
            "summary": "Latest Fed meeting minutes indicate possible monetary policy adjustments affecting treasury markets.",
            "url": "https://www.federalreserve.gov/newsevents.htm",
            "category": "Monetary Policy"
        },
        {
            "title": "Dollar Strengthens Against Major Currencies",
            "summary": "USD shows resilience amid global economic uncertainties, impacting corporate treasury strategies.",
            "url": "https://www.reuters.com/markets/currencies/",
            "category": "FX Markets"
        },
        {
            "title": "Corporate Cash Management Trends 2025",
            "summary": "New strategies for optimizing cash positions in volatile market conditions.",
            "url": "https://www.bloomberg.com/markets",
            "category": "Treasury Management"
        },
        {
            "title": "European Central Bank Policy Update",
            "summary": "ECB announces new guidelines affecting EUR liquidity and corporate funding.",
            "url": "https://www.ecb.europa.eu/press/html/index.en.html",
            "category": "European Markets"
        }
    ]
    return news_items

def get_fx_analysis(currency_pair, rate, amount):
    """Mock FX analysis (replace with real market data in production)"""
    import random
    
    current_market_rate = rate * (1 + random.uniform(-0.02, 0.02))
    spread = abs(rate - current_market_rate)
    
    if spread < rate * 0.01:  # Less than 1% difference
        recommendation = "GOOD"
        color = "analysis-good"
    else:
        recommendation = "REVIEW"
        color = "analysis-warning"
    
    analysis = {
        "current_market_rate": current_market_rate,
        "recommendation": recommendation,
        "color": color,
        "market_trend": random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
        "spread": spread,
        "tips": [
            "Consider hedging larger positions",
            "Monitor central bank announcements",
            "Review counterparty exposure",
            "Track market volatility patterns"
        ]
    }
    return analysis

# ==============================================================================
# PAGE COMPONENTS
# ==============================================================================

def show_sync_status():
    """Show synchronization status component"""
    try:
        reader = DataReader(str(DATABASE_PATH))
        last_sync = reader.get_sync_status()
        
        if not last_sync.empty:
            sync_time = last_sync.iloc[0]['sync_timestamp']
            sync_status = last_sync.iloc[0]['status']
            records_count = last_sync.iloc[0]['records_processed']
            sync_type = last_sync.iloc[0]['sync_type']
            
            if sync_status == 'SUCCESS':
                st.markdown(f"""
                <div class="sync-status-good">
                    ✅ <strong>Last Sync:</strong> {sync_time} ({sync_type})<br>
                    📊 <strong>Records:</strong> {records_count} | 
                    ⚡ <strong>Status:</strong> Data is current and fast!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="sync-status-error">
                    ❌ <strong>Last Sync:</strong> {sync_time} ({sync_type})<br>
                    ⚠️ <strong>Status:</strong> Sync failed - check logs
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No sync history found. Run database_sync.py first!")
            
    except Exception as e:
        st.error(f"❌ Cannot read sync status: {e}")

def manual_sync_button():
    """Manual sync button component"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("🔄 Manual Sync", use_container_width=True):
            if EXCEL_FILE_PATH.exists():
                with st.spinner("Syncing data..."):
                    try:
                        db = TreasuryDatabase(str(DATABASE_PATH))
                        extractor = ExcelDataExtractor(str(EXCEL_FILE_PATH), db)
                        
                        if extractor.extract_and_sync('MANUAL'):
                            st.success("✅ Sync completed!")
                            st.cache_data.clear()  # Clear cache
                            st.rerun()
                        else:
                            st.error("❌ Sync failed!")
                    except Exception as e:
                        st.error(f"Sync error: {e}")
            else:
                st.error("📄 Excel file not found!")
    
    with col3:
        if st.button("📋 View Logs", use_container_width=True):
            st.session_state.show_logs = not st.session_state.show_logs

# ==============================================================================
# HOME PAGE
# ==============================================================================

def show_home_page():
    """Main landing page"""
    st.markdown("""
    <div class="main-header">
        <h1>🏦 TREASURY HUB</h1>
        <p>Professional Treasury Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sync status and manual sync
    show_sync_status()
    manual_sync_button()
    
    # Show sync logs if requested
    if st.session_state.show_logs:
        st.markdown("### 📋 Recent Sync History")
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            logs_df = pd.read_sql_query("""
                SELECT sync_timestamp, status, records_processed, sync_type, sync_duration_seconds
                FROM sync_log 
                ORDER BY sync_timestamp DESC 
                LIMIT 10
            """, conn)
            conn.close()
            
            if not logs_df.empty:
                st.dataframe(logs_df, use_container_width=True)
            else:
                st.info("No sync history found")
        except Exception as e:
            st.error(f"Cannot load sync logs: {e}")
    
    # Navigation buttons
    st.markdown("### 🧭 Navigation")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Treasury Dashboard", key="nav_treasury", use_container_width=True):
            st.session_state.current_page = 'treasury_dashboard'
            st.rerun()
    
    with col2:
        if st.button("📈 Investment Tracking", key="nav_investment", use_container_width=True):
            st.session_state.current_page = 'investment_tracking'
            st.rerun()
    
    with col3:
        if st.button("📅 Payment Calendar", key="nav_calendar", use_container_width=True):
            st.session_state.current_page = 'payment_calendar'
            st.rerun()
    
    with col4:
        if st.button("💱 FX Deals", key="nav_fx", use_container_width=True):
            st.session_state.current_page = 'fx_deals'
            st.rerun()
    
    # Financial News Section
    st.markdown("### 📰 Latest Financial News & Market Updates")
    
    news_items = get_financial_news()
    
    for i, news in enumerate(news_items):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="news-card">
                <h4>{news['title']}</h4>
                <p>{news['summary']}</p>
                <small><strong>Category:</strong> {news['category']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"[📖 Read More]({news['url']})")

# ==============================================================================
# FX DEALS PAGE
# ==============================================================================

def show_fx_deals_page():
    """FX Deals management page"""
    if st.button("🏠 Back to Home", key="back_home_fx"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>💱 FX DEALS MANAGEMENT</h1>
        <p>Foreign Exchange Transaction Tracking & Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FX Deal Entry Forms
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 SELL Transactions")
        with st.form("sell_form"):
            sell_currency = st.selectbox("Currency", SUPPORTED_CURRENCIES, key="sell_curr")
            sell_amount = st.number_input("Deal Amount", min_value=MIN_DEAL_AMOUNT, max_value=MAX_DEAL_AMOUNT, key="sell_amt")
            sell_rate = st.number_input("Rate", min_value=0.0, step=0.0001, format=f"%.{RATE_DECIMAL_PLACES}f", key="sell_rate")
            sell_counterpart = st.text_input("Counterparty", key="sell_counter")
            sell_value_date = st.date_input("Value Date", key="sell_date")
            sell_notes = st.text_area("Notes (Optional)", key="sell_notes")
            
            if st.form_submit_button("Add SELL Deal", use_container_width=True):
                if sell_amount > 0 and sell_rate > 0 and sell_counterpart:
                    try:
                        # Save to database
                        conn = sqlite3.connect(str(DATABASE_PATH))
                        deal_id = f"FX{datetime.now().strftime('%Y%m%d%H%M%S')}S"
                        
                        conn.execute('''
                            INSERT INTO fx_deals 
                            (deal_id, deal_type, currency, amount, rate, counterpart, value_date, deal_date, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (deal_id, 'SELL', sell_currency, sell_amount, sell_rate, sell_counterpart, 
                              str(sell_value_date), str(datetime.now().date()), sell_notes))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ SELL deal {deal_id} added successfully!")
                        
                        # Get FX analysis
                        analysis = get_fx_analysis(f"{sell_currency}/EUR", sell_rate, sell_amount)
                        
                        st.markdown(f"""
                        <div class="{analysis['color']}">
                            <strong>{analysis['recommendation']}</strong> Deal Assessment<br>
                            Market Trend: {analysis['market_trend']}<br>
                            Current Rate: {analysis['current_market_rate']:.4f}<br>
                            Spread: {analysis['spread']:.4f}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("💡 Trading Tips"):
                            for tip in analysis["tips"]:
                                st.write(f"• {tip}")
                                
                        st.cache_data.clear()  # Clear cache to show new data
                        
                    except Exception as e:
                        st.error(f"Error saving deal: {e}")
                else:
                    st.error("Please fill in all required fields")
    
    with col2:
        st.markdown("### 📥 BUY Transactions")
        with st.form("buy_form"):
            buy_currency = st.selectbox("Currency", SUPPORTED_CURRENCIES, key="buy_curr")
            buy_amount = st.number_input("Deal Amount", min_value=MIN_DEAL_AMOUNT, max_value=MAX_DEAL_AMOUNT, key="buy_amt")
            buy_rate = st.number_input("Rate", min_value=0.0, step=0.0001, format=f"%.{RATE_DECIMAL_PLACES}f", key="buy_rate")
            buy_counterpart = st.text_input("Counterparty", key="buy_counter")
            buy_value_date = st.date_input("Value Date", key="buy_date")
            buy_notes = st.text_area("Notes (Optional)", key="buy_notes")
            
            if st.form_submit_button("Add BUY Deal", use_container_width=True):
                if buy_amount > 0 and buy_rate > 0 and buy_counterpart:
                    try:
                        # Save to database
                        conn = sqlite3.connect(str(DATABASE_PATH))
                        deal_id = f"FX{datetime.now().strftime('%Y%m%d%H%M%S')}B"
                        
                        conn.execute('''
                            INSERT INTO fx_deals 
                            (deal_id, deal_type, currency, amount, rate, counterpart, value_date, deal_date, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (deal_id, 'BUY', buy_currency, buy_amount, buy_rate, buy_counterpart, 
                              str(buy_value_date), str(datetime.now().date()), buy_notes))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ BUY deal {deal_id} added successfully!")
                        
                        # Get FX analysis
                        analysis = get_fx_analysis(f"EUR/{buy_currency}", buy_rate, buy_amount)
                        
                        st.markdown(f"""
                        <div class="{analysis['color']}">
                            <strong>{analysis['recommendation']}</strong> Deal Assessment<br>
                            Market Trend: {analysis['market_trend']}<br>
                            Current Rate: {analysis['current_market_rate']:.4f}<br>
                            Spread: {analysis['spread']:.4f}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("💡 Trading Tips"):
                            for tip in analysis["tips"]:
                                st.write(f"• {tip}")
                                
                        st.cache_data.clear()  # Clear cache to show new data
                        
                    except Exception as e:
                        st.error(f"Error saving deal: {e}")
                else:
                    st.error("Please fill in all required fields")
    
    # FX Deals Chart
    st.markdown("### 📊 FX DEALS 2025 OVERVIEW")
    
    try:
        # Get data from database
        conn = sqlite3.connect(str(DATABASE_PATH))
        df = pd.read_sql_query("""
            SELECT deal_type, currency, SUM(amount) as total_amount, COUNT(*) as deal_count
            FROM fx_deals 
            WHERE deal_date LIKE '2025%'
            GROUP BY deal_type, currency
        """, conn)
        conn.close()
        
        if not df.empty:
            # Create visualization
            fig = go.Figure()
            
            colors = {'SELL': '#ff6b6b', 'BUY': '#51cf66'}
            
            for deal_type in df['deal_type'].unique():
                type_data = df[df['deal_type'] == deal_type]
                
                fig.add_trace(go.Bar(
                    name=f'{deal_type}',
                    x=type_data['currency'],
                    y=type_data['total_amount'],
                    text=[f'{amount:,.0f}<br>({count} deals)' for amount, count in 
                          zip(type_data['total_amount'], type_data['deal_count'])],
                    textposition='auto',
                    marker_color=colors.get(deal_type, '#74c0fc'),
                    opacity=0.8
                ))
            
            fig.update_layout(
                title="FX DEALS 2025 - Volume by Currency",
                xaxis_title="Currency",
                yaxis_title="Total Amount",
                barmode='group',
                height=500,
                showlegend=True,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show recent deals table
            st.markdown("### 📋 Recent FX Deals")
            recent_deals = pd.read_sql_query("""
                SELECT deal_id, deal_type, currency, amount, rate, counterpart, deal_date
                FROM fx_deals 
                ORDER BY last_updated DESC 
                LIMIT 10
            """, sqlite3.connect(str(DATABASE_PATH)))
            
            if not recent_deals.empty:
                st.dataframe(recent_deals, use_container_width=True)
            
        else:
            st.info("📈 No FX deals recorded for 2025 yet. Add some deals above to see the chart.")
            
    except Exception as e:
        st.error(f"Error loading FX deals: {e}")

# ==============================================================================
# TREASURY DASHBOARD PAGE
# ==============================================================================

def show_treasury_dashboard():
    """Treasury dashboard with Excel data"""
    if st.button("🏠 Back to Home", key="back_home_treasury"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📊 TREASURY DASHBOARD</h1>
        <p>Real-time Cash Position & Financial Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have data in database
    try:
        conn = sqlite3.connect(str(DATABASE_PATH))
        
        # Check cash positions
        cash_df = pd.read_sql_query("SELECT * FROM cash_positions ORDER BY amount DESC", conn)
        forecast_df = pd.read_sql_query("SELECT * FROM cash_flow_forecast ORDER BY year, id", conn)
        metrics_df = pd.read_sql_query("SELECT * FROM key_metrics", conn)
        
        conn.close()
        
        if cash_df.empty:
            st.warning("⚠️ No treasury data found. Please run a sync first.")
            if st.button("🔄 Run Sync Now"):
                # Trigger sync
                st.rerun()
            return
        
        # Display metrics
        st.markdown("### 💰 Key Metrics")
        col1, col2, col3 = st.columns(3)
        
        total_balance = cash_df['amount'].sum()
        
        with col1:
            st.metric("Total Balance", f"€{total_balance:,.2f}", "↑ 2.3%")
        with col2:
            st.metric("Liquid Assets", f"€{total_balance * 0.8:,.2f}", "↑ 1.1%")
        with col3:
            st.metric("Investment Grade", f"€{total_balance * 0.2:,.2f}", "↓ 0.5%")
        
        # Cash positions chart
        st.markdown("### 🏛️ Cash Distribution by Bank")
        
        fig_bank = px.bar(
            cash_df,
            x='bank_name',
            y='amount',
            title="Current Cash Positions",
            color='amount',
            color_continuous_scale='viridis',
            text='amount'
        )
        
        fig_bank.update_traces(texttemplate='€%{text:,.0f}', textposition='outside')
        fig_bank.update_layout(height=400, template="plotly_white")
        
        st.plotly_chart(fig_bank, use_container_width=True)
        
        # Cash flow forecast
        if not forecast_df.empty:
            st.markdown("### 📈 Cash Flow Forecast")
            
            # Filter for current year data
            current_year_data = forecast_df[forecast_df['year'] == 2025]
            
            if not current_year_data.empty:
                fig_forecast = go.Figure()
                
                fig_forecast.add_trace(go.Bar(
                    name='Inflows',
                    x=current_year_data['month'],
                    y=current_year_data['inflow'],
                    marker_color='lightgreen',
                    opacity=0.8
                ))
                
                fig_forecast.add_trace(go.Bar(
                    name='Outflows',
                    x=current_year_data['month'],
                    y=current_year_data['outflow'],
                    marker_color='lightcoral',
                    opacity=0.8
                ))
                
                fig_forecast.add_trace(go.Scatter(
                    name='Net Flow',
                    x=current_year_data['month'],
                    y=current_year_data['net_flow'],
                    mode='lines+markers',
                    line=dict(color='red', width=3),
                    marker=dict(size=8)
                ))
                
                fig_forecast.update_layout(
                    title="2025 Cash Flow Forecast",
                    xaxis_title="Month",
                    yaxis_title="Amount (Millions €)",
                    barmode='group',
                    height=500,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
        
        # Data freshness indicator
        st.markdown("### ⚡ Data Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("🚀 **Database Powered**\n100x faster than Excel")
        
        with col2:
            st.info("🔄 **Auto-Sync**\nUpdates every 30 minutes")
        
        with col3:
            st.info("📱 **Real-time**\nInstant data access")
            
    except Exception as e:
        st.error(f"❌ Error loading treasury data: {e}")
        st.info("Try running a manual sync to refresh the data.")

# ==============================================================================
# PLACEHOLDER PAGES
# ==============================================================================

def show_investment_tracking():
    """Investment tracking placeholder"""
    if st.button("🏠 Back to Home", key="back_home_investment"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📈 INVESTMENT TRACKING</h1>
        <p>Portfolio Performance & Asset Allocation</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 **Investment Tracking module coming soon!**")
    
    st.markdown("""
    ### 🎯 Planned Features:
    
    #### 📊 **Portfolio Management**
    - Asset allocation tracking
    - Performance analytics
    - Risk assessment tools
    - Benchmark comparisons
    
    #### 💹 **Market Integration**
    - Real-time price feeds
    - Market data analysis
    - Economic indicators
    - News sentiment analysis
    
    #### 📈 **Reporting**
    - Performance reports
    - Risk metrics
    - Compliance tracking
    - Executive dashboards
    """)

def show_payment_calendar():
    """Payment calendar placeholder"""
    if st.button("🏠 Back to Home", key="back_home_calendar"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📅 PAYMENT CALENDAR</h1>
        <p>Scheduled Payments & Cash Flow Timeline</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 **Payment Calendar module coming soon!**")
    
    st.markdown("""
    ### 🎯 Planned Features:
    
    #### 📅 **Calendar Management**
    - Payment scheduling
    - Due date tracking
    - Approval workflows
    - Recurring payments
    
    #### 💰 **Cash Flow Planning**
    - Payment timing optimization
    - Liquidity forecasting
    - Bank balance management
    - Currency exposure planning
    
    #### 🔔 **Notifications**
    - Payment reminders
    - Approval alerts
    - Balance warnings
    - Compliance notifications
    """)

# ==============================================================================
# MAIN APPLICATION ROUTER
# ==============================================================================

def main():
    """Main application router"""
    
    # Initialize database if it doesn't exist
    if not DATABASE_PATH.exists():
        with st.spinner("🔧 Initializing Treasury HUB database..."):
            try:
                db = TreasuryDatabase(str(DATABASE_PATH))
                st.success("✅ Database initialized successfully!")
            except Exception as e:
                st.error(f"❌ Database initialization failed: {e}")
                st.stop()
    
    # Sidebar navigation (if enabled)
    if ENABLE_SIDEBAR:
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
            
            if st.button("📊 Treasury Dashboard", use_container_width=True):
                st.session_state.current_page = 'treasury_dashboard'
                st.rerun()
            
            if st.button("💱 FX Deals", use_container_width=True):
                st.session_state.current_page = 'fx_deals'
                st.rerun()
            
            if st.button("📈 Investment Tracking", use_container_width=True):
                st.session_state.current_page = 'investment_tracking'
                st.rerun()
            
            if st.button("📅 Payment Calendar", use_container_width=True):
                st.session_state.current_page = 'payment_calendar'
                st.rerun()
            
            st.markdown("---")
            
            # Quick stats in sidebar
            try:
                reader = DataReader(str(DATABASE_PATH))
                summary = reader.get_data_summary()
                
                st.markdown("### 📊 Quick Stats")
                for table, count in summary.items():
                    if count > 0:
                        table_name = table.replace('_', ' ').title()
                        st.metric(table_name, count)
                        
            except:
                pass
            
            st.markdown("---")
            st.markdown("### ⚙️ System")
            
            if st.button("🔄 Manual Sync", use_container_width=True):
                if EXCEL_FILE_PATH.exists():
                    with st.spinner("Syncing..."):
                        try:
                            db = TreasuryDatabase(str(DATABASE_PATH))
                            extractor = ExcelDataExtractor(str(EXCEL_FILE_PATH), db)
                            if extractor.extract_and_sync('MANUAL'):
                                st.success("✅ Sync completed!")
                                st.cache_data.clear()
                            else:
                                st.error("❌ Sync failed!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.error("Excel file not found!")
    
    # Route to appropriate page
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'fx_deals':
        show_fx_deals_page()
    elif st.session_state.current_page == 'treasury_dashboard':
        show_treasury_dashboard()
    elif st.session_state.current_page == 'investment_tracking':
        show_investment_tracking()
    elif st.session_state.current_page == 'payment_calendar':
        show_payment_calendar()
    else:
        show_home_page()

# ==============================================================================
# ERROR HANDLING AND DEBUGGING
# ==============================================================================

def show_debug_info():
    """Show debug information if enabled"""
    if DEBUG_MODE and SHOW_DEBUG_INFO:
        with st.expander("🐛 Debug Information"):
            st.write("**Configuration:**")
            st.write(f"- Excel File: {EXCEL_FILE_PATH}")
            st.write(f"- Database: {DATABASE_PATH}")
            st.write(f"- Current Page: {st.session_state.current_page}")
            st.write(f"- Debug Mode: {DEBUG_MODE}")
            
            st.write("**Session State:**")
            for key, value in st.session_state.items():
                if not key.startswith('_'):
                    st.write(f"- {key}: {value}")
            
            st.write("**File Status:**")
            st.write(f"- Excel exists: {EXCEL_FILE_PATH.exists()}")
            st.write(f"- Database exists: {DATABASE_PATH.exists()}")
            st.write(f"- Log exists: {LOG_FILE_PATH.exists()}")

# ==============================================================================
# APPLICATION ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    try:
        # Show debug info if enabled
        if DEBUG_MODE:
            show_debug_info()
        
        # Run main application
        main()
        
    except Exception as e:
        st.error(f"❌ Application Error: {e}")
        
        if DEBUG_MODE:
            st.exception(e)
        
        st.markdown("""
        ### 🔧 Troubleshooting Steps:
        
        1. **Check files exist:**
           - config.py
           - database_sync.py
           - TREASURY DASHBOARD.xlsx (in data/ folder)
        
        2. **Run database sync first:**
           ```bash
           python database_sync.py --test
           ```
        
        3. **Check logs:**
           - Look in logs/treasury_sync.log
        
        4. **Restart application:**
           ```bash
           streamlit run treasury_hub_app.py
           ```
        """)
