import math
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

st.set_page_config(
    page_title="Andy's FIRE Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Design Tokens ────────────────────────────────────────────────────────────
# Private Banking · Light Luxury palette
BG          = "#FAF8F5"   # warm cream
SURFACE     = "#FFFFFF"   # card white
SURFACE_2   = "#F5F1EB"   # warm stone-100
PRIMARY     = "#1C1917"   # stone-900
SECONDARY   = "#44403C"   # stone-700
MUTED       = "#78716C"   # stone-500
CAPTION     = "#A8A29E"   # stone-400
BORDER      = "#E7E2D9"   # warm stone-200
BORDER_SUB  = "#F0EDE8"   # subtle border
GOLD        = "#B45309"   # amber-700 (accent)
GOLD_LIGHT  = "#FEF3C7"   # amber-50
CHART_BG    = "#FFFDFB"   # warm white for charts
GRID        = "rgba(231,226,217,0.7)"

# ─── Global CSS (Light Luxury) ────────────────────────────────────────────────
# st.html() correctly injects <style> tags into the page scope (Streamlit 1.31+)
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

/* ── font ── */
html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Sans', -apple-system, 'Helvetica Neue', sans-serif !important;
}

/* ── app background ── */
.stApp {
    background: linear-gradient(160deg, #FAF8F5 0%, #F5F1EB 100%) !important;
}

/* ── spacing ── */
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1280px;
}
@media (max-width: 640px) {
    .block-container { padding-top: 0.5rem !important; }
}

/* ── frosted header ── */
[data-testid="stHeader"] {
    background: rgba(250,248,245,0.9) !important;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid #E7E2D9;
}

/* ── section headings ── */
h2 {
    color: #1C1917 !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 14px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
h3 {
    color: #44403C !important;
    font-weight: 600 !important;
}

/* ── metric cards ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E7E2D9 !important;
    border-radius: 18px;
    padding: 18px 22px !important;
    box-shadow: 0 1px 4px rgba(28,25,23,0.05), 0 4px 16px rgba(28,25,23,0.04);
    transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 20px rgba(180,83,9,0.12), 0 1px 4px rgba(28,25,23,0.06);
    transform: translateY(-2px);
    border-color: #B45309 !important;
}

/* ── metric values — monospace for numbers ── */
[data-testid="stMetricValue"] > div {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    color: #1C1917 !important;
    letter-spacing: -0.01em !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}

/* ── plotly chart cards — borderless, shadow only ── */
[data-testid="stPlotlyChart"] > div {
    background: #FFFDFB;
    border: none;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(28,25,23,0.07), 0 0 0 1px rgba(231,226,217,0.45);
    padding: 4px;
}

/* ── dataframes ── */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    border: 1px solid #E7E2D9 !important;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(28,25,23,0.05);
}

