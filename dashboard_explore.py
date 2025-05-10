import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def load_data():
    return pd.read_parquet("./indicators_time_series.parquet")

df = load_data()

# Sidebar filters
st.sidebar.header("Filter")
countries = sorted(df['iso3'].unique())
indicators = sorted(df['indicator_name'].unique())

selected_country_1 = st.sidebar.selectbox("Country 1 (ISO3)", countries, index=0)
selected_country_2 = st.sidebar.selectbox("Country 2 (ISO3)", countries, index=0)
selected_indicator_1 = st.sidebar.selectbox("Indicator 1", indicators, index=0)
selected_indicator_2 = st.sidebar.selectbox("Indicator 2", indicators, index=1 if len(indicators) > 1 else 0)

# Metric toggles
available_metrics = ['value', 'weighted_status', 'ema_status', 'weighted_heritage', 'trend', 'seasonal', 'resid']
selected_metrics = st.sidebar.multiselect(
    "Select metrics to display",
    options=available_metrics,
    default=['value', 'weighted_status', 'ema_status', 'trend']
)

# Define styles
colors = {
    'value': 'black',
    'weighted_status': '#e3120b',
    'ema_status': '#1f77b4',
    'weighted_heritage': '#999999',
    'trend': '#2ca02c',
    'seasonal': '#ff7f0e',
    'resid': 'gray'
}

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

# Prepare data for each chart
df1 = df[(df['iso3'] == selected_country_1) & (df['indicator_name'] == selected_indicator_1)].copy()
df1['period'] = pd.to_datetime(df1['period'])
df1 = df1.sort_values("period")

show_second = not (selected_country_1 == selected_country_2 and selected_indicator_1 == selected_indicator_2)

if show_second:
    df2 = df[(df['iso3'] == selected_country_2) & (df['indicator_name'] == selected_indicator_2)].copy()
    df2['period'] = pd.to_datetime(df2['period'])
    df2 = df2.sort_values("period")

# Layout
st.plotly_chart(create_chart(df1, f"{selected_indicator_1} for {selected_country_1}"), use_container_width=True, key="chart1")

if show_second:
    st.plotly_chart(create_chart(df2, f"{selected_indicator_2} for {selected_country_2}"), use_container_width=True, key="chart2")
else:
    st.info("Select a different indicator or country to compare.")
