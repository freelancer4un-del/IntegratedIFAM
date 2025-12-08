"""
IFAM 통합 대시보드 v1.1
인프라프론티어자산운용(주) - Infra Frontier Asset Management

통합 기능:
1. 🌱 Daily Market - 친환경·인프라 투자 지표 (환율, LNG, 스왑 추가)
2. 📊 VC Analyzer - Term Sheet 분석 & 밸류에이션
3. 🏢 LP Discovery - Potential LP 발굴 & IPO 캘린더 (일괄 다운로드, ESG, 가중치 점수)
4. 📈 Portfolio - 통합 포트폴리오 대시보드 (수정/삭제 기능)

v1.1 업데이트:
- 포트폴리오 수정/삭제 기능
- 환율 크롤링 개선
- LNG, 금리스왑 추가
- IPO 연도/월 필터, 수요예측/심사승인 탭
- LP 발굴 일괄 다운로드, ESG 동향, 가중치 점수

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
    if 'lp_corp_list' not in st.session_state:
        st.session_state.lp_corp_list = None
    if 'lp_data' not in st.session_state:
        st.session_state.lp_data = pd.DataFrame()
    if 'lp_idx' not in st.session_state:
        st.session_state.lp_idx = 0
    if 'lp_loading' not in st.session_state:
        st.session_state.lp_loading = False

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
        
        .action-btn { padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
        .action-btn-edit { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
        .action-btn-edit:hover { background: rgba(99, 102, 241, 0.4); }
        .action-btn-delete { background: rgba(244, 63, 94, 0.2); color: #fb7185; }
        .action-btn-delete:hover { background: rgba(244, 63, 94, 0.4); }
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
# 크롤링 함수들 - Daily Market (개선)
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_exchange_rates():
    """환율 정보 크롤링 - 개선 버전"""
    try:
        # 방법 1: 네이버 금융 API 스타일
        url = 'https://finance.naver.com/marketindex/exchangeList.naver'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rates = {}
        
        # 테이블에서 환율 추출
        table = soup.find('table', class_='tbl_exchange')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        name_cell = cells[0]
                        name = name_cell.get_text(strip=True)
                        
                        # 매매기준율
                        value_text = cells[1].get_text(strip=True).replace(',', '')
                        value = float(value_text)
                        
                        # 전일대비
                        change_cell = cells[2]
                        change_text = change_cell.get_text(strip=True).replace(',', '')
                        try:
                            change = float(change_text)
                        except:
                            change = 0
                        
                        # 방향 확인
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
        
        # 방법 2: 메인 페이지에서 추출 (백업)
        if not rates:
            url2 = 'https://finance.naver.com/marketindex/'
            response2 = requests.get(url2, headers=headers, timeout=10)
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            
            # market_data 클래스에서 추출
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
                    
                    # 하락 체크
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
        
        # 기본값 사용 (크롤링 실패 시)
        if not rates:
            rates = {
                'USD': {'value': 1450.0, 'change': 5.0, 'name': '미국 달러'},
                'JPY': {'value': 950.0, 'change': -2.0, 'name': '일본 엔(100)'},
                'EUR': {'value': 1520.0, 'change': 3.0, 'name': '유로'},
                'CNY': {'value': 198.0, 'change': 0.5, 'name': '중국 위안'}
            }
        
        return rates
    except Exception as e:
        # 기본값 반환
        return {
            'USD': {'value': 1450.0, 'change': 5.0, 'name': '미국 달러'},
            'JPY': {'value': 950.0, 'change': -2.0, 'name': '일본 엔(100)'},
            'EUR': {'value': 1520.0, 'change': 3.0, 'name': '유로'},
            'CNY': {'value': 198.0, 'change': 0.5, 'name': '중국 위안'}
        }

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_oil_prices():
    """국제유가 크롤링"""
    try:
        url = 'https://finance.naver.com/marketindex/worldOilIndex.naver'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    try:
                        name = cells[0].get_text(strip=True)
                        value = float(cells[1].get_text(strip=True).replace(',', ''))
                        change = float(cells[2].get_text(strip=True).replace(',', '')) if len(cells) > 2 else 0
                        
                        if 'WTI' in name:
                            prices['WTI'] = {'value': value, 'change': change}
                        elif '브렌트' in name or 'Brent' in name:
                            prices['Brent'] = {'value': value, 'change': change}
                        elif '두바이' in name:
                            prices['Dubai'] = {'value': value, 'change': change}
                    except:
                        continue
        
        if not prices:
            prices = {'WTI': {'value': 68.5, 'change': 0.5}, 'Brent': {'value': 72.3, 'change': 0.3}, 'Dubai': {'value': 70.1, 'change': 0.2}}
        return prices
    except:
        return {'WTI': {'value': 68.5, 'change': 0.5}, 'Brent': {'value': 72.3, 'change': 0.3}, 'Dubai': {'value': 70.1, 'change': 0.2}}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_data():
    """통합 시장 데이터 (LNG, 스왑 추가)"""
    return {
        'rec': {
            'mainland': {'price': 72303, 'change': -35, 'volume': 12534}, 
            'jeju': {'price': 63904, 'change': -8783, 'volume': 6}
        },
        'smp': {
            'mainland': {'price': 110.52, 'change': 2.3}, 
            'jeju': {'price': 95.17, 'change': -1.5}
        },
        'lng': {
            'tanker': {'value': 23.45, 'change': 0.15, 'unit': '원/MJ'},
            'fuel_cell': {'value': 19.72, 'change': -0.08, 'unit': '원/MJ'},
            'city_gas': {'value': 15.85, 'change': 0.05, 'unit': '원/MJ'}
        },
        'swap': {
            'irs_1y': {'value': 2.85, 'change': 0.02, 'name': 'IRS 1년'},
            'irs_3y': {'value': 2.92, 'change': 0.01, 'name': 'IRS 3년'},
            'irs_5y': {'value': 3.05, 'change': -0.02, 'name': 'IRS 5년'},
            'crs_1y': {'value': 2.45, 'change': 0.03, 'name': 'CRS 1년'},
            'crs_5y': {'value': 2.78, 'change': -0.01, 'name': 'CRS 5년'}
        },
        'rates': {
            'call': {'value': 3.00, 'change': 0.00},
            'cd_91': {'value': 3.15, 'change': -0.02},
            'treasury_3y': {'value': 2.85, 'change': 0.03},
            'treasury_10y': {'value': 3.05, 'change': 0.01},
            'corp_aa_3y': {'value': 3.45, 'change': 0.02}
        }
    }

# =============================================================================
# 크롤링 함수들 - IPO (연도/월 필터, 수요예측, 심사승인 추가)
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

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_subscription(year=None, month=None):
    """IPO 청약 일정 (연도/월 필터)"""
    try:
        # 기본 URL (현재 진행중)
        url = 'http://www.ipostock.co.kr/sub03/ipo04.asp'
        
        # 연도/월 파라미터 추가
        if year and month:
            url = f'http://www.ipostock.co.kr/sub03/ipo04.asp?str_year={year}&str_month={month:02d}'
        elif year:
            url = f'http://www.ipostock.co.kr/sub03/ipo04.asp?str_year={year}'
        
        content = fetch_with_encoding(url)
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
                    if '~' not in date_cell:
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
                        'listing_date': cells[7].get_text(strip=True) if len(cells) > 7 else '-',
                        'competition': cells[8].get_text(strip=True) if len(cells) > 8 else '-',
                        'underwriter': cells[9].get_text(strip=True) if len(cells) > 9 else '-',
                        'type': 'subscription'
                    })
                except:
                    continue
        return results
    except:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_demand_forecast(debug=False):
    """수요예측 일정 (ipo01.asp)"""
    try:
        url = 'http://www.ipostock.co.kr/sub03/ipo01.asp'
        content = fetch_with_encoding(url)
        if not content:
            return [] if not debug else ([], [])
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        debug_rows = []
        
        # 테이블 찾기
        tables = soup.find_all('table')
        target_table = None
        for table in tables:
            if table.find('th') or table.find('td'):
                rows = table.find_all('tr')
                if len(rows) > 3:
                    target_table = table
                    break
        
        if not target_table:
            rows = soup.find_all('tr')
        else:
            rows = target_table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                try:
                    # 디버그용 raw 데이터
                    raw_cells = [c.get_text(strip=True) for c in cells]
                    if debug:
                        debug_rows.append(raw_cells)
                    
                    # 회사명 찾기 (링크가 있는 셀)
                    company_name = None
                    company_idx = -1
                    for idx, cell in enumerate(cells):
                        link = cell.find('a')
                        if link:
                            name = link.get_text(strip=True)
                            if name and len(name) >= 2 and not name.isdigit():
                                company_name = name
                                company_idx = idx
                                break
                    
                    if not company_name:
                        continue
                    
                    # 컬럼 매핑 (테이블 구조에 따라 조정)
                    # 일반적인 구조: 번호, 회사명, 수요예측일, 희망가, 공모금액, 주간사
                    remaining_cells = [c.get_text(strip=True) for i, c in enumerate(cells) if i != company_idx]
                    
                    results.append({
                        'company': company_name,
                        'demand_date': remaining_cells[1] if len(remaining_cells) > 1 else '-',
                        'hope_price': remaining_cells[2] if len(remaining_cells) > 2 else '-',
                        'offer_amount': remaining_cells[3] if len(remaining_cells) > 3 else '-',
                        'underwriter': remaining_cells[4] if len(remaining_cells) > 4 else '-',
                        'raw_data': raw_cells,
                        'type': 'demand_forecast'
                    })
                except:
                    continue
        
        if debug:
            return results, debug_rows
        return results
    except Exception as e:
        if debug:
            return [], [f"Error: {str(e)}"]
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ipo_preliminary_approval(debug=False):
    """상장예비심사 승인 종목 (ipo02.asp)"""
    try:
        url = 'http://www.ipostock.co.kr/sub03/ipo02.asp'
        content = fetch_with_encoding(url)
        if not content:
            return [] if not debug else ([], [])
        
        soup = BeautifulSoup(content, 'html.parser')
        results = []
        debug_rows = []
        
        # 테이블 찾기
        tables = soup.find_all('table')
        target_table = None
        for table in tables:
            if table.find('th') or table.find('td'):
                rows = table.find_all('tr')
                if len(rows) > 3:
                    target_table = table
                    break
        
        if not target_table:
            rows = soup.find_all('tr')
        else:
            rows = target_table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                try:
                    # 디버그용 raw 데이터
                    raw_cells = [c.get_text(strip=True) for c in cells]
                    if debug:
                        debug_rows.append(raw_cells)
                    
                    # 회사명 찾기 (링크가 있는 셀)
                    company_name = None
                    company_idx = -1
                    for idx, cell in enumerate(cells):
                        link = cell.find('a')
                        if link:
                            name = link.get_text(strip=True)
                            if name and len(name) >= 2 and not name.isdigit():
                                company_name = name
                                company_idx = idx
                                break
                    
                    if not company_name:
                        continue
                    
                    # 컬럼 매핑 (테이블 구조에 따라 조정)
                    # 일반적인 구조: 번호, 회사명, 승인일, 시장, 주간사
                    remaining_cells = [c.get_text(strip=True) for i, c in enumerate(cells) if i != company_idx]
                    
                    results.append({
                        'company': company_name,
                        'approval_date': remaining_cells[1] if len(remaining_cells) > 1 else '-',
                        'market': remaining_cells[2] if len(remaining_cells) > 2 else '-',
                        'underwriter': remaining_cells[3] if len(remaining_cells) > 3 else '-',
                        'raw_data': raw_cells,
                        'type': 'preliminary_approval'
                    })
                except:
                    continue
        
        if debug:
            return results, debug_rows
        return results
    except Exception as e:
        if debug:
            return [], [f"Error: {str(e)}"]
        return []
# =============================================================================
# 크롤링 함수들 - LP Discovery (일괄 다운로드, ESG, 가중치 점수)
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
    """재무데이터 추출 (확장)"""
    result = {
        'retained_earnings': None,
        'total_equity': None,
        'revenue': None,
        'operating_profit': None,
        'net_income': None,
        'total_assets': None,
        'total_liabilities': None
    }
    
    if df is None or df.empty:
        return result
    
    # 이익잉여금
    for kw in ['이익잉여금', '이익(손실)잉여금']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['retained_earnings'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    # 자본총계
    for kw in ['자본총계']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['total_equity'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    # 매출액
    for kw in ['매출액', '영업수익', '수익']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['revenue'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    # 영업이익
    for kw in ['영업이익', '영업손익']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['operating_profit'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    # 당기순이익
    for kw in ['당기순이익', '당기순손익']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['net_income'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    # 자산총계
    for kw in ['자산총계']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['total_assets'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
    return result

def calculate_lp_score(row, weights=None):
    """LP 가중치 점수 계산"""
    if weights is None:
        weights = {
            'retained_earnings': 0.35,  # 이익잉여금
            'total_equity': 0.20,       # 자본총계
            'revenue': 0.15,            # 매출액
            'operating_profit': 0.15,   # 영업이익
            'net_income': 0.10,         # 당기순이익
            'esg_score': 0.05           # ESG 점수
        }
    
    score = 0
    max_score = 100
    
    # 이익잉여금 점수 (0-35점)
    re = row.get('retained_earnings', 0) or 0
    if re >= 5000:
        score += weights['retained_earnings'] * max_score
    elif re >= 1000:
        score += weights['retained_earnings'] * max_score * 0.8
    elif re >= 500:
        score += weights['retained_earnings'] * max_score * 0.6
    elif re >= 300:
        score += weights['retained_earnings'] * max_score * 0.4
    elif re >= 100:
        score += weights['retained_earnings'] * max_score * 0.2
    
    # 자본총계 점수 (0-20점)
    te = row.get('total_equity', 0) or 0
    if te >= 10000:
        score += weights['total_equity'] * max_score
    elif te >= 5000:
        score += weights['total_equity'] * max_score * 0.7
    elif te >= 1000:
        score += weights['total_equity'] * max_score * 0.4
    
    # 매출액 점수 (0-15점)
    rev = row.get('revenue', 0) or 0
    if rev >= 10000:
        score += weights['revenue'] * max_score
    elif rev >= 5000:
        score += weights['revenue'] * max_score * 0.7
    elif rev >= 1000:
        score += weights['revenue'] * max_score * 0.4
    
    # 영업이익 점수 (0-15점)
    op = row.get('operating_profit', 0) or 0
    if op >= 1000:
        score += weights['operating_profit'] * max_score
    elif op >= 500:
        score += weights['operating_profit'] * max_score * 0.7
    elif op >= 100:
        score += weights['operating_profit'] * max_score * 0.4
    elif op > 0:
        score += weights['operating_profit'] * max_score * 0.2
    
    # 당기순이익 점수 (0-10점)
    ni = row.get('net_income', 0) or 0
    if ni >= 500:
        score += weights['net_income'] * max_score
    elif ni >= 100:
        score += weights['net_income'] * max_score * 0.6
    elif ni > 0:
        score += weights['net_income'] * max_score * 0.3
    
    # ESG 점수 (0-5점)
    esg = row.get('esg_score', 0) or 0
    score += esg * weights['esg_score']
    
    return round(score, 1)

def get_esg_keywords():
    """ESG 관련 키워드"""
    return {
        'environment': ['환경', '탄소', '친환경', '재생에너지', '태양광', '풍력', '수소', 'ESG', '기후변화', 
                       '탄소중립', '넷제로', '그린', '신재생', '폐기물', '순환경제', '저탄소'],
        'social': ['사회공헌', '지역사회', '근로환경', '안전보건', '인권', '다양성', '포용', '상생'],
        'governance': ['지배구조', '이사회', '감사', '윤리경영', '준법', '투명성', '공시']
    }

def check_esg_involvement(corp_name, sector=None):
    """기업의 ESG 관련 여부 체크 (간단한 휴리스틱)"""
    esg_keywords = get_esg_keywords()
    
    # 친환경/ESG 관련 기업명 체크
    env_score = 0
    for kw in esg_keywords['environment']:
        if kw in corp_name:
            env_score += 20
    
    # 섹터 기반 ESG 점수
    esg_sectors = ['신재생에너지', '환경', '폐기물', '수처리', '태양광', '풍력', '수소', '전기차', '2차전지']
    if sector:
        for s in esg_sectors:
            if s in sector:
                env_score += 30
    
    return min(env_score, 100)

def batch_process_lp_data(corp_list, bsns_year, start_idx, batch_size, progress_callback=None):
    """배치 처리 함수"""
    end_idx = min(start_idx + batch_size, len(corp_list))
    batch = corp_list.iloc[start_idx:end_idx]
    
    results = []
    for i, row in enumerate(batch.itertuples()):
        if progress_callback:
            progress_callback((i + 1) / len(batch))
        
        fs_df = get_financial_statement(row.corp_code, bsns_year)
        fin_data = extract_financial_data(fs_df)
        
        if fin_data['retained_earnings'] is not None:
            # ESG 점수 추가
            esg_score = check_esg_involvement(row.corp_name)
            fin_data['esg_score'] = esg_score
            
            # LP 점수 계산
            lp_score = calculate_lp_score(fin_data)
            
            results.append({
                'corp_code': row.corp_code,
                'corp_name': row.corp_name,
                'stock_code': row.stock_code,
                'lp_score': lp_score,
                'esg_score': esg_score,
                **fin_data
            })
        
        time.sleep(0.15)  # API 제한 준수
    
    return results, end_idx

def auto_download_all_lp_data(corp_list, bsns_year, min_re, progress_placeholder):
    """전체 LP 데이터 자동 다운로드 (일괄처리)"""
    total = len(corp_list)
    batch_size = 100
    all_results = []
    current_idx = 0
    
    progress_bar = progress_placeholder.progress(0)
    status_text = progress_placeholder.empty()
    
    while current_idx < total:
        status_text.text(f"📊 조회 중... {current_idx}/{total} ({current_idx/total*100:.1f}%)")
        
        results, new_idx = batch_process_lp_data(
            corp_list, bsns_year, current_idx, batch_size,
            progress_callback=lambda p: progress_bar.progress((current_idx + p * batch_size) / total)
        )
        
        all_results.extend(results)
        current_idx = new_idx
        
        # 중간 결과 업데이트
        progress_bar.progress(current_idx / total)
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ 완료! 총 {len(all_results)}개 기업 조회")
    
    # 필터링 및 정렬
    df = pd.DataFrame(all_results)
    if not df.empty:
        df_filtered = df[df['retained_earnings'] >= min_re].copy()
        df_filtered = df_filtered.sort_values('lp_score', ascending=False)
        return df_filtered
    
    return pd.DataFrame()
# =============================================================================
# 포트폴리오 데이터 정의 (세션 상태 기반)
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
        {'id': 13, 'company': '친환경모빌리티', 'sector': 'EV/모빌리티', 'fund': '고유계정', 'account': '고유',
         'investment_type': 'RCPS', 'investment_date': '2024-02-10', 'amount': 0, 'current_value': 0,
         'shares': 0, 'price_per_share': 0, 'valuation': 0, 'ownership': 0, 'status': 'committed',
         'milestone': 'Due Diligence 완료', 'next_event': '투자 검토 중'},
        {'id': 14, 'company': '그린빌딩', 'sector': '건설/에너지효율', 'fund': '고유계정', 'account': '고유',
         'investment_type': 'CB', 'investment_date': '2024-03-20', 'amount': 0, 'current_value': 0,
         'shares': 0, 'price_per_share': 0, 'valuation': 0, 'ownership': 0, 'status': 'committed',
         'milestone': 'MOU 체결', 'next_event': '구조화 진행 중'},
    ]

def get_fund_data():
    """펀드 데이터 반환 (세션 상태)"""
    return st.session_state.fund_data

def get_portfolio_data():
    """포트폴리오 데이터 반환 (세션 상태)"""
    return st.session_state.portfolio_data

def add_portfolio_item(item):
    """포트폴리오 항목 추가"""
    # 새 ID 생성
    max_id = max([p['id'] for p in st.session_state.portfolio_data], default=0)
    item['id'] = max_id + 1
    st.session_state.portfolio_data.append(item)
    return item['id']

def update_portfolio_item(item_id, updates):
    """포트폴리오 항목 수정"""
    for i, p in enumerate(st.session_state.portfolio_data):
        if p['id'] == item_id:
            st.session_state.portfolio_data[i].update(updates)
            return True
    return False

def delete_portfolio_item(item_id):
    """포트폴리오 항목 삭제"""
    st.session_state.portfolio_data = [p for p in st.session_state.portfolio_data if p['id'] != item_id]

def get_sector_allocation():
    """섹터별 배분"""
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
    """투자유형별 배분"""
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
    """RVPS 계산"""
    total_shares = founder_shares + sum(r.shares for r in rounds)
    results = []
    
    for r in rounds:
        if r.shares > 0:
            rvps = (r.investment * r.liquidation_multiple) / r.shares
        else:
            rvps = 0
        results.append({
            'name': r.name,
            'investment': r.investment,
            'shares': r.shares,
            'ownership': r.shares / total_shares * 100 if total_shares > 0 else 0,
            'rvps': rvps,
            'participating': r.is_participating,
            'liq_multiple': r.liquidation_multiple,
            'seniority': r.seniority
        })
    
    results.append({
        'name': '창업자',
        'investment': 0,
        'shares': founder_shares,
        'ownership': founder_shares / total_shares * 100 if total_shares > 0 else 0,
        'rvps': 0,
        'participating': False,
        'liq_multiple': 0,
        'seniority': 999
    })
    
    return sorted(results, key=lambda x: (-x['rvps'], x['seniority']))

def calculate_exit_payoffs(rounds: List[InvestmentRound], founder_shares: float, exit_values: np.ndarray) -> Dict[str, np.ndarray]:
    """Exit 시나리오별 수익 계산"""
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
    """LP 기준 투자비용"""
    lifetime_fees = fund.committed_capital * (fund.management_fee_rate / 100) * 10
    investable = fund.committed_capital - lifetime_fees
    return (fund.committed_capital / investable) * investment if investable > 0 else investment

def calculate_gp_lp_split(partial_val: float, fund: FundInfo, investment: float):
    """GP/LP 수익 분배"""
    lp_cost = calculate_lp_cost(fund, investment)
    profit = max(0, partial_val - investment)
    hurdle_amount = investment * (fund.hurdle_rate / 100) * 5
    
    if profit > hurdle_amount:
        gp_carry = (profit - hurdle_amount) * (fund.carried_interest / 100)
    else:
        gp_carry = 0
    
    lp_val = partial_val - gp_carry
    return {
        'lp_cost': lp_cost,
        'partial_val': partial_val,
        'profit': profit,
        'hurdle': hurdle_amount,
        'gp_carry': gp_carry,
        'lp_val': lp_val,
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
            <span class="header-meta-item">🔄 실시간 데이터</span>
            <span class="header-meta-item">📊 v1.1</span>
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
    prop_count = len([p for p in portfolio if p['account'] == '고유'])
    
    st.markdown("### 📊 IFAM 운용 현황")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-indigo);"><div class="metric-label">총 AUM</div><div class="metric-value large">{total_aum:,.1f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {len(funds)}개 운용</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-emerald);"><div class="metric-label">투자집행</div><div class="metric-value large">{total_invested:,.2f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">집행률 {total_invested/total_aum*100:.1f}%</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-amber);"><div class="metric-label">투자건수</div><div class="metric-value large">{total_investments}건</div><div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {fund_count} / 고유 {prop_count}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-violet);"><div class="metric-label">미회수자산</div><div class="metric-value large">{total_invested:,.2f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">회수 0건 | MOIC 1.0x</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🧭 바로가기")
    col1, col2, col3, col4 = st.columns(4)
    nav_items = [("🌱", "Daily Market", "친환경·인프라 투자 지표"), ("📊", "VC Analyzer", "Term Sheet 분석"), ("🏢", "LP Discovery", "LP 발굴 & IPO"), ("📈", "Portfolio", "통합 포트폴리오")]
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], nav_items):
        with col:
            st.markdown(f'<div class="nav-card"><div class="nav-card-icon">{icon}</div><div class="nav-card-title">{title}</div><div class="nav-card-desc">{desc}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<p class="section-title"><span class="icon">📊</span> 오늘의 주요 지표</p>', unsafe_allow_html=True)
    
    exchange_rates = fetch_exchange_rates()
    oil_prices = fetch_oil_prices()
    market_data = fetch_market_data()
    
    col1, col2, col3, col4 = st.columns(4)
    if exchange_rates and 'USD' in exchange_rates:
        usd = exchange_rates['USD']
        cls, arrow = get_change_class(usd['change'])
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">USD/KRW</div><div class="metric-value">{usd["value"]:,.2f}</div><div class="metric-change {cls}">{arrow} {abs(usd["change"]):.2f}</div></div>', unsafe_allow_html=True)
    if oil_prices and 'WTI' in oil_prices:
        wti = oil_prices['WTI']
        cls, arrow = get_change_class(wti['change'])
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">WTI 유가</div><div class="metric-value">${wti["value"]:.2f}</div><div class="metric-change {cls}">{arrow} ${abs(wti["change"]):.2f}</div></div>', unsafe_allow_html=True)
    rec = market_data['rec']['mainland']
    cls, arrow = get_change_class(rec['change'])
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">REC 가격 (육지)</div><div class="metric-value">{rec["price"]:,}원</div><div class="metric-change {cls}">{arrow} {abs(rec["change"]):,}</div></div>', unsafe_allow_html=True)
    treasury = market_data['rates']['treasury_3y']
    cls, arrow = get_change_class(treasury['change'])
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">국고채 3년</div><div class="metric-value">{treasury["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(treasury["change"]):.2f}%p</div></div>', unsafe_allow_html=True)

def render_daily_market():
    st.markdown('<p class="section-title"><span class="icon">🌱</span> Daily Market - 친환경·인프라 지표</p>', unsafe_allow_html=True)
    
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
        st.warning("환율 데이터를 불러오는 중...")
    
    st.markdown("---")
    st.markdown("#### ⚡ 신재생에너지")
    market_data = fetch_market_data()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### REC")
        rec = market_data['rec']
        c1, c2 = st.columns(2)
        for col, (key, label) in zip([c1, c2], [('mainland', '육지'), ('jeju', '제주')]):
            cls, arrow = get_change_class(rec[key]['change'])
            with col:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{label} REC</div><div class="metric-value">{rec[key]["price"]:,}원</div><div class="metric-change {cls}">{arrow} {abs(rec[key]["change"]):,}</div><div style="color: var(--text-muted); font-size: 0.75rem;">거래량: {rec[key]["volume"]:,}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("##### SMP")
        smp = market_data['smp']
        c1, c2 = st.columns(2)
        for col, (key, label) in zip([c1, c2], [('mainland', '육지'), ('jeju', '제주')]):
            cls, arrow = get_change_class(smp[key]['change'])
            with col:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{label} SMP</div><div class="metric-value">{smp[key]["price"]:.2f}</div><div style="color: var(--text-muted); font-size: 0.8rem;">원/kWh</div><div class="metric-change {cls}">{arrow} {abs(smp[key]["change"]):.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛢️ 국제유가")
        oil_prices = fetch_oil_prices()
        cols = st.columns(3)
        for i, (code, name) in enumerate([('WTI', '서부텍사스'), ('Brent', '북해 브렌트'), ('Dubai', '두바이')]):
            if code in oil_prices:
                data = oil_prices[code]
                cls, arrow = get_change_class(data['change'])
                with cols[i]:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">${data["value"]:.2f}</div><div class="metric-change {cls}">{arrow} ${abs(data["change"]):.2f}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🔥 LNG")
        lng = market_data['lng']
        cols = st.columns(3)
        for i, (key, name) in enumerate([('tanker', '탱크로리'), ('fuel_cell', '연료전지'), ('city_gas', '도시가스')]):
            data = lng[key]
            cls, arrow = get_change_class(data['change'])
            with cols[i]:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div class="metric-value">{data["value"]:.2f}</div><div style="color: var(--text-muted); font-size: 0.75rem;">{data["unit"]}</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 금리")
        rates = market_data['rates']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 단기금리")
            for key, label in [('call', '콜금리'), ('cd_91', 'CD 91일')]:
                data = rates[key]
                cls, arrow = get_change_class(data['change'])
                st.markdown(f'<div class="metric-card" style="margin-bottom: 0.5rem;"><div class="metric-label">{label}</div><div class="metric-value">{data["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}%p</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown("##### 채권금리")
            for key, label in [('treasury_3y', '국고채 3년'), ('corp_aa_3y', '회사채 AA-')]:
                data = rates[key]
                cls, arrow = get_change_class(data['change'])
                st.markdown(f'<div class="metric-card" style="margin-bottom: 0.5rem;"><div class="metric-label">{label}</div><div class="metric-value">{data["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}%p</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📈 금리스왑")
        swap = market_data['swap']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### IRS")
            for key in ['irs_1y', 'irs_3y', 'irs_5y']:
                data = swap[key]
                cls, arrow = get_change_class(data['change'])
                st.markdown(f'<div class="metric-card" style="margin-bottom: 0.5rem;"><div class="metric-label">{data["name"]}</div><div class="metric-value">{data["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}%p</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown("##### CRS")
            for key in ['crs_1y', 'crs_5y']:
                data = swap[key]
                cls, arrow = get_change_class(data['change'])
                st.markdown(f'<div class="metric-card" style="margin-bottom: 0.5rem;"><div class="metric-label">{data["name"]}</div><div class="metric-value">{data["value"]:.2f}%</div><div class="metric-change {cls}">{arrow} {abs(data["change"]):.2f}%p</div></div>', unsafe_allow_html=True)
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
    st.markdown('<p class="section-title"><span class="icon">🏢</span> LP Discovery & IPO 캘린더</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📅 IPO 일정", "🔍 LP 발굴", "📊 ESG 동향"])
    
    with tab1:
        st.markdown("### 📅 IPO 일정")
        
        # 필터
        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
        with col1:
            ipo_year = st.selectbox("연도", [2026, 2025, 2024, 2023], index=0)
        with col2:
            ipo_month = st.selectbox("월", [None] + list(range(1, 13)), format_func=lambda x: "전체" if x is None else f"{x}월")
        with col3:
            ipo_type = st.selectbox("유형", ["청약일정", "수요예측", "심사승인"])
        with col4:
            debug_mode = st.checkbox("🔧 디버그", help="크롤링 raw 데이터 확인")
        
        if ipo_type == "청약일정":
            ipo_data = fetch_ipo_subscription(ipo_year, ipo_month)
            if ipo_data:
                st.markdown(f'<div class="metric-card" style="text-align: center;"><div class="metric-label">IPO 일정</div><div class="metric-value large">{len(ipo_data)}건</div></div>', unsafe_allow_html=True)
                for item in ipo_data[:20]:
                    is_ongoing = item.get('competition', '-') == '-'
                    badge_class = 'rose' if is_ongoing else 'emerald'
                    badge_text = '청약중' if is_ongoing else '완료'
                    st.markdown(f'<div class="ipo-card"><div class="ipo-name"><span class="badge badge-{badge_class}">{badge_text}</span> {item["company"]}</div><div class="ipo-detail">📅 청약: <span class="ipo-date">{item["subscription_date"]}</span> | 💰 공모가: <span class="ipo-price">{item["offer_price"]}</span><br>📊 공모금액: {item["offer_amount"]} | 경쟁률: {item["competition"]}<br>🏢 주간사: {item["underwriter"]} | 상장일: {item["listing_date"]}</div></div>', unsafe_allow_html=True)
            else:
                st.info("해당 기간 IPO 일정이 없습니다.")
        
        elif ipo_type == "수요예측":
            if debug_mode:
                demand_data, debug_rows = fetch_ipo_demand_forecast(debug=True)
                if debug_rows:
                    st.markdown("#### 🔧 디버그: Raw 테이블 데이터")
                    st.write(f"총 {len(debug_rows)}행 발견")
                    for i, row in enumerate(debug_rows[:10]):
                        st.code(f"행 {i}: {row}")
            else:
                demand_data = fetch_ipo_demand_forecast(debug=False)
            
            if demand_data:
                st.markdown(f'<div class="metric-card" style="text-align: center;"><div class="metric-label">수요예측 일정</div><div class="metric-value large">{len(demand_data)}건</div></div>', unsafe_allow_html=True)
                for item in demand_data[:15]:
                    if debug_mode and 'raw_data' in item:
                        st.code(f"Raw: {item['raw_data']}")
                    st.markdown(f'<div class="ipo-card"><div class="ipo-name"><span class="badge badge-amber">수요예측</span> {item["company"]}</div><div class="ipo-detail">📅 예측일: <span class="ipo-date">{item["demand_date"]}</span> | 💰 희망가: {item["hope_price"]}<br>📊 공모금액: {item["offer_amount"]} | 🏢 주간사: {item["underwriter"]}</div></div>', unsafe_allow_html=True)
            else:
                st.info("수요예측 일정을 불러오는 중...")
        
        else:  # 심사승인
            if debug_mode:
                approval_data, debug_rows = fetch_ipo_preliminary_approval(debug=True)
                if debug_rows:
                    st.markdown("#### 🔧 디버그: Raw 테이블 데이터")
                    st.write(f"총 {len(debug_rows)}행 발견")
                    for i, row in enumerate(debug_rows[:10]):
                        st.code(f"행 {i}: {row}")
            else:
                approval_data = fetch_ipo_preliminary_approval(debug=False)
            
            if approval_data:
                st.markdown(f'<div class="metric-card" style="text-align: center;"><div class="metric-label">상장예비심사 승인</div><div class="metric-value large">{len(approval_data)}건</div></div>', unsafe_allow_html=True)
                for item in approval_data[:15]:
                    if debug_mode and 'raw_data' in item:
                        st.code(f"Raw: {item['raw_data']}")
                    st.markdown(f'<div class="ipo-card"><div class="ipo-name"><span class="badge badge-emerald">승인</span> {item["company"]}</div><div class="ipo-detail">📅 승인일: <span class="ipo-date">{item["approval_date"]}</span> | 📈 시장: {item["market"]}<br>🏢 주간사: {item["underwriter"]}</div></div>', unsafe_allow_html=True)
            else:
                st.info("심사승인 종목을 불러오는 중...")
    
    with tab2:
        st.markdown("### 🔍 Potential LP 발굴 (일괄 다운로드)")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            bsns_year = st.selectbox("사업연도", ['2024', '2023', '2022'], index=0, key='lp_year')
            min_re = st.number_input("최소 이익잉여금 (억원)", 0, 10000, 300, 100, key='lp_min_re')
        with col2:
            st.markdown("#### 가중치 설정")
            w_re = st.slider("이익잉여금", 0, 100, 35)
            w_equity = st.slider("자본총계", 0, 100, 20)
            w_esg = st.slider("ESG", 0, 100, 15)
        
        weights = {'retained_earnings': w_re/100, 'total_equity': w_equity/100, 'revenue': 0.15, 'operating_profit': 0.10, 'net_income': 0.05, 'esg_score': w_esg/100}
        
        if st.session_state.lp_corp_list is None:
            st.markdown('<div class="info-box"><p><strong>💡 사용법</strong><br>1. "일괄 조회 시작" 클릭<br>2. 자동으로 전체 기업 조회<br>3. 완료 후 CSV 다운로드</p></div>', unsafe_allow_html=True)
            
            if st.button("📥 기업 목록 불러오기", type="primary", use_container_width=True):
                with st.spinner("기업 목록 다운로드 중..."):
                    corp_df = get_corp_code_list()
                if corp_df is not None:
                    st.session_state.lp_corp_list = corp_df
                    st.success(f"✅ {len(corp_df)}개 기업 로드!")
                    st.rerun()
        else:
            total = len(st.session_state.lp_corp_list)
            
            if st.session_state.lp_data.empty:
                if st.button("🚀 일괄 조회 시작", type="primary", use_container_width=True):
                    progress_placeholder = st.container()
                    result_df = auto_download_all_lp_data(st.session_state.lp_corp_list, bsns_year, min_re, progress_placeholder)
                    if not result_df.empty:
                        st.session_state.lp_data = result_df
                        st.rerun()
            else:
                df = st.session_state.lp_data.copy()
                df_filtered = df[df['retained_earnings'] >= min_re].sort_values('lp_score', ascending=False)
                
                st.markdown(f"### 🏆 LP 후보 ({min_re}억 이상): {len(df_filtered)}개")
                st.markdown(f"<small>LP 점수 기준 정렬 (이익잉여금 {w_re}% + 자본 {w_equity}% + ESG {w_esg}%)</small>", unsafe_allow_html=True)
                
                for _, row in df_filtered.head(20).iterrows():
                    score_color = 'emerald' if row['lp_score'] >= 70 else 'amber' if row['lp_score'] >= 50 else 'rose'
                    esg_badge = f'<span class="badge badge-emerald">ESG {row["esg_score"]:.0f}</span>' if row.get('esg_score', 0) > 0 else ''
                    st.markdown(f'<div class="data-row"><div class="data-row-left"><div class="data-row-title"><span class="badge badge-{score_color}">{row["lp_score"]:.0f}점</span> {esg_badge} {row["corp_name"]}</div><div class="data-row-subtitle">{row["stock_code"]}</div></div><div class="data-row-value">{format_number(row["retained_earnings"], 0)}원</div></div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 CSV 다운로드", csv, f"lp_candidates_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
                with col2:
                    if st.button("🔄 초기화", use_container_width=True):
                        st.session_state.lp_data = pd.DataFrame()
                        st.session_state.lp_corp_list = None
                        st.rerun()
    
    with tab3:
        st.markdown("### 📊 ESG 동향 분석")
        
        esg_keywords = get_esg_keywords()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 🌿 환경 (E)")
            for kw in esg_keywords['environment'][:8]:
                st.markdown(f'<span class="badge badge-emerald" style="margin: 0.2rem;">{kw}</span>', unsafe_allow_html=True)
        with col2:
            st.markdown("#### 👥 사회 (S)")
            for kw in esg_keywords['social']:
                st.markdown(f'<span class="badge badge-sky" style="margin: 0.2rem;">{kw}</span>', unsafe_allow_html=True)
        with col3:
            st.markdown("#### 🏛️ 지배구조 (G)")
            for kw in esg_keywords['governance']:
                st.markdown(f'<span class="badge badge-violet" style="margin: 0.2rem;">{kw}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🎯 ESG 관련 유망 섹터")
        esg_sectors = [("신재생에너지", "태양광, 풍력, 수소 발전", 95), ("2차전지/배터리", "배터리 재활용, ESS", 90), ("전기차/모빌리티", "EV, 충전 인프라", 85), ("탄소중립/CCUS", "탄소포집, 저장", 88), ("폐기물/자원순환", "폐기물 처리, 재활용", 82)]
        
        for sector, desc, score in esg_sectors:
            st.markdown(f'<div class="data-row"><div class="data-row-left"><div class="data-row-title">{sector}</div><div class="data-row-subtitle">{desc}</div></div><div class="data-row-value"><span class="badge badge-emerald">{score}점</span></div></div>', unsafe_allow_html=True)
def render_portfolio():
    st.markdown('<p class="section-title"><span class="icon">📈</span> 통합 포트폴리오 관리</p>', unsafe_allow_html=True)
    
    funds = get_fund_data()
    portfolio = get_portfolio_data()
    
    total_aum = sum(f['aum'] for f in funds)
    total_investments = len([p for p in portfolio if p['amount'] > 0])
    total_invested = sum(p['amount'] for p in portfolio)
    total_current_value = sum(p['current_value'] for p in portfolio)
    fund_investments = len([p for p in portfolio if p['account'] == '펀드' and p['amount'] > 0])
    proprietary_investments = len([p for p in portfolio if p['account'] == '고유'])
    moic = total_current_value / total_invested if total_invested > 0 else 0
    
    st.markdown("### 📊 핵심 KPI")
    col1, col2, col3, col4 = st.columns(4)
    kpis = [("총 운용자산 (AUM)", f"{total_aum:,.1f}억", f"펀드 {len(funds)}개 운용", "indigo"),
            ("총 투자집행", f"{total_invested:,.2f}억", f"투자비율 {total_invested/total_aum*100:.1f}%", "emerald"),
            ("총 투자 건수", f"{total_investments}건", f"펀드 {fund_investments} / 고유 {proprietary_investments}", "amber"),
            ("미회수자산 가치", f"{total_current_value:,.2f}억", f"MOIC {moic:.2f}x | 회수 0건", "violet")]
    
    for col, (label, value, sub, color) in zip([col1, col2, col3, col4], kpis):
        with col:
            st.markdown(f'<div class="metric-card" style="border-left: 3px solid var(--accent-{color});"><div class="metric-label">{label}</div><div class="metric-value large">{value}</div><div style="color: var(--text-muted); font-size: 0.75rem;">{sub}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏦 펀드 현황", "💼 포트폴리오", "📊 분석", "📅 이벤트", "⚙️ 관리"])
    
    with tab1:
        st.markdown("### 🏦 운용 펀드 현황")
        for fund in funds:
            fund_portfolio = [p for p in portfolio if p['fund'] == fund['name'] and p['amount'] > 0]
            fund_invested = sum(p['amount'] for p in fund_portfolio)
            deployment_ratio = fund_invested / fund['aum'] * 100 if fund['aum'] > 0 else 0
            status_class = 'emerald' if fund['status'] == 'active' else 'amber'
            
            st.markdown(f'''<div class="card" style="margin-bottom: 1rem;">
                <div class="card-header"><div class="card-title"><span class="badge badge-{status_class}">운용중</span> {fund['name']}</div><div class="card-badge">Vintage {fund['vintage']}</div></div>
                <div style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">{fund['full_name']}</div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">약정총액</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{fund['aum']:,.1f}억</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">투자집행</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{fund_invested:,.2f}억</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">투자건수</div><div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600;">{len(fund_portfolio)}건</div></div>
                    <div><div style="color: var(--text-muted); font-size: 0.7rem;">집행률</div><div style="color: var(--accent-emerald); font-size: 1.1rem; font-weight: 600;">{deployment_ratio:.1f}%</div></div>
                </div>
                <div style="margin-top: 1rem;"><div style="background: var(--bg-secondary); border-radius: 4px; height: 8px;"><div style="background: var(--gradient-brand); height: 100%; width: {deployment_ratio}%;"></div></div></div>
                <div style="display: flex; gap: 2rem; margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">
                    <span>📅 {fund['investment_period']}</span><span>🏢 GP: {', '.join(fund['gp'])}</span><span>💰 LP: {fund['lp']}</span>
                </div>
            </div>''', unsafe_allow_html=True)
        
        remaining = total_aum - total_invested
        st.markdown(f'<div class="info-box"><p><strong>💰 잔여 투자여력</strong><br>총 약정 {total_aum:,.1f}억 - 투자집행 {total_invested:,.2f}억 = <strong style="color: var(--accent-emerald);">{remaining:,.2f}억</strong></p></div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 💼 포트폴리오 상세 현황")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fund_filter = st.selectbox("펀드", ["전체"] + [f['name'] for f in funds] + ["고유계정"])
        with col2:
            type_filter = st.selectbox("투자유형", ["전체", "RCPS", "CB", "보통주"])
        with col3:
            status_filter = st.selectbox("상태", ["전체", "active", "committed", "exited"])
        
        filtered = portfolio
        if fund_filter != "전체":
            filtered = [p for p in filtered if p['fund'] == fund_filter]
        if type_filter != "전체":
            filtered = [p for p in filtered if p['investment_type'] == type_filter]
        if status_filter != "전체":
            filtered = [p for p in filtered if p['status'] == status_filter]
        
        st.markdown(f"**{len(filtered)}개** 투자건")
        
        # 수정/삭제 모달
        if 'edit_item_id' not in st.session_state:
            st.session_state.edit_item_id = None
        if 'delete_item_id' not in st.session_state:
            st.session_state.delete_item_id = None
        
        for p in filtered:
            if p['amount'] > 0:
                type_colors = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}
                status_colors = {'active': 'emerald', 'committed': 'amber', 'exited': 'rose'}
                status_texts = {'active': '투자중', 'committed': '검토중', 'exited': '회수완료'}
                
                unrealized_gain = p['current_value'] - p['amount']
                gain_class = 'up' if unrealized_gain >= 0 else 'down'
                gain_arrow = '▲' if unrealized_gain >= 0 else '▼'
                
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f'''<div class="card" style="margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                                    <span class="badge badge-{type_colors.get(p['investment_type'], 'sky')}">{p['investment_type']}</span>
                                    <span class="badge badge-{status_colors.get(p['status'], 'sky')}">{status_texts.get(p['status'], p['status'])}</span>
                                    <span style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700;">{p['company']}</span>
                                </div>
                                <div style="color: var(--text-muted); font-size: 0.8rem;">{p['sector']} | {p['fund']} | {p['investment_date']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: var(--text-primary); font-size: 1.2rem; font-weight: 700;">{p['amount']:,.1f}억</div>
                                <div class="metric-change {gain_class}">{gain_arrow} {abs(unrealized_gain):,.2f}억</div>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                            <div><div style="color: var(--text-muted); font-size: 0.65rem;">기업가치</div><div style="color: var(--text-secondary); font-size: 0.85rem;">{p['valuation']:,.0f}억</div></div>
                            <div><div style="color: var(--text-muted); font-size: 0.65rem;">지분율</div><div style="color: var(--text-secondary); font-size: 0.85rem;">{p['ownership']:.1f}%</div></div>
                            <div><div style="color: var(--text-muted); font-size: 0.65rem;">MOIC</div><div style="color: var(--accent-emerald); font-size: 0.85rem;">{p['current_value']/p['amount']:.2f}x</div></div>
                            <div><div style="color: var(--text-muted); font-size: 0.65rem;">마일스톤</div><div style="color: var(--text-secondary); font-size: 0.8rem;">{p['milestone']}</div></div>
                            <div><div style="color: var(--text-muted); font-size: 0.65rem;">다음 이벤트</div><div style="color: var(--accent-amber); font-size: 0.8rem;">{p['next_event']}</div></div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                
                with col2:
                    if st.button("✏️", key=f"edit_{p['id']}", help="수정"):
                        st.session_state.edit_item_id = p['id']
                    if st.button("🗑️", key=f"del_{p['id']}", help="삭제"):
                        st.session_state.delete_item_id = p['id']
        
        # 수정 폼
        if st.session_state.edit_item_id:
            item = next((p for p in portfolio if p['id'] == st.session_state.edit_item_id), None)
            if item:
                st.markdown("---")
                st.markdown(f"### ✏️ {item['company']} 수정")
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_amount = st.number_input("투자금액 (억)", 0.0, 500.0, float(item['amount']), 1.0)
                        new_current = st.number_input("현재가치 (억)", 0.0, 500.0, float(item['current_value']), 1.0)
                        new_valuation = st.number_input("기업가치 (억)", 0.0, 2000.0, float(item['valuation']), 10.0)
                    with col2:
                        new_ownership = st.number_input("지분율 (%)", 0.0, 100.0, float(item['ownership']), 0.1)
                        new_milestone = st.text_input("마일스톤", item['milestone'])
                        new_next_event = st.text_input("다음 이벤트", item['next_event'])
                        new_status = st.selectbox("상태", ['active', 'committed', 'exited'], index=['active', 'committed', 'exited'].index(item['status']))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 저장", use_container_width=True):
                            update_portfolio_item(item['id'], {
                                'amount': new_amount, 'current_value': new_current, 'valuation': new_valuation,
                                'ownership': new_ownership, 'milestone': new_milestone, 'next_event': new_next_event, 'status': new_status
                            })
                            st.session_state.edit_item_id = None
                            st.success(f"✅ {item['company']} 수정 완료!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("❌ 취소", use_container_width=True):
                            st.session_state.edit_item_id = None
                            st.rerun()
        
        # 삭제 확인
        if st.session_state.delete_item_id:
            item = next((p for p in portfolio if p['id'] == st.session_state.delete_item_id), None)
            if item:
                st.markdown("---")
                st.warning(f"⚠️ **{item['company']}** 를 삭제하시겠습니까?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ 삭제 확인", type="primary", use_container_width=True):
                        delete_portfolio_item(item['id'])
                        st.session_state.delete_item_id = None
                        st.success(f"✅ {item['company']} 삭제 완료!")
                        st.rerun()
                with col2:
                    if st.button("❌ 취소", use_container_width=True):
                        st.session_state.delete_item_id = None
                        st.rerun()
    
    with tab3:
        st.markdown("### 📊 포트폴리오 분석")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 섹터별 배분")
            sector_data = get_sector_allocation()
            fig_sector = go.Figure(data=[go.Pie(labels=list(sector_data.keys()), values=[d['amount'] for d in sector_data.values()], hole=0.4, marker_colors=['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#f59e0b', '#ef4444'])])
            fig_sector.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(fig_sector, use_container_width=True)
            
            for sector, data in sorted(sector_data.items(), key=lambda x: x[1]['amount'], reverse=True):
                pct = data['amount'] / total_invested * 100
                st.markdown(f'<div class="data-row"><div class="data-row-left"><div class="data-row-title">{sector}</div><div class="data-row-subtitle">{data["count"]}건</div></div><div class="data-row-value">{data["amount"]:,.1f}억 ({pct:.1f}%)</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 투자유형별 배분")
            type_data = get_investment_type_allocation()
            fig_type = go.Figure(data=[go.Bar(x=list(type_data.keys()), y=[d['amount'] for d in type_data.values()], marker_color=['#6366f1', '#f59e0b', '#10b981'], text=[f"{d['amount']:.1f}억" for d in type_data.values()], textposition='outside')])
            fig_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, xaxis=dict(showgrid=False, color='#a1a1aa'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#a1a1aa'), margin=dict(t=50, b=30, l=30, r=30))
            st.plotly_chart(fig_type, use_container_width=True)
            
            type_colors = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}
            for inv_type, data in sorted(type_data.items(), key=lambda x: x[1]['amount'], reverse=True):
                pct = data['amount'] / total_invested * 100
                st.markdown(f'<div class="data-row"><div class="data-row-left"><div class="data-row-title"><span class="badge badge-{type_colors.get(inv_type, "sky")}">{inv_type}</span></div><div class="data-row-subtitle">{data["count"]}건</div></div><div class="data-row-value">{data["amount"]:,.1f}억 ({pct:.1f}%)</div></div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 📅 주요 이벤트 캘린더")
        events = [{'company': p['company'], 'event': p['next_event'], 'milestone': p['milestone'], 'amount': p['amount'], 'type': p['investment_type']} for p in portfolio if p['amount'] > 0 and p['next_event']]
        
        quarters = {'Q1 (1-3월)': [e for e in events if 'Q1' in e['event']], 'Q2 (4-6월)': [e for e in events if 'Q2' in e['event']], 'Q3 (7-9월)': [e for e in events if 'Q3' in e['event']], 'Q4 (10-12월)': [e for e in events if 'Q4' in e['event']], '2026년 이후': [e for e in events if '2026' in e['event']]}
        
        for quarter, quarter_events in quarters.items():
            if quarter_events:
                st.markdown(f"##### {quarter}")
                for e in quarter_events:
                    type_class = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}.get(e['type'], 'sky')
                    st.markdown(f'<div class="data-row"><div class="data-row-left"><div class="data-row-title"><span class="badge badge-{type_class}">{e["type"]}</span> {e["company"]}</div><div class="data-row-subtitle">{e["event"]}</div></div><div style="text-align: right;"><div style="color: var(--text-primary); font-weight: 600;">{e["amount"]:,.1f}억</div><div style="color: var(--text-muted); font-size: 0.75rem;">{e["milestone"]}</div></div></div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### ⚙️ 포트폴리오 관리")
        st.markdown("#### ➕ 신규 투자 등록")
        
        with st.form("new_investment"):
            col1, col2 = st.columns(2)
            with col1:
                new_company = st.text_input("회사명")
                new_sector = st.selectbox("섹터", ["환경/폐기물", "신재생에너지", "수처리", "CCUS", "자원순환", "ESG/SaaS", "수소", "태양광", "풍력", "배터리재활용", "에너지IT", "EV/모빌리티", "기타"])
                new_fund = st.selectbox("펀드", ["미래환경펀드", "IPO 일반사모 1호", "고유계정"])
            with col2:
                new_type = st.selectbox("투자유형", ["RCPS", "CB", "보통주"])
                new_amount = st.number_input("투자금액 (억원)", 0.0, 100.0, 10.0, 1.0)
                new_date = st.date_input("투자일")
            
            col1, col2 = st.columns(2)
            with col1:
                new_valuation = st.number_input("기업가치 (억원)", 0.0, 1000.0, 50.0, 10.0)
            with col2:
                new_ownership = st.number_input("지분율 (%)", 0.0, 100.0, 10.0, 1.0)
            
            new_milestone = st.text_input("마일스톤")
            new_next_event = st.text_input("다음 이벤트")
            
            if st.form_submit_button("📝 등록", use_container_width=True):
                if new_company:
                    new_item = {
                        'company': new_company, 'sector': new_sector, 'fund': new_fund,
                        'account': '고유' if new_fund == '고유계정' else '펀드',
                        'investment_type': new_type, 'investment_date': str(new_date),
                        'amount': new_amount, 'current_value': new_amount,
                        'shares': 0, 'price_per_share': 0, 'valuation': new_valuation,
                        'ownership': new_ownership, 'status': 'active',
                        'milestone': new_milestone, 'next_event': new_next_event
                    }
                    add_portfolio_item(new_item)
                    st.success(f"✅ {new_company} 등록 완료!")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📥 데이터 내보내기")
        col1, col2 = st.columns(2)
        with col1:
            portfolio_df = pd.DataFrame(portfolio)
            csv = portfolio_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📊 포트폴리오 CSV", csv, f"ifam_portfolio_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
        with col2:
            fund_df = pd.DataFrame(funds)
            csv_fund = fund_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("🏦 펀드현황 CSV", csv_fund, f"ifam_funds_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
# =============================================================================
# 메인 앱
# =============================================================================
def main():
    init_session_state()
    load_css()
    render_header()
    
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page = st.radio("메뉴 선택", ["🏠 홈", "🌱 Daily Market", "📊 VC Analyzer", "🏢 LP Discovery", "📈 Portfolio"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown('<div style="color: var(--text-muted); font-size: 0.75rem; text-align: center;">IFAM Dashboard v1.1<br>© 2025 인프라프론티어</div>', unsafe_allow_html=True)
    
    if page == "🏠 홈":
        render_home()
    elif page == "🌱 Daily Market":
        render_daily_market()
    elif page == "📊 VC Analyzer":
        render_vc_analyzer()
    elif page == "🏢 LP Discovery":
        render_lp_discovery()
    elif page == "📈 Portfolio":
        render_portfolio()
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: var(--text-muted); padding: 1rem; font-size: 0.8rem;">🏛️ IFAM 통합 대시보드 v1.1 | 인프라프론티어자산운용(주)<br><small>본 대시보드의 데이터는 참고용이며, 투자 결정 전 원본 데이터를 반드시 확인하세요.</small></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