/* ── divider ── */
hr { border-color: #E7E2D9 !important; }

/* ── selectbox / toggle labels ── */
[data-testid="stSelectbox"] label,
[data-testid="stToggle"] label,
[data-testid="stNumberInput"] label {
    color: #78716C !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
}

/* ── caption ── */
[data-testid="stCaptionContainer"] p {
    color: #A8A29E !important;
    font-size: 12px !important;
}

/* ── expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E7E2D9 !important;
    border-radius: 16px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(28,25,23,0.04) !important;
}
[data-testid="stExpander"] summary {
    color: #44403C !important;
    font-weight: 600 !important;
}

/* ── action bar ── */
.action-bar {
    border-radius: 22px;
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    border: 1px solid rgba(255,255,255,0.3);
}
.action-bar-left  { min-width: 180px; }
.action-bar-right {
    display: flex;
    gap: clamp(16px, 4vw, 44px);
    flex-wrap: wrap;
    align-items: center;
}
.ab-label {
    margin: 0;
    font-size: 10px;
    opacity: .65;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-weight: 600;
    font-family: 'IBM Plex Sans', sans-serif;
}
.ab-value {
    margin: 4px 0 0;
    font-size: clamp(16px, 3vw, 22px);
    font-weight: 700;
    letter-spacing: -.01em;
    font-family: 'IBM Plex Mono', monospace;
}
.ab-divider {
    width: 1px;
    min-height: 36px;
    background: rgba(255,255,255,0.25);
    align-self: stretch;
}

/* ── mobile ── */
@media (max-width: 640px) {
    .action-bar { flex-direction: column; align-items: flex-start; padding: 20px; }
    .action-bar-right { gap: 20px; }
}

/* ── top gold signature bar ── */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #92400E 0%, #D97706 35%, #B45309 65%, #92400E 100%);
    z-index: 99999;
    pointer-events: none;
}
</style>
""")

# ─── PE Zone Definitions ─────────────────────────────────────────────────────
ZONES = [
    {
        "zone_name": "高危禁区", "range_label": "PE > 40",
        "icon": "🔴", "target": "—", "multiplier": "0×",
        "amount": 0, "reserve_change": 125, "reserve_sign": "+",
        "reserve_note": "本周 $125 全部留存账户",
        "gradient": "linear-gradient(135deg, #7f1d1d 0%, #b91c1c 100%)",
        "shadow": "rgba(185,28,28,0.28)",
        "table_bg": "#b91c1c", "text_color": "#ffffff",
    },
    {
        "zone_name": "虚高警戒", "range_label": "35 < PE ≤ 40",
        "icon": "🟠", "target": "VOO", "multiplier": "0.6×",
        "amount": 75, "reserve_change": 50, "reserve_sign": "+",
        "reserve_note": "本周留存 $50 进入账户结余",
        "gradient": "linear-gradient(135deg, #7c2d12 0%, #c2410c 100%)",
        "shadow": "rgba(194,65,12,0.28)",
        "table_bg": "#c2410c", "text_color": "#ffffff",
    },
    {
        "zone_name": "均衡配置", "range_label": "32 < PE ≤ 35",
        "icon": "🟡", "target": "VOO", "multiplier": "1×",
        "amount": 125, "reserve_change": 0, "reserve_sign": "",
        "reserve_note": "本周不留存",
        "gradient": "linear-gradient(135deg, #713f12 0%, #a16207 100%)",
        "shadow": "rgba(161,98,7,0.28)",
        "table_bg": "#a16207", "text_color": "#ffffff",
    },
    {
        "zone_name": "价值洼地", "range_label": "28 < PE ≤ 32",
        "icon": "🟢", "target": "QQQM", "multiplier": "1.5×",
        "amount": 187, "reserve_change": 62, "reserve_sign": "-",
        "reserve_note": "从账户结余取用 $62",
        "gradient": "linear-gradient(135deg, #14532d 0%, #15803d 100%)",
        "shadow": "rgba(21,128,61,0.25)",
        "table_bg": "#15803d", "text_color": "#ffffff",
    },
    {
        "zone_name": "超值猎场", "range_label": "25 < PE ≤ 28",
        "icon": "🩵", "target": "QQQM", "multiplier": "2×",
        "amount": 250, "reserve_change": 125, "reserve_sign": "-",
        "reserve_note": "从账户结余取用 $125",
        "gradient": "linear-gradient(135deg, #155e75 0%, #0e7490 100%)",
        "shadow": "rgba(14,116,144,0.25)",
        "table_bg": "#0e7490", "text_color": "#ffffff",
    },
    {
        "zone_name": "黄金大底", "range_label": "PE ≤ 25",
        "icon": "💙", "target": "QQQM", "multiplier": "2.5× + 全清结余",
        "amount": 312, "reserve_change": None, "reserve_sign": "",
        "reserve_note": "$312 定投 + 累计结余全部一次性买入 QQQM",
        "gradient": "linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%)",
        "shadow": "rgba(29,78,216,0.28)",
        "table_bg": "#1d4ed8", "text_color": "#ffffff",
    },
]

ZONE_BG_MAP = {z["zone_name"]: z["table_bg"] for z in ZONES}

# Gauge step colors — unified with table colors (700-series, good contrast with white)
GAUGE_STEPS = [
    {"range": [0,   25],  "color": "#1d4ed8"},  # 黄金大底  blue-700
    {"range": [25,  28],  "color": "#0e7490"},  # 超值猎场  cyan-700
    {"range": [28,  32],  "color": "#15803d"},  # 价值洼地  green-700
    {"range": [32,  35],  "color": "#a16207"},  # 均衡配置  yellow-700
    {"range": [35,  40],  "color": "#c2410c"},  # 虚高警戒  orange-700
    {"range": [40,  55],  "color": "#b91c1c"},  # 高危禁区  red-700
]
ZONE_LEGEND = [
    ("≤25",   "黄金大底",  "#1d4ed8"),
    ("25-28",  "超值猎场", "#0e7490"),
    ("28-32",  "价值洼地", "#15803d"),
    ("32-35",  "均衡配置", "#a16207"),
    ("35-40",  "虚高警戒", "#c2410c"),
    (">40",    "高危禁区", "#b91c1c"),
]


def get_pe_zone(pe: float) -> dict:
    if pe > 40:  return ZONES[0]
    if pe > 35:  return ZONES[1]
    if pe > 32:  return ZONES[2]
    if pe > 28:  return ZONES[3]
    if pe > 25:  return ZONES[4]
    return ZONES[5]


def fmt_reserve(zone: dict) -> str:
    if zone["reserve_change"] is None:
        return "全部清空"
    if zone["reserve_sign"] == "+":
        return f"+${zone['reserve_change']}"
    if zone["reserve_sign"] == "-":
        return f"-${zone['reserve_change']}"
    return "$0"


def section_title(icon: str, text: str):
    """Premium section header with gold accent bar."""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:32px 0 18px;">
      <div style="width:3px;height:26px;background:linear-gradient(180deg,#B45309,#D97706);
                  border-radius:2px;flex-shrink:0;"></div>
      <span style="font-family:'IBM Plex Sans',sans-serif;font-size:clamp(1.05rem,2.5vw,1.35rem);
                   color:#1C1917;font-weight:700;letter-spacing:-0.025em;">{icon}&ensp;{text}</span>
    </div>
    """, unsafe_allow_html=True)


