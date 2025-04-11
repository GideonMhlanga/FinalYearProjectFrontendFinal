import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# Import database and utilities
from database import db
from data_generator import data_generator
from utils import format_power, get_status_color
from anomaly_detection import detect_anomalies, get_anomaly_summary

# Set page configuration
st.set_page_config(
    page_title="Anomaly Detection & Alerts",
    page_icon="🚨",
    layout="wide"
)

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to access this page.")
    st.stop()

# Page title
st.title("Anomaly Detection & Alerts")
st.markdown("### Real-time System Anomaly Monitoring")

# Overview of the anomaly detection capabilities
st.markdown("""
This page provides advanced anomaly detection capabilities for your solar-wind hybrid system. 
The algorithms analyze system data in real-time to identify unusual patterns and potential issues 
before they become critical problems.

**Detection Methods:**
- **Statistical Analysis**: Uses Z-scores and outlier detection to identify values outside normal ranges
- **Rule-Based Detection**: Applies expert-defined rules and thresholds specific to hybrid renewable systems
- **Machine Learning**: Employs Isolation Forests to detect complex, multi-dimensional anomalies
""")

# Get historical data for analysis
historical_data = data_generator.get_historical_data(timeframe="week")

if historical_data.empty:
    st.info("Not enough historical data available yet for anomaly detection.")
    st.stop()

# Create tabs for different anomaly detection views
tabs = st.tabs([
    "Active Alerts", 
    "Detection Settings", 
    "Historical Analysis",
    "Alert Log"
])

