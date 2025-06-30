# https://www.notion.so/adidas-dashboard-2218c1a6fba8801691d4f539e84a7635

# 1. 라이브러리 임포트 및 기본 설정
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sms
import plotly.graph_objects as go

st.set_page_config(page_title="Adidas US Sales Dashboard", layout="wide")
st.title("👟 Adidas US Sales Data Dashboard")

# 2. 데이터 불러오기 및 전처리
data = pd.read_csv("https://raw.githubusercontent.com/myoh0623/dataset/refs/heads/main/adidas_us_sales_datasets.csv")

data.columns = data.columns.str.strip()
for col in ["Price per Unit", "Total Sales", "Operating Profit"]:
    data[col] = data[col].replace("[\$,]", "", regex=True).astype(float)
data["Units Sold"] = data["Units Sold"].replace("[,]", "", regex=True).astype(int)
data["Operating Margin"] = data["Operating Margin"].replace("[\%]", "", regex=True).astype(float)
data["Invoice Date"] = pd.to_datetime(data["Invoice Date"], errors="coerce")
data = data.dropna(subset=["Invoice Date"])

# 3. 파생 변수 생성
data["Profit Rete"] = data["Operating Margin"] * 0.01
data["Year"] = data["Invoice Date"].dt.year
data["Month"] = data["Invoice Date"].dt.month

# 4. 사이드바 필터 구현
st.sidebar.header("Filter Options")
region = st.sidebar.multiselect("Region", options=sorted(data["Region"].dropna().unique()), default=list(data["Region"].dropna().unique()))
retailer = st.sidebar.multiselect("Retailer", options=sorted(data["Retailer"].dropna().unique()), default=list(data["Retailer"].dropna().unique()))
product = st.sidebar.multiselect("Product", options=sorted(data["Product"].dropna().unique()), default=list(data["Product"].dropna().unique()))
sales_method = st.sidebar.multiselect("Sales Method", options=sorted(data["Sales Method"].dropna().unique()), default=list(data["Sales Method"].dropna().unique()))

filtered = data[
    (data["Region"].isin(region)) &
    (data["Retailer"].isin(retailer)) &
    (data["Product"].isin(product)) &
    (data["Sales Method"].isin(sales_method))
]

# 5. 주요 지표 요약 표시
st.markdown("## 📈 주요 지표")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"${filtered['Total Sales'].sum():,.0f}")
k2.metric("Units Sold", f"{filtered['Units Sold'].sum():,} 개")
k3.metric("Price per Unit", f"${filtered['Price per Unit'].mean():.2f}")
k4.metric("Operating Margin", f"{filtered['Operating Margin'].mean():.2f}%")

# 6. 탭(Tab) 레이아웃 구성
tab1, tab2, tab3 = st.tabs(["트렌드 및 분포", "소매점/제품", "심화 분석"])

# 7. 트렌드 및 분포 시각화
# 월별 판매 트렌드
st.subheader("월별 판매 트렌드")
monthly_summary = filtered.groupby("Month").agg({
    "Units Sold": "sum",
    "Total Sales": "sum"
}).reset_index()
st.line_chart(monthly_summary)

# 판매방법 비율
import plotly.graph_objects as go

st.subheader("판매방법 비율")
sales_method_counts = filtered["Sales Method"].value_counts()
fig_pie = go.Figure(data=[go.Pie(
    labels=sales_method_counts.index,
    values=sales_method_counts.values,
    hole=0.3  
)])
st.plotly_chart(fig_pie)

# 제품-지역별 판매 히트맵
import plotly.express as px

st.subheader("제품-지역별 판매 히트맵")
pivot_table = filtered.pivot_table(
    index="Product", 
    columns="Region", 
    values="Units Sold", 
    aggfunc="sum",
    fill_value=0
)
fig_heatmap = px.imshow(
    pivot_table,
    labels=dict(x="Region", y="Product", color="Units Sold"),
    x=pivot_table.columns,
    y=pivot_table.index,
    color_continuous_scale='Viridis'
)
st.plotly_chart(fig_heatmap)

# 8. 소매점/제품 분석
# 소매점별 판매수량/매출
retailer_summary = filtered.groupby("Retailer").agg({
    "Units Sold": "sum",
    "Total Sales": "sum"
}).sort_values("Units Sold", ascending=False).reset_index()

st.subheader("소매점별 판매수량 및 매출")
st.bar_chart(retailer_summary.set_index("Retailer")[["Units Sold", "Total Sales"]])

# 제품별 판매수량
product_summary = filtered.groupby("Product")["Units Sold"].sum().sort_values(ascending=False)

st.subheader("제품별 판매수량")
st.bar_chart(product_summary)

# 월별-제품별 판매 피벗테이블
filtered["Invoice Date"] = pd.to_datetime(filtered["Invoice Date"], errors="coerce")
filtered["Month"] = filtered["Invoice Date"].dt.to_period("M").astype(str)

pivot_month_product = pd.pivot_table(
    filtered,
    values="Units Sold",
    index="Month",
    columns="Product",
    aggfunc="sum",
    fill_value=0
).sort_index()

st.subheader("월별-제품별 판매량 피벗테이블")
st.dataframe(pivot_month_product)

# 9. 심화 분석
# 판매방법별 평균 마진율/단가
margin_price_summary = filtered.groupby("Sales Method").agg({
    "Operating Margin": "mean",
    "Price per Unit": "mean"
}).reset_index()

st.subheader("판매방법별 평균 마진율 및 단가")
st.bar_chart(margin_price_summary.set_index("Sales Method")[["Operating Margin", "Price per Unit"]])

# 단가-판매수량 산점도
st.subheader("단가와 판매수량 산점도")
fig_scatter = px.scatter(
    filtered,
    x="Price per Unit",
    y="Units Sold",
    color="Sales Method",
    size="Total Sales",          
    hover_data=["Product", "Retailer"],
    title="단가 대비 판매수량 분포"
)
st.plotly_chart(fig_scatter)

# 데이터 미리보기
with st.expander("원본 데이터 미리보기"):
    st.dataframe(filtered)

# 10. 인사이트 요약
st.markdown("""
---
### 📌 인사이트 요약
- **판매방법별 마진율**: 온라인, 아울렛, 오프라인 등 판매방법에 따라 마진율과 단가가 다릅니다.
- **소매업체별 실적**: 주요 소매업체별 판매량/매출을 비교할 수 있습니다.
- **월별 추이**: 월별 판매량/매출의 계절성 및 트렌드를 파악할 수 있습니다.
- **제품별 인기**: 어떤 제품군이 많이 팔리는지 한눈에 확인할 수 있습니다.
- **필터**: 지역, 소매업체, 제품, 판매방법별로 상세 분석이 가능합니다.

> 데이터를 다양한 각도에서 탐색하며, 비즈니스 전략 수립에 활용해보세요.
""")