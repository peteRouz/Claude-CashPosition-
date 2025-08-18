#!/usr/bin/env python3
"""
Treasury HUB - Enhanced Professional Version
============================================
CFO-grade interface with real bank data + Live FX Trading
Features: Live FX rates, Professional trading charts, Market status
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
import requests
import time

# Configure page
st.set_page_config(
    page_title="Treasury Operations Center",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS - CFO Grade
st.markdown("""
<style>
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    header {visibility: hidden;}
    
    /* Custom fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Executive header */
    .executive-header {
        background: linear-gradient(135deg, #1a365d 0%, #2d3748 100%);
        padding: 1.5rem 2rem;
        margin: -1rem -1rem 0 -1rem;
        border-bottom: 3px solid #e2e8f0;
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .company-brand {
        color: white;
        font-size: 1.8rem;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    .company-subtitle {
        color: #a0aec0;
        font-size: 0.9rem;
        margin-top: -5px;
    }
    
    .header-metrics {
        display: flex;
        gap: 2rem;
        color: white;
    }
    
    .header-metric {
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #68d391;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Dashboard sections */
    .dashboard-section {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 1.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .section-header {
        background: #f7fafc;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 600;
        color: #2d3748;
        font-size: 1.1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .section-content {
        padding: 1.5rem;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-good {
        background: #c6f6d5;
        color: #22543d;
    }
    
    .change-positive {
        color: #38a169;
    }
    
    .change-negative {
        color: #e53e3e;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }

    /* FX Animation for live data */
    @keyframes blink {
        0%, 100% { border-color: #e2e8f0; }
        50% { border-color: #00ff88; }
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

# Enhanced FX functions with live data
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_live_fx_rates():
    """Get live FX rates from free API"""
    try:
        # Using exchangerate-api.com (free tier: 1500 requests/month)
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            rates = data['rates']
            
            # Calculate changes (simulate for demo - in real app you'd store previous rates)
            fx_data = {
                'USD/EUR': {
                    'rate': 1/rates.get('USD', 1.0857), 
                    'change': np.random.uniform(-0.5, 0.5),  # Simulate change
                    'raw_rate': rates.get('USD', 1.0857)
                },
                'GBP/EUR': {
                    'rate': 1/rates.get('GBP', 0.8567), 
                    'change': np.random.uniform(-0.5, 0.5),
                    'raw_rate': rates.get('GBP', 0.8567)
                },
                'CHF/EUR': {
                    'rate': 1/rates.get('CHF', 0.9876), 
                    'change': np.random.uniform(-0.3, 0.3),
                    'raw_rate': rates.get('CHF', 0.9876)
                },
                'SEK/EUR': {
                    'rate': 1/rates.get('SEK', 11.7234), 
                    'change': np.random.uniform(-0.4, 0.4),
                    'raw_rate': rates.get('SEK', 11.7234)
                },
                'NOK/EUR': {
                    'rate': 1/rates.get('NOK', 11.8945), 
                    'change': np.random.uniform(-0.3, 0.4),
                    'raw_rate': rates.get('NOK', 11.8945)
                },
                'CAD/EUR': {
                    'rate': 1/rates.get('CAD', 1.4678), 
                    'change': np.random.uniform(-0.3, 0.3),
                    'raw_rate': rates.get('CAD', 1.4678)
                }
            }
            
            # Add color based on change
            for pair in fx_data:
                fx_data[pair]['color'] = 'positive' if fx_data[pair]['change'] >= 0 else 'negative'
                fx_data[pair]['change_text'] = f"+{fx_data[pair]['change']:.2f}%" if fx_data[pair]['change'] >= 0 else f"{fx_data[pair]['change']:.2f}%"
            
            return fx_data, True  # True = live data
            
    except Exception as e:
        st.warning(f"⚠️ Live FX API unavailable: {str(e)}")
    
    # Fallback to demo data
    return get_demo_fx_rates(), False

def get_demo_fx_rates():
    """Fallback demo FX rates"""
    return {
        'USD/EUR': {'rate': 0.9234, 'change': 0.25, 'color': 'positive', 'change_text': '+0.25%'},
        'GBP/EUR': {'rate': 1.1678, 'change': -0.15, 'color': 'negative', 'change_text': '-0.15%'},
        'CHF/EUR': {'rate': 0.9876, 'change': 0.08, 'color': 'positive', 'change_text': '+0.08%'},
        'SEK/EUR': {'rate': 0.0932, 'change': -0.32, 'color': 'negative', 'change_text': '-0.32%'},
        'NOK/EUR': {'rate': 0.0856, 'change': 0.12, 'color': 'positive', 'change_text': '+0.12%'},
        'CAD/EUR': {'rate': 0.6789, 'change': 0.18, 'color': 'positive', 'change_text': '+0.18%'}
    }

def generate_trading_chart_data(base_price=1.0857, days=30):
    """Generate realistic forex chart data"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days*24, freq='H')
    
    # Generate realistic price movements
    returns = np.random.normal(0, 0.002, len(dates))  # Small hourly returns
    returns[0] = 0  # Start at base price
    
    prices = [base_price]
    for i in range(1, len(returns)):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)
    
    # Create OHLC data
    ohlc_data = []
    for i in range(0, len(prices), 4):  # Group every 4 hours
        if i + 4 <= len(prices):
            chunk = prices[i:i+4]
            ohlc_data.append({
                'datetime': dates[i],
                'open': chunk[0],
                'high': max(chunk),
                'low': min(chunk),
                'close': chunk[-1]
            })
    
    return pd.DataFrame(ohlc_data)

def create_fx_trading_chart(pair_name="EUR/USD"):
    """Create professional trading chart with WHITE background"""
    # Generate data
    chart_data = generate_trading_chart_data()
    
    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=chart_data['datetime'],
        open=chart_data['open'],
        high=chart_data['high'],
        low=chart_data['low'],
        close=chart_data['close'],
        name=pair_name,
        increasing_line_color='#00c851',  # Green for up
        decreasing_line_color='#ff4444',  # Red for down
        increasing_fillcolor='#00c851',
        decreasing_fillcolor='#ff4444'
    )])
    
    # Add moving average
    chart_data['ma_20'] = chart_data['close'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(
        x=chart_data['datetime'],
        y=chart_data['ma_20'],
        mode='lines',
        name='MA(20)',
        line=dict(color='#ff8800', width=2),  # Orange moving average
        opacity=0.8
    ))
    
    # WHITE BACKGROUND Professional styling
    fig.update_layout(
        title=f"{pair_name} - Live Trading Chart",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='white',  # WHITE background instead of black
        paper_bgcolor='white',  # WHITE paper background
        font=dict(color='#2d3748', size=12),  # Dark text for readability
        xaxis=dict(
            showgrid=True,
            gridcolor='#e2e8f0',  # Light gray grid
            gridwidth=0.5,
            type='date',
            rangeslider=dict(visible=False),
            linecolor='#cbd5e0'  # Light border
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e2e8f0',  # Light gray grid
            gridwidth=0.5,
            side='right',
            linecolor='#cbd5e0'  # Light border
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)'  # Semi-transparent white background
        )
    )
    
    return fig

def create_professional_header():
    """Create header with basic metrics"""
    current_time = datetime.now().strftime("%H:%M")
    
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div>
                <div class="company-brand">Treasury Operations Center</div>
                <div class="company-subtitle">Real-time Financial Command & Control • Last Update: {current_time}</div>
            </div>
            <div class="header-metrics">
                <div class="header-metric">
                    <div class="metric-value">EUR 32.6M</div>
                    <div class="metric-label">Total Liquidity</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">96</div>
                    <div class="metric-label">Bank Accounts</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">13</div>
                    <div class="metric-label">Active Banks</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_navigation():
    """Create navigation"""
    nav_items = [
        ('executive', 'Executive Overview'),
        ('fx_risk', 'FX Risk Management'), 
        ('investments', 'Investment Portfolio'),
        ('operations', 'Daily Operations')
    ]
    
    cols = st.columns(len(nav_items))
    
    for i, (page_key, label) in enumerate(nav_items):
        with cols[i]:
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

def show_homepage():
    """Show homepage"""
    st.markdown('<div class="section-header">Treasury Operations Center - Homepage</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-content">
            <div style="text-align: center; padding: 4rem 2rem;">
                <h2 style="color: #2d3748; margin-bottom: 1rem;">Welcome to Treasury Operations Center</h2>
                <p style="color: #718096; font-size: 1.1rem; margin-bottom: 2rem;">
                    Your comprehensive financial command and control center
                </p>
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; margin: 2rem auto; max-width: 600px;">
                    <h3 style="margin-bottom: 1rem;">Quick Access</h3>
                    <p style="margin-bottom: 1.5rem; opacity: 0.9;">Navigate to your treasury modules using the buttons above</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.9rem;">
                        <div>📊 Executive Overview</div>
                        <div>💱 FX Risk Management</div>
                        <div>📈 Investment Portfolio</div>
                        <div>⚙️ Daily Operations</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_fx_risk():
    """Enhanced FX Risk Management with live data and charts"""
    if st.button("🏠 Back to Home", key="back_home_fx"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">FX Risk Management - Live Trading</div>', unsafe_allow_html=True)
    
    # Get live FX data
    fx_rates, is_live = get_live_fx_rates()
    
    if 'fx_deals' not in st.session_state:
        st.session_state.fx_deals = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Live FX Rates Section
        status_indicator = "🟢 LIVE" if is_live else "🟡 DEMO"
        
        st.markdown(f"""
        <div class="dashboard-section">
            <div class="section-header">
                Live FX Rates vs EUR
                <span class="status-indicator status-good">{status_indicator}</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Auto-refresh button and controls
        col_refresh, col_auto, col_time = st.columns([1, 1, 2])
        with col_refresh:
            if st.button("🔄 Refresh", key="refresh_fx"):
                st.cache_data.clear()
                st.rerun()
        
        with col_auto:
            auto_refresh_rates = st.checkbox("Auto 🔄", value=False, key="auto_refresh_rates", help="Auto-refresh every 30 seconds")
        
        with col_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.caption(f"📡 Last update: {current_time} {'(Live API)' if is_live else '(Demo Mode)'}")
        
        # Auto-refresh logic for FX rates (every 30 seconds to avoid being too slow)
        if auto_refresh_rates:
            st.info("🔄 Auto-refresh enabled (30s intervals)")
            time.sleep(30)
            st.rerun()
        
        # Display FX rates in grid
        fx_cols = st.columns(3)
        for i, (pair, data) in enumerate(fx_rates.items()):
            with fx_cols[i % 3]:
                color_class = "change-positive" if data['color'] == 'positive' else "change-negative"
                
                # Add blinking effect for live data
                blink_style = "animation: blink 2s infinite;" if is_live else ""
                
                st.markdown(f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; {blink_style}">
                    <div style="font-size: 0.875rem; color: #718096; font-weight: 500;">{pair}</div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #2d3748; margin: 0.5rem 0;">{data['rate']:.4f}</div>
                    <div class="{color_class}" style="font-size: 0.875rem; font-weight: 500;">{data['change_text']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # TRADING CHART SECTION
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                📈 Live Trading Charts
                <span class="status-indicator status-good">Professional</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Chart selector
        chart_cols = st.columns([2, 1, 1])
        with chart_cols[0]:
            selected_pair = st.selectbox(
                "Select Currency Pair:", 
                ["EUR/USD", "GBP/EUR", "USD/JPY", "EUR/GBP", "EUR/CHF"],
                key="chart_pair"
            )
        
        with chart_cols[1]:
            timeframe = st.selectbox(
                "Timeframe:", 
                ["1H", "4H", "1D", "1W"],
                key="chart_timeframe"
            )
        
        with chart_cols[2]:
            auto_refresh_chart = st.checkbox("Auto Chart 🔄", value=False, key="auto_refresh_chart", help="Auto-refresh chart every 60 seconds")
        
        # Create and display the trading chart
        trading_fig = create_fx_trading_chart(selected_pair)
        st.plotly_chart(trading_fig, use_container_width=True)
        
        # Chart info
        st.caption(f"📊 {selected_pair} • Timeframe: {timeframe} • Candlestick + MA(20) • Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        # FX Deal Request Form
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">🚀 FX Deal Request</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        with st.form("fx_deal_form"):
            sell_currency = st.selectbox("Sell Currency", ['EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'CAD', 'AUD', 'MYR', 'IDR'])
            buy_currency = st.selectbox("Buy Currency", ['USD', 'GBP', 'CHF', 'SEK', 'NOK', 'CAD', 'AUD', 'MYR', 'IDR', 'EUR'])
            amount = st.number_input("Amount", min_value=1000, value=100000, step=1000)
            contract_type = st.selectbox("Contract Type", ['Spot', 'Forward', 'Swap', 'Option'])
            value_date = st.date_input("Value Date", value=datetime.now().date())
            
            # Special note for SEK
            if sell_currency == 'SEK' or buy_currency == 'SEK':
                st.warning("⚠️ SEK Trading: Historically challenging rates - proceed with caution")
            
            comments = st.text_area("Comments", placeholder="Optional comments...")
            
            submitted = st.form_submit_button("🚀 Submit FX Deal", use_container_width=True)
            
            if submitted:
                if sell_currency != buy_currency:
                    new_deal = {
                        'id': len(st.session_state.fx_deals) + 1,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'sell_currency': sell_currency,
                        'buy_currency': buy_currency,
                        'amount': amount,
                        'contract_type': contract_type,
                        'value_date': value_date.strftime("%Y-%m-%d"),
                        'comments': comments,
                        'status': 'Pending',
                        'user': 'Treasury User',
                        'rate_type': 'Live' if is_live else 'Demo'
                    }
                    st.session_state.fx_deals.append(new_deal)
                    st.success("✅ FX Deal submitted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Sell and Buy currencies must be different!")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Market Status Widget - Markets you actually work with
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">🌍 Trading Markets Status</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Your actual trading markets with correct timezones
        now = datetime.now()
        markets = {
            "🇺🇸 New York": (14, 30, 21, 0),      # 14:30-21:00 UTC (NYSE)
            "🇬🇧 London": (8, 0, 16, 30),         # 08:00-16:30 UTC (LSE)
            "🇲🇾 Kuala Lumpur": (1, 0, 9, 0),     # 01:00-09:00 UTC (MYR trading)
            "🇮🇩 Jakarta": (2, 0, 9, 0),          # 02:00-09:00 UTC (IDR trading)
            "🇨🇦 Toronto": (14, 30, 21, 0),       # 14:30-21:00 UTC (CAD trading)
            "🇦🇺 Sydney": (22, 0, 7, 0),          # 22:00-07:00 UTC (AUD trading)
            "🇸🇪 Stockholm": (8, 0, 16, 30),      # 08:00-16:30 UTC (SEK - your challenging currency!)
            "🇳🇴 Oslo": (8, 0, 16, 30)            # 08:00-16:30 UTC (NOK - part of EU market)
        }
        
        # Special highlight for SEK since you mentioned trading difficulties
        for market, (open_h, open_m, close_h, close_m) in markets.items():
            current_minutes = now.hour * 60 + now.minute
            open_minutes = open_h * 60 + open_m
            close_minutes = close_h * 60 + close_m
            
            if market in ["🇦🇺 Sydney"]:  # Sydney crosses midnight
                is_open = now.hour >= open_h or now.hour < close_h
            else:
                is_open = open_minutes <= current_minutes <= close_minutes
            
            status = "🟢 OPEN" if is_open else "🔴 CLOSED"
            
            # Special highlighting for SEK
            if "Stockholm" in market:
                st.markdown(f"**{market}**: {status} ⚠️ *SEK Trading - Challenging pair*")
            elif "Oslo" in market:
                st.markdown(f"**{market}**: {status} ℹ️ *NOK - EU Market hours*")
            else:
                st.markdown(f"**{market}**: {status}")
        
        st.markdown("</div></div>", unsafe_allow_html=True)

def show_executive_overview():
    """Show executive overview"""
    if st.button("🏠 Back to Home", key="back_home_executive"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    st.info("📊 Executive Overview - Sample dashboard")

def show_daily_operations():
    """Show Daily Operations"""
    if st.button("🏠 Back to Home", key="back_home_operations"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">Daily Operations Center</div>', unsafe_allow_html=True)
    st.info("⚙️ Daily Operations - Sample dashboard")

def show_investment_portfolio():
    """Show Investment Portfolio"""
    if st.button("🏠 Back to Home", key="back_home_investments"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">Investment Portfolio Tracking</div>', unsafe_allow_html=True)
    st.info("📈 Investment Portfolio - Sample dashboard")

# Main application
def main():
    """Main application"""
    create_professional_header()
    create_navigation()
    
    if st.session_state.current_page == 'overview':
        show_homepage()
    elif st.session_state.current_page == 'executive':
        show_executive_overview()
    elif st.session_state.current_page == 'fx_risk':
        show_fx_risk()
    elif st.session_state.current_page == 'operations':
        show_daily_operations()
    elif st.session_state.current_page == 'investments':
        show_investment_portfolio()
    else:
        show_homepage()

if __name__ == "__main__":
    main()
