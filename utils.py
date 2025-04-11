import numpy as np
import pandas as pd
import datetime
from typing import Tuple, Dict, List, Any, Optional
from database import db


def get_solar_power(timestamp: datetime.datetime, irradiance: float) -> float:
    """
    Calculate solar power output based on real-time irradiance data
    
    Args:
        timestamp: Current timestamp
        irradiance: Current solar irradiance in W/m²
        
    Returns:
        Solar power output in kW
    """
    # Get system settings
    system_settings = db.get_settings("system")
    solar_capacity = system_settings.get("solar_capacity", 5.0)  # Default 5kW system
    
    # Calculate power output
    # Assuming 15% system losses (inverter, wiring, etc.)
    system_efficiency = 0.85
    
    # Convert irradiance to power output
    # Standard test conditions: 1000 W/m² = rated power
    power_output = (irradiance / 1000) * solar_capacity * system_efficiency
    
    # Ensure power output is within system capacity
    power_output = min(power_output, solar_capacity)
    
    return max(0, power_output)  # Ensure non-negative power output


def get_wind_power(timestamp: datetime.datetime, wind_speed: float) -> float:
    """
    Calculate wind power output based on real-time wind speed data
    
    Args:
        timestamp: Current timestamp
        wind_speed: Current wind speed in m/s
        
    Returns:
        Wind power output in kW
    """
    # Get system settings
    system_settings = db.get_settings("system")
    wind_capacity = system_settings.get("wind_capacity", 3.0)  # Default 3kW system
    
    # Wind turbine power curve parameters
    cut_in_speed = 3.0  # m/s
    rated_speed = 12.0  # m/s
    cut_out_speed = 25.0  # m/s
    
    # Calculate power output
    if wind_speed < cut_in_speed or wind_speed > cut_out_speed:
        power_output = 0
    elif wind_speed >= rated_speed:
        power_output = wind_capacity
    else:
        # Cubic relationship between wind speed and power
        power_output = wind_capacity * ((wind_speed - cut_in_speed) / (rated_speed - cut_in_speed)) ** 3
    
    # Ensure power output is within system capacity
    power_output = min(power_output, wind_capacity)
    
    return max(0, power_output)  # Ensure non-negative power output


