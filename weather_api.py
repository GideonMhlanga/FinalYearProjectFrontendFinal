import requests
import datetime
import json
import os
import numpy as np
from typing import Dict, List, Any, Optional

class ZimbabweWeatherAPI:
    """
    Client for accessing Zimbabwe weather forecast data
    This class interfaces with a Zimbabwean weather service API
    """
    def __init__(self):
        self.api_base_url = "https://weatherapi-zimbabwe.example.com/api/v1"
        self.api_key = os.environ.get("ZIMBABWE_WEATHER_API_KEY", "")
        self.locations = {
            "Harare": {"lat": -17.8292, "lon": 31.0522},
            "Bulawayo": {"lat": -20.1325, "lon": 28.6240},
            "Mutare": {"lat": -18.9707, "lon": 32.6709},
            "Gweru": {"lat": -19.5170, "lon": 29.8149},
            "Kadoma": {"lat": -18.3342, "lon": 29.9151},
            "Kwekwe": {"lat": -18.9282, "lon": 29.8149},
            "Chinhoyi": {"lat": -17.3671, "lon": 30.2059},
            "Masvingo": {"lat": -20.0624, "lon": 30.8277}
        }
        self.default_location = "Harare"
        
    def get_current_weather(self, location: str = None) -> Dict[str, Any]:
        """
        Get current weather for a location in Zimbabwe
        
        Args:
            location: City name in Zimbabwe (default: Harare)
            
        Returns:
            Dictionary with current weather data
        """
        location = location or self.default_location
        
        # Check if we have API key
        if not self.api_key:
            return self._generate_fallback_current_weather(location)
            
        # In a real implementation, we would make an API call here
        try:
            # Simulated API call - would be replaced with actual API request
            # response = requests.get(
            #    f"{self.api_base_url}/current",
            #    params={"location": location, "api_key": self.api_key}
            # )
            # response.raise_for_status()
            # return response.json()
            
            # For now, return simulated data
            return self._generate_fallback_current_weather(location)
        except Exception as e:
            print(f"Error fetching current weather: {e}")
            return self._generate_fallback_current_weather(location)
    
    def get_forecast(self, location: str = None, days: int = 5) -> List[Dict[str, Any]]:
        """
        Get weather forecast for a location in Zimbabwe
        
        Args:
            location: City name in Zimbabwe (default: Harare)
            days: Number of days for forecast (default: 5)
            
        Returns:
            List of dictionaries with forecast data
        """
        location = location or self.default_location
        
        # Check if we have API key
        if not self.api_key:
            return self._generate_fallback_forecast(location, days)
            
        # In a real implementation, we would make an API call here
        try:
            # Simulated API call - would be replaced with actual API request
            # response = requests.get(
            #    f"{self.api_base_url}/forecast",
            #    params={"location": location, "days": days, "api_key": self.api_key}
            # )
            # response.raise_for_status()
            # return response.json()
            
            # For now, return simulated data
            return self._generate_fallback_forecast(location, days)
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return self._generate_fallback_forecast(location, days)
    
    def _generate_fallback_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Generate fallback weather data for when API is unavailable
        
        Args:
            location: City name in Zimbabwe
            
        Returns:
            Dictionary with simulated current weather data
        """
        # Use the requested location's coordinates for more realistic simulation
        loc_data = self.locations.get(location, self.locations[self.default_location])
        
        # Base temperature varies by latitude (cooler in the south)
        base_temp = 26 - (loc_data["lat"] + 15) * 0.8
        
        # Current time in Zimbabwe
        now = datetime.datetime.now()
        hour = now.hour
        
        # Temperature varies by time of day
        if 6 <= hour <= 18:
            # Daytime temperature (peaks at noon)
            time_factor = 1 - abs((hour - 12) / 6)
            temp = base_temp + time_factor * 8
        else:
            # Nighttime temperature
            time_factor = abs((hour - 0 if hour < 6 else hour - 24) / 6)
            temp = base_temp - 5 + time_factor * 2
        
        # Add some randomness
        temp += np.random.normal(0, 1.5)
        
        # Determine weather condition based on temperature and randomness
        condition_options = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Thunderstorm"]
        condition_weights = [0.5, 0.25, 0.15, 0.07, 0.03]
        condition = np.random.choice(condition_options, p=condition_weights)
        
        # Wind speed (higher in more open areas, typically higher during daytime)
        wind_speed = 3 + 2 * time_factor + np.random.normal(0, 1)
        wind_speed = max(0.5, wind_speed)
        
        # Wind direction
        wind_directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        wind_direction = np.random.choice(wind_directions)
        
        # Humidity (higher at night and early morning, lower during day)
        if 10 <= hour <= 16:
            humidity = 40 + np.random.normal(0, 10)
        else:
            humidity = 65 + np.random.normal(0, 10)
        humidity = max(30, min(95, humidity))
        
        # Generate solar irradiance based on time and conditions
        if 6 <= hour <= 18:
            base_irradiance = 1000 * np.sin(((hour - 6) / 12) * np.pi)
            if condition == "Sunny":
                irradiance_factor = 1.0
            elif condition == "Partly Cloudy":
                irradiance_factor = 0.7
            elif condition == "Cloudy":
                irradiance_factor = 0.4
            else:
                irradiance_factor = 0.2
            irradiance = base_irradiance * irradiance_factor
        else:
            irradiance = 0
        
        return {
            "location": location,
            "timestamp": now.isoformat(),
            "temperature": round(temp, 1),
            "condition": condition,
            "wind_speed": round(wind_speed, 1),
            "wind_direction": wind_direction,
            "humidity": round(humidity, 1),
            "pressure": round(1013 + np.random.normal(0, 3), 1),
            "irradiance": round(irradiance, 1)
        }
    
    def _generate_fallback_forecast(self, location: str, days: int) -> List[Dict[str, Any]]:
        """
        Generate fallback forecast data for when API is unavailable
        
        Args:
            location: City name in Zimbabwe
            days: Number of days for forecast
            
        Returns:
            List of dictionaries with simulated forecast data
        """
        forecast = []
        base_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Use the requested location's coordinates
        loc_data = self.locations.get(location, self.locations[self.default_location])
        
        # Base temperature varies by latitude (cooler in the south)
        base_temp = 26 - (loc_data["lat"] + 15) * 0.8
        
        for day in range(days):
            date = base_date + datetime.timedelta(days=day)
            
            # Randomize conditions with some weather patterns
            # More likely to be sunny in dry season, rainy in wet season
            month = date.month
            
            # Zimbabwe rainy season: November to March
            if 11 <= month or month <= 3:
                # Rainy season probabilities
                condition_options = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Thunderstorm"]
                condition_weights = [0.2, 0.25, 0.25, 0.2, 0.1]
            else:
                # Dry season probabilities
                condition_options = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Thunderstorm"]
                condition_weights = [0.5, 0.3, 0.15, 0.04, 0.01]
                
            condition = np.random.choice(condition_options, p=condition_weights)
            
            # Temperature with slight variation day to day
            temp_high = base_temp + day * 0.2 + np.random.uniform(-2, 2)
            temp_low = temp_high - 10 + np.random.uniform(-2, 2)
            
            # Wind speed with more randomness
            wind_speed = 3 + np.random.uniform(-1, 5)
            
            # Humidity based on condition
            if condition in ["Light Rain", "Thunderstorm"]:
                humidity = 80 + np.random.uniform(-5, 15)
            elif condition == "Cloudy":
                humidity = 65 + np.random.uniform(-10, 15)
            elif condition == "Partly Cloudy":
                humidity = 50 + np.random.uniform(-10, 15)
            else:
                humidity = 40 + np.random.uniform(-10, 15)
            humidity = max(30, min(95, humidity))
            
            # Solar irradiance based on conditions
            if condition == "Sunny":
                irradiance_factor = 0.9 + np.random.uniform(0, 0.1)
            elif condition == "Partly Cloudy":
                irradiance_factor = 0.6 + np.random.uniform(0, 0.2)
            elif condition == "Cloudy":
                irradiance_factor = 0.3 + np.random.uniform(0, 0.2)
            else:
                irradiance_factor = 0.1 + np.random.uniform(0, 0.2)
            
            max_irradiance = 1000 * irradiance_factor
            
            # Generate weather forecast for the day
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][date.weekday()],
                "conditions": condition,
                "temp_high": round(temp_high, 1),
                "temp_low": round(temp_low, 1),
                "wind_speed": round(wind_speed, 1),
                "humidity": round(humidity, 1),
                "max_irradiance": round(max_irradiance, 1),
                "solar_potential": "High" if max_irradiance > 700 else "Medium" if max_irradiance > 400 else "Low",
                "wind_potential": "High" if wind_speed > 6 else "Medium" if wind_speed > 3 else "Low",
                "location": location
            })
        
        return forecast
        
    def get_available_locations(self) -> List[str]:
        """
        Get list of available locations in Zimbabwe
        
        Returns:
            List of location names 
        """
        return list(self.locations.keys())


# Singleton instance for use throughout the app
zimbabwe_weather = ZimbabweWeatherAPI()