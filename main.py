import streamlit as st
import pandas as pd

# 앱 제목
st.title("MBTI 국가별 데이터 미리보기")

# CSV 파일 불러오기
df = pd.read_csv("countriesMBTI_16types.csv")

# 데이터 상위 5줄 출력
st.subheader("상위 5줄 데이터")
st.dataframe(df.head())  # 상위 5개 행 표시
