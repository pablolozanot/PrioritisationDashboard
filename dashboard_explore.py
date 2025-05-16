import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import itertools
from plotly.colors import qualitative

# Custom sidebar width
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            min-width: 300px;
            max-width: 350px;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_parquet("./indicators_time_series.parquet")

@st.cache_data
def load_country_mapping():
    return pd.read_csv("./iso_country_codes.csv")

# Load data and mapping
df = load_data()
country_map_df = load_country_mapping()
st.title("Country Data Exploration Tool")

# Country name mappings
name_by_iso3 = country_map_df.set_index("alpha-3")["name"].to_dict()
iso3_by_name = {v: k for k, v in name_by_iso3.items()}
country_names = sorted(iso3_by_name.keys())

# Detect metrics dynamically
non_metrics = ['period', 'iso3', 'indicator_name', 'resid_spike']
available_metrics = [col for col in df.columns if col not in non_metrics]
default_metrics = [m for m in ['value', 'Weighted Status', 'Variation (weighted) - Weighted Status'] if m in available_metrics]

# Assign colors: fixed for key metrics, vibrant for others
base_colors = {
    'value': 'black',
    'Weighted Status': '#e3120b',
    'Heritage Status': '#999999',
    'Long Term Trend': '#2ca02c',
    'Seasonal Trend': '#ff7f0e',
    'Residual Trend': 'gray',
    'Variation (weighted) - Smooth Status': '#9467bd',
    'Variation (weighted) - Weighted Status': '#8c564b'
}
color_cycle = itertools.cycle(qualitative.Plotly + qualitative.Set2 + qualitative.Dark24)
colors = {metric: base_colors.get(metric, next(color_cycle)) for metric in available_metrics}

# Sidebar filters
st.sidebar.header("Chart Filters")
indicators = sorted(df['indicator_name'].unique())

# Chart 1
st.sidebar.markdown("### Chart 1")
selected_country_name_1 = st.sidebar.selectbox("Country 1", country_names, index=0, key="country1")
selected_country_1 = iso3_by_name[selected_country_name_1]
selected_indicator_1 = st.sidebar.selectbox("Indicator 1", indicators, index=0, key="indicator1")

# Chart 2
st.sidebar.markdown("### Chart 2")
selected_country_name_2 = st.sidebar.selectbox("Country 2", country_names, index=0, key="country2")
selected_country_2 = iso3_by_name[selected_country_name_2]
selected_indicator_2 = st.sidebar.selectbox("Indicator 2", indicators, index=1 if len(indicators) > 1 else 0, key="indicator2")

# Metric selection
st.sidebar.markdown("### Metrics to Display")
metric_cols = st.sidebar.columns(2)
selected_metrics = []
for i, metric in enumerate(available_metrics):
    with metric_cols[i % 2]:
        if st.checkbox(metric.replace("_", " ").title(), value=metric in default_metrics, key=f"metric_{metric}"):
            selected_metrics.append(metric)

# Chart generator
def create_chart(df_filtered, title):
    fig = go.Figure()
    for metric in selected_metrics:
        if metric in df_filtered.columns:
            fig.add_trace(go.Scatter(
                x=df_filtered['period'],
                y=df_filtered[metric],
                mode='markers' if metric == 'value' else 'lines',
                name=metric.replace('_', ' ').title(),
                line=dict(color=colors.get(metric, 'gray'), width=2,
                          dash='dash' if metric in ['trend', 'seasonal'] else 'solid') if metric != 'value' else None,
                marker=dict(color='black') if metric == 'value' else None,
                opacity=0.9 if metric != 'resid' else 0.4
            ))
    if 'resid_spike' in df_filtered.columns:
        for d in df_filtered[df_filtered['resid_spike']]['period']:
            fig.add_vline(x=d, line_color='red', line_dash='dash', opacity=0.3)

    fig.update_layout(
        title=title,
        xaxis_title="Period",
        yaxis_title="Value",
        template="plotly_white",
        hovermode="x unified",
        height=500,
        width=900
    )
    return fig

# Data for Chart 1
df1 = df[(df['iso3'] == selected_country_1) & (df['indicator_name'] == selected_indicator_1)].copy()
df1['period'] = pd.to_datetime(df1['period'])
df1 = df1.sort_values("period")

# Data for Chart 2 (only if different)
show_second = not (selected_country_1 == selected_country_2 and selected_indicator_1 == selected_indicator_2)
if show_second:
    df2 = df[(df['iso3'] == selected_country_2) & (df['indicator_name'] == selected_indicator_2)].copy()
    df2['period'] = pd.to_datetime(df2['period'])
    df2 = df2.sort_values("period")

# Display charts
st.plotly_chart(create_chart(df1, f"{selected_indicator_1} for {selected_country_name_1} ({selected_country_1})"),
                use_container_width=True, key="chart1")

if show_second:
    st.plotly_chart(create_chart(df2, f"{selected_indicator_2} for {selected_country_name_2} ({selected_country_2})"),
                    use_container_width=True, key="chart2")
else:
    st.info("Select a different indicator or country to compare.")
