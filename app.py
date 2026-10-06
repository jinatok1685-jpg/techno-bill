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
    st.caption("점주님들께서 입력하신 계량기 수치의 증빙 사진을 업로드하고 다른 점주님들과 공유하는 공간입니다.")
    
    with st.form("upload_form", clear_on_submit=True):
        st.markdown("#### 📝 새 증빙 사진 등록")
        post_shop = st.selectbox("점포 선택", list(db["shops"].keys()), key="post_shop_select")
        post_title = st.text_input("제목 (예: 10월 전기/수도 계량기 인증)", key="post_title_input")
        uploaded_image = st.file_uploader("계량기 사진 업로드 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="post_img_file")
        post_desc = st.text_area("설명 또는 메모 (선택사항)", key="post_desc_input")
        
        submit_post = st.form_submit_button("사진 등록하기")
        if submit_post:
            if not post_title.strip():
                st.error("제목을 입력해주세요.")
            elif not uploaded_image:
                st.error("업로드할 계량기 사진을 첨부해주세요.")
            else:
                if "posts" not in db:
                    db["posts"] = []
                
                new_post = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "shop": post_shop,
                    "title": post_title,
                    "image_name": uploaded_image.name,
                    "image_bytes": uploaded_image.getvalue().hex(), # 바이트를 hex 문자열로 저장하여 JSON 직렬화 가능하게 함
                    "desc": post_desc
                }
                db["posts"].insert(0, new_post) # 최신글이 위로 오도록
                save_data(db)
                st.success("계량기 증빙 사진이 성공적으로 등록되었습니다!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 📋 등록된 증빙 사진 목록")
    
    posts = db.get("posts", [])
    if not posts:
        st.info("등록된 계량기 증빙 사진이 없습니다. 첫 번째 인증 사진을 등록해보세요!")
    else:
        for idx, post in enumerate(posts):
            with st.container():
                st.markdown(f"#### 📌 [{post['shop']}] {post['title']}")
                st.caption(f"작성일시: {post['date']} | 점포: {post['shop']}")
                
                try:
                    img_bytes = bytes.fromhex(post["image_bytes"])
                    st.image(img_bytes, caption=post['image_name'], use_container_width=True)
                except Exception:
                    st.warning("이미지를 불러오는 중 오류가 발생했습니다.")
                
                if post.get("desc"):
                    st.info(f"메모: {post['desc']}")
                
                if st.session_state.get("admin_auth", False):
                    if st.button(f"🗑️ 이 게시물 삭제 (관리자용)", key=f"del_post_{post['id']}_{idx}"):
                        db["posts"].remove(post)
                        save_data(db)
                        st.success("게시물이 삭제되었습니다.")
                        st.rerun()
                
                st.markdown("---")

