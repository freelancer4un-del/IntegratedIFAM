"""
IFAM 통합 대시보드 v1.2
인프라프론티어자산운용(주) - Infra Frontier Asset Management

통합 기능:
1. 🌱 Daily Market - 친환경·인프라 투자 지표 (실시간 크롤링)
2. 📊 VC Analyzer - Term Sheet 분석 & 밸류에이션
3. 🏢 LP Discovery - LP & IPO 모니터링 (v2.4 통합)
4. 📈 Portfolio - 통합 포트폴리오 대시보드

v1.2 업데이트:
- 더미데이터 완전 제거, 실시간 크롤링만 사용
- LP Discovery를 LP & IPO 모니터링 대시보드 v2.4와 동일하게 변경
- IPO 4개 탭: 청약일정, 수요예측, 월별캘린더, 승인종목

작성: 2025.12
"""

import streamlit as st

# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="IFAM 통합 대시보드 | 인프라프론티어",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import xml.etree.ElementTree as ET
import time
import math
import re
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 전역 설정
# =============================================================================
DART_API_KEY = "d69ac794205d2dce718abfd6a27e4e4e295accae"
DART_BASE_URL = 'https://opendart.fss.or.kr/api'

# =============================================================================
# 세션 상태 초기화
# =============================================================================
def init_session_state():
    """세션 상태 초기화"""
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = get_default_portfolio_data()
    if 'fund_data' not in st.session_state:
        st.session_state.fund_data = get_default_fund_data()
    # LP 발굴용 세션 상태
    if 'lp_corp_list' not in st.session_state:
        st.session_state.lp_corp_list = None
    if 'lp_financial_data' not in st.session_state:
        st.session_state.lp_financial_data = pd.DataFrame()
    if 'lp_current_idx' not in st.session_state:
        st.session_state.lp_current_idx = 0

# =============================================================================
# 통합 CSS 스타일 시스템
# =============================================================================
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
        
        :root {
            --bg-primary: #09090b;
            --bg-secondary: #0f0f12;
            --bg-tertiary: #18181b;
            --bg-card: rgba(24, 24, 27, 0.8);
            --bg-hover: rgba(39, 39, 42, 0.8);
            --border-subtle: rgba(63, 63, 70, 0.5);
            --border-accent: rgba(99, 102, 241, 0.4);
            --glass-bg: rgba(255, 255, 255, 0.02);
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-indigo: #6366f1;
            --accent-violet: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --accent-sky: #0ea5e9;
            --gradient-brand: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        }
        
        .stApp {
            background: var(--bg-primary);
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
        }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-secondary); }
        ::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
        
        .main-header {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }
        .header-brand { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
        .header-logo { font-size: 2.5rem; }
        .header-title {
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.8rem;
            font-weight: 800;
        }
        .header-subtitle { color: var(--text-secondary); font-size: 0.9rem; }
        .header-meta { display: flex; gap: 1.5rem; margin-top: 0.75rem; }
        .header-meta-item { color: var(--text-muted); font-size: 0.8rem; display: flex; align-items: center; gap: 0.4rem; }
        
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.25rem;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }
        .card:hover { border-color: var(--border-accent); transform: translateY(-2px); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); }
        .card-title { color: var(--text-primary); font-size: 1rem; font-weight: 600; }
        .card-badge { background: var(--glass-bg); border: 1px solid var(--border-subtle); border-radius: 9999px; padding: 0.25rem 0.75rem; font-size: 0.7rem; color: var(--text-secondary); }
        
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }
        .metric-card:hover { border-color: var(--border-accent); }
        .metric-label { color: var(--text-muted); font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
        .metric-value { color: var(--text-primary); font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .metric-value.large { font-size: 2rem; }
        .metric-change { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.8rem; font-weight: 600; margin-top: 0.4rem; padding: 0.15rem 0.5rem; border-radius: 6px; }
        .metric-change.up { color: var(--accent-emerald); background: rgba(16, 185, 129, 0.1); }
        .metric-change.down { color: var(--accent-rose); background: rgba(244, 63, 94, 0.1); }
        .metric-change.neutral { color: var(--text-muted); background: var(--glass-bg); }
        
        .data-row {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }
        .data-row:hover { background: var(--bg-hover); border-color: var(--border-accent); }
        .data-row-left { display: flex; flex-direction: column; gap: 0.2rem; }
        .data-row-title { color: var(--text-primary); font-size: 0.95rem; font-weight: 600; }
        .data-row-subtitle { color: var(--text-muted); font-size: 0.8rem; }
        .data-row-value { color: var(--text-primary); font-size: 1rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
        
        .badge { display: inline-flex; align-items: center; padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.7rem; font-weight: 600; }
        .badge-indigo { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
        .badge-emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-rose { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
        .badge-sky { background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); }
        .badge-violet { background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); }
        
        .section-title { color: var(--text-primary); font-size: 1.1rem; font-weight: 700; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border-subtle); display: flex; align-items: center; gap: 0.5rem; }
        .section-title .icon { font-size: 1.2rem; }
        
        .info-box { background: rgba(99, 102, 241, 0.08); border-left: 3px solid var(--accent-indigo); padding: 1rem 1.2rem; border-radius: 0 10px 10px 0; margin: 1rem 0; }
        .info-box p { color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6; margin: 0; }
        .info-box strong { color: var(--text-primary); }
        
        .stTabs [data-baseweb="tab-list"] { gap: 4px; background: var(--bg-secondary); padding: 4px; border-radius: 10px; }
        .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: var(--text-secondary); font-weight: 500; padding: 0.5rem 1rem; }
        .stTabs [aria-selected="true"] { background: var(--gradient-brand); color: white; }
        
        section[data-testid="stSidebar"] { background: var(--bg-secondary); border-right: 1px solid var(--border-subtle); }
        
        .stButton > button { background: var(--gradient-brand); color: white; border: none; border-radius: 8px; font-weight: 600; padding: 0.6rem 1.2rem; transition: all 0.2s ease; }
        .stButton > button:hover { opacity: 0.9; transform: translateY(-1px); }
        
        .nav-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.5rem; cursor: pointer; transition: all 0.3s ease; text-align: center; }
        .nav-card:hover { border-color: var(--accent-indigo); transform: translateY(-4px); box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.3); }
        .nav-card-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
        .nav-card-title { color: var(--text-primary); font-size: 1.1rem; font-weight: 700; margin-bottom: 0.3rem; }
        .nav-card-desc { color: var(--text-muted); font-size: 0.85rem; }
        
        .ipo-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.75rem; transition: all 0.2s ease; }
        .ipo-card:hover { border-color: var(--accent-sky); }
        .ipo-name { color: var(--accent-sky); font-size: 1rem; font-weight: 700; margin-bottom: 0.3rem; }
        .ipo-detail { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.6; }
        .ipo-date { color: var(--accent-amber); font-weight: 600; }
        .ipo-price { color: var(--accent-emerald); font-weight: 600; }
        
        .company-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem; transition: all 0.2s; }
        .company-card:hover { border-color: var(--accent-indigo); }
        .company-name { color: var(--text-primary); font-size: 0.95rem; font-weight: 700; margin-bottom: 0.2rem; }
        .company-info { color: var(--text-secondary); font-size: 0.8rem; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 유틸리티 함수
# =============================================================================
def format_number(value, decimals=0, prefix='', suffix=''):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 'N/A'
    try:
        if abs(value) >= 1e12:
            return f"{prefix}{value/1e12:,.{decimals}f}조{suffix}"
        elif abs(value) >= 1e8:
            return f"{prefix}{value/1e8:,.{decimals}f}억{suffix}"
        elif abs(value) >= 1e4:
            return f"{prefix}{value/1e4:,.{decimals}f}만{suffix}"
        else:
            return f"{prefix}{value:,.{decimals}f}{suffix}"
    except:
        return str(value)

def format_number_simple(value, unit='억원'):
    """숫자 포맷팅 (LP용)"""
    if pd.isna(value) or value is None:
        return 'N/A'
    if abs(value) >= 10000:
        return f"{value/10000:,.1f}조원"
    return f"{value:,.0f}{unit}"

def get_change_class(change):
    if change > 0:
        return 'up', '▲'
    elif change < 0:
        return 'down', '▼'
    return 'neutral', '-'

# =============================================================================
# 수학 함수 (VC Analyzer용)
# =============================================================================
def norm_cdf(x):
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)

def black_scholes_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0 or S <= 0:
        return max(0, S - K)
    if K <= 0:
        return S
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return max(0, S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2))