def build_gauge_svg(pe_val: float) -> str:
    """240° wide-sweep gauge — automotive speedometer arc from 7 oʼclock to 5 oʼclock."""
    GAUGE_MIN, GAUGE_MAX = 20.0, 45.0
    cx, cy   = 200, 185          # arc centre
    r_out    = 155               # outer radius of coloured band
    r_in     = 98                # inner radius → 57px band
    START_DEG = 210.0            # PE 20 → ~7 oʼclock (lower-left)
    SWEEP_DEG = 240.0            # 210° → -30° (330°) → 5 oʼclock (lower-right)

    zone_defs = [
        (20,        25, "#1d4ed8"),
        (25,        28, "#0e7490"),
        (28,        32, "#15803d"),
        (32,        35, "#a16207"),
        (35,        40, "#c2410c"),
        (40, GAUGE_MAX, "#b91c1c"),
    ]

    def val_to_rad(v: float) -> float:
        v = max(GAUGE_MIN, min(v, GAUGE_MAX))
        frac = (v - GAUGE_MIN) / (GAUGE_MAX - GAUGE_MIN)
        return math.radians(START_DEG - frac * SWEEP_DEG)

    def pt(r: float, theta: float):
        return cx + r * math.cos(theta), cy - r * math.sin(theta)

    # ── Background track (grey arc spanning 240°) ──
    ba1 = val_to_rad(GAUGE_MIN)   # 210°
    ba2 = val_to_rad(GAUGE_MAX)   # -30°
    bx1, by1 = pt(r_out, ba1); bx2, by2 = pt(r_out, ba2)
    bi1, bj1 = pt(r_in,  ba1); bi2, bj2 = pt(r_in,  ba2)
    bg_arc = (
        f'<path d="M {bx1:.1f},{by1:.1f} '
        f'A {r_out},{r_out} 0 0 0 {bx2:.1f},{by2:.1f} '
        f'L {bi2:.1f},{bj2:.1f} '
        f'A {r_in},{r_in} 0 0 1 {bi1:.1f},{bj1:.1f} Z" '
        f'fill="#E7E2D9" opacity="0.85"/>'
    )

    # ── Coloured zone arcs ──
    arcs = ""
    for v1, v2, color in zone_defs:
        a1, a2 = val_to_rad(v1), val_to_rad(v2)
        ox1, oy1 = pt(r_out, a1); ox2, oy2 = pt(r_out, a2)
        ix1, iy1 = pt(r_in,  a1); ix2, iy2 = pt(r_in,  a2)
        arcs += (
            f'<path d="M {ox1:.1f},{oy1:.1f} '
            f'A {r_out},{r_out} 0 0 0 {ox2:.1f},{oy2:.1f} '
            f'L {ix2:.1f},{iy2:.1f} '
            f'A {r_in},{r_in} 0 0 1 {ix1:.1f},{iy1:.1f} Z" '
            f'fill="{color}"/>'
        )

    # ── Tick marks: major every 5, minor every 1 ──
    ticks = ""
    for v in range(20, 46):
        a = val_to_rad(float(v))
        if v % 5 == 0:
            x1, y1 = pt(r_in - 4, a); x2, y2 = pt(r_out + 5, a)
            ticks += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="#1c1917" stroke-width="1.5"/>')
        else:
            x1, y1 = pt(r_out - 14, a); x2, y2 = pt(r_out + 4, a)
            ticks += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="#A8A29E" stroke-width="0.7"/>')

    # ── Zone separator lines (subtle, at boundaries) ──
    seps = ""
    for v in [25, 28, 32, 35, 40]:
        a = val_to_rad(v)
        x1, y1 = pt(r_in - 2, a); x2, y2 = pt(r_out + 3, a)
        seps += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>')

    # ── Scale labels (outside the arc) ──
    lbls = ""
    for v in [20, 25, 30, 35, 40, 45]:
        a = val_to_rad(v)
        lx, ly = pt(r_out + 24, a)
        lbls += (
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" fill="#44403C" '
            f'font-size="13" font-family="IBM Plex Mono,monospace" '
            f'font-weight="500">{v}</text>'
        )

    # ── Current PE & zone colour ──
    pe_c = max(GAUGE_MIN, min(float(pe_val), GAUGE_MAX))
    pe_color = "#78716C"
    for v1, v2, zc in zone_defs:
        if v1 <= pe_c < v2 or (v2 == GAUGE_MAX and pe_c == v2):
            pe_color = zc
            break

    # ── Needle (slender, dark) ──
    na = val_to_rad(pe_c)
    ntx, nty = pt(r_out + 10, na)    # tip beyond outer arc
    tail_r = 28                       # counterweight tail length
    t_a = na + math.pi
    ttx, tty = cx + tail_r * math.cos(t_a), cy - tail_r * math.sin(t_a)
    perp = na + math.pi / 2
    hw = 3.0                          # half-width at base
    b1x = cx + hw * math.cos(perp); b1y = cy - hw * math.sin(perp)
    b2x = cx - hw * math.cos(perp); b2y = cy + hw * math.sin(perp)
    npts = f"{ntx:.1f},{nty:.1f} {b1x:.1f},{b1y:.1f} {ttx:.1f},{tty:.1f} {b2x:.1f},{b2y:.1f}"
    needle = (
        f'<polygon points="{npts}" fill="#1c1917" stroke="#B45309" stroke-width="0.5"/>'
    )

    # ── Centre hub ──
    hub = (
        f'<circle cx="{cx}" cy="{cy}" r="7" fill="#292524"/>'
        f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="#B45309"/>'
    )

    # ── Readout — centred below the arc ──
    ry = cy + 68
    readout = (
        f'<text x="{cx}" y="{ry}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="IBM Plex Mono,monospace" font-size="38" font-weight="600" '
        f'fill="{pe_color}" letter-spacing="-0.02em">{pe_c:.1f}</text>'
        f'<text x="{cx}" y="{ry + 30}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="IBM Plex Mono,monospace" font-size="12" fill="#A8A29E" '
        f'letter-spacing="0.18em">P / E</text>'
    )

    return (
        f'<svg viewBox="0 0 400 310" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;overflow:visible">'
        f'{bg_arc}{arcs}{ticks}{seps}{lbls}{needle}{hub}{readout}</svg>'
    )


