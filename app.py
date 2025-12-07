"""
IFAM 통합 대시보드 v1.0
인프라프론티어자산운용(주) - Infra Frontier Asset Management

통합 기능:
1. 🌱 Daily Market - 친환경·인프라 투자 지표
2. 📊 VC Analyzer - Term Sheet 분석 & 밸류에이션
3. 🏢 LP Discovery - Potential LP 발굴 & IPO 캘린더
4. 📈 Portfolio - 통합 포트폴리오 대시보드

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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 전역 설정
# =============================================================================
DART_API_KEY = "d69ac794205d2dce718abfd6a27e4e4e295accae"
DART_BASE_URL = 'https://opendart.fss.or.kr/api'

# =============================================================================
# 통합 CSS 스타일 시스템
# =============================================================================
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
        
        :root {
            /* 다크 테마 색상 팔레트 */
            --bg-primary: #09090b;
            --bg-secondary: #0f0f12;
            --bg-tertiary: #18181b;
            --bg-card: rgba(24, 24, 27, 0.8);
            --bg-hover: rgba(39, 39, 42, 0.8);
            
            /* 보더 & 글라스 */
            --border-subtle: rgba(63, 63, 70, 0.5);
            --border-accent: rgba(99, 102, 241, 0.4);
            --glass-bg: rgba(255, 255, 255, 0.02);
            
            /* 텍스트 색상 */
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            
            /* 액센트 색상 */
            --accent-indigo: #6366f1;
            --accent-violet: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --accent-sky: #0ea5e9;
            
            /* 그라디언트 */
            --gradient-brand: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            --gradient-success: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
            --gradient-danger: linear-gradient(135deg, #f43f5e 0%, #fb7185 100%);
        }
        
        /* 기본 앱 스타일 */
        .stApp {
            background: var(--bg-primary);
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
        }
        
        /* 스크롤바 스타일 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-subtle);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
        
        /* ============================================
           메인 헤더 시스템
           ============================================ */
        .main-header {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }
        
        .header-brand {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .header-logo {
            font-size: 2.5rem;
        }
        
        .header-title {
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        
        .header-subtitle {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 400;
        }
        
        .header-meta {
            display: flex;
            gap: 1.5rem;
            margin-top: 0.75rem;
        }
        
        .header-meta-item {
            color: var(--text-muted);
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        
        /* ============================================
           카드 시스템
           ============================================ */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.25rem;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }
        
        .card:hover {
            border-color: var(--border-accent);
            transform: translateY(-2px);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .card-title {
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
        }
        
        .card-badge {
            background: var(--glass-bg);
            border: 1px solid var(--border-subtle);
            border-radius: 9999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.7rem;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        /* ============================================
           메트릭 카드
           ============================================ */
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }
        
        .metric-card:hover {
            border-color: var(--border-accent);
        }
        
        .metric-label {
            color: var(--text-muted);
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: var(--text-primary);
            font-size: 1.5rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.02em;
        }
        
        .metric-value.large {
            font-size: 2rem;
        }
        
        .metric-change {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.4rem;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
        }
        
        .metric-change.up {
            color: var(--accent-emerald);
            background: rgba(16, 185, 129, 0.1);
        }
        
        .metric-change.down {
            color: var(--accent-rose);
            background: rgba(244, 63, 94, 0.1);
        }
        
        .metric-change.neutral {
            color: var(--text-muted);
            background: var(--glass-bg);
        }
        
        /* ============================================
           데이터 행
           ============================================ */
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
        
        .data-row:hover {
            background: var(--bg-hover);
            border-color: var(--border-accent);
        }
        
        .data-row-left {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }
        
        .data-row-title {
            color: var(--text-primary);
            font-size: 0.95rem;
            font-weight: 600;
        }
        
        .data-row-subtitle {
            color: var(--text-muted);
            font-size: 0.8rem;
        }
        
        .data-row-value {
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* ============================================
           뱃지 시스템
           ============================================ */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        
        .badge-indigo {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        
        .badge-emerald {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .badge-amber {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        
        .badge-rose {
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }
        
        .badge-sky {
            background: rgba(14, 165, 233, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(14, 165, 233, 0.3);
        }
        
        /* ============================================
           섹션 타이틀
           ============================================ */
        .section-title {
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 700;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .section-title .icon {
            font-size: 1.2rem;
        }
        
        /* ============================================
           정보 박스
           ============================================ */
        .info-box {
            background: rgba(99, 102, 241, 0.08);
            border-left: 3px solid var(--accent-indigo);
            padding: 1rem 1.2rem;
            border-radius: 0 10px 10px 0;
            margin: 1rem 0;
        }
        
        .info-box p {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
        
        .info-box strong {
            color: var(--text-primary);
        }
        
        /* ============================================
           탭 스타일 오버라이드
           ============================================ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: var(--bg-secondary);
            padding: 4px;
            border-radius: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            color: var(--text-secondary);
            font-weight: 500;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--gradient-brand);
            color: white;
        }
        
        /* ============================================
           사이드바 스타일
           ============================================ */
        section[data-testid="stSidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-subtle);
        }
        
        section[data-testid="stSidebar"] .stMarkdown h2 {
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 700;
        }
        
        /* ============================================
           버튼 스타일
           ============================================ */
        .stButton > button {
            background: var(--gradient-brand);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        
        /* ============================================
           입력 필드 스타일
           ============================================ */
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-primary);
        }
        
        /* ============================================
           테이블 스타일
           ============================================ */
        .dataframe {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: 10px !important;
        }
        
        /* ============================================
           프로그레스 바
           ============================================ */
        .stProgress > div > div > div > div {
            background: var(--gradient-brand);
        }
        
        /* ============================================
           네비게이션 카드
           ============================================ */
        .nav-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .nav-card:hover {
            border-color: var(--accent-indigo);
            transform: translateY(-4px);
            box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.3);
        }
        
        .nav-card-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }
        
        .nav-card-title {
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        
        .nav-card-desc {
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        
        /* ============================================
           IPO 카드
           ============================================ */
        .ipo-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.75rem;
            transition: all 0.2s ease;
        }
        
        .ipo-card:hover {
            border-color: var(--accent-sky);
        }
        
        .ipo-name {
            color: var(--accent-sky);
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        
        .ipo-detail {
            color: var(--text-secondary);
            font-size: 0.85rem;
            line-height: 1.6;
        }
        
        .ipo-date {
            color: var(--accent-amber);
            font-weight: 600;
        }
        
        .ipo-price {
            color: var(--accent-emerald);
            font-weight: 600;
        }
        
        /* ============================================
           스파크라인
           ============================================ */
        .sparkline-container {
            height: 40px;
            margin-top: 0.5rem;
        }
        
        /* ============================================
           레이아웃 유틸리티
           ============================================ */
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .flex-center {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .gap-1 { gap: 0.5rem; }
        .gap-2 { gap: 1rem; }
        .mt-1 { margin-top: 0.5rem; }
        .mt-2 { margin-top: 1rem; }
        .mb-1 { margin-bottom: 0.5rem; }
        .mb-2 { margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 유틸리티 함수
# =============================================================================
def format_number(value, decimals=0, prefix='', suffix=''):
    """숫자 포맷팅"""
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

def format_currency(value, currency='₩'):
    """통화 포맷팅"""
    if value is None:
        return 'N/A'
    return f"{currency}{value:,.0f}"

def format_percent(value, decimals=2):
    """퍼센트 포맷팅"""
    if value is None:
        return 'N/A'
    return f"{value:.{decimals}f}%"

def get_change_class(change):
    """변화량 CSS 클래스"""
    if change > 0:
        return 'up', '▲'
    elif change < 0:
        return 'down', '▼'
    return 'neutral', '-'

# =============================================================================
# 수학 함수 (VC Analyzer용)
# =============================================================================
def norm_cdf(x):
    """표준정규분포 누적분포함수"""
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)

def black_scholes_call(S, K, T, r, sigma):
    """Black-Scholes 콜옵션"""
    if T <= 0 or sigma <= 0 or S <= 0:
        return max(0, S - K)
    if K <= 0:
        return S
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return max(0, S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2))

def re_option_call(S, K, H, r, sigma):
    """Random Expiration Option"""
    if H <= 0:
        return max(0, S - K)
    total = 0
    for i in range(1, 21):
        t = i * H / 20
        prob = (1 / H) * math.exp(-t / H) * (H / 20)
        total += prob * black_scholes_call(S, K, t, r, sigma)
    return total * H

# =============================================================================
# 데이터 클래스 (VC Analyzer용)
# =============================================================================
@dataclass
class InvestmentRound:
    name: str
    investment: float  # 억원
    shares: float  # 만주
    is_participating: bool = True
    liquidation_multiple: float = 1.0
    seniority: int = 1

@dataclass
class GlobalInput:
    founder_shares: float = 100.0  # 만주
    current_valuation: float = 100.0  # 억원
    exit_valuation: float = 500.0  # 억원
    volatility: float = 90.0  # %
    risk_free_rate: float = 3.0  # %
    holding_period: float = 5.0  # 년

@dataclass
class FundInfo:
    committed_capital: float = 1000.0  # 억원
    management_fee_rate: float = 2.0  # %
    carried_interest: float = 20.0  # %
    hurdle_rate: float = 8.0  # %

# =============================================================================
# 크롤링 함수들 - Daily Market
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_exchange_rates():
    """환율 정보 크롤링"""
    try:
        url = 'https://finance.naver.com/marketindex/'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rates = {}
        exchange_list = soup.find('div', {'id': 'exchangeList'})
        if exchange_list:
            items = exchange_list.find_all('li')
            for item in items:
                try:
                    title = item.find('h3', class_='h_lst')
                    if not title:
                        continue
                    name = title.get_text(strip=True)
                    value_tag = item.find('span', class_='value')
                    change_tag = item.find('span', class_='change')
                    blind_tag = item.find('span', class_='blind')
                    
                    if value_tag:
                        value = float(value_tag.get_text(strip=True).replace(',', ''))
                        change = 0
                        direction = 'neutral'
                        
                        if change_tag:
                            try:
                                change = float(change_tag.get_text(strip=True).replace(',', ''))
                            except:
                                pass
                        
                        if blind_tag:
                            blind_text = blind_tag.get_text(strip=True)
                            if '상승' in blind_text:
                                direction = 'up'
                            elif '하락' in blind_text:
                                direction = 'down'
                                change = -abs(change)
                        
                        if '달러' in name or 'USD' in name:
                            rates['USD'] = {'value': value, 'change': change, 'direction': direction, 'name': '미국 달러'}
                        elif '엔' in name or 'JPY' in name:
                            rates['JPY'] = {'value': value, 'change': change, 'direction': direction, 'name': '일본 엔(100)'}
                        elif '유로' in name or 'EUR' in name:
                            rates['EUR'] = {'value': value, 'change': change, 'direction': direction, 'name': '유로'}
                        elif '위안' in name or 'CNY' in name:
                            rates['CNY'] = {'value': value, 'change': change, 'direction': direction, 'name': '중국 위안'}
                except:
                    continue
        return rates if rates else None
    except:
        return None

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
        return prices if prices else {'WTI': {'value': 68.5, 'change': 0.5}, 'Brent': {'value': 72.3, 'change': 0.3}, 'Dubai': {'value': 70.1, 'change': 0.2}}
    except:
        return {'WTI': {'value': 68.5, 'change': 0.5}, 'Brent': {'value': 72.3, 'change': 0.3}, 'Dubai': {'value': 70.1, 'change': 0.2}}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_data():
    """통합 시장 데이터"""
    return {
        'rec': {'mainland': {'price': 72303, 'change': -35, 'volume': 12534}, 'jeju': {'price': 63904, 'change': -8783, 'volume': 6}},
        'smp': {'mainland': {'price': 110.52, 'change': 2.3}, 'jeju': {'price': 95.17, 'change': -1.5}},
        'gas': {'tanker': 23.45, 'fuel_cell': 19.72},
        'rates': {
            'call': {'value': 3.00, 'change': 0.00},
            'cd_91': {'value': 3.15, 'change': -0.02},
            'treasury_3y': {'value': 2.85, 'change': 0.03},
            'treasury_10y': {'value': 3.05, 'change': 0.01},
            'corp_aa_3y': {'value': 3.45, 'change': 0.02}
        }
    }

# =============================================================================
# 크롤링 함수들 - LP Discovery
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
                if '공모' in decoded or '청약' in decoded or '상장' in decoded:
                    return decoded
            except:
                continue
        return content_bytes.decode('euc-kr', errors='replace')
    except:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_subscription():
    """IPO 청약 일정"""
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
                        'listing_date': cells[7].get_text(strip=True),
                        'competition': cells[8].get_text(strip=True),
                        'underwriter': cells[9].get_text(strip=True)
                    })
                except:
                    continue
        return results
    except:
        return []

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
                result['retained_earnings'] = float(val) / 1e8 if val else None
                break
            except:
                pass
    
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
    
    return result

# =============================================================================
# 이하 Part 2에서 계속
# =============================================================================
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
# 메인 앱 - 모듈별 페이지
# =============================================================================

def render_header():
    """통합 헤더"""
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
            <span class="header-meta-item">📊 v1.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_home():
    """홈 페이지"""
    st.markdown('<p class="section-title"><span class="icon">🏠</span> 대시보드 홈</p>', unsafe_allow_html=True)
    
    # 포트폴리오 요약 (실제 데이터)
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
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-indigo);">
            <div class="metric-label">총 AUM</div>
            <div class="metric-value large">{total_aum:,.1f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {len(funds)}개 운용</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-emerald);">
            <div class="metric-label">투자집행</div>
            <div class="metric-value large">{total_invested:,.2f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem;">집행률 {total_invested/total_aum*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-amber);">
            <div class="metric-label">투자건수</div>
            <div class="metric-value large">{total_investments}건</div>
            <div style="color: var(--text-muted); font-size: 0.75rem;">펀드 {fund_count} / 고유 {prop_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-violet);">
            <div class="metric-label">미회수자산</div>
            <div class="metric-value large">{total_invested:,.2f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem;">회수 0건 | MOIC 1.0x</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 네비게이션 카드
    st.markdown("### 🧭 바로가기")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-card-icon">🌱</div>
            <div class="nav-card-title">Daily Market</div>
            <div class="nav-card-desc">친환경·인프라 투자 지표</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-card-icon">📊</div>
            <div class="nav-card-title">VC Analyzer</div>
            <div class="nav-card-desc">Term Sheet 분석</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-card-icon">🏢</div>
            <div class="nav-card-title">LP Discovery</div>
            <div class="nav-card-desc">LP 발굴 & IPO</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-card-icon">📈</div>
            <div class="nav-card-title">Portfolio</div>
            <div class="nav-card-desc">통합 포트폴리오</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 주요 지표 요약
    st.markdown('<p class="section-title"><span class="icon">📊</span> 오늘의 주요 지표</p>', unsafe_allow_html=True)
    
    exchange_rates = fetch_exchange_rates()
    oil_prices = fetch_oil_prices()
    market_data = fetch_market_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if exchange_rates and 'USD' in exchange_rates:
        usd = exchange_rates['USD']
        cls, arrow = get_change_class(usd['change'])
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">USD/KRW</div>
                <div class="metric-value">{usd['value']:,.2f}</div>
                <div class="metric-change {cls}">{arrow} {abs(usd['change']):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    if oil_prices and 'WTI' in oil_prices:
        wti = oil_prices['WTI']
        cls, arrow = get_change_class(wti['change'])
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">WTI 유가</div>
                <div class="metric-value">${wti['value']:.2f}</div>
                <div class="metric-change {cls}">{arrow} ${abs(wti['change']):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    rec = market_data['rec']['mainland']
    cls, arrow = get_change_class(rec['change'])
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">REC 가격 (육지)</div>
            <div class="metric-value">{rec['price']:,}원</div>
            <div class="metric-change {cls}">{arrow} {abs(rec['change']):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    treasury = market_data['rates']['treasury_3y']
    cls, arrow = get_change_class(treasury['change'])
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">국고채 3년</div>
            <div class="metric-value">{treasury['value']:.2f}%</div>
            <div class="metric-change {cls}">{arrow} {abs(treasury['change']):.2f}%p</div>
        </div>
        """, unsafe_allow_html=True)
    
    # IPO 일정 요약
    st.markdown('<p class="section-title"><span class="icon">📅</span> 금주 IPO 일정</p>', unsafe_allow_html=True)
    
    ipo_data = fetch_ipo_subscription()
    if ipo_data:
        for item in ipo_data[:5]:
            is_ongoing = item.get('competition', '-') == '-'
            st.markdown(f"""
            <div class="data-row">
                <div class="data-row-left">
                    <div class="data-row-title">
                        <span class="badge badge-{'rose' if is_ongoing else 'emerald'}">{'청약중' if is_ongoing else '완료'}</span>
                        {item['company']}
                    </div>
                    <div class="data-row-subtitle">청약: {item['subscription_date']} | 상장: {item['listing_date']}</div>
                </div>
                <div class="data-row-value">{item['offer_price']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("IPO 일정을 불러오는 중...")

def render_daily_market():
    """Daily Market 페이지"""
    st.markdown('<p class="section-title"><span class="icon">🌱</span> Daily Market - 친환경·인프라 지표</p>', unsafe_allow_html=True)
    
    # 환율
    st.markdown("#### 💱 환율")
    exchange_rates = fetch_exchange_rates()
    
    if exchange_rates:
        cols = st.columns(4)
        currencies = ['USD', 'JPY', 'EUR', 'CNY']
        
        for i, code in enumerate(currencies):
            if code in exchange_rates:
                data = exchange_rates[code]
                cls, arrow = get_change_class(data['change'])
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{data.get('name', code)}</div>
                        <div class="metric-value">{data['value']:,.2f}</div>
                        <div class="metric-change {cls}">{arrow} {abs(data['change']):.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 신재생에너지
    st.markdown("#### ⚡ 신재생에너지")
    market_data = fetch_market_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### REC (신재생에너지공급인증서)")
        rec = market_data['rec']
        
        c1, c2 = st.columns(2)
        with c1:
            cls, arrow = get_change_class(rec['mainland']['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">육지 REC</div>
                <div class="metric-value">{rec['mainland']['price']:,}원</div>
                <div class="metric-change {cls}">{arrow} {abs(rec['mainland']['change']):,}</div>
                <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                    거래량: {rec['mainland']['volume']:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            cls, arrow = get_change_class(rec['jeju']['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">제주 REC</div>
                <div class="metric-value">{rec['jeju']['price']:,}원</div>
                <div class="metric-change {cls}">{arrow} {abs(rec['jeju']['change']):,}</div>
                <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                    거래량: {rec['jeju']['volume']:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("##### SMP (계통한계가격)")
        smp = market_data['smp']
        
        c1, c2 = st.columns(2)
        with c1:
            cls, arrow = get_change_class(smp['mainland']['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">육지 SMP</div>
                <div class="metric-value">{smp['mainland']['price']:.2f}</div>
                <div style="color: var(--text-muted); font-size: 0.8rem;">원/kWh</div>
                <div class="metric-change {cls}">{arrow} {abs(smp['mainland']['change']):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            cls, arrow = get_change_class(smp['jeju']['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">제주 SMP</div>
                <div class="metric-value">{smp['jeju']['price']:.2f}</div>
                <div style="color: var(--text-muted); font-size: 0.8rem;">원/kWh</div>
                <div class="metric-change {cls}">{arrow} {abs(smp['jeju']['change']):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 국제유가
    st.markdown("#### 🛢️ 국제유가")
    oil_prices = fetch_oil_prices()
    
    cols = st.columns(3)
    oils = [('WTI', '서부텍사스'), ('Brent', '북해 브렌트'), ('Dubai', '두바이')]
    
    for i, (code, name) in enumerate(oils):
        if code in oil_prices:
            data = oil_prices[code]
            cls, arrow = get_change_class(data['change'])
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{name}</div>
                    <div class="metric-value">${data['value']:.2f}</div>
                    <div class="metric-change {cls}">{arrow} ${abs(data['change']):.2f}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 금리
    st.markdown("#### 📊 금리")
    rates = market_data['rates']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 단기금리")
        c1, c2 = st.columns(2)
        with c1:
            data = rates['call']
            cls, arrow = get_change_class(data['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">콜금리 (1일)</div>
                <div class="metric-value">{data['value']:.2f}%</div>
                <div class="metric-change {cls}">{arrow} {abs(data['change']):.2f}%p</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            data = rates['cd_91']
            cls, arrow = get_change_class(data['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CD (91일)</div>
                <div class="metric-value">{data['value']:.2f}%</div>
                <div class="metric-change {cls}">{arrow} {abs(data['change']):.2f}%p</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("##### 국고채/회사채")
        c1, c2 = st.columns(2)
        with c1:
            data = rates['treasury_3y']
            cls, arrow = get_change_class(data['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">국고채 (3년)</div>
                <div class="metric-value">{data['value']:.2f}%</div>
                <div class="metric-change {cls}">{arrow} {abs(data['change']):.2f}%p</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            data = rates['corp_aa_3y']
            cls, arrow = get_change_class(data['change'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">회사채 AA- (3년)</div>
                <div class="metric-value">{data['value']:.2f}%</div>
                <div class="metric-change {cls}">{arrow} {abs(data['change']):.2f}%p</div>
            </div>
            """, unsafe_allow_html=True)

