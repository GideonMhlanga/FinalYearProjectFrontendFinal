import requests
import datetime
import pandas as pd
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WeatherAPIs:
    """
    Class to handle various weather and environmental data APIs
    """
    
    def __init__(self):
        # Initialize API keys from environment variables
        self.solar_api_key = os.getenv('SOLAR_API_KEY')
        self.wind_api_key = os.getenv('WIND_API_KEY')
        self.location = os.getenv('LOCATION', 'Bulawayo')
        self.latitude = os.getenv('LATITUDE', '-20.1325')
        self.longitude = os.getenv('LONGITUDE', '28.6264')
        
    def get_solar_irradiance(self, timestamp: datetime.datetime) -> Dict[str, float]:
        """
        Get solar irradiance data from a solar irradiance API
        
        Args:
            timestamp: The datetime to get data for
            
        Returns:
            Dict with solar irradiance data
        """
        try:
            # Example using Solcast API (you'll need to sign up for an API key)
            # This is a placeholder - replace with actual API call
            url = f"https://api.solcast.com.au/radiation/forecasts"
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'api_key': self.solar_api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process the API response
            # This is an example - adjust based on actual API response structure
            irradiance_data = {
                'ghi': data.get('ghi', 0),  # Global Horizontal Irradiance
                'dni': data.get('dni', 0),  # Direct Normal Irradiance
                'dhi': data.get('dhi', 0),  # Diffuse Horizontal Irradiance
                'timestamp': timestamp
            }
            
            return irradiance_data
            
        except Exception as e:
            print(f"Error getting solar irradiance data: {e}")
            # Return default values if API fails
            return {
                'ghi': 0,
                'dni': 0,
                'dhi': 0,
                'timestamp': timestamp
            }
    
    def get_wind_speed(self, timestamp: datetime.datetime) -> Dict[str, float]:
        """
        Get wind speed data from a wind data API
        
        Args:
            timestamp: The datetime to get data for
            
        Returns:
            Dict with wind speed data
        """
        try:
            # Example using OpenWeatherMap API (you'll need to sign up for an API key)
            # This is a placeholder - replace with actual API call
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.wind_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process the API response
            # This is an example - adjust based on actual API response structure
            wind_data = {
                'speed': data.get('wind', {}).get('speed', 0),
                'direction': data.get('wind', {}).get('deg', 0),
                'gust': data.get('wind', {}).get('gust', 0),
                'timestamp': timestamp
            }
            
            return wind_data
            
        except Exception as e:
            print(f"Error getting wind speed data: {e}")
            # Return default values if API fails
            return {
                'speed': 0,
                'direction': 0,
                'gust': 0,
                'timestamp': timestamp
            }
    
    def get_historical_solar_data(self, start_date: datetime.datetime, 
                                end_date: datetime.datetime) -> pd.DataFrame:
        """
        Get historical solar irradiance data
        
        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with historical solar data
        """
        try:
            # Example using Solcast historical API
            url = f"https://api.solcast.com.au/radiation/historical"
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'api_key': self.solar_api_key,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'format': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data.get('data', []))
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting historical solar data: {e}")
            return pd.DataFrame()
    
    def get_historical_wind_data(self, start_date: datetime.datetime,
                               end_date: datetime.datetime) -> pd.DataFrame:
        """
        Get historical wind speed data
        
        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with historical wind data
        """
        try:
            # Example using OpenWeatherMap historical API
            url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.wind_api_key,
                'units': 'metric',
                'dt': int(start_date.timestamp())
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and convert to DataFrame
            wind_data = []
            for hour in data.get('hourly', []):
                wind_data.append({
                    'timestamp': pd.to_datetime(hour['dt'], unit='s'),
                    'speed': hour.get('wind_speed', 0),
                    'direction': hour.get('wind_deg', 0),
                    'gust': hour.get('wind_gust', 0)
                })
            
            df = pd.DataFrame(wind_data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting historical wind data: {e}")
            return pd.DataFrame()

# Create a global instance
weather_apis = WeatherAPIs() 