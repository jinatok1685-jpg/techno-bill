import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 기본 설정
st.set_page_config(page_title="관리비 입력 및 요약", layout="wide")

st.header("📋 당월 입력 및 요금 요약 표")

# 1. 샘플 데이터 (화면에 표시 중인 데이터 예시)
data = [
    {"점포명": "지하105-3호 바른푸드(쌀국수)", "당월 전기": 123555.0, "전기 사용량": 311.6, "당월 수도": 1600.0, "수도 사용량": 51.0, "총 관리비": "531,457 원"},
    {"점포명": "A동 102호 두찜", "당월 전기": "-", "전기 사용량": "-", "당월 수도": "-", "수도 사용량": "-", "총 관리비": "미입력 또는 계산 전"},
    {"점포명": "A동 104호 멍앤멍", "당월 전기": "-", "전기 사용량": "-", "당월 수도": "-", "수도 사용량": "-", "총 관리비": "미입력 또는 계산 전"},
    {"점포명": "A동 303호 점핑", "당월 전기": "-", "전기 사용량": "-", "당월 수도": "-", "수도 사용량": "-", "총 관리비": "미입력 또는 계산 전"},
    {"점포명": "B동 107호 덮밥90도", "당월 전기": "-", "전기 사용량": "-", "당월 수도": "-", "수도 사용량": "-", "총 관리비": "미입력 또는 계산 전"},
    {"점포명": "B동 108호 부릉", "당월 전기": "-", "전기 사용량": "-", "당월 수도": "-", "수도 사용량": "-", "총 관리비": "미입력 또는 계산 전"},
]

df = pd.DataFrame(data)

# 2. 요약 표 출력
st.dataframe(df, use_container_width=True)

st.write("---")

# 3. 당월 현황 저장 및 관리 영역
col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    # 저장할 연월 선택
    current_month = datetime.now().strftime("%Y-%m")
    target_month = st.text_input("저장할 기준 연월", value=current_month)

with col2:
    st.write(" ") # 여백 맞춤
    st.write(" ")
    # 당월 현황 저장 버튼
    if st.button("💾 당월 현황 데이터 저장하기", type="primary"):
        # 저장할 데이터에 기준 연월 및 저장 시각 추가
        save_df = df.copy()
        save_df.insert(0, "기준연월", target_month)
        save_df["저장시각"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        file_name = "monthly_summary_history.csv"
        
        # 기존 파일이 있으면 누적(append), 없으면 신규 생성
        if os.path.exists(file_name):
            save_df.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            save_df.to_csv(file_name, mode='w', header=True, index=False, encoding='utf-8-sig')
            
        st.success("{} 현황 데이터가 성공적으로 저장되었습니다!".format(target_month))

with col3:
    st.write(" ")
    st.write(" ")
    # CSV 파일 다운로드 버튼
    file_name = "monthly_summary_history.csv"
    if os.path.exists(file_name):
        history_df = pd.read_csv(file_name)
        csv_data = history_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 누적 저장 기록 다운로드(CSV)",
            data=csv_data,
            file_name="관리비_월별_누적현황_{}.csv".format(target_month),
            mime="text/csv"
        )

st.write(" ")

# 4. 초기화 버튼 영역
if st.button("🔄 모든 점포 당월 입력 상태 초기화하기 (미입력으로 되돌리기)"):
    st.warning("초기화 기능이 실행되었습니다.")
