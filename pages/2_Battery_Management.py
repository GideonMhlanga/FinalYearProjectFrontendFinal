import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from data_generator import data_generator
from utils import get_status_color

# Configure the page
st.set_page_config(
    page_title="Battery Management | Solar-Wind Hybrid Monitor",
    page_icon="🔋",
    layout="wide"
)

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Title and description
st.title("Battery Management")
st.write("Monitor and manage your battery system performance and health")

# Function to refresh data
def refresh_data():
    return data_generator.generate_current_data()

# Auto-refresh checkbox
auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=True)

# Refresh interval
refresh_interval = st.sidebar.slider("Auto-refresh interval (sec)", 5, 60, 15)

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
battery_data = current_data["battery"]
last_refresh = st.session_state.last_refresh_time

# Display last refresh time
st.caption(f"Last updated: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Create two columns for the main content
col1, col2 = st.columns([2, 1])

# Left column - Battery SOC and key metrics
with col1:
    # Create a larger SOC gauge
    soc = battery_data["soc"]
    soc_color = get_status_color(soc, {"green": (60, 100), "yellow": (20, 60), "red": (0, 20)})
    
    # Create gauge chart for battery SOC
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=soc,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Battery State of Charge (SOC)", 'font': {'size': 24}},
        delta={'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "green" if soc_color == "green" else "orange" if soc_color == "yellow" else "red"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
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
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA", size=16)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Battery status indicators
    st.subheader("Current Battery Status")
    
    status_cols = st.columns(4)
    
    # Voltage
    voltage = battery_data["voltage"]
    voltage_color = get_status_color(voltage, {"green": (45, 51), "yellow": (42, 45), "red": (0, 42)})
    
    with status_cols[0]:
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {'#e6f2ff' if st.session_state.theme == 'light' else '#1a2833'};">
                <h3 style="margin:0;">Voltage</h3>
                <h2 style="margin:0; color: {'green' if voltage_color == 'green' else 'orange' if voltage_color == 'yellow' else 'red'};">
                    {voltage:.2f} V
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Current
    current = battery_data["current"]
    current_status = "Charging" if current > 0 else "Discharging"
    current_color = "green" if current > 0 else "red"
    
    with status_cols[1]:
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {'#e6ffe6' if current > 0 else '#ffe6e6'};">
                <h3 style="margin:0;">Current</h3>
                <h2 style="margin:0; color: {current_color};">
                    {abs(current):.2f} A {current_status}
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Temperature
    temp = battery_data["temperature"]
    temp_color = get_status_color(temp, {"green": (15, 30), "yellow": (30, 40), "red": (40, 100)})
    
    with status_cols[2]:
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {'#f2e6ff' if st.session_state.theme == 'light' else '#261a33'};">
                <h3 style="margin:0;">Temperature</h3>
                <h2 style="margin:0; color: {'green' if temp_color == 'green' else 'orange' if temp_color == 'yellow' else 'red'};">
                    {temp:.1f} °C
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Health
    health = battery_data["health_pct"]
    health_color = get_status_color(health, {"green": (80, 100), "yellow": (60, 80), "red": (0, 60)})
    
    with status_cols[3]:
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {'#e8f4ea' if st.session_state.theme == 'light' else '#1e352f'};">
                <h3 style="margin:0;">Health</h3>
                <h2 style="margin:0; color: {'green' if health_color == 'green' else 'orange' if health_color == 'yellow' else 'red'};">
                    {health:.1f}%
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Battery charging/discharging history
    st.subheader("Battery Current History")
    
    # Get historical data
    historical_data = data_generator.get_historical_data(timeframe="day")
    
    if not historical_data.empty:
        # Create time series plot for battery current
        fig = go.Figure()
        
        # Add current line
        fig.add_trace(go.Scatter(
            x=historical_data["timestamps"],
            y=historical_data["battery_current"],
            name="Current",
            line=dict(color="#4CAF50", width=2),
            fill="tozeroy",
            fillcolor="rgba(76, 175, 80, 0.2)"
        ))
        
        # Add zero line for reference
        fig.add_shape(
            type="line",
            x0=historical_data["timestamps"].iloc[0],
            y0=0,
            x1=historical_data["timestamps"].iloc[-1],
            y1=0,
            line=dict(color="gray", width=2, dash="dash")
        )
        
        # Update layout
        fig.update_layout(
            height=300,
            xaxis_title="Time",
            yaxis_title="Current (A)",
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
        
        # Add annotations
        fig.add_annotation(
            x=historical_data["timestamps"].iloc[len(historical_data) // 2],
            y=2,
            text="Charging ↑",
            showarrow=False,
            font=dict(size=14, color="green")
        )
        
        fig.add_annotation(
            x=historical_data["timestamps"].iloc[len(historical_data) // 2],
            y=-2,
            text="Discharging ↓",
            showarrow=False,
            font=dict(size=14, color="red")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough historical data available yet. Please wait while data is being collected.")

# Right column - Battery Health and Additional Info
with col2:
    # Battery health gauge
    st.subheader("Battery Health")
    
    health = battery_data["health_pct"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Battery Health"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "green" if health >= 80 else "orange" if health >= 60 else "red"},
            'steps': [
                {'range': [0, 60], 'color': "#ffcccc"},
                {'range': [60, 80], 'color': "#ffffcc"},
                {'range': [80, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': health
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
    
    # Battery specs
    st.subheader("Battery Specifications")
    
    # Check if we have saved battery specs in session state
    if "battery_specs" not in st.session_state:
        # Initialize with default values
        st.session_state.battery_specs = {
            "Type": "Lithium Iron Phosphate (LiFePO4)",
            "Capacity": "20 kWh",
            "Nominal Voltage": "48V",
            "Max Charging Rate": "5 kW",
            "Expected Lifespan": "~3000 cycles",
            "Installation Date": "2023-01-15"
        }
    
    # Add real-time data
    display_specs = st.session_state.battery_specs.copy()
    display_specs["Cycle Count"] = f"{battery_data['cycle_count']}"
    
    # Create two columns for display and edit mode
    spec_col1, spec_col2 = st.columns([3, 1])
    
    with spec_col1:
        # Display specs as a table
        df_specs = pd.DataFrame(list(display_specs.items()), columns=["Specification", "Value"])
        st.table(df_specs)
    
    with spec_col2:
        # Edit button
        if st.button("Edit Specifications", key="edit_battery_specs"):
            st.session_state.editing_battery_specs = True
    
    # Edit mode
    if st.session_state.get("editing_battery_specs", False):
        st.subheader("Edit Battery Specifications")
        
        with st.form("battery_specs_form"):
            new_specs = {}
            new_specs["Type"] = st.text_input("Battery Type", value=st.session_state.battery_specs["Type"])
            new_specs["Capacity"] = st.text_input("Capacity (kWh)", value=st.session_state.battery_specs["Capacity"])
            new_specs["Nominal Voltage"] = st.text_input("Nominal Voltage", value=st.session_state.battery_specs["Nominal Voltage"])
            new_specs["Max Charging Rate"] = st.text_input("Max Charging Rate", value=st.session_state.battery_specs["Max Charging Rate"])
            new_specs["Expected Lifespan"] = st.text_input("Expected Lifespan", value=st.session_state.battery_specs["Expected Lifespan"])
            new_specs["Installation Date"] = st.text_input("Installation Date", value=st.session_state.battery_specs["Installation Date"])
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Save Changes")
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if submit:
                st.session_state.battery_specs = new_specs
                st.session_state.editing_battery_specs = False
                st.success("Battery specifications updated successfully!")
                st.rerun()
            
            if cancel:
                st.session_state.editing_battery_specs = False
                st.rerun()
    
    # Battery maintenance tips
    st.subheader("Maintenance Recommendations")
    
    with st.expander("Battery Care Tips", expanded=True):
        st.markdown("""
        - Keep battery temperature between 15-30°C for optimal performance
        - Avoid frequent deep discharges below 20% SOC
        - Periodic checks for loose connections
        - Monitor for unusual temperature increases
        - Schedule full system inspection every 6 months
        """)
    
    # Next maintenance
    days_to_maintenance = 45
    st.info(f"Next scheduled maintenance: {days_to_maintenance} days")

# Advanced Battery Analytics Section
st.subheader("Advanced Battery Analytics")

# Create tabs for different analytics views
tab1, tab2 = st.tabs(["Performance Metrics", "Charge-Discharge Cycles"])

# Tab 1: Performance Metrics
with tab1:
    if not historical_data.empty:
        # Calculate battery efficiency
        # For demo purposes, we're using a simulated calculation
        charging_periods = historical_data[historical_data["battery_current"] > 0]
        discharging_periods = historical_data[historical_data["battery_current"] < 0]
        
        if not charging_periods.empty and not discharging_periods.empty:
            # Calculate energy in/out
            time_factor = 1/60  # each data point is 1 minute = 1/60 hour
            energy_in = (charging_periods["battery_current"] * charging_periods["battery_voltage"]).sum() * time_factor
            energy_out = abs((discharging_periods["battery_current"] * discharging_periods["battery_voltage"]).sum()) * time_factor
            
            if energy_in > 0:
                efficiency = (energy_out / energy_in) * 100
            else:
                efficiency = 0
        else:
            efficiency = 90  # Default for demonstration
        
        # Display metrics
        metric_cols = st.columns(3)
        
        with metric_cols[0]:
            st.metric("Round-Trip Efficiency", f"{efficiency:.1f}%")
        
        with metric_cols[1]:
            # Calculate depth of discharge (DoD)
            min_soc = historical_data["battery_soc"].min()
            max_dod = 100 - min_soc
            st.metric("Max Depth of Discharge", f"{max_dod:.1f}%")
        
        with metric_cols[2]:
            # Average temperature
            avg_temp = historical_data["battery_temperature"].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        # Plot voltage vs SOC relationship
        st.subheader("Voltage vs. State of Charge")
        
        fig = px.scatter(
            historical_data, 
            x="battery_soc", 
            y="battery_voltage",
            color="battery_current",
            color_continuous_scale="RdYlGn",
            labels={"battery_soc": "State of Charge (%)", "battery_voltage": "Voltage (V)", "battery_current": "Current (A)"}
        )
        
        fig.update_layout(
            height=400,
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
        st.info("Not enough historical data available yet for performance metrics.")

# Tab 2: Charge-Discharge Cycles
with tab2:
    if not historical_data.empty:
        # Identify charge-discharge cycles
        # For this demo, we'll create a simplified cycle visualization
        
        # Create a sign change column to identify transitions between charging and discharging
        historical_data["current_sign"] = np.sign(historical_data["battery_current"])
        historical_data["sign_change"] = historical_data["current_sign"].diff().fillna(0) != 0
        
        # Get cycle transition points
        cycle_transitions = historical_data[historical_data["sign_change"]].copy()
        
        if len(cycle_transitions) > 0:
            # Plot cycles
            st.subheader("Charge-Discharge Cycles")
            
            fig = go.Figure()
            
            # Add SOC line
            fig.add_trace(go.Scatter(
                x=historical_data["timestamps"],
                y=historical_data["battery_soc"],
                name="State of Charge",
                line=dict(color="#4CAF50", width=2)
            ))
            
            # Add current line on secondary y-axis
            fig.add_trace(go.Scatter(
                x=historical_data["timestamps"],
                y=historical_data["battery_current"],
                name="Current",
                line=dict(color="#FF9800", width=2, dash="dot"),
                yaxis="y2"
            ))
            
            # Add cycle transition markers
            fig.add_trace(go.Scatter(
                x=cycle_transitions["timestamps"],
                y=cycle_transitions["battery_soc"],
                mode="markers",
                marker=dict(size=10, color="red", symbol="circle"),
                name="Cycle Transitions"
            ))
            
            # Update layout with secondary y-axis
            fig.update_layout(
                height=400,
                xaxis_title="Time",
                yaxis_title="State of Charge (%)",
                yaxis2=dict(
                    title="Current (A)",
                    title_font=dict(color="#FF9800"),
                    tickfont=dict(color="#FF9800"),
                    overlaying="y",
                    side="right"
                ),
                margin=dict(l=60, r=60, t=30, b=60),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
            
            # Cycle statistics
            st.subheader("Cycle Statistics")
            
            # Count charge and discharge cycles
            charge_cycles = len(cycle_transitions[cycle_transitions["current_sign"] > 0])
            discharge_cycles = len(cycle_transitions[cycle_transitions["current_sign"] < 0])
            
            cycle_cols = st.columns(3)
            
            with cycle_cols[0]:
                st.metric("Complete Cycles Today", f"{min(charge_cycles, discharge_cycles)}")
            
            with cycle_cols[1]:
                st.metric("Charging Events", f"{charge_cycles}")
            
            with cycle_cols[2]:
                st.metric("Discharging Events", f"{discharge_cycles}")
            
            # Display average cycle depth
            cycle_depths = []
            current_min = 100
            current_max = 0
            
            for _, row in historical_data.iterrows():
                soc = row["battery_soc"]
                current_min = min(current_min, soc)
                current_max = max(current_max, soc)
                
                if row["sign_change"] and row["current_sign"] < 0:  # Transition to discharge
                    cycle_depths.append(current_max - current_min)
                    current_min = soc
                    current_max = soc
            
            if cycle_depths:
                avg_cycle_depth = sum(cycle_depths) / len(cycle_depths)
                st.metric("Average Cycle Depth", f"{avg_cycle_depth:.1f}%")
        else:
            st.info("No complete charge-discharge cycles detected in the current data.")
    else:
        st.info("Not enough historical data available yet for cycle analysis.")