def get_battery_data(current_time: datetime.datetime, 
                     solar_power: float, 
                     wind_power: float, 
                     load: float, 
                     previous_soc: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate battery state based on energy generation and consumption
    
    Args:
        current_time: Current datetime
        solar_power: Solar power generation in kW
        wind_power: Wind power generation in kW
        load: Current power load in kW
        previous_soc: Previous state of charge (0-100%)
        
    Returns:
        Dict with battery data
    """
    # Battery specs
    battery_capacity = 20.0  # kWh
    max_charging_rate = 5.0  # kW
    max_voltage = 48.0  # Volts
    min_voltage = 42.0  # Volts
    
    # Calculate power balance
    total_generation = solar_power + wind_power
    power_balance = total_generation - load  # Positive means charging, negative means discharging
    
    # If first time running or no previous SoC
    if previous_soc is None:
        soc = 70.0  # Default starting SoC
    else:
        soc = previous_soc
        
        # Update SoC based on power balance (simple model)
        time_factor = 1/60  # Assuming this runs every minute, 1/60 hr
        energy_change = power_balance * time_factor  # kWh
        soc_change = (energy_change / battery_capacity) * 100  # percentage points
        soc += soc_change
        
        # Clamp SoC between 0-100%
        soc = max(0, min(100, soc))
    
    # Calculate voltage (simple linear model)
    voltage = min_voltage + (max_voltage - min_voltage) * (soc / 100.0)
    
    # Calculate current
    if power_balance >= 0:
        current = min(power_balance, max_charging_rate) / voltage  # Charging (positive)
    else:
        current = power_balance / voltage  # Discharging (negative)
    
    # Temperature model: slightly higher when charging/discharging heavily
    temperature = 25.0 + abs(current) * 0.5
    
    # Health metrics
    cycle_count = int(current_time.timestamp() / 86400) % 1000  # Just a placeholder
    health_pct = 100 - (cycle_count / 20)
    
    return {
        "soc": soc,
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "cycle_count": cycle_count,
        "health_pct": health_pct,
        "charging": power_balance > 0
    }


def get_load_data(time: datetime.datetime, base_load: float = 2.0, noise: float = 0.5) -> float:
    """
    Generate simulated load data based on time of day
    
    Args:
        time: Current datetime
        base_load: Base load in kW
        noise: Random noise factor
        
    Returns:
        Simulated load in kW
    """
    hour = time.hour
    
    # Morning peak (7-9am)
    if 7 <= hour <= 9:
        load_factor = 1.5
    # Evening peak (6-10pm)
    elif 18 <= hour <= 22:
        load_factor = 1.8
    # Night (reduced)
    elif hour < 6 or hour > 22:
        load_factor = 0.6
    # Normal daytime
    else:
        load_factor = 1.0
    
    # Calculate load with some randomness
    load = base_load * load_factor * (1 + np.random.normal(0, noise/base_load))
    return max(0.1, load)


def get_environmental_data(time: datetime.datetime) -> Dict[str, float]:
    """
    Generate simulated environmental data
    
    Args:
        time: Current datetime
        
    Returns:
        Dict with environmental data
    """
    hour = time.hour + time.minute / 60.0
    
    # Solar irradiance follows similar pattern to solar power
    if 6 <= hour <= 18:
        normalized_hour = (hour - 6) / 12.0
        irradiance = 1000 * np.sin(normalized_hour * np.pi)
        irradiance += np.random.normal(0, 50)
        irradiance = max(0, irradiance)
    else:
        irradiance = 0.0
    
    # Wind speed with daily pattern
    if hour < 12:
        base_wind = 3.0 + (12 - hour) / 4
    else:
        base_wind = 3.0 + (hour - 12) / 6
    
    wind_speed = base_wind * (0.8 + 0.4 * np.random.random())
    
    # Temperature with daily pattern
    temp_base = 20  # Base temperature
    temp_variation = 10  # Daily variation
    if 6 <= hour <= 14:
        temp_factor = (hour - 6) / 8
    elif 14 < hour <= 22:
        temp_factor = (22 - hour) / 8
    else:
        temp_factor = 0
    
    temperature = temp_base + temp_variation * temp_factor
    temperature += np.random.normal(0, 1.5)  # Add some randomness
    
    return {
        "irradiance": irradiance,  # W/m²
        "wind_speed": wind_speed,  # m/s
        "temperature": temperature  # °C
    }


def get_system_alerts(solar_power: float, wind_power: float, battery_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate system alerts based on current system status
    
    Args:
        solar_power: Current solar power in kW
        wind_power: Current wind power in kW
        battery_data: Battery status data
        
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    # Check battery status
    if battery_data["soc"] < 20:
        alerts.append({
            "type": "warning",
            "component": "battery",
            "message": f"Low battery level: {battery_data['soc']:.1f}%",
            "severity": "high" if battery_data["soc"] < 10 else "medium"
        })
    
    if battery_data["temperature"] > 35:
        alerts.append({
            "type": "warning",
            "component": "battery",
            "message": f"High battery temperature: {battery_data['temperature']:.1f}°C",
            "severity": "high" if battery_data["temperature"] > 40 else "medium"
        })
    
    # Check solar and wind output
    daytime = 6 <= datetime.datetime.now().hour <= 18
    if daytime and solar_power < 0.5:
        alerts.append({
            "type": "info",
            "component": "solar",
            "message": "Low solar output during daytime",
            "severity": "low"
        })
    
    if wind_power < 0.2:
        alerts.append({
            "type": "info",
            "component": "wind",
            "message": "Low wind power output",
            "severity": "low"
        })
    
    return alerts


def get_weather_forecast() -> List[Dict[str, Any]]:
    """
    Generate simulated weather forecast for next 5 days
    
    Returns:
        List of forecast dictionaries
    """
    forecast = []
    base_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for day in range(5):
        date = base_date + datetime.timedelta(days=day)
        
        # Randomize conditions
        conditions = np.random.choice(
            ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Windy"],
            p=[0.4, 0.3, 0.15, 0.1, 0.05]
        )
        
        # Base temperature with slight rising trend
        temp_high = 22 + day * 0.5 + np.random.uniform(-3, 3)
        temp_low = temp_high - 8 + np.random.uniform(-2, 2)
        
        # Wind speed with more randomness
        wind_speed = 3 + np.random.uniform(-1, 5)
        
        # Solar irradiance based on conditions
        if conditions == "Sunny":
            irradiance_factor = 0.9 + np.random.uniform(0, 0.1)
        elif conditions == "Partly Cloudy":
            irradiance_factor = 0.6 + np.random.uniform(0, 0.2)
        elif conditions == "Cloudy":
            irradiance_factor = 0.3 + np.random.uniform(0, 0.2)
        else:
            irradiance_factor = 0.1 + np.random.uniform(0, 0.2)
        
        max_irradiance = 1000 * irradiance_factor
        
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][date.weekday()],
            "conditions": conditions,
            "temp_high": temp_high,
            "temp_low": temp_low,
            "wind_speed": wind_speed,
            "max_irradiance": max_irradiance,
            "solar_potential": "High" if max_irradiance > 700 else "Medium" if max_irradiance > 400 else "Low",
            "wind_potential": "High" if wind_speed > 6 else "Medium" if wind_speed > 3 else "Low"
        })
    
    return forecast


def get_status_color(value: float, thresholds: Dict[str, Tuple[float, float]]) -> str:
    """
    Get color based on value and thresholds
    
    Args:
        value: The value to evaluate
        thresholds: Dict with color keys and (min, max) value tuples
        
    Returns:
        Color string
    """
    for color, (min_val, max_val) in thresholds.items():
        if min_val <= value <= max_val:
            return color
    return "gray"


def format_power(power: float) -> str:
    """Format power value with appropriate unit (W or kW)"""
    if power < 1:
        return f"{power * 1000:.0f} W"
    return f"{power:.2f} kW"
