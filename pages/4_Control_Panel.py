import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from data_generator import data_generator
from utils import format_power, get_status_color

# Configure the page
st.set_page_config(
    page_title="Control Panel | Solar-Wind Hybrid Monitor",
    page_icon="🎛️",
    layout="wide"
)

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Title and description
st.title("System Control Panel")
st.write("Manage and control your hybrid solar-wind system settings and operations")

# Check if user is logged in and has admin privileges
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please login from the main dashboard to access the control panel.")
    st.stop()
elif st.session_state.role != "admin":
    st.error("You need administrator privileges to access this page.")
    st.stop()

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
last_refresh = st.session_state.last_refresh_time

# Get current settings
if "settings" not in st.session_state:
    st.session_state.settings = data_generator.get_settings()

# Display last refresh time
st.caption(f"Last updated: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Create tabs for different control sections
tab1, tab2, tab3, tab4 = st.tabs(["System Mode", "Load Management", "System Status", "Maintenance"])

# Tab 1: System Mode
with tab1:
    st.subheader("System Operation Mode")
    
    # Current status overview
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Solar-Wind priority toggle
        solar_priority = st.radio(
            "Generation Priority",
            ["Solar Priority", "Wind Priority", "Balanced/Auto"],
            index=0 if st.session_state.settings["solar_priority"] else 2
        )
        
        # Battery discharge limit
        max_discharge = st.slider(
            "Max Battery Discharge Level (%)",
            0, 90, st.session_state.settings["max_battery_discharge"],
            help="Battery will not discharge below this level unless critical loads are enabled"
        )
        
        # Critical loads only mode
        critical_loads_only = st.checkbox(
            "Critical Loads Only Mode",
            value=st.session_state.settings["critical_loads_only"],
            help="When enabled, only critical loads will be powered"
        )
        
        # Apply changes button
        if st.button("Apply Settings"):
            new_settings = {
                "solar_priority": solar_priority == "Solar Priority",
                "max_battery_discharge": max_discharge,
                "critical_loads_only": critical_loads_only
            }
            st.session_state.settings = data_generator.update_settings(new_settings)
            st.success("Settings updated successfully!")
    
    with col2:
        # System mode visualization
        st.subheader("Current System Mode")
        
        # Calculate current power flow
        solar_power = current_data["solar_power"]
        wind_power = current_data["wind_power"]
        total_generation = current_data["total_generation"]
        load = current_data["load"]
        battery = current_data["battery"]
        net_power = current_data["net_power"]
        
        # Create Sankey diagram for power flow
        label_names = ["Solar", "Wind", "Battery", "Loads"]
        
        # Calculate the values for the Sankey diagram
        # Assumes: positive net_power charges battery, negative draws from battery
        if net_power > 0:
            # Excess power flows to battery
            solar_to_loads = min(solar_power, load)
            wind_to_loads = min(wind_power, max(0, load - solar_to_loads))
            solar_to_battery = max(0, solar_power - solar_to_loads)
            wind_to_battery = max(0, wind_power - wind_to_loads)
            battery_to_loads = 0
        else:
            # Battery supplements power
            solar_to_loads = solar_power
            wind_to_loads = wind_power
            solar_to_battery = 0
            wind_to_battery = 0
            battery_to_loads = abs(net_power)
        
        # Create links for the Sankey diagram
        sources = [0, 0, 1, 1, 2]  # Solar, Solar, Wind, Wind, Battery
        targets = [3, 2, 3, 2, 3]  # Loads, Battery, Loads, Battery, Loads
        values = [solar_to_loads, solar_to_battery, wind_to_loads, wind_to_battery, battery_to_loads]
        
        # Remove links with zero value
        non_zero_links = [(s, t, v) for s, t, v in zip(sources, targets, values) if v > 0.01]
        if non_zero_links:
            sources, targets, values = zip(*non_zero_links)
        else:
            sources, targets, values = [0], [3], [0.01]  # Prevent empty diagram
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=label_names,
                color=["#FFD700", "#4682B4", "#32CD32", "#FF6347"]
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=["rgba(255, 215, 0, 0.4)", "rgba(255, 215, 0, 0.4)", 
                       "rgba(70, 130, 180, 0.4)", "rgba(70, 130, 180, 0.4)",
                       "rgba(50, 205, 50, 0.4)"]
            )
        )])
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=5, b=5),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA", size=14)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Power flow summary
        st.markdown("#### Power Flow Summary")
        
        if net_power > 0:
            st.info(f"System is generating excess power ({format_power(net_power)}), charging battery")
        else:
            st.warning(f"System is drawing from battery ({format_power(abs(net_power))}) to supplement load")
        
        st.markdown(f"""
        - **Total Generation:** {format_power(total_generation)}
        - **Total Load:** {format_power(load)}
        - **Battery State:** {"Charging" if battery["charging"] else "Discharging"} ({battery["soc"]:.1f}% SOC)
        """)