# ─── Data Fetching (cached) ───────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_qqq_info() -> dict:
    try:
        info = yf.Ticker("QQQM").info
        return {"pe": info.get("trailingPE")}
    except Exception:
        return {"pe": None}


@st.cache_data(ttl=300)
def fetch_current_price(ticker: str) -> dict:
    try:
        fi = yf.Ticker(ticker).fast_info
        return {"price": fi.last_price, "prev_close": fi.previous_close}
    except Exception:
        return {"price": None, "prev_close": None}


@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_price_on_date(ticker: str, target_date: date) -> float | None:
    try:
        start = target_date - timedelta(days=7)
        end   = target_date + timedelta(days=2)
        df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None


# ─── Session State ────────────────────────────────────────────────────────────
if "records" not in st.session_state:
    st.session_state.records = []

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:4px 0 16px;">
  <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">
    <h1 style="font-family:'IBM Plex Sans',sans-serif;
               color:{PRIMARY};font-size:clamp(1.5rem,4vw,2.1rem);
               font-weight:700;margin:0;letter-spacing:-0.03em;white-space:nowrap;">
      📈&ensp;Andy's FIRE Tracker
    </h1>
    <span style="font-family:'IBM Plex Sans',sans-serif;
                 color:{MUTED};font-size:0.85rem;font-weight:400;white-space:nowrap;">
      QQQM / VOO 纳指动态定投 · 基于纳斯达克100 TTM PE
    </span>
  </div>
  <div style="margin-top:12px;display:flex;align-items:center;gap:8px;">
    <div style="height:1px;background:linear-gradient(90deg,{GOLD},rgba(180,83,9,0.08));flex:1;max-width:280px;"></div>
    <span style="font-size:10px;color:{CAPTION};letter-spacing:0.12em;text-transform:uppercase;
                 font-family:'IBM Plex Sans',sans-serif;font-weight:500;">
      Private · Long-term · Disciplined
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Fetch data once ──────────────────────────────────────────────────────────
qqq_info  = fetch_qqq_info()
qqqm_data = fetch_current_price("QQQM")
voo_data  = fetch_current_price("VOO")
auto_pe   = qqq_info["pe"]

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 1 — 市场快照 + PE 仪表盘
# ═══════════════════════════════════════════════════════════════════════════════
section_title("📊", "市场快照")

