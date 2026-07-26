import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Global Climate & Natural Disaster Analysis",
    page_icon="🌍",
    layout="wide"
)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🌍 Global Climate & Natural Disaster Analysis (1970–2021)")
st.markdown(
    """
This dashboard explores global natural disasters using the EM-DAT dataset.
Use the filters in the sidebar to interactively explore disaster trends,
human impact and economic losses.
"""
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "raw" / "emdat_disasters_1970_2021.csv"
    df = pd.read_csv(DATA_PATH)

    numeric_cols = [
    "Start Year",
    "Total Deaths",
    "Total Affected",
    "Total Damages ('000 US$)",
    "Dis Mag Value",
    "Latitude",
    "Longitude"
]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

# Year Filter
years = sorted(df["Start Year"].dropna().unique())

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

# Continent Filter
continents = sorted(df["Continent"].dropna().unique())

selected_continents = st.sidebar.multiselect(
    "Select Continents",
    continents,
    default=continents
)

# Disaster Type Filter
types = sorted(df["Disaster Type"].dropna().unique())

selected_types = st.sidebar.multiselect(
    "Select Disaster Types",
    types,
    default=types
)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df[
    (df["Start Year"] >= year_range[0]) &
    (df["Start Year"] <= year_range[1]) &
    (df["Continent"].isin(selected_continents)) &
    (df["Disaster Type"].isin(selected_types))
]

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

st.markdown("## 📊 Key Statistics")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Total Disasters",
        f"{len(filtered_df):,}"
    )

with kpi2:
    st.metric(
        "Total Deaths",
        f"{filtered_df['Total Deaths'].sum():,.0f}"
    )

with kpi3:
    st.metric(
        "People Affected",
        f"{filtered_df['Total Affected'].sum():,.0f}"
    )

damage = filtered_df["Total Damages ('000 US$)"].fillna(0).sum()

with kpi4:
    st.metric(
        "Economic Damage ('000 US$)",
        f"{damage:,.0f}"
    )

st.markdown("---")
# ==================================================
# CHART 1 : Disaster Trend Over Time
# ==================================================

trend = (
    filtered_df.groupby("Start Year")
    .size()
    .reset_index(name="Number of Disasters")
)

fig1 = px.line(
    trend,
    x="Start Year",
    y="Number of Disasters",
    markers=True,
    title="Trend of Natural Disasters (1970–2021)"
)

fig1.update_layout(
    template="plotly_white",
    title_x=0.5,
    xaxis_title="Year",
    yaxis_title="Number of Disasters"
)

# ==================================================
# CHART 2 : Deaths by Disaster Type
# ==================================================

deaths = (
    filtered_df.groupby("Disaster Type", as_index=False)["Total Deaths"]
    .sum()
    .sort_values("Total Deaths", ascending=False)
)

fig2 = px.bar(
    deaths,
    x="Total Deaths",
    y="Disaster Type",
    orientation="h",
    color="Total Deaths",
    color_continuous_scale="Reds",
    title="Total Deaths by Disaster Type"
)

fig2.update_layout(
    template="plotly_white",
    title_x=0.5,
    yaxis=dict(categoryorder="total ascending")
)

# ==================================================
# CHART 3 : Human Impact by Continent
# ==================================================

continent = (
    filtered_df.groupby("Continent", as_index=False)["Total Affected"]
    .sum()
)

fig3 = px.bar(
    continent,
    x="Continent",
    y="Total Affected",
    color="Continent",
    title="People Affected by Continent"
)

fig3.update_layout(
    template="plotly_white",
    title_x=0.5,
    xaxis_title="Continent",
    yaxis_title="People Affected"
)

# ==================================================
# CHART 4 : Economic Loss by Country
# ==================================================

damage = (
    filtered_df.groupby("Country", as_index=False)["Total Damages ('000 US$)"]
    .sum()
    .sort_values("Total Damages ('000 US$)", ascending=False)
    .head(15)
)

fig4 = px.bar(
    damage,
    x="Total Damages ('000 US$)",
    y="Country",
    orientation="h",
    color="Total Damages ('000 US$)",
    color_continuous_scale="Viridis",
    title="Top 15 Countries by Economic Damage"
)

fig4.update_layout(
    template="plotly_white",
    title_x=0.5,
    yaxis=dict(categoryorder="total ascending")
)

# ==================================================
# CHART 5 : Disaster Magnitude vs Total Deaths
# ==================================================

