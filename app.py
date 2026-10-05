import streamlit as st
import json
import os

st.set_page_config(page_title="테크노푸드몰 관리비 고지서", page_icon="🏢", layout="wide")

DATA_FILE = "data.json"

DEFAULT_SHOPS = {
    "지하105-3호 바른푸드(쌀국수)": {"전월전기": 123243.4, "전월수도": 1549.0},
    "A동102호 두찜": {"전월전기": 65010.4, "전월수도": 1391.0},
    "A동104호 멍앤멍": {"전월전기": 20611.4, "전월수도": 170.0},
    "A동303호 점핑": {"전월전기": 45613.6, "전월수도": 138.0},
    "B동107호 덮밥90도": {"전월전기": 65680.0, "전월수도": 712.0},
    "B동108호 부릉": {"전월전기": 28996.3, "전월수도": 2.0}
}

DEFAULT_CONFIG = {
    "month": "10월",
    "n_shops": 6,
    "total_elec_kwh": 0.0,
    "total_elec_fee": 0,
    "total_water_ton": 0.0,
    "total_water_fee": 11784000,
    "elec_unit": 135.0,
    "account": "카카오뱅크 7942-07-89864 (예금주: 하기수)"
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"shops": DEFAULT_SHOPS, "config": DEFAULT_CONFIG}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

st.title("🏢 테크노푸드몰 관리비 고지서")
st.caption("당월 계량기 수치를 입력하시면 고정 공용비가 포함된 10월 관리비가 자동 계산됩니다.")

tab1, tab2 = st.tabs(["📲 [점주용] 관리비 조회", "⚙️ [관리자] 단가 및 공용비 설정"])

# ---------------------------------------------------------
# TAB 1: [점주용] 관리비 조회
# ---------------------------------------------------------
with tab1:
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    st.subheader(f"📌 {cfg['month']} 관리비 조회")
    
    selected_shop = st.selectbox("가게(점포)를 선택하세요", list(shops.keys()))
    shop_info = shops[selected_shop]
    
    st.info(f"💡 [전월 기준 수치] 전기: {shop_info['전월전기']:,} kWh | 수도: {shop_info['전월수도']:,} ton")
    
    col1, col2 = st.columns(2)
    with col1:
        curr_elec = st.number_input("⚡ 당월 전기 계량기 수치", value=float(shop_info["전월전기"]))
    with col2:
        curr_water = st.number_input("💧 당월 수도 계량기 수치", value=float(shop_info
