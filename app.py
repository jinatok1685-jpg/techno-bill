import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="테크노푸드몰", layout="wide")

st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        border: 1px solid #d1d5db;
        background-color: #f9fafb;
        color: #374151;
    }
    .stButton > button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "data.json"

DEFAULT_SHOPS = {
    "지하105-3호 바른푸드(쌀국수)": {"전월전기": 123243.4, "전월수도": 1549.0, "당월전기": 0.0, "당월수도": 0.0},
    "A동102호 두찜": {"전월전기": 65010.4, "전월수도": 1391.0, "당월전기": 0.0, "당월수도": 0.0},
    "A동104호 멍앤멍": {"전월전기": 20611.4, "전월수도": 170.0, "당월전기": 0.0, "당월수도": 0.0},
    "A동303호 점핑": {"전월전기": 45613.6, "전월수도": 138.0, "당월전기": 0.0, "당월수도": 0.0},
    "B동107호 덮밥90도": {"전월전기": 65680.0, "전월수도": 712.0, "당월전기": 0.0, "당월수도": 0.0},
    "B동108호 부릉": {"전월전기": 28996.3, "전월수도": 2.0, "당월전기": 0.0, "당월수도": 0.0}
}

DEFAULT_CONFIG = {
    "month": "10월",
    "n_shops": 6,
    "account": "카카오뱅크 7942-07-89864 (예금주: 하기수)",
    "admin_password": "1234"
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for shop in data.get("shops", {}):
                    if "당월전기" not in data["shops"][shop]:
                        data["shops"][shop]["당월전기"] = 0.0
                    if "당월수도" not in data["shops"][shop]:
                        data["shops"][shop]["당월수도"] = 0.0
                if "config" in data and "admin_password" not in data["config"]:
                    data["config"]["admin_password"] = "1234"
                if "posts" not in data:
                    data["posts"] = []
                return data
        except Exception:
            pass
    return {"shops": DEFAULT_SHOPS, "config": DEFAULT_CONFIG, "posts": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

st.title("테크노푸드몰")
st.caption("당월 계량기 수치를 입력하시면 요청하신 공식에 맞춰 전기세, 수도세 및 공용 관리비가 자동 계산됩니다.")

tab1, tab2, tab3 = st.tabs(["점주용 관리비 조회", "📷 계량기 증빙 사진 게시판", "관리자 설정"])

with tab1:
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    st.subheader(f"{cfg['month']} 관리비 조회")
    st.markdown("##### 🏪 본인의 점포를 **클릭하여** 선택해주세요")
    
    shop_list = list(shops.keys())
    
    if "selected_shop" not in st.session_state or st.session_state.selected_shop not in shop_list:
        st.session_state.selected_shop = shop_list[0]

    cols = st.columns(len(shop_list))
    for idx, shop_name in enumerate(shop_list):
        with cols[idx]:
            is_selected = (st.session_state.selected_shop == shop_name)
            if is_selected:
                btn_label = f"👉 [ {shop_name} ]"
            else:
                btn_label = shop_name
                
            if st.button(btn_label, key=f"btn_shop_{idx}", use_container_width=True):
                st.session_state.selected_shop = shop_name
                st.rerun()

    selected_shop = st.session_state.selected_shop
    shop_info = shops[selected_shop]
    
    st.markdown("---")
    st.markdown(f"""
    <div style="padding: 15px 20px; background-color: #eff6ff; border-left: 6px solid #3b82f6; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0; color: #1e40af;">🔍 현재 선택된 점포: {selected_shop}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚡ 전기 계량기")
    st.info(f"전월 기준 전기 수치: **{shop_info['전월전기']:,.1f} kWh**")
    
    elec_key = f"c_elec_{selected_shop}"
    if elec_key not in st.session_state:
        st.session_state[elec_key] = float(shop_info["당월전기"])
        
    curr_elec = st.number_input("당월 전기 계량기 수치 입력", value=float(shop_info["당월전기"]), step=1.0, format="%.1f", key=elec_key)
    
    st.markdown("")
    
    st.markdown("### 💧 수도 계량기")
    st.info(f"전월 기준 수도 수치: **{shop_info['전월수도']:,.1f} ton**")
    
    water_key = f"c_water_{selected_shop}"
    if water_key not in st.session_state:
        st.session_state[water_key] = float(shop_info["당월수도"])
        
    curr_water = st.number_input("당월 수도 계량기 수치 입력", value=float(shop_info["당월수도"]), step=1.0, format="%.1f", key=water_key)
        
    use_elec = round(curr_elec - shop_info["전월전기"], 1)
    use_water = round(curr_water - shop_info["전월수도"], 1)
    
    st.markdown("---")
    
    if curr_elec > 0 or curr_water > 0:
        invalid_elec = (curr_elec > 0 and use_elec < 0)
        invalid_water = (curr_water > 0 and use_water < 0)
        
        if invalid_elec or invalid_water:
            st.warning("⚠️ 당월 계량기 수치가 전월 기준 수치보다 작습니다. 수치를 확인해주세요.")
        else:
            disp_elec = use_elec if curr_elec > 0 else 0.0
            disp_water = use_water if curr_water > 0 else 0.0
            st.success(f"📊 당월 사용량 - 전기: {disp_elec:,.1f} kWh / 수도: {disp_water:,.1f} ton")
        
    if st.button("이번 달 관리비 고지서 계산하기 및 저장", key=f"calc_btn_{selected_shop}"):
        if curr_elec == 0.0 and curr_water == 0.0:
            st.error("당월 계량기 수치를 입력해주세요.")
        elif use_elec < 0 or use_water < 0:
            st.error("당월 수치가 전월 수치보다 작습니다. 계량기 수치를 확인해주세요.")
        else:
            db["shops"][selected_shop]["당월전기"] = curr_elec
            db["shops"][selected_shop]["당월수도"] = curr_water
            save_data(db)
            
            base_elec_share = 750000 / n
            public_elec_fee = 75000
            indiv_elec_fee = (use_elec * 140.0) + public_elec_fee + base_elec_share
            
            public_water_fee = 13000
            indiv_water_fee = (use_water * 3000.0) + public_water_fee
            
            base_elevator = 70000 / n
            elevator_fee = base_elevator + 50000 if "점핑" in selected_shop else base_elevator
            taedong_fee = 370000 / n
            repair_reserve = 10000
            daehan_elec_fee = 231000 / n
            
            fixed_sum = elevator_fee + taedong_fee + repair_reserve + daehan_elec_fee
            total_fee = indiv_elec_fee + indiv_water_fee + fixed_sum
            
            st.markdown("---")
            st.success(f"📢 {selected_shop}님의 {cfg['month']} 총 청구금액: {total_fee:,.0f} 원")
            st.info(f"입금계좌: {cfg['account']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 전기 및 수도 요금")
                st.write(f"- **전기세**: {indiv_elec_fee:,.0f}원")
                st.caption(f"  (사용량 {use_elec:,.1f}kWh × 140원 + 공용전기 75,000원 + 기본전기 {base_elec_share:,.0f}원)")
                
                st.write(f"- **수도세**: {indiv_water_fee:,.0f}원")
                st.caption(f"  (사용량 {use_water:,.1f}톤 × 3,000원 + 공용수도 13,000원)")
            
            with c2:
                st.markdown("### 기타 공용 관리비 분담 항목")
                jump_text = " (점핑 +50,000원 포함)" if "점핑" in selected_shop else ""
                st.write(f"- 엘리베이터 요금: {elevator_fee:,.0f}원{jump_text}")
                st.write(f"- 태동환경: {taedong_fee:,.0f}원")
                st.write(f"- 수선예비비: {repair_reserve:,.0f}원")
                st.write(f"- 대한전기: {daehan_elec_fee:,.0f}원")

with tab2:
    st.subheader(f"📷 {db['config']['month']} 계량기 증빙 사진 게시판")
    st.caption("점주님들께서 입력하신 계량기 수치의 증빙 사진을 업로드하고 다른 점주님들과 공유하는 공간입니다