def render_vc_analyzer():
    """VC Analyzer 페이지"""
    st.markdown('<p class="section-title"><span class="icon">📊</span> VC Term Sheet Analyzer</p>', unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'vc_rounds' not in st.session_state:
        st.session_state.vc_rounds = [
            InvestmentRound("Series A", 30.0, 15.0, True, 1.0, 1),
            InvestmentRound("Series B", 80.0, 20.0, True, 1.0, 2),
        ]
    if 'vc_global' not in st.session_state:
        st.session_state.vc_global = GlobalInput()
    if 'vc_fund' not in st.session_state:
        st.session_state.vc_fund = FundInfo()
    
    # 사이드바 입력
    with st.sidebar:
        st.markdown("### 📝 투자 조건")
        
        st.markdown("#### 👤 창업자 정보")
        founder_shares = st.number_input("창업자 보통주 (만주)", 1.0, 1000.0, 
                                          value=float(st.session_state.vc_global.founder_shares), step=10.0)
        st.session_state.vc_global.founder_shares = founder_shares
        
        st.markdown("#### 💰 기업가치")
        current_val = st.number_input("현재 가치 (억원)", 10.0, 10000.0,
                                       value=float(st.session_state.vc_global.current_valuation), step=10.0)
        exit_val = st.number_input("Exit 가치 (억원)", 50.0, 50000.0,
                                    value=float(st.session_state.vc_global.exit_valuation), step=50.0)
        st.session_state.vc_global.current_valuation = current_val
        st.session_state.vc_global.exit_valuation = exit_val
        
        st.markdown("#### 📈 옵션 파라미터")
        volatility = st.slider("변동성 (%)", 30, 150, int(st.session_state.vc_global.volatility))
        risk_free = st.slider("무위험이자율 (%)", 1.0, 10.0, st.session_state.vc_global.risk_free_rate, 0.5)
        holding = st.slider("보유기간 (년)", 1, 10, int(st.session_state.vc_global.holding_period))
        
        st.session_state.vc_global.volatility = volatility
        st.session_state.vc_global.risk_free_rate = risk_free
        st.session_state.vc_global.holding_period = holding
        
        st.markdown("#### 🏦 펀드 정보")
        committed = st.number_input("약정총액 (억원)", 100.0, 10000.0, 
                                     value=float(st.session_state.vc_fund.committed_capital), step=100.0)
        mgmt_fee = st.number_input("관리보수 (%)", 1.0, 3.0, 
                                    value=float(st.session_state.vc_fund.management_fee_rate), step=0.1)
        carry = st.number_input("성과보수 (%)", 10.0, 30.0,
                                 value=float(st.session_state.vc_fund.carried_interest), step=1.0)
        hurdle = st.number_input("허들레이트 (%)", 0.0, 15.0,
                                  value=float(st.session_state.vc_fund.hurdle_rate), step=1.0)
        
        st.session_state.vc_fund.committed_capital = committed
        st.session_state.vc_fund.management_fee_rate = mgmt_fee
        st.session_state.vc_fund.carried_interest = carry
        st.session_state.vc_fund.hurdle_rate = hurdle
    
    # 투자 라운드 입력
    st.markdown("### 💼 투자 라운드")
    
    num_rounds = st.number_input("라운드 수", 1, 6, len(st.session_state.vc_rounds))
    
    while len(st.session_state.vc_rounds) < num_rounds:
        idx = len(st.session_state.vc_rounds)
        st.session_state.vc_rounds.append(
            InvestmentRound(f"Series {chr(65+idx)}", 50.0, 10.0, True, 1.0, idx+1)
        )
    while len(st.session_state.vc_rounds) > num_rounds:
        st.session_state.vc_rounds.pop()
    
    cols = st.columns(min(num_rounds, 3))
    for i, r in enumerate(st.session_state.vc_rounds):
        with cols[i % 3]:
            with st.expander(f"📌 {r.name}", expanded=True):
                r.investment = st.number_input(f"투자금액 (억원)", 1.0, 1000.0, 
                                                value=float(r.investment), step=10.0, key=f"inv_{i}")
                r.shares = st.number_input(f"배정주식 (만주)", 1.0, 500.0,
                                            value=float(r.shares), step=5.0, key=f"shares_{i}")
                r.is_participating = st.checkbox("참가 우선주", value=r.is_participating, key=f"part_{i}")
                r.liquidation_multiple = st.selectbox("청산배수", [1.0, 1.5, 2.0, 3.0], 
                                                       index=[1.0, 1.5, 2.0, 3.0].index(r.liquidation_multiple), 
                                                       key=f"liq_{i}")
    
    st.markdown("---")
    
    # RVPS 분석
    st.markdown("### 📊 RVPS 분석 (전환순서)")
    
    rvps_data = calculate_rvps(st.session_state.vc_rounds, st.session_state.vc_global.founder_shares)
    
    df_rvps = pd.DataFrame(rvps_data)
    df_rvps['투자금액'] = df_rvps['investment'].apply(lambda x: f"{x:,.0f}억")
    df_rvps['지분율'] = df_rvps['ownership'].apply(lambda x: f"{x:.1f}%")
    df_rvps['RVPS'] = df_rvps['rvps'].apply(lambda x: f"{x:,.2f}억/만주")
    df_rvps['유형'] = df_rvps['participating'].apply(lambda x: '참가' if x else '비참가/보통주')
    
    st.dataframe(
        df_rvps[['name', '투자금액', '지분율', 'RVPS', '유형']].rename(columns={'name': '라운드'}),
        use_container_width=True,
        hide_index=True
    )
    
    # Exit Diagram
    st.markdown("### 📈 Exit Diagram (Payoff Schedule)")
    
    exit_values = np.linspace(0, st.session_state.vc_global.exit_valuation * 1.5, 100)
    payoffs = calculate_exit_payoffs(st.session_state.vc_rounds, 
                                      st.session_state.vc_global.founder_shares, exit_values)
    
    fig = go.Figure()
    colors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#10b981']
    
    for i, (name, values) in enumerate(payoffs.items()):
        fig.add_trace(go.Scatter(
            x=exit_values, y=values,
            name=name,
            mode='lines',
            line=dict(width=2, color=colors[i % len(colors)]),
            fill='tonexty' if i > 0 else None
        ))
    
    fig.update_layout(
        title='Exit Value별 수익 분배',
        xaxis_title='Exit Value (억원)',
        yaxis_title='수익 (억원)',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # GP/LP 분배
    st.markdown("### 💰 GP/LP 수익 분배")
    
    total_investment = sum(r.investment for r in st.session_state.vc_rounds)
    total_shares = st.session_state.vc_global.founder_shares + sum(r.shares for r in st.session_state.vc_rounds)
    inv_shares = sum(r.shares for r in st.session_state.vc_rounds)
    
    partial_val = st.session_state.vc_global.exit_valuation * (inv_shares / total_shares) if total_shares > 0 else 0
    
    split = calculate_gp_lp_split(partial_val, st.session_state.vc_fund, total_investment)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LP 투자비용</div>
            <div class="metric-value">{split['lp_cost']:.1f}억</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">GP Carry</div>
            <div class="metric-value">{split['gp_carry']:.1f}억</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LP 수령액</div>
            <div class="metric-value">{split['lp_val']:.1f}억</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LP Multiple</div>
            <div class="metric-value">{split['lp_multiple']:.2f}x</div>
        </div>
        """, unsafe_allow_html=True)

def render_lp_discovery():
    """LP Discovery 페이지"""
    st.markdown('<p class="section-title"><span class="icon">🏢</span> LP Discovery & IPO 캘린더</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📅 IPO 일정", "🔍 LP 발굴"])
    
    with tab1:
        st.markdown("### 📅 IPO 청약 일정")
        
        ipo_data = fetch_ipo_subscription()
        
        if ipo_data:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label">현재 IPO 일정</div>
                <div class="metric-value large">{len(ipo_data)}건</div>
            </div>
            """, unsafe_allow_html=True)
            
            for item in ipo_data[:15]:
                is_ongoing = item.get('competition', '-') == '-'
                badge_class = 'rose' if is_ongoing else 'emerald'
                badge_text = '청약중' if is_ongoing else '완료'
                
                st.markdown(f"""
                <div class="ipo-card">
                    <div class="ipo-name">
                        <span class="badge badge-{badge_class}">{badge_text}</span>
                        {item['company']}
                    </div>
                    <div class="ipo-detail">
                        📅 청약일: <span class="ipo-date">{item['subscription_date']}</span> |
                        💰 공모가: <span class="ipo-price">{item['offer_price']}</span><br>
                        📊 공모금액: {item['offer_amount']} | 경쟁률: {item['competition']}<br>
                        🏢 주간사: {item['underwriter']} | 상장일: {item['listing_date']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("IPO 일정을 불러오는 중...")
    
    with tab2:
        st.markdown("### 🔍 Potential LP 발굴")
        
        # 세션 상태 초기화
        if 'lp_corp_list' not in st.session_state:
            st.session_state.lp_corp_list = None
        if 'lp_data' not in st.session_state:
            st.session_state.lp_data = pd.DataFrame()
        if 'lp_idx' not in st.session_state:
            st.session_state.lp_idx = 0
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            bsns_year = st.selectbox("사업연도", ['2024', '2023', '2022'], index=0)
            min_re = st.number_input("최소 이익잉여금 (억원)", 0, 10000, 300, 100)
        
        with col2:
            batch_size = st.selectbox("배치 크기", [30, 50, 100], index=1)
        
        if st.session_state.lp_corp_list is None:
            st.markdown("""
            <div class="info-box">
                <p><strong>💡 사용법</strong><br>
                1. "기업 목록 불러오기" 클릭<br>
                2. "다음 배치 조회"로 50개씩 조회<br>
                3. CSV 다운로드</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📥 기업 목록 불러오기", type="primary", use_container_width=True):
                with st.spinner("다운로드 중..."):
                    corp_df = get_corp_code_list()
                if corp_df is not None:
                    st.session_state.lp_corp_list = corp_df
                    st.success(f"✅ {len(corp_df)}개 기업 로드!")
                    st.rerun()
        else:
            total = len(st.session_state.lp_corp_list)
            current_idx = st.session_state.lp_idx
            
            st.progress(current_idx / total if total > 0 else 0)
            st.caption(f"진행률: {current_idx}/{total} ({current_idx/total*100:.1f}%) | LP 후보: {len(st.session_state.lp_data)}개")
            
            if current_idx < total:
                if st.button(f"⏭️ 다음 {batch_size}개 조회", type="primary", use_container_width=True):
                    end_idx = min(current_idx + batch_size, total)
                    batch = st.session_state.lp_corp_list.iloc[current_idx:end_idx]
                    
                    results = []
                    progress_bar = st.progress(0)
                    
                    for i, row in enumerate(batch.itertuples()):
                        progress_bar.progress((i + 1) / len(batch))
                        fs_df = get_financial_statement(row.corp_code, bsns_year)
                        fin_data = extract_financial_data(fs_df)
                        
                        if fin_data['retained_earnings'] is not None:
                            results.append({
                                'corp_code': row.corp_code,
                                'corp_name': row.corp_name,
                                'stock_code': row.stock_code,
                                **fin_data
                            })
                        time.sleep(0.2)
                    
                    if results:
                        new_df = pd.DataFrame(results)
                        if st.session_state.lp_data.empty:
                            st.session_state.lp_data = new_df
                        else:
                            st.session_state.lp_data = pd.concat([st.session_state.lp_data, new_df], ignore_index=True)
                    
                    st.session_state.lp_idx = end_idx
                    st.rerun()
            
            # 결과 표시
            if not st.session_state.lp_data.empty:
                df = st.session_state.lp_data.copy()
                df_filtered = df[df['retained_earnings'] >= min_re].copy()
                df_filtered = df_filtered.sort_values('retained_earnings', ascending=False)
                
                st.markdown(f"### LP 후보 ({min_re}억 이상): {len(df_filtered)}개")
                
                for _, row in df_filtered.head(15).iterrows():
                    st.markdown(f"""
                    <div class="data-row">
                        <div class="data-row-left">
                            <div class="data-row-title">{row['corp_name']}</div>
                            <div class="data-row-subtitle">{row['stock_code']}</div>
                        </div>
                        <div class="data-row-value">{format_number(row['retained_earnings'], 0)}원</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 CSV 다운로드", csv, f"lp_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# =============================================================================
# 포트폴리오 데이터 정의
# =============================================================================
def get_fund_data():
    """펀드 정보"""
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
            'committed': 775.0,
            'called': 360.18,
            'distributed': 0,
            'nav': 360.18,
            'investments': 12
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
            'committed': 84.5,
            'called': 0,
            'distributed': 0,
            'nav': 0,
            'investments': 0
        }
    ]

def get_portfolio_data():
    """포트폴리오 투자 현황"""
    return [
        # 펀드 계정 투자 (미래환경펀드)
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
        # 고유계정 투자
        {'id': 13, 'company': '친환경모빌리티', 'sector': 'EV/모빌리티', 'fund': '고유계정', 'account': '고유',
         'investment_type': 'RCPS', 'investment_date': '2024-02-10', 'amount': 0, 'current_value': 0,
         'shares': 0, 'price_per_share': 0, 'valuation': 0, 'ownership': 0, 'status': 'committed',
         'milestone': 'Due Diligence 완료', 'next_event': '투자 검토 중'},
        {'id': 14, 'company': '그린빌딩', 'sector': '건설/에너지효율', 'fund': '고유계정', 'account': '고유',
         'investment_type': 'CB', 'investment_date': '2024-03-20', 'amount': 0, 'current_value': 0,
         'shares': 0, 'price_per_share': 0, 'valuation': 0, 'ownership': 0, 'status': 'committed',
         'milestone': 'MOU 체결', 'next_event': '구조화 진행 중'},
    ]

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

def render_portfolio():
    """Portfolio 페이지 - 완전 개발 버전"""
    st.markdown('<p class="section-title"><span class="icon">📈</span> 통합 포트폴리오 관리</p>', unsafe_allow_html=True)
    
    # 데이터 로드
    funds = get_fund_data()
    portfolio = get_portfolio_data()
    
    # 핵심 지표 계산
    total_aum = sum(f['aum'] for f in funds)
    total_investments = len([p for p in portfolio if p['amount'] > 0])
    total_invested = sum(p['amount'] for p in portfolio)
    total_current_value = sum(p['current_value'] for p in portfolio)
    fund_investments = len([p for p in portfolio if p['account'] == '펀드' and p['amount'] > 0])
    proprietary_investments = len([p for p in portfolio if p['account'] == '고유'])
    exits = len([p for p in portfolio if p['status'] == 'exited'])
    moic = total_current_value / total_invested if total_invested > 0 else 0
    
    # =========================================================================
    # 1. 핵심 KPI 대시보드
    # =========================================================================
    st.markdown("### 📊 핵심 KPI")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-indigo);">
            <div class="metric-label">총 운용자산 (AUM)</div>
            <div class="metric-value large">{total_aum:,.1f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                펀드 {len(funds)}개 운용 중
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-emerald);">
            <div class="metric-label">총 투자집행</div>
            <div class="metric-value large">{total_invested:,.2f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                투자비율 {total_invested/total_aum*100:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-amber);">
            <div class="metric-label">총 투자 건수</div>
            <div class="metric-value large">{total_investments}건</div>
            <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                펀드 {fund_investments} / 고유 {proprietary_investments}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid var(--accent-violet);">
            <div class="metric-label">미회수자산 가치</div>
            <div class="metric-value large">{total_current_value:,.2f}억</div>
            <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.3rem;">
                MOIC {moic:.2f}x | 회수 {exits}건
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # =========================================================================
    # 2. 탭 구조
    # =========================================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏦 펀드 현황", "💼 포트폴리오", "📊 분석", "📅 이벤트", "⚙️ 관리"
    ])
    
    # =========================================================================
    # Tab 1: 펀드 현황
    # =========================================================================
    with tab1:
        st.markdown("### 🏦 운용 펀드 현황")
        
        for fund in funds:
            # 펀드별 투자 건수 계산
            fund_portfolio = [p for p in portfolio if p['fund'] == fund['name'] and p['amount'] > 0]
            fund_invested = sum(p['amount'] for p in fund_portfolio)
            
            # 진행률 계산
            deployment_ratio = fund_invested / fund['aum'] * 100 if fund['aum'] > 0 else 0
            
            # 상태 배지
            status_class = 'emerald' if fund['status'] == 'active' else 'amber'
            status_text = '운용중' if fund['status'] == 'active' else '대기'
            
            st.markdown(f"""
            <div class="card" style="margin-bottom: 1rem;">
                <div class="card-header">
                    <div class="card-title">
                        <span class="badge badge-{status_class}" style="margin-right: 0.5rem;">{status_text}</span>
                        {fund['name']}
                    </div>
                    <div class="card-badge">Vintage {fund['vintage']}</div>
                </div>
                <div style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">
                    {fund['full_name']}
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.7rem;">약정총액</div>
                        <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600; font-family: 'JetBrains Mono';">{fund['aum']:,.1f}억</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.7rem;">투자집행</div>
                        <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600; font-family: 'JetBrains Mono';">{fund_invested:,.2f}억</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.7rem;">투자건수</div>
                        <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 600; font-family: 'JetBrains Mono';">{len(fund_portfolio)}건</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.7rem;">집행률</div>
                        <div style="color: var(--accent-emerald); font-size: 1.1rem; font-weight: 600; font-family: 'JetBrains Mono';">{deployment_ratio:.1f}%</div>
                    </div>
                </div>
                <div style="margin-top: 1rem;">
                    <div style="background: var(--bg-secondary); border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: var(--gradient-brand); height: 100%; width: {deployment_ratio}%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div style="display: flex; gap: 2rem; margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">
                    <span>📅 투자기간: {fund['investment_period']}</span>
                    <span>🏢 GP: {', '.join(fund['gp'])}</span>
                    <span>💰 LP: {fund['lp']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 잔여 투자여력
        remaining = total_aum - total_invested
        st.markdown(f"""
        <div class="info-box">
            <p><strong>💰 잔여 투자여력</strong><br>
            총 약정 {total_aum:,.1f}억 - 투자집행 {total_invested:,.2f}억 = <strong style="color: var(--accent-emerald);">{remaining:,.2f}억</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # Tab 2: 포트폴리오 상세
    # =========================================================================
    with tab2:
        st.markdown("### 💼 포트폴리오 상세 현황")
        
        # 필터
        col1, col2, col3 = st.columns(3)
        with col1:
            fund_filter = st.selectbox("펀드", ["전체"] + [f['name'] for f in funds] + ["고유계정"])
        with col2:
            type_filter = st.selectbox("투자유형", ["전체", "RCPS", "CB", "보통주"])
        with col3:
            status_filter = st.selectbox("상태", ["전체", "active", "committed", "exited"])
        
        # 필터 적용
        filtered = portfolio
        if fund_filter != "전체":
            filtered = [p for p in filtered if p['fund'] == fund_filter]
        if type_filter != "전체":
            filtered = [p for p in filtered if p['investment_type'] == type_filter]
        if status_filter != "전체":
            filtered = [p for p in filtered if p['status'] == status_filter]
        
        st.markdown(f"**{len(filtered)}개** 투자건")
        
        # 포트폴리오 카드
        for p in filtered:
            if p['amount'] > 0:
                type_class = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}.get(p['investment_type'], 'sky')
                status_class = {'active': 'emerald', 'committed': 'amber', 'exited': 'rose'}.get(p['status'], 'sky')
                status_text = {'active': '투자중', 'committed': '검토중', 'exited': '회수완료'}.get(p['status'], p['status'])
                
                unrealized_gain = p['current_value'] - p['amount']
                gain_class = 'up' if unrealized_gain >= 0 else 'down'
                gain_arrow = '▲' if unrealized_gain >= 0 else '▼'
                
                st.markdown(f"""
                <div class="card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                                <span class="badge badge-{type_class}">{p['investment_type']}</span>
                                <span class="badge badge-{status_class}">{status_text}</span>
                                <span style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700;">{p['company']}</span>
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">
                                {p['sector']} | {p['fund']} | {p['investment_date']}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: var(--text-primary); font-size: 1.2rem; font-weight: 700; font-family: 'JetBrains Mono';">
                                {p['amount']:,.1f}억
                            </div>
                            <div class="metric-change {gain_class}" style="display: inline-block;">
                                {gain_arrow} {abs(unrealized_gain):,.2f}억
                            </div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.65rem;">기업가치</div>
                            <div style="color: var(--text-secondary); font-size: 0.85rem; font-family: 'JetBrains Mono';">{p['valuation']:,.0f}억</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.65rem;">지분율</div>
                            <div style="color: var(--text-secondary); font-size: 0.85rem; font-family: 'JetBrains Mono';">{p['ownership']:.1f}%</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.65rem;">MOIC</div>
                            <div style="color: var(--accent-emerald); font-size: 0.85rem; font-family: 'JetBrains Mono';">{p['current_value']/p['amount']:.2f}x</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.65rem;">마일스톤</div>
                            <div style="color: var(--text-secondary); font-size: 0.8rem;">{p['milestone']}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.65rem;">다음 이벤트</div>
                            <div style="color: var(--accent-amber); font-size: 0.8rem;">{p['next_event']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 검토중 건
                st.markdown(f"""
                <div class="card" style="margin-bottom: 0.75rem; opacity: 0.7;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span class="badge badge-amber">검토중</span>
                                <span style="color: var(--text-primary); font-size: 1rem; font-weight: 600;">{p['company']}</span>
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">{p['sector']} | {p['fund']}</div>
                        </div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">{p['milestone']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # =========================================================================
    # Tab 3: 분석
    # =========================================================================
    with tab3:
        st.markdown("### 📊 포트폴리오 분석")
        
        col1, col2 = st.columns(2)
        
        # 섹터별 배분
        with col1:
            st.markdown("#### 섹터별 배분")
            sector_data = get_sector_allocation()
            
            # Pie Chart
            fig_sector = go.Figure(data=[go.Pie(
                labels=list(sector_data.keys()),
                values=[d['amount'] for d in sector_data.values()],
                hole=0.4,
                marker_colors=['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', 
                               '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#f59e0b', '#ef4444'],
                textposition='inside',
                textinfo='percent+label'
            )])
            fig_sector.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig_sector, use_container_width=True)
            
            # 섹터 상세
            for sector, data in sorted(sector_data.items(), key=lambda x: x[1]['amount'], reverse=True):
                pct = data['amount'] / total_invested * 100
                st.markdown(f"""
                <div class="data-row">
                    <div class="data-row-left">
                        <div class="data-row-title">{sector}</div>
                        <div class="data-row-subtitle">{data['count']}건</div>
                    </div>
                    <div class="data-row-value">{data['amount']:,.1f}억 ({pct:.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
        
        # 투자유형별 배분
        with col2:
            st.markdown("#### 투자유형별 배분")
            type_data = get_investment_type_allocation()
            
            # Bar Chart
            fig_type = go.Figure(data=[go.Bar(
                x=list(type_data.keys()),
                y=[d['amount'] for d in type_data.values()],
                marker_color=['#6366f1', '#f59e0b', '#10b981'],
                text=[f"{d['amount']:.1f}억" for d in type_data.values()],
                textposition='outside'
            )])
            fig_type.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                xaxis=dict(showgrid=False, color='#a1a1aa'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#a1a1aa'),
                margin=dict(t=50, b=30, l=30, r=30)
            )
            st.plotly_chart(fig_type, use_container_width=True)
            
            # 투자유형 상세
            type_colors = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}
            for inv_type, data in sorted(type_data.items(), key=lambda x: x[1]['amount'], reverse=True):
                pct = data['amount'] / total_invested * 100
                st.markdown(f"""
                <div class="data-row">
                    <div class="data-row-left">
                        <div class="data-row-title">
                            <span class="badge badge-{type_colors.get(inv_type, 'sky')}">{inv_type}</span>
                        </div>
                        <div class="data-row-subtitle">{data['count']}건</div>
                    </div>
                    <div class="data-row-value">{data['amount']:,.1f}억 ({pct:.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Vintage 분석
        st.markdown("#### 📅 Vintage별 투자 현황")
        
        vintage_data = {}
        for p in portfolio:
            if p['amount'] > 0:
                year = p['investment_date'][:4]
                if year not in vintage_data:
                    vintage_data[year] = {'amount': 0, 'count': 0, 'current': 0}
                vintage_data[year]['amount'] += p['amount']
                vintage_data[year]['count'] += 1
                vintage_data[year]['current'] += p['current_value']
        
        fig_vintage = go.Figure()
        years = sorted(vintage_data.keys())
        
        fig_vintage.add_trace(go.Bar(
            name='투자금액',
            x=years,
            y=[vintage_data[y]['amount'] for y in years],
            marker_color='#6366f1'
        ))
        fig_vintage.add_trace(go.Bar(
            name='현재가치',
            x=years,
            y=[vintage_data[y]['current'] for y in years],
            marker_color='#10b981'
        ))
        
        fig_vintage.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(showgrid=False, color='#a1a1aa'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#a1a1aa', title='억원'),
            margin=dict(t=50, b=30, l=50, r=30)
        )
        st.plotly_chart(fig_vintage, use_container_width=True)
    
    # =========================================================================
    # Tab 4: 이벤트 캘린더
    # =========================================================================
    with tab4:
        st.markdown("### 📅 주요 이벤트 캘린더")
        
        # 이벤트 추출 및 정렬
        events = []
        for p in portfolio:
            if p['amount'] > 0 and p['next_event']:
                events.append({
                    'company': p['company'],
                    'event': p['next_event'],
                    'milestone': p['milestone'],
                    'amount': p['amount'],
                    'type': p['investment_type']
                })
        
        # 분기별 그룹핑
        st.markdown("#### 🗓️ 2025년 예정 이벤트")
        
        quarters = {
            'Q1 (1-3월)': [e for e in events if 'Q1' in e['event']],
            'Q2 (4-6월)': [e for e in events if 'Q2' in e['event']],
            'Q3 (7-9월)': [e for e in events if 'Q3' in e['event']],
            'Q4 (10-12월)': [e for e in events if 'Q4' in e['event']],
            '2026년 이후': [e for e in events if '2026' in e['event']]
        }
        
        for quarter, quarter_events in quarters.items():
            if quarter_events:
                st.markdown(f"##### {quarter}")
                for e in quarter_events:
                    type_class = {'RCPS': 'indigo', 'CB': 'amber', '보통주': 'emerald'}.get(e['type'], 'sky')
                    st.markdown(f"""
                    <div class="data-row">
                        <div class="data-row-left">
                            <div class="data-row-title">
                                <span class="badge badge-{type_class}">{e['type']}</span>
                                {e['company']}
                            </div>
                            <div class="data-row-subtitle">{e['event']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: var(--text-primary); font-weight: 600;">{e['amount']:,.1f}억</div>
                            <div style="color: var(--text-muted); font-size: 0.75rem;">{e['milestone']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 회수 파이프라인
        st.markdown("#### 🎯 Exit 파이프라인")
        
        exit_candidates = [p for p in portfolio if p['amount'] > 0 and ('IPO' in p['next_event'] or 'Series' in p['next_event'])]
        
        if exit_candidates:
            for p in exit_candidates:
                potential_return = p['valuation'] * (p['ownership'] / 100)
                moic = potential_return / p['amount'] if p['amount'] > 0 else 0
                
                st.markdown(f"""
                <div class="card" style="margin-bottom: 0.75rem; border-left: 3px solid var(--accent-emerald);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: var(--text-primary); font-weight: 700; font-size: 1rem;">{p['company']}</div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">{p['next_event']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: var(--accent-emerald); font-size: 1.1rem; font-weight: 700;">
                                {potential_return:,.1f}억 예상
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">
                                투자 {p['amount']:,.1f}억 → {moic:.1f}x MOIC
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("현재 Exit 예정 건이 없습니다.")
    
    # =========================================================================
    # Tab 5: 관리
    # =========================================================================
    with tab5:
        st.markdown("### ⚙️ 포트폴리오 관리")
        
        # 신규 투자 등록
        st.markdown("#### ➕ 신규 투자 등록")
        
        with st.form("new_investment"):
            col1, col2 = st.columns(2)
            with col1:
                new_company = st.text_input("회사명")
                new_sector = st.selectbox("섹터", ["환경/폐기물", "신재생에너지", "수처리", "CCUS", "자원순환", 
                                                   "ESG/SaaS", "수소", "태양광", "풍력", "배터리재활용", "에너지IT", "EV/모빌리티", "기타"])
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
            
            submitted = st.form_submit_button("📝 등록", use_container_width=True)
            if submitted:
                st.success(f"✅ {new_company} 투자건이 등록되었습니다. (실제 저장은 DB 연동 필요)")
        
        st.markdown("---")
        
        # 가치평가 업데이트
        st.markdown("#### 📊 가치평가 일괄 업데이트")
        
        active_portfolio = [p for p in portfolio if p['amount'] > 0]
        
        update_data = []
        for p in active_portfolio:
            update_data.append({
                'ID': p['id'],
                '회사': p['company'],
                '투자금액': p['amount'],
                '현재가치': p['current_value'],
                '기업가치': p['valuation'],
                'MOIC': round(p['current_value'] / p['amount'], 2) if p['amount'] > 0 else 0
            })
        
        df_update = pd.DataFrame(update_data)
        edited_df = st.data_editor(
            df_update,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "회사": st.column_config.TextColumn("회사", disabled=True),
                "투자금액": st.column_config.NumberColumn("투자금액", disabled=True, format="%.1f억"),
                "현재가치": st.column_config.NumberColumn("현재가치 (수정가능)", format="%.2f억"),
                "기업가치": st.column_config.NumberColumn("기업가치 (수정가능)", format="%.0f억"),
                "MOIC": st.column_config.NumberColumn("MOIC", disabled=True, format="%.2fx")
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("💾 가치평가 저장", use_container_width=True):
            st.success("✅ 가치평가가 업데이트되었습니다. (실제 저장은 DB 연동 필요)")
        
        st.markdown("---")
        
        # 데이터 내보내기
        st.markdown("#### 📥 데이터 내보내기")
        
        col1, col2 = st.columns(2)
        with col1:
            portfolio_df = pd.DataFrame(portfolio)
            csv = portfolio_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📊 포트폴리오 CSV",
                csv,
                f"ifam_portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        with col2:
            fund_df = pd.DataFrame(funds)
            csv_fund = fund_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "🏦 펀드현황 CSV",
                csv_fund,
                f"ifam_funds_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    load_css()
    render_header()
    
    # 사이드바 네비게이션
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        page = st.radio(
            "메뉴 선택",
            ["🏠 홈", "🌱 Daily Market", "📊 VC Analyzer", "🏢 LP Discovery", "📈 Portfolio"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="color: var(--text-muted); font-size: 0.75rem; text-align: center;">
            IFAM Dashboard v1.0<br>
            © 2025 인프라프론티어
        </div>
        """, unsafe_allow_html=True)
    
    # 페이지 라우팅
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
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: var(--text-muted); padding: 1rem; font-size: 0.8rem;">
        🏛️ IFAM 통합 대시보드 v1.0 | 인프라프론티어자산운용(주)<br>
        <small>본 대시보드의 데이터는 참고용이며, 투자 결정 전 원본 데이터를 반드시 확인하세요.</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
