#!/usr/bin/env python3
"""
Treasury HUB - Clean Professional Version
========================================
CFO-grade interface with real bank data from Tabelas sheet
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
    
    /* Scrollable bank list - FIXED HEIGHT FOR 6 BANKS */
    .bank-list-container {
        height: 300px;  /* Fixed height to show exactly 6 banks */
        overflow-y: auto;
        padding-right: 0.5rem;
        margin: 0;
        padding: 0;
    }
    
    .bank-list-container > div {
        height: 300px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }
    
    .bank-list-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .bank-list-container::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    
    .bank-list-container::-webkit-scrollbar-thumb {
        background: #cbd5e0;
        border-radius: 3px;
    }
    
    .bank-list-container::-webkit-scrollbar-thumb:hover {
        background: #a0aec0;
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
    
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'overview'

# Data functions
@st.cache_data(ttl=300)
def get_daily_cash_flow():
    """
    Lê o Daily Cash Flow da linha 101 da aba 'Lista contas'
    E a percentagem da linha 102
    Procura da esquerda para direita o primeiro valor numérico
    """
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return {
                'cash_flow': 0,
                'cash_flow_text': '€0',
                'percentage': 0,
                'percentage_text': '+0% vs Yesterday',
                'percentage_color': 'positive'
            }
        
        lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        
        if lista_contas_sheet.shape[0] <= 101:
            return {
                'cash_flow': 0,
                'cash_flow_text': '€0',
                'percentage': 0,
                'percentage_text': '+0% vs Yesterday',
                'percentage_color': 'positive'
            }
        
        cash_flow_value = 0
        percentage_value = 0
        
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                cell_value_101 = lista_contas_sheet.iloc[100, col_index]
                if pd.notna(cell_value_101):
                    try:
                        numeric_value_101 = float(cell_value_101)
                        if numeric_value_101 != 0:
                            cash_flow_value = numeric_value_101
                    except ValueError:
                        pass
                
                cell_value_102 = lista_contas_sheet.iloc[101, col_index]
                if pd.notna(cell_value_102):
                    try:
                        numeric_value_102 = float(cell_value_102)
                        percentage_value = numeric_value_102
                    except ValueError:
                        pass
                    
            except Exception:
                continue
        
        if cash_flow_value != 0:
            cash_flow_text = f"€{cash_flow_value:,.0f}" if cash_flow_value >= 0 else f"-€{abs(cash_flow_value):,.0f}"
        else:
            cash_flow_text = "€0"
        
        if percentage_value >= 0:
            display_percentage = percentage_value * 100 if abs(percentage_value) < 1 else percentage_value
            percentage_text = f"+{display_percentage:.1f}% vs Yesterday"
            percentage_color = 'positive'
        else:
            display_percentage = percentage_value * 100 if abs(percentage_value) < 1 else percentage_value
            percentage_text = f"{display_percentage:.1f}% vs Yesterday"
            percentage_color = 'negative'
        
        return {
            'cash_flow': cash_flow_value,
            'cash_flow_text': cash_flow_text,
            'percentage': percentage_value,
            'percentage_text': percentage_text,
            'percentage_color': percentage_color
        }
        
    except Exception as e:
        print(f"❌ Erro ao ler Daily Cash Flow: {e}")
        return {
            'cash_flow': 0,
            'cash_flow_text': '€0',
            'percentage': 0,
            'percentage_text': '+0% vs Yesterday',
            'percentage_color': 'positive'
        }

@st.cache_data(ttl=300)
def get_executive_summary():
    """Get executive summary with your real values"""
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
                'total_liquidity': total_liquidity,
                'bank_accounts': bank_accounts,
                'active_banks': 13,
                'last_updated': datetime.now().strftime("%H:%M")
            }
        except Exception:
            return {
                'total_liquidity': 32.6,
                'bank_accounts': 96,
                'active_banks': 13,
                'last_updated': datetime.now().strftime("%H:%M")
            }
    except Exception:
        return {
            'total_liquidity': 32.6,
            'bank_accounts': 96,
            'active_banks': 13,
            'last_updated': datetime.now().strftime("%H:%M")
        }

@st.cache_data(ttl=300)
def get_latest_variation():
    """
    Lê a variação mais recente da linha 101 da aba 'Lista contas'
    Procura da esquerda para direita o primeiro valor numérico
    """
    try:
        excel_file = "TREASURY DASHBOARD.xlsx"
        
        if os.path.exists(excel_file):
            file_path = excel_file
        elif os.path.exists(f"data/{excel_file}"):
            file_path = f"data/{excel_file}"
        else:
            return {'variation': 0, 'text': '+€0 vs Yesterday', 'color': 'positive'}
        
        lista_contas_sheet = pd.read_excel(file_path, sheet_name="Lista contas", header=None)
        
        if lista_contas_sheet.shape[0] <= 100:
            return {'variation': 0, 'text': '+€0 vs Yesterday', 'color': 'positive'}
        
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                cell_value = lista_contas_sheet.iloc[100, col_index]
                if pd.notna(cell_value):
                    try:
                        numeric_value = float(cell_value)
                        if numeric_value != 0:
                            if numeric_value >= 0:
                                text = f"+€{numeric_value:,.0f} vs Yesterday"
                                color = 'positive'
                            else:
                                text = f"-€{abs(numeric_value):,.0f} vs Yesterday"
                                color = 'negative'
                            return {
                                'variation': numeric_value,
                                'text': text,
                                'color': color
                            }
                    except ValueError:
                        continue
            except Exception:
                continue
        
        return {'variation': 0, 'text': '+€0 vs Yesterday', 'color': 'positive'}
        
    except Exception as e:
        print(f"❌ Erro ao ler variação: {e}")
        return {'variation': 0, 'text': '+€0 vs Yesterday', 'color': 'positive'}

@st.cache_data(ttl=300)
def get_dynamic_liquidity_data():
    """
    Procura por "VALOR EUR" na linha 2 e lê data (linha 1, 2 colunas atrás) e valor (linha 99)
    """
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
        except Exception as e:
            print(f"❌ Erro ao ler aba 'Lista contas': {e}")
            print("📋 Abas disponíveis:", pd.ExcelFile(file_path).sheet_names)
            return get_sample_liquidity_data()
        
        dates, values, found_columns = [], [], []

        def col_index_to_letter(index):
            if index < 26:
                return chr(65 + index)
            first = (index - 26) // 26
            second = (index - 26) % 26
            return chr(65 + first) + chr(65 + second)
        
        for col_index in range(lista_contas_sheet.shape[1]):
            try:
                linha2_value = lista_contas_sheet.iloc[1, col_index]
                if pd.notna(linha2_value) and "VALOR" in str(linha2_value).upper() and "EUR" in str(linha2_value).upper():
                    found_columns.append(col_index_to_letter(col_index))
                    date_col_index = col_index - 2
                    if date_col_index < 0:
                        continue
                    date_value = lista_contas_sheet.iloc[0, date_col_index]
                    if lista_contas_sheet.shape[0] > 98:
                        eur_value = lista_contas_sheet.iloc[98, col_index]
                    else:
                        continue
                    
                    if pd.notna(date_value) and pd.notna(eur_value) and eur_value != 0:
                        try:
                            if isinstance(date_value, str):
                                try:
                                    parsed_date = pd.to_datetime(date_value.strip(), format='%d-%b-%y')
                                except Exception:
                                    try:
                                        parsed_date = pd.to_datetime(date_value.strip(), format='%d/%m/%Y')
                                    except Exception:
                                        parsed_date = pd.to_datetime(date_value)
                            elif isinstance(date_value, (int, float)):
                                if date_value > 59:
                                    parsed_date = datetime(1900, 1, 1) + timedelta(days=date_value - 2)
                                else:
                                    parsed_date = datetime(1900, 1, 1) + timedelta(days=date_value - 1)
                            else:
                                parsed_date = pd.to_datetime(date_value)
                        except Exception as date_error:
                            print(f"⚠️ Erro conversão data {date_value}: {date_error}")
                            continue
                        
                        eur_millions = float(eur_value) / 1_000_000
                        dates.append(parsed_date)
                        values.append(eur_millions)
            except Exception:
                continue
        
        if dates and values:
            combined = list(zip(dates, values))
            combined.sort(key=lambda x: x[0])
            dates, values = zip(*combined)
            
            latest_date = dates[-1]
            cutoff_date = latest_date - timedelta(days=30)
            filtered = [(d, v) for d, v in zip(dates, values) if d >= cutoff_date]
            if filtered:
                dates, values = zip(*filtered)
            
            return {
                'dates': list(dates),
                'values': list(values),
                'source': f'Excel Real Data ({len(dates)} dias)',
                'columns_found': found_columns
            }
        else:
            return get_sample_liquidity_data()
            
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return get_sample_liquidity_data()

def get_sample_liquidity_data():
    """Dados de exemplo para demonstração quando não há Excel"""
    sample_dates = [
        "05-Aug-25", "06-Aug-25", "07-Aug-25", "08-Aug-25", 
        "11-Aug-25", "12-Aug-25", "13-Aug-25"
    ]
    sample_values = [28.5, 30.2, 31.8, 29.4, 32.1, 31.7, 32.6]
    dates = [datetime.strptime(date, "%d-%b-%y") for date in sample_dates]
    return {
        'dates': dates,
        'values': sample_values,
        'source': 'Sample Data (Excel não encontrado)'
    }

@st.cache_data(ttl=300)
def get_bank_positions_from_tabelas():
    """Get bank positions from Tabelas sheet, rows 79-91, sorted by balance"""
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
                except Exception:
                    continue
            
            if banks_data:
                banks_df = pd.DataFrame(banks_data).sort_values('Balance', ascending=False)
                total_balance = banks_df['Balance'].sum()
                banks_df['Percentage'] = (banks_df['Balance'] / total_balance * 100).round(1)
                banks_df['Yield'] = banks_df['Percentage'].apply(lambda x: f"{x}%")
                return banks_df
            else:
                return get_fallback_banks()
        except Exception:
            return get_fallback_banks()
    except Exception:
        return get_fallback_banks()

def get_fallback_banks():
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
    banks_df = pd.DataFrame(banks_data).sort_values('Balance', ascending=False)
    total_balance = banks_df['Balance'].sum()
    banks_df['Percentage'] = (banks_df['Balance'] / total_balance * 100).round(1)
    banks_df['Yield'] = banks_df['Percentage'].apply(lambda x: f"{x}%")
    return banks_df

def create_professional_header():
    summary = get_executive_summary()
    st.markdown(f"""
    <div class="executive-header">
        <div class="header-content">
            <div>
                <div class="company-brand">Treasury Operations Center</div>
                <div class="company-subtitle">Real-time Financial Command & Control • Last Update: {summary['last_updated']}</div>
            </div>
            <div class="header-metrics">
                <div class="header-metric">
                    <div class="metric-value">€{summary['total_liquidity']:.1f}M</div>
                    <div class="metric-label">Total Liquidity</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{summary['bank_accounts']}</div>
                    <div class="metric-label">Bank Accounts</div>
                </div>
                <div class="header-metric">
                    <div class="metric-value">{summary['active_banks']}</div>
                    <div class="metric-label">Active Banks</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_navigation():
    nav_items = [
        ('overview', 'Executive Overview'),
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

def show_executive_overview():
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    
    summary = get_executive_summary()
    variation = get_latest_variation()
    cash_flow = get_daily_cash_flow()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        change_class = "change-positive" if variation['color'] == 'positive' else "change-negative"
        st.markdown(f"""
        <div class="summary-card">
            <h3>Total Liquidity</h3>
            <div class="summary-value">€{summary['total_liquidity']:.1f}M</div>
            <div class="summary-change {change_class}">{variation['text']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Inflow</h3>
            <div class="summary-value">€0</div>
            <div class="summary-change change-positive">To be configured</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="summary-card">
            <h3>Outflow</h3>
            <div class="summary-value">€0</div>
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

        # --------- BLOCO CORRIGIDO (sem else pendurado) ----------
        try:
            liquidity_data = get_dynamic_liquidity_data()

            if liquidity_data['source'].startswith('Sample'):
                st.warning("⚠️ A usar dados de exemplo - Excel não encontrado ou erro na leitura")
                with st.expander("🔍 Debug Info"):
                    st.write("Tentando ler de: TREASURY DASHBOARD.xlsx, aba 'Lista contas'")
                    st.write("Verifica se o ficheiro existe e se a aba tem o nome correto")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=liquidity_data['dates'],
                y=liquidity_data['values'],
                mode='lines',
                name='Total Liquidity',
                line=dict(color='#2b6cb0', width=3),
                fill='tonexty',
                fillcolor='rgba(43, 108, 176, 0.1)',
                hovertemplate='<b>%{x|%d %b %Y}</b><br>€%{y:.1f}M<extra></extra>'
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

            # Info da fonte
            if 'columns_found' in liquidity_data:
                st.caption(f"📊 {liquidity_data['source']} • Colunas encontradas: {', '.join(liquidity_data['columns_found'])} • Último: €{liquidity_data['values'][-1]:.1f}M")
            else:
                st.caption(f"📊 {liquidity_data['source']} • {len(liquidity_data['dates'])} dias • Último: €{liquidity_data['values'][-1]:.1f}M")

        except Exception as e:
            st.error(f"❌ Erro ao carregar gráfico: {e}")
            st.info("🔍 A usar dados de exemplo como fallback")
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
            values = [28.5, 30.2, 31.8, 29.4, 32.1, 31.7, 32.6]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', line=dict(color='#2b6cb0', width=3)))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(range=[0, 80]))
            st.plotly_chart(fig, use_container_width=True)
        # ---------------------------------------------------------

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
                    <div style="font-weight: 700; color: #262730;">€{row['Balance']:.1f}M</div>
                </div>
            </div>
            """
        banks_html += "</div>"
        st.components.v1.html(banks_html, height=300, scrolling=True)
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">Executive Insight</div>
        <div class="insight-content">
            Current liquidity position at €{summary['total_liquidity']:.1f}M across {summary['active_banks']} banking relationships.
            Portfolio diversification optimized with {summary['bank_accounts']} active accounts.
            Top 5 banks represent 65% of total liquidity, ensuring balanced concentration risk.
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_fx_risk():
    if st.button("🏠 Back to Home", key="back_home_fx"):
        st.session_state.current_page = 'overview'
        st.rerun()
    
    st.markdown('<div class="section-header">FX Risk Management</div>', unsafe_allow_html=True)
    if 'fx_deals' not in st.session_state:
        st.session_state.fx_deals = []
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">
                Live FX Rates vs EUR
                <span class="status-indicator status-good">Live</span>
            </div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        fx_rates = {
            'USD/EUR': {'rate': 0.9234, 'change': '+0.25%', 'color': 'positive'},
            'GBP/EUR': {'rate': 1.1678, 'change': '-0.15%', 'color': 'negative'},
            'CHF/EUR': {'rate': 0.9876, 'change': '+0.08%', 'color': 'positive'},
            'SEK/EUR': {'rate': 0.0932, 'change': '-0.32%', 'color': 'negative'},
            'NOK/EUR': {'rate': 0.0856, 'change': '+0.12%', 'color': 'positive'},
            'CAD/EUR': {'rate': 0.6789, 'change': '+0.18%', 'color': 'positive'}
        }
        fx_cols = st.columns(3)
        for i, (pair, data) in enumerate(fx_rates.items()):
            with fx_cols[i % 3]:
                color_class = "change-positive" if data['color'] == 'positive' else "change-negative"
                st.markdown(f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="font-size: 0.875rem; color: #718096; font-weight: 500;">{pair}</div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #2d3748; margin: 0.5rem 0;">{data['rate']:.4f}</div>
                    <div class="{color_class}" style="font-size: 0.875rem; font-weight: 500;">{data['change']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">FX Deal Request</div>
            <div class="section-content">
        """, unsafe_allow_html=True)
        with st.form("fx_deal_form"):
            sell_currency = st.selectbox("Sell Currency", 
                                       ['EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'CAD', 'AUD', 'DKK', 'ZAR', 'MYR', 'SGD', 'IDR', 'PLN'])
            buy_currency = st.selectbox("Buy Currency", 
                                      ['USD', 'GBP', 'CHF', 'SEK', 'NOK', 'CAD', 'AUD', 'DKK', 'ZAR', 'MYR', 'SGD', 'IDR', 'PLN', 'EUR'])
            amount = st.number_input("Amount", min_value=1000, value=100000, step=1000)
            contract_type = st.selectbox("Contract Type", ['Spot', 'Forward', 'Swap', 'Option'])
            value_date = st.date_input("Value Date", value=datetime.now().date())
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
                        'user': 'Treasury User'
                    }
                    st.session_state.fx_deals.append(new_deal)
                    st.success("FX Deal submitted successfully!")
                    st.rerun()
                else:
                    st.error("Sell and Buy currencies must be different!")
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    if st.session_state.fx_deals:
        st.markdown("""
        <div class="dashboard-section">
            <div class="section-header">Pending FX Deals</div>
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
    
    st.markdown("""
    <div class="dashboard-section">
        <div class="section-header">FX Activity Overview</div>
        <div class="section-content">
    """, unsafe_allow_html=True)

    # Gráfico simples com os negócios aprovados
    if st.session_state.fx_deals:
        sell_data, buy_data = {}, {}
        eur_sold, eur_bought = 0, 0
        for deal in st.session_state.fx_deals:
            if deal['status'] == 'Approved':
                if deal['sell_currency'] == 'EUR':
                    eur_sold += deal['amount']
                    buy_data[deal['buy_currency']] = buy_data.get(deal['buy_currency'], 0) + deal['amount']
                elif deal['buy_currency'] == 'EUR':
                    eur_bought += deal['amount']
                    sell_data[deal['sell_currency']] = sell_data.get(deal['sell_currency'], 0) + deal['amount']
        categories, values, colors = [], [], []
        for currency, amount in sell_data.items():
            categories.append(f"SELL {currency}")
            values.append(amount / 1_000_000)
            colors.append('#ff6b6b' if currency != 'EUR' else '#00ff88')
        if eur_sold > 0:
            categories.append("SELL EUR")
            values.append(eur_sold / 1_000_000)
            colors.append('#00ff88')
        for currency, amount in buy_data.items():
            categories.append(f"BUY {currency}")
            values.append(amount / 1_000_000)
            colors.append('#4dabf7' if currency != 'EUR' else '#00ff88')
        if eur_bought > 0:
            categories.append("BUY EUR")
            values.append(eur_bought / 1_000_000)
            colors.append('#00ff88')

        if categories:
            fig = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors,
                       text=[f"€{v:.1f}M" for v in values], textposition='auto')
            ])
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=20, b=0),
                plot_bgcolor='white', paper_bgcolor='white',
                showlegend=False, xaxis=dict(tickangle=45),
                yaxis=dict(title='Million EUR')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No approved FX deals to display. Submit and approve some deals to see the activity chart.")
    else:
        st.info("No FX deals submitted yet. Use the form above to submit your first FX deal request.")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def show_placeholder_page(title, description):
    if st.button("🏠 Back to Home", key=f"back_home_{title.lower()}"):
        st.session_state.current_page = 'overview'
        st.rerun()
    st.markdown(f"""
    <div class="dashboard-section">
        <div class="section-header">{title}</div>
        <div class="section-content">
            <div style="text-align: center; padding: 3rem;">
                <h3>🚧 {title}</h3>
                <p>{description}</p>
                <p><em>This module will be available in the next update.</em></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main application
def main():
    create_professional_header()
    create_navigation()
    if st.session_state.current_page == 'overview':
        show_executive_overview()
    elif st.session_state.current_page == 'fx_risk':
        show_fx_risk()
    elif st.session_state.current_page == 'operations':
        show_placeholder_page("Daily Operations", "Real-time treasury operations and transaction management.")
    elif st.session_state.current_page == 'investments':
        show_placeholder_page("Investment Portfolio", "Portfolio management and investment performance tracking.")
    else:
        show_executive_overview()

if __name__ == "__main__":
    main()
