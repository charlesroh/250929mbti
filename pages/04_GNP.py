import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
from scipy import stats

# ============================
# 페이지 설정
# ============================
st.set_page_config(page_title="국가별 GNP × MBTI 상관분석", page_icon="📈", layout="wide")
st.title("📈 국가별 GNP와 MBTI 비율 상관관계 대시보드")
st.caption("• MBTI 16유형 비율과 국가별 GNP 간의 상관관계를 피어슨/스피어만으로 분석하고, 히트맵/산점도로 시각화함")

# ============================
# 헬퍼 함수
# ============================
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def normalize_country_name(s: pd.Series) -> pd.Series:
    """
    국가명 정규화(라이트 버전).
    - 좌우 공백 제거, 중복 공백 정리
    - 일부 자주 충돌하는 이름 매핑(필요시 추가)
    """
    base = s.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    repl = {
        "United States": "United States of America",
        "Russia": "Russian Federation",
        "South Korea": "Korea, Republic of",
        "North Korea": "Korea, Democratic People's Republic of",
        "Vietnam": "Viet Nam",
        "Czech Republic": "Czechia",
        "Ivory Coast": "Côte d'Ivoire",
        "Tanzania": "United Republic of Tanzania",
        "Syria": "Syrian Arab Republic",
        "Macau": "Macao",
        "Hong Kong": "Hong Kong SAR, China",
        "Iran": "Iran, Islamic Republic of",
        "Moldova": "Moldova, Republic of",
        "Laos": "Lao People's Democratic Republic",
        "Bolivia": "Bolivia (Plurinational State of)",
        "Venezuela": "Venezuela (Bolivarian Republic of)",
        "Brunei": "Brunei Darussalam",
        "Cape Verde": "Cabo Verde",
        "Congo (Kinshasa)": "Congo, the Democratic Republic of the",
        "Congo (Brazzaville)": "Congo",
        "Micronesia": "Micronesia, Federated States of",
        "The Bahamas": "Bahamas",
        "Gambia": "Gambia, The",
        "Eswatini": "Swaziland",
        "Burma": "Myanmar",
        "Kyrgyzstan": "Kyrgyz Republic",
    }
    base = base.replace(repl)
    return base

def compute_correlations(df_join: pd.DataFrame, mbti_cols: list, y_col: str):
    """
    각 MBTI 열과 y_col(GNP 등) 간의 피어슨/스피어만 r 및 p-value 계산
    """
    rows = []
    for c in mbti_cols:
        # 결측 제거
        sub = df_join[[c, y_col]].dropna()
        if len(sub) < 3:
            rows.append({
                "MBTI": c,
                "pearson_r": np.nan, "pearson_p": np.nan,
                "spearman_r": np.nan, "spearman_p": np.nan,
                "n": len(sub)
            })
            continue
        pr, pp = stats.pearsonr(sub[c], sub[y_col])
        sr, sp = stats.spearmanr(sub[c], sub[y_col])
        rows.append({
            "MBTI": c,
            "pearson_r": pr, "pearson_p": pp,
            "spearman_r": sr, "spearman_p": sp,
            "n": len(sub)
        })
    return pd.DataFrame(rows)

# ============================
# 데이터 입력(파일 또는 업로드)
# ============================
left, right = st.columns(2)
with left:
    st.subheader("📄 MBTI 데이터")
    mbti_file = st.file_uploader("MBTI CSV 업로드 (미업로드 시 기본 파일 사용)", type=["csv"], key="mbti")
    if mbti_file is not None:
        df_mbti = pd.read_csv(mbti_file)
    else:
        # 기본 파일명 시도
        try:
            df_mbti = load_csv("countriesMBTI_16types.csv")
        except Exception as e:
            st.error("MBTI 파일을 업로드하거나 폴더에 'countriesMBTI_16types.csv'를 두세요.")
            st.stop()

with right:
    st.subheader("💰 GNP 데이터")
    st.caption("예시 스키마: Country, GNP 또는 Country, GNP_per_capita")
    gnp_file = st.file_uploader("GNP CSV 업로드 (미업로드 시 기본 파일 사용)", type=["csv"], key="gnp")
    if gnp_file is not None:
        df_gnp = pd.read_csv(gnp_file)
    else:
        # 기본 파일명 시도
        try:
            df_gnp = load_csv("country_gnp.csv")
        except Exception as e:
            st.error("GNP 파일을 업로드하거나 폴더에 'country_gnp.csv'를 두세요.")
            st.stop()

