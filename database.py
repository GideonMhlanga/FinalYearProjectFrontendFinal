import os
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import json

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import and_

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL","postgresql://gmhlanga:2001@localhost:5432/frontend_finalproject")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    """User account information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # In a production app, this would be hashed
    
    # Extended user profile information
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    
    # User role and permissions
    role = Column(String(20), nullable=False)  # 'admin', 'maintenance', 'operator', 'viewer', 'owner'
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert User object to dictionary (exclude password)"""
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class SystemSetting(Base):
    """System settings and configuration"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    setting_name = Column(String(50), unique=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def to_dict(self):
        """Convert setting to dictionary"""
        # Try to parse JSON value if possible
        try:
            value = json.loads(self.setting_value)
        except:
            value = self.setting_value
            
        return {
            "id": self.id,
            "setting_name": self.setting_name,
            "setting_value": value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PowerData(Base):
    """Historical power generation and consumption data"""
    __tablename__ = "power_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    solar_power = Column(Float)  # kW
    wind_power = Column(Float)   # kW
    load = Column(Float)         # kW
    battery_soc = Column(Float)  # %
    battery_voltage = Column(Float)  # V
    battery_current = Column(Float)  # A
    battery_temperature = Column(Float)  # °C
    irradiance = Column(Float)   # W/m²
    wind_speed = Column(Float)   # m/s
    temperature = Column(Float)  # °C
    
    def to_dict(self):
        """Convert power data to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "solar_power": self.solar_power,
            "wind_power": self.wind_power,
            "load": self.load,
            "battery_soc": self.battery_soc,
            "battery_voltage": self.battery_voltage,
            "battery_current": self.battery_current,
            "battery_temperature": self.battery_temperature,
            "irradiance": self.irradiance,
            "wind_speed": self.wind_speed,
            "temperature": self.temperature
        }

class SystemLog(Base):
    """System event and alert logs"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, index=True)
    log_type = Column(String(20), nullable=False)  # 'info', 'warning', 'error', 'alert'
    message = Column(Text, nullable=False)
    details = Column(Text)
    
    def to_dict(self):
        """Convert log to dictionary"""
        # Try to parse JSON details if possible
        try:
            details = json.loads(self.details) if self.details else None
        except:
            details = self.details
            
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "log_type": self.log_type,
            "message": self.message,
            "details": details
        }

class WeatherData(Base):
    """Historical weather data"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    location = Column(String(50), nullable=False)
    temperature = Column(Float)  # °C
    condition = Column(String(50))  # sunny, cloudy, etc.
    wind_speed = Column(Float)   # m/s
    wind_direction = Column(String(10))  # N, NE, etc.
    humidity = Column(Float)     # %
    pressure = Column(Float)     # hPa
    irradiance = Column(Float)   # W/m²
    
    def to_dict(self):
        """Convert weather data to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "temperature": self.temperature,
            "condition": self.condition,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "irradiance": self.irradiance
        }

class BlockchainLog(Base):
    """Blockchain energy data logs"""
    __tablename__ = "blockchain_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, index=True)
    data_type = Column(String(50), nullable=False)  # current_snapshot, daily_summary, weekly_summary, custom
    description = Column(Text, nullable=True)
    data_hash = Column(String(128), nullable=False)  # SHA-256 hash of the data
    transaction_hash = Column(String(128), nullable=False)  # Blockchain transaction hash
    blockchain_network = Column(String(50), default="Simulation")  # Ethereum, Polygon, etc.
    status = Column(String(20), default="confirmed")  # pending, confirmed, failed
    data_json = Column(Text, nullable=True)  # JSON data that was logged (only for simulation mode)
    
    def to_dict(self):
        """Convert blockchain log to dictionary"""
        # Try to parse JSON data if possible
        try:
            data = json.loads(self.data_json) if self.data_json else None
        except:
            data = self.data_json
            
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "data_type": self.data_type,
            "description": self.description,
            "data_hash": self.data_hash,
            "transaction_hash": self.transaction_hash,
            "blockchain_network": self.blockchain_network,
            "status": self.status,
            "data": data
        }

