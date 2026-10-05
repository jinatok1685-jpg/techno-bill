import streamlit as st

st.set_page_config(page_title="테크노푸드몰 관리비 고지서", page_icon="🏢", layout="centered")

DEFAULT_SHOPS = {
    "지하105-3호 바른푸드(쌀국수)": {"전월전기": 121525.5, "전월수도": 1530.0},
    "A동102호 두찜": {"전월전기": 63543.9, "전월수도": 1367.0},
    "A동104호 멍앤멍": {"전월전기": 20357.6, "전월수도": 168.0},
    "A동303호 점핑": {"전월전기": 45371.3, "전월수도": 137.0},
    "B동107호 덮밥90도": {"전월전기": 64458.7, "전월수도": 703.0},
    "B동108호 부릉": {"전월전기": 28438.6, "전월수도": 2.0}
}

DEFAULT_CONFIG = {
    "month": "10월",
    "elec_unit": 135.0,
    "pub_elec": 72920,
    "water_unit": 2946.0,
    "pub_water": 12929,
    "elec_base": 95966,
    "fixed_common": 131833,
    "account": "카카오뱅크 7942-07-89864 (예금주: 하기수)"
}

if "shops" not in st.session_state:
    st.session_state.shops = DEFAULT_SHOPS
if "config" not in st.session_state:
    st.session_state.config = DEFAULT_CONFIG

st.title("🏢 테크노푸드몰 관리비 고지서")
st.caption("당월 계량기 수치를 입력하시면 이번 달 관리비가 즉시 계산됩니다.")

tab1, tab2 = st.tabs(["📲 [점주용] 관리비 조회", "⚙️ [관리자] 단가 및 공용비 설정"])

with tab1:
    cfg = st.session_state.config
    st.subheader(f"📌 {cfg['month']} 관리비 조회")
    
    selected_shop = st.selectbox("가게(점포)를 선택하세요", list(st.session_state.shops.keys()))
    shop_info = st.session_state.shops[selected_shop]
    
    st.info(f"💡 지난달 전기: {shop_info['전월전기']:,} kWh / 지난달 수도: {shop_info['전월수도']:,} ton")
    
    col1, col2 = st.columns(2)
    with col1:
        curr_elec = st.number_input("⚡ 당월 전기 계량기 수치", value=float(shop_info["전월전기"]))
    with col2:
        curr_water = st.number_input("💧 당월 수도 계량기 수치", value=float(shop_info["전월수도"]))
        
    use_elec = curr_elec - shop_info["전월전기"]
    use_water = curr_water - shop_info["전월수도"]
    
    if use_elec >= 0 and use_water >= 0:
        st.caption(f"이번 달 사용량: 전기 {use_elec:.1f} kWh / 수도 {use_water:.1f} ton")
        
    if st.button("📄 이번 달 관리비 고지서 보기"):
        if use_elec < 0 or use_water < 0:
            st.error("당월 수치가 전월 수치보다 작습니다.")
        else:
            elec_fee = (use_elec * cfg["elec_unit"]) + cfg["elec_base"] + cfg["pub_elec"]
            water_fee = (use_water * cfg["water_unit"]) + cfg["pub_water"]
            total_fee = elec_fee + water_fee + cfg["fixed_common"]
            
            st.success(f"🧾 {selected_shop} 총 청구금액: {total_fee:,.0f} 원")
            st.write(f"🏦 입금계좌: {cfg['account']}")
            st.write(f"- 전기요금: {elec_fee:,.0f}원")
            st.write(f"- 수도요금: {water_fee:,.0f}원")
            st.write(f"- 건물공용비: {cfg['fixed_common']:,.0f}원")

with tab2:
    st.subheader("⚙️ 관리자 설정")
    admin_pw = st.text_input("관리자 비밀번호", type="password")
    if admin_pw == "1234":
        with st.form("config_form"):
            new_month = st.text_input("정산 월", value=st.session_state.config["month"])
            new_elec_unit = st.number_input("전기 단가", value=float(st.session_state.config["elec_unit"]))
            new_pub_elec = st.number_input("공용전기료", value=int(st.session_state.config["pub_elec"]))
            new_water_unit = st.number_input("수도 단가", value=float(st.session_state.config["water_unit"]))
            new_pub_water = st.number_input("공용수도료", value=int(st.session_state.config["pub_water"]))
            new_fixed = st.number_input("건물 고정비", value=int(st.session_state.config["fixed_common"]))
            
            if st.form_submit_button("저장하기"):
                st.session_state.config["month"] = new_month
                st.session_state.config["elec_unit"] = new_elec_unit
                st.session_state.config["pub_elec"] = new_pub_elec
                st.session_state.config["water_unit"] = new_water_unit
                st.session_state.config["pub_water"] = new_pub_water
                st.session_state.config["fixed_common"] = new_fixed
                st.success("저장되었습니다!")
