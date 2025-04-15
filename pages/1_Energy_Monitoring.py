import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from data_generator import data_generator
from utils import format_power

# Configure the page
st.set_page_config(
    page_title="Energy Monitoring | Solar-Wind Hybrid Monitor",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Title and description
st.title("Energy Monitoring")
st.write("Detailed view of energy generation, battery status, and consumption patterns")

# Time period selector
timeframe = st.radio(
    "Select Time Period",
    ["Day", "Week", "Month"],
    horizontal=True
)

# Get historical data based on selected timeframe
historical_data = data_generator.get_historical_data(timeframe=timeframe.lower())

if historical_data.empty:
    st.info("Not enough historical data available yet. Please wait while data is being collected.")
    st.stop()

# Create tabs for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["Power Generation", "Energy Balance", "Battery Status", "Environmental Data"])

# Tab 1: Power Generation
with tab1:
    if timeframe == "Day":
        period_text = "Daily"
    elif timeframe == "Week":
        period_text = "Weekly"
    else:
        period_text = "Monthly"
        
    st.subheader(f"{period_text} Power Generation")
    
    # Create time series plot for power generation
    fig = go.Figure()
    
    # Add solar power line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["solar_power"],
        name="Solar",
        line=dict(color="#FFD700", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 215, 0, 0.2)"
    ))
    
    # Add wind power line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["wind_power"],
        name="Wind",
        line=dict(color="#4682B4", width=2),
        fill="tozeroy",
        fillcolor="rgba(70, 130, 180, 0.2)"
    ))
    
    # Add total generation line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["total_generation"],
        name="Total",
        line=dict(color="#32CD32", width=3)
    ))
    
    # Update layout
    fig.update_layout(
        height=500,
        xaxis_title="Time",
        yaxis_title="Power (kW)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=30, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    # Add grid lines
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add summary stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_solar = historical_data["solar_power"].mean()
        max_solar = historical_data["solar_power"].max()
        st.metric("Avg Solar Power", f"{avg_solar:.2f} kW", f"Max: {max_solar:.2f} kW")
    
    with col2:
        avg_wind = historical_data["wind_power"].mean()
        max_wind = historical_data["wind_power"].max()
        st.metric("Avg Wind Power", f"{avg_wind:.2f} kW", f"Max: {max_wind:.2f} kW")
    
    with col3:
        avg_total = historical_data["total_generation"].mean()
        max_total = historical_data["total_generation"].max()
        st.metric("Avg Total Power", f"{avg_total:.2f} kW", f"Max: {max_total:.2f} kW")

# Tab 2: Energy Balance
with tab2:
    if timeframe == "Day":
        period_text = "Daily"
    elif timeframe == "Week":
        period_text = "Weekly"
    else:
        period_text = "Monthly"
        
    st.subheader(f"{period_text} Energy Balance")
    
    # Create time series plot for power balance
    fig = go.Figure()
    
    # Add total generation line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["total_generation"],
        name="Generation",
        line=dict(color="#32CD32", width=2),
        fill="tozeroy",
        fillcolor="rgba(50, 205, 50, 0.2)"
    ))
    
    # Add load line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["load"],
        name="Load",
        line=dict(color="#FF6347", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 99, 71, 0.2)"
    ))
    
    # Add net power line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["net_power"],
        name="Net Power",
        line=dict(color="#9370DB", width=3)
    ))
    
    # Update layout
    fig.update_layout(
        height=500,
        xaxis_title="Time",
        yaxis_title="Power (kW)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=30, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    # Add grid lines
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='rgba(128,128,128,0.3)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate energy summary
    energy_summary = data_generator.get_energy_summary()
    
    # Show energy contribution chart
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create pie chart for energy sources
        fig = px.pie(
            values=[energy_summary["solar_energy"], energy_summary["wind_energy"]],
            names=["Solar", "Wind"],
            color_discrete_sequence=["#FFD700", "#4682B4"],
            title="Energy Source Distribution"
        )
        
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Show energy metrics
        st.subheader("Energy Summary")
        
        total_generation = energy_summary["total_energy"]
        total_load = energy_summary["load_energy"]
        net_energy = total_generation - total_load
        
        energy_metrics = {
            "Solar Energy": f"{energy_summary['solar_energy']:.2f} kWh ({energy_summary['solar_percentage']:.1f}%)",
            "Wind Energy": f"{energy_summary['wind_energy']:.2f} kWh ({energy_summary['wind_percentage']:.1f}%)",
            "Total Generation": f"{total_generation:.2f} kWh",
            "Total Consumption": f"{total_load:.2f} kWh",
            "Net Energy": f"{net_energy:.2f} kWh ({'Surplus' if net_energy > 0 else 'Deficit'})"
        }
        
        # Create a table
        df_metrics = pd.DataFrame(list(energy_metrics.items()), columns=["Metric", "Value"])
        st.table(df_metrics)

# Tab 3: Battery Status
with tab3:
    if timeframe == "Day":
        period_text = "Daily"
    elif timeframe == "Week":
        period_text = "Weekly"
    else:
        period_text = "Monthly"
        
    st.subheader(f"{period_text} Battery Status")
    
    # Create time series plot for battery SOC
    fig = go.Figure()
    
    # Add SOC line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["battery_soc"],
        name="State of Charge",
        line=dict(color="#4CAF50", width=3),
        fill="tozeroy",
        fillcolor="rgba(76, 175, 80, 0.2)"
    ))
    
    # Add reference lines for SOC thresholds
    fig.add_shape(
        type="line",
        x0=historical_data["timestamp"].iloc[0],
        y0=20,
        x1=historical_data["timestamp"].iloc[-1],
        y1=20,
        line=dict(color="red", width=2, dash="dash")
    )
    
    fig.add_shape(
        type="line",
        x0=historical_data["timestamp"].iloc[0],
        y0=80,
        x1=historical_data["timestamp"].iloc[-1],
        y1=80,
        line=dict(color="green", width=2, dash="dash")
    )
    
    # Update layout
    fig.update_layout(
        height=350,
        xaxis_title="Time",
        yaxis_title="State of Charge (%)",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
        margin=dict(l=60, r=20, t=30, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    # Add grid lines
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional battery statistics
    col1, col2 = st.columns(2)
    
    with col1:
        # Battery voltage chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data["timestamp"],
            y=historical_data["battery_voltage"],
            name="Voltage",
            line=dict(color="#FF9800", width=2)
        ))
        
        fig.update_layout(
            height=250,
            xaxis_title="Time",
            yaxis_title="Voltage (V)",
            margin=dict(l=60, r=20, t=30, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Battery temperature chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data["timestamp"],
            y=historical_data["battery_temperature"],
            name="Temperature",
            line=dict(color="#E91E63", width=2)
        ))
        
        fig.update_layout(
            height=250,
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            margin=dict(l=60, r=20, t=30, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Environmental Data
with tab4:
    if timeframe == "Day":
        period_text = "Daily"
    elif timeframe == "Week":
        period_text = "Weekly"
    else:
        period_text = "Monthly"
        
    st.subheader(f"{period_text} Environmental Data")
    
    # Create environmental data visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Solar irradiance chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data["timestamp"],
            y=historical_data["irradiance"],
            name="Solar Irradiance",
            line=dict(color="#FFC107", width=2),
            fill="tozeroy",
            fillcolor="rgba(255, 193, 7, 0.2)"
        ))
        
        fig.update_layout(
            height=300,
            xaxis_title="Time",
            yaxis_title="Irradiance (W/m²)",
            title="Solar Irradiance",
            margin=dict(l=60, r=20, t=50, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Wind speed chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data["timestamp"],
            y=historical_data["wind_speed"],
            name="Wind Speed",
            line=dict(color="#2196F3", width=2),
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.2)"
        ))
        
        fig.update_layout(
            height=300,
            xaxis_title="Time",
            yaxis_title="Wind Speed (m/s)",
            title="Wind Speed",
            margin=dict(l=60, r=20, t=50, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Ambient temperature chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data["timestamp"],
        y=historical_data["temperature"],
        name="Ambient Temperature",
        line=dict(color="#9C27B0", width=2)
    ))
    
    fig.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        title="Ambient Temperature",
        margin=dict(l=60, r=20, t=50, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation analysis
    st.subheader("Parameter Correlations")
    
    # Create correlation dataframe
    corr_data = historical_data[["solar_power", "wind_power", "irradiance", "wind_speed", "temperature"]].copy()
    corr_data.columns = ["Solar Power", "Wind Power", "Irradiance", "Wind Speed", "Temperature"]
    
    # Calculate correlation matrix
    corr_matrix = corr_data.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto"
    )
    
    fig.update_layout(
        height=400,
        title="Correlation Matrix",
        margin=dict(l=60, r=20, t=50, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    st.plotly_chart(fig, use_container_width=True)