class PredictiveMaintenance(Base):
    """Predictive maintenance data and forecasts"""
    __tablename__ = "predictive_maintenance"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, index=True)
    component = Column(String(50), nullable=False)  # solar_panel, wind_turbine, battery, inverter, etc.
    health_score = Column(Float, nullable=False)  # 0-100 score indicating component health
    predicted_failure_date = Column(DateTime, nullable=True)  # When component is predicted to fail
    maintenance_recommended = Column(Boolean, default=False)  # Whether maintenance is recommended
    recommendation = Column(Text, nullable=True)  # Specific maintenance recommendation
    confidence = Column(Float)  # Confidence in prediction (0-1)
    analysis_data = Column(Text, nullable=True)  # JSON data with detailed analysis
    maintenance_cost = Column(Float, nullable=True)  # Estimated cost of maintenance
    failure_cost = Column(Float, nullable=True)  # Estimated cost if failure occurs
    
    def to_dict(self):
        """Convert predictive maintenance data to dictionary"""
        # Parse JSON analysis data if possible
        try:
            analysis = json.loads(self.analysis_data) if self.analysis_data else None
        except:
            analysis = self.analysis_data
            
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "component": self.component,
            "health_score": self.health_score,
            "predicted_failure_date": self.predicted_failure_date.isoformat() if self.predicted_failure_date else None,
            "maintenance_recommended": self.maintenance_recommended,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "analysis_data": analysis,
            "maintenance_cost": self.maintenance_cost,
            "failure_cost": self.failure_cost
        }

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self):
        """Initialize the database manager"""
        self.engine = engine
        self.Session = Session
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Seed initial data if needed
        self._seed_initial_data()
        
    def _seed_initial_data(self):
        """Seed initial data if database is empty"""
        session = self.Session()
        
        # Check if users table is empty
        if session.query(User).count() == 0:
            # Add admin user
            admin_user = User(
                username="admin",
                password="admin123",  # In production, this would be hashed
                role="admin"
            )
            session.add(admin_user)
            
        # Check if system settings table is empty
        if session.query(SystemSetting).count() == 0:
            # Add default battery settings
            battery_settings = {
                "capacity": 10.0,      # kWh
                "charge_rate": 2.0,    # kW
                "discharge_rate": 2.0, # kW
                "min_soc": 20.0,       # %
                "max_soc": 90.0,       # %
                "efficiency": 92.0,    # %
                "chemistry": "Lithium Ion"
            }
            
            # Add default system settings
            system_settings = {
                "solar_capacity": 5.0,  # kW
                "wind_capacity": 3.0,   # kW
                "backup_enabled": True,
                "backup_threshold": 30.0,  # %
                "grid_connected": False
            }
            
            # Add location settings
            location_settings = {
                "name": "Harare",
                "latitude": -17.8292,
                "longitude": 31.0522,
                "timezone": "Africa/Harare",
                "country": "Zimbabwe"
            }
            
            # Create system settings
            settings = [
                SystemSetting(setting_name="battery", setting_value=json.dumps(battery_settings)),
                SystemSetting(setting_name="system", setting_value=json.dumps(system_settings)),
                SystemSetting(setting_name="location", setting_value=json.dumps(location_settings))
            ]
            
            session.add_all(settings)
            
            # Add sample system log
            initial_log = SystemLog(
                log_type="info",
                message="System initialized",
                details=json.dumps({"source": "DatabaseManager"})
            )
            
            session.add(initial_log)
        
        # Commit changes
        session.commit()
        session.close()
        
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users (excluding passwords)"""
        session = self.Session()
        users = session.query(User).all()
        user_list = [user.to_dict() for user in users]
        session.close()
        return user_list
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user credentials
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            Dict with authentication result
        """
        session = self.Session()
        user = session.query(User).filter_by(username=username).first()
        
        if user and user.password == password:  # In production, would use password hashing
            result = {"authenticated": True, "role": user.role, "user": user.to_dict()}
        else:
            result = {"authenticated": False, "role": None, "user": None}
            
        session.close()
        return result
    
    def add_user(self, username: str, password: str, role: str) -> bool:
        """
        Add a new user
        
        Args:
            username: Username for the new user
            password: Password for the new user
            role: Role for the new user
            
        Returns:
            True if user added successfully, False otherwise
        """
        session = self.Session()
        
        # Check if user already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            session.close()
            return False
        
        # Create new user
        user = User(
            username=username,
            password=password,  # In production, would hash password
            role=role
        )
        
        try:
            session.add(user)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user
        
        Args:
            username: Username to delete
            
        Returns:
            True if user deleted successfully, False otherwise
        """
        session = self.Session()
        
        # Don't allow deletion of admin user
        if username == "admin":
            session.close()
            return False
        
        user = session.query(User).filter_by(username=username).first()
        if not user:
            session.close()
            return False
        
        try:
            session.delete(user)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def get_settings(self, setting_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get system settings
        
        Args:
            setting_name: Optional name of specific setting to retrieve
            
        Returns:
            Dict with settings
        """
        session = self.Session()
        
        if setting_name:
            # Get specific setting
            setting = session.query(SystemSetting).filter_by(setting_name=setting_name).first()
            if setting:
                result = setting.to_dict()["setting_value"]
            else:
                result = {}
        else:
            # Get all settings
            settings = session.query(SystemSetting).all()
            result = {setting.setting_name: setting.to_dict()["setting_value"] for setting in settings}
        
        session.close()
        return result
    
    def update_settings(self, setting_name: str, setting_value: Union[Dict[str, Any], str]) -> bool:
        """
        Update system settings
        
        Args:
            setting_name: Name of setting to update
            setting_value: New value for setting (can be dict or JSON string)
            
        Returns:
            True if setting updated successfully, False otherwise
        """
        session = self.Session()
        
        # Convert value to JSON string
        if isinstance(setting_value, dict):
            setting_value_str = json.dumps(setting_value)
        else:
            setting_value_str = setting_value
        
        # Check if setting exists
        setting = session.query(SystemSetting).filter_by(setting_name=setting_name).first()
        
        if setting:
            # Update existing setting
            setting.setting_value = setting_value_str
            setting.updated_at = datetime.datetime.now()
        else:
            # Create new setting
            setting = SystemSetting(
                setting_name=setting_name,
                setting_value=setting_value_str
            )
            session.add(setting)
        
        try:
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def save_power_data(self, data: Dict[str, Any]) -> bool:
        """
        Save power generation/consumption data
        
        Args:
            data: Dict with power data
            
        Returns:
            True if data saved successfully, False otherwise
        """
        session = self.Session()
        
        # Create PowerData object
        power_data = PowerData(
            timestamp=data.get("timestamp", datetime.datetime.now()),
            solar_power=data.get("solar_power"),
            wind_power=data.get("wind_power"),
            load=data.get("load"),
            battery_soc=data.get("battery_soc"),
            battery_voltage=data.get("battery_voltage"),
            battery_current=data.get("battery_current"),
            battery_temperature=data.get("battery_temperature"),
            irradiance=data.get("irradiance"),
            wind_speed=data.get("wind_speed"),
            temperature=data.get("temperature")
        )
        
        try:
            session.add(power_data)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def get_power_data(self, timeframe: str = "day") -> pd.DataFrame:
        """
        Get historical power data
        
        Args:
            timeframe: 'day', 'week', or 'month'
            
        Returns:
            Pandas DataFrame with data
        """
        session = self.Session()
        
        # Determine time range
        now = datetime.datetime.now()
        
        if timeframe == "day":
            start_time = now - datetime.timedelta(days=1)
        elif timeframe == "week":
            start_time = now - datetime.timedelta(weeks=1)
        elif timeframe == "month":
            start_time = now - datetime.timedelta(days=30)
        else:
            start_time = now - datetime.timedelta(days=1)  # Default to 1 day
        
        # Query data
        data = session.query(PowerData).filter(PowerData.timestamp >= start_time).order_by(PowerData.timestamp).all()
        
        # Convert to DataFrame
        if data:
            df = pd.DataFrame([d.to_dict() for d in data])
            # Additional calculated columns
            df["total_generation"] = df["solar_power"] + df["wind_power"]
            df["net_power"] = df["total_generation"] - df["load"]
        else:
            # Empty DataFrame with expected columns
            df = pd.DataFrame(columns=[
                "timestamp", "solar_power", "wind_power", "load", "battery_soc",
                "battery_voltage", "battery_current", "battery_temperature",
                "irradiance", "wind_speed", "temperature", "total_generation", "net_power"
            ])
        
        session.close()
        return df
    
    def save_weather_data(self, data: Dict[str, Any]) -> bool:
        """
        Save weather data
        
        Args:
            data: Dict with weather data
            
        Returns:
            True if data saved successfully, False otherwise
        """
        session = self.Session()
        
        # Create WeatherData object
        weather_data = WeatherData(
            timestamp=data.get("timestamp", datetime.datetime.now()),
            location=data.get("location", "Harare"),
            temperature=data.get("temperature"),
            condition=data.get("condition"),
            wind_speed=data.get("wind_speed"),
            wind_direction=data.get("wind_direction"),
            humidity=data.get("humidity"),
            pressure=data.get("pressure"),
            irradiance=data.get("irradiance")
        )
        
        try:
            session.add(weather_data)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def add_system_log(self, log_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a system log entry
        
        Args:
            log_type: Type of log ('info', 'warning', 'error', 'alert')
            message: Log message
            details: Optional dict with additional details
            
        Returns:
            True if log added successfully, False otherwise
        """
        session = self.Session()
        
        # Convert details to JSON string if provided
        details_str = None
        if details and isinstance(details, dict):
            details_str = json.dumps(details)
        
        # Create SystemLog object
        log = SystemLog(
            log_type=log_type,
            message=message,
            details=details_str
        )
        
        try:
            session.add(log)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def get_system_logs(self, limit: int = 50, log_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get system logs
        
        Args:
            limit: Maximum number of logs to retrieve
            log_type: Optional filter by log type
            
        Returns:
            List of log dictionaries
        """
        session = self.Session()
        
        # Build query
        query = session.query(SystemLog).order_by(SystemLog.timestamp.desc())
        
        if log_type:
            query = query.filter(SystemLog.log_type == log_type)
        
        logs = query.limit(limit).all()
        
        # Convert to list of dicts
        log_list = [log.to_dict() for log in logs]
        
        session.close()
        return log_list
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile information
        
        Args:
            username: Username of the user to update
            profile_data: Dict with profile fields to update
            
        Returns:
            True if profile updated successfully, False otherwise
        """
        session = self.Session()
        
        # Get user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            session.close()
            return False
        
        # Update fields
        if "first_name" in profile_data:
            user.first_name = profile_data["first_name"]
        if "last_name" in profile_data:
            user.last_name = profile_data["last_name"]
        if "email" in profile_data:
            user.email = profile_data["email"]
        if "phone" in profile_data:
            user.phone = profile_data["phone"]
        if "address" in profile_data:
            user.address = profile_data["address"]
        if "role" in profile_data and username != "admin":  # Don't allow changing admin's role
            user.role = profile_data["role"]
            
        try:
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Get a user's profile information
        
        Args:
            username: Username to retrieve
            
        Returns:
            Dict with user profile data
        """
        session = self.Session()
        
        user = session.query(User).filter_by(username=username).first()
        if user:
            result = user.to_dict()
        else:
            result = {}
            
        session.close()
        return result
    
    def record_user_login(self, username: str) -> bool:
        """
        Update the last_login timestamp for a user
        
        Args:
            username: Username of user who just logged in
            
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.Session()
        
        user = session.query(User).filter_by(username=username).first()
        if not user:
            session.close()
            return False
            
        user.last_login = datetime.datetime.now()
        
        try:
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def save_blockchain_log(self, data_type: str, data_hash: str, transaction_hash: str, 
                          description: str = "", data_json: Optional[str] = None,
                          blockchain_network: str = "Simulation", status: str = "confirmed") -> bool:
        """
        Save a blockchain log entry
        
        Args:
            data_type: Type of data logged ('current_snapshot', 'daily_summary', etc.)
            data_hash: Hash of the data recorded on blockchain
            transaction_hash: Transaction hash from the blockchain
            description: Optional description of the log
            data_json: Optional JSON string of the actual data (for simulation mode)
            blockchain_network: Blockchain network used (default: "Simulation")
            status: Status of the blockchain transaction
            
        Returns:
            True if log saved successfully, False otherwise
        """
        session = self.Session()
        
        # Create BlockchainLog object
        blockchain_log = BlockchainLog(
            timestamp=datetime.datetime.now(),
            data_type=data_type,
            description=description,
            data_hash=data_hash,
            transaction_hash=transaction_hash,
            blockchain_network=blockchain_network,
            status=status,
            data_json=data_json
        )
        
        try:
            session.add(blockchain_log)
            session.commit()
            success = True
        except Exception as e:
            session.rollback()
            print(f"Error saving blockchain log: {e}")
            success = False
        finally:
            session.close()
            
        return success
    
    def get_blockchain_logs(self, limit: int = 20, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get blockchain logs
        
        Args:
            limit: Maximum number of logs to retrieve
            data_type: Optional filter by data type
            
        Returns:
            List of blockchain log dictionaries
        """
        session = self.Session()
        
        # Build query
        query = session.query(BlockchainLog).order_by(BlockchainLog.timestamp.desc())
        
        # Apply filter if specified
        if data_type:
            query = query.filter(BlockchainLog.data_type == data_type)
        
        # Limit results
        query = query.limit(limit)
        
        # Execute query
        logs = query.all()
        
        # Convert to dictionaries
        log_list = [log.to_dict() for log in logs]
        
        session.close()
        return log_list
    
    def get_blockchain_log_by_transaction(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get a blockchain log by transaction hash
        
        Args:
            transaction_hash: Transaction hash to search for
            
        Returns:
            Blockchain log dictionary or None if not found
        """
        session = self.Session()
        
        # Query log by transaction hash
        log = session.query(BlockchainLog).filter_by(transaction_hash=transaction_hash).first()
        
        # Convert to dictionary if found
        result = log.to_dict() if log else None
        
        session.close()
        return result
    
    def get_blockchain_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about blockchain logs
        
        Returns:
            Dictionary with blockchain statistics
        """
        session = self.Session()
        
        # Get total log count
        total_logs = session.query(func.count(BlockchainLog.id)).scalar()
        
        # Get count by data type
        type_counts = {}
        for data_type, count in session.query(BlockchainLog.data_type, func.count(BlockchainLog.id)).\
                                         group_by(BlockchainLog.data_type).all():
            type_counts[data_type] = count
        
        # Get count by network
        network_counts = {}
        for network, count in session.query(BlockchainLog.blockchain_network, func.count(BlockchainLog.id)).\
                                       group_by(BlockchainLog.blockchain_network).all():
            network_counts[network] = count
        
        # Get most recent log
        latest_log = session.query(BlockchainLog).order_by(BlockchainLog.timestamp.desc()).first()
        latest = latest_log.to_dict() if latest_log else None
        
        # Compile statistics
        stats = {
            "total_logs": total_logs,
            "by_data_type": type_counts,
            "by_network": network_counts,
            "latest_log": latest
        }
        
        session.close()
        return stats
    
    def save_predictive_maintenance(self, data: Dict[str, Any]) -> bool:
        """
        Save predictive maintenance data
        
        Args:
            data: Dict with predictive maintenance data
            
        Returns:
            True if data saved successfully, False otherwise
        """
        session = self.Session()
        
        # Parse dates if they are strings
        predicted_failure_date = data.get("predicted_failure_date")
        if isinstance(predicted_failure_date, str):
            try:
                predicted_failure_date = datetime.datetime.fromisoformat(predicted_failure_date)
            except:
                predicted_failure_date = None
        
        # Convert analysis data to JSON string if it's a dict
        analysis_data = data.get("analysis_data")
        if isinstance(analysis_data, dict):
            analysis_data = json.dumps(analysis_data)
        
        # Create PredictiveMaintenance object
        predictive_data = PredictiveMaintenance(
            timestamp=data.get("timestamp", datetime.datetime.now()),
            component=data.get("component"),
            health_score=data.get("health_score"),
            predicted_failure_date=predicted_failure_date,
            maintenance_recommended=data.get("maintenance_recommended", False),
            recommendation=data.get("recommendation"),
            confidence=data.get("confidence"),
            analysis_data=analysis_data,
            maintenance_cost=data.get("maintenance_cost"),
            failure_cost=data.get("failure_cost")
        )
        
        try:
            session.add(predictive_data)
            session.commit()
            success = True
        except:
            session.rollback()
            success = False
        finally:
            session.close()
            
        return success
    
    def get_predictive_maintenance(self, component: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get predictive maintenance data
        
        Args:
            component: Optional component to filter by
            
        Returns:
            List of predictive maintenance dictionaries
        """
        session = self.Session()
        
        # Query data
        if component:
            data = session.query(PredictiveMaintenance).filter_by(component=component).order_by(PredictiveMaintenance.timestamp.desc()).all()
        else:
            data = session.query(PredictiveMaintenance).order_by(PredictiveMaintenance.timestamp.desc()).all()
        
        # Convert to list of dicts
        result = [item.to_dict() for item in data]
        
        session.close()
        return result
    
    def get_component_health(self) -> Dict[str, Any]:
        """
        Get current health status of all components
        
        Returns:
            Dict with component health information
        """
        session = self.Session()
        
        # Get the latest health score for each component
        subquery = session.query(
            PredictiveMaintenance.component,
            func.max(PredictiveMaintenance.timestamp).label("max_timestamp")
        ).group_by(PredictiveMaintenance.component).subquery("latest")
        
        latest_scores = session.query(PredictiveMaintenance).join(
            subquery,
            and_(
                PredictiveMaintenance.component == subquery.c.component,
                PredictiveMaintenance.timestamp == subquery.c.max_timestamp
            )
        ).all()
        
        # Convert to dict
        result = {item.component: item.to_dict() for item in latest_scores}
        
        session.close()
        return result
    
    def truncate_old_data(self, days_to_keep: int = 90) -> Tuple[int, int, int]:
        """
        Remove old data to prevent database from growing too large
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Tuple with (power_data_removed, weather_data_removed, maintenance_data_removed)
        """
        session = self.Session()
        
        # Calculate cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        
        # Delete old power data
        power_deleted = session.query(PowerData).filter(PowerData.timestamp < cutoff_date).delete()
        
        # Delete old weather data
        weather_deleted = session.query(WeatherData).filter(WeatherData.timestamp < cutoff_date).delete()
        
        # Delete old predictive maintenance data
        maintenance_deleted = session.query(PredictiveMaintenance).filter(PredictiveMaintenance.timestamp < cutoff_date).delete()
        
        # Commit changes
        session.commit()
        session.close()
        
        return (power_deleted, weather_deleted, maintenance_deleted)


# Create singleton instance
db = DatabaseManager()