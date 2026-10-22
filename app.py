import streamlit as st
import streamlit.components.v1 as components
import json
import os
import io
import time
import base64
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageOps

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
    [data-testid="InputInstructions"] { display: none; }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; align-items: flex-end; gap: 8px; }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div:last-child { flex: 0 0 32% !important; }
    [data-testid="stFormSubmitButton"] > button { height: 2.6em; font-weight: 600; }
    .stButton > button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

DATA_PATH = "data.json"

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
    "account": "관리자 설정에서 입금 계좌를 입력해주세요",
    "admin_password": "1234"
}


# ───────────── 저장소 (GitHub 비공개 저장소 / 없으면 서버 파일) ─────────────
def _secret(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


TOKEN = _secret("GITHUB_TOKEN")
REPO = _secret("DATA_REPO")
USE_GH = bool(TOKEN and REPO)
API = f"https://api.github.com/repos/{REPO}/contents/"
HEAD = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class Conflict(Exception):
    pass


KST = timezone(timedelta(hours=9))     # Streamlit 서버는 세계 표준시(UTC)라 한국 시간으로 맞춤


def next_month(m):
    """'10월' → '11월', '12월' → '1월' (숫자를 못 찾으면 그대로)"""
    import re
    x = re.search(r"(\d+)", str(m))
    return f"{int(x.group(1)) % 12 + 1}월" if x else m


def gh_get(path):
    r = requests.get(API + path, headers=HEAD, timeout=15)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    j = r.json()
    return base64.b64decode(j["content"]), j["sha"]


def gh_put(path, raw, sha, msg):
    body = {"message": msg, "content": base64.b64encode(raw).decode()}
    if sha:
        body["sha"] = sha
    r = requests.put(API + path, headers=HEAD, json=body, timeout=30)
    if r.status_code in (409, 422):
        raise Conflict()
    r.raise_for_status()


def normalize(data):
    data.setdefault("shops", json.loads(json.dumps(DEFAULT_SHOPS)))
    data.setdefault("config", dict(DEFAULT_CONFIG))
    data.setdefault("posts", [])
    for shop in data["shops"].values():
        shop.setdefault("당월전기", 0.0)
        shop.setdefault("당월수도", 0.0)
    for k, v in DEFAULT_CONFIG.items():
        data["config"].setdefault(k, v)
    return data


def read_raw():
    if USE_GH:
        raw, sha = gh_get(DATA_PATH)
    else:
        raw, sha = None, None
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "rb") as f:
                raw = f.read()
    if raw is None:
        data = {}
    else:
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = {}
    return normalize(data), sha


@st.cache_data(ttl=60, show_spinner=False)
def load_data():
    return read_raw()[0]


def update_data(mutate, msg):
    """저장 직전에 최신 데이터를 다시 읽고, 바꿀 부분만 바꿔서 저장 (동시 저장 대비)"""
    for i in range(4):
        data, sha = read_raw()
        mutate(data)
        raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        try:
            if USE_GH:
                gh_put(DATA_PATH, raw, sha, msg)
            else:
                with open(DATA_PATH, "wb") as f:
                    f.write(raw)
            load_data.clear()
            return data
        except Conflict:
            time.sleep(1 + i)
    raise RuntimeError("다른 분과 동시에 저장되어 실패했습니다. 다시 눌러주세요.")


def shrink_photo(file):
    img = Image.open(file)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70, optimize=True)
    return buf.getvalue()


def save_photo(path, raw):
    if USE_GH:
        gh_put(path, raw, None, f"사진 등록 {path}")
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(raw)


@st.cache_data(show_spinner=False)
def load_photo(path):
    if USE_GH:
        return gh_get(path)[0]
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def delete_photo(path):
    try:
        if USE_GH:
            _, sha = gh_get(path)
            if sha:
                requests.delete(API + path, headers=HEAD,
                                json={"message": f"사진 삭제 {path}", "sha": sha}, timeout=15)
        elif os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ───────────── 요금 계산 (한 곳에서만) ─────────────
