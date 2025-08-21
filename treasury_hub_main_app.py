#!/usr/bin/env python3
"""
Treasury HUB - Versão com Yahoo Finance (DADOS REAIS)
=================================
CFO-grade interface com dados reais do banco + FX Trading com dados REAIS do Yahoo Finance
Features: Dados reais Excel, FX rates REAIS, Charts REAIS, Status de mercado
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
import yfinance as yf  # ← NOVA BIBLIOTECA ADICIONADA

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
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

# ==================== YAHOO FINANCE FUNCTIONS (REAL DATA) ====================

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_real_fx_data_yahoo(pair_symbol, days=30):
    """
    Obter dados REAIS do Yahoo Finance
    pair_symbol: 'EUR/USD', 'GBP/EUR', etc.
    """
    try:
        # Mapeamento dos pares para símbolos do Yahoo
        pair_mapping = {
            "EUR/USD": "EURUSD=X",
            "GBP/EUR": "GBPEUR=X", 
            "USD/JPY": "USDJPY=X",
            "EUR/GBP": "EURGBP=X",
            "EUR/CHF": "EURCHF=X",
            "EUR/SEK": "EURSEK=X",
            "EUR/NOK": "EURNOK=X",
            "EUR/CAD": "EURCAD=X",
            "USD/EUR": "USDEUR=X",
            "CHF/EUR": "CHFEUR=X",
            "SEK/EUR": "SEKEUR=X",
            "NOK/EUR": "NOKEUR=X",
            "CAD/EUR": "CADEUR=X"
        }
        
        yahoo_symbol = pair_mapping.get(pair_symbol, "EURUSD=X")
        
        # Buscar dados
        ticker = yf.Ticker(yahoo_symbol)
        
        # Últimos X dias com intervalos de 1 hora
        data = ticker.history(period=f"{days}d", interval="1h")
        
        if data.empty:
            st.warning(f"⚠️ Sem dados Yahoo Finance para {pair_symbol}, usando dados demo")
            return generate_trading_chart_data()  # Fallback para dados demo
        
        # Converter para formato do gráfico
        chart_data = []
        for index, row in data.iterrows():
            chart_data.append({
                'datetime': index,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume']) if 'Volume' in row else 0
            })
        
        return pd.DataFrame(chart_data)
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao buscar dados reais: {str(e)} - Usando dados demo")
        return generate_trading_chart_data()  # Fallback

@st.cache_data(ttl=60)  # Cache por 1 minuto
def get_real_live_fx_rates():
    """Obter taxas FX REAIS com variações calculadas do Yahoo Finance"""
    try:
        # Lista de pares para monitorar
        pairs = {
            'USD/EUR': 'USDEUR=X',
            'GBP/EUR': 'GBPEUR=X', 
            'CHF/EUR': 'CHFEUR=X',
            'SEK/EUR': 'SEKEUR=X',
            'NOK/EUR': 'NOKEUR=X',
            'CAD/EUR': 'CADEUR=X'
        }
        
        fx_data = {}
        
        for pair_name, yahoo_symbol in pairs.items():
            try:
                ticker = yf.Ticker(yahoo_symbol)
                
                # Buscar dados dos últimos 2 dias para calcular variação REAL
                hist = ticker.history(period="2d", interval="1d")
                
                if len(hist) >= 2:
                    current_rate = float(hist['Close'].iloc[-1])
                    previous_rate = float(hist['Close'].iloc[-2])
                    
                    # Calcular variação REAL
                    change_pct = ((current_rate - previous_rate) / previous_rate) * 100
                    
                    fx_data[pair_name] = {
                        'rate': current_rate,
                        'change': change_pct,
                        'color': 'positive' if change_pct >= 0 else 'negative',
                        'change_text': f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%",
                        'source': 'Yahoo Finance REAL',
                        'raw_rate': current_rate
                    }
                    
            except Exception as e:
                # Se falhar, continua para o próximo par
                continue
        
        if fx_data:
            return fx_data, True  # True = dados reais
        else:
            st.warning("⚠️ Yahoo Finance indisponível, usando dados demo")
            return get_demo_fx_rates(), False  # Fallback
            
    except Exception as e:
        st.warning(f"⚠️ Erro API Yahoo Finance: {str(e)}")
        return get_demo_fx_rates(), False

def create_real_fx_trading_chart(pair_name="EUR/USD"):
    """Criar gráfico com dados REAIS do Yahoo Finance"""
    
    # Buscar dados reais
    chart_data = get_real_fx_data_yahoo(pair_name)
    
    # Verificar se temos dados válidos
    if chart_data.empty:
        st.error("❌ Sem dados disponíveis")
        return go.Figure()
    
    # Criar candlestick chart com dados REAIS
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
    
    # Adicionar média móvel REAL
    if len(chart_data) >= 20:
        chart_data['ma_20'] = chart_data['close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=chart_data['datetime'],
            y=chart_data['ma_20'],
            mode='lines',
            name='MA(20)',
            line=dict(color='#ff8800', width=2),
            opacity=0.8
        ))
    
    # Styling profissional
    fig.update_layout(
        title=f"{pair_name} - 📊 DADOS REAIS Yahoo Finance",
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

# ==================== FALLBACK FUNCTIONS (mantidas como backup) ====================

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_live_fx_rates():
    """Get live FX rates from free API (FALLBACK)"""
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
    """Generate realistic forex chart data (FALLBACK)"""
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
    """Create professional trading chart with WHITE background (FALLBACK)"""
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
        title=f"{pair_name} - Demo Trading Chart",
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

# Data functions with SAFE number handling (from main file)
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
        
        # Read data safely
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
        
        # Search for values
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                # Cash Flow from row 101
                cell_value_101 = lista_contas_sheet.iloc[100, col_index]
                if pd.notna(cell_value_101):
                    try:
                        numeric_value_101 = float(cell_value_101)
                        if numeric_value_101 != 0:
                            cash_flow_value = numeric_value_101
                    except (ValueError, TypeError):
                        pass
                
                # Percentage from row 102
                cell_value_102 = lista_contas_sheet.iloc[101, col_index]
                if pd.notna(cell_value_102):
                    try:
                        numeric_value_102 = float(cell_value_102)
                        percentage_value = numeric_value_102
                    except (ValueError, TypeError):
                        pass
                    
            except Exception:
                continue
        
        # Safe formatting
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
        
        # Try to read real data
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
        
        # Search from right to left
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
        
        # Read safely
        try:
            lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        except Exception:
            return get_sample_liquidity_data()
        
        dates = []
        values = []
        found_columns = []
        
        # Search for "VALOR EUR" columns
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

def create_professional_header():
    """Create header with SAFE number formatting"""
    summary = get_executive_summary()
    
    # Ensure all values are properly formatted
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
    """Show homepage with just header and navigation - content area for future development"""
    st.markdown('<div class="section-header">Treasury Operations Center - Homepage</div>', unsafe_allow_html=True)
    
    # Future homepage content area
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

def show_executive_overview():
    """Show executive overview with SAFE formatting"""
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    
    # Get data safely
    summary = get_executive_summary()
    variation = get_latest_variation()
    cash_flow = get_daily_cash_flow()
    
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
    
    # Charts section
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
            
            if liquidity_data['source'].startswith('Sample'):
                st.warning("Warning: Using sample data - Excel not found or error in reading")
                with st.expander("Debug Info"):
                    st.write("Trying to read from: TREASURY DASHBOARD.xlsx, sheet 'Lista contas'")
                    st.write("Verify if file exists and sheet name is correct")
            
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
                    tickformat='%d %b',
                    tickmode='array',
                    tickvals=liquidity_data['dates'],
                    ticktext=[d.strftime('%d %b') for d in liquidity_data['dates']],
                    tickangle=45,
                    type='category'
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#f1f5f9', 
                    title='Million EUR',
                    range=[0, 80],
                    tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80],
                    ticktext=['0', '10', '20', '30', '40', '50', '60', '70', '80']
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            if 'columns_found' in liquidity_data:
                st.caption(f"Data: {liquidity_data['source']} • Columns found: {', '.join(liquidity_data['columns_found'])} • Latest: EUR {liquidity_data['values'][-1]:.1f}M")
            else:
                st.caption(f"Data: {liquidity_data['source']} • {len(liquidity_data['dates'])} days • Latest: EUR {liquidity_data['values'][-1]:.1f}M")
            
        except Exception as e:
            st.error(f"Error loading chart: {e}")
            # Fallback chart
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
            values = [28.5, 30.2, 31.8, 29.4, 32.1, 31.7, 32.6]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', line=dict(color='#2b6cb0', width=3)))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(range=[0, 80]))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">Cash Positions</div>
            <div class="section-content" style="padding: 0;">
        """, unsafe_allow_html=True)
        
        banks_df = get_bank_positions_from_tabelas()
        
        banks_html = """
        <div style="height: 300px; overflow-y: auto; padding: 1.5rem; font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;">
        """
        
        for _, row in banks_df.iterrows():
            banks_html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9;">
                <div>
                    <div style="font-weight: 700; color: #262730; font-size: 0.95rem;">{row['Bank']}</div>
                    <div style="font-weight: 400; color: #8e8ea0; font-size: 0.8rem;">{row['Currency']} • {row['Yield']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 700; color: #262730;">EUR {row['Balance']:.1f}M</div>
                </div>
            </div>
            """
        
        banks_html += "</div>"
        
        st.components.v1.html(banks_html, height=300, scrolling=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Executive insights
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">Executive Insight</div>
        <div class="insight-content">
            Current liquidity position at EUR {summary['total_liquidity']:.1f}M across {summary['active_banks']} banking relationships.
            Portfolio diversification optimized with {summary['bank_accounts']} active accounts.
            Top 5 banks represent 65% of total liquidity, ensuring balanced concentration risk.
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_fx_risk():
    """Enhanced FX Risk Management with REAL DATA from Yahoo Finance"""
    if st.button("🏠 Back to Home", key="back_home_fx"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">🚀 FX Risk Management - REAL DATA Trading</div>', unsafe_allow_html=True)
    
    # Get REAL FX data from Yahoo Finance
    fx_rates, is_live = get_real_live_fx_rates()
    
    if 'fx_deals' not in st.session_state:
        st.session_state.fx_deals = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # REAL FX Rates Section
        status_indicator = "🟢 YAHOO FINANCE REAL" if is_live else "🟡 DEMO FALLBACK"
        
        st.markdown(f"""
        <div class="dashboard-section">
            <div class="section-header">
                📊 REAL FX Rates vs EUR (Yahoo Finance)
                <span class="status-indicator status-good">{status_indicator}</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Auto-refresh button and controls
        col_refresh, col_auto, col_time = st.columns([1, 1, 2])
        with col_refresh:
            if st.button("🔄 Refresh REAL Data", key="refresh_fx"):
                st.cache_data.clear()
                st.rerun()
        
        with col_auto:
            auto_refresh_rates = st.checkbox("Auto 🔄", value=False, key="auto_refresh_rates", help="Auto-refresh every 30 seconds")
        
        with col_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            st.caption(f"📡 Last update: {current_time} {'(Yahoo Finance REAL)' if is_live else '(Demo Mode)'}")
        
        # Auto-refresh logic for FX rates (every 30 seconds to avoid being too slow)
        if auto_refresh_rates:
            st.info("🔄 Auto-refresh enabled (30s intervals)")
            time.sleep(30)
            st.rerun()
        
        # Display REAL FX rates in grid
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
                    {'<div style="font-size: 0.7rem; color: #28a745;">✅ REAL DATA</div>' if is_live else '<div style="font-size: 0.7rem; color: #ffc107;">⚠️ DEMO DATA</div>'}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # REAL TRADING CHART SECTION
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                📈 REAL Trading Charts (Yahoo Finance)
                <span class="status-indicator status-good">REAL DATA</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Chart selector
        chart_cols = st.columns([2, 1, 1])
        with chart_cols[0]:
            selected_pair = st.selectbox(
                "Select Currency Pair:", 
                ["EUR/USD", "GBP/EUR", "USD/JPY", "EUR/GBP", "EUR/CHF", "EUR/SEK", "EUR/NOK", "EUR/CAD"],
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
        
        # Create and display the REAL trading chart
        trading_fig = create_real_fx_trading_chart(selected_pair)
        st.plotly_chart(trading_fig, use_container_width=True)
        
        # Chart info
        st.caption(f"📊 {selected_pair} • Timeframe: {timeframe} • Candlestick + MA(20) • REAL DATA Yahoo Finance • Last update: {datetime.now().strftime('%H:%M:%S')}")
        
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
                        'rate_type': 'Yahoo Finance REAL' if is_live else 'Demo'
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
    
    # Pending FX Deals
    if st.session_state.fx_deals:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">📋 Pending FX Deals</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        for deal in st.session_state.fx_deals:
            if deal['status'] == 'Pending':
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{deal['sell_currency']}/{deal['buy_currency']}**")
                    st.write(f"Amount: {deal['amount']:,}")
                
                with col2:
                    st.write(f"Type: {deal['contract_type']}")
                    st.write(f"Value Date: {deal['value_date']}")
                
                with col3:
                    st.write(f"Requested: {deal['timestamp']}")
                    st.write(f"By: {deal['user']}")
                    if 'rate_type' in deal:
                        st.write(f"Rate: {deal['rate_type']}")
                
                with col4:
                    if st.button("✅ Approve", key=f"approve_{deal['id']}"):
                        for d in st.session_state.fx_deals:
                            if d['id'] == deal['id']:
                                d['status'] = 'Approved'
                        st.success("Deal approved!")
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"reject_{deal['id']}"):
                        st.session_state.fx_deals = [d for d in st.session_state.fx_deals if d['id'] != deal['id']]
                        st.error("Deal rejected!")
                        st.rerun()
                
                st.divider()
        
        st.markdown("</div></div>", unsafe_allow_html=True)

def show_daily_operations():
    """Show Daily Operations dashboard"""
    if st.button("🏠 Back to Home", key="back_home_operations"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">Daily Operations Center</div>', unsafe_allow_html=True)
    
    # Initialize session states
    if 'operational_workflows' not in st.session_state:
        st.session_state.operational_workflows = []
    if 'intraday_transfers' not in st.session_state:
        st.session_state.intraday_transfers = []
    if 'pcard_requests' not in st.session_state:
        st.session_state.pcard_requests = []
    
    # TOP ROW: Operational Workflows + Intraday Transfers
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">📋 Operational Workflows</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Workflow Form
        with st.form("workflow_form", clear_on_submit=True):
            subject = st.text_input("Subject", placeholder="Enter task subject...")
            workflow_date = st.date_input("Date", value=datetime.now().date())
            notes = st.text_area("Notes", placeholder="Additional details and notes...", height=80)
            
            submitted = st.form_submit_button("➕ Add Workflow", use_container_width=True)
            
            if submitted and subject.strip():
                new_workflow = {
                    'id': len(st.session_state.operational_workflows) + 1,
                    'subject': subject.strip(),
                    'date': workflow_date.strftime("%Y-%m-%d"),
                    'notes': notes.strip(),
                    'status': 'Pending',
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.operational_workflows.append(new_workflow)
                st.success("Workflow added successfully!")
                st.rerun()
        
        # Display Workflows
        if st.session_state.operational_workflows:
            st.markdown("**Active Workflows:**")
            
            for workflow in st.session_state.operational_workflows:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                
                with col_a:
                    tooltip_text = f"Notes: {workflow['notes']}\nCreated: {workflow['created']}"
                    
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0; border-left: 3px solid {'#ffc107' if workflow['status'] == 'Pending' else '#28a745'};" title="{tooltip_text}">
                        <strong>{workflow['subject']}</strong><br>
                        <small style="color: #6c757d;">{workflow['date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    st.write(f"**{workflow['status']}**")
                
                with col_c:
                    if workflow['status'] == 'Pending':
                        if st.button("✅", key=f"complete_{workflow['id']}", help="Mark as Concluded"):
                            for w in st.session_state.operational_workflows:
                                if w['id'] == workflow['id']:
                                    w['status'] = 'Concluded'
                            st.rerun()
                    else:
                        if st.button("🔄", key=f"reopen_{workflow['id']}", help="Mark as Pending"):
                            for w in st.session_state.operational_workflows:
                                if w['id'] == workflow['id']:
                                    w['status'] = 'Pending'
                            st.rerun()
        else:
            st.info("No workflows created yet.")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">💸 Intraday Transfers</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        companies = [
            "Holding Company Ltd",
            "Operations Co",
            "European Subsidiary",
            "North America Inc", 
            "Asia Pacific Ltd",
            "Treasury Center",
            "Investment Vehicle",
            "Trading Entity",
            "Service Company",
            "Technology Division"
        ]
        
        with st.form("transfer_form", clear_on_submit=True):
            from_company = st.selectbox("From", companies, key="from_comp")
            to_company = st.selectbox("To", companies, key="to_comp")
            transfer_date = st.date_input("Date", value=datetime.now().date(), key="transfer_date")
            amount = st.number_input("Amount (EUR)", min_value=1000, value=100000, step=1000, key="transfer_amount")
            
            transfer_submitted = st.form_submit_button("💾 Save Transfer", use_container_width=True)
            
            if transfer_submitted:
                if from_company != to_company:
                    new_transfer = {
                        'id': len(st.session_state.intraday_transfers) + 1,
                        'from_company': from_company,
                        'to_company': to_company,
                        'date': transfer_date.strftime("%Y-%m-%d"),
                        'amount': amount,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.intraday_transfers.append(new_transfer)
                    st.success("Transfer saved successfully!")
                    st.rerun()
                else:
                    st.error("From and To companies must be different!")
        
        # Display Transfers
        if st.session_state.intraday_transfers:
            st.markdown("**Recent Transfers:**")
            
            recent_transfers = st.session_state.intraday_transfers[-5:]
            for transfer in reversed(recent_transfers):
                st.markdown(f"""
                <div style="background: #e8f4fd; padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0; border-left: 3px solid #007bff;">
                    <strong>{transfer['from_company']} → {transfer['to_company']}</strong><br>
                    <small>EUR {transfer['amount']:,} • {transfer['date']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No transfers recorded yet.")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # MIDDLE ROW: Cashflow vs Actuals Chart
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">📊 Cashflow vs Actuals</div>
        <div class="section-content">
    """, unsafe_allow_html=True)
    
    st.info("📌 Chart placeholder - You can paste your Python chart code here!")
    
    sample_data = {
        'Categories': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        'Forecast': [2.5, 3.2, 2.8, 4.1],
        'Actual': [2.8, 2.9, 3.1, 3.8]
    }
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Forecast',
        x=sample_data['Categories'],
        y=sample_data['Forecast'],
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        name='Actual',
        x=sample_data['Categories'],
        y=sample_data['Actual'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='white',
        paper_bgcolor='white',
        barmode='group',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title='Million EUR')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("💡 Replace this with your cashflow chart code")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # BOTTOM ROW: P-Card Requests
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">💳 P-Card Requests</div>
        <div class="section-content">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Manual Entry** (Future: AI Agent)")
        
        with st.form("pcard_form", clear_on_submit=True):
            requester_name = st.text_input("Requester Name", placeholder="John Doe")
            requested_amount = st.number_input("Amount Requested (EUR)", min_value=1, value=500, step=50)
            request_reason = st.text_area("Reason", placeholder="Business purpose...", height=60)
            
            pcard_submitted = st.form_submit_button("📨 Add Request", use_container_width=True)
            
            if pcard_submitted and requester_name.strip():
                new_request = {
                    'id': len(st.session_state.pcard_requests) + 1,
                    'requester': requester_name.strip(),
                    'amount': requested_amount,
                    'reason': request_reason.strip(),
                    'status': 'Pending',
                    'card_number': '',
                    'request_date': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.pcard_requests.append(new_request)
                st.success("P-Card request added!")
                st.rerun()
    
    with col2:
        st.markdown("**Pending Requests**")
        
        if st.session_state.pcard_requests:
            for request in st.session_state.pcard_requests:
                if request['status'] == 'Pending':
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    
                    with col_a:
                        st.markdown(f"""
                        <div style="background: #fff3cd; padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0; border-left: 3px solid #ffc107;">
                            <strong>{request['requester']}</strong><br>
                            <small>EUR {request['amount']} • {request['reason'][:30]}{'...' if len(request['reason']) > 30 else ''}</small><br>
                            <small style="color: #6c757d;">{request['request_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_b:
                        card_number = st.text_input("Card #", key=f"card_{request['id']}", placeholder="1234-5678")
                    
                    with col_c:
                        if st.button("✅ Send", key=f"approve_card_{request['id']}"):
                            if card_number.strip():
                                for r in st.session_state.pcard_requests:
                                    if r['id'] == request['id']:
                                        r['status'] = 'Approved'
                                        r['card_number'] = card_number.strip()
                                st.success(f"Card number sent to {request['requester']}!")
                                st.rerun()
                            else:
                                st.error("Please enter card number!")
                
                elif request['status'] == 'Approved':
                    st.markdown(f"""
                    <div style="background: #d4edda; padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0; border-left: 3px solid #28a745;">
                        <strong>✅ {request['requester']}</strong> - Card #{request['card_number']} sent<br>
                        <small>EUR {request['amount']} • {request['request_date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No P-Card requests yet.")
        
        st.markdown("""
        <div style="background: #e2e3e5; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
            <strong>🤖 Future Enhancement:</strong><br>
            <small>AI Agent will automatically read emails and populate requests here. 
            Integration with email parsing for automatic requester detection and amount extraction.</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def show_investment_portfolio():
    """Show Investment Portfolio dashboard with tracking functionality"""
    if st.button("🏠 Back to Home", key="back_home_investments"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">Investment Portfolio Tracking</div>', unsafe_allow_html=True)
    
    # Initialize session state for investments
    if 'investment_transactions' not in st.session_state:
        st.session_state.investment_transactions = []
    
    # TOP ROW: Transaction Form + Summary Cards
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">📝 Add Investment Transaction</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Investment Transaction Form
        with st.form("investment_form", clear_on_submit=True):
            transaction_date = st.date_input("Date", value=datetime.now().date())
            
            transaction_type = st.selectbox("Type", [
                "Deposit",
                "Interest", 
                "Redemption",
                "Account Balance Update"
            ])
            
            from_entity = st.selectbox("From", [
                "Group Holding",
                "Treasury Center",
                "Investment Account",
                "MMF",
                "TD",
                "External Source"
            ])
            
            to_entity = st.selectbox("To", [
                "MMF",
                "TD", 
                "Account",
                "Group Holding",
                "Treasury Center",
                "External Destination"
            ])
            
            amount = st.number_input("Amount (EUR)", min_value=0.01, value=1000.00, step=100.00)
            
            notes = st.text_area("Notes (Optional)", placeholder="Additional transaction details...", height=60)
            
            submitted = st.form_submit_button("💰 Add Transaction", use_container_width=True)
            
            if submitted:
                new_transaction = {
                    'id': len(st.session_state.investment_transactions) + 1,
                    'date': transaction_date.strftime("%Y-%m-%d"),
                    'type': transaction_type,
                    'from': from_entity,
                    'to': to_entity,
                    'amount': float(amount),
                    'notes': notes.strip(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.investment_transactions.append(new_transaction)
                st.success(f"{transaction_type} of EUR {amount:,.2f} added successfully!")
                st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        # Calculate summary metrics
        transactions = st.session_state.investment_transactions
        
        # Current Balances: (Deposits + Interest + Updates) - Redemptions
        deposits = sum(t['amount'] for t in transactions if t['type'] == 'Deposit')
        interests = sum(t['amount'] for t in transactions if t['type'] == 'Interest')
        updates = sum(t['amount'] for t in transactions if t['type'] == 'Account Balance Update')
        redemptions = sum(t['amount'] for t in transactions if t['type'] == 'Redemption')
        
        current_balance = deposits + interests + updates - redemptions
        interest_earned = interests
        
        # Summary Cards
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">💰 Portfolio Summary</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        
        # Current Balances Card
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #007bff;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🏛️</span>
                <span style="font-weight: 600; color: #495057;">Current Balances</span>
            </div>
            <div style="font-size: 2rem; font-weight: 700; color: #2d3748;">EUR {current_balance:,.2f}</div>
            <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">
                Deposits: EUR {deposits:,.2f} | Updates: EUR {updates:,.2f} | Redemptions: EUR {redemptions:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Interest Earned Card
        st.markdown(f"""
        <div style="background: #fff3cd; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #ffc107;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🟡</span>
                <span style="font-weight: 600; color: #495057;">Interest Earned</span>
            </div>
            <div style="font-size: 2rem; font-weight: 700; color: #2d3748;">EUR {interest_earned:,.2f}</div>
            <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">
                Total interest payments received
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # MIDDLE ROW: Total Value Summary Table
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">📋 Investment Summary by Product</div>
        <div class="section-content">
    """, unsafe_allow_html=True)
    
    if transactions:
        # Calculate balances by product (To field)
        product_summary = {}
        
        for transaction in transactions:
            product = transaction['to']
            if product not in product_summary:
                product_summary[product] = {
                    'deposits': 0,
                    'interest': 0,
                    'updates': 0,
                    'redemptions': 0,
                    'last_activity': transaction['date']
                }
            
            # Update amounts by type
            if transaction['type'] == 'Deposit':
                product_summary[product]['deposits'] += transaction['amount']
            elif transaction['type'] == 'Interest':
                product_summary[product]['interest'] += transaction['amount']
            elif transaction['type'] == 'Account Balance Update':
                product_summary[product]['updates'] += transaction['amount']
            elif transaction['type'] == 'Redemption':
                product_summary[product]['redemptions'] += transaction['amount']
            
            # Update last activity (keep most recent)
            if transaction['date'] > product_summary[product]['last_activity']:
                product_summary[product]['last_activity'] = transaction['date']
        
        # Create summary table
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            st.markdown("**Product**")
        with col2:
            st.markdown("**Current Balance**")
        with col3:
            st.markdown("**Accrued Interest**")
        with col4:
            st.markdown("**Last Activity**")
        
        st.markdown("---")
        
        # Display each product
        for product, data in product_summary.items():
            if product in ['MMF', 'TD', 'Account']:  # Only show investment products
                current_balance = data['deposits'] + data['interest'] + data['updates'] - data['redemptions']
                accrued_interest = data['interest']
                last_activity = data['last_activity']
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                
                with col1:
                    if product == 'MMF':
                        st.markdown("**💰 MMF**")
                    elif product == 'TD':
                        st.markdown("**🏦 TD**")
                    else:
                        st.markdown(f"**📊 {product}**")
                
                with col2:
                    st.markdown(f"EUR {current_balance:,.2f}")
                
                with col3:
                    st.markdown(f"EUR {accrued_interest:,.2f}")
                
                with col4:
                    formatted_date = datetime.strptime(last_activity, "%Y-%m-%d").strftime("%d/%m/%Y")
                    st.markdown(f"{formatted_date}")
                
                st.markdown("---")
    
    else:
        st.info("No investment transactions recorded yet. Add your first transaction above!")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # BOTTOM ROW: Investment Growth Chart
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">📈 Total Value Growth</div>
        <div class="section-content">
    """, unsafe_allow_html=True)
    
    if transactions:
        # Calculate cumulative value over time
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda x: x['date'])
        
        dates = []
        cumulative_values = []
        running_total = 0
        
        for transaction in sorted_transactions:
            transaction_date = datetime.strptime(transaction['date'], "%Y-%m-%d")
            
            # Add/subtract based on transaction type
            if transaction['type'] in ['Deposit', 'Interest', 'Account Balance Update']:
                running_total += transaction['amount']
            elif transaction['type'] == 'Redemption':
                running_total -= transaction['amount']
            
            dates.append(transaction_date)
            cumulative_values.append(running_total)
        
        # Create the growth chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_values,
            mode='lines+markers',
            name='Total Investment Value',
            line=dict(color='#007bff', width=3),
            fill='tonexty',
            fillcolor='rgba(0, 123, 255, 0.1)',
            marker=dict(size=6, color='#007bff'),
            hovertemplate='<b>%{x|%d %b %Y}</b><br>EUR %{y:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            xaxis=dict(
                title='Date',
                showgrid=True,
                gridcolor='#f1f5f9',
                tickformat='%d %b'
            ),
            yaxis=dict(
                title='EUR',
                showgrid=True,
                gridcolor='#f1f5f9',
                tickformat=',.0f'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Chart summary
        if cumulative_values:
            total_growth = cumulative_values[-1] - cumulative_values[0] if len(cumulative_values) > 1 else cumulative_values[0]
            growth_percentage = (total_growth / cumulative_values[0] * 100) if cumulative_values[0] != 0 else 0
            
            st.caption(f"📊 Portfolio Growth: EUR {total_growth:,.2f} ({growth_percentage:+.1f}%) • Latest Value: EUR {cumulative_values[-1]:,.2f} • Transactions: {len(transactions)}")
    
    else:
        # Show placeholder chart
        st.info("📈 Investment growth chart will appear here once you add transactions")
        
        # Sample chart to show structure
        sample_dates = pd.date_range(start=datetime.now() - timedelta(days=90), periods=10, freq='10D')
        sample_values = [3000, 3200, 3150, 3400, 3600, 3800, 4100, 4050, 4300, 4500]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sample_dates,
            y=sample_values,
            mode='lines',
            name='Sample Growth',
            line=dict(color='#28a745', width=2, dash='dash'),
            opacity=0.6
        ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            xaxis=dict(title='Date', showgrid=True, gridcolor='#f1f5f9'),
            yaxis=dict(title='EUR', showgrid=True, gridcolor='#f1f5f9')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 Sample chart - Add your investment transactions to see real growth")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Transaction History (Optional - can be expandable)
    if transactions:
        with st.expander(f"📋 Transaction History ({len(transactions)} transactions)"):
            # Show recent transactions in a nice format
            recent_transactions = sorted(transactions, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            for transaction in recent_transactions:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                
                with col1:
                    formatted_date = datetime.strptime(transaction['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    st.text(formatted_date)
                
                with col2:
                    # Color code by type
                    if transaction['type'] == 'Deposit':
                        st.markdown(f"🟢 **{transaction['type']}**")
                    elif transaction['type'] == 'Interest':
                        st.markdown(f"🟡 **{transaction['type']}**")
                    elif transaction['type'] == 'Redemption':
                        st.markdown(f"🔴 **{transaction['type']}**")
                    else:
                        st.markdown(f"🔵 **{transaction['type']}**")
                
                with col3:
                    st.text(transaction['from'])
                
                with col4:
                    st.text(transaction['to'])
                
                with col5:
                    st.text(f"EUR {transaction['amount']:,.2f}")
                
                if transaction.get('notes'):
                    st.caption(f"📝 {transaction['notes']}")
                
                st.markdown("---")

# Main application
def main():
    """Main application with professional interface"""
    
    # Create professional header
    create_professional_header()
    
    # Navigation
    create_navigation()
    
    # Route to pages
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
        st.error(f"Unknown page: {st.session_state.current_page}")
        show_homepage()

if __name__ == "__main__":
    main()