toggle_col, _ = st.columns([2.2, 5.8])
with toggle_col:
    use_manual = st.toggle("手动输入 PE（以 Gurufocus 为准）", value=False)
    if use_manual:
        current_pe = st.number_input(
            "纳斯达克100 TTM PE", min_value=0.0, max_value=300.0,
            value=float(auto_pe) if auto_pe else 30.0,
            step=0.1, format="%.2f",
        )
    else:
        current_pe = auto_pe

left_col, right_col = st.columns([1, 2.3])

with left_col:
    st.metric(
        "纳斯达克100 TTM PE",
        f"{current_pe:.2f}" if current_pe else "—",
        help="来自 QQQ trailingPE，可手动覆盖以 Gurufocus 数据为准",
    )
    if qqqm_data["price"] and qqqm_data["prev_close"]:
        chg = (qqqm_data["price"] - qqqm_data["prev_close"]) / qqqm_data["prev_close"] * 100
        st.metric("QQQM 实时价", f"${qqqm_data['price']:.2f}", f"{chg:+.2f}%")
    else:
        st.metric("QQQM 实时价", "—")
    if voo_data["price"] and voo_data["prev_close"]:
        chg = (voo_data["price"] - voo_data["prev_close"]) / voo_data["prev_close"] * 100
        st.metric("VOO 实时价", f"${voo_data['price']:.2f}", f"{chg:+.2f}%")
    else:
        st.metric("VOO 实时价", "—")

if current_pe:
    cz    = get_pe_zone(float(current_pe))
    c_amt = f"${cz['amount']}" if cz["amount"] > 0 else "—"
    c_res = fmt_reserve(cz)

    with right_col:
        pe_val = float(current_pe)

        # ── Zone name badge ──
        zone_badge = (
            f'<div style="text-align:center;padding:6px 0 2px;">'
            f'<span style="font-family:\'IBM Plex Sans\',sans-serif;font-size:17px;'
            f'font-weight:700;letter-spacing:-0.01em;color:{cz["table_bg"]};">'
            f'{cz["icon"]}&ensp;{cz["zone_name"]}</span></div>'
        )
        st.html(zone_badge)

        # ── Plotly gauge — clean semicircular, no frame, needle pointer only ──
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(pe_val, 45.0),
            number={"font": {"size": 44, "color": "#1c1917", "family": "IBM Plex Mono"},
                    "valueformat": ".1f"},
            title={"text": "TTM P/E",
                   "font": {"size": 13, "color": "#A8A29E", "family": "IBM Plex Sans"}},
            gauge={
                "axis": {
                    "range": [20, 45],
                    "tickvals": [20, 25, 28, 32, 35, 40, 45],
                    "tickcolor": "#78716C",
                    "tickfont": {"color": "#78716C", "size": 10, "family": "IBM Plex Mono"},
                    "tickwidth": 1,
                },
                "bar": {"thickness": 0},           # no path trace
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [20, 25], "color": "#1d4ed8"},
                    {"range": [25, 28], "color": "#0e7490"},
                    {"range": [28, 32], "color": "#15803d"},
                    {"range": [32, 35], "color": "#a16207"},
                    {"range": [35, 40], "color": "#c2410c"},
                    {"range": [40, 45], "color": "#b91c1c"},
                ],
                "threshold": {
                    "line": {"color": "#1c1917", "width": 3.5},
                    "thickness": 0.85,              # longer needle line
                    "value": min(pe_val, 45.0),
                },
            },
        ))
        gauge_fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            height=270,
            margin=dict(l=30, r=30, t=25, b=0),
            font={"color": "#44403C"},
        )
        # Inline CSS to kill Plotly's container border/frame
        st.html("""
        <style>
        .stPlotlyChart {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        .stPlotlyChart > div {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        </style>
        """)
        st.plotly_chart(gauge_fig, width="stretch", config={"displayModeBar": False})

        # ── Zone legend chips — inactive chips keep their zone color at low opacity ──
        chips = ""
        for rng, name, bg in ZONE_LEGEND:
            is_cur = (name == cz["zone_name"])
            if is_cur:
                chips += (
                    f'<span style="background:{bg};color:#fff;border-radius:20px;'
                    f'font-size:12.5px;font-weight:700;padding:6px 16px;'
                    f'border:2px solid rgba(255,255,255,0.45);display:inline-block;margin:3px;'
                    f'box-shadow:0 4px 14px {cz["shadow"]};'
                    f'font-family:IBM Plex Sans,sans-serif;letter-spacing:0.01em;">'
                    f'{rng}&nbsp;{name}</span>'
                )
            else:
                # bg28 = ~16% opacity fill; bg55 = ~33% opacity border
                chips += (
                    f'<span style="background:{bg}28;color:{bg};'
                    f'border-radius:20px;font-size:11px;font-weight:600;padding:5px 13px;'
                    f'border:1.5px solid {bg}66;display:inline-block;margin:3px;'
                    f'font-family:IBM Plex Sans,sans-serif;">'
                    f'{rng}&nbsp;{name}</span>'
                )
        st.markdown(
            f'<div style="text-align:center;margin-bottom:10px;">{chips}</div>',
            unsafe_allow_html=True,
        )

    # ── Action recommendation bar ──
    st.markdown(f"""
    <div class="action-bar" style="background:{cz['gradient']};color:#fff;
         box-shadow:0 12px 48px {cz['shadow']},0 4px 12px rgba(28,25,23,0.12),
                   inset 0 1px 0 rgba(255,255,255,0.22);">
      <div class="action-bar-left">
        <p style="margin:0;font-size:10px;opacity:.6;text-transform:uppercase;
                  letter-spacing:.14em;font-weight:600;font-family:'IBM Plex Sans',sans-serif;">
          当前区间
        </p>
        <p style="margin:6px 0 0;font-size:clamp(16px,3vw,23px);font-weight:700;
                  letter-spacing:-.015em;font-family:'IBM Plex Sans',sans-serif;">
          {cz['icon']}&ensp;{cz['zone_name']}&ensp;·&ensp;{cz['range_label']}
        </p>
      </div>
      <div class="action-bar-right">
        <div>
          <p class="ab-label">买入标的</p>
          <p class="ab-value">{cz['target']}</p>
        </div>
        <div class="ab-divider"></div>
        <div>
          <p class="ab-label">买入倍数</p>
          <p class="ab-value">{cz['multiplier']}</p>
        </div>
        <div class="ab-divider"></div>
        <div>
          <p class="ab-label">建议金额</p>
          <p class="ab-value">{c_amt}</p>
        </div>
        <div class="ab-divider"></div>
        <div>
          <p class="ab-label">结余变化</p>
          <p class="ab-value">{c_res}</p>
        </div>
      </div>
    </div>
    <p style="color:{CAPTION};font-size:12px;margin:8px 0 0 6px;letter-spacing:.01em;
              font-family:'IBM Plex Sans',sans-serif;">
      {cz['reserve_note']}
    </p>
    """, unsafe_allow_html=True)
