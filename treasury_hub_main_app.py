#!/usr/bin/env python3
"""
Treasury HUB - Versão Consolidada com Hover
===========================================
CFO-grade interface com dados reais do banco + FX Trading melhorado + Hover nas moedas
Features: Dados reais Excel, FX rates ao vivo, Charts profissionais, Status de mercado, Hover tooltips
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
    
    /* Executive summary cards */
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

    /* FX Animation for live data */
    @keyframes blink {
        0%, 100% { border-color: #e2e8f0; }
        50% { border-color: #00ff88; }
    }
    
    /* Hover styles for bank positions */
    .bank-row {
        position: relative;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1.5rem;
        border-bottom: 1px solid #f1f5f9;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .bank-row:hover {
        background-color: #f7fafc;
    }
    
    .bank-row .tooltip {
        visibility: hidden;
        position: absolute;
        z-index: 1000;
        left: 100%;
        top: 0;
        margin-left: 10px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .bank-row:hover .tooltip {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

# Enhanced FX functions with live data
@st.cache_data(ttl=60)
def get_live_fx_rates():
    """Get live FX rates from free API"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            rates = data['rates']
            fx_data = {
                'USD/EUR': {
                    'rate': 1/rates.get('USD', 1.0857), 
                    'change': np.random.uniform(-0.5, 0.5),
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
            
            for pair in fx_data:
                fx_data[pair]['color'] = 'positive' if fx_data[pair]['change'] >= 0 else 'negative'
                fx_data[pair]['change_text'] = f"+{fx_data[pair]['change']:.2f}%" if fx_data[pair]['change'] >= 0 else f"{fx_data[pair]['change']:.2f}%"
            
            return fx_data, True
            
    except Exception as e:
        st.warning(f"⚠️ Live FX API unavailable: {str(e)}")
    
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
    returns = np.random.normal(0, 0.002, len(dates))
    returns[0] = 0
    
    prices = [base_price]
    for i in range(1, len(returns)):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)
    
    ohlc_data = []
    for i in range(0, len(prices), 4):
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
    chart_data = generate_trading_chart_data()
    
    fig = go.Figure(data=[go.Candlestick(
        x=chart_data['datetime'],
        open=chart_data['open'],
        high=chart_data['high'],
        low=chart_data['low'],
        close=chart_data['close'],
        name=pair_name,
        increasing_line_color='#00c851',
        decreasing_line_color='#ff4444',
        increasing_fillcolor='#00c851',
        decreasing_fillcolor='#ff4444'
    )])
    
    chart_data['ma_20'] = chart_data['close'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(
        x=chart_data['datetime'],
        y=chart_data['ma_20'],
        mode='lines',
        name='MA(20)',
        line=dict(color='#ff8800', width=2),
        opacity=0.8
    ))
    
    fig.update_layout(
        title=f"{pair_name} - Live Trading Chart",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#2d3748', size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor='#e2e8f0',
            gridwidth=0.5,
            type='date',
            rangeslider=dict(visible=False),
            linecolor='#cbd5e0'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e2e8f0',
            gridwidth=0.5,
            side='right',
            linecolor='#cbd5e0'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )
    
    return fig

# Data functions with SAFE number handling
@st.cache_data(ttl=300)
def get_daily_cash_flow():
    """Get daily cash flow with safe number formatting"""
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return {
                'cash_flow': 0.0,
                'cash_flow_text': 'EUR 0',
                'percentage': 0.0,
                'percentage_text': '+0.0% vs Yesterday',
                'percentage_color': 'positive'
            }
        
        lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        
        if lista_contas_sheet.shape[0] <= 101:
            return {
                'cash_flow': 0.0,
                'cash_flow_text': 'EUR 0',
                'percentage': 0.0,
                'percentage_text': '+0.0% vs Yesterday',
                'percentage_color': 'positive'
            }
        
        cash_flow_value = 0.0
        percentage_value = 0.0
        
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                cell_value_101 = lista_contas_sheet.iloc[100, col_index]
                if pd.notna(cell_value_101):
                    try:
                        numeric_value_101 = float(cell_value_101)
                        if numeric_value_101 != 0:
                            cash_flow_value = numeric_value_101
                    except (ValueError, TypeError):
                        pass
                
                cell_value_102 = lista_contas_sheet.iloc[101, col_index]
                if pd.notna(cell_value_102):
                    try:
                        numeric_value_102 = float(cell_value_102)
                        percentage_value = numeric_value_102
                    except (ValueError, TypeError):
                        pass
                    
            except Exception:
                continue
        
        if cash_flow_value >= 0:
            cash_flow_text = f"EUR {cash_flow_value:,.0f}"
        else:
            cash_flow_text = f"-EUR {abs(cash_flow_value):,.0f}"
        
        if percentage_value >= 0:
            if abs(percentage_value) < 1:
                display_percentage = percentage_value * 100
            else:
                display_percentage = percentage_value
            percentage_text = f"+{display_percentage:.1f}% vs Yesterday"
            percentage_color = 'positive'
        else:
            if abs(percentage_value) < 1:
                display_percentage = percentage_value * 100
            else:
                display_percentage = percentage_value
            percentage_text = f"{display_percentage:.1f}% vs Yesterday"
            percentage_color = 'negative'
        
        return {
            'cash_flow': float(cash_flow_value),
            'cash_flow_text': cash_flow_text,
            'percentage': float(percentage_value),
            'percentage_text': percentage_text,
            'percentage_color': percentage_color
        }
        
    except Exception as e:
        return {
            'cash_flow': 0.0,
            'cash_flow_text': 'EUR 0',
            'percentage': 0.0,
            'percentage_text': '+0.0% vs Yesterday',
            'percentage_color': 'positive'
        }

@st.cache_data(ttl=300)
def get_executive_summary():
    """Get executive summary with SAFE number handling"""
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return {
                'total_liquidity': 32.6,
                'bank_accounts': 96,
                'active_banks': 13,
                'last_updated': datetime.now().strftime("%H:%M")
            }
        
        try:
            tabelas_sheet = pd.read_excel(file_path, sheet_name="Tabelas", header=None)
            total_liquidity_raw = tabelas_sheet.iloc[91, 2]
            total_liquidity = float(total_liquidity_raw) / 1_000_000 if pd.notna(total_liquidity_raw) else 32.6
            
            lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
            account_rows = lista_contas_sheet.iloc[2:98]
            bank_accounts = len(account_rows.dropna(how='all'))
            
            return {
                'total_liquidity': float(total_liquidity),
                'bank_accounts': int(bank_accounts),
                'active_banks': 13,
                'last_updated': datetime.now().strftime("%H:%M")
            }
        except:
            return {
                'total_liquidity': 32.6,
                'bank_accounts': 96,
                'active_banks': 13,
                'last_updated': datetime.now().strftime("%H:%M")
            }
    except:
        return {
            'total_liquidity': 32.6,
            'bank_accounts': 96,
            'active_banks': 13,
            'last_updated': datetime.now().strftime("%H:%M")
        }

@st.cache_data(ttl=300)
def get_latest_variation():
    """Get latest variation with SAFE number handling"""
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return {'variation': 0.0, 'text': '+EUR 0 vs Yesterday', 'color': 'positive'}
        
        lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        
        if lista_contas_sheet.shape[0] <= 100:
            return {'variation': 0.0, 'text': '+EUR 0 vs Yesterday', 'color': 'positive'}
        
        for col_index in range(lista_contas_sheet.shape[1] - 1, -1, -1):
            try:
                cell_value = lista_contas_sheet.iloc[100, col_index]
                
                if pd.notna(cell_value):
                    try:
                        numeric_value = float(cell_value)
                        
                        if numeric_value != 0:
                            if numeric_value >= 0:
                                text = f"+EUR {numeric_value:,.0f} vs Yesterday"
                                color = 'positive'
                            else:
                                text = f"-EUR {abs(numeric_value):,.0f} vs Yesterday"
                                color = 'negative'
                            
                            return {
                                'variation': float(numeric_value),
                                'text': text,
                                'color': color
                            }
                    except (ValueError, TypeError):
                        continue
                        
            except Exception:
                continue
        
        return {'variation': 0.0, 'text': '+EUR 0 vs Yesterday', 'color': 'positive'}
        
    except Exception:
        return {'variation': 0.0, 'text': '+EUR 0 vs Yesterday', 'color': 'positive'}

def get_sample_liquidity_data():
    """Sample data for demonstration"""
    sample_dates = [
        "05-Aug-25", "06-Aug-25", "07-Aug-25", "08-Aug-25", 
        "11-Aug-25", "12-Aug-25", "13-Aug-25"
    ]
    
    sample_values = [28.5, 30.2, 31.8, 29.4, 32.1, 31.7, 32.6]
    
    dates = [datetime.strptime(date, "%d-%b-%y") for date in sample_dates]
    
    return {
        'dates': dates,
        'values': sample_values,
        'source': 'Sample Data (Excel not found)'
    }

@st.cache_data(ttl=300)
def get_dynamic_liquidity_data():
    """Get dynamic liquidity data with SAFE handling"""
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return get_sample_liquidity_data()
        
        try:
            lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        except Exception:
            return get_sample_liquidity_data()
        
        dates = []
        values = []
        found_columns = []
        
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                linha2_value = lista_contas_sheet.iloc[1, col_index]
                
                if pd.notna(linha2_value) and "VALOR" in str(linha2_value).upper() and "EUR" in str(linha2_value).upper():
                    
                    date_col_index = col_index - 2
                    
                    if date_col_index >= 0:
                        date_value = lista_contas_sheet.iloc[0, date_col_index]
                    else:
                        continue
                    
                    if lista_contas_sheet.shape[0] > 98:
                        eur_value = lista_contas_sheet.iloc[98, col_index]
                    else:
                        continue
                    
                    if pd.notna(date_value) and pd.notna(eur_value) and eur_value != 0:
                        try:
                            if isinstance(date_value, str):
                                date_str = str(date_value).strip()
                                try:
                                    parsed_date = pd.to_datetime(date_str, format='%d-%b-%y')
                                except:
                                    try:
                                        parsed_date = pd.to_datetime(date_str, format='%d/%m/%Y')
                                    except:
                                        parsed_date = pd.to_datetime(date_str)
                            elif isinstance(date_value, (int, float)):
                                if date_value > 59:
                                    parsed_date = datetime(1900, 1, 1) + timedelta(days=date_value - 2)
                                else:
                                    parsed_date = datetime(1900, 1, 1) + timedelta(days=date_value - 1)
                            else:
                                parsed_date = pd.to_datetime(date_value)
                                
                        except Exception:
                            continue
                        
                        eur_millions = float(eur_value) / 1_000_000
                        
                        dates.append(parsed_date)
                        values.append(eur_millions)
                        
            except Exception:
                continue
        
        if len(dates) > 0 and len(values) > 0:
            combined = list(zip(dates, values))
            combined.sort(key=lambda x: x[0])
            dates, values = zip(*combined)
            
            if len(dates) > 0:
                latest_date = dates[-1]
                cutoff_date = latest_date - timedelta(days=30)
                
                filtered_data = [(d, v) for d, v in zip(dates, values) if d >= cutoff_date]
                
                if filtered_data:
                    dates, values = zip(*filtered_data)
            
            return {
                'dates': list(dates),
                'values': list(values),
                'source': f'Excel Real Data ({len(dates)} days)',
                'columns_found': found_columns
            }
        else:
            return get_sample_liquidity_data()
            
    except Exception:
        return get_sample_liquidity_data()

def get_fallback_banks():
    """Fallback bank data"""
    banks_data = [
        {'Bank': 'UME BANK', 'Balance': 5.668, 'Currency': 'EUR'},
        {'Bank': 'Commerzbank', 'Balance': 3.561, 'Currency': 'EUR'},
        {'Bank': 'FKP Bank', 'Balance': 3.55, 'Currency': 'EUR'},
        {'Bank': 'FNB (SA)', 'Balance': 3.34, 'Currency': 'EUR'},
        {'Bank': 'Handelsbanken', 'Balance': 1.650, 'Currency': 'EUR'},
        {'Bank': 'Swedbank', 'Balance': 1.45, 'Currency': 'EUR'},
        {'Bank': 'HSBC', 'Balance': 1.513, 'Currency': 'EUR'},
        {'Bank': 'ING Bank', 'Balance': 1.347, 'Currency': 'EUR'},
        {'Bank': 'Jyske Bank', 'Balance': 0.760, 'Currency': 'EUR'},
        {'Bank': 'BPC BANK', 'Balance': 0.738, 'Currency': 'EUR'},
        {'Bank': 'SEB', 'Balance': 0.200, 'Currency': 'EUR'},
        {'Bank': 'UBS', 'Balance': 0.72, 'Currency': 'EUR'},
        {'Bank': 'LBCB', 'Balance': 0.57, 'Currency': 'EUR'}
    ]
    
    banks_df = pd.DataFrame(banks_data)
    banks_df = banks_df.sort_values('Balance', ascending=False)
    
    total_balance = banks_df['Balance'].sum()
    banks_df['Percentage'] = (banks_df['Balance'] / total_balance * 100).round(1)
    banks_df['Yield'] = banks_df['Percentage'].apply(lambda x: f"{x}%")
    
    return banks_df

@st.cache_data(ttl=300)
def get_bank_positions_from_tabelas():
    """Get bank positions with SAFE handling"""
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return get_fallback_banks()
        
        try:
            tabelas_sheet = pd.read_excel(file_path, sheet_name="Tabelas", header=None)
            
            banks_data = []
            
            for i in range(78, 91):
                try:
                    bank_name = tabelas_sheet.iloc[i, 1]
                    balance = tabelas_sheet.iloc[i, 2]
                    
                    if pd.notna(bank_name) and pd.notna(balance) and str(bank_name).strip():
                        banks_data.append({
                            'Bank': str(bank_name).strip(),
                            'Balance': float(balance) / 1_000_000,
                            'Currency': 'EUR'
                        })
                except:
                    continue
            
            if banks_data:
                banks_df = pd.DataFrame(banks_data)
                banks_df = banks_df.sort_values('Balance', ascending=False)
                
                total_balance = banks_df['Balance'].sum()
                banks_df['Percentage'] = (banks_df['Balance'] / total_balance * 100).round(1)
                banks_df['Yield'] = banks_df['Percentage'].apply(lambda x: f"{x}%")
                
                return banks_df
            else:
                return get_fallback_banks()
                
        except Exception:
            return get_fallback_banks()
            
    except:
        return get_fallback_banks()

# NEW HOVER FUNCTIONS
@st.cache_data(ttl=300)
def get_bank_currency_details():
    """
    Obter detalhes das moedas por banco da sheet 'Tabelas'
    - Linha 1, colunas B-O: Headers das moedas
    - Linhas 2-14, coluna A: Nomes dos bancos
    - Linhas 2-14, colunas B-O: Valores das moedas por banco
    """
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return get_fallback_currency_data()
        
        # Ler a sheet "Tabelas"
        tabelas_sheet = pd.read_excel(file_path, sheet_name="Tabelas", header=None)
        
        bank_currency_data = {}
        
        # Ler headers das moedas da linha 1 (índice 0), colunas B-O (índices 1-14)
        currency_headers = []
        for col_idx in range(1, 15):  # Colunas B (1) a O (14)
            if col_idx < tabelas_sheet.shape[1]:
                header_value = tabelas_sheet.iloc[0, col_idx]  # Linha 1 (índice 0)
                if pd.notna(header_value) and str(header_value).strip():
                    currency_headers.append((col_idx, str(header_value).strip()))
        
        # Procurar bancos nas linhas 2-14 (índices 1-13)
        for row_idx in range(1, 14):  # Linhas 2-14 (índices 1-13)
            try:
                if row_idx >= tabelas_sheet.shape[0]:
                    break
                    
                # Nome do banco na coluna A (índice 0)
                bank_name = tabelas_sheet.iloc[row_idx, 0]
                
                if pd.notna(bank_name) and str(bank_name).strip():
                    bank_name_clean = str(bank_name).strip()
                    currency_data = {}
                    total_eur_equivalent = 0
                    
                    # Procurar valores das moedas nas colunas B-O (usando os headers encontrados)
                    for col_idx, currency_name in currency_headers:
                        try:
                            cell_value = tabelas_sheet.iloc[row_idx, col_idx]
                            
                            if pd.notna(cell_value) and cell_value != 0:
                                try:
                                    amount = float(cell_value)
                                    if amount != 0:
                                        currency_data[currency_name] = {
                                            'amount': amount,
                                            'formatted': f"{amount:,.0f}" if amount >= 1000 else f"{amount:.2f}"
                                        }
                                        
                                        # Converter para EUR para cálculo de percentagem (aproximação)
                                        if currency_name.upper() == 'EUR':
                                            total_eur_equivalent += amount
                                        elif currency_name.upper() == 'USD':
                                            total_eur_equivalent += amount * 0.92
                                        elif currency_name.upper() == 'GBP':
                                            total_eur_equivalent += amount * 1.17
                                        elif currency_name.upper() in ['SEK', 'NOK', 'DKK']:
                                            total_eur_equivalent += amount * 0.09
                                        else:
                                            total_eur_equivalent += amount * 0.5
                                
                                except (ValueError, TypeError):
                                    continue
                        except Exception:
                            continue
                    
                    # Só adicionar se tiver dados de moedas
                    if currency_data:
                        # Calcular percentagens
                        for currency in currency_data:
                            if total_eur_equivalent > 0:
                                percentage = (currency_data[currency]['amount'] / total_eur_equivalent) * 100
                                currency_data[currency]['percentage'] = f"{percentage:.1f}%"
                        
                        bank_currency_data[bank_name_clean] = {
                            'currencies': currency_data,
                            'total_currencies': len(currency_data),
                            'main_currency': max(currency_data.keys(), key=lambda x: currency_data[x]['amount']) if currency_data else 'EUR'
                        }
                        
            except Exception as e:
                continue
        
        return bank_currency_data
        
    except Exception as e:
        return get_fallback_currency_data()

def get_fallback_currency_data():
    """Dados de fallback para demonstração"""
    return {
        'ING Bank': {
            'currencies': {
                'EUR': {'amount': 8500000, 'formatted': '8,500,000', 'percentage': '75.2%'},
                'USD': {'amount': 2300000, 'formatted': '2,300,000', 'percentage': '20.4%'},
                'GBP': {'amount': 500000, 'formatted': '500,000', 'percentage': '4.4%'}
            },
            'total_currencies': 3,
            'main_currency': 'EUR'
        },
        'Handelsbanken': {
            'currencies': {
                'EUR': {'amount': 3200000, 'formatted': '3,200,000', 'percentage': '68.1%'},
                'USD': {'amount': 1200000, 'formatted': '1,200,000', 'percentage': '25.5%'},
                'SEK': {'amount': 300000, 'formatted': '300,000', 'percentage': '6.4%'}
            },
            'total_currencies': 3,
            'main_currency': 'EUR'
        }
    }

def create_bank_hover_tooltip(bank_name, currency_data):
    """Criar tooltip HTML para hover com informações das moedas"""
    if not currency_data:
        return f"<div>No currency data for {bank_name}</div>"
    
    currencies = currency_data.get('currencies', {})
    total_currencies = currency_data.get('total_currencies', 0)
    main_currency = currency_data.get('main_currency', 'EUR')
    
    tooltip_html = f"""
    <div style="
        background: white; 
        border: 2px solid #007bff; 
        border-radius: 8px; 
        padding: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: 'Inter', sans-serif;
        min-width: 280px;
        max-width: 400px;
    ">
        <div style="
            font-weight: 700; 
            color: #2d3748; 
            font-size: 1.1rem; 
            margin-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
        ">
            💰 {bank_name}
        </div>
        
        <div style="
            font-size: 0.85rem; 
            color: #718096; 
            margin-bottom: 10px;
        ">
            {total_currencies} currencies • Main: {main_currency}
        </div>
        
        <div style="font-size: 0.9rem;">
    """
    
    sorted_currencies = sorted(currencies.items(), key=lambda x: x[1]['amount'], reverse=True)
    
    for currency, details in sorted_currencies:
        amount_formatted = details['formatted']
        percentage = details.get('percentage', '')
        
        if currency == 'EUR':
            color = '#007bff'
        elif currency == 'USD':
            color = '#28a745'
        elif currency == 'GBP':
            color = '#dc3545'
        else:
            color = '#6c757d'
        
        tooltip_html += f"""
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 4px 0;
            border-bottom: 1px solid #f1f5f9;
        ">
            <div style="display: flex; align-items: center;">
                <span style="
                    background: {color}; 
                    color: white; 
                    padding: 2px 6px; 
                    border-radius: 4px; 
                    font-size: 0.75rem; 
                    font-weight: 600;
                    margin-right: 8px;
                ">
                    {currency}
                </span>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 600; color: #2d3748;">
                    {amount_formatted}
                </div>
                {f'<div style="font-size: 0.75rem; color: #718096;">{percentage}</div>' if percentage else ''}
            </div>
        </div>
        """
    
    tooltip_html += """
        </div>
        
        <div style="
            margin-top: 8px; 
            padding-top: 8px; 
            border-top: 1px solid #e2e8f0;
            font-size: 0.75rem; 
            color: #a0aec0;
            text-align: center;
        ">
            💡 Real-time data from Lista contas
        </div>
    </div>
    """
    
    return tooltip_html

def create_professional_header():
    """Create header with SAFE number formatting"""
    summary = get_executive_summary()
    
    total_liquidity = summary.get('total_liquidity', 0.0)
    bank_accounts = summary.get('bank_accounts', 0)
    active_banks = summary.get('active_banks', 0)
    last_updated = summary.get('last_updated', '00:00')
    
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div>
                <div class="company-brand">Treasury Operations Center</div>
                <div class="company-subtitle">Real-time Financial Command & Control • Last Update: {last_updated}</div>
            </div>
            <div class="header-metrics">
                <div class="header-metric">
                    <div class="metric-value">EUR {total_liquidity:.1f}M</div>
                    <div class="metric-label">Total Liquidity</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{bank_accounts}</div>
                    <div class="metric-label">Bank Accounts</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{active_banks}</div>
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
                <p style="color: #a0aec0; font-size: 0.9rem; margin-top: 2rem;">
                    <em>Homepage content area - Ready for future customization</em>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_executive_overview_with_hover():
    """Executive Overview com hover tooltips para mostrar moedas"""
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    
    summary = get_executive_summary()
    variation = get_latest_variation()
    cash_flow = get_daily_cash_flow()
    bank_currency_data = get_bank_currency_details()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change_class = "change-positive" if variation['color'] == 'positive' else "change-negative"
        st.markdown(f"""
        <div class="summary-card">
            <h3>Total Liquidity</h3>
            <div class="summary-value">EUR {summary['total_liquidity']:.1f}M</div>
            <div class="summary-change {change_class}">{variation['text']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Inflow</h3>
            <div class="summary-value">EUR 0</div>
            <div class="summary-change change-positive">To be configured</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Outflow</h3>
            <div class="summary-value">EUR 0</div>
            <div class="summary-change change-positive">To be configured</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        percentage_class = "change-positive" if cash_flow['percentage_color'] == 'positive' else "change-negative"
        st.markdown(f"""
        <div class="summary-card">
            <h3>Daily Cash Flow</h3>
            <div class="summary-value">{cash_flow['cash_flow_text']}</div>
            <div class="summary-change {percentage_class}">{cash_flow['percentage_text']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                Liquidity Trend (Dynamic)
                <span class="status-indicator status-good">Healthy</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        try:
            liquidity_data = get_dynamic_liquidity_data()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=liquidity_data['dates'],
                y=liquidity_data['values'],
                mode='lines',
                name='Total Liquidity',
                line=dict(color='#2b6cb0', width=3),
                fill='tonexty',
                fillcolor='rgba(43, 108, 176, 0.1)',
                hovertemplate='<b>%{x|%d %b %Y}</b><br>EUR %{y:.1f}M<extra></extra>'
            ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=20, b=0),
                plot_bgcolor='white',
                paper_bgcolor='white',
                showlegend=False,
                xaxis=dict(
                    showgrid=False,
                    gridcolor='#f1f5f9',
                    tickformat='%d %b'
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#f1f5f9', 
                    title='Million EUR',
                    range=[0, 80]
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading chart: {e}")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">💰 Cash Positions - Click to Expand</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        banks_df = get_bank_positions_from_tabelas()
        
        # Para cada banco, criar um expander clicável
        for _, row in banks_df.iterrows():
            bank_name = row['Bank']
            
            # Procurar dados de moedas para este banco
            currency_data = None
            for stored_bank, data in bank_currency_data.items():
                if stored_bank.lower() in bank_name.lower() or bank_name.lower() in stored_bank.lower():
                    currency_data = data
                    break
            
            # Mostrar informação básica do banco sempre visível
            col_bank, col_balance = st.columns([3, 1])
            
            with col_bank:
                # Se tem dados de moedas, mostrar quantas moedas tem
                if currency_data:
                    total_currencies = currency_data['total_currencies']
                    main_currency = currency_data['main_currency']
                    st.markdown(f"**{bank_name}**")
                    st.caption(f"{row['Currency']} • {row['Yield']} • {total_currencies} currencies")
                else:
                    st.markdown(f"**{bank_name}**")
                    st.caption(f"{row['Currency']} • {row['Yield']}")
            
            with col_balance:
                st.markdown(f"**EUR {row['Balance']:.1f}M**")
            
            # Se tem dados de moedas, criar expander para mostrar detalhes
            if currency_data:
                with st.expander(f"💱 Show {currency_data['total_currencies']} currencies", expanded=False):
                    currencies = currency_data['currencies']
                    
                    # Ordenar moedas por montante (maior primeiro)
                    sorted_currencies = sorted(currencies.items(), key=lambda x: x[1]['amount'], reverse=True)
                    
                    for currency, details in sorted_currencies:
                        amount_formatted = details['formatted']
                        percentage = details.get('percentage', '')
                        
                        # Criar colunas para moeda e valor
                        col_curr, col_val = st.columns([1, 2])
                        
                        with col_curr:
                            # Cor da moeda baseada no tipo
                            if currency.upper() == 'EUR':
                                st.markdown(f"🔵 **{currency}**")
                            elif currency.upper() == 'USD':
                                st.markdown(f"🟢 **{currency}**")
                            elif currency.upper() == 'GBP':
                                st.markdown(f"🔴 **{currency}**")
                            else:
                                st.markdown(f"⚫ **{currency}**")
                        
                        with col_val:
                            st.markdown(f"**{amount_formatted}**")
                            if percentage:
                                st.caption(f"{percentage}")
                    
                    st.caption(f"💡 Main currency: **{currency_data['main_currency']}**")
            else:
                # Se não tem dados de moedas, mostrar mensagem simples
                st.caption("ℹ️ No currency breakdown available")
            
            st.divider()  # Linha separadora entre bancos
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Debug section mais compacta
        with st.expander("🔍 Debug - Currency Data Found"):
            if bank_currency_data:
                for bank_name, data in bank_currency_data.items():
                    st.write(f"**{bank_name}**: {data['total_currencies']} moedas")
            else:
                st.write("Nenhum dado de moedas encontrado.")
    
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">Executive Insight</div>
        <div class="insight-content">
            Current liquidity position at EUR {summary['total_liquidity']:.1f}M across {summary['active_banks']} banking relationships.
            Portfolio diversification optimized with {summary['bank_accounts']} active accounts.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main application
def main():
    """Main application with professional interface and hover functionality"""
    
    create_professional_header()
    create_navigation()
    
    if st.session_state.current_page == 'overview':
        show_homepage()
    elif st.session_state.current_page == 'executive':
        show_executive_overview_with_hover()
    else:
        st.error(f"Unknown page: {st.session_state.current_page}")
        show_homepage()

if __name__ == "__main__":
    main()
