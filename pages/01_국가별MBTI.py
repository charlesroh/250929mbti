
import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================
# 페이지 기본 설정
# =========================================
st.set_page_config(page_title="MBTI 국가별 비율 대시보드", page_icon="🌏", layout="wide")

st.title("🌏 MBTI 국가별 비율 대시보드")
st.caption("나라를 선택하면 해당 국가의 MBTI 16유형 비율을 예쁜 막대그래프로 보여줌 😊")

# =========================================
# 데이터 로드
# =========================================
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 기본 유효성 체크
    assert "Country" in df.columns, "CSV에 'Country' 컬럼이 필요합니다."
    return df

df = load_data("countriesMBTI_16types.csv")

# MBTI 컬럼 목록 (첫 열 Country 제외)
mbti_cols = [c for c in df.columns if c != "Country"]

# =========================================
# 사이드바 컨트롤
# =========================================
st.sidebar.header("⚙️ 설정")
country = st.sidebar.selectbox("국가 선택", options=sorted(df["Country"].unique()))
sort_desc = st.sidebar.checkbox("값 기준 내림차순 정렬", value=True)
show_emoji_label = st.sidebar.checkbox("MBTI 라벨에 이모지 추가", value=True)
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Tip: CSV 파일만 같은 폴더에 두면 바로 작동함!")

# 간단한 이모지 매핑(센스 있게 가볍게🙂)
emoji_map = {
    "I":"🧠", "E":"🎤", "N":"💡", "S":"🔎", "T":"⚙️", "F":"💞", "J":"📅", "P":"🎯"
}
def mbti_with_emoji(x: str) -> str:
    if not show_emoji_label:
        return x
    return "".join(emoji_map.get(ch, "") for ch in x) + f"  {x}"

# =========================================
# 선택 국가의 데이터 준비
# =========================================
row = df.loc[df["Country"] == country, mbti_cols].iloc[0]
plot_df = (
    pd.DataFrame({"MBTI": mbti_cols, "ratio": row.values})
    .assign(label=lambda d: d["MBTI"].apply(mbti_with_emoji))
)

if sort_desc:
    plot_df = plot_df.sort_values("ratio", ascending=False)
else:
    plot_df = plot_df.sort_values("MBTI")

# =========================================
# 컬러 팔레트 (부드럽고 산뜻한 조합)
# =========================================
color_seq = [
    "#6C8AE4", "#70C1B3", "#F3A712", "#F25F5C",
    "#B08BBB", "#84C7D0", "#E26D5A", "#7BC950",
    "#FFB3C1", "#8EA604", "#4CB944", "#FFD449",
    "#5DADEC", "#C48CFF", "#FF9F1C", "#9EADC8"
]

# =========================================
# 그래프
# =========================================
title_txt = f"🇺🇳 {country} — MBTI 비율"
fig = px.bar(
    plot_df,
    x="label",
    y="ratio",
    title=title_txt,
    color="label",
    color_discrete_sequence=color_seq,
    text="ratio",
)

fig.update_traces(
    hovertemplate="<b>%{x}</b><br>비율: %{y:.2%}",
    texttemplate="%{text:.1%}",
    textposition="outside"
)

fig.update_layout(
    xaxis_title="MBTI 유형",
    yaxis_title="비율",
    uniformtext_minsize=10,
    uniformtext_mode="show",
    showlegend=False,
    margin=dict(l=20, r=20, t=60, b=20),
)

fig.update_yaxes(tickformat=".0%", rangemode="tozero")

# =========================================
# 출력
# =========================================
st.subheader(f"📊 {country}의 MBTI 16유형 비율")
st.plotly_chart(fig, use_container_width=True)

# 표도 함께 제공 (엑셀 붙여넣기 용)
st.subheader("📋 데이터 표 (복사 붙여넣기 용)")
view_df = plot_df[["MBTI", "ratio"]].copy()
view_df["ratio(%)"] = (view_df["ratio"] * 100).round(2)
view_df = view_df.drop(columns=["ratio"]).rename(columns={"MBTI": "MBTI 유형"})
st.dataframe(view_df, use_container_width=True)

st.markdown(
    """
    ---  
    📝 **설명**  
    - 사이드바에서 국가 선택 및 정렬/이모지 라벨 옵션을 조절할 수 있음.  
    - y축은 0~1 값을 **%**로 표시함.  
    - 막대 위 텍스트는 소수점 한 자리까지 퍼센트로 표기함.  
    """
)