def calc_fee(shop_name, use_elec, use_water, n):
    base_elec_share = 750000 / n
    public_elec_fee = 75000
    indiv_elec_fee = (use_elec * 140.0) + public_elec_fee + base_elec_share

    public_water_fee = 13000
    indiv_water_fee = (use_water * 3000.0) + public_water_fee

    is_jump = "점핑" in shop_name
    base_elevator = 70000 / n
    elevator_fee = base_elevator + 50000 if is_jump else base_elevator
    taedong_fee = 370000 / n
    repair_reserve = 10000
    daehan_elec_fee = 231000 / n

    fixed_sum = elevator_fee + taedong_fee + repair_reserve + daehan_elec_fee
    return {
        "base_elec_share": base_elec_share,
        "indiv_elec_fee": indiv_elec_fee,
        "indiv_water_fee": indiv_water_fee,
        "elevator_fee": elevator_fee,
        "taedong_fee": taedong_fee,
        "repair_reserve": repair_reserve,
        "daehan_elec_fee": daehan_elec_fee,
        "is_jump": is_jump,
        "total": indiv_elec_fee + indiv_water_fee + fixed_sum,
    }


# ───────────── 데이터 불러오기 ─────────────
try:
    db = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다. 잠시 후 새로고침해주세요. ({e})")
    st.stop()

if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

page = st.session_state.get("page", "fee")

# 화면이 바뀌면 맨 위로 올리기
if st.session_state.pop("scroll_top", False):
    st.session_state.scroll_n = st.session_state.get("scroll_n", 0) + 1
    components.html(f"""<script>
        // {st.session_state.scroll_n}
        const d = window.parent.document;
        window.parent.scrollTo(0, 0);
        d.querySelectorAll('[data-testid="stAppViewContainer"], [data-testid="stMain"], section.main')
         .forEach(e => e.scrollTo(0, 0));
    </script>""", height=0)