else:
    st.warning("无法自动获取 PE，请开启手动输入。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 2 — QQQM 日 K 线图
# ═══════════════════════════════════════════════════════════════════════════════
section_title("📉", "QQQM 日 K 线图")

PERIOD_OPTS = {"1 月": "1mo", "3 月": "3mo", "6 月": "6mo", "1 年": "1y", "3 年": "3y", "全部": "max"}
sel_label = st.selectbox("时间窗口", list(PERIOD_OPTS.keys()), index=3, key="kline_period")
kline_df  = fetch_history("QQQM", PERIOD_OPTS[sel_label])

if not kline_df.empty:
    df_k = kline_df.copy()
    df_k["MA20"] = df_k["Close"].rolling(20).mean()
    df_k["MA60"] = df_k["Close"].rolling(60).mean()
    vol_colors = ["#22c55e" if c >= o else "#ef4444"
                  for c, o in zip(df_k["Close"], df_k["Open"])]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.02, row_heights=[0.7, 0.3],
    )
    fig.add_trace(go.Candlestick(
        x=df_k.index,
        open=df_k["Open"], high=df_k["High"],
        low=df_k["Low"],   close=df_k["Close"],
        increasing=dict(fillcolor="#22c55e", line=dict(color="#16a34a")),
        decreasing=dict(fillcolor="#ef4444", line=dict(color="#dc2626")),
        name="QQQM", showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_k.index, y=df_k["MA20"],
        line=dict(color="#D97706", width=1.5), name="MA20",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_k.index, y=df_k["MA60"],
        line=dict(color="#B45309", width=1.5, dash="dot"), name="MA60",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=df_k.index, y=df_k["Volume"],
        marker_color=vol_colors, name="成交量", showlegend=False,
        marker_line_width=0,
    ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=MUTED, family="IBM Plex Sans, sans-serif"),
        height=540,
        margin=dict(l=0, r=0, t=16, b=0),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="rgba(255,253,251,0.95)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=SECONDARY, size=12),
        ),
    )
    fig.update_xaxes(
        gridcolor=GRID, tickfont=dict(color=CAPTION, size=11),
        rangebreaks=[dict(bounds=["sat", "mon"])],
        showline=False,
    )
    fig.update_yaxes(
        gridcolor=GRID, tickfont=dict(color=CAPTION, size=11),
        showline=False,
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.warning("无法加载 QQQM 历史数据。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 3 — QQQM 历史数据 + PE 表
# ═══════════════════════════════════════════════════════════════════════════════
section_title("📋", "QQQM 历史数据 + PE 估算")

HIST_OPTS  = {"近 30 天": "1mo", "近 90 天": "3mo", "近半年": "6mo", "近 1 年": "1y", "全部": "max"}
hist_label = st.selectbox("数据范围", list(HIST_OPTS.keys()), index=2, key="hist_range")
hist_df    = fetch_history("QQQM", HIST_OPTS[hist_label])

if not hist_df.empty and current_pe and qqqm_data["price"]:
    cur_pe    = float(current_pe)
    cur_price = float(qqqm_data["price"])
    hist_pe   = (hist_df["Close"] / cur_price * cur_pe).round(2)

    tbl = pd.DataFrame({
        "日期":  hist_df.index.strftime("%Y-%m-%d"),
        "开盘":  hist_df["Open"].round(2),
        "收盘":  hist_df["Close"].round(2),
        "最高":  hist_df["High"].round(2),
        "最低":  hist_df["Low"].round(2),
        "PE":    hist_pe,
    }).reset_index(drop=True)
    tbl["PE 区间"] = tbl["PE"].apply(lambda v: get_pe_zone(float(v))["zone_name"])

    def _style_zone(val):
        bg = ZONE_BG_MAP.get(val, "")
        return f"background-color:{bg};color:white;font-weight:600;" if bg else ""

    st.dataframe(
        tbl.style
            .format({"开盘": "{:.2f}", "收盘": "{:.2f}", "最高": "{:.2f}", "最低": "{:.2f}", "PE": "{:.2f}"})
            .map(_style_zone, subset=["PE 区间"]),
        width="stretch", hide_index=True,
    )
    st.caption(
        f"PE 基于爬取的实时 NDX PE（{cur_pe:.2f}）按价格比例推算。"
        "精确历史 PE 请参考 [Gurufocus](https://www.gurufocus.com/term/pe/QQQM/PE-Ratio/QQQM)。"
    )
elif not current_pe:
    st.warning("无法获取当前 PE，请开启手动输入后刷新。")
else:
    st.warning("无法加载 QQQM 历史数据。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 5 — 策略速查表
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📖 策略速查表（点击展开）", expanded=False):
    rows = []
    for z in ZONES:
        rows.append({
            "PE 区间":    z["range_label"],
            "区间名":     z["zone_name"],
            "买入标的":   z["target"],
            "倍数":       z["multiplier"],
            "金额 (USD)": f"${z['amount']}" if z["amount"] > 0 else "—",
            "结余变化":   fmt_reserve(z),
            "备注":       z["reserve_note"],
        })
    strat_df = pd.DataFrame(rows)
    st.dataframe(
        strat_df.style.map(
            lambda v: f"background-color:{ZONE_BG_MAP.get(v,'')};color:white;font-weight:600;"
                      if v in ZONE_BG_MAP else "",
            subset=["区间名"],
        ),
        width="stretch", hide_index=True,
    )
    st.caption("边界规则：PE 恰好等于边界值时（如 35 或 32），按**较低**区间执行。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 6 — 定投记录
# ═══════════════════════════════════════════════════════════════════════════════
section_title("💰", "定投记录")

imp_col, exp_col, _ = st.columns([1.5, 1.5, 5])
with imp_col:
    uploaded = st.file_uploader("导入 CSV", type="csv",
                                label_visibility="collapsed", key="csv_upload")
    if uploaded:
        try:
            imported = pd.read_csv(uploaded)
            st.session_state.records = imported.to_dict("records")
            st.success(f"已导入 {len(st.session_state.records)} 条记录")
        except Exception as e:
            st.error(f"导入失败：{e}")
with exp_col:
    if st.session_state.records:
        csv_bytes = pd.DataFrame(st.session_state.records).to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 导出 CSV", data=csv_bytes,
            file_name=f"fire_tracker_{date.today()}.csv", mime="text/csv",
        )

default_pe_val  = float(current_pe) if current_pe else 30.0
default_zone    = get_pe_zone(default_pe_val)
default_amount  = float(default_zone["amount"])
default_reserve = (
    float(default_zone["reserve_change"]) * (1 if default_zone["reserve_sign"] != "-" else -1)
    if default_zone["reserve_change"] is not None else 0.0
)

with st.expander("➕ 新增定投记录", expanded=len(st.session_state.records) == 0):
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        rec_date = st.date_input("日期", value=date.today(), key="rec_date")
        rec_pe   = st.number_input("当周 PE", min_value=0.0, value=default_pe_val,
                                   step=0.1, format="%.2f", key="rec_pe")
    with f2:
        rec_target = st.selectbox("买入标的", ["VOO", "QQQM", "无（停止定投）"], key="rec_target")
        rec_amount = st.number_input("买入金额 ($)", min_value=0.0, value=default_amount,
                                     step=1.0, format="%.2f", key="rec_amount")
    with f3:
        rec_price = st.number_input("买入价格（填 0 自动获取）", min_value=0.0, value=0.0,
                                    step=0.01, format="%.2f", key="rec_price")
        rec_fee   = st.number_input("手续费 ($)", min_value=0.0, value=1.00,
                                    step=0.01, format="%.2f", key="rec_fee")
    with f4:
        rec_reserve = st.number_input("本周留存 ($，负数=取用结余)", value=default_reserve,
                                      step=1.0, format="%.2f", key="rec_reserve")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        submit = st.button("✅ 提交记录", width="stretch", key="submit_rec")

    if submit:
        actual_price = rec_price
        if actual_price == 0 and rec_target != "无（停止定投）":
            ticker_sym = "QQQM" if "QQQM" in rec_target else "VOO"
            fetched = fetch_price_on_date(ticker_sym, rec_date)
            if fetched:
                actual_price = fetched
            else:
                st.error("无法自动获取该日期价格，请手动填写。")
                st.stop()

        shares   = rec_amount / actual_price if actual_price > 0 else 0.0
        prev_res = st.session_state.records[-1].get("累计结余", 0) if st.session_state.records else 0
        cum_res  = prev_res + rec_reserve

        st.session_state.records.append({
            "日期":     rec_date.isoformat(),
            "当周PE":   round(rec_pe, 2),
            "买入标的": rec_target,
            "买入金额": round(rec_amount, 2),
            "买入价格": round(actual_price, 2),
            "股数":     round(shares, 6),
            "手续费":   round(rec_fee, 2),
            "本周留存": round(rec_reserve, 2),
            "累计结余": round(cum_res, 2),
        })
        st.success("记录已添加！")
        st.rerun()

if st.session_state.records:
    rdf = pd.DataFrame(st.session_state.records)
    qp  = qqqm_data["price"] or 0.0
    vp  = voo_data["price"]  or 0.0

    def _cur_price(target):
        if "QQQM" in str(target): return qp
        if "VOO"  in str(target): return vp
        return 0.0

    rdf["当前市值"]        = (rdf["股数"] * rdf["买入标的"].apply(_cur_price)).round(2)
    rdf["纯盈利 (不含费)"]  = (rdf["当前市值"] - rdf["买入金额"]).round(2)
    rdf["实际盈利 (含费)"]  = (rdf["当前市值"] - rdf["买入金额"] - rdf["手续费"]).round(2)

    st.dataframe(rdf, width="stretch", hide_index=True)

    st.markdown(f"""
    <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.95rem;
                font-weight:600;color:{SECONDARY};margin:20px 0 12px;letter-spacing:-0.01em;">
      汇总
    </div>
    """, unsafe_allow_html=True)

    total_in  = rdf["买入金额"].sum()
    total_mv  = rdf["当前市值"].sum()
    total_pp  = rdf["纯盈利 (不含费)"].sum()
    total_ap  = rdf["实际盈利 (含费)"].sum()
    total_fee = rdf["手续费"].sum()
    last_res  = rdf["累计结余"].iloc[-1]
    pct       = (total_mv - total_in) / total_in * 100 if total_in > 0 else 0

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("累计投入",        f"${total_in:,.2f}")
    s2.metric("当前市值",        f"${total_mv:,.2f}", f"{pct:+.2f}%")
    s3.metric("纯盈利 (不含费)", f"${total_pp:,.2f}")
    s4.metric("实际盈利 (含费)", f"${total_ap:,.2f}", f"手续费 ${total_fee:.2f}")
    s5.metric("账户结余",        f"${last_res:,.2f}")

    with st.expander("🗑️ 记录管理"):
        mg1, mg2 = st.columns(2)
        with mg1:
            if st.button("清空全部记录", type="secondary"):
                st.session_state.records = []
                st.rerun()
        with mg2:
            n     = len(st.session_state.records)
            del_n = st.number_input("删除第 N 条（从 1 开始）",
                                    min_value=1, max_value=n, step=1, key="del_n")
            if st.button("删除该条", type="secondary"):
                st.session_state.records.pop(int(del_n) - 1)
                st.rerun()
else:
    st.info("暂无定投记录。点击上方「新增定投记录」开始记录。")
