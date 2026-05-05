"""
Taiwan Stock Coverage — Admin Dashboard
Run: streamlit run admin.py
"""

import os
import subprocess
import sys
import threading
import queue
import time
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
PYTHON = sys.executable

SECTORS = [
    "Advertising Agencies", "Aerospace & Defense", "Agricultural Inputs",
    "Airlines", "Aluminum", "Apparel Manufacturing", "Apparel Retail",
    "Asset Management", "Auto & Truck Dealerships", "Auto Manufacturers",
    "Auto Parts", "Banks", "Banks - Regional", "Beverages - Non-Alcoholic",
    "Biotech - Therapeutics", "Biotechnology", "Broadcasting",
    "Building Materials", "Building Products & Equipment",
    "Business Equipment & Supplies", "Capital Markets", "Chemicals",
    "Communication Equipment", "Computer Hardware", "Conglomerates",
    "Consulting Services", "Consumer Electronics", "Copper",
    "Credit Services", "Department Stores",
    "Drug Manufacturers - Specialty & Generic",
    "Education & Training Services", "Electrical Equipment & Parts",
    "Electronic Components", "Electronic Gaming & Multimedia",
    "Electronics & Computer Distribution", "Engineering & Construction",
    "Entertainment", "Farm Products", "Financial Conglomerates",
    "Food Distribution", "Footwear & Accessories",
    "Furnishings, Fixtures & Appliances", "Gambling",
    "Home Improvement Retail", "Household & Personal Products",
    "Industrial Distribution", "Information Technology Services",
    "Insurance - Diversified", "Insurance - Life",
    "Insurance - Property & Casualty", "Insurance - Reinsurance",
    "Insurance Brokers", "Integrated Freight & Logistics",
    "Internet Content & Information", "Internet Retail", "Leisure",
    "Lodging", "Lumber & Wood Production", "Marine Shipping",
    "Medical Devices", "Metal Fabrication",
    "Oil & Gas Equipment & Services", "Oil & Gas Refining & Marketing",
    "Other Industrial Metals & Mining", "Packaged Foods",
    "Packaging & Containers", "Personal Services",
    "Pollution & Treatment Controls", "Publishing", "Railroads",
    "Real Estate - Development", "Real Estate - Diversified",
    "Real Estate Services", "Recreational Vehicles",
    "Scientific & Technical Instruments", "Security & Protection Services",
    "Semiconductor Equipment & Materials", "Semiconductors",
    "Software - Application", "Software - Infrastructure", "Solar",
    "Specialty Business Services", "Specialty Chemicals",
    "Specialty Industrial Machinery", "Specialty Retail",
    "Staffing & Employment Services", "Steel", "Telecom Services",
    "Textile Manufacturing", "Thermal Coal", "Tools & Accessories",
    "Trucking", "Utilities - Regulated Electric",
    "Utilities - Regulated Gas", "Utilities - Regulated Water",
    "Utilities - Renewable", "Waste Management",
]

