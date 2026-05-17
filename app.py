import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import io

st.set_page_config(
    page_title="Andy's FIRE Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── spacing ── */
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
@media (max-width: 640px) { .block-container { padding-top: 0.25rem !important; } }

/* ── frosted header ── */
[data-testid="stHeader"] {
    background: rgba(245,245,247,0.85) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(0,0,0,0.06);
}

/* ── section headings ── */
h2 { font-weight: 700 !important; letter-spacing: -0.02em; margin-bottom: 12px !important; }

/* ── metric cards: elevate above the F5F5F7 background ── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 16px;
    padding: 16px 20px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 6px 28px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

/* ── dataframes ── */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    border: 1px solid rgba(0,0,0,0.06) !important;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

/* ── divider ── */
hr { border-color: rgba(0,0,0,0.08) !important; }

/* ── zone card ── */
.zone-card {
    border-radius: 20px; padding: 24px 28px; margin: 14px 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.25);
}

/* ── action bar ── */
.action-bar {
    border-radius: 20px; padding: 22px 30px;
    display: flex; justify-content: space-between;
    align-items: center; flex-wrap: wrap; gap: 14px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.25);
    border: 1px solid rgba(255,255,255,0.2);
}
.action-bar-left  { min-width: 160px; }
.action-bar-right { display: flex; gap: clamp(16px,4vw,40px); flex-wrap: wrap; align-items: center; }
.ab-label { margin: 0; font-size: 11px; opacity: .75; text-transform: uppercase; letter-spacing: .1em; font-weight: 600; }
.ab-value { margin: 4px 0 0; font-size: clamp(16px,3vw,22px); font-weight: 700; letter-spacing: -.01em; }
.ab-divider { width: 1px; min-height: 36px; background: rgba(255,255,255,0.25); align-self: stretch; }

