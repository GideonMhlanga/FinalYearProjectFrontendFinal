import streamlit as st
from paho.mqtt import client as mqtt
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import ssl

# Configure the page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Solar-Wind Hybrid Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MQTT Configuration
HIVE_MQTT_BROKER = "4ad81ef75d944ea19791360d57b55735.s1.eu.hivemq.cloud"
HIVE_MQTT_PORT = 8883
HIVE_MQTT_TOPIC = "solar/pzem-017"
HIVE_USER = "hivemq.webclient.1744393295548"
HIVE_PASS = "9BD8C42AbvfdrsFI,!*<"

# Initialize session state
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = {
        "solar": {"voltage": 0, "current": 0, "power": 0, "energy": 0},
        "load": {"current": 0, "power": 0}
    }
if "mqtt_data" not in st.session_state:
    st.session_state.mqtt_data = {
        "wind_power": 0,
        "environmental": {"wind_speed": 0, "temperature": 0},
        "total_generation": 0,
        "net_power": 0
    }
if "historical_data" not in st.session_state:
    st.session_state.historical_data = pd.DataFrame(columns=["timestamp", "power"])
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "last_soc" not in st.session_state:
    st.session_state.last_soc = 0

# MQTT Callback
def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        current_time = datetime.now()
        
        # Update solar and load data
        st.session_state.sensor_data = {
            "solar": payload.get("solar", {"voltage": 0, "current": 0, "power": 0, "energy": 0}),
            "load": payload.get("load", {"current": 0, "power": 0})
        }
        
        # Update wind data if available
        if "wind" in payload:
            st.session_state.mqtt_data.update({
                "wind_power": payload["wind"].get("power", 0),
                "environmental": {
                    "wind_speed": payload["wind"].get("speed", 0),
                    "temperature": payload.get("temperature", 0)
                }
            })
            
            # Calculate totals
            solar_power = st.session_state.sensor_data["solar"]["power"]
            wind_power = st.session_state.mqtt_data["wind_power"]
            load_power = st.session_state.sensor_data["load"]["power"]
            
            st.session_state.mqtt_data["total_generation"] = solar_power + wind_power
            st.session_state.mqtt_data["net_power"] = (solar_power + wind_power) - load_power
            
            # Update historical data
            new_row = pd.DataFrame({
                "timestamp": [current_time],
                "power": [solar_power]
            })
            st.session_state.historical_data = pd.concat(
                [st.session_state.historical_data, new_row],
                ignore_index=True
            ).tail(100)  # Keep last 100 readings
            
    except Exception as e:
        st.error(f"MQTT Data Error: {str(e)}")

# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(HIVE_USER, HIVE_PASS)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.on_message = on_message
client.connect(HIVE_MQTT_BROKER, HIVE_MQTT_PORT, 60)
client.subscribe(HIVE_MQTT_TOPIC, qos=1)
client.loop_start()

from database import db
from utils import format_power, get_status_color
from welcome import show_landing_page

# Theme switching functionality
with st.sidebar:
    st.title("Solar-Wind Monitor")
    theme = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
    st.session_state.theme = theme.lower()
    
    # [Keep your original user auth components here]

# Check login status
if "user" not in st.session_state or st.session_state.user is None:
    show_landing_page()
    st.stop()

# Main dashboard layout
st.title("Hybrid Solar-Wind Monitoring Dashboard")

# Create placeholders for dynamic components
dashboard_placeholder = st.empty()
battery_gauge_placeholder = st.empty()
energy_pie_placeholder = st.empty()
live_chart_placeholder = st.empty()

# Battery data initialization
battery_data = {
    "soc": 65,  # Replace with real data when available
    "voltage": 12.6,
    "temperature": 35,
    "current": 2.1,
    "cycle_count": 42
}

def create_battery_gauge(soc):
    soc_color = get_status_color(soc, {"green": (60, 100), "yellow": (20, 60), "red": (0, 20)})
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
    return fig

def create_energy_pie():
    solar_power = st.session_state.sensor_data["solar"]["power"]
    wind_power = st.session_state.mqtt_data["wind_power"]
    total = solar_power + wind_power
    solar_percent = (solar_power / total * 100) if total > 0 else 100
    wind_percent = (wind_power / total * 100) if total > 0 else 0
    
    fig = px.pie(
        values=[solar_percent, wind_percent],
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
    return fig

def create_live_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=st.session_state.historical_data["timestamp"],
        y=st.session_state.historical_data["power"],
        name="Solar",
        line=dict(color="#FFD700", width=2),
        fill="tozeroy",
        fillcolor="rgba(255, 215, 0, 0.2)"
    ))
    fig.add_trace(go.Scatter(
        x=st.session_state.historical_data["timestamp"],
        y=st.session_state.historical_data["power"] * 0.7,
        name="Load",
        line=dict(color="#FF6347", width=2, dash="dot")
    ))
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
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')
    return fig