# ============================
# 컬럼 검사 & 전처리
# ============================
if "Country" not in df_mbti.columns:
    st.error("MBTI CSV에 'Country' 컬럼이 필요합니다.")
    st.stop()

# MBTI 열(첫 컬럼 Country 제외, 숫자형만)
mbti_cols = [c for c in df_mbti.columns if c != "Country" and pd.api.types.is_numeric_dtype(df_mbti[c])]

# GNP 타깃 컬럼 자동 탐지
candidate_y = [c for c in df_gnp.columns if c.lower() in ["gnp", "gnp_per_capita", "gni", "gni_per_capita", "gdp", "gdp_per_capita"]]
if len(candidate_y) == 0:
    st.error("GNP CSV에서 타깃 수치 컬럼을 찾지 못했습니다. (예: GNP, GNP_per_capita 등)")
    st.stop()

# 국가명 정규화(충돌 완화)
df_mbti["Country_norm"] = normalize_country_name(df_mbti["Country"])
df_gnp["Country_norm"] = normalize_country_name(df_gnp["Country"]) if "Country" in df_gnp.columns else np.nan

# GNP 타깃 선택
st.sidebar.header("⚙️ 분석 설정")
y_col = st.sidebar.selectbox("GNP(또는 유사 지표) 컬럼 선택", options=candidate_y, index=0)
log_scale = st.sidebar.checkbox("Y(경제지표) 로그 스케일 적용", value=True)
use_abs_sort = st.sidebar.checkbox("상관계수 정렬 시 절댓값 기준", value=True)

# 조인
df_join = pd.merge(
    df_mbti[["Country", "Country_norm"] + mbti_cols],
    df_gnp[["Country_norm", y_col]],
    on="Country_norm",
    how="inner",
    validate="m:1"
).rename(columns={y_col: "Y_value"})

# 조인 결과 안내
miss_mbti = set(df_mbti["Country_norm"]) - set(df_join["Country_norm"])
miss_gnp = set(df_gnp["Country_norm"]) - set(df_join["Country_norm"])
with st.expander("🔎 매칭 결과(국가명 기준) 확인"):
    st.write(f"• MBTI 파일 국가 수: {df_mbti['Country_norm'].nunique()}  /  GNP 파일 국가 수: {df_gnp['Country_norm'].nunique()}  /  매칭 성공: {df_join['Country_norm'].nunique()}")
    if len(miss_mbti) > 0:
        st.write("• MBTI에만 있고 매칭 안 된 국가 수:", len(miss_mbti))
    if len(miss_gnp) > 0:
        st.write("• GNP에만 있고 매칭 안 된 국가 수:", len(miss_gnp))

# 로그 변환(선택)
if log_scale:
    df_join["Y_trans"] = np.log1p(df_join["Y_value"])
    y_for_corr = "Y_trans"
    y_label = f"{y_col} (log1p)"
else:
    y_for_corr = "Y_value"
    y_label = y_col

# ============================
# 1) 상관계수 표
# ============================
st.subheader("📋 MBTI × GNP 상관분석 표")
corr_df = compute_correlations(df_join.rename(columns={"Y_value": y_col, "Y_trans": y_for_corr}), mbti_cols, y_for_corr)

# 정렬 옵션 적용
sort_key = corr_df["pearson_r"].abs() if use_abs_sort else corr_df["pearson_r"]
corr_df_display = corr_df.sort_values(by=sort_key.name, ascending=False).copy()

# 보기 좋게 형식화
def fmt(p):
    return "" if pd.isna(p) else f"{p:,.4f}"

corr_df_display["pearson_r"] = corr_df_display["pearson_r"].map(lambda x: fmt(x))
corr_df_display["pearson_p"] = corr_df_display["pearson_p"].map(lambda x: fmt(x))
corr_df_display["spearman_r"] = corr_df_display["spearman_r"].map(lambda x: fmt(x))
corr_df_display["spearman_p"] = corr_df_display["spearman_p"].map(lambda x: fmt(x))