/* ── mobile ── */
@media (max-width: 640px) {
    .zone-card { padding: 18px 16px; }
    .action-bar { flex-direction: column; align-items: flex-start; padding: 18px; }
    .action-bar-right { gap: 20px; }
}
</style>
""", unsafe_allow_html=True)

# ─── PE Zone Definitions ─────────────────────────────────────────────────────
ZONES = [
    {
        "zone_name": "危险！别碰", "range_label": "PE > 40",
        "icon": "🔴", "target": "—", "multiplier": "0×",
        "amount": 0, "reserve_change": 125, "reserve_sign": "+",
        "reserve_note": "本周 $125 全部留存账户",
        "gradient": "linear-gradient(135deg, #8b0000 0%, #d32f2f 100%)",
        "table_bg": "#8b0000", "text_color": "#ffffff",
    },
    {
        "zone_name": "有点贵", "range_label": "35 < PE ≤ 40",
        "icon": "🟠", "target": "VOO", "multiplier": "0.6×",
        "amount": 75, "reserve_change": 50, "reserve_sign": "+",
        "reserve_note": "本周留存 $50 进入账户结余",
        "gradient": "linear-gradient(135deg, #c2410c 0%, #ea580c 100%)",
        "table_bg": "#c2410c", "text_color": "#ffffff",
    },
    {
        "zone_name": "正常发挥", "range_label": "32 < PE ≤ 35",
        "icon": "🟡", "target": "VOO", "multiplier": "1×",
        "amount": 125, "reserve_change": 0, "reserve_sign": "",
        "reserve_note": "本周不留存",
        "gradient": "linear-gradient(135deg, #a16207 0%, #eab308 100%)",
        "table_bg": "#a16207", "text_color": "#ffffff",
    },
    {
        "zone_name": "小捡漏", "range_label": "28 < PE ≤ 32",
        "icon": "🟢", "target": "QQQM", "multiplier": "1.5×",
        "amount": 187, "reserve_change": 62, "reserve_sign": "-",
        "reserve_note": "从账户结余取用 $62",
        "gradient": "linear-gradient(135deg, #4d7c0f 0%, #84cc16 100%)",
        "table_bg": "#4d7c0f", "text_color": "#ffffff",
    },
    {
        "zone_name": "大甩卖", "range_label": "25 < PE ≤ 28",
        "icon": "💚", "target": "QQQM", "multiplier": "2×",
        "amount": 250, "reserve_change": 125, "reserve_sign": "-",
        "reserve_note": "从账户结余取用 $125",
        "gradient": "linear-gradient(135deg, #15803d 0%, #22c55e 100%)",
        "table_bg": "#15803d", "text_color": "#ffffff",
    },
    {
        "zone_name": "黄金坑", "range_label": "PE ≤ 25",
        "icon": "🩵", "target": "QQQM", "multiplier": "2.5× + 全清结余",
        "amount": 312, "reserve_change": None, "reserve_sign": "",
        "reserve_note": "$312 定投 + 累计结余全部一次性买入 QQQM",
        "gradient": "linear-gradient(135deg, #0e7490 0%, #06b6d4 100%)",
        "table_bg": "#0e7490", "text_color": "#ffffff",
    },
]

ZONE_BG_MAP = {z["zone_name"]: z["table_bg"] for z in ZONES}


def get_pe_zone(pe: float) -> dict:
    if pe > 40:   return ZONES[0]
    if pe > 35:   return ZONES[1]
    if pe > 32:   return ZONES[2]
    if pe > 28:   return ZONES[3]
    if pe > 25:   return ZONES[4]
    return ZONES[5]


def fmt_reserve(zone: dict) -> str:
    if zone["reserve_change"] is None:
        return "全部清空"
    if zone["reserve_sign"] == "+":
        return f"+${zone['reserve_change']}"
    if zone["reserve_sign"] == "-":
        return f"-${zone['reserve_change']}"
    return "$0"


# ─── Data Fetching (cached) ───────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_qqq_info() -> dict:
    try:
        info = yf.Ticker("QQQ").info
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
        df = df.dropna(subset=["Close"])
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_price_on_date(ticker: str, target_date: date) -> float | None:
    try:
        start = target_date - timedelta(days=7)
        end = target_date + timedelta(days=2)
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
st.markdown("""
<h1 style="color:#1D1D1F;font-size:clamp(1.4rem,5vw,2.2rem);font-weight:800;margin-bottom:4px;white-space:nowrap;letter-spacing:-0.02em;">
  📈 Andy's FIRE Tracker
</h1>
<p style="color:#6E6E73;font-size:.9rem;margin-top:0;margin-bottom:0;font-weight:400;">
  QQQM / VOO 纳指动态定投 Dashboard · 基于纳斯达克100 TTM PE