st.set_page_config(
    page_title="TW Coverage Admin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stButton > button { width: 100%; }
.log-box { font-family: monospace; font-size: 12px; background: #0e1117;
           color: #00ff41; padding: 12px; border-radius: 6px;
           max-height: 400px; overflow-y: auto; white-space: pre-wrap; }
.metric-card { background: #1e2130; padding: 12px 16px; border-radius: 8px;
               border-left: 3px solid #4c9aff; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)


def run_script(cmd: list) -> None:
    """Stream subprocess output to a Streamlit placeholder."""
    st.session_state["running"] = True
    output_box = st.empty()
    lines = []

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_ROOT,
        )
        for line in proc.stdout:
            lines.append(line.rstrip())
            output_box.markdown(
                f'<div class="log-box">' + "\n".join(lines[-200:]) + "</div>",
                unsafe_allow_html=True,
            )
        proc.wait()
        status = "✅ 完成" if proc.returncode == 0 else f"❌ 錯誤 (exit {proc.returncode})"
        st.info(status)
    except Exception as e:
        st.error(f"執行失敗：{e}")
    finally:
        st.session_state["running"] = False


def scope_picker(key_prefix: str) -> list:
    """Returns a list of CLI args based on user-selected scope."""
    scope_type = st.radio(
        "範圍",
        ["單一 Ticker", "多個 Ticker", "批次 (Batch)", "產業 (Sector)", "全部"],
        horizontal=True,
        key=f"{key_prefix}_scope_type",
    )

    if scope_type == "單一 Ticker":
        ticker = st.text_input("Ticker 代碼", placeholder="例：2330", key=f"{key_prefix}_ticker")
        return [ticker.strip()] if ticker.strip() else []

    elif scope_type == "多個 Ticker":
        tickers = st.text_input("多個代碼（空格分隔）", placeholder="例：2330 2454 3034", key=f"{key_prefix}_tickers")
        return tickers.strip().split() if tickers.strip() else []

    elif scope_type == "批次 (Batch)":
        batch = st.number_input("批次號碼", min_value=1, max_value=999, value=101, step=1, key=f"{key_prefix}_batch")
        return ["--batch", str(int(batch))]

    elif scope_type == "產業 (Sector)":
        sector = st.selectbox("選擇產業", SECTORS, key=f"{key_prefix}_sector")
        return ["--sector", sector]

    else:  # 全部
        st.warning("⚠️ 全部更新需要較長時間（1,700+ 檔）")
        return []


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 TW Coverage")
    st.caption("Admin Dashboard")
    st.divider()

    page = st.radio(
        "功能",
        [
            "🏠 總覽",
            "💰 更新財報",
            "📈 更新估值",
            "🔗 重建 Wikilink 索引",
            "🗺️ 重建主題頁",
            "🔍 品質檢查",
            "🔭 反向搜尋",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"專案：{PROJECT_ROOT}")


# ─── Pages ────────────────────────────────────────────────────────────────────

if page == "🏠 總覽":
    st.title("Taiwan Stock Coverage")
    st.markdown("1,735 家台股的研究資料庫 + Wikilink 知識圖譜")

    col1, col2, col3 = st.columns(3)

    with col1:
        count = sum(
            len(os.listdir(os.path.join(PROJECT_ROOT, "Pilot_Reports", d)))
            for d in os.listdir(os.path.join(PROJECT_ROOT, "Pilot_Reports"))
            if os.path.isdir(os.path.join(PROJECT_ROOT, "Pilot_Reports", d))
        )
        st.metric("總 Ticker 數", count)

    with col2:
        sectors = len([
            d for d in os.listdir(os.path.join(PROJECT_ROOT, "Pilot_Reports"))
            if os.path.isdir(os.path.join(PROJECT_ROOT, "Pilot_Reports", d))
        ])
        st.metric("產業數", sectors)

    with col3:
        themes = len([
            f for f in os.listdir(os.path.join(PROJECT_ROOT, "themes"))
            if f.endswith(".md") and f != "README.md"
        ]) if os.path.exists(os.path.join(PROJECT_ROOT, "themes")) else 0
        st.metric("主題頁數", themes)

    st.divider()
    st.markdown("""
    ### 常用流程
    | 動作 | 使用功能 | 頻率 |
    |---|---|---|
    | 每週更新估值（快速） | 📈 更新估值 → 全部 | 每週 |
    | 每月更新完整財報 | 💰 更新財報 → 全部 | 每月 |
    | 新增/更新公司後重建索引 | 🔗 重建 Wikilink 索引 | 每次 push 前 |
    | 搜尋主題相關公司 | 🔭 反向搜尋 | 隨時 |
    | 批次完成後品質檢查 | 🔍 品質檢查 | 每批次完成後 |
    """)


elif page == "💰 更新財報":
    st.title("💰 更新財報")
    st.markdown("從 yfinance 抓取最新的年度（3年）及季度（4Q）財務數據，更新 `## 財務概況` 區塊。業務描述與供應鏈**不受影響**。")

    args = scope_picker("financials")
    dry_run = st.checkbox("Dry Run（預覽不寫入）", key="financials_dry")

    if st.button("🚀 開始更新財報", disabled=st.session_state.get("running", False)):
        if args is not None:
            cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "update_financials.py")] + args
            if dry_run:
                cmd.append("--dry-run")
            run_script(cmd)