with tab3:
    st.subheader("관리자 설정")
    cfg = db["config"]
    shops = db["shops"]
    n = cfg["n_shops"] if cfg["n_shops"] > 0 else 1

    if not st.session_state.admin_auth:
        st.markdown("🔒 **관리자 모드 접근을 위해 비밀번호를 입력해주세요.**")
        input_pw = st.text_input("비밀번호", type="password", key="admin_pw_input")
        if st.button("로그인", key="admin_login_btn"):
            correct_pw = cfg.get("admin_password", "1234")
            if input_pw == correct_pw:
                st.session_state.admin_auth = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    else:
        if st.button("🚪 관리자 로그아웃", key="admin_logout_btn"):
            st.session_state.admin_auth = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 1. 기본 설정 (정산 월, 계좌 및 비밀번호)")
        m = st.text_input("정산 월", value=cfg["month"], key="cfg_month_input")
        n_s = st.number_input("점포 수 (n)", value=int(cfg["n_shops"]), min_value=1, key="cfg_n_input")
        acc = st.text_input("입금 계좌 안내", value=cfg["account"], key="cfg_acc_input")
        new_pw = st.text_input("새 관리자 비밀번호 변경 (변경시에만 입력)", type="password", key="cfg_new_pw")
            
        if st.button("기본 설정 저장하기", key="save_cfg_btn"):
            updated_pw = new_pw if new_pw.strip() != "" else cfg.get("admin_password", "1234")
            db["config"] = {
                "month": m,
                "n_shops": int(n_s),
                "account": acc,
                "admin_password": updated_pw
            }
            save_data(db)
            st.success("기본 설정 및 비밀번호가 저장되었습니다!")
            st.rerun()

        st.markdown("---")
        st.markdown("### 2. 📊 이번 달 전체 점포 현황 및 기준 수치 수정")
        st.caption("각 점포의 **'전월 전기'와 '전월 수도' 수치를 직접 수정**하실 수 있으며, 당월 입력 현황과 총 관리비를 한눈에 확인할 수 있습니다.")
        
        updated_shops = {}
        summary_data = []
        
        for shop_name, vals in shops.items():
            st.markdown(f"**📌 {shop_name}**")
            col_e, col_w, col_info = st.columns([1, 1, 2])
            
            with col_e:
                pe = st.number_input("전월 전기 (kWh)", value=float(vals["전월전기"]), step=1.0, format="%.1f", key=f"adm_pe_{shop_name}")
            with col_w:
                pw = st.number_input("전월 수도 (ton)", value=float(vals["전월수도"]), step=1.0, format="%.1f", key=f"adm_pw_{shop_name}")
                
            updated_shops[shop_name] = {
                "전월전기": pe, 
                "전월수도": pw,
                "당월전기": vals.get("당월전기", 0.0),
                "당월수도": vals.get("당월수도", 0.0)
            }
            
            c_e = vals.get("당월전기", 0.0)
            c_w = vals.get("당월수도", 0.0)
            
            u_e = round(c_e - pe, 1) if c_e > 0 else 0.0
            u_w = round(c_w - pw, 1) if c_w > 0 else 0.0
            
            if c_e > 0 and u_e >= 0 and c_w > 0 and u_w >= 0:
                base_elec_share = 750000 / n
                public_elec_fee = 75000
                indiv_elec_fee = (u_e * 140.0) + public_elec_fee + base_elec_share
                
                public_water_fee = 13000
                indiv_water_fee = (u_w * 3000.0) + public_water_fee
                
                base_elevator = 70000 / n
                elevator_fee = base_elevator + 50000 if "점핑" in shop_name else base_elevator
                taedong_fee = 370000 / n
                repair_reserve = 10000
                daehan_elec_fee = 231000 / n
                
                fixed_sum = elevator_fee + taedong_fee + repair_reserve + daehan_elec_fee
                total_fee = indiv_elec_fee + indiv_water_fee + fixed_sum
                fee_str = f"{total_fee:,.0f} 원"
            else:
                fee_str = "미입력 또는 계산 전"
                
            summary_data.append({
                "점포명": shop_name,
                "당월 전기": f"{c_e:,.1f}" if c_e > 0 else "-",
                "전기 사용량": f"{u_e:,.1f}" if c_e > 0 and u_e >= 0 else "-",
                "당월 수도": f"{c_w:,.1f}" if c_w > 0 else "-",
                "수도 사용량": f"{u_w:,.1f}" if c_w > 0 and u_w >= 0 else "-",
                "총 관리비": fee_str
            })
            st.markdown("")

        if st.button("수정된 기준 수치 및 전체 현황 저장", key="save_shops_btn"):
            db["shops"] = updated_shops
            save_data(db)
            st.success("점포 기준 수치가 성공적으로 업데이트되었습니다!")
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 당월 입력 및 요금 요약 표")
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        csv_data = df_summary.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=f"💾 {cfg['month']} 종합 정산 결과 파일(CSV) 저장하기",
            data=csv_data,
            file_name=f"테크노푸드몰_{cfg['month']}_관리자정산.csv",
            mime="text/csv",
            key="download_summary_csv"
        )

        st.markdown("")
        if st.button("🔄 모든 점포 당월 입력 상태 초기화하기 (미입력으로 되돌리기)", key="reset_inputs_btn"):
            for shop_name in shops.keys():
                db["shops"][shop_name]["당월전기"] = 0.0
                db["shops"][shop_name]["당월수도"] = 0.0
            save_data(db)
            st.success("모든 점포의 당월 입력값이 초기화되었습니다!")
            st.rerun()