# Check which magnitude column exists
if "Dis Mag Value" in filtered_df.columns:
    mag_col = "Dis Mag Value"
elif "Magnitude" in filtered_df.columns:
    mag_col = "Magnitude"
else:
    mag_col = None

if mag_col is not None:

    scatter = filtered_df[
        [mag_col, "Total Deaths", "Disaster Type"]
    ].copy()

    scatter = scatter.dropna()

    fig5 = px.scatter(
        scatter,
        x=mag_col,
        y="Total Deaths",
        color="Disaster Type",
        hover_name="Disaster Type",
        opacity=0.75,
        title="Relationship Between Disaster Magnitude and Total Deaths"
    )

    fig5.update_traces(marker=dict(size=8))

    fig5.update_layout(
        template="plotly_white",
        title_x=0.5,
        xaxis_title="Disaster Magnitude",
        yaxis_title="Total Deaths",
        legend_title="Disaster Type",
        height=600
    )

else:

    fig5 = px.scatter(
        title="Magnitude information is not available in this dataset."
    )

    fig5.update_layout(
        template="plotly_white",
        height=600
    )
# ==================================================
# CHART 6 : Disaster Occurrence by Month
# ==================================================

month_col = None

possible_month_columns = [
    "Start Month",
    "Start Month Num",
    "Month",
    "Start_Month"
]

for col in possible_month_columns:
    if col in filtered_df.columns:
        month_col = col
        break

if month_col:

    month_data = (
        filtered_df
        .groupby([month_col, "Disaster Type"])
        .size()
        .reset_index(name="Count")
    )

    month_pivot = month_data.pivot(
        index="Disaster Type",
        columns=month_col,
        values="Count"
    ).fillna(0)

    fig6 = px.imshow(
        month_pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Seasonality of Natural Disasters"
    )

    fig6.update_layout(
        template="plotly_white",
        title_x=0.5,
        xaxis_title="Month",
        yaxis_title="Disaster Type",
        height=600
    )

else:

    fig6 = px.imshow(
        [[0]],
        title="Month information not available"
    )

# ==================================================
# CHART 7 : Disaster Subgroup Treemap
# ==================================================

subgroup_col = None

possible_subgroup_columns = [
    "Disaster Subgroup",
    "Dis Subtype",
    "Disaster Subtype",
    "Subgroup"
]

for col in possible_subgroup_columns:
    if col in filtered_df.columns:
        subgroup_col = col
        break

if subgroup_col:

    tree = (
        filtered_df
        .groupby([subgroup_col, "Disaster Type"])
        .size()
        .reset_index(name="Count")
    )

    fig7 = px.treemap(
        tree,
        path=[subgroup_col, "Disaster Type"],
        values="Count",
        color="Count",
        color_continuous_scale="Teal",
        title="Distribution of Disaster Types"
    )

    fig7.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=700
    )

else:

    tree = (
        filtered_df
        .groupby("Disaster Type")
        .size()
        .reset_index(name="Count")
    )

    fig7 = px.treemap(
        tree,
        path=["Disaster Type"],
        values="Count",
        color="Count",
        color_continuous_scale="Teal",
        title="Distribution of Disaster Types"
    )

# ==================================================
# CHART 8 : Human Impact vs Economic Damage
# ==================================================

damage_col = None

possible_damage_columns = [
    "Total Damages ('000 US$)",
    "Total Damages, Adjusted ('000 US$)",
    "Reconstruction Costs ('000 US$)"
]

for col in possible_damage_columns:
    if col in filtered_df.columns:
        damage_col = col
        break

if damage_col:

    bubble = (
        filtered_df
        .groupby("Disaster Type", as_index=False)
        .agg({
            "Total Affected": "sum",
            damage_col: "sum"
        })
    )

    bubble = bubble.fillna(0)

    fig8 = px.scatter(
        bubble,
        x="Total Affected",
        y=damage_col,
        size=damage_col,
        color="Disaster Type",
        hover_name="Disaster Type",
        size_max=60,
        title="Human Impact vs Economic Damage"
    )

    fig8.update_layout(
        template="plotly_white",
        title_x=0.5,
        xaxis_title="People Affected",
        yaxis_title="Economic Damage ('000 US$)",
        height=650
    )

else:

    fig8 = px.scatter(
        title="Economic damage information not available."
    )

# ==================================================
# CHART 9 : Global Disaster Map
# ==================================================

lat_col = None
lon_col = None