elif page == "📈 更新估值":
    st.title("📈 更新估值")
    st.markdown("只更新 P/E、Forward P/E、P/S、P/B、EV/EBITDA 及股價。比完整財報快 3x。")

    args = scope_picker("valuation")
    dry_run = st.checkbox("Dry Run（預覽不寫入）", key="valuation_dry")

    if st.button("🚀 開始更新估值", disabled=st.session_state.get("running", False)):
        if args is not None:
            cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "update_valuation.py")] + args
            if dry_run:
                cmd.append("--dry-run")
            run_script(cmd)


elif page == "🔗 重建 Wikilink 索引":
    st.title("🔗 重建 Wikilink 索引")
    st.markdown("掃描所有報告的 `[[wikilink]]`，重建 `WIKILINKS.md` 索引。新增或更新公司後執行一次。")

    st.info("此操作掃描所有 1,700+ 檔，約需 10–30 秒。")

    if st.button("🚀 重建索引", disabled=st.session_state.get("running", False)):
        run_script([PYTHON, os.path.join(SCRIPTS_DIR, "build_wikilink_index.py")])


elif page == "🗺️ 重建主題頁":
    st.title("🗺️ 重建主題頁")
    st.markdown("根據 wikilink 圖譜生成 `themes/` 下的主題供應鏈頁面（CoWoS、HBM、矽光子...）。")

    theme_input = st.text_input(
        "指定主題（留空 = 全部重建）",
        placeholder="例：CoWoS",
        key="theme_name",
    )

    if st.button("🚀 重建主題頁", disabled=st.session_state.get("running", False)):
        cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "build_themes.py")]
        if theme_input.strip():
            cmd.append(theme_input.strip())
        run_script(cmd)


elif page == "🔍 品質檢查":
    st.title("🔍 品質檢查")
    st.markdown("檢查 wikilink 數量、佔位符、元數據完整性、章節結構等品質規則。")

    check_type = st.radio(
        "範圍",
        ["指定批次", "全部已完成批次"],
        horizontal=True,
        key="audit_type",
    )

    if check_type == "指定批次":
        batch = st.number_input("批次號碼", min_value=1, max_value=999, value=101, step=1, key="audit_batch")
        args = [str(int(batch))]
    else:
        args = ["--all"]

    verbose = st.checkbox("詳細輸出（-v）", value=True, key="audit_verbose")

    if st.button("🚀 開始檢查", disabled=st.session_state.get("running", False)):
        cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "audit_batch.py")] + args
        if verbose:
            cmd.append("-v")
        run_script(cmd)


elif page == "🔭 反向搜尋":
    st.title("🔭 反向搜尋")
    st.markdown("輸入一個關鍵字（buzzword），找出資料庫中哪些公司與它相關。")

    keyword = st.text_input(
        "搜尋關鍵字",
        placeholder="例：液冷散熱、矽光子、CPO、核融合",
        key="discover_keyword",
    )

    col1, col2 = st.columns(2)
    with col1:
        smart = st.checkbox("Smart 模式（自動篩選相關產業）", value=True, key="discover_smart")
    with col2:
        apply_links = st.checkbox("Apply（自動補 wikilink 到報告）", value=False, key="discover_apply")

    if apply_links:
        st.warning("⚠️ Apply 模式會直接修改報告檔案，請確認後再執行。")

    sector_filter = st.text_input(
        "限定產業（選填，多個用逗號隔開）",
        placeholder="例：Semiconductors,Electronic Components",
        key="discover_sector",
    )

    if st.button("🔍 搜尋", disabled=st.session_state.get("running", False)):
        if not keyword.strip():
            st.error("請輸入搜尋關鍵字")
        else:
            cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "discover.py"), keyword.strip()]
            if smart:
                cmd.append("--smart")
            if apply_links:
                cmd.append("--apply")
            if sector_filter.strip():
                cmd.extend(["--sectors", sector_filter.strip()])
            run_script(cmd)
