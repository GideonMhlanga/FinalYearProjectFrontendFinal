import streamlit as st
# Configure the page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Solar-Wind Hybrid Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure server settings
import os
if __name__ == '__main__':
    os.environ['STREAMLIT_SERVER_PORT'] = '5000'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os

# Import database and utilities
from database import db
from data_generator import data_generator
from utils import format_power, get_status_color
from welcome import show_landing_page

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Initialize database tables and ensure they exist
try:
    # This will create all tables if they don't exist
    # The database is initialized in the DatabaseManager constructor
    st.sidebar.success("Database connected successfully!")
    
    # Log application startup
    db.add_system_log(
        log_type="info",
        message="Application started",
        details={"version": "1.0.0", "database_url": os.environ.get("DATABASE_URL", "").split("@")[1] if "@" in os.environ.get("DATABASE_URL", "") else "local"}
    )
except Exception as e:
    st.sidebar.error(f"Database connection error: {str(e)}")
    st.stop()

# Theme switching functionality

# Add theme toggle in sidebar
with st.sidebar:
    st.title("Solar-Wind Monitor")
    
    # Theme selector
    theme = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
    st.session_state.theme = theme.lower()
    
    st.divider()
    
    # User info
    if "user" not in st.session_state:
        st.session_state.user = None
        st.session_state.role = None
    
    if st.session_state.user:
        st.success(f"Logged in as: {st.session_state.user} ({st.session_state.role})")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
    
    st.divider()
    st.caption("© 2025 Zimbabwe Renewable Energy")

# Function to refresh data
def refresh_data():
    return data_generator.generate_current_data()

# Check if user is logged in, if not, show the landing page
if "user" not in st.session_state or st.session_state.user is None:
    show_landing_page()
    st.stop()  # Stop execution if not logged in

# Main dashboard layout for logged-in users
st.title("Hybrid Solar-Wind Monitoring Dashboard")

# Refresh interval
refresh_interval = st.sidebar.slider("Auto-refresh interval (sec)", 5, 60, 10)

# Auto-refresh checkbox
auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=True)

# Manual refresh button
if st.sidebar.button("Refresh Now"):
    st.session_state.last_refresh_time = datetime.now()
    st.session_state.current_data = refresh_data()

# Check if we need to refresh based on the time elapsed
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()
    st.session_state.current_data = refresh_data()
else:
    elapsed = (datetime.now() - st.session_state.last_refresh_time).total_seconds()
    if auto_refresh and elapsed >= refresh_interval:
        st.session_state.last_refresh_time = datetime.now()
        st.session_state.current_data = refresh_data()

# Get current data
current_data = st.session_state.current_data
last_refresh = st.session_state.last_refresh_time