if page == "fee":
    cfg = db["config"]
    shops = db["shops"]
    n = len(shops) or 1          # 점포 수 = 점포 목록 개수 (자동)

    shop_list = list(shops.keys())

    if st.session_state.get("selected_shop") not in shop_list:
        st.session_state.selected_shop = None

    if st.session_state.selected_shop is None:
        # ── 첫 화면: 점포 목록 ──
        st.subheader(f"{cfg['month']} 관리비 조회")
        st.markdown("##### 🏪 본인의 점포를 **클릭하여** 선택해주세요")
        for idx, shop_name in enumerate(shop_list):
            if st.button(shop_name, key=f"btn_shop_{idx}", use_container_width=True):
                st.session_state.selected_shop = shop_name
                st.session_state.step = 1
                st.session_state.elec_val = float(shops[shop_name]["당월전기"]) or None
                st.session_state.water_val = float(shops[shop_name]["당월수도"]) or None
                st.session_state.scroll_top = True
                st.rerun()
    else:
        # ── 점포 화면: 1 전기 → 2 수도 → 3 결과 ──
        selected_shop = st.session_state.selected_shop
        shop_info = shops[selected_shop]
        step = st.session_state.get("step", 1)

        def go(step_no):
            st.session_state.step = step_no
            st.session_state.scroll_top = True

        prev_e = shop_info["전월전기"]
        prev_w = shop_info["전월수도"]

        if step == 1:
            st.markdown("### ⚡ 전기 계량기")
            st.info(f"전월 기준 전기 수치: **{prev_e:,.1f} kWh**")
            with st.form(f"elec_form_{selected_shop}"):
                c_in, c_btn = st.columns([3, 1])
                with c_in:
                    v = st.number_input("당월 전기 계량기 수치 입력", value=st.session_state.get("elec_val"),
                                        step=1.0, format="%.1f")
                with c_btn:
                    ok = st.form_submit_button("↵ 다음", use_container_width=True)
            if ok:
                if v is None:
                    st.error("전기 계량기 수치를 입력해주세요.")
                elif v < prev_e:
                    st.error("⚠️ 당월 전기 수치가 전월 기준 수치보다 작습니다. 수치를 확인해주세요.")
                else:
                    st.session_state.elec_val = v
                    go(2)
                    st.rerun()

        elif step == 2:
            st.success(f"⚡ 전기: {st.session_state.elec_val:,.1f} kWh (사용량 {st.session_state.elec_val - prev_e:,.1f} kWh)")
            st.markdown("### 💧 수도 계량기")
            st.info(f"전월 기준 수도 수치: **{prev_w:,.1f} ton**")
            with st.form(f"water_form_{selected_shop}"):
                c_in, c_btn = st.columns([3, 1])
                with c_in:
                    v = st.number_input("당월 수도 계량기 수치 입력", value=st.session_state.get("water_val"),
                                        step=1.0, format="%.1f")
                with c_btn:
                    ok = st.form_submit_button("↵ 결과 보기", use_container_width=True)
            if ok:
                if v is None:
                    st.error("수도 계량기 수치를 입력해주세요.")
                elif v < prev_w:
                    st.error("⚠️ 당월 수도 수치가 전월 기준 수치보다 작습니다. 수치를 확인해주세요.")
                else:
                    e_val = st.session_state.elec_val

                    def _set_meter(d, s=selected_shop, e=e_val, w=v):
                        if s in d["shops"]:
                            d["shops"][s]["당월전기"] = e
                            d["shops"][s]["당월수도"] = w
                    try:
                        with st.spinner("저장 중..."):
                            update_data(_set_meter, f"{selected_shop} 계량기 입력")
                    except Exception as e:
                        st.error(f"저장하지 못했습니다. 다시 눌러주세요. ({e})")
                    else:
                        st.session_state.water_val = v
                        go(3)
                        st.rerun()

        else:
            curr_elec = st.session_state.elec_val
            curr_water = st.session_state.water_val
            use_elec = round(curr_elec - prev_e, 1)
            use_water = round(curr_water - prev_w, 1)
            f = calc_fee(selected_shop, use_elec, use_water, n)

            st.markdown(f"""
            <div style="padding:18px 20px; background:#fff7ed; border:2px solid #fb923c; border-radius:12px; margin-bottom:16px; text-align:center;">
                <div style="color:#9a3412; font-size:1em; font-weight:600;">{selected_shop} · {cfg['month']} 관리비</div>
                <div style="color:#dc2626; font-size:2.6em; font-weight:800; line-height:1.3;">{f['total']:,.0f}원</div>
            </div>
            """, unsafe_allow_html=True)
            st.success(f"📊 당월 사용량 - 전기: {use_elec:,.1f} kWh / 수도: {use_water:,.1f} ton")
            st.info(f"입금계좌: {cfg['account']}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 전기 및 수도 요금")
                st.write(f"- **전기세**: {f['indiv_elec_fee']:,.0f}원")
                st.caption(f"  (사용량 {use_elec:,.1f}kWh × 140원 + 공용전기 75,000원 + 기본전기 {f['base_elec_share']:,.0f}원)")
                st.write(f"- **수도세**: {f['indiv_water_fee']:,.0f}원")
                st.caption(f"  (사용량 {use_water:,.1f}톤 × 3,000원 + 공용수도 13,000원)")
            with c2:
                st.markdown("### 기타 공용 관리비 분담 항목")
                jump_text = " (점핑 +50,000원 포함)" if f["is_jump"] else ""
                st.write(f"- 엘리베이터 요금: {f['elevator_fee']:,.0f}원{jump_text}")
                st.write(f"- 태동환경: {f['taedong_fee']:,.0f}원")
                st.write(f"- 수선예비비: {f['repair_reserve']:,.0f}원")
                st.write(f"- 대한전기: {f['daehan_elec_fee']:,.0f}원")

        # ── 아래쪽: 점포 이름 + 돌아가기 ──
        st.markdown("---")
        st.markdown(f"<div style='padding:8px 12px; background:#eff6ff; border-left:4px solid #3b82f6; "
                    f"border-radius:4px; color:#1e40af; font-weight:600;'>🔍 {selected_shop}</div>",
                    unsafe_allow_html=True)
        st.markdown("")
        if step == 2:
            if st.button("← 전기 다시 입력", key="back_elec"):
                go(1)
                st.rerun()
        else:
            if st.button("← 점포 목록으로", key="back_to_list"):
                st.session_state.selected_shop = None
                go(1)
                st.rerun()