while True:
    with dashboard_placeholder.container():
        solar = st.session_state.sensor_data["solar"]
        load = st.session_state.sensor_data["load"]
        
        # Create main sections using columns
        col1, col2, col3 = st.columns([1, 1, 1])

        # Section 1: Power Generation
        with col1:
            st.subheader("Power Generation")
            
            # Solar card
            solar_color = get_status_color(solar["power"], {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
            st.markdown(
                f"""
                <div style="padding: 10px; border-radius: 5px; background-color: {'#e8f4ea' if st.session_state.theme == 'light' else '#1e352f'};">
                    <h3 style="margin:0;">☀️ Solar Power</h3>
                    <h2 style="margin:0; color: {'green' if solar_color == 'green' else 'orange' if solar_color == 'yellow' else 'red'};">
                        {format_power(solar["power"])}
                    </h2>
                    <p style="margin:0;">Voltage: {solar["voltage"]:.1f}V | Current: {solar["current"]:.2f}A</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            # Wind power card
            wind_power = st.session_state.mqtt_data["wind_power"]
            wind_color = get_status_color(wind_power, {"green": (2, float('inf')), "yellow": (0.5, 2), "red": (0, 0.5)})
            st.markdown(
                f"""
                <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#e6f2ff' if st.session_state.theme == 'light' else '#1a2833'};">
                    <h3 style="margin:0;">💨 Wind Power</h3>
                    <h2 style="margin:0; color: {'green' if wind_color == 'green' else 'orange' if wind_color == 'yellow' else 'red'};">
                        {format_power(wind_power)}
                    </h2>
                    <p style="margin:0;">Wind Speed: {st.session_state.mqtt_data["environmental"]["wind_speed"]:.1f} m/s</p>
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
            soc = battery_data["soc"]
           
            if abs(soc - st.session_state.last_soc)>1: 
                fig = create_battery_gauge(soc)
                st.plotly_chart(
                        fig,
                        use_container_width=True,
                        key=f"battery_gauge_{time.time()}"
                )
                st.session_state.last_soc = soc

            st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; margin-top: 10px; background-color: {'#fff0e6' if st.session_state.theme == 'light' else '#33261a'};">
                <h3 style="margin:0;">🔋 Battery Info</h3>
                <p style="margin:0;">Voltage: {battery_data["voltage"]:.1f}V</p>
                <p style="margin:0;">Temperature: {battery_data["temperature"]:.1f}°C</p>
                <p style="margin:0;">Current: {battery_data["current"]:.1f}A</p>
            </div>
            """,
            unsafe_allow_html=True
            )

        # Section 3: Load Monitoring
        with col3:
            st.subheader("Load Monitoring")
            load_color = get_status_color(load["power"], {"green": (0, 3), "yellow": (3, 6), "red": (6, float('inf'))})
            
            st.markdown(
                f"""
                <div style="padding: 10px; border-radius: 5px; background-color: {'#f2e6ff' if st.session_state.theme == 'light' else '#261a33'};">
                    <h3 style="margin:0;">🔌 Current Load</h3>
                    <h2 style="margin:0; color: {'green' if load_color == 'green' else 'orange' if load_color == 'yellow' else 'red'};">
                        {format_power(load["power"])}
                    </h2>
                    <p style="margin:0;">Current: {load["current"]:.2f}A</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            # Net power
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
            st.plotly_chart(
                create_energy_pie(),
                use_container_width=True,
                key=f"energy_pie_{time.time()}"
            )

        # Section 4: Real-time generation chart
        st.subheader("Live Power Generation")
        if not st.session_state.historical_data.empty:
            with live_chart_placeholder.container():
                st.plotly_chart(
                    create_live_chart(),
                    use_container_width=True,
                    key=f"live_chasrt_{time.time()}"
                )
        else:
            st.info("Waiting for data... Chart will appear soon.")

        # Footer
        st.divider()
        st.caption("This dashboard provides real-time monitoring of the hybrid solar-wind power system.")

    time.sleep(1)