# Display last refresh time
st.caption(f"Last updated: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Get system anomalies
try:
    anomaly_data = data_generator.get_system_anomalies("day")
    anomaly_summary = anomaly_data["summary"]
    anomalies = anomaly_data["anomalies"]
    
    # If we have anomalies, show them in an expander
    if anomaly_summary["total"] > 0:
        system_status = "Critical" if anomaly_summary["severe"] > 0 else \
                        "Warning" if anomaly_summary["moderate"] > 0 else \
                        "Caution" if anomaly_summary["mild"] > 0 else "Normal"
        
        status_icon = "🔴" if system_status == "Critical" else \
                      "🟠" if system_status == "Warning" else \
                      "🟡" if system_status == "Caution" else "🟢"
        
        with st.expander(f"{status_icon} {system_status}: Anomaly Alerts ({anomaly_summary['total']})", expanded=True):
            # Add a quick summary
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold; color: red;">{anomaly_summary['severe']} severe</span> | 
                <span style="font-weight: bold; color: orange;">{anomaly_summary['moderate']} moderate</span> | 
                <span style="font-weight: bold; color: #CCB800;">{anomaly_summary['mild']} mild</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Show the most severe anomalies first
            shown_anomalies = 0
            max_anomalies_to_show = 3
            
            # Show severe anomalies
            for category, anomaly_list in anomalies.items():
                if shown_anomalies >= max_anomalies_to_show:
                    break
                    
                severe_anomalies = [a for a in anomaly_list if a["severity"] == "severe"]
                for anomaly in severe_anomalies:
                    if shown_anomalies >= max_anomalies_to_show:
                        break
                        
                    st.error(f"⚠️ **{category.replace('_', ' ').title()}**: {anomaly['message']}")
                    shown_anomalies += 1
            
            # Show moderate anomalies if we have space
            if shown_anomalies < max_anomalies_to_show:
                for category, anomaly_list in anomalies.items():
                    if shown_anomalies >= max_anomalies_to_show:
                        break
                        
                    moderate_anomalies = [a for a in anomaly_list if a["severity"] == "moderate"]
                    for anomaly in moderate_anomalies:
                        if shown_anomalies >= max_anomalies_to_show:
                            break
                            
                        st.warning(f"⚠️ **{category.replace('_', ' ').title()}**: {anomaly['message']}")
                        shown_anomalies += 1
            
            # If we still have space, show mild anomalies (but just count them by category)
            if shown_anomalies < max_anomalies_to_show:
                mild_categories = {}
                for category, anomaly_list in anomalies.items():
                    mild_anomalies = [a for a in anomaly_list if a["severity"] == "mild"]
                    if mild_anomalies:
                        if category not in mild_categories:
                            mild_categories[category] = 0
                        mild_categories[category] += len(mild_anomalies)
                
                for category, count in mild_categories.items():
                    if shown_anomalies >= max_anomalies_to_show:
                        break
                        
                    st.info(f"ℹ️ **{category.replace('_', ' ').title()}**: {count} mild anomalies detected")
                    shown_anomalies += 1
            
            # If there are more anomalies than we can show, add a link to the anomaly page
            if anomaly_summary["total"] > max_anomalies_to_show:
                st.markdown(f"[View all {anomaly_summary['total']} anomalies on the Anomaly Detection page →](/Anomaly_Detection)")
except Exception as e:
    # Fall back to the original alerts if anomaly detection fails
    st.error(f"Error detecting anomalies: {str(e)}")
    
    # Display original alert messages if any
    alerts = current_data.get("alerts", [])
    if alerts:
        with st.expander(f"System Alerts ({len(alerts)})", expanded=True):
            for alert in alerts:
                severity = alert["severity"]
                if severity == "high":
                    st.error(f"⚠️ {alert['component'].title()}: {alert['message']}")
                elif severity == "medium":
                    st.warning(f"⚠️ {alert['component'].title()}: {alert['message']}")
                else:
                    st.info(f"ℹ️ {alert['component'].title()}: {alert['message']}")

# Create main sections using columns
col1, col2, col3 = st.columns([1, 1, 1])

# Section 1: Current Power Generation
with col1:
    st.subheader("Power Generation")
    
    # Solar power card
    solar_power = current_data["solar_power"]
    solar_color = get_status_color(solar_power, {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {'#e8f4ea' if st.session_state.theme == 'light' else '#1e352f'};">
            <h3 style="margin:0;">☀️ Solar Power</h3>
            <h2 style="margin:0; color: {'green' if solar_color == 'green' else 'orange' if solar_color == 'yellow' else 'red'};">
                {format_power(solar_power)}
            </h2>
            <p style="margin:0;">Irradiance: {current_data['environmental']['irradiance']:.1f} W/m²</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Wind power card
    wind_power = current_data["wind_power"]
    wind_color = get_status_color(wind_power, {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#e6f2ff' if st.session_state.theme == 'light' else '#1a2833'};">
            <h3 style="margin:0;">💨 Wind Power</h3>
            <h2 style="margin:0; color: {'green' if wind_color == 'green' else 'orange' if wind_color == 'yellow' else 'red'};">
                {format_power(wind_power)}
            </h2>
            <p style="margin:0;">Wind Speed: {current_data['environmental']['wind_speed']:.1f} m/s</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Total generation card
    total_power = current_data["total_generation"]
    total_color = get_status_color(total_power, {"green": (4, float('inf')), "yellow": (1, 4), "red": (0, 1)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#f0f0f0' if st.session_state.theme == 'light' else '#2d2d2d'};">
            <h3 style="margin:0;">⚡ Total Generation</h3>
            <h2 style="margin:0; color: {'green' if total_color == 'green' else 'orange' if total_color == 'yellow' else 'red'};">
                {format_power(total_power)}
            </h2>
            <p style="margin:0;">Temperature: {current_data['environmental']['temperature']:.1f}°C</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Section 2: Battery Status
with col2:
    st.subheader("Battery Status")
    
    # Battery state of charge
    battery = current_data["battery"]
    soc = battery["soc"]
    soc_color = get_status_color(soc, {"green": (60, 100), "yellow": (20, 60), "red": (0, 20)})
    
    # Create gauge chart for battery SOC
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=soc,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "State of Charge"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "green" if soc_color == "green" else "orange" if soc_color == "yellow" else "red"},
            'steps': [
                {'range': [0, 20], 'color': "#ffcccc"},
                {'range': [20, 60], 'color': "#ffffcc"},
                {'range': [60, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': soc
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Battery details
    col2a, col2b = st.columns(2)
    
    with col2a:
        st.metric("Voltage", f"{battery['voltage']:.1f}V")
        st.metric("Temperature", f"{battery['temperature']:.1f}°C")
    
    with col2b:
        current_val = battery['current']
        current_label = f"{abs(current_val):.2f}A"
        if current_val > 0:
            st.metric("Current", f"{current_label} ↑", "Charging")
        else:
            st.metric("Current", f"{current_label} ↓", "Discharging")
        
        st.metric("Cycle Count", f"{battery['cycle_count']}")

# Section 3: Current Load & Energy Balance
with col3:
    st.subheader("Load & Energy Balance")
    
    # Current load
    load = current_data["load"]
    load_color = get_status_color(load, {"green": (0, 3), "yellow": (3, 6), "red": (6, float('inf'))})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {'#f2e6ff' if st.session_state.theme == 'light' else '#261a33'};">
            <h3 style="margin:0;">🔌 Current Load</h3>
            <h2 style="margin:0; color: {'green' if load_color == 'green' else 'orange' if load_color == 'yellow' else 'red'};">
                {format_power(load)}
            </h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Net power (generation - load)
    net_power = current_data["net_power"]
    net_status = "Surplus" if net_power > 0 else "Deficit"
    net_color = "green" if net_power > 0 else "red"
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#e6ffe6' if net_power > 0 else '#ffe6e6'};">
            <h3 style="margin:0;">⚖️ Power Balance</h3>
            <h2 style="margin:0; color: {net_color};">
                {format_power(abs(net_power))}
            </h2>
            <p style="margin:0;">{net_status}: {'+' if net_power > 0 else '-'}{format_power(abs(net_power))}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Energy contribution
    st.subheader("Energy Source")
    
    # Calculate energy summary
    energy_summary = data_generator.get_energy_summary()
    
    # Create pie chart for energy sources
    fig = px.pie(
        values=[energy_summary["solar_percentage"], energy_summary["wind_percentage"]],
        names=["Solar", "Wind"],
        color_discrete_sequence=["#FFD700", "#4682B4"],
        hole=0.4
    )
    
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Section 4: Real-time generation chart
st.subheader("Live Power Generation")

# Get historical data
historical_data = data_generator.get_historical_data(timeframe="day")

if not historical_data.empty:
    # Create time series plot for power generation
    fig = go.Figure()
    
    # Add solar power line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamps"],
        y=historical_data["solar_power"],
        name="Solar",
        line=dict(color="#FFD700", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 215, 0, 0.2)"
    ))
    
    # Add wind power line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamps"],
        y=historical_data["wind_power"],
        name="Wind",
        line=dict(color="#4682B4", width=2),
        fill="tozeroy",
        fillcolor="rgba(70, 130, 180, 0.2)"
    ))
    
    # Add load line
    fig.add_trace(go.Scatter(
        x=historical_data["timestamps"],
        y=historical_data["load"],
        name="Load",
        line=dict(color="#FF6347", width=2, dash="dot")
    ))
    
    # Update layout
    fig.update_layout(
        height=400,
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
else:
    st.info("Collecting data... Chart will appear soon.")

# Footer information
st.divider()
st.caption("This dashboard provides real-time monitoring of the hybrid solar-wind power system. Navigate to other pages using the sidebar for more detailed information.")
