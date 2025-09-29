import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="국가별 최다 MBTI 세계 지도", page_icon="🗺️", layout="wide")
st.title("🗺️ 국가별 ‘가장 높은 비율’ MBTI 세계 지도")
st.caption("CSV의 16개 MBTI 비율 중 각 국가에서 가장 높은 유형을 계산하여 지도에 표시함.")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    assert "Country" in df.columns, "CSV에 'Country' 컬럼이 필요합니다."
    return df

# 데이터 로드
df = load_data("countriesMBTI_16types.csv")

# MBTI 열 목록 (Country 제외)
mbti_cols = [c for c in df.columns if c != "Country"]

# 각 국가별 최다 MBTI 계산
def compute_dominant(row):
    sub = row[mbti_cols]
    top1_mbti = sub.idxmax()
    top1_val = sub.max()
    # 상위 3개 문자열(툴팁용)
    top3 = sub.sort_values(ascending=False).head(3)
    top3_str = " / ".join([f"{k}:{v:.1%}" for k, v in top3.items()])
    return pd.Series({
        "Country": row["Country"],
        "최다_MBTI": top1_mbti,
        "최다_비율": top1_val,
        "상위3": top3_str
    })

map_df = df.apply(compute_dominant, axis=1)

# 색상 매핑(16유형 고유색)
color_map = {
    "INFJ": "#6C8AE4", "ISFJ": "#70C1B3", "INTP": "#F3A712", "ISFP": "#F25F5C",
    "ENTP": "#B08BBB", "INFP": "#84C7D0", "ENTJ": "#E26D5A", "ISTP": "#7BC950",
    "INTJ": "#FFB3C1", "ESFP": "#8EA604", "ESTJ": "#4CB944", "ENFP": "#FFD449",
    "ESTP": "#5DADEC", "ISTJ": "#C48CFF", "ENFJ": "#FF9F1C", "ESFJ": "#9EADC8"
}

# 사이드바 필터(선택): 특정 MBTI만 강조 표시
st.sidebar.header("⚙️ 보기 옵션")
highlight = st.sidebar.multiselect("강조할 MBTI(선택)", options=mbti_cols, default=[])

# 강조 여부 컬럼(선택했을 때만 불투명도 높임)
map_df["강조"] = map_df["최다_MBTI"].isin(highlight).astype(int) if highlight else 1

# Choropleth 생성
fig = px.choropleth(
    map_df,
    locations="Country",
    locationmode="country names",
    color="최다_MBTI",
    color_discrete_map=color_map,
    hover_name="Country",
    hover_data={
        "최다_MBTI": True,
        "최다_비율": ":.1%",
        "상위3": True,
        "Country": False
    },
    title="국가별 최다 MBTI 세계 지도"
)

# 강조: 선택된 유형이면 불투명도 0.95, 아니면 0.6
opacity_series = map_df["강조"].map({1: 0.95, 0: 0.6}) if highlight else pd.Series([0.95]*len(map_df))
fig.data[0].marker.opacity = opacity_series

fig.update_layout(
    margin=dict(l=10, r=10, t=60, b=10),
    legend_title_text="최다 MBTI",
)

st.plotly_chart(fig, use_container_width=True)

# 표도 제공(엑셀 붙여넣기 용)
st.subheader("📋 국가별 최다 MBTI 표")
table_df = map_df[["Country", "최다_MBTI", "최다_비율", "상위3"]].copy()
table_df["최다_비율(%)"] = (table_df["최다_비율"] * 100).round(2)
table_df = table_df.drop(columns=["최다_비율"])
st.dataframe(table_df, use_container_width=True)

st.markdown("""
---
**설명**  
- 각 국가에서 16개 MBTI 중 **가장 높은 비율(최다_MBTI)**을 계산하여 색상으로 표시함.  
- 마우스 오버 시 **최다 비율**과 **상위 3개 유형**이 함께 표시됨.  
- 사이드바에서 특정 MBTI를 선택하면 해당 유형 국가들의 불투명도가 높아져 **강조**됨.
""")

