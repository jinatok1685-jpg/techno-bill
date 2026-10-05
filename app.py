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
st.caption("당월 계량기 수치를 입력하시면 요청하신 공식에 맞춰 전기세, 수도세 및 공용 관리비가 자동 계산됩니다.")

tab1, tab2 = st.tabs(["점주용 관리비 조회", "관리자 설정"])

with tab1:
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    st.subheader(f"{cfg['month']} 관리비 조회")
    
    selected_shop = st.selectbox("가게(점포)를 선택하세요", list(shops.keys()), key="select_shop_main")
    shop_info = shops[selected_shop]
    
    st.info(f"전월 기준 수치 - 전기: {shop_info['전월전기']:,} kWh / 수도: {shop_info['전월수도']:,} ton")
    
    col1, col2 = st.columns(2)
    with col1:
        curr_elec = st.number_input("당월 전기 계량기 수치", value=float(shop_info["전월전기"]), key="c_elec")
    with col2:
        curr_water = st.number_input("당월 수도 계량기 수치", value=float(shop_info["전월수도"]), key="c_water")
        
    use_elec = curr_elec - shop_info["전월전기"]
    use_water = curr_water - shop_info["전월수도"]
    
    if use_elec >= 0 and use_water >= 0:
        st.caption(f"당월 사용량 - 전기: {round(use_elec, 1)} kWh / 수도: {round(use_water, 1)} ton")
        
    if st.button("이번 달 관리비 고지서 계산 및 수치 저장", key="calc_btn"):
        if use_elec < 0 or use_water < 0:
            st.error("당월 수치가 전월 수치보다 작습니다. 계량기 수치를 확인해주세요.")
        else:
            base_elec_share = 750000 / n
            public_elec_fee = 75000
            indiv_elec_fee = (use_elec * 140.0) + public_elec_fee + base_elec_share
            
            public_water_fee = 13000
            indiv_water_fee = (use_water * 3000.0) + public_water_fee
            
            base_elevator = 70000 / n
            elevator_fee = base_elevator + 50000 if "점핑" in selected_shop else base_elevator
            taedong_fee = 370000 / n
            repair_reserve = 20000
            daehan_elec_fee = 231000 / n
            
            fixed_sum = elevator_fee + taedong_fee + repair_reserve + daehan_elec_fee
            total_fee = indiv_elec_fee + indiv_water_fee + fixed_sum
            
            db["shops"][selected_shop] = {"전월전기": curr_elec, "전월수도": curr_water}
            save_data(db)
            
            st.markdown("---")
            st.success(f"{selected_shop}님의 {cfg['month']} 총 청구금액: {total_fee:,.0f} 원 (수치 저장 완료!)")
            st.info(f"입금계좌: {cfg['account']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 전기 및 수도 요금")
                st.write(f"- **전기세**: {indiv_elec_fee:,.0f}원")
                st.caption(f"  (사용량 {round(use_elec, 1)}kWh × 140원 + 공용전기 75,000원 + 기본전기 {base_elec_share:,.0f}원)")
                
                st.write(f"- **수도세**: {indiv_water_fee:,.0f}원")
                st.caption(f"  (사용량 {round(use_water, 1)}톤 × 3,000원 + 공용수도 13,000원)")
            
            with c2:
                st.markdown("### 기타 공용 관리비 분담 항목")
                jump_text = " (점핑 +50,000원 포함)" if "점핑" in selected_shop else ""
                st.write(f"- 엘리베이터 요금: {elevator_fee:,.0f}원{jump_text}")
                st.write(f"- 태동환경: {taedong_fee:,.0f}원")
                st.write(f"- 수선예비비: {repair_reserve:,.0f}원")
                st.write(f"- 대한전기: {daehan_elec_fee:,.0f}원")

with tab2:
    st.subheader("관리자 설정")
    
    st.markdown("### 1. 기본 설정 (정산 월 및 계좌)")
    m = st.text_input("정산 월", value=cfg["month"], key="cfg_month_input")
    n_s = st.number_input("점포 수 (n)", value=int(cfg["n_shops"]), min_value=1, key="cfg_n_input")
    acc = st.text_input("입금 계좌 안내", value=cfg["account"], key="cfg_acc_input")
        
    if st.button("기본 설정 저장하기", key="save_cfg_btn"):
        db["config"] = {
            "month": m,
            "n_shops": int(n_s),
            "account": acc
        }
        save_data(db)
        st.success("기본 설정이 저장되었습니다!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 2. 점포별 기준 수치 수동 수정/이월 점검")
    
    updated_shops = {}
    for shop_name, vals in shops.items():
        st.markdown(f"**{shop_name}**")
        sc1, sc2 = st.columns(2)
        with sc1:
            pe = st.number_input("기준 전기(kWh)", value=float(vals["전월전기"]), key=f"pe_{shop_name}")
        with sc2:
            pw = st.number_input("기준 수도(ton)", value=float(vals["전월수도"]), key=f"pw_{shop_name}")
        updated_shops[shop_name] = {"전월전기": pe, "전월수도": pw}
        st.write("")
    
    if st.button("수치 수동 업데이트 저장", key="save_shops_btn"):
        db["shops"] = updated_shops
        save_data(db)
        st.success("점포 기준 수치가 개별 업데이트되었습니다!")
        st.rerun()