if page == "photo":
    st.subheader(f"📷 {db['config']['month']} 계량기 증빙 사진 게시판")
    st.caption("점주님들께서 입력하신 계량기 수치의 증빙 사진을 업로드하고 다른 점주님들과 공유하는 공간입니다.")

    with st.form("upload_form", clear_on_submit=True):
        st.markdown("#### 📝 새 증빙 사진 등록")
        shop_names = list(db["shops"].keys())
        post_shop = st.selectbox("점포 선택", shop_names, key="post_shop_select")
        uploaded_images = st.file_uploader("계량기 사진 업로드 (PNG, JPG, JPEG · 최대 4장)", type=["png", "jpg", "jpeg"],
                                           accept_multiple_files=True, key="post_img_file")
        post_desc = st.text_area("설명 또는 메모 (선택사항)", key="post_desc_input")

        submit_post = st.form_submit_button("사진 등록하기")
        if submit_post:
            if not uploaded_images:
                st.error("업로드할 계량기 사진을 첨부해주세요.")
            elif len(uploaded_images) > 4:
                st.error("사진은 한 번에 4장까지 올릴 수 있습니다.")
            else:
                now = datetime.now(KST)
                post_id = now.strftime("%Y%m%d%H%M%S%f")
                shop_no = shop_names.index(post_shop) + 1
                photo_paths = [f"photos/{now.strftime('%Y-%m')}/{post_id}_{shop_no}_{i + 1}.jpg"
                               for i in range(len(uploaded_images))]
                new_post = {
                    "id": post_id,
                    "date": now.strftime("%Y-%m-%d %H:%M"),
                    "shop": post_shop,
                    "title": f"{db['config']['month']} 계량기 인증",
                    "image_names": [u.name for u in uploaded_images],
                    "image_paths": photo_paths,
                    "desc": post_desc,
                }
                try:
                    with st.spinner("사진 올리는 중..."):
                        for pth, up in zip(photo_paths, uploaded_images):
                            save_photo(pth, shrink_photo(up))
                        update_data(lambda d, p=new_post: d["posts"].insert(0, p), f"{post_shop} 사진 게시")
                except Exception as e:
                    st.error(f"사진을 등록하지 못했습니다. 다시 시도해주세요. ({e})")
                else:
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

                paths = post.get("image_paths") or ([post["image_path"]] if post.get("image_path") else [])
                if paths:
                    img_cols = st.columns(min(len(paths), 2))
                    for i, pth in enumerate(paths):
                        with img_cols[i % len(img_cols)]:
                            try:
                                img_bytes = load_photo(pth)
                                if img_bytes:
                                    st.image(img_bytes, use_container_width=True)
                                else:
                                    st.warning("사진 파일을 찾을 수 없습니다.")
                            except Exception:
                                st.warning("이미지를 불러오는 중 오류가 발생했습니다.")
                elif post.get("image_bytes"):
                    try:
                        st.image(bytes.fromhex(post["image_bytes"]), width=350)
                    except Exception:
                        st.warning("이미지를 불러오는 중 오류가 발생했습니다.")

                if post.get("desc"):
                    st.info(f"메모: {post['desc']}")

                if st.session_state.get("admin_auth", False):
                    if st.button("🗑️ 이 게시물 삭제 (관리자용)", key=f"del_post_{post['id']}_{idx}"):
                        pid = post["id"]
                        try:
                            update_data(lambda d, pid=pid: d.__setitem__(
                                "posts", [p for p in d["posts"] if p.get("id") != pid]), "게시물 삭제")
                            for pth in post.get("image_paths") or ([post["image_path"]] if post.get("image_path") else []):
                                delete_photo(pth)
                        except Exception as e:
                            st.error(f"삭제하지 못했습니다. ({e})")
                        else:
                            st.success("게시물이 삭제되었습니다.")
                            st.rerun()

                st.markdown("---")