possible_lat = [
    "Latitude",
    "Lat",
    "latitude"
]

possible_lon = [
    "Longitude",
    "Lon",
    "longitude"
]

for col in possible_lat:
    if col in filtered_df.columns:
        lat_col = col
        break

for col in possible_lon:
    if col in filtered_df.columns:
        lon_col = col
        break

if lat_col and lon_col:

    map_df = filtered_df[
        [
            lat_col,
            lon_col,
            "Country",
            "Disaster Type"
        ]
    ].dropna()

    fig9 = px.scatter_geo(
        map_df,
        lat=lat_col,
        lon=lon_col,
        color="Disaster Type",
        hover_name="Country",
        title="Global Distribution of Natural Disasters"
    )

    fig9.update_layout(
        template="plotly_white",
        title_x=0.5,
        geo=dict(
            showland=True,
            showcountries=True,
            landcolor="rgb(245,245,245)"
        ),
        height=700
    )

else:

    country_counts = (
        filtered_df
        .groupby("Country")
        .size()
        .reset_index(name="Disasters")
    )

    fig9 = px.bar(
        country_counts.sort_values(
            "Disasters",
            ascending=False
        ).head(20),
        x="Disasters",
        y="Country",
        orientation="h",
        title="Top 20 Countries by Number of Recorded Disasters"
    )

    fig9.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=700
    )

# ==================================================
# CHART 10 : Economic Damage Sunburst
# ==================================================

damage_col = None

possible_damage_columns = [
    "Total Damages ('000 US$)",
    "Total Damages, Adjusted ('000 US$)",
    "Reconstruction Costs ('000 US$)"
]

for col in possible_damage_columns:
    if col in filtered_df.columns:
        damage_col = col
        break

if damage_col:

    sunburst = (
        filtered_df
        .groupby(
            ["Continent", "Disaster Type"],
            as_index=False
        )[damage_col]
        .sum()
    )

    fig10 = px.sunburst(
        sunburst,
        path=["Continent", "Disaster Type"],
        values=damage_col,
        color=damage_col,
        color_continuous_scale="Viridis",
        title="Economic Damage by Continent and Disaster Type"
    )

    fig10.update_layout(
        template="plotly_white",
        title_x=0.5,
        height=700
    )

else:

    fig10 = px.sunburst(
        names=["No Data"],
        parents=[""],
        values=[1],
        title="Economic damage information not available."
    )

    fig10.update_layout(
        template="plotly_white",
        height=700
    )
# ==================================================
# CREATE DASHBOARD TABS
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Overview",
        "👥 Human Impact",
        "🌍 Disaster Analysis",
        "💰 Economic Impact"
    ]
)

# ==================================================
# TAB 1
# ==================================================

with tab1:

    st.subheader("Global Disaster Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.plotly_chart(fig2, use_container_width=True)

    st.plotly_chart(fig6, use_container_width=True)

# ==================================================
# TAB 2
# ==================================================

with tab2:

    st.subheader("Human Impact")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        st.plotly_chart(fig5, use_container_width=True)

    st.plotly_chart(fig8, use_container_width=True)

# ==================================================
# TAB 3
# ==================================================

with tab3:

    st.subheader("Disaster Distribution")

    st.plotly_chart(fig7, use_container_width=True)

    st.plotly_chart(fig9, use_container_width=True)

# ==================================================
# TAB 4
# ==================================================

with tab4:

    st.subheader("Economic Impact")

    st.plotly_chart(fig10, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Project Summary")

    st.success(
        """
### Key Findings

• The number of recorded natural disasters has generally increased over time.

• Floods, storms, and earthquakes account for the majority of disasters worldwide.

• Asia experiences the greatest human impact in terms of deaths and affected populations.

• Economic losses are concentrated in a relatively small number of countries.

• Different disaster types show distinct seasonal patterns.

• Disaster magnitude does not always correspond directly to higher fatalities.

• The dashboard enables interactive exploration using year, continent, and disaster-type filters.
"""
    )

# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

st.markdown(
    """
<div style='text-align:center; padding:20px;'>

<h3>🌍 Global Climate & Natural Disaster Analysis</h3>

<b>Prepared By</b><br>
Ankit Semwal

<br><br>

<b>Course</b><br>
Data Visualization

<br><br>

<b>University</b><br>
University of Europe for Applied Sciences

<br><br>

<b>Dataset</b><br>
EM-DAT International Disaster Database (1970–2021)

</div>
""",
    unsafe_allow_html=True,
)