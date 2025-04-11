import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import ssl
from database import db
from utils import format_power, get_status_color
from welcome import show_landing_page

# MQTT Configuration (Replace with your HiveMQ details)
MQTT_BROKER = "4ad81ef75d944ea19791360d57b55735.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "solar/pzem-017"
MQTT_USER = "hivemq.webclient.1744393295548"
MQTT_PASS = "9BD8C42AbvfdrsFI,!*<"

# Configure the page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Solar-Wind Hybrid Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for MQTT data
if "mqtt_data" not in st.session_state:
    st.session_state.mqtt_data = {
        "solar_power": 0,
        "voltage": 0,
        "current": 0,
        "energy": 0,
        "environmental": {
            "irradiance": 0,
            "temperature": 25,
            "wind_speed": 0
        },
        "battery": {
            "soc": 50,
            "voltage": 12.6,
            "current": 0,
            "temperature": 25,
            "cycle_count": 10
        },
        "load": 0,
        "total_generation": 0,
        "net_power": 0
    }
if "historical_data" not in st.session_state:
    st.session_state.historical_data = pd.DataFrame(columns=["timestamp", "power", "voltage", "current"])

# MQTT Callback Function
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        new_data = {
            "solar_power": payload["data"]["power"],
            "voltage": payload["data"]["voltage"],
            "current": payload["data"]["current"],
            "energy": payload["data"]["energy"],
            "environmental": {
                "irradiance": payload["data"].get("irradiance", 800),
                "temperature": payload["data"].get("temperature", 25)
            },
            "load": payload["data"]["power"] * 0.7,  # Example calculation
            "total_generation": payload["data"]["power"],
            "net_power": payload["data"]["power"] * 0.3
        }
        
        # Update session state
        st.session_state.mqtt_data = new_data
        
        # Update historical data
        new_row = {
            "timestamp": datetime.now(),
            "power": payload["data"]["power"],
            "voltage": payload["data"]["voltage"],
            "current": payload["data"]["current"]
        }
        st.session_state.historical_data = pd.concat([
            st.session_state.historical_data,
            pd.DataFrame([new_row])
        ]).tail(1000)  # Keep last 1000 readings
        
    except Exception as e:
        st.error(f"MQTT Data Processing Error: {str(e)}")

# Initialize MQTT Client
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set(
    ca_certs=None,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS
)
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC, qos=1)
client.loop_start()

# Configure server settings
import os
if __name__ == '__main__':
    os.environ['STREAMLIT_SERVER_PORT'] = '5000'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'

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

# Display last update time
if "last_update" in st.session_state:
    st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Create main sections using columns
col1, col2, col3 = st.columns([1, 1, 1])

# Section 1: Current Power Generation
with col1:
    st.subheader("Power Generation")
    
    # Solar power card
    solar_power = st.session_state.mqtt_data["solar_power"]
    solar_color = get_status_color(solar_power, {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {'#e8f4ea' if st.session_state.theme == 'light' else '#1e352f'};">
            <h3 style="margin:0;">☀️ Solar Power</h3>
            <h2 style="margin:0; color: {'green' if solar_color == 'green' else 'orange' if solar_color == 'yellow' else 'red'};">
                {format_power(solar_power)}
            </h2>
            <p style="margin:0;">Irradiance: {st.session_state.mqtt_data['environmental']['irradiance']:.1f} W/m²</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Wind power card (placeholder - modify if you have wind data)
    wind_power = st.session_state.mqtt_data.get("wind_power", 0)
    wind_color = get_status_color(wind_power, {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#e6f2ff' if st.session_state.theme == 'light' else '#1a2833'};">
            <h3 style="margin:0;">💨 Wind Power</h3>
            <h2 style="margin:0; color: {'green' if wind_color == 'green' else 'orange' if wind_color == 'yellow' else 'red'};">
                {format_power(wind_power)}
            </h2>
            <p style="margin:0;">Wind Speed: {st.session_state.mqtt_data['environmental']['wind_speed']:.1f} m/s</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Total generation card
    total_power = st.session_state.mqtt_data["total_generation"]
    total_color = get_status_color(total_power, {"green": (4, float('inf')), "yellow": (1, 4), "red": (0, 1)})
    
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#f0f0f0' if st.session_state.theme == 'light' else '#2d2d2d'};">
            <h3 style="margin:0;">⚡ Total Generation</h3>
            <h2 style="margin:0; color: {'green' if total_color == 'green' else 'orange' if total_color == 'yellow' else 'red'};">
                {format_power(total_power)}
            </h2>
            <p style="margin:0;">Temperature: {st.session_state.mqtt_data['environmental']['temperature']:.1f}°C</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Section 2: Battery Status
with col2:
    st.subheader("Battery Status")
    
    # Battery state of charge
    battery = st.session_state.mqtt_data["battery"]
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
    load = st.session_state.mqtt_data["load"]
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
    net_power = st.session_state.mqtt_data["net_power"]
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
    
    # Create pie chart for energy sources (modify if you have wind data)
    fig = px.pie(
        values=[100, 0],  # 100% solar, 0% wind (adjust as needed)
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

if not st.session_state.historical_data.empty:
    # Create time series plot for power generation
    fig = go.Figure()
    
    # Add solar power line
    fig.add_trace(go.Scatter(
        x=st.session_state.historical_data["timestamp"],
        y=st.session_state.historical_data["power"],
        name="Solar",
        line=dict(color="#FFD700", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 215, 0, 0.2)"
    ))
    
    # Add load line (calculated as 70% of power)
    fig.add_trace(go.Scatter(
        x=st.session_state.historical_data["timestamp"],
        y=st.session_state.historical_data["power"] * 0.7,
        name="Load",
        line=dict(color="#FF6347", width=2, dash="dot")
    ))
    
    # Update layout
    fig.update_layout(
        height=400,
        xaxis_title="Time",
        yaxis_title="Power (W)",
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
    st.info("Waiting for data... Chart will appear soon.")

# Footer information
st.divider()
st.caption("This dashboard provides real-time monitoring of the hybrid solar-wind power system. Navigate to other pages using the sidebar for more detailed information.")