if page == "admin":
    st.subheader("관리자 설정")
    cfg = db["config"]
    shops = db["shops"]
    n = len(shops) or 1          # 점포 수 = 점포 목록 개수 (자동)

    if not st.session_state.admin_auth:
        st.markdown("🔒 **관리자 모드 접근을 위해 비밀번호를 입력해주세요.**")
        input_pw = st.text_input("비밀번호", type="password", key="admin_pw_input")
        if st.button("로그인", key="admin_login_btn"):
            if input_pw == cfg.get("admin_password", "1234"):
                st.session_state.admin_auth = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    else:
        if USE_GH:
            st.success("✅ 데이터와 사진이 GitHub 비공개 저장소에 저장되고 있습니다.")
        else:
            st.warning("⚠️ GitHub 저장소가 연결되지 않아 서버에 임시 저장 중입니다. Secrets 설정을 확인해주세요.")

        if st.button("🚪 관리자 로그아웃", key="admin_logout_btn"):
            st.session_state.admin_auth = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 1. 기본 설정 (정산 월, 계좌 및 비밀번호)")
        m = st.text_input("정산 월", value=cfg["month"], key="cfg_month_input")
        st.caption(f"점포 수: {n}개 (점포 목록에서 자동으로 계산해요)")
        acc = st.text_input("입금 계좌 안내", value=cfg["account"], key="cfg_acc_input")
        new_pw = st.text_input("새 관리자 비밀번호 변경 (변경시에만 입력)", type="password", key="cfg_new_pw")

        if st.button("기본 설정 저장하기", key="save_cfg_btn"):
            def _set_cfg(d, m=m, acc=acc, new_pw=new_pw):
                d["config"]["month"] = m
                d["config"]["n_shops"] = len(d["shops"])
                d["config"]["account"] = acc
                if new_pw.strip() != "":
                    d["config"]["admin_password"] = new_pw
            try:
                update_data(_set_cfg, "기본 설정 변경")
            except Exception as e:
                st.error(f"저장하지 못했습니다. ({e})")
            else:
                st.success("기본 설정 및 비밀번호가 저장되었습니다!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 2. 📊 이번 달 전체 점포 현황 및 기준 수치 수정")
        st.caption("각 점포의 **'전월 전기'와 '전월 수도' 수치를 직접 수정**하실 수 있으며, 당월 입력 현황과 총 관리비를 한눈에 확인할 수 있습니다.")

        new_prev = {}
        summary_data = []

        for shop_name, vals in shops.items():
            st.markdown(f"**📌 {shop_name}**")
            col_e, col_w, col_info = st.columns([1, 1, 2])

            with col_e:
                pe = st.number_input("전월 전기 (kWh)", value=float(vals["전월전기"]), step=1.0, format="%.1f", key=f"adm_pe_{shop_name}")
            with col_w:
                pw = st.number_input("전월 수도 (ton)", value=float(vals["전월수도"]), step=1.0, format="%.1f", key=f"adm_pw_{shop_name}")

            new_prev[shop_name] = (pe, pw)

            c_e = vals.get("당월전기", 0.0)
            c_w = vals.get("당월수도", 0.0)

            u_e = round(c_e - pe, 1) if c_e > 0 else 0.0
            u_w = round(c_w - pw, 1) if c_w > 0 else 0.0

            if c_e > 0 and u_e >= 0 and c_w > 0 and u_w >= 0:
                fee_str = f"{calc_fee(shop_name, u_e, u_w, n)['total']:,.0f} 원"
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
            def _set_prev(d, new_prev=new_prev):
                for s, (pe, pw) in new_prev.items():
                    if s in d["shops"]:
                        d["shops"][s]["전월전기"] = pe
                        d["shops"][s]["전월수도"] = pw
            try:
                update_data(_set_prev, "전월 기준 수치 수정")
            except Exception as e:
                st.error(f"저장하지 못했습니다. ({e})")
            else:
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

        # ── 정산 마감: 모든 점포가 입력해야 켜짐 ──
        st.markdown("---")
        st.markdown(f"### ✅ {cfg['month']} 정산 마감")
        missing = [r["점포명"] for r in summary_data if r["총 관리비"] == "미입력 또는 계산 전"]
        nxt = next_month(cfg["month"])
        msg = st.session_state.pop("close_msg", None)
        if msg:
            (st.success if msg[0] == "ok" else st.error)(msg[1])
        if missing:
            st.warning(f"아직 입력하지 않은 점포가 {len(missing)}곳 있어요: " + ", ".join(missing))
        else:
            st.caption(f"마감하면 CSV 파일이 저장되고, {cfg['month']} 기록을 보관한 뒤 당월 수치를 전월로 옮기고 {nxt}을 시작해요.")
        agree = st.checkbox(f"{cfg['month']} 정산을 마감합니다 (되돌릴 수 없어요)", key="close_ok", disabled=bool(missing))

        def _close_month(month=cfg["month"], nxt=nxt):
            def _close(d):
                if d["config"].get("month") != month:
                    raise RuntimeError("이미 마감된 달이에요. 새로고침해 주세요.")
                n_now = len(d["shops"]) or 1
                rows = {}
                for s_name, v in d["shops"].items():
                    ue = round(v["당월전기"] - v["전월전기"], 1)
                    uw = round(v["당월수도"] - v["전월수도"], 1)
                    if v["당월전기"] <= 0 or v["당월수도"] <= 0 or ue < 0 or uw < 0:
                        raise RuntimeError(f"{s_name} 입력이 비어 있거나 전월보다 작아요.")
                    rows[s_name] = {"전월전기": v["전월전기"], "당월전기": v["당월전기"], "전기사용량": ue,
                                    "전월수도": v["전월수도"], "당월수도": v["당월수도"], "수도사용량": uw,
                                    "관리비": round(calc_fee(s_name, ue, uw, n_now)["total"])}
                d.setdefault("history", {})[month] = {"closed": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
                                                      "shops": rows}
                for v in d["shops"].values():
                    v["전월전기"], v["전월수도"] = v["당월전기"], v["당월수도"]
                    v["당월전기"], v["당월수도"] = 0.0, 0.0
                d["config"]["month"] = nxt
            try:
                update_data(_close, f"{month} 정산 마감")
            except Exception as e:
                st.session_state.close_msg = ("err", f"마감하지 못했습니다. ({e})")
            else:
                for k in list(st.session_state.keys()):
                    if k.startswith(("adm_pe_", "adm_pw_")) or k in ("cfg_month_input", "close_ok", "elec_val", "water_val"):
                        del st.session_state[k]
                st.session_state.close_msg = ("ok", f"{month} 정산을 마감했어요. 이제 {nxt} 입력을 받을 수 있어요.")

        st.download_button(
            label=f"✅ {cfg['month']} 정산 마감하고 {nxt} 시작 (CSV 저장)",
            data=csv_data,
            file_name=f"테크노푸드몰_{cfg['month']}_관리자정산.csv",
            mime="text/csv",
            key="close_month_btn",
            on_click=_close_month,
            disabled=bool(missing) or not agree,
            use_container_width=True,
        )

        st.markdown("---")
        if st.button("🔄 모든 점포 당월 입력 상태 초기화하기 (미입력으로 되돌리기)", key="reset_inputs_btn"):
            def _reset(d):
                for s in d["shops"]:
                    d["shops"][s]["당월전기"] = 0.0
                    d["shops"][s]["당월수도"] = 0.0
            try:
                update_data(_reset, "당월 입력 초기화")
            except Exception as e:
                st.error(f"초기화하지 못했습니다. ({e})")
            else:
                for k in list(st.session_state.keys()):
                    if k.startswith(("c_elec_", "c_water_")) or k in ("elec_val", "water_val"):
                        del st.session_state[k]
                st.success("모든 점포의 당월 입력값이 초기화되었습니다!")
                st.rerun()


# ───────────── 아래쪽 메뉴 ─────────────
st.markdown("---")
MENU = [("fee", "관리비 조회"), ("photo", "📷 사진 게시판"), ("admin", "관리자 설정")]
for col, (k, label) in zip(st.columns(len(MENU)), MENU):
    with col:
        if st.button(f"👉 {label}" if page == k else label, key=f"menu_{k}", use_container_width=True):
            st.session_state.page = k
            st.session_state.scroll_top = True
            st.rerun()
st.markdown("<div style='text-align:center; color:#9ca3af; font-size:0.9em; margin-top:6px;'>테크노푸드몰</div>",
            unsafe_allow_html=True)
