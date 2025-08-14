#!/usr/bin/env python3
"""
Treasury HUB - Professional CFO-Grade Interface
==============================================
Enterprise treasury management platform with executive-level design
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

# Configure page
st.set_page_config(
    page_title="Treasury Operations Center",
    page_icon="💼",
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
    
    /* Navigation bar */
    .nav-container {
        background: white;
        border-bottom: 1px solid #e2e8f0;
        padding: 0;
        margin: 0 -1rem 2rem -1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .nav-content {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        padding: 0 2rem;
    }
    
    .nav-item {
        padding: 1rem 1.5rem;
        color: #4a5568;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
        border-bottom: 3px solid transparent;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .nav-item:hover {
        color: #2d3748;
        border-bottom-color: #4299e1;
        background: #f7fafc;
    }
    
    .nav-item.active {
        color: #2b6cb0;
        border-bottom-color: #2b6cb0;
        background: #ebf8ff;
    }
    
    /* Executive summary cards */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .summary-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .summary-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 0.875rem;
        font-weight: 500;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .summary-value {
        font-size: 2rem;
        font-weight: 600;
        color: #2d3748;
        margin: 0.5rem 0;
    }
    
    .summary-change {
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .change-positive {
        color: #38a169;
    }
    
    .change-negative {
        color: #e53e3e;
    }
    
    /* Professional tables */
    .professional-table {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .table-header {
        background: #f7fafc;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 600;
        color: #2d3748;
        font-size: 1rem;
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
    
    .status-warning {
        background: #fef5e7;
        color: #744210;
    }
    
    .status-error {
        background: #fed7d7;
        color: #742a2a;
    }
    
    /* Professional buttons */
    .executive-button {
        background: #2b6cb0;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .executive-button:hover {
        background: #2c5282;
        box-shadow: 0 4px 12px rgba(43, 108, 176, 0.3);
    }
    
    .secondary-button {
        background: white;
        color: #4a5568;
        border: 1px solid #e2e8f0;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .secondary-button:hover {
        background: #f7fafc;
        border-color: #cbd5e0;
    }
    
    /* Market data feed */
    .market-feed {
        background: #1a202c;
        color: white;
        padding: 0.75rem 1.5rem;
        margin: 0 -1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        overflow: hidden;
        white-space: nowrap;
    }
    
    .ticker-item {
        display: inline-block;
        margin-right: 3rem;
    }
    
    .ticker-symbol {
        color: #68d391;
        font-weight: bold;
    }
    
    .ticker-price {
        color: white;
        margin-left: 0.5rem;
    }
    
    .ticker-change {
        margin-left: 0.5rem;
    }
    
    .ticker-up {
        color: #68d391;
    }
    
    .ticker-down {
        color: #fc8181;
    }
    
    /* Executive insights */
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .insight-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .insight-content {
        font-size: 0.9rem;
        line-height: 1.5;
        opacity: 0.95;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    
    /* Custom chart styling */
    .plotly-chart {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

# Mock data for professional display
@st.cache_data
def get_executive_summary():
    """Get executive summary data"""
    return {
        'total_liquidity': 47.2,  # Million EUR
        'fx_exposure': 12.8,      # Million EUR  
        'daily_flow': 3.4,        # Million EUR
        'yield': 2.47,            # Percentage
        'var_95': 0.8,            # Million EUR
        'counterparties': 14
    }

@st.cache_data
def get_market_data():
    """Get market data ticker"""
    return [
        {'symbol': 'EUR/USD', 'price': '1.0847', 'change': '+0.0023', 'direction': 'up'},
        {'symbol': 'GBP/EUR', 'price': '0.8634', 'change': '-0.0012', 'direction': 'down'},
        {'symbol': 'USD/JPY', 'price': '148.72', 'change': '+0.34', 'direction': 'up'},
        {'symbol': 'EUR/CHF', 'price': '0.9456', 'change': '+0.0008', 'direction': 'up'},
        {'symbol': '10Y BUND', 'price': '2.47%', 'change': '+0.03', 'direction': 'up'},
        {'symbol': 'EURIBOR 3M', 'price': '3.89%', 'change': '-0.01', 'direction': 'down'}
    ]

@st.cache_data  
def get_cash_positions():
    """Get current cash positions"""
    return pd.DataFrame([
        {'Bank': 'Deutsche Bank', 'Currency': 'EUR', 'Balance': 15.4, 'Yield': '2.1%'},
        {'Bank': 'BNP Paribas', 'Currency': 'EUR', 'Balance': 12.8, 'Yield': '2.0%'},
        {'Bank': 'Santander', 'Currency': 'EUR', 'Balance': 8.9, 'Yield': '1.9%'},
        {'Bank': 'HSBC', 'Currency': 'USD', 'Balance': 7.2, 'Yield': '4.2%'},
        {'Bank': 'UBS', 'Currency': 'CHF', 'Balance': 2.9, 'Yield': '0.8%'}
    ])

def create_professional_header():
    """Create executive header with real-time metrics"""
    summary = get_executive_summary()
    
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div>
                <div class="company-brand">Treasury Operations Center</div>
                <div class="company-subtitle">Real-time Financial Command & Control</div>
            </div>
            <div class="header-metrics">
                <div class="header-metric">
                    <div class="metric-value">€{summary['total_liquidity']:.1f}M</div>
                    <div class="metric-label">Total Liquidity</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{summary['yield']:.2f}%</div>
                    <div class="metric-label">Portfolio Yield</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{summary['counterparties']}</div>
                    <div class="metric-label">Active Banks</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_market_ticker():
    """Create professional market data ticker"""
    market_data = get_market_data()
    
    ticker_html = '<div class="market-feed">'
    for item in market_data:
        direction_class = 'ticker-up' if item['direction'] == 'up' else 'ticker-down'
        ticker_html += f'''
        <span class="ticker-item">
            <span class="ticker-symbol">{item['symbol']}</span>
            <span class="ticker-price">{item['price']}</span>
            <span class="ticker-change {direction_class}">{item['change']}</span>
        </span>
        '''
    ticker_html += '</div>'
    
    st.markdown(ticker_html, unsafe_allow_html=True)

def create_navigation():
    """Create professional navigation"""
    nav_items = [
        ('overview', 'Executive Overview'),
        ('liquidity', 'Liquidity Management'),
        ('fx_risk', 'FX Risk Management'), 
        ('investments', 'Investment Portfolio'),
        ('operations', 'Daily Operations'),
        ('analytics', 'Advanced Analytics')
    ]
    
    cols = st.columns(len(nav_items))
    
    for i, (page_key, label) in enumerate(nav_items):
        with cols[i]:
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

def show_executive_overview():
    """Show executive overview dashboard"""
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    
    # Key metrics cards
    summary = get_executive_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Total Liquidity</h3>
            <div class="summary-value">€{summary['total_liquidity']:.1f}M</div>
            <div class="summary-change change-positive">+€2.1M vs Yesterday</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <h3>FX Exposure</h3>
            <div class="summary-value">€{summary['fx_exposure']:.1f}M</div>
            <div class="summary-change change-negative">-€0.4M vs Yesterday</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Daily Cash Flow</h3>
            <div class="summary-value">€{summary['daily_flow']:.1f}M</div>
            <div class="summary-change change-positive">+€1.2M Inflow Today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Portfolio Yield</h3>
            <div class="summary-value">{summary['yield']:.2f}%</div>
            <div class="summary-change change-positive">+0.03% vs Last Week</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                Liquidity Trend (30 Days)
                <span class="status-indicator status-good">Healthy</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Professional liquidity chart
        dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
        liquidity = 45 + np.cumsum(np.random.normal(0.1, 0.8, 30))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=liquidity,
            mode='lines',
            name='Total Liquidity',
            line=dict(color='#2b6cb0', width=3),
            fill='tonexty',
            fillcolor='rgba(43, 108, 176, 0.1)'
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title='Million EUR')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">Cash Positions</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        cash_df = get_cash_positions()
        
        # Professional bank breakdown
        for _, row in cash_df.iterrows():
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">
                <div>
                    <div style="font-weight: 600; color: #2d3748;">{row['Bank']}</div>
                    <div style="font-size: 0.8rem; color: #718096;">{row['Currency']} • {row['Yield']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600; color: #2d3748;">€{row['Balance']:.1f}M</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Executive insights
    st.markdown("""
    <div class="insight-box">
        <div class="insight-title">Executive Insight</div>
        <div class="insight-content">
            Current liquidity position is optimal at €47.2M, representing 94% of target range. 
            FX exposure within risk parameters. Recommend maintaining current positioning ahead of ECB meeting.
            Portfolio yield outperforming benchmark by 47 basis points.
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_fx_risk_management():
    """Show FX risk management page"""
    st.markdown('<div class="section-header">FX Risk Management</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                Currency Exposure Analysis
                <span class="status-indicator status-good">Within Limits</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Professional FX exposure chart
        currencies = ['EUR', 'USD', 'GBP', 'CHF', 'JPY']
        exposures = [28.4, 12.8, 4.2, 2.9, -1.1]
        colors = ['#2b6cb0' if x >= 0 else '#e53e3e' for x in exposures]
        
        fig = go.Figure(data=[
            go.Bar(x=currencies, y=exposures, marker_color=colors)
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(title='Currency'),
            yaxis=dict(title='Exposure (Million EUR)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">Risk Metrics</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        metrics = [
            ('Value at Risk (95%)', '€0.8M', 'good'),
            ('Expected Shortfall', '€1.2M', 'good'),
            ('Max Exposure Limit', '€15M', 'warning'),
            ('Hedge Ratio', '76%', 'good')
        ]
        
        for label, value, status in metrics:
            status_class = f"status-{status}"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9;">
                <div style="color: #4a5568; font-weight: 500;">{label}</div>
                <div>
                    <span class="status-indicator {status_class}">{value}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

def show_daily_operations():
    """Show daily operations page"""
    st.markdown('<div class="section-header">Daily Operations Center</div>', unsafe_allow_html=True)
    
    # Quick actions bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Execute FX Trade", use_container_width=True):
            st.session_state.show_fx_form = True
    
    with col2:
        if st.button("Transfer Funds", use_container_width=True):
            st.info("Transfer module activated")
    
    with col3:
        if st.button("Generate Report", use_container_width=True):
            st.info("Report generation started")
    
    with col4:
        if st.button("Risk Assessment", use_container_width=True):
            st.info("Risk analysis initiated")
    
    # FX Trading form (professional)
    if st.session_state.get('show_fx_form', False):
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">Execute FX Transaction</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_type = st.selectbox("Transaction Type", ["SPOT", "FORWARD", "SWAP"])
            base_currency = st.selectbox("Base Currency", ["EUR", "USD", "GBP", "CHF"])
            quote_currency = st.selectbox("Quote Currency", ["USD", "EUR", "GBP", "JPY"])
            
        with col2:
            amount = st.number_input("Amount (Millions)", min_value=0.1, max_value=50.0, value=1.0)
            rate = st.number_input("Rate", min_value=0.0001, value=1.0847, format="%.4f")
            counterparty = st.selectbox("Counterparty", ["Deutsche Bank", "BNP Paribas", "HSBC"])
        
        value_date = st.date_input("Value Date")
        
        if st.button("Execute Transaction", type="primary"):
            st.success(f"✅ {transaction_type} transaction executed: {amount:.1f}M {base_currency}/{quote_currency} @ {rate:.4f}")
            st.session_state.show_fx_form = False
            st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Recent transactions
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">Recent Transactions</div>
        <div class="section-content">
    """, unsafe_allow_html=True)
    
    # Professional transaction table
    transactions = pd.DataFrame([
        {'Time': '14:32', 'Type': 'SPOT', 'Currency': 'EUR/USD', 'Amount': '€2.5M', 'Rate': '1.0847', 'Counterparty': 'Deutsche Bank', 'Status': 'Settled'},
        {'Time': '13:15', 'Type': 'FORWARD', 'Currency': 'GBP/EUR', 'Amount': '£1.8M', 'Rate': '0.8634', 'Counterparty': 'BNP Paribas', 'Status': 'Pending'},
        {'Time': '11:42', 'Type': 'SPOT', 'Currency': 'USD/JPY', 'Amount': '$3.2M', 'Rate': '148.72', 'Counterparty': 'HSBC', 'Status': 'Settled'},
    ])
    
    st.dataframe(transactions, use_container_width=True, hide_index=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# Main application
def main():
    """Main application with professional interface"""
    
    # Create professional header
    create_professional_header()
    
    # Market data ticker
    create_market_ticker()
    
    # Navigation
    create_navigation()
    
    # Route to pages
    if st.session_state.current_page == 'overview':
        show_executive_overview()
    elif st.session_state.current_page == 'fx_risk':
        show_fx_risk_management()
    elif st.session_state.current_page == 'operations':
        show_daily_operations()
    elif st.session_state.current_page == 'liquidity':
        st.markdown("### 🏗️ Liquidity Management")
        st.info("Advanced liquidity optimization module - Available in next update")
    elif st.session_state.current_page == 'investments':
        st.markdown("### 🏗️ Investment Portfolio")
        st.info("Portfolio management module - Available in next update")
    elif st.session_state.current_page == 'analytics':
        st.markdown("### 🏗️ Advanced Analytics")
        st.info("Predictive analytics and AI insights - Available in next update")

if __name__ == "__main__":
    main()