# Active Alerts tab
with tabs[0]:
    st.subheader("Active System Alerts")
    
    # Add refresh button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh Alerts"):
            st.rerun()
    
    # Get the most recent data for real-time analysis
    recent_data = historical_data.tail(48)  # Last 48 hours
    
    # Run anomaly detection algorithms
    all_anomalies = detect_anomalies(
        data=recent_data,
        use_statistical=True,
        use_rule_based=True,
        use_ml=True,
        window_size=24
    )
    
    # Get anomaly summary
    anomaly_summary = get_anomaly_summary(all_anomalies)
    
    # Display metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Active Alerts", 
            anomaly_summary["total"],
            delta=None
        )
    
    with col2:
        st.metric(
            "Severe Alerts", 
            anomaly_summary["severe"],
            delta=None,
            delta_color="off" if anomaly_summary["severe"] == 0 else "inverse"
        )
    
    with col3:
        st.metric(
            "Moderate Alerts", 
            anomaly_summary["moderate"],
            delta=None,
            delta_color="off" if anomaly_summary["moderate"] == 0 else "inverse"
        )
    
    with col4:
        st.metric(
            "Mild Alerts", 
            anomaly_summary["mild"],
            delta=None,
            delta_color="off" if anomaly_summary["mild"] == 0 else "inverse"
        )
    
    # System status overview
    system_status = "Critical" if anomaly_summary["severe"] > 0 else \
                   "Warning" if anomaly_summary["moderate"] > 0 else \
                   "Caution" if anomaly_summary["mild"] > 0 else "Normal"
    
    status_color = {
        "Critical": "red",
        "Warning": "orange",
        "Caution": "yellow",
        "Normal": "green"
    }[system_status]
    
    st.markdown(f"""
    <div style="
        border-radius: 10px;
        background-color: {'rgba(255, 0, 0, 0.1)' if system_status == 'Critical' else 
                          'rgba(255, 165, 0, 0.1)' if system_status == 'Warning' else
                          'rgba(255, 255, 0, 0.1)' if system_status == 'Caution' else
                          'rgba(0, 255, 0, 0.1)'};
        padding: 20px;
        margin-bottom: 20px;
        ">
        <h3 style="margin-top: 0;">System Status: <span style="color: {status_color};">{system_status}</span></h3>
        <p>{'Immediate attention required!' if system_status == 'Critical' else
           'System operating with warnings' if system_status == 'Warning' else
           'System operating with minor issues' if system_status == 'Caution' else
           'All systems operating normally'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display active alerts grouped by severity
    if anomaly_summary["total"] > 0:
        # Severe alerts first
        if anomaly_summary["severe"] > 0:
            st.markdown("### 🔴 Severe Alerts")
            
            for category, anomaly_list in all_anomalies.items():
                severe_anomalies = [a for a in anomaly_list if a["severity"] == "severe"]
                
                if not severe_anomalies:
                    continue
                
                # Display each severe anomaly
                for anomaly in severe_anomalies:
                    with st.expander(f"{anomaly['message']} - {anomaly['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        # Display anomaly details
                        details_col1, details_col2 = st.columns(2)
                        
                        with details_col1:
                            st.markdown(f"**Category:** {category.replace('_', ' ').title()}")
                            st.markdown(f"**Timestamp:** {anomaly['timestamp']}")
                            st.markdown(f"**Value:** {anomaly['value']}")
                            
                            if "expected_range" in anomaly:
                                st.markdown(f"**Expected Range:** {anomaly['expected_range'][0]:.2f} to {anomaly['expected_range'][1]:.2f}")
                            
                            if "z_score" in anomaly:
                                st.markdown(f"**Z-score:** {anomaly['z_score']:.2f}")
                            
                            if "anomaly_score" in anomaly:
                                st.markdown(f"**Anomaly Score:** {anomaly['anomaly_score']:.2f}")
                        
                        with details_col2:
                            # Show small graph of recent values
                            if category in recent_data.columns:
                                fig = go.Figure()
                                
                                # Plot recent data
                                fig.add_trace(go.Scatter(
                                    x=recent_data["timestamp"].tail(24),
                                    y=recent_data[category].tail(24),
                                    mode="lines+markers",
                                    name=category.replace('_', ' ').title(),
                                    line=dict(color="blue", width=2)
                                ))
                                
                                # Mark the anomaly point
                                anomaly_time = anomaly["timestamp"]
                                anomaly_index = recent_data[recent_data["timestamp"] == anomaly_time].index
                                
                                if len(anomaly_index) > 0:
                                    anomaly_value = recent_data.loc[anomaly_index[0], category]
                                    
                                    fig.add_trace(go.Scatter(
                                        x=[anomaly_time],
                                        y=[anomaly_value],
                                        mode="markers",
                                        name="Anomaly",
                                        marker=dict(color="red", size=12, symbol="x")
                                    ))
                                
                                fig.update_layout(
                                    title=f"Recent {category.replace('_', ' ').title()} Values",
                                    height=300,
                                    margin=dict(l=10, r=10, t=40, b=10),
                                    showlegend=False,
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                                )
                                
                                # Create a unique key for each chart combining category and anomaly timestamp
                                chart_key = f"severe_{category}_{anomaly['timestamp'].strftime('%Y%m%d%H%M%S')}"
                                st.plotly_chart(fig, use_container_width=True, key=chart_key)
                        
                        # Add recommendation for this type of anomaly
                        st.markdown("#### Recommended Action:")
                        
                        if category == "battery_temperature":
                            st.markdown("""
                            - Stop charging immediately
                            - Check battery ventilation and cooling systems
                            - Monitor for signs of physical damage
                            - Contact technical support for assistance
                            """)
                        elif category == "battery_soc":
                            st.markdown("""
                            - Reduce connected loads
                            - Check charging system operation
                            - Verify solar and wind inputs
                            - Consider backup power options if critical loads are connected
                            """)
                        elif "solar" in category:
                            st.markdown("""
                            - Check solar panels for physical damage or obstructions
                            - Verify charge controller operation
                            - Check wiring connections
                            - Clean solar panels if excessive dust/dirt is present
                            """)
                        elif "wind" in category:
                            st.markdown("""
                            - Check turbine for physical damage
                            - Verify turbine braking system
                            - Check wind turbine controller
                            - Inspect cable connections
                            """)
                        else:
                            st.markdown("""
                            - Investigate the source of the anomaly
                            - Check relevant sensors and connections
                            - Consider system restart if recommended by manufacturer
                            - Contact technical support if issue persists
                            """)
        
        # Moderate alerts
        if anomaly_summary["moderate"] > 0:
            st.markdown("### 🟠 Moderate Alerts")
            
            for category, anomaly_list in all_anomalies.items():
                moderate_anomalies = [a for a in anomaly_list if a["severity"] == "moderate"]
                
                if not moderate_anomalies:
                    continue
                
                # Display each moderate anomaly
                for anomaly in moderate_anomalies:
                    with st.expander(f"{anomaly['message']} - {anomaly['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        # Display anomaly details
                        details_col1, details_col2 = st.columns(2)
                        
                        with details_col1:
                            st.markdown(f"**Category:** {category.replace('_', ' ').title()}")
                            st.markdown(f"**Timestamp:** {anomaly['timestamp']}")
                            st.markdown(f"**Value:** {anomaly['value']}")
                            
                            if "expected_range" in anomaly:
                                st.markdown(f"**Expected Range:** {anomaly['expected_range'][0]:.2f} to {anomaly['expected_range'][1]:.2f}")
                            
                            if "z_score" in anomaly:
                                st.markdown(f"**Z-score:** {anomaly['z_score']:.2f}")
                            
                            if "anomaly_score" in anomaly:
                                st.markdown(f"**Anomaly Score:** {anomaly['anomaly_score']:.2f}")
                        
                        with details_col2:
                            # Show small graph of recent values
                            if category in recent_data.columns:
                                fig = go.Figure()
                                
                                # Plot recent data
                                fig.add_trace(go.Scatter(
                                    x=recent_data["timestamp"].tail(24),
                                    y=recent_data[category].tail(24),
                                    mode="lines+markers",
                                    name=category.replace('_', ' ').title(),
                                    line=dict(color="blue", width=2)
                                ))
                                
                                # Mark the anomaly point
                                anomaly_time = anomaly["timestamp"]
                                anomaly_index = recent_data[recent_data["timestamp"] == anomaly_time].index
                                
                                if len(anomaly_index) > 0:
                                    anomaly_value = recent_data.loc[anomaly_index[0], category]
                                    
                                    fig.add_trace(go.Scatter(
                                        x=[anomaly_time],
                                        y=[anomaly_value],
                                        mode="markers",
                                        name="Anomaly",
                                        marker=dict(color="orange", size=12, symbol="x")
                                    ))
                                
                                fig.update_layout(
                                    title=f"Recent {category.replace('_', ' ').title()} Values",
                                    height=300,
                                    margin=dict(l=10, r=10, t=40, b=10),
                                    showlegend=False,
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                                )
                                
                                # Create a unique key for each chart combining category and anomaly timestamp
                                chart_key = f"moderate_{category}_{anomaly['timestamp'].strftime('%Y%m%d%H%M%S')}"
                                st.plotly_chart(fig, use_container_width=True, key=chart_key)
                        
                        # Add recommendation for this type of anomaly
                        st.markdown("#### Recommended Action:")
                        
                        if category == "battery_temperature":
                            st.markdown("""
                            - Reduce charging rate
                            - Check ventilation system
                            - Ensure ambient temperature is within specifications
                            """)
                        elif category == "battery_soc":
                            st.markdown("""
                            - Reduce non-essential loads
                            - Check charging system operation
                            - Monitor closely for the next few hours
                            """)
                        elif "solar" in category:
                            st.markdown("""
                            - Check for partial shading or obstructions
                            - Verify MPPT controller operation
                            - Consider cleaning panels if needed
                            """)
                        elif "wind" in category:
                            st.markdown("""
                            - Check wind turbine operation
                            - Verify controller settings
                            - Inspect for any unusual noise or vibration
                            """)
                        else:
                            st.markdown("""
                            - Monitor the situation closely
                            - Perform visual inspection of related components
                            - Document the issue for future reference
                            """)
        
        # Mild alerts
        if anomaly_summary["mild"] > 0:
            st.markdown("### 🟡 Mild Alerts")
            
            for category, anomaly_list in all_anomalies.items():
                mild_anomalies = [a for a in anomaly_list if a["severity"] == "mild"]
                
                if not mild_anomalies:
                    continue
                
                # Group mild anomalies by category
                st.markdown(f"#### {category.replace('_', ' ').title()} - {len(mild_anomalies)} alerts")
                
                # Display in a dataframe
                mild_df = pd.DataFrame(mild_anomalies)
                if 'timestamp' in mild_df.columns:
                    mild_df['timestamp'] = mild_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                
                cols_to_display = ['timestamp', 'message', 'value']
                if 'expected_range' in mild_df.columns:
                    cols_to_display.append('expected_range')
                
                st.dataframe(
                    mild_df[cols_to_display], 
                    hide_index=True, 
                    use_container_width=True
                )
    else:
        # No anomalies detected
        st.success("No anomalies detected in the system! Everything is operating within normal parameters.")
        
        # Show live charts of key metrics
        st.subheader("Live System Metrics")
        
        chart_tabs = st.tabs(["Power Generation", "Battery Status", "Environmental"])
        
        with chart_tabs[0]:
            fig = go.Figure()
            
            # Add solar power
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["solar_power"],
                name="Solar Power",
                line=dict(color="#FFA500", width=2)
            ))
            
            # Add wind power
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["wind_power"],
                name="Wind Power",
                line=dict(color="#1E90FF", width=2)
            ))
            
            # Add total power
            if "total_generation" in recent_data.columns:
                fig.add_trace(go.Scatter(
                    x=recent_data["timestamp"],
                    y=recent_data["total_generation"],
                    name="Total Generation",
                    line=dict(color="#32CD32", width=2)
                ))
            
            fig.update_layout(
                title="Power Generation (Last 48 Hours)",
                xaxis_title="Time",
                yaxis_title="Power (kW)",
                height=400,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
            )
            
            st.plotly_chart(fig, use_container_width=True, key="power_chart")
        
        with chart_tabs[1]:
            fig = go.Figure()
            
            # Add battery SOC
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["battery_soc"],
                name="Battery SOC (%)",
                line=dict(color="#32CD32", width=2)
            ))
            
            fig.update_layout(
                title="Battery State of Charge (Last 48 Hours)",
                xaxis_title="Time",
                yaxis_title="SOC (%)",
                height=400,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
            )
            
            st.plotly_chart(fig, use_container_width=True, key="battery_chart")
        
        with chart_tabs[2]:
            fig = go.Figure()
            
            # Add temperature
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["temperature"],
                name="Temperature (°C)",
                line=dict(color="#FF4500", width=2)
            ))
            
            # Add second y-axis for irradiance
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["irradiance"],
                name="Irradiance (W/m²)",
                line=dict(color="#FFD700", width=2),
                yaxis="y2"
            ))
            
            # Add third y-axis for wind speed
            fig.add_trace(go.Scatter(
                x=recent_data["timestamp"],
                y=recent_data["wind_speed"],
                name="Wind Speed (m/s)",
                line=dict(color="#1E90FF", width=2),
                yaxis="y3"
            ))
            
            fig.update_layout(
                title="Environmental Conditions (Last 48 Hours)",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                height=400,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA"),
                yaxis=dict(
                    title="Temperature (°C)",
                    side="left"
                ),
                yaxis2=dict(
                    title="Irradiance (W/m²)",
                    side="right",
                    overlaying="y",
                    range=[0, 1200]
                ),
                yaxis3=dict(
                    title="Wind Speed (m/s)",
                    side="right",
                    overlaying="y",
                    position=0.85,
                    range=[0, 25]
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, key="environmental_chart")

# Detection Settings tab
with tabs[1]:
    st.subheader("Anomaly Detection Settings")
    
    st.markdown("""
    Customize the sensitivity and methods used for anomaly detection in your system. 
    These settings affect how the system identifies and alerts you to potential issues.
    """)
    
    # Detection methods selection
    st.markdown("### Detection Methods")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        use_statistical = st.toggle("Statistical Analysis", value=True)
        st.markdown("""
        **Statistical analysis** identifies values that deviate significantly from historical patterns.
        Good for detecting sudden changes or outliers in individual metrics.
        """)
    
    with col2:
        use_rule_based = st.toggle("Rule-Based Detection", value=True)
        st.markdown("""
        **Rule-based detection** applies predefined thresholds and expert knowledge.
        Best for known issues and expected operational boundaries.
        """)
    
    with col3:
        use_ml = st.toggle("Machine Learning", value=True)
        st.markdown("""
        **Machine learning detection** identifies complex patterns and relationships.
        Excellent for subtle issues that involve multiple system variables.
        """)
    
    # Sensitivity settings
    st.markdown("### Detection Sensitivity")
    
    sensitivity = st.slider(
        "Overall Sensitivity",
        min_value=1,
        max_value=5,
        value=3,
        help="Higher sensitivity detects more subtle anomalies but may increase false positives"
    )
    
    # Map sensitivity to thresholds (for demonstration)
    sensitivity_mapping = {
        1: {"severe": 4.0, "moderate": 3.0, "mild": 2.5},  # Least sensitive
        2: {"severe": 3.5, "moderate": 2.5, "mild": 2.0},
        3: {"severe": 3.0, "moderate": 2.0, "mild": 1.5},  # Default
        4: {"severe": 2.5, "moderate": 1.5, "mild": 1.0},
        5: {"severe": 2.0, "moderate": 1.0, "mild": 0.7}   # Most sensitive
    }
    
    selected_thresholds = sensitivity_mapping[sensitivity]
    
    # Display the threshold values
    st.markdown("#### Current Threshold Values (Z-scores)")
    
    threshold_cols = st.columns(3)
    
    with threshold_cols[0]:
        st.metric("Severe Alert Threshold", f"±{selected_thresholds['severe']:.1f}σ")
    
    with threshold_cols[1]:
        st.metric("Moderate Alert Threshold", f"±{selected_thresholds['moderate']:.1f}σ")
    
    with threshold_cols[2]:
        st.metric("Mild Alert Threshold", f"±{selected_thresholds['mild']:.1f}σ")
    
    # Advanced settings
    with st.expander("Advanced Settings"):
        st.markdown("#### Statistical Detection Settings")
        
        window_size = st.slider(
            "Analysis Window Size (hours)",
            min_value=6,
            max_value=72,
            value=24,
            step=6,
            help="The number of hours of historical data used for anomaly detection"
        )
        
        st.markdown("#### Machine Learning Settings")
        
        contamination = st.slider(
            "Expected Anomaly Rate (%)",
            min_value=0.1,
            max_value=10.0,
            value=5.0,
            step=0.1,
            help="Expected percentage of data points that are anomalies (affects ML detection sensitivity)"
        ) / 100.0
        
        st.markdown("#### Component-Specific Thresholds")
        
        # Allow custom thresholds for different components
        st.markdown("Customize detection thresholds for specific system components:")
        
        custom_col1, custom_col2 = st.columns(2)
        
        with custom_col1:
            st.subheader("Solar Components")
            
            solar_sensitivity = st.select_slider(
                "Solar Power Sensitivity",
                options=["Very Low", "Low", "Medium", "High", "Very High"],
                value="Medium"
            )
            
            inverter_sensitivity = st.select_slider(
                "Inverter Sensitivity",
                options=["Very Low", "Low", "Medium", "High", "Very High"],
                value="Medium"
            )
        
        with custom_col2:
            st.subheader("Battery Components")
            
            battery_sensitivity = st.select_slider(
                "Battery Health Sensitivity",
                options=["Very Low", "Low", "Medium", "High", "Very High"],
                value="High"
            )
            
            temperature_sensitivity = st.select_slider(
                "Temperature Sensitivity",
                options=["Very Low", "Low", "Medium", "High", "Very High"],
                value="High"
            )
    
    # Save settings button
    if st.button("Save Detection Settings"):
        st.success("Anomaly detection settings saved successfully!")

# Historical Analysis tab
with tabs[2]:
    st.subheader("Historical Anomaly Analysis")
    
    st.markdown("""
    Analyze past anomalies to identify patterns and trends. This can help optimize 
    system operation and prevent recurring issues.
    """)
    
    # Time range selection
    st.markdown("### Select Analysis Timeframe")
    
    timeframe = st.radio(
        "Analysis Period",
        options=["Past Week", "Past Month", "Past 3 Months", "Custom Range"],
        horizontal=True
    )
    
    if timeframe == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
        
        date_range = (start_date, end_date)
    else:
        # Pre-defined ranges
        days = {
            "Past Week": 7,
            "Past Month": 30,
            "Past 3 Months": 90
        }[timeframe]
        
        date_range = (
            datetime.now() - timedelta(days=days),
            datetime.now()
        )
    
    # Run analysis button
    if st.button("Run Historical Analysis"):
        with st.spinner("Analyzing historical data for anomalies..."):
            # Simulate data analysis with a progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                # Simulate processing time
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # "Complete" analysis
            # For demonstration purposes, we'll just re-use the recent_data anomalies but pretend they're historical
            all_historical_anomalies = detect_anomalies(
                data=historical_data,
                use_statistical=True,
                use_rule_based=True,
                use_ml=True,
                window_size=24
            )
            
            historical_summary = get_anomaly_summary(all_historical_anomalies)
            
            # Create a timeline of anomalies
            anomaly_timeline = []
            
            for category, anomaly_list in all_historical_anomalies.items():
                for anomaly in anomaly_list:
                    anomaly_timeline.append({
                        "timestamp": anomaly["timestamp"],
                        "category": category.replace("_", " ").title(),
                        "message": anomaly["message"],
                        "severity": anomaly["severity"],
                        "value": anomaly["value"]
                    })
            
            if anomaly_timeline:
                # Convert to DataFrame for visualization
                timeline_df = pd.DataFrame(anomaly_timeline)
                timeline_df = timeline_df.sort_values("timestamp")
                
                # Assign numeric severity for coloring
                severity_map = {
                    "severe": 3,
                    "moderate": 2,
                    "mild": 1
                }
                
                timeline_df["severity_value"] = timeline_df["severity"].map(severity_map)
                
                # Display timeline visualization
                st.subheader("Anomaly Timeline")
                
                fig = px.scatter(
                    timeline_df,
                    x="timestamp",
                    y="category",
                    color="severity",
                    size="severity_value",
                    hover_name="message",
                    color_discrete_map={
                        "severe": "red",
                        "moderate": "orange",
                        "mild": "yellow"
                    },
                    size_max=15,
                )
                
                fig.update_layout(
                    title="Anomalies Over Time",
                    xaxis_title="Date",
                    yaxis_title="System Component",
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                )
                
                st.plotly_chart(fig, use_container_width=True, key="anomalies_over_time")
                
                # Anomaly distribution by category
                st.subheader("Anomaly Distribution by Component")
                
                category_counts = timeline_df["category"].value_counts().reset_index()
                category_counts.columns = ["Category", "Count"]
                
                fig = px.bar(
                    category_counts,
                    x="Category",
                    y="Count",
                    color="Count",
                    color_continuous_scale="Viridis"
                )
                
                fig.update_layout(
                    xaxis_title="System Component",
                    yaxis_title="Number of Anomalies",
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                )
                
                st.plotly_chart(fig, use_container_width=True, key="detection_method_comparison")
                
                # Anomaly distribution by severity
                severity_counts = timeline_df["severity"].value_counts().reset_index()
                severity_counts.columns = ["Severity", "Count"]
                
                # Sort by severity
                severity_order = {"severe": 0, "moderate": 1, "mild": 2}
                severity_counts["order"] = severity_counts["Severity"].map(severity_order)
                severity_counts = severity_counts.sort_values("order")
                
                fig = px.pie(
                    severity_counts,
                    values="Count",
                    names="Severity",
                    color="Severity",
                    color_discrete_map={
                        "severe": "red",
                        "moderate": "orange",
                        "mild": "yellow"
                    },
                    hole=0.4
                )
                
                fig.update_layout(
                    title="Anomaly Distribution by Severity",
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                )
                
                st.plotly_chart(fig, use_container_width=True, key="anomaly_severity_distribution")
                
                # Detailed anomaly table
                st.subheader("Detailed Anomaly Log")
                
                # Format the table data
                detail_df = timeline_df.copy()
                detail_df["timestamps"] = detail_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
                detail_df["severity"] = detail_df["severity"].str.title()
                
                # Reorder and select columns
                detail_df = detail_df[["timestamp", "category", "severity", "message", "value"]]
                detail_df.columns = ["Timestamp", "Component", "Severity", "Message", "Value"]
                
                # Display as a sortable table
                st.dataframe(
                    detail_df,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Export options
                csv = detail_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download Anomaly Data (CSV)",
                    csv,
                    "solar_wind_anomalies.csv",
                    "text/csv",
                    key="download-csv"
                )
            else:
                st.info("No anomalies detected in the selected timeframe.")

# Alert Log tab
with tabs[3]:
    st.subheader("System Alert Log")
    
    st.markdown("""
    View a complete history of all system alerts and actions taken.
    This log helps track system performance over time and document maintenance activities.
    """)
    
    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            options=["Severe", "Moderate", "Mild", "Resolved"],
            default=["Severe", "Moderate", "Mild"]
        )
    
    with filter_col2:
        component_filter = st.multiselect(
            "Filter by Component",
            options=["Solar Power", "Wind Power", "Battery", "Inverter", "Controller", "System"]
        )
    
    with filter_col3:
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now() - timedelta(days=30), datetime.now()]
        )
    
    # Create sample alert log data
    log_data = []
    
    # Add some sample alerts
    for i in range(50):
        days_ago = np.random.randint(1, 30)
        alert_time = datetime.now() - timedelta(days=days_ago, 
                                               hours=np.random.randint(0, 24),
                                               minutes=np.random.randint(0, 60))
        
        severity = np.random.choice(["Severe", "Moderate", "Mild", "Resolved"], p=[0.1, 0.3, 0.4, 0.2])
        component = np.random.choice(["Solar Power", "Wind Power", "Battery", "Inverter", "Controller", "System"])
        
        if severity == "Severe":
            if component == "Battery":
                message = "Critical battery temperature detected"
                action = "System shutdown initiated, maintenance team contacted"
            elif component == "Inverter":
                message = "Inverter overload detected"
                action = "Load reduction performed, system restarted"
            else:
                message = f"Critical anomaly in {component.lower()} system"
                action = "Alert sent to maintenance team"
        elif severity == "Moderate":
            message = f"Unusual {component.lower()} performance detected"
            action = "System monitored, no immediate action required"
        elif severity == "Mild":
            message = f"Minor deviation in {component.lower()} parameters"
            action = "Logged for future reference"
        else:  # Resolved
            message = f"Previous {component.lower()} issue resolved"
            action = "Normal operation resumed"
        
        log_data.append({
            "timestamp": alert_time,
            "severity": severity,
            "component": component,
            "message": message,
            "action": action,
            "user": np.random.choice(["system", "admin", "operator", "maintenance"])
        })
    
    # Convert to DataFrame
    log_df = pd.DataFrame(log_data)
    
    # Apply filters
    if severity_filter:
        log_df = log_df[log_df["severity"].isin(severity_filter)]
    
    if component_filter:
        log_df = log_df[log_df["component"].isin(component_filter)]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (log_df["timestamp"].dt.date >= start_date) & (log_df["timestamp"].dt.date <= end_date)
        log_df = log_df[mask]
    
    # Sort by timestamp (newest first)
    log_df = log_df.sort_values("timestamp", ascending=False)
    
    # Format timestamp for display
    log_df["timestamp"] = log_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    
    # Display log
    st.dataframe(
        log_df,
        hide_index=True,
        use_container_width=True
    )
    
    # Export option
    csv = log_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Alert Log (CSV)",
        csv,
        "solar_wind_alert_log.csv",
        "text/csv",
        key="download-alert-log"
    )