import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="테크노푸드몰 관리비 고지서", layout="wide")

DATA_FILE = "data.json"
HISTORY_FILE = "history.json"

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
    "account": "카카오뱅크 7942-07-89864 (예금주: 하기수)"
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
                return data
        except Exception:
            pass
    return {"shops": DEFAULT_SHOPS, "config": DEFAULT_CONFIG}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r
