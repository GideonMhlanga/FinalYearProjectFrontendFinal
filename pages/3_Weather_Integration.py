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
    page_title="Weather Integration | Solar-Wind Hybrid Monitor",
    page_icon="🌤️",
    layout="wide"
)

# Initialize session state for theme if it doesn't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Title and description
st.title("Zimbabwe Weather Integration")
st.write("Live Zimbabwe weather data and forecasts to optimize your energy generation")

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
environmental_data = current_data["environmental"]
last_refresh = st.session_state.last_refresh_time

# Display last refresh time
st.caption(f"Last updated: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Current weather conditions
st.subheader("Current Weather Conditions")

# Create columns for current conditions
col1, col2, col3 = st.columns(3)

# Solar irradiance
irradiance = environmental_data["irradiance"]
irradiance_color = get_status_color(irradiance, {"green": (600, float('inf')), "yellow": (200, 600), "red": (0, 200)})

with col1:
    st.markdown(
        f"""
        <div style="padding: 20px; border-radius: 5px; background-color: {'#fff9e6' if st.session_state.theme == 'light' else '#332e1f'};">
            <h3 style="margin:0;">☀️ Solar Irradiance</h3>
            <h2 style="margin:0; color: {'green' if irradiance_color == 'green' else 'orange' if irradiance_color == 'yellow' else 'red'};">
                {irradiance:.1f} W/m²
            </h2>
            <p style="margin:0;">
                {
                    "Excellent for solar generation" if irradiance > 800 else
                    "Good for solar generation" if irradiance > 500 else
                    "Moderate solar potential" if irradiance > 200 else
                    "Low solar potential"
                }
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Wind speed
wind_speed = environmental_data["wind_speed"]
wind_color = get_status_color(wind_speed, {"green": (4, float('inf')), "yellow": (2, 4), "red": (0, 2)})

with col2:
    st.markdown(
        f"""
        <div style="padding: 20px; border-radius: 5px; background-color: {'#e6f2ff' if st.session_state.theme == 'light' else '#1a2833'};">
            <h3 style="margin:0;">💨 Wind Speed</h3>
            <h2 style="margin:0; color: {'green' if wind_color == 'green' else 'orange' if wind_color == 'yellow' else 'red'};">
                {wind_speed:.1f} m/s
            </h2>
            <p style="margin:0;">
                {
                    "Excellent for wind generation" if wind_speed > 6 else
                    "Good for wind generation" if wind_speed > 4 else
                    "Moderate wind potential" if wind_speed > 2 else
                    "Low wind potential"
                }
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Temperature
temperature = environmental_data["temperature"]
temp_color = get_status_color(temperature, {"green": (15, 25), "yellow": (5, 15), "red": (25, 45)})

with col3:
    st.markdown(
        f"""
        <div style="padding: 20px; border-radius: 5px; background-color: {'#e6ffe6' if st.session_state.theme == 'light' else '#1a331a'};">
            <h3 style="margin:0;">🌡️ Temperature</h3>
            <h2 style="margin:0; color: {'green' if temp_color == 'green' else 'orange' if temp_color == 'yellow' else 'red'};">
                {temperature:.1f} °C
            </h2>
            <p style="margin:0;">
                {
                    "Optimal for system performance" if 15 <= temperature <= 25 else
                    "Too hot - reduced efficiency" if temperature > 25 else
                    "Too cold - reduced efficiency"
                }
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Zimbabwe location selector
from weather_api import zimbabwe_weather

# Add a location selector in the sidebar
if "weather_location" not in st.session_state:
    st.session_state.weather_location = "Harare"

available_locations = zimbabwe_weather.get_available_locations()
selected_location = st.sidebar.selectbox(
    "Select Zimbabwe Location",
    available_locations,
    index=available_locations.index(st.session_state.weather_location)
)

# Update the selected location
if selected_location != st.session_state.weather_location:
    st.session_state.weather_location = selected_location
    st.rerun()

# API Key Input
if "zimbabwe_weather_api_key" not in st.session_state:
    st.session_state.zimbabwe_weather_api_key = ""

with st.sidebar.expander("Zimbabwe Weather API Settings"):
    api_key = st.text_input(
        "Zimbabwe Weather API Key",
        value=st.session_state.zimbabwe_weather_api_key,
        type="password",
        help="Enter your Zimbabwe Weather API key to access real weather data"
    )
    
    if api_key != st.session_state.zimbabwe_weather_api_key:
        st.session_state.zimbabwe_weather_api_key = api_key
        # Set the API key in environment variables
        import os
        os.environ["ZIMBABWE_WEATHER_API_KEY"] = api_key
        st.success("API key updated. Refresh data to use it.")

# Weather forecast section
st.subheader(f"5-Day Weather Forecast for {st.session_state.weather_location}")

# Get weather forecast data for the selected location
forecast = data_generator.get_weather_forecast(st.session_state.weather_location)

# Create forecast cards
forecast_cols = st.columns(len(forecast))

for i, day in enumerate(forecast):
    with forecast_cols[i]:
        # Determine weather icon
        if day["conditions"] == "Sunny":
            icon = "☀️"
        elif day["conditions"] == "Partly Cloudy":
            icon = "⛅"
        elif day["conditions"] == "Cloudy":
            icon = "☁️"
        elif day["conditions"] == "Rainy":
            icon = "🌧️"
        elif day["conditions"] == "Windy":
            icon = "💨"
        else:
            icon = "🌤️"
        
        # Set background color based on conditions
        if day["conditions"] == "Sunny":
            bg_color = "#fff9e6" if st.session_state.theme == "light" else "#332e1f"
        elif day["conditions"] == "Partly Cloudy":
            bg_color = "#f0f0f0" if st.session_state.theme == "light" else "#2a2a2a"
        elif day["conditions"] == "Cloudy":
            bg_color = "#e0e0e0" if st.session_state.theme == "light" else "#252525"
        elif day["conditions"] == "Rainy":
            bg_color = "#e6f2ff" if st.session_state.theme == "light" else "#1a2833"
        elif day["conditions"] == "Windy":
            bg_color = "#e6ffe6" if st.session_state.theme == "light" else "#1a331a"
        else:
            bg_color = "#f5f5f5" if st.session_state.theme == "light" else "#2d2d2d"
        
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 5px; background-color: {bg_color}; text-align: center;">
                <h3 style="margin:0;">{day["day"]}</h3>
                <p style="margin:0; font-size: 0.8em;">{day["date"]}</p>
                <h1 style="margin:5px 0; font-size: 2.5em;">{icon}</h1>
                <h3 style="margin:0;">{day["conditions"]}</h3>
                <p style="margin:5px 0;">{day["temp_high"]:.1f}°C / {day["temp_low"]:.1f}°C</p>
                <p style="margin:0;">Wind: {day["wind_speed"]:.1f} m/s</p>
                <div style="margin-top: 10px; padding: 5px; border-radius: 3px; background-color: rgba(0,0,0,0.05);">
                    <p style="margin:0; font-weight: bold;">Energy Forecast</p>
                    <p style="margin:0;">Solar: <span style="color: {'green' if day['solar_potential'] == 'High' else 'orange' if day['solar_potential'] == 'Medium' else 'red'}">{day["solar_potential"]}</span></p>
                    <p style="margin:0;">Wind: <span style="color: {'green' if day['wind_potential'] == 'High' else 'orange' if day['wind_potential'] == 'Medium' else 'red'}">{day["wind_potential"]}</span></p>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

# Weather impact on energy generation
st.subheader("Weather Impact on Energy Generation")

# Get historical data
historical_data = data_generator.get_historical_data(timeframe="day")

if not historical_data.empty:
    # Create tabs for different analyses
    tab1, tab2 = st.tabs(["Solar vs. Weather", "Wind vs. Weather"])
    
    # Tab 1: Solar vs. Weather
    with tab1:
        # Create scatter plot for solar power vs. irradiance
        fig = px.scatter(
            historical_data,
            x="irradiance",
            y="solar_power",
            color="temperature",
            color_continuous_scale="Viridis",
            labels={"irradiance": "Solar Irradiance (W/m²)", "solar_power": "Solar Power (kW)", "temperature": "Temperature (°C)"},
            title="Solar Power vs. Irradiance"
        )
        
        # Add trendline with error handling
        try:
            # Check for NaN or zero values that could cause the SVD convergence error
            mask = ~np.isnan(historical_data["irradiance"]) & ~np.isnan(historical_data["solar_power"]) & (historical_data["irradiance"] != 0)
            
            if sum(mask) > 1:  # We need at least 2 valid points for a line
                x_valid = historical_data["irradiance"][mask]
                y_valid = historical_data["solar_power"][mask]
                
                # Sort the data for plotting
                sort_indices = np.argsort(x_valid)
                x_sorted = x_valid.iloc[sort_indices]
                
                # Calculate the trendline
                poly_fit = np.polyfit(x_valid, y_valid, 1)
                poly_1d = np.poly1d(poly_fit)
                
                # Add trendline to the plot
                fig.add_trace(
                    go.Scatter(
                        x=x_sorted,
                        y=poly_1d(x_sorted),
                        mode="lines",
                        line=dict(color="red", dash="dash"),
                        name="Trendline"
                    )
                )
        except Exception as e:
            st.warning(f"Could not calculate trendline: insufficient or invalid data")
        
        fig.update_layout(
            height=500,
            xaxis_title="Solar Irradiance (W/m²)",
            yaxis_title="Solar Power (kW)",
            margin=dict(l=60, r=20, t=50, b=60),
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
        
        # Add explanation
        st.markdown("""
        The scatter plot above shows the relationship between solar irradiance and solar power generation. 
        Each point is colored according to the ambient temperature at that time. As expected, there is a 
        strong positive correlation between irradiance and power output.
        
        **Key observations:**
        - Higher irradiance generally results in higher power output
        - Temperature also affects solar panel efficiency (slightly lower efficiency at higher temperatures)
        - The relationship is approximately linear within the operating range
        """)
    
    # Tab 2: Wind vs. Weather
    with tab2:
        # Create scatter plot for wind power vs. wind speed
        fig = px.scatter(
            historical_data,
            x="wind_speed",
            y="wind_power",
            color="temperature",
            color_continuous_scale="Viridis",
            labels={"wind_speed": "Wind Speed (m/s)", "wind_power": "Wind Power (kW)", "temperature": "Temperature (°C)"},
            title="Wind Power vs. Wind Speed"
        )
        
        # Cubic relationship for wind power (power ~ wind_speed^3)
        x_range = np.linspace(min(historical_data["wind_speed"]), max(historical_data["wind_speed"]), 100)
        
        # Simple cubic model approximation
        a = 0.1  # scaling factor
        y_model = a * x_range**3
        
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=y_model,
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="Power Curve Model"
            )
        )
        
        fig.update_layout(
            height=500,
            xaxis_title="Wind Speed (m/s)",
            yaxis_title="Wind Power (kW)",
            margin=dict(l=60, r=20, t=50, b=60),
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
        
        # Add explanation
        st.markdown("""
        The scatter plot above shows the relationship between wind speed and wind power generation.
        Each point is colored according to the ambient temperature at that time. Wind power has a 
        cubic relationship with wind speed (P ∝ v³), which is illustrated by the model curve.
        
        **Key observations:**
        - Wind power increases with the cube of wind speed (P ∝ v³)
        - There is more variability in wind power output compared to solar
        - Temperature has minimal effect on wind power generation
        - Cut-in speed (minimum speed to generate power) is around 2 m/s
        """)
else:
    st.info("Not enough historical data available yet for weather impact analysis.")

# Weather-based energy optimization
st.subheader("Weather-Based Energy Optimization")

# Create columns for optimization insights
opt_col1, opt_col2 = st.columns(2)

with opt_col1:
    st.markdown("### Today's Generation Strategy")
    
    # Determine optimal strategy based on current conditions
    if irradiance > 500 and wind_speed < 3:
        strategy = "Solar Priority"
        explanation = "High solar irradiance and low wind speed indicate solar will be your primary generation source today."
        icon = "☀️"
        color = "#FFD700"
    elif irradiance < 300 and wind_speed > 4:
        strategy = "Wind Priority"
        explanation = "Low solar irradiance and good wind speed indicate wind will be your primary generation source today."
        icon = "💨"
        color = "#4682B4"
    else:
        strategy = "Balanced"
        explanation = "Current conditions support both solar and wind generation. A balanced approach is recommended."
        icon = "⚖️"
        color = "#9370DB"
    
    st.markdown(
        f"""
        <div style="padding: 20px; border-radius: 5px; border: 2px solid {color}; background-color: {'rgba(255,255,255,0.1)' if st.session_state.theme == 'dark' else 'rgba(0,0,0,0.05)'};">
            <h2 style="margin:0; color: {color};">{icon} {strategy}</h2>
            <p style="margin-top: 10px;">{explanation}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Add specific recommendations
    st.markdown("### Recommendations")
    
    recommendations = []
    if strategy == "Solar Priority":
        recommendations = [
            "Ensure solar panels are clean and unobstructed",
            "Temporarily disable any shadowing automation to maximize solar exposure",
            "Consider scheduling high-energy activities during peak sun hours",
            "Store excess energy in battery for night use"
        ]
    elif strategy == "Wind Priority":
        recommendations = [
            "Verify wind turbine maintenance is up to date",
            "Clear any potential obstructions around turbines",
            "Consider scheduling high-energy activities during peak wind periods",
            "Store excess energy in battery for low-wind periods"
        ]
    else:
        recommendations = [
            "Divide loads between both energy sources based on real-time generation",
            "Monitor both systems for optimal performance",
            "Dynamically adjust consumption based on generation patterns",
            "Maintain batteries at moderate charge level to accommodate fluctuations"
        ]
    
    for rec in recommendations:
        st.markdown(f"- {rec}")

with opt_col2:
    st.markdown("### 5-Day Energy Forecast")
    
    # Process forecast data for chart
    dates = [day["date"] for day in forecast]
    solar_potential = [100 if day["solar_potential"] == "High" else 60 if day["solar_potential"] == "Medium" else 30 for day in forecast]
    wind_potential = [100 if day["wind_potential"] == "High" else 60 if day["wind_potential"] == "Medium" else 30 for day in forecast]
    
    # Create grouped bar chart for energy potential
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates,
        y=solar_potential,
        name="Solar Potential",
        marker_color="#FFD700"
    ))
    
    fig.add_trace(go.Bar(
        x=dates,
        y=wind_potential,
        name="Wind Potential",
        marker_color="#4682B4"
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Energy Potential (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=30, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)' if st.session_state.theme == "dark" else 'rgba(240,242,246,0.5)',
        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA"),
        barmode="group"
    )
    
    # Add grid lines
    fig.update_xaxes(
        showgrid=False
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add weekly optimization tips
    st.markdown("### Weekly Planning Recommendations")
    
    # Create simple forecasting for the week based on forecast data
    best_solar_day = dates[solar_potential.index(max(solar_potential))]
    best_wind_day = dates[wind_potential.index(max(wind_potential))]
    worst_day_index = [s + w for s, w in zip(solar_potential, wind_potential)].index(min([s + w for s, w in zip(solar_potential, wind_potential)]))
    worst_day = dates[worst_day_index]
    
    st.markdown(f"""
    - **Best day for solar generation:** {best_solar_day}
    - **Best day for wind generation:** {best_wind_day}
    - **Energy conservation day:** {worst_day} (lowest combined generation potential)
    """)
    
    # Add a custom conservation plan
    with st.expander("Energy Conservation Plan for Low Generation Days"):
        st.markdown("""
        1. **Shift non-essential loads** to high-generation days
        2. **Reduce discretionary energy use** (HVAC settings, etc.)
        3. **Pre-charge battery** to maximum capacity the day before
        4. **Prioritize critical loads** with automated load shedding
        5. **Activate backup systems** if available for extended low-generation periods
        """)

# Weather alert system
with st.expander("Weather Alerts and Notifications", expanded=False):
    st.markdown("### Configure Weather Alerts")
    
    # Weather alert settings
    alert_cols = st.columns(3)
    
    with alert_cols[0]:
        st.checkbox("High wind alerts (>15 m/s)", value=True)
        st.checkbox("Low irradiance alerts (<100 W/m²)", value=True)
    
    with alert_cols[1]:
        st.checkbox("Extreme temperature alerts", value=True)
        st.checkbox("Freezing condition alerts", value=True)
    
    with alert_cols[2]:
        st.checkbox("Favorable generation condition alerts", value=False)
        st.checkbox("Daily weather forecast summary", value=True)
    
    st.markdown("### Notification Methods")
    
    notification_cols = st.columns(3)
    
    with notification_cols[0]:
        st.checkbox("Dashboard notifications", value=True)
    
    with notification_cols[1]:
        st.checkbox("Email alerts", value=False)
        st.text_input("Email address")
    
    with notification_cols[2]:
        st.checkbox("SMS alerts (for critical issues only)", value=False)
        st.text_input("Phone number")
    
    # Save settings button
    st.button("Save Alert Settings")