# Tab 2: Load Management
with tab2:
    st.subheader("Load Management")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Load Priority Settings")
        
        # Sample load categories with sliders for demonstration
        st.markdown("Adjust priority levels for different load categories:")
        
        critical_priority = st.slider("Critical Loads (medical, essential lighting)", 80, 100, 100)
        primary_priority = st.slider("Primary Loads (refrigeration, water pumping)", 50, 90, 80)
        secondary_priority = st.slider("Secondary Loads (general appliances)", 20, 70, 50)
        tertiary_priority = st.slider("Tertiary Loads (optional, entertainment)", 0, 40, 20)
        
        # Load shedding threshold
        load_shed_threshold = st.slider(
            "Load Shedding Battery Threshold (%)",
            10, 50, 25,
            help="When battery drops below this level, automatic load shedding will activate"
        )
        
        if st.button("Update Load Priorities"):
            st.success("Load priorities updated successfully!")
    
    with col2:
        st.markdown("### Scheduled Load Management")
        
        # Time-based load scheduling
        st.markdown("Configure scheduled load operations:")
        
        schedule_enabled = st.checkbox("Enable scheduled load management", value=True)
        
        if schedule_enabled:
            # Sample schedules for demonstration
            schedules = [
                {"id": 1, "load": "Irrigation Pump", "start": "06:00", "end": "08:00", "days": "Mon, Wed, Fri", "enabled": True},
                {"id": 2, "load": "Water Heater", "start": "18:00", "end": "20:00", "days": "Daily", "enabled": True},
                {"id": 3, "load": "AC System", "start": "13:00", "end": "16:00", "days": "Weekdays", "enabled": False},
            ]
            
            # Display schedules in a table
            df_schedules = pd.DataFrame(schedules)
            
            # Add edit buttons
            df_schedules["Action"] = [
                f'<button style="padding: 0.1rem 0.5rem; font-size: 0.8rem;">Edit</button> ' +
                f'<button style="padding: 0.1rem 0.5rem; font-size: 0.8rem; {"background-color: #4CAF50;" if row["enabled"] else "background-color: #f44336;"}">' +
                f'{"Enabled" if row["enabled"] else "Disabled"}</button>'
                for _, row in df_schedules.iterrows()
            ]
            
            # Display as HTML to show buttons (note: buttons are for display only in this demo)
            st.markdown(df_schedules.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Add new schedule form
            with st.expander("Add New Scheduled Load"):
                load_name = st.text_input("Load Name")
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.time_input("Start Time")
                with col2:
                    end_time = st.time_input("End Time")
                
                days_options = st.multiselect(
                    "Days",
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    default=["Monday", "Wednesday", "Friday"]
                )
                
                if st.button("Add Schedule"):
                    st.success(f"Added schedule for {load_name}")
        else:
            st.info("Scheduled load management is disabled")

# Tab 3: System Status
with tab3:
    st.subheader("System Status and Monitoring")
    
    # Create status indicators for all system components
    components = [
        {"name": "Solar Array", "status": "Online", "health": 98, "last_maintenance": "2023-04-15"},
        {"name": "Wind Turbine", "status": "Online", "health": 95, "last_maintenance": "2023-03-22"},
        {"name": "Battery Bank", "status": "Online", "health": current_data["battery"]["health_pct"], "last_maintenance": "2023-05-10"},
        {"name": "Charge Controller", "status": "Online", "health": 99, "last_maintenance": "2023-02-28"},
        {"name": "Main Inverter", "status": "Online", "health": 97, "last_maintenance": "2023-04-02"},
        {"name": "Control System", "status": "Online", "health": 100, "last_maintenance": "2023-05-20"},
    ]
    
    # Display components in a grid
    cols = st.columns(3)
    
    for i, component in enumerate(components):
        with cols[i % 3]:
            health = component["health"]
            health_color = "green" if health >= 90 else "orange" if health >= 70 else "red"
            
            st.markdown(
                f"""
                <div style="padding: 15px; border-radius: 5px; margin-bottom: 15px; 
                      background-color: {'#f5f5f5' if st.session_state.theme == 'light' else '#2d2d2d'};">
                    <h3 style="margin:0;">{component["name"]}</h3>
                    <p style="margin:5px 0;"><strong>Status:</strong> 
                        <span style="color: {'green' if component["status"] == 'Online' else 'red'};">
                            {component["status"]}
                        </span>
                    </p>
                    <p style="margin:5px 0;"><strong>Health:</strong> 
                        <span style="color: {health_color};">{health}%</span>
                    </p>
                    <p style="margin:5px 0;"><strong>Last Maintenance:</strong> {component["last_maintenance"]}</p>
                    <button style="padding: 5px 10px; margin-top: 5px; width: 100%;">
                        View Details
                    </button>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # System alerts
    st.subheader("Active System Alerts")
    
    alerts = current_data.get("alerts", [])
    if alerts:
        for alert in alerts:
            severity = alert["severity"]
            if severity == "high":
                st.error(f"⚠️ {alert['component'].title()}: {alert['message']}")
            elif severity == "medium":
                st.warning(f"⚠️ {alert['component'].title()}: {alert['message']}")
            else:
                st.info(f"ℹ️ {alert['component'].title()}: {alert['message']}")
    else:
        st.success("No active alerts - all systems operating normally")
    
    # System logs
    st.subheader("System Logs")
    
    # Generate sample logs for demonstration
    log_types = ["INFO", "WARNING", "ERROR"]
    log_weights = [0.7, 0.2, 0.1]
    components = ["Solar Controller", "Wind Controller", "Battery Management", "Inverter", "System"]
    
    # Create sample log entries for demonstration
    log_entries = []
    for i in range(10):
        log_type = np.random.choice(log_types, p=log_weights)
        component = np.random.choice(components)
        timestamps = (datetime.now() - timedelta(minutes=i*15)).strftime("%Y-%m-%d %H:%M:%S")
        
        if log_type == "INFO":
            message = np.random.choice([
                "System status check completed",
                "Energy production within normal parameters",
                "Battery charging cycle completed",
                "Load balance optimized",
                "Scheduled maintenance reminder set"
            ])
        elif log_type == "WARNING":
            message = np.random.choice([
                "Battery temperature slightly elevated",
                "Solar production below expected levels",
                "Wind turbine vibration detected",
                "Network connectivity intermittent",
                "Load approaching system capacity"
            ])
        else:  # ERROR
            message = np.random.choice([
                "Communication timeout detected",
                "Sensor data out of expected range",
                "Inverter reporting fault code",
                "Battery cell imbalance detected",
                "Emergency shutdown triggered"
            ])
        
        log_entries.append({
            "timestamps": timestamps,
            "type": log_type,
            "component": component,
            "message": message
        })
    
    # Create DataFrame for logs
    df_logs = pd.DataFrame(log_entries)
    
    # Add styling based on log type
    def color_log_type(val):
        color = "green" if val == "INFO" else "orange" if val == "WARNING" else "red"
        return f'color: {color}'
    
    # Apply styling and display
    styled_logs = df_logs.style.map(color_log_type, subset=["type"])
    st.dataframe(styled_logs, use_container_width=True)
    
    # Log filter and export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button("Export Logs", df_logs.to_csv(index=False), "system_logs.csv", "text/csv")
    
    with col2:
        log_level = st.selectbox("Filter by Level", ["All Levels", "INFO", "WARNING", "ERROR"])
    
    with col3:
        component_filter = st.selectbox("Filter by Component", ["All Components"] + components)

# Tab 4: Maintenance
with tab4:
    st.subheader("System Maintenance")

    # Create two columns outside the expander
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Create maintenance schedule expander
        with st.expander("Maintenance Schedule", expanded=True):
            st.markdown("### Maintenance Schedule")
            
            # Sample maintenance tasks
            maintenance_tasks = [
                {"component": "Solar Panels", "task": "Clean solar panels", "frequency": "Monthly", "last_done": "2023-05-15", "next_due": "2023-06-15", "status": "Upcoming"},
                {"component": "Wind Turbine", "task": "Lubricate bearings", "frequency": "Quarterly", "last_done": "2023-04-10", "next_due": "2023-07-10", "status": "Upcoming"},
                {"component": "Battery Bank", "task": "Check connections", "frequency": "Monthly", "last_done": "2023-05-15", "next_due": "2023-06-15", "status": "Upcoming"},
                {"component": "Inverter", "task": "Firmware update", "frequency": "As needed", "last_done": "2023-03-05", "next_due": "2023-06-05", "status": "Overdue"},
                {"component": "System", "task": "Full inspection", "frequency": "Bi-annually", "last_done": "2023-01-20", "next_due": "2023-07-20", "status": "Upcoming"},
            ]
            
            # Create a DataFrame for maintenance tasks
            df_tasks = pd.DataFrame(maintenance_tasks)
            
            # Add custom styling based on status
            def highlight_status(val):
                color = "green" if val == "Completed" else "red" if val == "Overdue" else "orange"
                return f'color: {color}'
            
            # Apply styling and display
            styled_tasks = df_tasks.style.map(highlight_status, subset=["status"])
            st.dataframe(styled_tasks, use_container_width=True)
        
        # Move the "Add Maintenance Task" expander outside the first expander but still in the same column
        with st.expander("Add Maintenance Task"):
            component = st.selectbox("Component", ["Solar Panels", "Wind Turbine", "Battery Bank", "Inverter", "Control System", "System"])
            task = st.text_input("Maintenance Task")
            frequency = st.selectbox("Frequency", ["Weekly", "Monthly", "Quarterly", "Bi-annually", "Annually", "As needed"])
            due_date = st.date_input("Due Date")
            
            if st.button("Add Task"):
                st.success(f"Added maintenance task for {component}")
                
    with col2:
        st.markdown("### System Performance Optimization")
        
        # Solar panel angle optimization
        st.markdown("#### Solar Panel Optimization")
        
        current_angle = 30
        optimal_angle = 32
        
        st.markdown(f"""
        Current tilt angle: {current_angle}°
        
        Recommended optimal angle: {optimal_angle}° (based on seasonal position)
        
        Estimated improvement: +1.5% generation
        """)
        
        if st.button("Adjust Solar Panel Angle"):
            st.success(f"Adjustment command sent - angle set to {optimal_angle}°")
        
        # Wind turbine optimization
        st.markdown("#### Wind Turbine Optimization")
        
        st.markdown("""
        Current cut-in speed: 2.5 m/s
        
        Brake status: Operational
        
        Yaw control: Automatic
        """)
        
        maintenance_mode = st.checkbox("Enable Turbine Maintenance Mode")
        
        if maintenance_mode:
            st.warning("Maintenance mode will temporarily disable the wind turbine")
            
            if st.button("Confirm Maintenance Mode"):
                st.success("Wind turbine entering maintenance mode")
        
        # Battery optimization
        st.markdown("#### Battery Optimization")
        
        st.markdown("""
        Battery balancing status: Normal
        
        Charging algorithm: Adaptive Multi-Stage
        """)
        
        charging_algorithm = st.selectbox(
            "Charging Algorithm",
            ["Adaptive Multi-Stage", "Constant Current", "Constant Voltage", "Float Charging"],
            index=0
        )
        
        if st.button("Update Charging Algorithm"):
            st.success(f"Charging algorithm updated to {charging_algorithm}")

# Footer with additional controls
st.divider()
col1, col2 = st.columns(2)

with col1:
    # System control buttons
    st.markdown("### Quick System Controls")
    
    control_cols = st.columns(3)
    
    with control_cols[0]:
        if st.button("🔄 System Restart", use_container_width=True):
            with st.spinner("Restarting system..."):
                time.sleep(2)
            st.success("System restart command sent successfully")
    
    with control_cols[1]:
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Generating system report..."):
                time.sleep(3)
            st.success("System report generated successfully")
            st.download_button(
                "Download Report",
                "This is a simulated system report in CSV format.",
                "system_report.csv",
                "text/csv"
            )
    
    with control_cols[2]:
        if st.button("🔋 Battery Test", use_container_width=True):
            with st.spinner("Running battery diagnostics..."):
                time.sleep(3)
            st.success("Battery diagnostics completed successfully")

with col2:
    # Emergency controls with confirmation
    st.markdown("### Emergency Controls")
    
    st.warning("These controls should only be used in emergency situations")
    
    emergency_cols = st.columns(2)
    
    with emergency_cols[0]:
        if st.button("⚠️ Emergency Stop", use_container_width=True):
            confirm = st.checkbox("Confirm Emergency Stop")
            
            if confirm:
                with st.spinner("Executing emergency stop..."):
                    time.sleep(2)
                st.error("Emergency stop executed. System is now offline.")
    
    with emergency_cols[1]:
        if st.button("🔌 Disconnect Grid", use_container_width=True):
            confirm = st.checkbox("Confirm Grid Disconnect")
            
            if confirm:
                with st.spinner("Disconnecting from grid..."):
                    time.sleep(2)
                st.warning("Grid disconnected. System running in island mode.")
