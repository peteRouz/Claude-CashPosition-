import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import requests
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import make_interp_spline
import os
import sqlite3
import json

# Configure page
st.set_page_config(
    page_title="Treasury HUB",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern corporate look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .nav-buttons {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .nav-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 2rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .news-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    .fx-table {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .back-button {
        background: #dc3545;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'fx_deals_sell' not in st.session_state:
    st.session_state.fx_deals_sell = []
if 'fx_deals_buy' not in st.session_state:
    st.session_state.fx_deals_buy = []

# Database setup for FX deals
def init_db():
    conn = sqlite3.connect('treasury_hub.db')
    c = conn.cursor()
    
    # Create FX deals table
    c.execute('''CREATE TABLE IF NOT EXISTS fx_deals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  deal_type TEXT,
                  currency TEXT,
                  amount REAL,
                  rate REAL,
                  counterpart TEXT,
                  value_date TEXT,
                  date_created TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# Function to get financial news
def get_financial_news():
    # Mock news data - in production, integrate with real news API
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

# Function to get FX rate analysis
def get_fx_analysis(currency_pair, rate, amount):
    # Mock analysis - integrate with real FX data providers
    analysis = {
        "current_market_rate": rate * (1 + np.random.uniform(-0.02, 0.02)),
        "recommendation": "GOOD" if np.random.random() > 0.3 else "REVIEW",
        "market_trend": np.random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
        "tips": [
            "Consider hedging larger positions",
            "Monitor central bank announcements",
            "Review counterparty exposure"
        ]
    }
    return analysis

# Home Page
def show_home_page():
    st.markdown("""
    <div class="main-header">
        <h1>🏦 TREASURY HUB</h1>
        <p>Professional Treasury Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
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
    st.markdown("## 📰 Latest Financial News & Market Updates")
    
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
            if st.button(f"Read More", key=f"news_{i}"):
                st.markdown(f"[Open Article]({news['url']})")

# FX Deals Page
def show_fx_deals_page():
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
            sell_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"], key="sell_curr")
            sell_amount = st.number_input("Deal Amount", min_value=0.0, key="sell_amt")
            sell_rate = st.number_input("Rate", min_value=0.0, step=0.0001, format="%.4f", key="sell_rate")
            sell_counterpart = st.text_input("Counterparty", key="sell_counter")
            sell_value_date = st.date_input("Value Date", key="sell_date")
            
            if st.form_submit_button("Add SELL Deal"):
                # Save to database
                conn = sqlite3.connect('treasury_hub.db')
                c = conn.cursor()
                c.execute('''INSERT INTO fx_deals 
                           (deal_type, currency, amount, rate, counterpart, value_date, date_created)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         ('SELL', sell_currency, sell_amount, sell_rate, sell_counterpart, 
                          str(sell_value_date), str(datetime.now().date())))
                conn.commit()
                conn.close()
                st.success("SELL deal added successfully!")
                
                # Get FX analysis
                analysis = get_fx_analysis(f"{sell_currency}/EUR", sell_rate, sell_amount)
                
                if analysis["recommendation"] == "GOOD":
                    st.success(f"✅ Good deal! Market trend: {analysis['market_trend']}")
                else:
                    st.warning(f"⚠️ Review recommended. Market trend: {analysis['market_trend']}")
                
                with st.expander("💡 Trading Tips"):
                    for tip in analysis["tips"]:
                        st.write(f"• {tip}")
    
    with col2:
        st.markdown("### 📥 BUY Transactions")
        with st.form("buy_form"):
            buy_currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"], key="buy_curr")
            buy_amount = st.number_input("Deal Amount", min_value=0.0, key="buy_amt")
            buy_rate = st.number_input("Rate", min_value=0.0, step=0.0001, format="%.4f", key="buy_rate")
            buy_counterpart = st.text_input("Counterparty", key="buy_counter")
            buy_value_date = st.date_input("Value Date", key="buy_date")
            
            if st.form_submit_button("Add BUY Deal"):
                # Save to database
                conn = sqlite3.connect('treasury_hub.db')
                c = conn.cursor()
                c.execute('''INSERT INTO fx_deals 
                           (deal_type, currency, amount, rate, counterpart, value_date, date_created)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         ('BUY', buy_currency, buy_amount, buy_rate, buy_counterpart, 
                          str(buy_value_date), str(datetime.now().date())))
                conn.commit()
                conn.close()
                st.success("BUY deal added successfully!")
                
                # Get FX analysis
                analysis = get_fx_analysis(f"EUR/{buy_currency}", buy_rate, buy_amount)
                
                if analysis["recommendation"] == "GOOD":
                    st.success(f"✅ Good deal! Market trend: {analysis['market_trend']}")
                else:
                    st.warning(f"⚠️ Review recommended. Market trend: {analysis['market_trend']}")
                
                with st.expander("💡 Trading Tips"):
                    for tip in analysis["tips"]:
                        st.write(f"• {tip}")
    
    # FX Deals Chart
    st.markdown("### 📊 FX DEALS 2025 OVERVIEW")
    
    # Get data from database
    conn = sqlite3.connect('treasury_hub.db')
    df = pd.read_sql_query("SELECT * FROM fx_deals WHERE date_created LIKE '2025%'", conn)
    conn.close()
    
    if not df.empty:
        # Create visualization similar to your image
        fig = go.Figure()
        
        # Group by currency and deal type
        sell_data = df[df['deal_type'] == 'SELL'].groupby('currency')['amount'].sum()
        buy_data = df[df['deal_type'] == 'BUY'].groupby('currency')['amount'].sum()
        
        currencies = list(set(sell_data.index.tolist() + buy_data.index.tolist()))
        
        # Create bars for sell and buy
        for currency in currencies:
            sell_amount = sell_data.get(currency, 0)
            buy_amount = buy_data.get(currency, 0)
            
            if sell_amount > 0:
                fig.add_trace(go.Bar(
                    name=f'Sell {currency}',
                    x=['Sell'],
                    y=[sell_amount],
                    text=f'{sell_amount:,.0f}',
                    textposition='auto',
                    marker_color='red',
                    opacity=0.8
                ))
            
            if buy_amount > 0:
                fig.add_trace(go.Bar(
                    name=f'Buy {currency}',
                    x=['Buy'],
                    y=[buy_amount],
                    text=f'{buy_amount:,.0f}',
                    textposition='auto',
                    marker_color='green',
                    opacity=0.8
                ))
        
        fig.update_layout(
            title="FX DEALS 2025",
            xaxis_title="Transaction Type",
            yaxis_title="Amount",
            barmode='group',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No FX deals recorded for 2025 yet. Add some deals above to see the chart.")

# Treasury Dashboard Page (Updated from your code)
def show_treasury_dashboard():
    if st.button("🏠 Back to Home", key="back_home_treasury"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📊 TREASURY DASHBOARD</h1>
        <p>Real-time Cash Position & Financial Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if Excel file exists
    EXCEL_FILE = "TREASURY DASHBOARD.xlsx"
    
    if not os.path.exists(EXCEL_FILE):
        st.error(f"""
        📁 Excel file '{EXCEL_FILE}' not found!
        
        **Instructions:**
        1. Ensure your SharePoint file is downloaded and renamed to 'TREASURY DASHBOARD.xlsx'
        2. Place it in the same folder as this application
        3. Refresh the page
        
        **Alternative:** Upload your Excel file below:
        """)
        
        uploaded_file = st.file_uploader("Upload Treasury Dashboard Excel", type=['xlsx'])
        if uploaded_file:
            with open(EXCEL_FILE, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded successfully! Please refresh the page.")
            st.rerun()
        return
    
    try:
        # Load Excel sheets (updated to new file name)
        dash_sheet = pd.read_excel(EXCEL_FILE, sheet_name="Information to feed dash", header=None)
        sheet7 = pd.read_excel(EXCEL_FILE, sheet_name="Sheet7", header=None)
        
        # Your existing dashboard code with modern styling
        st.markdown("### 💰 Cash Position Overview")
        
        # Net Cash per Bank
        net_cash_df = sheet7.iloc[77:91, [1, 2]].copy()
        net_cash_df.columns = ["Bank", "Value_EUR"]
        net_cash_df.dropna(inplace=True)
        net_cash_df.reset_index(drop=True, inplace=True)
        
        # Display current balance
        total_balance = net_cash_df["Value_EUR"].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Balance", f"€{total_balance:,.2f}", "↑ 2.3%")
        with col2:
            st.metric("Liquid Assets", f"€{total_balance * 0.8:,.2f}", "↑ 1.1%")
        with col3:
            st.metric("Investment Grade", f"€{total_balance * 0.2:,.2f}", "↓ 0.5%")
        
        # Cash Flow Forecast Chart
        st.markdown("### 📈 Cash Flow Forecast")
        
        # Extract forecast data
        m25 = dash_sheet.iloc[2, 1:13].astype(str).tolist()
        i25 = dash_sheet.iloc[5, 1:13].astype(float).tolist()
        o25 = dash_sheet.iloc[6, 1:13].astype(float).tolist()
        n25 = dash_sheet.iloc[4, 1:13].astype(float).tolist()
        
        # Create modern Plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Inflows',
            x=m25,
            y=i25,
            marker_color='lightgreen',
            opacity=0.8
        ))
        
        fig.add_trace(go.Bar(
            name='Outflows',
            x=m25,
            y=o25,
            marker_color='lightcoral',
            opacity=0.8
        ))
        
        fig.add_trace(go.Scatter(
            name='Net Flow',
            x=m25,
            y=n25,
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Monthly Cash Flow Forecast",
            xaxis_title="Month",
            yaxis_title="Amount (Millions €)",
            barmode='group',
            height=500,
            showlegend=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Bank Distribution
        st.markdown("### 🏛️ Cash Distribution by Bank")
        
        fig_bank = px.bar(
            net_cash_df,
            x='Bank',
            y='Value_EUR',
            title="Net Cash per Bank",
            color='Value_EUR',
            color_continuous_scale='viridis'
        )
        
        fig_bank.update_layout(
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_bank, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        st.info("Please ensure the Excel file structure matches the expected format.")

# Investment Tracking Page (Placeholder)
def show_investment_tracking():
    if st.button("🏠 Back to Home", key="back_home_investment"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📈 INVESTMENT TRACKING</h1>
        <p>Portfolio Performance & Asset Allocation</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 Investment Tracking module coming soon! This will include portfolio analysis, performance metrics, and asset allocation tracking.")

# Payment Calendar Page (Placeholder)
def show_payment_calendar():
    if st.button("🏠 Back to Home", key="back_home_calendar"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.markdown("""
    <div class="main-header">
        <h1>📅 PAYMENT CALENDAR</h1>
        <p>Scheduled Payments & Cash Flow Timeline</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 Payment Calendar module coming soon! This will include payment scheduling, approval workflows, and cash flow timing.")

# Main App Logic
def main():
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

if __name__ == "__main__":
    main()
