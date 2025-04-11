import datetime
import time
import json
import os
import numpy as np
import pandas as pd
from utils import (
    get_solar_power, 
    get_wind_power, 
    get_battery_data, 
    get_load_data,
    get_environmental_data,
    get_system_alerts
)
from database import db
from weather_apis import weather_apis

class DataGenerator:
    """
    Simulates data for the solar-wind hybrid monitoring system
    """
    def __init__(self):
        self.data_history = {
            "timestamps": [],
            "solar_power": [],
            "wind_power": [],
            "load": [],
            "battery_soc": [],
            "battery_voltage": [],
            "battery_current": [],
            "battery_temperature": [],
            "irradiance": [],
            "wind_speed": [],
            "temperature": [],
            "total_generation": [],
            "net_power": []
        }
        self.settings = {
            "solar_priority": True,
            "max_battery_discharge": 80,
            "critical_loads_only": False
        }
        self.users = {
            "admin": {"password": "admin123", "role": "admin"},
            "user": {"password": "user123", "role": "user"},
            "guest": {"password": "guest", "role": "readonly"}
        }
        self.last_battery_soc = None
        self.alerts = []
        
    def generate_current_data(self):
        """Generate a snapshot of current system data"""
        current_time = datetime.datetime.now()
        
        # Get real-time solar irradiance data
        solar_data = weather_apis.get_solar_irradiance(current_time)
        irradiance = solar_data['ghi']  # Using Global Horizontal Irradiance
        
        # Get real-time wind speed data
        wind_data = weather_apis.get_wind_speed(current_time)
        wind_speed = wind_data['speed']
        
        # Get environmental data
        env_data = get_environmental_data(current_time)
        
        # Calculate power generation based on real data
        solar_power = get_solar_power(current_time, env_data["irradiance"])
        wind_power = get_wind_power(current_time, env_data["wind_speed"])
        load = get_load_data(current_time)
        
        # Get battery settings from database
        battery_settings = db.get_settings("battery")
        
        # Calculate battery status
        battery_data = get_battery_data(
            current_time, 
            solar_power, 
            wind_power, 
            load, 
            self.last_battery_soc
        )
        self.last_battery_soc = battery_data["soc"]
        
        # Get system alerts
        self.alerts = get_system_alerts(solar_power, wind_power, battery_data)
        
        # Calculate totals
        total_generation = solar_power + wind_power
        net_power = total_generation - load
        
        # Update data history (for in-memory display)
        self.data_history["timestamps"].append(current_time)
        self.data_history["solar_power"].append(solar_power)
        self.data_history["wind_power"].append(wind_power)
        self.data_history["load"].append(load)
        self.data_history["battery_soc"].append(battery_data["soc"])
        self.data_history["battery_voltage"].append(battery_data["voltage"])
        self.data_history["battery_current"].append(battery_data["current"])
        self.data_history["battery_temperature"].append(battery_data["temperature"])
        self.data_history["irradiance"].append(env_data["irradiance"])
        self.data_history["wind_speed"].append(env_data["wind_speed"])
        self.data_history["temperature"].append(env_data["temperature"])
        self.data_history["total_generation"].append(total_generation)
        self.data_history["net_power"].append(net_power)
        
        # Keep only the last 24 hours of data at minute resolution (for in-memory)
        max_history = 60 * 24  # 24 hours x 60 minutes
        if len(self.data_history["timestamps"]) > max_history:
            for key in self.data_history:
                self.data_history[key] = self.data_history[key][-max_history:]
        
        # Save data to database (for long-term storage)
        power_data = {
            "timestamp": current_time,
            "solar_power": solar_power,
            "wind_power": wind_power,
            "load": load,
            "battery_soc": battery_data["soc"],
            "battery_voltage": battery_data["voltage"],
            "battery_current": battery_data["current"],
            "battery_temperature": battery_data["temperature"],
            "irradiance": env_data["irradiance"],
            "wind_speed": env_data["wind_speed"],
            "temperature": env_data["temperature"]
        }
        db.save_power_data(power_data)
        
        # Save weather data to database
        weather_data = {
            "timestamp": current_time,
            "location": db.get_settings("location").get("name", "Harare"),
            "temperature": env_data["temperature"],
            "condition": "Real-time",  # Now using real-time data
            "wind_speed": env_data["wind_speed"],
            "wind_direction": wind_data.get('direction', 0),
            "humidity": wind_data.get('humidity', 50.0),
            "pressure": wind_data.get('pressure', 1013.0),
            "irradiance": env_data["irradiance"]
        }
        db.save_weather_data(weather_data)
        
        # Log alerts to database
        for alert in self.alerts:
            db.add_system_log(
                log_type="alert", 
                message=alert["message"], 
                details={"severity": alert["severity"], "source": alert["component"]}
            )
        
        # Return current snapshot
        return {
            "timestamp": current_time,
            "solar_power": solar_power,
            "wind_power": wind_power,
            "load": load,
            "battery": battery_data,
            "environmental": env_data,
            "alerts": self.alerts,
            "total_generation": total_generation,
            "net_power": net_power
        }
    
    def get_historical_data(self, timeframe="day"):
        """
        Get historical data for the specified timeframe
        
        Args:
            timeframe: 'day', 'week', or 'month'
            
        Returns:
            Pandas DataFrame with historical data
        """
        # Try to get data from database first
        df = db.get_power_data(timeframe)
        
        # If database doesn't have data yet, fall back to in-memory data
        if df.empty and self.data_history["timestamps"]:
            df = pd.DataFrame(self.data_history)
        
        # If we still don't have data, return empty DataFrame
        if df.empty:
            return df
        
        # For longer timeframes, downsample the data to reduce points
        if timeframe == "day":
            # For day view, use all data points (minute resolution)
            return df
        elif timeframe == "week" and len(df) > 168:  # More than a week of hourly data
            # For week view, downsample to hourly resolution
            # First ensure we have the right column name and it's a datetime index
            if "timestamp" in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            elif "timestamps" in df.columns:
                df['timestamps'] = pd.to_datetime(df['timestamps'])
                df.set_index('timestamps', inplace=True)
                
            resampled = df.resample('1H').mean()
            resampled.reset_index(inplace=True)
            return resampled
        elif timeframe == "month" and len(df) > 720:  # More than a month of hourly data
            # For month view, downsample to daily resolution
            # First ensure we have the right column name and it's a datetime index
            if "timestamp" in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            elif "timestamps" in df.columns:
                df['timestamps'] = pd.to_datetime(df['timestamps'])
                df.set_index('timestamps', inplace=True)
                
            resampled = df.resample('1D').mean()
            resampled.reset_index(inplace=True)
            return resampled
        
        return df
    
    def get_energy_summary(self):
        """Calculate energy summary stats"""
        if not self.data_history["timestamps"]:
            return {
                "solar_energy": 0,
                "wind_energy": 0,
                "total_energy": 0,
                "load_energy": 0,
                "solar_percentage": 50,
                "wind_percentage": 50
            }
        
        # Calculate energy in kWh (assuming data points are 1 minute apart)
        df = pd.DataFrame(self.data_history)
        
        # Convert power (kW) to energy (kWh) - each reading represents 1 minute = 1/60 hour
        time_factor = 1/60
        solar_energy = sum(df["solar_power"]) * time_factor
        wind_energy = sum(df["wind_power"]) * time_factor
        total_energy = solar_energy + wind_energy
        load_energy = sum(df["load"]) * time_factor
        
        # Calculate percentages
        if total_energy > 0:
            solar_percentage = (solar_energy / total_energy) * 100
            wind_percentage = (wind_energy / total_energy) * 100
        else:
            solar_percentage = 50
            wind_percentage = 50
        
        return {
            "solar_energy": solar_energy,
            "wind_energy": wind_energy,
            "total_energy": total_energy,
            "load_energy": load_energy,
            "solar_percentage": solar_percentage,
            "wind_percentage": wind_percentage
        }
    
    def update_settings(self, settings):
        """Update system settings"""
        # Update in-memory settings
        self.settings.update(settings)
        
        # Update database settings
        # Determine which settings category to update based on keys
        if "capacity" in settings or "charge_rate" in settings or "chemistry" in settings:
            # Battery settings
            current_battery = db.get_settings("battery")
            current_battery.update(settings)
            db.update_settings("battery", current_battery)
        elif "solar_capacity" in settings or "wind_capacity" in settings:
            # System settings
            current_system = db.get_settings("system")
            current_system.update(settings)
            db.update_settings("system", current_system)
        else:
            # General settings
            db.update_settings("operational", settings)
        
        return self.settings
    
    def get_settings(self):
        """Get current system settings"""
        # Get all settings from database and merge with in-memory settings
        db_settings = db.get_settings()
        
        # Merge database settings with in-memory settings (in-memory takes precedence)
        combined = {}
        for key, value in db_settings.items():
            if isinstance(value, dict):
                combined.update(value)
        
        # Override with in-memory settings
        combined.update(self.settings)
        
        return combined
    
    def get_weather_forecast(self, location=None):
        """
        Get weather forecast data from Zimbabwe Weather API
        
        Args:
            location: Optional location name in Zimbabwe
            
        Returns:
            List of forecast dictionaries
        """
        from weather_api import zimbabwe_weather
        return zimbabwe_weather.get_forecast(location)
    
    def authenticate_user(self, username, password):
        """
        Authenticate user credentials
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            Dict with authentication result including user details
        """
        # Use database authentication
        result = db.authenticate_user(username, password)
        
        # If database authentication fails, try in-memory users as fallback
        if not result["authenticated"] and username in self.users:
            if self.users[username]["password"] == password:
                result = {
                    "authenticated": True, 
                    "role": self.users[username]["role"],
                    "user": {
                        "username": username,
                        "role": self.users[username]["role"]
                    }
                }
        
        # Record successful login in the database
        if result["authenticated"]:
            db.record_user_login(username)
            
        return result
    
    def get_users(self):
        """
        Get all users with their details
        
        Returns:
            Dict with username keys and user details
        """
        # Get users from database
        db_users = db.get_users()
        
        # Format database users to match expected output format
        users_dict = {}
        for user in db_users:
            users_dict[user["username"]] = {
                "role": user["role"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
                "address": user.get("address", ""),
                "created_at": user.get("created_at", ""),
                "last_login": user.get("last_login", "")
            }
        
        # Add in-memory users (for backwards compatibility)
        for username, data in self.users.items():
            if username not in users_dict:
                users_dict[username] = {"role": data["role"]}
        
        return users_dict
        
    def get_user_profile(self, username):
        """
        Get a specific user's profile information
        
        Args:
            username: Username to retrieve profile for
            
        Returns:
            Dict with user profile information
        """
        return db.get_user_profile(username)
        
    def update_user_profile(self, username, profile_data):
        """
        Update a user's profile information
        
        Args:
            username: Username of user to update
            profile_data: Dict with profile fields to update
            
        Returns:
            Boolean indicating success
        """
        return db.update_user_profile(username, profile_data)
    
    def get_predictive_maintenance(self, component=None):
        """
        Get predictive maintenance data for components
        
        Args:
            component: Optional component name to filter by
            
        Returns:
            List of predictive maintenance data dictionaries
        """
        return db.get_predictive_maintenance(component)
    
    def get_component_health(self):
        """
        Get current health status of all components
        
        Returns:
            Dict with component health information
        """
        return db.get_component_health()
    
    def generate_predictive_analysis(self, component):
        """
        Generate predictive maintenance analysis for a component
        
        Args:
            component: Component name to analyze (solar_panel, wind_turbine, battery, inverter, etc.)
            
        Returns:
            Dict with predictive maintenance data
        """
        # Get historical data to analyze
        df = db.get_power_data(timeframe="month")
        
        # Calculate health score based on component type
        now = datetime.datetime.now()
        
        # Default values
        health_score = 0
        failure_days = 0
        recommendation = ""
        confidence = 0
        maintenance_cost = 0
        failure_cost = 0
        analysis_data = {}
        maintenance_recommended = False
        
        if component == "solar_panel":
            # Calculate health based on solar power efficiency
            if not df.empty and "solar_power" in df.columns and "irradiance" in df.columns:
                # Filter out night time (irradiance close to 0)
                day_data = df[df["irradiance"] > 50]
                
                if not day_data.empty:
                    # Calculate expected vs actual power ratio
                    # Expected: 1kW per 1000 W/m² for a 1kW system
                    system_capacity = db.get_settings("system").get("solar_capacity", 5.0)
                    expected_ratio = system_capacity / 1000
                    
                    day_data["expected_power"] = day_data["irradiance"] * expected_ratio
                    day_data["efficiency_ratio"] = day_data["solar_power"] / day_data["expected_power"]
                    
                    # Remove outliers
                    day_data = day_data[day_data["efficiency_ratio"] < 2]  # Remove extreme outliers
                    
                    avg_efficiency = day_data["efficiency_ratio"].mean() * 100  # as percentage
                    efficiency_std = day_data["efficiency_ratio"].std() * 100
                    
                    # Map average efficiency to health score (0-100)
                    # Typical solar panel degradation is 0.5-1% per year
                    # New panel: ~100% efficiency, End of life: ~80% efficiency
                    health_score = min(100, max(0, avg_efficiency))
                    
                    # Predict days until failure (efficiency < 80%)
                    if avg_efficiency > 80:
                        # Estimate degradation rate (% per day)
                        # Use historical data to estimate if enough data points
                        if len(day_data) > 30:
                            # Use linear regression on data points
                            earliest_date = day_data["timestamp"].min()
                            days_span = (day_data["timestamp"].max() - earliest_date).total_seconds() / (24*3600)
                            if days_span > 0:
                                # Group by day and calculate average efficiency
                                day_data["day"] = day_data["timestamp"].dt.date
                                daily_efficiency = day_data.groupby("day")["efficiency_ratio"].mean()
                                
                                if len(daily_efficiency) > 5:
                                    # Simple linear regression
                                    x = np.arange(len(daily_efficiency))
                                    y = daily_efficiency.values
                                    slope, intercept = np.polyfit(x, y, 1)
                                    
                                    # Calculate days until efficiency < 0.8
                                    if slope < 0:  # Only if degrading
                                        days_to_failure = int((0.8 - intercept) / slope) if slope != 0 else 3650
                                        failure_days = min(3650, max(0, days_to_failure))  # Cap at 10 years
                                    else:
                                        failure_days = 3650  # 10 years if not degrading
                                else:
                                    failure_days = 3650  # Not enough daily data points
                            else:
                                failure_days = 3650  # Not enough time span
                        else:
                            # Use standard degradation rate if not enough data
                            # 0.5% degradation per year = 0.00137% per day
                            failure_days = int((avg_efficiency - 80) / 0.00137) if avg_efficiency > 80 else 0
                    else:
                        failure_days = 0  # Already below threshold
                    
                    # Set confidence based on data quality
                    if len(day_data) > 90:  # 3 months of data
                        confidence = 0.85
                    elif len(day_data) > 30:  # 1 month of data
                        confidence = 0.7
                    else:
                        confidence = 0.5
                    
                    # Determine if maintenance is recommended
                    if health_score < 85:
                        maintenance_recommended = True
                        recommendation = "Clean solar panels and check for physical damage or shading issues."
                    elif health_score < 90:
                        maintenance_recommended = True
                        recommendation = "Inspect solar panels for dust accumulation or partial shading."
                    
                    # Set maintenance and failure costs
                    maintenance_cost = system_capacity * 50  # $50 per kW for cleaning/inspection
                    failure_cost = system_capacity * 250  # $250 per kW for major repairs
                    
                    # Store detailed analysis data
                    analysis_data = {
                        "avg_efficiency": avg_efficiency,
                        "efficiency_std": efficiency_std,
                        "data_points": len(day_data),
                        "system_capacity": system_capacity
                    }
        
        elif component == "wind_turbine":
            # Calculate health based on wind power performance
            if not df.empty and "wind_power" in df.columns and "wind_speed" in df.columns:
                # Filter for wind speeds in operational range (typically 3-25 m/s)
                wind_data = df[(df["wind_speed"] >= 3.0) & (df["wind_speed"] <= 25.0)]
                
                if not wind_data.empty:
                    # Calculate expected vs actual power ratio
                    # Power output should follow a cubic relationship with wind speed
                    # P = 0.5 * air_density * swept_area * Cp * V^3
                    # Simplify by using the rated capacity and rated wind speed
                    system_capacity = db.get_settings("system").get("wind_capacity", 3.0)
                    rated_wind_speed = 12.0  # typical rated wind speed in m/s
                    
                    # Calculate expected power at each wind speed (simplified model)
                    wind_data["expected_power"] = system_capacity * (wind_data["wind_speed"]**3) / (rated_wind_speed**3)
                    wind_data["expected_power"] = wind_data["expected_power"].clip(upper=system_capacity)  # Cap at rated capacity
                    
                    wind_data["performance_ratio"] = wind_data["wind_power"] / wind_data["expected_power"]
                    
                    # Remove outliers
                    wind_data = wind_data[wind_data["performance_ratio"] < 2]  # Remove extreme outliers
                    
                    avg_performance = wind_data["performance_ratio"].mean() * 100  # as percentage
                    performance_std = wind_data["performance_ratio"].std() * 100
                    
                    # Map average performance to health score (0-100)
                    health_score = min(100, max(0, avg_performance))
                    
                    # Predict days until failure (performance < 70%)
                    if avg_performance > 70:
                        # Similar approach as solar, but wind turbines typically degrade faster
                        # Use simplified approach with standard degradation rate
                        # 2% degradation per year = 0.00548% per day
                        failure_days = int((avg_performance - 70) / 0.00548) if avg_performance > 70 else 0
                    else:
                        failure_days = 0  # Already below threshold
                    
                    # Set confidence based on data quality
                    if len(wind_data) > 90:  # 3 months of data with sufficient wind
                        confidence = 0.8
                    elif len(wind_data) > 30:  # 1 month of data
                        confidence = 0.65
                    else:
                        confidence = 0.45
                    
                    # Determine if maintenance is recommended
                    if health_score < 75:
                        maintenance_recommended = True
                        recommendation = "Perform full inspection of wind turbine, check bearings, blades and generator."
                    elif health_score < 85:
                        maintenance_recommended = True
                        recommendation = "Inspect wind turbine for blade imbalance or mechanical issues."
                    
                    # Set maintenance and failure costs
                    maintenance_cost = system_capacity * 80  # $80 per kW for inspection/minor repairs
                    failure_cost = system_capacity * 400  # $400 per kW for major repairs
                    
                    # Store detailed analysis data
                    analysis_data = {
                        "avg_performance": avg_performance,
                        "performance_std": performance_std,
                        "data_points": len(wind_data),
                        "system_capacity": system_capacity
                    }
        
        elif component == "battery":
            # Calculate health based on battery performance
            if not df.empty and "battery_soc" in df.columns and "battery_voltage" in df.columns:
                # Check voltage vs SOC relationship and charging/discharging efficiency
                
                # Get battery cycle count
                current_data = self.generate_current_data()
                cycle_count = current_data["battery"]["cycle_count"]
                
                # Get battery settings
                battery_settings = db.get_settings("battery")
                capacity = battery_settings.get("capacity", 10.0)
                chemistry = battery_settings.get("chemistry", "Lithium Ion")
                
                # Different battery chemistries have different cycle life expectations
                expected_cycles = 3000 if chemistry == "Lithium Iron Phosphate" else 2000
                
                # Calculate remaining cycle life as a percentage
                cycle_life_pct = max(0, min(100, 100 * (1 - (cycle_count / expected_cycles))))
                
                # Analyze voltage performance
                df_discharging = df[df["battery_current"] < 0]
                df_charging = df[df["battery_current"] > 0]
                
                voltage_health = 100
                efficiency_health = 100
                
                if not df_discharging.empty and not df_charging.empty:
                    # Calculate voltage sag during discharge
                    soc_80_voltage = df_discharging[df_discharging["battery_soc"] >= 80]["battery_voltage"].mean()
                    soc_20_voltage = df_discharging[df_discharging["battery_soc"] <= 20]["battery_voltage"].mean()
                    
                    if not (np.isnan(soc_80_voltage) or np.isnan(soc_20_voltage)):
                        voltage_drop = soc_80_voltage - soc_20_voltage
                        
                        # Check if voltage drop is within expected range
                        # For a 48V system, we'd expect a drop of around 4-6V
                        nominal_voltage = 48
                        expected_drop = nominal_voltage * 0.1  # 10% drop is normal
                        
                        # Calculate voltage health based on voltage drop
                        voltage_drop_ratio = min(2, voltage_drop / expected_drop)
                        voltage_health = max(0, 100 - (voltage_drop_ratio - 1) * 100) if voltage_drop_ratio > 1 else 100
                    
                    # Calculate charging efficiency
                    charge_energy = (df_charging["battery_current"] * df_charging["battery_voltage"]).sum()
                    discharge_energy = (df_discharging["battery_current"].abs() * df_discharging["battery_voltage"]).sum()
                    
                    if charge_energy > 0 and discharge_energy > 0:
                        efficiency = (discharge_energy / charge_energy) * 100
                        
                        # Good efficiency is typically 90-95% for lithium batteries
                        if efficiency < 80:
                            efficiency_health = max(0, (efficiency / 80) * 100)
                
                # Combine factors with appropriate weights
                health_score = (cycle_life_pct * 0.5) + (voltage_health * 0.3) + (efficiency_health * 0.2)
                
                # Predict days until failure
                if health_score > 50:
                    # Estimate days to failure based on current degradation rate
                    # For simplicity, use cycle count as the main indicator
                    remaining_cycles = expected_cycles - cycle_count
                    
                    # Estimate cycles per day from recent data
                    days_span = (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / (24*3600)
                    if days_span > 0:
                        # Rough estimate of cycles: significant discharge/charge events
                        soc_changes = df["battery_soc"].diff().abs().sum() / 100
                        cycles_per_day = soc_changes / days_span
                        
                        if cycles_per_day > 0:
                            failure_days = int(remaining_cycles / cycles_per_day)
                        else:
                            failure_days = 1825  # Default to 5 years if can't determine
                    else:
                        failure_days = 1825  # Default to 5 years
                else:
                    failure_days = 0
                
                # Set confidence
                confidence = 0.75  # Battery predictions are generally reliable if we have cycle data
                
                # Recommendations
                if health_score < 70:
                    maintenance_recommended = True
                    recommendation = "Plan for battery replacement. Battery health is significantly degraded."
                elif health_score < 85:
                    maintenance_recommended = True
                    recommendation = "Review charging patterns and optimize battery usage to extend life."
                
                # Costs 
                maintenance_cost = capacity * 20  # $20 per kWh for maintenance
                failure_cost = capacity * 500  # $500 per kWh for replacement
                
                # Analysis data
                analysis_data = {
                    "cycle_count": cycle_count,
                    "expected_cycles": expected_cycles,
                    "capacity": capacity,
                    "chemistry": chemistry,
                    "cycle_life_pct": cycle_life_pct,
                    "voltage_health": voltage_health,
                    "efficiency_health": efficiency_health
                }
                
        elif component == "inverter":
            # Simplified inverter health analysis
            if not df.empty:
                # Calculate conversion efficiency over time
                system_settings = db.get_settings("system")
                
                # Inverter health is often related to heat dissipation and component wear
                # We can use the temperature data as one indicator
                avg_temp = df["temperature"].mean() if "temperature" in df.columns else 25
                
                # Age-based degradation (assume 10-year lifespan)
                # We would typically get this from a commissioning date
                estimated_age_days = 365  # Assume 1 year old for demonstration
                age_factor = max(0, min(100, 100 * (1 - (estimated_age_days / 3650))))
                
                # Temperature stress factor
                temp_stress = max(0, min(100, 100 - (max(0, avg_temp - 25) * 2)))
                
                # Combine factors
                health_score = (age_factor * 0.7) + (temp_stress * 0.3)
                
                # Predict days until failure
                if health_score > 50:
                    failure_days = int((3650 - estimated_age_days) * (health_score / 100))
                else:
                    failure_days = 0
                
                # Confidence
                confidence = 0.6  # Inverter predictions are less reliable without component-level monitoring
                
                # Recommendations
                if health_score < 75:
                    maintenance_recommended = True
                    recommendation = "Schedule inverter inspection, check cooling systems and capacitors."
                elif health_score < 85:
                    maintenance_recommended = False
                    recommendation = "Monitor inverter performance and ensure adequate ventilation."
                
                # Costs (based on system capacity)
                system_capacity = system_settings.get("solar_capacity", 5.0) + system_settings.get("wind_capacity", 3.0)
                maintenance_cost = system_capacity * 30  # $30 per kW
                failure_cost = system_capacity * 150  # $150 per kW
                
                # Analysis data
                analysis_data = {
                    "avg_temperature": avg_temp,
                    "estimated_age_days": estimated_age_days,
                    "age_factor": age_factor,
                    "temp_stress": temp_stress,
                    "system_capacity": system_capacity
                }
        
        # Create predictive maintenance record
        prediction = {
            "timestamp": now,
            "component": component,
            "health_score": health_score,
            "predicted_failure_date": now + datetime.timedelta(days=failure_days) if failure_days > 0 else None,
            "maintenance_recommended": maintenance_recommended,
            "recommendation": recommendation,
            "confidence": confidence,
            "analysis_data": analysis_data,
            "maintenance_cost": maintenance_cost,
            "failure_cost": failure_cost
        }
        
        # Save prediction to database
        db.save_predictive_maintenance(prediction)
        
        return prediction
    
    def add_user(self, username, password, role):
        """Add a new user"""
        # Add user to database
        success = db.add_user(username, password, role)
        
        # If successful, also add to in-memory users for backwards compatibility
        if success:
            self.users[username] = {"password": password, "role": role}
            # Log the user creation
            db.add_system_log(
                log_type="info",
                message=f"User '{username}' created with role '{role}'",
                details={"action": "user_create"}
            )
        
        return success
    
    def delete_user(self, username):
        """Delete a user"""
        # Delete user from database
        success = db.delete_user(username)
        
        # If successful, also remove from in-memory users
        if success and username in self.users:
            del self.users[username]
            # Log the user deletion
            db.add_system_log(
                log_type="info",
                message=f"User '{username}' deleted",
                details={"action": "user_delete"}
            )
        
        return success
    
    def get_system_anomalies(self, timeframe="day"):
        """
        Get system anomalies for the given timeframe
        
        Args:
            timeframe: 'day', 'week', or 'month'
            
        Returns:
            Dict with anomalies by category and summary information
        """
        try:
            # Import here to avoid circular imports
            from anomaly_detection import detect_anomalies, get_anomaly_summary
            
            # Get historical data for analysis
            historical_data = self.get_historical_data(timeframe)
            
            if historical_data.empty:
                return {"anomalies": {}, "summary": {"total": 0, "severe": 0, "moderate": 0, "mild": 0}}
            
            # Get recent data for anomaly detection
            if timeframe == "day":
                data_to_analyze = historical_data
            else:
                # For longer timeframes, just analyze the most recent day
                data_to_analyze = historical_data.tail(48)  # Last 48 hours
            
            # Run anomaly detection
            anomalies = detect_anomalies(
                data=data_to_analyze,
                use_statistical=True,
                use_rule_based=True,
                use_ml=len(data_to_analyze) >= 10,  # Only use ML if we have enough data
                window_size=24
            )
            
            # Get summary statistics
            summary = get_anomaly_summary(anomalies)
            
            return {
                "anomalies": anomalies,
                "summary": summary
            }
        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return {"anomalies": {}, "summary": {"total": 0, "severe": 0, "moderate": 0, "mild": 0}}
    
    def seed_historical_data(self, days=1):
        """
        Seed historical data for a specified number of days
        Note: This is used for development/testing only
        """
        # Clear existing data
        for key in self.data_history:
            self.data_history[key] = []
            
        # Log database seeding
        db.add_system_log(
            log_type="info",
            message=f"Seeding historical data for {days} days",
            details={"action": "seed_data"}
        )
            
        # Start from days ago
        start_time = datetime.datetime.now() - datetime.timedelta(days=days)
        current_time = start_time
        
        # Default location from database
        location = db.get_settings("location").get("name", "Harare")
        
        # Generate data at 15-minute intervals
        while current_time < datetime.datetime.now():
            # Get environmental data first
            env_data = get_environmental_data(current_time)
            
            # Calculate power generation
            solar_power = get_solar_power(current_time, env_data["irradiance"])
            wind_power = get_wind_power(current_time, env_data["wind_speed"])
            load = get_load_data(current_time)
            
            # Calculate battery status
            battery_data = get_battery_data(
                current_time, 
                solar_power, 
                wind_power, 
                load, 
                self.last_battery_soc
            )
            self.last_battery_soc = battery_data["soc"]
            
            # Calculate totals
            total_generation = solar_power + wind_power
            net_power = total_generation - load
            
            # Update data history (in-memory)
            self.data_history["timestamps"].append(current_time)
            self.data_history["solar_power"].append(solar_power)
            self.data_history["wind_power"].append(wind_power)
            self.data_history["load"].append(load)
            self.data_history["battery_soc"].append(battery_data["soc"])
            self.data_history["battery_voltage"].append(battery_data["voltage"])
            self.data_history["battery_current"].append(battery_data["current"])
            self.data_history["battery_temperature"].append(battery_data["temperature"])
            self.data_history["irradiance"].append(env_data["irradiance"])
            self.data_history["wind_speed"].append(env_data["wind_speed"])
            self.data_history["temperature"].append(env_data["temperature"])
            self.data_history["total_generation"].append(total_generation)
            self.data_history["net_power"].append(net_power)
            
            # Save to database (only save every hour to avoid too many records)
            if current_time.minute == 0 or (current_time.minute % 15 == 0 and days <= 1):
                # Save power data
                power_data = {
                    "timestamp": current_time,
                    "solar_power": solar_power,
                    "wind_power": wind_power,
                    "load": load,
                    "battery_soc": battery_data["soc"],
                    "battery_voltage": battery_data["voltage"],
                    "battery_current": battery_data["current"],
                    "battery_temperature": battery_data["temperature"],
                    "irradiance": env_data["irradiance"],
                    "wind_speed": env_data["wind_speed"],
                    "temperature": env_data["temperature"]
                }
                db.save_power_data(power_data)
                
                # Save weather data
                weather_data = {
                    "timestamp": current_time,
                    "location": location,
                    "temperature": env_data["temperature"],
                    "condition": "Simulated",
                    "wind_speed": env_data["wind_speed"],
                    "wind_direction": "N",
                    "humidity": 50.0,
                    "pressure": 1013.0,
                    "irradiance": env_data["irradiance"]
                }
                db.save_weather_data(weather_data)
            
            # Increment time by 15 minutes
            current_time += datetime.timedelta(minutes=15)
        
        # Add system log for completion
        db.add_system_log(
            log_type="info",
            message=f"Historical data seeding completed with {len(self.data_history['timestamps'])} records",
            details={"action": "seed_data_complete"}
        )

# Create a global instance that will be shared across pages
data_generator = DataGenerator()

# Seed some historical data for development purposes
data_generator.seed_historical_data(days=1)