# =============================================================================
# 데이터 클래스
# =============================================================================
@dataclass
class InvestmentRound:
    name: str
    investment: float
    shares: float
    is_participating: bool = True
    liquidation_multiple: float = 1.0
    seniority: int = 1

@dataclass
class GlobalInput:
    founder_shares: float = 100.0
    current_valuation: float = 100.0
    exit_valuation: float = 500.0
    volatility: float = 90.0
    risk_free_rate: float = 3.0
    holding_period: float = 5.0

@dataclass
class FundInfo:
    committed_capital: float = 1000.0
    management_fee_rate: float = 2.0
    carried_interest: float = 20.0
    hurdle_rate: float = 8.0

# =============================================================================
# 크롤링 함수들 - Daily Market (더미데이터 제거, 실제 크롤링만)
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_exchange_rates():
    """환율 정보 크롤링 - 실제 데이터만"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        # 방법 1: 네이버 금융 환율 목록
        url = 'https://finance.naver.com/marketindex/exchangeList.naver'
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rates = {}
        table = soup.find('table', class_='tbl_exchange')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        name_cell = cells[0]
                        name = name_cell.get_text(strip=True)
                        value_text = cells[1].get_text(strip=True).replace(',', '')
                        value = float(value_text)
                        
                        change_cell = cells[2]
                        change_text = change_cell.get_text(strip=True).replace(',', '')
                        try:
                            change = float(change_text)
                        except:
                            change = 0
                        
                        if 'down' in str(change_cell) or '하락' in str(change_cell):
                            change = -abs(change)
                        
                        if '미국' in name or 'USD' in name:
                            rates['USD'] = {'value': value, 'change': change, 'name': '미국 달러'}
                        elif '일본' in name:
                            rates['JPY'] = {'value': value, 'change': change, 'name': '일본 엔(100)'}
                        elif '유럽연합' in name or '유로' in name:
                            rates['EUR'] = {'value': value, 'change': change, 'name': '유로'}
                        elif '중국' in name:
                            rates['CNY'] = {'value': value, 'change': change, 'name': '중국 위안'}
                    except:
                        continue
        
        if rates:
            return rates
            
        # 방법 2: 메인 페이지에서 추출 (백업)
        url2 = 'https://finance.naver.com/marketindex/'
        response2 = requests.get(url2, headers=headers, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        for item in soup2.select('.market_data .data_lst li, #exchangeList li'):
            try:
                name_tag = item.select_one('h3, .h_lst, a')
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)
                
                value_tag = item.select_one('.value, .head_info .value, span.value')
                if not value_tag:
                    continue
                value = float(value_tag.get_text(strip=True).replace(',', ''))
                
                change_tag = item.select_one('.change, .head_info .change')
                change = 0
                if change_tag:
                    try:
                        change = float(change_tag.get_text(strip=True).replace(',', ''))
                    except:
                        pass
                
                if item.select_one('.down, .ico_down'):
                    change = -abs(change)
                
                if '달러' in name or 'USD' in name:
                    rates['USD'] = {'value': value, 'change': change, 'name': '미국 달러'}
                elif '엔' in name or '100' in name:
                    rates['JPY'] = {'value': value, 'change': change, 'name': '일본 엔(100)'}
                elif '유로' in name:
                    rates['EUR'] = {'value': value, 'change': change, 'name': '유로'}
                elif '위안' in name:
                    rates['CNY'] = {'value': value, 'change': change, 'name': '중국 위안'}
            except:
                continue
        
        return rates if rates else None
    except Exception as e:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_oil_prices():
    """국제유가 크롤링 - 실제 데이터만"""
    try:
        url = 'https://finance.naver.com/marketindex/worldDailyQuote.naver?marketindexCd=OIL_CL&fdtc=2'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        
        # WTI
        try:
            table = soup.find('table', class_='tbl_exchange')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    cells = rows[1].find_all('td')
                    if len(cells) >= 2:
                        value = float(cells[1].get_text(strip=True).replace(',', ''))
                        change = 0
                        if len(cells) >= 3:
                            try:
                                change = float(cells[2].get_text(strip=True).replace(',', ''))
                            except:
                                pass
                        prices['WTI'] = {'value': value, 'change': change}
        except:
            pass
        
        # 다른 유가 (Brent, Dubai)
        for code, name in [('OIL_BRT', 'Brent'), ('OIL_DU', 'Dubai')]:
            try:
                url2 = f'https://finance.naver.com/marketindex/worldDailyQuote.naver?marketindexCd={code}&fdtc=2'
                response2 = requests.get(url2, headers=headers, timeout=10)
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                table2 = soup2.find('table', class_='tbl_exchange')
                if table2:
                    rows2 = table2.find_all('tr')
                    if len(rows2) > 1:
                        cells2 = rows2[1].find_all('td')
                        if len(cells2) >= 2:
                            value2 = float(cells2[1].get_text(strip=True).replace(',', ''))
                            change2 = 0
                            if len(cells2) >= 3:
                                try:
                                    change2 = float(cells2[2].get_text(strip=True).replace(',', ''))
                                except:
                                    pass
                            prices[name] = {'value': value2, 'change': change2}
            except:
                continue
        
        return prices if prices else None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rec_prices():
    """REC 가격 크롤링 - 실제 데이터만"""
    try:
        # 전력거래소 REC 가격 페이지
        url = 'https://onerec.kmos.kr/portal/rec/selectRecPriceList.do'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 테이블에서 가격 추출 시도
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        text = cells[0].get_text(strip=True)
                        if '육지' in text or '가격' in text:
                            try:
                                value = float(cells[1].get_text(strip=True).replace(',', ''))
                                return {'mainland': {'price': value, 'change': 0}, 
                                        'jeju': {'price': value * 0.9, 'change': 0}}
                            except:
                                continue
        return None
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_interest_rates():
    """금리 정보 크롤링 - 실제 데이터만"""
    try:
        # 한국은행 기준금리
        url = 'https://finance.naver.com/marketindex/interestDailyQuote.naver?marketindexCd=IRR_CALL'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rates = {}
        
        try:
            table = soup.find('table', class_='tbl_exchange')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    cells = rows[1].find_all('td')
                    if len(cells) >= 2:
                        value = float(cells[1].get_text(strip=True).replace(',', ''))
                        rates['call'] = {'value': value, 'change': 0}
        except:
            pass
        
        # 국고채 금리
        for code, name in [('IRR_GOVT03Y', 'treasury_3y'), ('IRR_GOVT10Y', 'treasury_10y')]:
            try:
                url2 = f'https://finance.naver.com/marketindex/interestDailyQuote.naver?marketindexCd={code}'
                response2 = requests.get(url2, headers=headers, timeout=10)
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                table2 = soup2.find('table', class_='tbl_exchange')
                if table2:
                    rows2 = table2.find_all('tr')
                    if len(rows2) > 1:
                        cells2 = rows2[1].find_all('td')
                        if len(cells2) >= 2:
                            value2 = float(cells2[1].get_text(strip=True).replace(',', ''))
                            rates[name] = {'value': value2, 'change': 0}
            except:
                continue
        
        return rates if rates else None
    except:
        return None

# =============================================================================
# 인코딩 헬퍼 함수 (IPO용)
# =============================================================================
def fetch_with_encoding(url, timeout=15):
    """올바른 인코딩으로 HTML 가져오기"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        content_bytes = response.content
        
        for encoding in ['euc-kr', 'cp949', 'utf-8']:
            try:
                decoded = content_bytes.decode(encoding)
                if '공모' in decoded or '청약' in decoded or '상장' in decoded or '예측' in decoded:
                    return decoded
            except:
                continue
        return content_bytes.decode('euc-kr', errors='replace')
    except:
        return None

