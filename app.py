import streamlit as st
import json
import os

st.set_page_config(page_title="테크노푸드몰 관리비 고지서", layout="wide")

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

st.title("테크노푸드몰 관리비 고지서")
st.caption("당월 계량기 수치를 입력하시면 고정 공용비가 포함된 10월 관리비가 자동 계산됩니다.")

tab1, tab2 = st.tabs(["점주용 관리비 조회", "관리자 단가 및 공용비 설정"])

with tab1:
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    st.subheader(cfg["month"] + " 관리비 조회")
    
    selected_shop = st.selectbox("가게(점포)를 선택하세요", list(shops.keys()))
    shop_info = shops[selected_shop]
    
    st.info("전월 기준 수치 - 전기: " + f"{shop_info['전월전기']:,}" + " kWh / 수도: " + f"{shop_info['전월수도']:,}" + " ton")
    
    col1, col2 = st.columns(2)
    with col1:
        curr_elec = st.number_input("당월 전기 계량기 수치", value=float(shop_info["전월전기"]))
    with col2:
        curr_water = st.number_input("당월 수도 계량기 수치", value=float(shop_info["전월수도"]))
        
    use_elec = curr_elec - shop_info["전월전기"]
    use_water = curr_water - shop_info["전월수도"]
    
    if use_elec >= 0 and use_water >= 0:
        st.caption("당월 사용량 - 전기: " + f"{use_elec:.1f}" + " kWh / 수도: " + f"{use_water:.1f}" + " ton")
        
    if st.button("이번 달 관리비 고지서 계산 및 수치 저장"):
        if use_elec < 0 or use_water < 0:
            st.error("당월 수치가 전월 수치보다 작습니다. 계량기 수치를 확인해주세요.")
        else:
            water_unit = cfg["total_water_fee"] / cfg["total_water_ton"] if cfg["total_water_ton"] > 0 else 0
            
            indiv_elec_fee = use_elec * cfg["elec_unit"]
            indiv_water_fee = use_water * water_unit
            
            public_elec_fee = 75000
            public_water_fee = 13000
            
            base_elevator = 70000 / n
            elevator_fee = base_elevator + 50000 if "점핑" in selected_shop else base_elevator
            taedong_fee = 370000 / n
            repair_reserve = 20000
            daehan_elec_fee = 231000 / n