st.dataframe(
    corr_df_display.rename(columns={
        "MBTI": "MBTI 유형",
        "pearson_r": "피어슨 r",
        "pearson_p": "피어슨 p",
        "spearman_r": "스피어만 r",
        "spearman_p": "스피어만 p",
        "n": "표본수"
    }),
    use_container_width=True
)

st.caption("• p < 0.05이면 통계적으로 유의미한 상관으로 해석 가능(표본 크기와 분포에 따라 달라질 수 있음)")

# ============================
# 2) 히트맵(피어슨 상관)
# ============================
st.subheader("🔥 피어슨 상관 히트맵 (MBTI 16유형 vs 경제지표)")
pearson_vals = []
for c in mbti_cols:
    sub = df_join[[c, y_for_corr]].dropna()
    if len(sub) >= 3:
        r, _ = stats.pearsonr(sub[c], sub[y_for_corr])
    else:
        r = np.nan
    pearson_vals.append(r)

heat_df = pd.DataFrame({"MBTI": mbti_cols, "pearson_r": pearson_vals}).set_index("MBTI")

# plotly figure_factory를 이용한 히트맵(1열짜리)
z = np.array([heat_df["pearson_r"].values])
fig_heat = ff.create_annotated_heatmap(
    z=z,
    x=heat_df.index.tolist(),
    y=[y_label + " 상관"],
    colorscale="RdBu",
    zmin=-1, zmax=1,
    showscale=True,
    annotation_text=np.array([[f"{v:.2f}" if not pd.isna(v) else "" for v in z[0]]])
)
fig_heat.update_layout(height=240, margin=dict(l=30, r=30, t=20, b=20))
st.plotly_chart(fig_heat, use_container_width=True)

# ============================
# 3) 산점도 + 추세선
# ============================
st.subheader("📉 산점도(국가별) + 선형 추세선")
target_mbti = st.selectbox("MBTI 유형 선택", options=mbti_cols, index=0)

scatter_df = df_join[["Country", target_mbti, y_for_corr]].dropna().copy()
scatter_df.rename(columns={target_mbti: "MBTI_ratio", y_for_corr: "Y_metric"}, inplace=True)

if scatter_df.empty or len(scatter_df) < 3:
    st.warning("표본이 부족하여 산점도를 표시할 수 없습니다. 다른 MBTI 유형을 선택해 보세요.")
else:
    fig_scatter = px.scatter(
        scatter_df,
        x="MBTI_ratio", y="Y_metric",
        hover_name="Country",
        trendline="ols",  # statsmodels 필요
        labels={"MBTI_ratio": f"{target_mbti} 비율", "Y_metric": y_label},
        opacity=0.85,
        title=f"{target_mbti} 비율 vs {y_label}"
    )
    fig_scatter.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 간단 회귀·상관 수치 표시
    pr, pp = stats.pearsonr(scatter_df["MBTI_ratio"], scatter_df["Y_metric"])
    sr, sp = stats.spearmanr(scatter_df["MBTI_ratio"], scatter_df["Y_metric"])
    st.markdown(
        f"- **피어슨 r** = {pr:.4f} (p={pp:.4f})  \n"
        f"- **스피어만 r** = {sr:.4f} (p={sp:.4f})  \n"
        f"- 표본수 n = {len(scatter_df)}"
    )

# ============================
# 부록: 데이터 미리보기
# ============================
with st.expander("🗂️ 조인된 원자료 미리보기"):
    preview_cols = ["Country"] + mbti_cols + ["Y_value"]
    if "Y_trans" in df_join.columns:
        preview_cols += ["Y_trans"]
    st.dataframe(df_join[preview_cols].head(20), use_container_width=True)

st.markdown("""
---
**해석 가이드**  
- 상관관계(r)는 **선형성 방향·강도**를 나타낼 뿐, **인과관계**를 의미하지 않음.  
- 국가별 표본 수(n)가 작거나 분포가 치우칠 경우 p값 해석에 주의가 필요함.  
- 로그 스케일(`log1p`)은 경제지표의 극단값(대국/소국 편차)을 완화하여 상관을 더 안정적으로 볼 수 있게 함.
""")

