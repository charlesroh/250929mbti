import streamlit as st
import pandas as pd
import altair as alt

# ------------------------
# 1. 앱 제목
# ------------------------
st.title("MBTI 국가별 상위 10개 국가 시각화")

# ------------------------
# 2. CSV 파일 로드
# ------------------------
df = pd.read_csv("countriesMBTI_16types.csv")

# ------------------------
# 3. MBTI 유형 선택
# ------------------------
mbti_types = df.columns[1:]  # 첫 번째 컬럼(Country) 제외
selected_mbti = st.selectbox("MBTI 유형을 선택하세요:", mbti_types)

# ------------------------
# 4. 선택된 MBTI 유형으로 상위 10개 국가 추출
# ------------------------
top10_df = df[['Country', selected_mbti]].sort_values(by=selected_mbti, ascending=False).head(10)

# ------------------------
# 5. Altair 막대 그래프 생성
# ------------------------
chart = (
    alt.Chart(top10_df)
    .mark_bar()
    .encode(
        x=alt.X('Country:N', sort='-y', title='국가'),
        y=alt.Y(f'{selected_mbti}:Q', title=f'{selected_mbti} 비율'),
        color=alt.Color('Country:N', legend=None)  # 색상 국가별 자동 지정
    )
    .properties(
        title=f"{selected_mbti} 유형 상위 10개 국가",
        width=600,
        height=400
    )
)

# ------------------------
# 6. 결과 출력
# ------------------------
st.subheader(f"{selected_mbti} 상위 10개 국가 막대 그래프")
st.altair_chart(chart, use_container_width=True)

# ------------------------
# 7. 데이터 테이블 출력
# ------------------------
st.subheader("상위 10개 데이터 표")
st.dataframe(top10_df.reset_index(drop=True))