# =============================================================================
# IPO 크롤링 함수들 (v2.4 동일)
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_subscription_schedule():
    """IPOStock 공모청약일정 스크래핑 (ipo04.asp)"""
    try:
        content = fetch_with_encoding('http://www.ipostock.co.kr/sub03/ipo04.asp')
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 10:
                try:
                    date_cell = cells[1].get_text(strip=True)
                    if not date_cell or '~' not in date_cell:
                        continue
                    
                    company_cell = cells[2]
                    company_link = company_cell.find('a')
                    company_name = company_link.get_text(strip=True) if company_link else company_cell.get_text(strip=True)
                    
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    results.append({
                        'company': company_name,
                        'subscription_date': date_cell,
                        'hope_price': cells[3].get_text(strip=True),
                        'offer_price': cells[4].get_text(strip=True),
                        'offer_amount': cells[5].get_text(strip=True),
                        'refund_date': cells[6].get_text(strip=True),
                        'listing_date': cells[7].get_text(strip=True) if len(cells) > 7 else '-',
                        'competition': cells[8].get_text(strip=True) if len(cells) > 8 else '-',
                        'underwriter': cells[9].get_text(strip=True) if len(cells) > 9 else '-'
                    })
                except:
                    continue
        return results
    except:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_forecast_schedule():
    """IPOStock 수요예측일정 스크래핑 (ipo02.asp)"""
    try:
        content = fetch_with_encoding('http://www.ipostock.co.kr/sub03/ipo02.asp')
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                try:
                    date_cell = cells[1].get_text(strip=True)
                    if not date_cell or '~' not in date_cell:
                        continue
                    
                    company_cell = cells[2]
                    company_link = company_cell.find('a')
                    company_name = company_link.get_text(strip=True) if company_link else company_cell.get_text(strip=True)
                    
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    results.append({
                        'company': company_name,
                        'forecast_date': date_cell,
                        'hope_price': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                        'underwriter': cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    })
                except:
                    continue
        return results
    except:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_calendar(year, month):
    """IPOStock IPO캘린더 스크래핑 (ipo06.asp)"""
    try:
        url = f'http://www.ipostock.co.kr/sub03/ipo06.asp?thisYear={year}&thisMonth={month}'
        content = fetch_with_encoding(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        events = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            if '/view_pg/view_04.asp' in href:
                title = link.get('title', '') or link.get_text(strip=True)
                if title and len(title) > 1:
                    events.append({
                        'company': title,
                        'month': month,
                        'year': year
                    })
        
        # 중복 제거
        seen = set()
        unique_events = []
        for e in events:
            if e['company'] not in seen:
                seen.add(e['company'])
                unique_events.append(e)
        
        return unique_events
    except:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_approval_list():
    """IPOStock 예비심사승인 목록 스크래핑 (exa03.asp)"""
    try:
        content = fetch_with_encoding('http://www.ipostock.co.kr/sub02/exa03.asp')
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                try:
                    approval_date = cells[0].get_text(strip=True)
                    if not approval_date or '/' not in approval_date:
                        continue
                    
                    company_cell = cells[1]
                    company_link = company_cell.find('a')
                    company_name = company_link.get_text(strip=True) if company_link else company_cell.get_text(strip=True)
                    
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    results.append({
                        'approval_date': approval_date,
                        'company': company_name,
                        'request_date': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'underwriter': cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    })
                except:
                    continue
        return results
    except:
        return []

# =============================================================================
# DART API 함수들 (LP 발굴용)
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def get_corp_code_list():
    """상장기업 코드 목록"""
    try:
        url = f'{DART_BASE_URL}/corpCode.xml'
        params = {'crtfc_key': DART_API_KEY}
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                xml_data = z.read('CORPCODE.xml')
            
            root = ET.fromstring(xml_data)
            corp_list = []
            
            for corp in root.findall('list'):
                corp_code = corp.find('corp_code').text
                corp_name = corp.find('corp_name').text
                stock_code_elem = corp.find('stock_code')
                stock_code = stock_code_elem.text if stock_code_elem is not None else None
                
                if stock_code and stock_code.strip():
                    corp_list.append({
                        'corp_code': corp_code,
                        'corp_name': corp_name,
                        'stock_code': stock_code.strip()
                    })
            
            return pd.DataFrame(corp_list)
        return None
    except:
        return None

def get_financial_statement(corp_code, bsns_year, reprt_code='11011'):
    """재무제표 조회"""
    try:
        url = f'{DART_BASE_URL}/fnlttSinglAcntAll.json'
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': 'CFS'
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '000':
                return pd.DataFrame(data.get('list', []))
        return None
    except:
        return None

def extract_financial_data(df):
    """재무데이터 추출"""
    result = {'retained_earnings': None, 'total_equity': None, 'revenue': None}
    
    if df is None or df.empty:
        return result
    
    for kw in ['이익잉여금', '이익(손실)잉여금']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['retained_earnings'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    for kw in ['자본총계', '자본 총계']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['total_equity'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    for kw in ['매출액', '수익(매출액)', '영업수익']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['revenue'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    return result

def fetch_single_company(corp_code, corp_name, stock_code, bsns_year):
    """단일 기업 조회"""
    fs_df = get_financial_statement(corp_code, bsns_year)
    fin_data = extract_financial_data(fs_df)
    
    if fin_data['retained_earnings'] is not None:
        return {
            'corp_code': corp_code,
            'corp_name': corp_name,
            'stock_code': stock_code,
            **fin_data
        }
    return None

def calculate_lp_score(df):
    """LP 스코어 계산"""
    df = df.copy()
    if len(df) == 0:
        return df
    
    if df['retained_earnings'].max() > df['retained_earnings'].min():
        df['re_score'] = (df['retained_earnings'] - df['retained_earnings'].min()) / \
                         (df['retained_earnings'].max() - df['retained_earnings'].min()) * 100
    else:
        df['re_score'] = 50
    
    df['total_equity'] = df['total_equity'].fillna(0)
    if df['total_equity'].max() > df['total_equity'].min():
        df['equity_score'] = (df['total_equity'] - df['total_equity'].min()) / \
                             (df['total_equity'].max() - df['total_equity'].min()) * 100
    else:
        df['equity_score'] = 50
    
    df['lp_score'] = df['re_score'] * 0.7 + df['equity_score'] * 0.3
    return df.sort_values('lp_score', ascending=False)

# =============================================================================
# ESG 검색
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def search_esg_disclosures(keyword, start_date, end_date, max_results=30):
    """ESG 키워드 검색"""
    try:
        url = 'https://dart.fss.or.kr/dsab007/search.ax'
        results = []
        
        response = requests.post(url, data={
            "currentPage": "1",
            "keyword": keyword,
            "dspType": "A",
            "maxResults": "50",
            "startDate": start_date,
            "endDate": end_date
        }, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for row in soup.find_all('tr'):
                try:
                    company_tag = row.find('a', class_='company')
                    if company_tag:
                        results.append({
                            'company': company_tag.text.strip(),
                            'report': row.find('a', class_='second').text.strip() if row.find('a', class_='second') else '',
                            'date': row.find('td', class_='date').text.strip() if row.find('td', class_='date') else '',
                            'keyword': keyword
                        })
                except:
                    continue
        
        return pd.DataFrame(results[:max_results]) if results else pd.DataFrame()
    except:
        return pd.DataFrame()

# =============================================================================
# 포트폴리오 데이터 정의
# =============================================================================
def get_default_fund_data():
    """기본 펀드 정보"""
    return [
        {
            'id': 'fund_001',
            'name': '미래환경펀드',
            'full_name': '환경부 모태펀드 출자 미래환경펀드',
            'aum': 775.0,
            'gp': ['현대차증권', 'IFAM'],
            'lp': '환경부 모태펀드',
            'vintage': 2023,
            'investment_period': '2023-2028',
            'fund_life': '2023-2033',
            'status': 'active',
        },
        {
            'id': 'fund_002',
            'name': 'IPO 일반사모 1호',
            'full_name': '인프라프론티어 IPO 일반사모투자신탁 제1호',
            'aum': 84.5,
            'gp': ['IFAM'],
            'lp': '일반투자자',
            'vintage': 2024,
            'investment_period': '2024-2026',
            'fund_life': '2024-2029',
            'status': 'active',
        }
    ]

def get_default_portfolio_data():
    """기본 포트폴리오 투자 현황"""
    return [
        {'id': 1, 'company': '에코솔루션', 'sector': '환경/폐기물', 'fund': '미래환경펀드', 'account': '펀드', 
         'investment_type': 'RCPS', 'investment_date': '2023-06-15', 'amount': 30.0, 'current_value': 30.0,
         'shares': 30000, 'price_per_share': 10000, 'valuation': 150.0, 'ownership': 20.0, 'status': 'active',
         'milestone': 'Series B 준비중', 'next_event': '2025 Q2 Series B'},
        {'id': 2, 'company': '그린테크', 'sector': '신재생에너지', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2023-08-20', 'amount': 25.0, 'current_value': 25.0,
         'shares': 25000, 'price_per_share': 10000, 'valuation': 180.0, 'ownership': 13.9, 'status': 'active',
         'milestone': '매출 성장 중', 'next_event': '2025 Q3 IPO 추진'},
        {'id': 3, 'company': '클린워터', 'sector': '수처리', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'CB', 'investment_date': '2023-09-10', 'amount': 20.0, 'current_value': 20.0,
         'shares': 0, 'price_per_share': 0, 'valuation': 120.0, 'ownership': 0, 'status': 'active',
         'milestone': '전환권 보유', 'next_event': '2025 Q4 전환 검토', 'coupon': 3.0, 'conversion_price': 8000},
        {'id': 4, 'company': '바이오매스에너지', 'sector': '신재생에너지', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2023-11-05', 'amount': 35.0, 'current_value': 35.0,
         'shares': 35000, 'price_per_share': 10000, 'valuation': 200.0, 'ownership': 17.5, 'status': 'active',
         'milestone': '발전소 가동 개시', 'next_event': '2025 Q1 BEP 달성'},
        {'id': 5, 'company': '스마트그리드', 'sector': '에너지IT', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-01-20', 'amount': 40.0, 'current_value': 40.0,
         'shares': 40000, 'price_per_share': 10000, 'valuation': 250.0, 'ownership': 16.0, 'status': 'active',
         'milestone': '대기업 계약 체결', 'next_event': '2025 Q2 해외 진출'},
        {'id': 6, 'company': '카본캡처', 'sector': 'CCUS', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-03-15', 'amount': 28.0, 'current_value': 28.0,
         'shares': 28000, 'price_per_share': 10000, 'valuation': 140.0, 'ownership': 20.0, 'status': 'active',
         'milestone': '파일럿 플랜트 완공', 'next_event': '2025 Q3 상용화'},
        {'id': 7, 'company': '순환자원', 'sector': '자원순환', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'CB', 'investment_date': '2024-04-10', 'amount': 22.0, 'current_value': 22.0,
         'shares': 0, 'price_per_share': 0, 'valuation': 100.0, 'ownership': 0, 'status': 'active',
         'milestone': '신규 시설 증설', 'next_event': '2025 Q2 증설 완료', 'coupon': 2.5, 'conversion_price': 12000},
        {'id': 8, 'company': 'ESG테크', 'sector': 'ESG/SaaS', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': '보통주', 'investment_date': '2024-05-25', 'amount': 15.0, 'current_value': 15.0,
         'shares': 15000, 'price_per_share': 10000, 'valuation': 80.0, 'ownership': 18.75, 'status': 'active',
         'milestone': 'MRR 10억 달성', 'next_event': '2025 Q3 Series A'},
        {'id': 9, 'company': '수소에너지', 'sector': '수소', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-07-10', 'amount': 45.0, 'current_value': 45.0,
         'shares': 45000, 'price_per_share': 10000, 'valuation': 300.0, 'ownership': 15.0, 'status': 'active',
         'milestone': '충전소 10개 운영', 'next_event': '2025 Q4 전국 확대'},
        {'id': 10, 'company': '태양광플러스', 'sector': '태양광', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-08-20', 'amount': 32.0, 'current_value': 32.0,
         'shares': 32000, 'price_per_share': 10000, 'valuation': 160.0, 'ownership': 20.0, 'status': 'active',
         'milestone': '100MW 발전 운영', 'next_event': '2025 Q2 ESS 연계'},
        {'id': 11, 'company': '풍력발전', 'sector': '풍력', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-09-15', 'amount': 38.0, 'current_value': 38.0,
         'shares': 38000, 'price_per_share': 10000, 'valuation': 220.0, 'ownership': 17.27, 'status': 'active',
         'milestone': '해상풍력 인허가', 'next_event': '2026 Q1 착공'},
        {'id': 12, 'company': '폐배터리리사이클', 'sector': '배터리재활용', 'fund': '미래환경펀드', 'account': '펀드',
         'investment_type': 'RCPS', 'investment_date': '2024-10-30', 'amount': 30.18, 'current_value': 30.18,
         'shares': 30180, 'price_per_share': 10000, 'valuation': 180.0, 'ownership': 16.77, 'status': 'active',
         'milestone': '처리용량 확대', 'next_event': '2025 Q3 EU 수출'},
    ]

def get_fund_data():
    return st.session_state.fund_data

def get_portfolio_data():
    return st.session_state.portfolio_data

def add_portfolio_item(item):
    max_id = max([p['id'] for p in st.session_state.portfolio_data], default=0)
    item['id'] = max_id + 1
    st.session_state.portfolio_data.append(item)
    return item['id']

def update_portfolio_item(item_id, updates):
    for i, p in enumerate(st.session_state.portfolio_data):
        if p['id'] == item_id:
            st.session_state.portfolio_data[i].update(updates)
            return True
    return False

def delete_portfolio_item(item_id):
    st.session_state.portfolio_data = [p for p in st.session_state.portfolio_data if p['id'] != item_id]

def get_sector_allocation():
    portfolio = get_portfolio_data()
    sector_data = {}
    for p in portfolio:
        if p['amount'] > 0:
            sector = p['sector']
            if sector not in sector_data:
                sector_data[sector] = {'amount': 0, 'count': 0, 'companies': []}
            sector_data[sector]['amount'] += p['amount']
            sector_data[sector]['count'] += 1
            sector_data[sector]['companies'].append(p['company'])
    return sector_data

def get_investment_type_allocation():
    portfolio = get_portfolio_data()
    type_data = {}
    for p in portfolio:
        if p['amount'] > 0:
            inv_type = p['investment_type']
            if inv_type not in type_data:
                type_data[inv_type] = {'amount': 0, 'count': 0}
            type_data[inv_type]['amount'] += p['amount']
            type_data[inv_type]['count'] += 1
    return type_data

# =============================================================================
# VC Analyzer 함수들
# =============================================================================
def calculate_rvps(rounds: List[InvestmentRound], founder_shares: float) -> List[dict]:
    total_shares = founder_shares + sum(r.shares for r in rounds)
    results = []
    
    for r in rounds:
        if r.shares > 0:
            rvps = (r.investment * r.liquidation_multiple) / r.shares
        else:
            rvps = 0
        results.append({
            'name': r.name, 'investment': r.investment, 'shares': r.shares,
            'ownership': r.shares / total_shares * 100 if total_shares > 0 else 0,
            'rvps': rvps, 'participating': r.is_participating,
            'liq_multiple': r.liquidation_multiple, 'seniority': r.seniority
        })
    
    results.append({
        'name': '창업자', 'investment': 0, 'shares': founder_shares,
        'ownership': founder_shares / total_shares * 100 if total_shares > 0 else 0,
        'rvps': 0, 'participating': False, 'liq_multiple': 0, 'seniority': 999
    })
    
    return sorted(results, key=lambda x: (-x['rvps'], x['seniority']))

def calculate_exit_payoffs(rounds: List[InvestmentRound], founder_shares: float, exit_values: np.ndarray) -> Dict[str, np.ndarray]:
    rvps_data = calculate_rvps(rounds, founder_shares)
    total_shares = founder_shares + sum(r.shares for r in rounds)
    
    payoffs = {d['name']: np.zeros_like(exit_values, dtype=float) for d in rvps_data}
    
    for exit_val in exit_values:
        remaining = exit_val
        idx = list(exit_values).index(exit_val)
        
        sorted_rounds = sorted([d for d in rvps_data if d['name'] != '창업자'], 
                               key=lambda x: (-x['seniority'], -x['rvps']))
        
        for d in sorted_rounds:
            liq_pref = d['investment'] * d['liq_multiple']
            
            if d['participating']:
                payout = min(liq_pref, remaining)
                remaining -= payout
                payoffs[d['name']][idx] = payout
            else:
                convert_val = (d['shares'] / total_shares) * exit_val if total_shares > 0 else 0
                if convert_val > liq_pref:
                    payoffs[d['name']][idx] = convert_val
                else:
                    payout = min(liq_pref, remaining)
                    remaining -= payout
                    payoffs[d['name']][idx] = payout
        
        if remaining > 0:
            participating_rounds = [d for d in rvps_data if d['participating'] and d['name'] != '창업자']
            total_participating_shares = sum(d['shares'] for d in participating_rounds) + founder_shares
            
            for d in participating_rounds:
                additional = (d['shares'] / total_participating_shares) * remaining if total_participating_shares > 0 else 0
                payoffs[d['name']][idx] += additional
            
            founder_add = (founder_shares / total_participating_shares) * remaining if total_participating_shares > 0 else remaining
            payoffs['창업자'][idx] = founder_add
    
    return payoffs

def calculate_lp_cost(fund: FundInfo, investment: float) -> float:
    lifetime_fees = fund.committed_capital * (fund.management_fee_rate / 100) * 10
    investable = fund.committed_capital - lifetime_fees
    return (fund.committed_capital / investable) * investment if investable > 0 else investment

def calculate_gp_lp_split(partial_val: float, fund: FundInfo, investment: float):
    lp_cost = calculate_lp_cost(fund, investment)
    profit = max(0, partial_val - investment)
    hurdle_amount = investment * (fund.hurdle_rate / 100) * 5
    
    if profit > hurdle_amount:
        gp_carry = (profit - hurdle_amount) * (fund.carried_interest / 100)
    else:
        gp_carry = 0
    
    lp_val = partial_val - gp_carry
    return {
        'lp_cost': lp_cost, 'partial_val': partial_val, 'profit': profit,
        'hurdle': hurdle_amount, 'gp_carry': gp_carry, 'lp_val': lp_val,
        'lp_multiple': lp_val / lp_cost if lp_cost > 0 else 0,
        'gp_multiple': (gp_carry + investment) / investment if investment > 0 else 0
    }
# =============================================================================
# 렌더링 함수들
# =============================================================================
def render_header():
    st.markdown(f"""
    <div class="main-header">
        <div class="header-brand">
            <span class="header-logo">🏛️</span>
            <span class="header-title">IFAM 통합 대시보드</span>
        </div>
        <div class="header-subtitle">Infra Frontier Asset Management - 인프라프론티어자산운용(주)</div>
        <div class="header-meta">
            <span class="header-meta-item">📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}</span>
            <span class="header-meta-item">🔄 실시간 크롤링</span>
            <span class="header-meta-item">📊 v1.2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_home():
    st.markdown('<p class="section-title"><span class="icon">🏠</span> 대시보드 홈</p>', unsafe_allow_html=True)
    
    funds = get_fund_data()
    portfolio = get_portfolio_data()
    total_aum = sum(f['aum'] for f in funds)
    total_invested = sum(p['amount'] for p in portfolio)
    total_investments = len([p for p in portfolio if p['amount'] > 0])
    fund_count = len([p for p in portfolio if p['account'] == '펀드' and p['amount'] > 0])
    
    st.markdown("### 📊 IFAM 운용 현황")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-indigo);"><div class="metric-label">총 AUM</div><div class="metric-value large">{total_aum:,.1f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {len(funds)}개 운용</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-emerald);"><div class="metric-label">투자집행</div><div class="metric-value large">{total_invested:,.2f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">집행률 {total_invested/total_aum*100:.1f}%</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-amber);"><div class="metric-label">투자건수</div><div class="metric-value large">{total_investments}건</div><div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {fund_count}건</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-violet);"><div class="metric-label">미회수자산</div><div class="metric-value large">{total_invested:,.2f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">MOIC 1.0x</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🧭 바로가기")
    col1, col2, col3, col4 = st.columns(4)
    nav_items = [("🌱", "Daily Market", "친환경·인프라 지표"), ("📊", "VC Analyzer", "Term Sheet 분석"), ("🏢", "LP & IPO", "LP 발굴 & IPO"), ("📈", "Portfolio", "통합 포트폴리오")]
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], nav_items):
        with col:
            st.markdown(f'<div class="nav-card"><div class="nav-card-icon">{icon}</div><div class="nav-card-title">{title}</div><div class="nav-card-desc">{desc}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<p class="section-title"><span class="icon">📊</span> 오늘의 주요 지표</p>', unsafe_allow_html=True)
    
    exchange_rates = fetch_exchange_rates()
    oil_prices = fetch_oil_prices()
    interest_rates = fetch_interest_rates()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if exchange_rates and 'USD' in exchange_rates:
        usd = exchange_rates['USD']
        cls, arrow = get_change_class(usd['change'])
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">USD/KRW</div><div class="metric-value">{usd["value"]:,.2f}</div><div class="metric-change {cls}">{arrow} {abs(usd["change"]):.2f}</div></div>', unsafe_allow_html=True)
    else:
        with col1:
            st.markdown('<div class="metric-card"><div class="metric-label">USD/KRW</div><div class="metric-value">-</div><div style="color: var(--text-muted); font-size: 0.75rem;">로딩 중...</div></div>', unsafe_allow_html=True)
    
    if oil_prices and 'WTI' in oil_prices:
        wti = oil_prices['WTI']
        cls, arrow = get_change_class(wti['change'])
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">WTI 유가</div><div class="metric-value">${wti["value"]:.2f}</div><div class="metric-change {cls}">{arrow} ${abs(wti["change"]):.2f}</div></div>', unsafe_allow_html=True)
    else:
        with col2:
            st.markdown('<div class="metric-card"><div class="metric-label">WTI 유가</div><div class="metric-value">-</div><div style="color: var(--text-muted); font-size: 0.75rem;">로딩 중...</div></div>', unsafe_allow_html=True)
    
    if interest_rates and 'treasury_3y' in interest_rates:
        treasury = interest_rates['treasury_3y']
        cls, arrow = get_change_class(treasury['change'])
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">국고채 3년</div><div class="metric-value">{treasury["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(treasury["change"]):.2f}%p</div></div>', unsafe_allow_html=True)
    else:
        with col3:
            st.markdown('<div class="metric-card"><div class="metric-label">국고채 3년</div><div class="metric-value">-</div><div style="color: var(--text-muted); font-size: 0.75rem;">로딩 중...</div></div>', unsafe_allow_html=True)
    
    if interest_rates and 'call' in interest_rates:
        call = interest_rates['call']
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">콜금리</div><div class="metric-value">{call["value"]:.2f}%</div></div>', unsafe_allow_html=True)
    else:
        with col4:
            st.markdown('<div class="metric-card"><div class="metric-label">콜금리</div><div class="metric-value">-</div><div style="color: var(--text-muted); font-size: 0.75rem;">로딩 중...</div></div>', unsafe_allow_html=True)

def render_daily_market():
    st.markdown('<p class="section-title"><span class="icon">🌱</span> Daily Market - 친환경·인프라 지표</p>', unsafe_allow_html=True)
    st.caption("⚠️ 모든 데이터는 실시간 크롤링 결과입니다. 크롤링 실패 시 '-'로 표시됩니다.")
    
    # 환율
    st.markdown("#### 💱 환율")
    exchange_rates = fetch_exchange_rates()
    if exchange_rates:
        cols = st.columns(4)
        for i, code in enumerate(['USD', 'JPY', 'EUR', 'CNY']):
            if code in exchange_rates:
                data = exchange_rates[code]
                cls, arrow = get_change_class(data['change'])
                with cols[i]:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">{data.get("name", code)}</div><div class="metric-value">{data["value"]:,.2f}</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}</div></div>', unsafe_allow_html=True)
            else:
                with cols[i]:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">{code}</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
    else:
        st.warning("환율 데이터를 불러올 수 없습니다.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛢️ 국제유가")
        oil_prices = fetch_oil_prices()
        if oil_prices:
            cols = st.columns(3)
            for i, (code, name) in enumerate([('WTI', '서부텍사스'), ('Brent', '북해 브렌트'), ('Dubai', '두바이')]):
                if code in oil_prices:
                    data = oil_prices[code]
                    cls, arrow = get_change_class(data['change'])
                    with cols[i]:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">${data["value"]:.2f}</div><div class="metric-change {cls}">{arrow} ${abs(data["change"]):.2f}</div></div>', unsafe_allow_html=True)
                else:
                    with cols[i]:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
        else:
            st.info("유가 데이터를 불러올 수 없습니다.")
    
    with col2:
        st.markdown("#### 📊 금리")
        interest_rates = fetch_interest_rates()
        if interest_rates:
            cols = st.columns(3)
            rate_items = [('call', '콜금리'), ('treasury_3y', '국고채 3년'), ('treasury_10y', '국고채 10년')]
            for i, (key, label) in enumerate(rate_items):
                if key in interest_rates:
                    data = interest_rates[key]
                    with cols[i]:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{data["value"]:.2f}%</div></div>', unsafe_allow_html=True)
                else:
                    with cols[i]:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
        else:
            st.info("금리 데이터를 불러올 수 없습니다.")
    
    st.markdown("---")
    st.markdown("#### ⚡ 신재생에너지 (REC/SMP)")
    
    rec_data = fetch_rec_prices()
    if rec_data:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### REC")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">육지 REC</div><div class="metric-value">{rec_data["mainland"]["price"]:,.0f}원</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><div class="metric-label">제주 REC</div><div class="metric-value">{rec_data["jeju"]["price"]:,.0f}원</div></div>', unsafe_allow_html=True)
    else:
        st.info("REC 가격은 전력거래소(onerec.kmos.kr)에서 확인하세요.")
    
    st.markdown("""
    <div class="info-box">
        <p><strong>📌 참고</strong><br>
        • REC/SMP 가격: <a href="https://onerec.kmos.kr" target="_blank">전력거래소 원REC</a><br>
        • LNG 가격: <a href="https://www.kogas.or.kr" target="_blank">한국가스공사</a><br>
        • 금리스왑: <a href="https://www.kofiabond.or.kr" target="_blank">금융투자협회</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_vc_analyzer():
    st.markdown('<p class="section-title"><span class="icon">📊</span> VC Term Sheet Analyzer</p>', unsafe_allow_html=True)
    
    if 'vc_rounds' not in st.session_state:
        st.session_state.vc_rounds = [InvestmentRound("Series A", 30.0, 15.0, True, 1.0, 1), InvestmentRound("Series B", 80.0, 20.0, True, 1.0, 2)]
    if 'vc_global' not in st.session_state:
        st.session_state.vc_global = GlobalInput()
    if 'vc_fund' not in st.session_state:
        st.session_state.vc_fund = FundInfo()
    
    with st.sidebar:
        st.markdown("### 📝 투자 조건")
        st.markdown("#### 👤 창업자")
        founder_shares = st.number_input("보통주 (만주)", 1.0, 1000.0, float(st.session_state.vc_global.founder_shares), 10.0)
        st.session_state.vc_global.founder_shares = founder_shares
        
        st.markdown("#### 💰 기업가치")
        st.session_state.vc_global.current_valuation = st.number_input("현재 가치 (억)", 10.0, 10000.0, float(st.session_state.vc_global.current_valuation), 10.0)
        st.session_state.vc_global.exit_valuation = st.number_input("Exit 가치 (억)", 50.0, 50000.0, float(st.session_state.vc_global.exit_valuation), 50.0)
        
        st.markdown("#### 📈 옵션")
        st.session_state.vc_global.volatility = st.slider("변동성 (%)", 30, 150, int(st.session_state.vc_global.volatility))
        st.session_state.vc_global.risk_free_rate = st.slider("무위험이자율 (%)", 1.0, 10.0, st.session_state.vc_global.risk_free_rate, 0.5)
        st.session_state.vc_global.holding_period = st.slider("보유기간 (년)", 1, 10, int(st.session_state.vc_global.holding_period))
        
        st.markdown("#### 🏦 펀드")
        st.session_state.vc_fund.committed_capital = st.number_input("약정총액 (억)", 100.0, 10000.0, float(st.session_state.vc_fund.committed_capital), 100.0)
        st.session_state.vc_fund.management_fee_rate = st.number_input("관리보수 (%)", 1.0, 3.0, float(st.session_state.vc_fund.management_fee_rate), 0.1)
        st.session_state.vc_fund.carried_interest = st.number_input("성과보수 (%)", 10.0, 30.0, float(st.session_state.vc_fund.carried_interest), 1.0)
        st.session_state.vc_fund.hurdle_rate = st.number_input("허들레이트 (%)", 0.0, 15.0, float(st.session_state.vc_fund.hurdle_rate), 1.0)
    
    st.markdown("### 💼 투자 라운드")
    num_rounds = st.number_input("라운드 수", 1, 6, len(st.session_state.vc_rounds))
    
    while len(st.session_state.vc_rounds) < num_rounds:
        idx = len(st.session_state.vc_rounds)
        st.session_state.vc_rounds.append(InvestmentRound(f"Series {chr(65+idx)}", 50.0, 10.0, True, 1.0, idx+1))
    while len(st.session_state.vc_rounds) > num_rounds:
        st.session_state.vc_rounds.pop()
    
    cols = st.columns(min(num_rounds, 3))
    for i, r in enumerate(st.session_state.vc_rounds):
        with cols[i % 3]:
            with st.expander(f"📌 {r.name}", expanded=True):
                r.investment = st.number_input("투자금액 (억)", 1.0, 1000.0, float(r.investment), 10.0, key=f"inv_{i}")
                r.shares = st.number_input("배정주식 (만주)", 1.0, 500.0, float(r.shares), 5.0, key=f"shares_{i}")
                r.is_participating = st.checkbox("참가 우선주", value=r.is_participating, key=f"part_{i}")
                r.liquidation_multiple = st.selectbox("청산배수", [1.0, 1.5, 2.0, 3.0], index=[1.0, 1.5, 2.0, 3.0].index(r.liquidation_multiple), key=f"liq_{i}")
    
    st.markdown("---")
    st.markdown("### 📊 RVPS 분석")
    
    rvps_data = calculate_rvps(st.session_state.vc_rounds, st.session_state.vc_global.founder_shares)
    df_rvps = pd.DataFrame(rvps_data)
    df_rvps['투자금액'] = df_rvps['investment'].apply(lambda x: f"{x:,.0f}억")
    df_rvps['지분율'] = df_rvps['ownership'].apply(lambda x: f"{x:.1f}%")
    df_rvps['RVPS'] = df_rvps['rvps'].apply(lambda x: f"{x:,.2f}억/만주")
    df_rvps['유형'] = df_rvps['participating'].apply(lambda x: '참가' if x else '비참가')
    st.dataframe(df_rvps[['name', '투자금액', '지분율', 'RVPS', '유형']].rename(columns={'name': '라운드'}), use_container_width=True, hide_index=True)
    
    st.markdown("### 📈 Exit Diagram")
    exit_values = np.linspace(0, st.session_state.vc_global.exit_valuation * 1.5, 100)
    payoffs = calculate_exit_payoffs(st.session_state.vc_rounds, st.session_state.vc_global.founder_shares, exit_values)
    
    fig = go.Figure()
    colors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#10b981']
    for i, (name, values) in enumerate(payoffs.items()):
        fig.add_trace(go.Scatter(x=exit_values, y=values, name=name, mode='lines', line=dict(width=2, color=colors[i % len(colors)])))
    fig.update_layout(title='Exit Value별 수익 분배', xaxis_title='Exit Value (억원)', yaxis_title='수익 (억원)', template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02))
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 💰 GP/LP 수익 분배")
    total_investment = sum(r.investment for r in st.session_state.vc_rounds)
    total_shares = st.session_state.vc_global.founder_shares + sum(r.shares for r in st.session_state.vc_rounds)
    inv_shares = sum(r.shares for r in st.session_state.vc_rounds)
    partial_val = st.session_state.vc_global.exit_valuation * (inv_shares / total_shares) if total_shares > 0 else 0
    split = calculate_gp_lp_split(partial_val, st.session_state.vc_fund, total_investment)
    
    col1, col2, col3, col4 = st.columns(4)
    metrics = [("LP 투자비용", f"{split['lp_cost']:.1f}억"), ("GP Carry", f"{split['gp_carry']:.1f}억"), ("LP 수령액", f"{split['lp_val']:.1f}억"), ("LP Multiple", f"{split['lp_multiple']:.2f}x")]
    for col, (label, value) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
def render_lp_discovery():
    """LP & IPO 모니터링 (v2.4 동일 구조)"""
    st.markdown('<p class="section-title"><span class="icon">🏢</span> LP & IPO 모니터링</p>', unsafe_allow_html=True)
    
    # 사이드바에서 설정 가져오기
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 상단 설정
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ipo_year = st.selectbox("📅 연도", list(range(current_year-1, current_year+3)), 
                                index=list(range(current_year-1, current_year+3)).index(current_year))
    with col2:
        ipo_month = st.selectbox("📅 월", list(range(1, 13)), index=current_month - 1)
    with col3:
        bsns_year = st.selectbox("📊 사업연도", ['2024', '2023', '2022'], index=0)
    with col4:
        min_re = st.number_input("최소 이익잉여금", 0, 10000, 300, 100)
    
    batch_size = 50  # 고정
    
    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📅 IPO 일정", "🔍 LP 발굴", "🌱 ESG 모니터링", "📋 데이터"])
    
    # =========================================================================
    # TAB 1: IPO 일정 (v2.4 동일)
    # =========================================================================
    with tab1:
        st.markdown("## 📅 IPO 일정")
        st.caption(f"📖 데이터: IPOStock | 조회: {ipo_year}년 {ipo_month}월")
        
        # 데이터 로드
        with st.spinner("IPO 일정 불러오는 중..."):
            subscription_data = fetch_ipo_subscription_schedule()
            forecast_data = fetch_ipo_forecast_schedule()
            calendar_data = fetch_ipo_calendar(ipo_year, ipo_month)
            approval_data = fetch_ipo_approval_list()
        
        # 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">청약 일정</div><div class="metric-value" style="color:#f43f5e">{len(subscription_data)}건</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">수요예측</div><div class="metric-value" style="color:#8b5cf6">{len(forecast_data)}건</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{ipo_month}월 일정</div><div class="metric-value" style="color:#0ea5e9">{len(calendar_data)}건</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">승인 종목</div><div class="metric-value" style="color:#f59e0b">{len(approval_data)}건</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 서브탭
        sub1, sub2, sub3, sub4 = st.tabs(["📝 청약 일정", "🎯 수요예측", f"📆 {ipo_month}월 캘린더", "✅ 승인 종목"])
        
        # 청약 일정
        with sub1:
            st.markdown("### 📝 공모주 청약 일정")
            
            if subscription_data:
                for item in subscription_data[:20]:
                    competition = item.get('competition', '-')
                    is_ongoing = competition == '-' or '진행' in str(competition)
                    badge_class = 'rose' if is_ongoing else 'emerald'
                    badge_text = '청약중' if is_ongoing else '완료'
                    
                    st.markdown(f'''<div class="ipo-card">
                        <div class="ipo-name"><span class="badge badge-{badge_class}">{badge_text}</span> {item['company']}</div>
                        <div class="ipo-detail">
                            📅 청약일: <span class="ipo-date">{item['subscription_date']}</span><br>
                            💰 공모가: <span class="ipo-price">{item['offer_price']}</span> (희망: {item['hope_price']})<br>
                            📊 공모금액: {item['offer_amount']} | 경쟁률: {competition}<br>
                            🏢 주간사: {item['underwriter']} | 상장일: {item['listing_date']}
                        </div>
                    </div>''', unsafe_allow_html=True)
            else:
                st.info("청약 일정을 불러오는 중... 잠시 후 새로고침 해주세요.")
        
        # 수요예측
        with sub2:
            st.markdown("### 🎯 수요예측 일정")
            
            if forecast_data:
                for item in forecast_data[:15]:
                    st.markdown(f'''<div class="ipo-card">
                        <div class="ipo-name"><span class="badge badge-violet">수요예측</span> {item['company']}</div>
                        <div class="ipo-detail">
                            📅 수요예측일: <span class="ipo-date">{item['forecast_date']}</span><br>
                            💰 희망공모가: {item['hope_price']}<br>
                            🏢 주간사: {item['underwriter']}
                        </div>
                    </div>''', unsafe_allow_html=True)
            else:
                st.info("수요예측 일정을 불러오는 중...")
        
        # 캘린더
        with sub3:
            st.markdown(f"### 📆 {ipo_year}년 {ipo_month}월 IPO 캘린더")
            
            if calendar_data:
                for item in calendar_data[:20]:
                    st.markdown(f'''<div class="ipo-card">
                        <div class="ipo-name">{item['company']}</div>
                        <div class="ipo-detail">{ipo_year}년 {ipo_month}월 일정</div>
                    </div>''', unsafe_allow_html=True)
                
                st.markdown(f'''<div class="info-box">
                    <p>💡 상세 일정: <a href="http://www.ipostock.co.kr/sub03/ipo06.asp?thisYear={ipo_year}&thisMonth={ipo_month}" target="_blank">IPOStock 캘린더</a></p>
                </div>''', unsafe_allow_html=True)
            else:
                st.info(f"{ipo_year}년 {ipo_month}월 일정이 없습니다.")
        
        # 승인 종목
        with sub4:
            st.markdown("### ✅ 상장예비심사 승인 종목")
            
            if approval_data:
                for item in approval_data[:15]:
                    st.markdown(f'''<div class="ipo-card">
                        <div class="ipo-name"><span class="badge badge-amber">승인</span> {item['company']}</div>
                        <div class="ipo-detail">
                            📅 승인일: <span class="ipo-date">{item['approval_date']}</span><br>
                            📝 청구일: {item['request_date']}<br>
                            🏢 주간사: {item['underwriter']}
                        </div>
                    </div>''', unsafe_allow_html=True)
            else:
                st.info("승인 종목을 불러오는 중...")
    
    # =========================================================================
    # TAB 2: LP 발굴 (v2.4 동일)
    # =========================================================================
    with tab2:
        st.markdown("## 🔍 Potential LP 발굴")
        
        if st.session_state.lp_corp_list is None:
            st.markdown('''<div class="info-box">
                <p><strong>💡 사용법</strong><br>
                1. "기업 목록 불러오기" 클릭<br>
                2. "다음 배치 조회"로 50개씩 조회<br>
                3. CSV 다운로드</p>
            </div>''', unsafe_allow_html=True)
            
            if st.button("📥 기업 목록 불러오기", type="primary", use_container_width=True):
                with st.spinner("다운로드 중..."):
                    corp_df = get_corp_code_list()
                
                if corp_df is not None:
                    st.session_state.lp_corp_list = corp_df
                    st.success(f"✅ {len(corp_df)}개 기업 로드!")
                    st.rerun()
        
        else:
            corp_df = st.session_state.lp_corp_list
            total = len(corp_df)
            current_idx = st.session_state.lp_current_idx
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("진행", f"{current_idx}/{total}")
            with col2:
                st.metric("LP 후보", f"{len(st.session_state.lp_financial_data)}개")
            with col3:
                st.metric("진행률", f"{current_idx/total*100:.1f}%")
            
            st.progress(current_idx / total if total > 0 else 0)
            
            if current_idx < total:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"⏭️ 다음 {batch_size}개", type="primary", use_container_width=True):
                        end_idx = min(current_idx + batch_size, total)
                        batch = corp_df.iloc[current_idx:end_idx]
                        
                        progress = st.progress(0)
                        results = []
                        
                        for i, row in enumerate(batch.itertuples()):
                            progress.progress((i + 1) / len(batch))
                            result = fetch_single_company(row.corp_code, row.corp_name, row.stock_code, bsns_year)
                            if result:
                                results.append(result)
                            time.sleep(0.2)
                        
                        if results:
                            new_df = pd.DataFrame(results)
                            if st.session_state.lp_financial_data.empty:
                                st.session_state.lp_financial_data = new_df
                            else:
                                st.session_state.lp_financial_data = pd.concat([
                                    st.session_state.lp_financial_data, new_df
                                ], ignore_index=True)
                        
                        st.session_state.lp_current_idx = end_idx
                        st.rerun()
                
                with col_btn2:
                    if st.button("⏩ 3배치", use_container_width=True):
                        for _ in range(3):
                            if st.session_state.lp_current_idx >= total:
                                break
                            
                            end_idx = min(st.session_state.lp_current_idx + batch_size, total)
                            batch = corp_df.iloc[st.session_state.lp_current_idx:end_idx]
                            
                            results = []
                            for row in batch.itertuples():
                                result = fetch_single_company(row.corp_code, row.corp_name, row.stock_code, bsns_year)
                                if result:
                                    results.append(result)
                                time.sleep(0.2)
                            
                            if results:
                                new_df = pd.DataFrame(results)
                                if st.session_state.lp_financial_data.empty:
                                    st.session_state.lp_financial_data = new_df
                                else:
                                    st.session_state.lp_financial_data = pd.concat([
                                        st.session_state.lp_financial_data, new_df
                                    ], ignore_index=True)
                            
                            st.session_state.lp_current_idx = end_idx
                        
                        st.rerun()
            
            st.markdown("---")
            
            if not st.session_state.lp_financial_data.empty:
                df = st.session_state.lp_financial_data.copy()
                df_filtered = df[df['retained_earnings'] >= min_re].copy()
                
                if len(df_filtered) > 0:
                    df_filtered = calculate_lp_score(df_filtered)
                
                st.markdown(f"### LP 후보 ({min_re}억 이상): {len(df_filtered)}개")
                
                if len(df_filtered) > 0:
                    for _, row in df_filtered.head(20).iterrows():
                        st.markdown(f'''<div class="company-card">
                            <div class="company-name">{row['corp_name']} ({row['stock_code']})</div>
                            <div class="company-info">
                                이익잉여금: <strong>{format_number_simple(row['retained_earnings'])}</strong> | 
                                자본총계: {format_number_simple(row.get('total_equity'))}
                            </div>
                        </div>''', unsafe_allow_html=True)
                    
                    csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 CSV 다운로드", csv, f"lp_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    # =========================================================================
    # TAB 3: ESG
    # =========================================================================
    with tab3:
        st.markdown("## 🌱 ESG 공시 검색")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            keyword = st.selectbox("키워드", ["탄소중립", "RE100", "ESG경영", "지속가능경영"])
        with col2:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
        with col3:
            end_date = st.date_input("종료일", datetime.now())
        
        if st.button("🔍 검색", use_container_width=True):
            with st.spinner("검색 중..."):
                df_esg = search_esg_disclosures(keyword, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
            
            if not df_esg.empty:
                st.success(f"✅ {len(df_esg)}건")
                for _, row in df_esg.iterrows():
                    st.markdown(f'''<div class="company-card">
                        <div class="company-name">{row['company']}</div>
                        <div class="company-info">{row['report']} | {row['date']}</div>
                    </div>''', unsafe_allow_html=True)
            else:
                st.info("검색 결과가 없습니다.")
    
    # =========================================================================
    # TAB 4: 데이터
    # =========================================================================
    with tab4:
        st.markdown("## 📋 전체 데이터")
        
        if not st.session_state.lp_financial_data.empty:
            df = st.session_state.lp_financial_data.sort_values('retained_earnings', ascending=False)
            st.dataframe(df, use_container_width=True, height=500)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 다운로드", csv, f"data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("LP 발굴 탭에서 조회를 시작하세요.")
        
        st.markdown("---")
        if st.button("🗑️ LP 데이터 초기화", use_container_width=True):
            st.session_state.lp_corp_list = None
            st.session_state.lp_financial_data = pd.DataFrame()
            st.session_state.lp_current_idx = 0
            st.rerun()
def render_portfolio():
    st.markdown('<p class="section-title"><span class="icon">📈</span> 통합 포트폴리오 관리</p>', unsafe_allow_html=True)
    
    funds = get_fund_data()
    portfolio = get_portfolio_data()
    
    total_aum = sum(f['aum'] for f in funds)
    total_investments = len([p for p in portfolio if p['amount'] > 0])
    total_invested = sum(p['amount'] for p in portfolio)
    total_current_value = sum(p['current_value'] for p in portfolio)
    fund_investments = len([p for p in portfolio if p['account'] == '펀드' and p['amount'] > 0])
    moic = total_current_value / total_invested if total_invested > 0 else 0
    
    st.markdown("### 📊 핵심 KPI")
    col1, col2, col3, col4 = st.columns(4)
    kpis = [("총 운용자산 (AUM)", f"{total_aum:,.1f}억", f"펀드 {len(funds)}개 운용", "indigo"),
            ("총 투자집행", f"{total_invested:,.2f}억", f"투자비율 {total_invested/total_aum*100:.1f}%", "emerald"),
            ("총 투자 건수", f"{total_investments}건", f"펀드 {fund_investments}건", "amber"),
            ("미회수자산 가치", f"{total_current_value:,.2f}억", f"MOIC {moic:.2f}x", "violet")]
    
    for col, (label, value, sub, color) in zip([col1, col2, col3, col4], kpis):
        with col:
            st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-{color});"><div class="metric-label">{label}</div><div class="metric-value large">{value}</div><div style="color: var(--text-muted); font-size: 0.75rem;">{sub}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏦 펀드 현황", "💼 포트폴리오", "📊 분석", "⚙️ 관리"])
    
    with tab1:
        st.markdown("### 🏦 운용 펀드 현황")
        for fund in funds:
            fund_portfolio = [p for p in portfolio if p['fund'] == fund['name'] and p['amount'] > 0]
            fund_invested = sum(p['amount'] for p in fund_portfolio)
            deployment_ratio = fund_invested / fund['aum'] * 100 if fund['aum'] > 0 else 0
            
            st.markdown(f'''<div class="card" style="margin-bottom: 1rem;">
                <div class="card-header"><div class="card-title"><span class="badge badge-emerald">운용중</span> {fund['name']}</div><div class="card-badge">Vintage {fund['vintage']}</div></div>
                <div style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">{fund['full_name']}</div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">약정총액</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{fund['aum']:,.1f}억</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">투자집행</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{fund_invested:,.2f}억</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">투자건수</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{len(fund_portfolio)}건</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">집행률</div><div style="color: var(--accent-emerald); font-size: 1.1rem; font-weight: 600;">{deployment_ratio:.1f}%</div></div>
                </div>
                <div style="margin-top: 1rem;"><div style="background: var(--bg-secondary); border-radius: 4px; height: 8px;"><div style="background: var(--gradient-brand); height: 100%; width: {deployment_ratio}%; border-radius: 4px;"></div></div></div>
            </div>''', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 💼 포트폴리오 상세")
        
        col1, col2 = st.columns(2)
        with col1:
            fund_filter = st.selectbox("펀드", ["전체"] + [f['name'] for f in funds])
        with col2:
            type_filter = st.selectbox("투자유형", ["전체", "RCPS", "CB", "보통주"])
        
        filtered = portfolio
        if fund_filter != "전체":
            filtered = [p for p in filtered if p['fund'] == fund_filter]
        if type_filter != "전체":
            filtered = [p for p in filtered if p['investment_type'] == type_filter]
        
        for p in filtered:
            if p['amount'] > 0:
                type_colors = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}
                
                st.markdown(f'''<div class="card" style="margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                                <span class="badge badge-{type_colors.get(p['investment_type'], 'sky')}">{p['investment_type']}</span>
                                <span style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700;">{p['company']}</span>
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">{p['sector']} | {p['fund']} | {p['investment_date']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: var(--text-primary); font-size: 1.2rem; font-weight: 700;">{p['amount']:,.1f}억</div>
                        </div>
                    </div>
                </div>''', unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### 📊 포트폴리오 분석")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 섹터별 배분")
            sector_data = get_sector_allocation()
            fig_sector = go.Figure(data=[go.Pie(labels=list(sector_data.keys()), values=[d['amount'] for d in sector_data.values()], hole=0.4)])
            fig_sector.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(fig_sector, use_container_width=True)
        
        with col2:
            st.markdown("#### 투자유형별 배분")
            type_data = get_investment_type_allocation()
            fig_type = go.Figure(data=[go.Bar(x=list(type_data.keys()), y=[d['amount'] for d in type_data.values()])])
            fig_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig_type, use_container_width=True)
    
    with tab4:
        st.markdown("### ⚙️ 포트폴리오 관리")
        st.markdown("#### ➕ 신규 투자 등록")
        
        with st.form("new_investment"):
            col1, col2 = st.columns(2)
            with col1:
                new_company = st.text_input("회사명")
                new_sector = st.selectbox("섹터", ["환경/폐기물", "신재생에너지", "수처리", "CCUS", "자원순환", "ESG/SaaS", "수소", "태양광", "풍력", "배터리재활용", "에너지IT", "기타"])
                new_fund = st.selectbox("펀드", ["미래환경펀드", "IPO 일반사모 1호"])
            with col2:
                new_type = st.selectbox("투자유형", ["RCPS", "CB", "보통주"])
                new_amount = st.number_input("투자금액 (억원)", 0.0, 100.0, 10.0, 1.0)
                new_date = st.date_input("투자일")
            
            if st.form_submit_button("📝 등록", use_container_width=True):
                if new_company:
                    new_item = {
                        'company': new_company, 'sector': new_sector, 'fund': new_fund,
                        'account': '펀드', 'investment_type': new_type, 'investment_date': str(new_date),
                        'amount': new_amount, 'current_value': new_amount, 'shares': 0, 'price_per_share': 0,
                        'valuation': new_amount * 5, 'ownership': 10.0, 'status': 'active',
                        'milestone': '', 'next_event': ''
                    }
                    add_portfolio_item(new_item)
                    st.success(f"✅ {new_company} 등록 완료!")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📥 데이터 내보내기")
        portfolio_df = pd.DataFrame(portfolio)
        csv = portfolio_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📊 포트폴리오 CSV", csv, f"ifam_portfolio_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    init_session_state()
    load_css()
    render_header()
    
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page = st.radio("메뉴 선택", ["🏠 홈", "🌱 Daily Market", "📊 VC Analyzer", "🏢 LP & IPO", "📈 Portfolio"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🔄 캐시 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown(f'''<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center;">
            IFAM Dashboard v1.2<br>
            © 2025 인프라프론티어<br><br>
            <strong>LP 후보:</strong> {len(st.session_state.lp_financial_data)}개
        </div>''', unsafe_allow_html=True)
    
    if page == "🏠 홈":
        render_home()
    elif page == "🌱 Daily Market":
        render_daily_market()
    elif page == "📊 VC Analyzer":
        render_vc_analyzer()
    elif page == "🏢 LP & IPO":
        render_lp_discovery()
    elif page == "📈 Portfolio":
        render_portfolio()
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: var(--text-muted); padding: 1rem; font-size: 0.8rem;">🏛️ IFAM 통합 대시보드 v1.2 | 인프라프론티어자산운용(주)<br><small>본 대시보드의 데이터는 참고용이며, 투자 결정 전 원본 데이터를 반드시 확인하세요.</small></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