</p>
<hr style="border:none;border-top:1px solid rgba(0,0,0,.08);margin:12px 0 10px;">
""", unsafe_allow_html=True)

# ─── Fetch data once ──────────────────────────────────────────────────────────
qqq_info  = fetch_qqq_info()
qqqm_data = fetch_current_price("QQQM")
voo_data  = fetch_current_price("VOO")
auto_pe   = qqq_info["pe"]

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 1 — 市场快照 + PE 仪表盘（合并）
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 市场快照")

toggle_col, _ = st.columns([2, 6])
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

left_col, right_col = st.columns([1, 2.2])

with left_col:
    st.metric("纳斯达克100 TTM PE",
              f"{current_pe:.2f}" if current_pe else "—",
              help="来自 QQQ trailingPE，可手动覆盖以 Wind / Gurufocus 数据为准")
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
        gauge_max = 55
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(float(current_pe), gauge_max),
            number={"font": {"size": 40, "color": "#1D1D1F"}, "valueformat": ".1f", "prefix": "PE "},
            title={"text": f"{cz['icon']} {cz['zone_name']}", "font": {"size": 20, "color": "#1D1D1F"}},
            gauge={
                "axis": {
                    "range": [0, gauge_max],
                    "tickvals": [25, 28, 32, 35, 40],
                    "tickcolor": "rgba(0,0,0,0.3)",
                    "tickfont": {"color": "rgba(0,0,0,0.55)", "size": 11},
                    "tickwidth": 1,
                },
                "bar": {"color": "#1D1D1F", "thickness": 0.04},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,   25],        "color": "#0e7490"},
                    {"range": [25,  28],        "color": "#15803d"},
                    {"range": [28,  32],        "color": "#4d7c0f"},
                    {"range": [32,  35],        "color": "#a16207"},
                    {"range": [35,  40],        "color": "#c2410c"},
                    {"range": [40,  gauge_max], "color": "#8b0000"},
                ],
                "threshold": {
                    "line": {"color": "#1D1D1F", "width": 4},
                    "thickness": 0.85,
                    "value": min(float(current_pe), gauge_max),
                },
            },
        ))
        gauge_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=290,
            margin=dict(l=40, r=40, t=50, b=0),
            font={"color": "#1D1D1F"},
        )
        st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})

        # 区间图例（gauge 内部，居中对齐）
        zone_legend = [
            ("≤25",  "黄金坑",   "#0e7490"),
            ("25-28","大甩卖",   "#15803d"),
            ("28-32","小捡漏",   "#4d7c0f"),
            ("32-35","正常发挥", "#a16207"),
            ("35-40","有点贵",   "#c2410c"),
            (">40",  "危险！别碰","#8b0000"),
        ]
        chips = ""
        for rng, name, bg in zone_legend:
            is_cur = (name == cz["zone_name"])
            border = "2px solid #1D1D1F" if is_cur else "2px solid transparent"
            scale  = "font-size:13px;font-weight:700;padding:5px 14px;" if is_cur else "font-size:11px;padding:4px 10px;opacity:0.7;"
            chips += (f'<span style="background:{bg};color:white;border-radius:20px;'
                      f'{scale}border:{border};display:inline-block;margin:3px;">'
                      f'{rng}&nbsp;{name}</span>')
        st.markdown(
            f'<div style="text-align:center;margin-top:-6px;margin-bottom:10px;">{chips}</div>',
            unsafe_allow_html=True,
        )

    # 操作建议横条
    tc = cz["text_color"]
    st.markdown(f"""
    <div class="action-bar" style="background:{cz['gradient']};color:{tc};">
      <div class="action-bar-left">
        <p style="margin:0;font-size:11px;opacity:.6;text-transform:uppercase;letter-spacing:.12em;font-weight:500;">当前区间</p>
        <p style="margin:6px 0 0;font-size:clamp(17px,3vw,24px);font-weight:800;letter-spacing:-.01em;">{cz['icon']} {cz['zone_name']} · {cz['range_label']}</p>
      </div>
      <div class="action-bar-right">
        <div><p class="ab-label">买入标的</p><p class="ab-value">{cz['target']}</p></div>
        <div class="ab-divider"></div>
        <div><p class="ab-label">买入倍数</p><p class="ab-value">{cz['multiplier']}</p></div>
        <div class="ab-divider"></div>
        <div><p class="ab-label">建议金额</p><p class="ab-value">{c_amt}</p></div>
        <div class="ab-divider"></div>
        <div><p class="ab-label">结余变化</p><p class="ab-value">{c_res}</p></div>
      </div>
    </div>
    <p style="color:#6E6E73;font-size:12px;margin:8px 0 0 6px;letter-spacing:.01em;">{cz['reserve_note']}</p>
    """, unsafe_allow_html=True)
else:
    st.warning("无法自动获取 PE，请开启手动输入。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 2 — QQQM 日 K 线图
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📉 QQQM 日 K 线图")

PERIOD_OPTS = {"1 月": "1mo", "3 月": "3mo", "6 月": "6mo", "1 年": "1y", "3 年": "3y", "全部": "max"}
sel_label  = st.selectbox("时间窗口", list(PERIOD_OPTS.keys()), index=3, key="kline_period")
kline_df   = fetch_history("QQQM", PERIOD_OPTS[sel_label])

if not kline_df.empty:
    df_k = kline_df.copy()
    df_k["MA20"] = df_k["Close"].rolling(20).mean()
    df_k["MA60"] = df_k["Close"].rolling(60).mean()
    vol_colors = ["#22c55e" if c >= o else "#ef4444"
                  for c, o in zip(df_k["Close"], df_k["Open"])]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(
        x=df_k.index, open=df_k["Open"], high=df_k["High"],
        low=df_k["Low"], close=df_k["Close"],
        increasing=dict(fillcolor="#22c55e", line=dict(color="#22c55e")),
        decreasing=dict(fillcolor="#ef4444", line=dict(color="#ef4444")),
        name="QQQM", showlegend=True,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df_k.index, y=df_k["MA20"],
        line=dict(color="#fbbf24", width=1.5), name="MA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_k.index, y=df_k["MA60"],
        line=dict(color="#f97316", width=1.5), name="MA60"), row=1, col=1)

    fig.add_trace(go.Bar(x=df_k.index, y=df_k["Volume"],
        marker_color=vol_colors, name="成交量", showlegend=False), row=2, col=1)

    fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(color="#1D1D1F"), height=560,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.08)", borderwidth=1),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.05)",
                     rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.05)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("无法加载 QQQM 历史数据。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 3 — QQQM 历史数据 + PE 表
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📋 QQQM 历史数据 + PE 估算")

HIST_OPTS = {"近 30 天": "1mo", "近 90 天": "3mo", "近半年": "6mo", "近 1 年": "1y", "全部": "max"}
hist_label = st.selectbox("数据范围", list(HIST_OPTS.keys()), index=2, key="hist_range")
hist_df    = fetch_history("QQQM", HIST_OPTS[hist_label])

if not hist_df.empty and current_pe and qqqm_data["price"]:
    cur_pe    = float(current_pe)
    cur_price = float(qqqm_data["price"])
    # 历史PE = (历史收盘价 / 当前收盘价) × 当前爬取PE，直接用爬取值推算，无需EPS
    hist_pe = (hist_df["Close"] / cur_price * cur_pe).round(2)
    tbl = pd.DataFrame({
        "日期":   hist_df.index.strftime("%Y-%m-%d"),
        "开盘":   hist_df["Open"].round(2),
        "收盘":   hist_df["Close"].round(2),
        "最高":   hist_df["High"].round(2),
        "最低":   hist_df["Low"].round(2),
        "PE":     hist_pe,
    }).reset_index(drop=True)
    tbl["PE 区间"] = tbl["PE"].apply(lambda v: get_pe_zone(float(v))["zone_name"])

    def _style_zone(val):
        bg = ZONE_BG_MAP.get(val, "")
        return f"background-color:{bg};color:white;font-weight:600;" if bg else ""

    st.dataframe(
        tbl.style
            .format({"开盘": "{:.2f}", "收盘": "{:.2f}", "最高": "{:.2f}", "最低": "{:.2f}", "PE": "{:.2f}"})
            .map(_style_zone, subset=["PE 区间"]),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        f"PE 基于爬取的实时 NDX PE（{cur_pe:.2f}）按价格比例推算，当日数值与实时一致。"
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
        use_container_width=True, hide_index=True,
    )
    st.caption("边界规则：PE 恰好等于边界值时（如 35 或 32），按**较低**区间执行。")

# ═══════════════════════════════════════════════════════════════════════════════
# 模块 6 — 定投记录
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 💰 定投记录")

# CSV 导入 / 导出
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
        st.download_button("📥 导出 CSV", data=csv_bytes,
                           file_name=f"fire_tracker_{date.today()}.csv", mime="text/csv")

# 新增记录表单
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
        rec_date   = st.date_input("日期", value=date.today(), key="rec_date")
        rec_pe     = st.number_input("当周 PE", min_value=0.0, value=default_pe_val,
                                     step=0.1, format="%.2f", key="rec_pe")
    with f2:
        rec_target = st.selectbox("买入标的", ["VOO", "QQQM", "无（停止定投）"], key="rec_target")
        rec_amount = st.number_input("买入金额 ($)", min_value=0.0, value=default_amount,
                                     step=1.0, format="%.2f", key="rec_amount")
    with f3:
        rec_price  = st.number_input("买入价格（填 0 自动获取）", min_value=0.0, value=0.0,
                                     step=0.01, format="%.2f", key="rec_price")
        rec_fee    = st.number_input("手续费 ($)", min_value=0.0, value=1.00,
                                     step=0.01, format="%.2f", key="rec_fee")
    with f4:
        rec_reserve = st.number_input("本周留存 ($，负数=取用结余)", value=default_reserve,
                                      step=1.0, format="%.2f", key="rec_reserve")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        submit = st.button("✅ 提交记录", use_container_width=True, key="submit_rec")

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

        shares     = rec_amount / actual_price if actual_price > 0 else 0.0
        prev_res   = st.session_state.records[-1].get("累计结余", 0) if st.session_state.records else 0
        cum_res    = prev_res + rec_reserve

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

# 记录表格 + 实时盈亏
if st.session_state.records:
    rdf = pd.DataFrame(st.session_state.records)
    qp  = qqqm_data["price"] or 0.0
    vp  = voo_data["price"]  or 0.0

    def _cur_price(target):
        if "QQQM" in str(target): return qp
        if "VOO"  in str(target): return vp
        return 0.0

    rdf["当前市值"]       = (rdf["股数"] * rdf["买入标的"].apply(_cur_price)).round(2)
    rdf["纯盈利 (不含费)"] = (rdf["当前市值"] - rdf["买入金额"]).round(2)
    rdf["实际盈利 (含费)"] = (rdf["当前市值"] - rdf["买入金额"] - rdf["手续费"]).round(2)

    st.dataframe(rdf, use_container_width=True, hide_index=True)

    # 汇总面板
    st.markdown("### 汇总")
    total_in   = rdf["买入金额"].sum()
    total_mv   = rdf["当前市值"].sum()
    total_pp   = rdf["纯盈利 (不含费)"].sum()
    total_ap   = rdf["实际盈利 (含费)"].sum()
    total_fee  = rdf["手续费"].sum()
    last_res   = rdf["累计结余"].iloc[-1]
    pct        = (total_mv - total_in) / total_in * 100 if total_in > 0 else 0

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("累计投入",       f"${total_in:,.2f}")
    s2.metric("当前市值",       f"${total_mv:,.2f}", f"{pct:+.2f}%")
    s3.metric("纯盈利 (不含费)", f"${total_pp:,.2f}")
    s4.metric("实际盈利 (含费)", f"${total_ap:,.2f}", f"累计手续费 ${total_fee:.2f}")
    s5.metric("账户结余",       f"${last_res:,.2f}")

    # 记录管理
    with st.expander("🗑️ 记录管理"):
        mg1, mg2 = st.columns(2)
        with mg1:
            if st.button("清空全部记录", type="secondary"):
                st.session_state.records = []
                st.rerun()
        with mg2:
            n = len(st.session_state.records)
            del_n = st.number_input("删除第 N 条（从 1 开始）",
                                    min_value=1, max_value=n, step=1, key="del_n")
            if st.button("删除该条", type="secondary"):
                st.session_state.records.pop(int(del_n) - 1)
                st.rerun()
else:
    st.info("暂无定投记录。点击上方「新增定投记录」开始记录。")
