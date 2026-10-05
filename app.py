import streamlit as st
import json
import os

st.set_page_config(page_title="테크노푸드몰 관리비 고지서", page_icon="🏢", layout="wide")

DATA_FILE = "data.json"

# 10월 시작 기준 (9월 엑셀의 정확한 당월검침 수치 반영)
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
    # 강제로 최신 기준값으로 초기화되도록 기존 파일 삭제 후 재생성
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
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

# ---------------------------------------------------------
# TAB 1: 점주용 관리비 조회
# ---------------------------------------------------------
with tab1:
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    st.subheader(f"{cfg['month']} 관리비 조회")
    
    selected_shop = st.selectbox("가게(점포)를 선택하세요", list(shops.keys()))
    shop_info = shops[selected_shop]
    
    st.info(f"전월 기준 수치 - 전기: {shop_info['전월전기']:,} kWh / 수도: {shop_info['전월수도']:,} ton")
    
    col1, col2 = st.columns(2)
    with col1:
        curr_elec = st.number_input("당월 전기 계량기 수치", value=float(shop_info["전월전기"]))
    with col2:
        curr_water = st.number_input("당월 수도 계량기 수치", value=float(shop_info["전월수도"]))
        
    use_elec = curr_elec - shop_info["전월전기"]
    use_water = curr_water - shop_info["전월수도"]
    
    if use_elec >= 0 and use_water >= 0:
        st.caption(f"당월 사용량 - 전기: {use_elec:.1f} kWh / 수도: {use_water:.1f} ton")
        
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
            
            fixed_sum = public_elec_fee + public_water_fee + elevator_fee + taedong_fee + repair_reserve + daehan_elec_fee
            total_fee = indiv_elec_fee + indiv_water_fee + fixed_sum
            
            db["shops"][selected_shop] = {"전월전기": curr_elec, "전월수도": curr_water}
            save_data(db)
            
            st.markdown("---")
            st.success(f"{selected_shop}님의 {cfg['month']} 총 청구금액: {total_fee:,.0f} 원 (수치 저장 완료!)")
            st.info(f"입금계좌: {cfg['account']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 전기 / 수도 사용료")
                st.write(f"- 사용 전기요금: {indiv_elec_fee:,.0f}원 (사용량: {use_elec:.1f} kWh)")
                st.write(f"- 사용 수도요금: {indiv_water_fee:,.0f}원 (사용량: {use_water:.1f} ton)")
            
            with c2:
                st.markdown("### 공용 관리비 분담 항목")
                st.write(f"- 공용전기요금: {public_elec_fee:,.0f}원 (고정)")
                st.write(f"- 공용수도요금: {public_water_fee:,.0f}원 (고정)")
                st.write(f"- 엘리베이터 요금: {elevator_fee:,.0f}원 {'(점핑 +50,000원 포함)' if '점핑' in selected_shop else ''}")
                st.write(f"- 태동환경: {
