"""
Anomaly Detection Module for Solar-Wind Hybrid Monitoring System

This module provides various algorithms and utilities for detecting anomalies
in the hybrid solar-wind system data. It supports multiple detection methods:

1. Statistical methods (Z-score, IQR)
2. Rule-based detection
3. Machine learning based detection (isolation forests)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Threshold levels for different anomaly types
ANOMALY_THRESHOLDS = {
    "solar_power": {
        "severe": 3.0,    # Z-score for severe anomaly
        "moderate": 2.0,  # Z-score for moderate anomaly
        "mild": 1.5       # Z-score for mild anomaly
    },
    "wind_power": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    },
    "battery_soc": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    },
    "battery_voltage": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    },
    "battery_temperature": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    },
    "wind_speed": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    },
    "irradiance": {
        "severe": 3.0, 
        "moderate": 2.0,
        "mild": 1.5
    }
}

# Expected value ranges for system components
VALUE_RANGES = {
    "solar_power": (0, 15),         # kW
    "wind_power": (0, 12),          # kW
    "battery_soc": (0, 100),        # %
    "battery_voltage": (44, 56),    # V
    "battery_temperature": (15, 45), # °C
    "wind_speed": (0, 25),          # m/s
    "irradiance": (0, 1200),        # W/m²
    "temperature": (-10, 50)        # °C
}

def detect_statistical_anomalies(data: pd.DataFrame, 
                                window_size: int = 24, 
                                columns_to_check: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect anomalies using statistical methods (Z-score)
    
    Args:
        data: DataFrame with time series data
        window_size: Size of the rolling window for analysis
        columns_to_check: Specific columns to check for anomalies
        
    Returns:
        Dictionary with anomalies by category
    """
    if data.empty:
        return {}
    
    if not columns_to_check:
        columns_to_check = [col for col in data.columns if col in ANOMALY_THRESHOLDS]
    
    anomalies = {}
    
    for column in columns_to_check:
        if column not in data.columns:
            continue
            
        column_anomalies = []
        
        # Calculate rolling mean and standard deviation
        rolling_mean = data[column].rolling(window=window_size, min_periods=1).mean()
        rolling_std = data[column].rolling(window=window_size, min_periods=1).std()
        
        # Replace zero std with a small value to avoid division by zero
        rolling_std = rolling_std.replace(0, 0.0001)
        
        # Calculate Z-scores
        z_scores = (data[column] - rolling_mean) / rolling_std
        
        # Find anomalies
        for i, (idx, z_score) in enumerate(z_scores.items()):
            if pd.isna(z_score):
                continue
                
            abs_z_score = abs(z_score)
            
            if abs_z_score >= ANOMALY_THRESHOLDS[column]["severe"]:
                severity = "severe"
            elif abs_z_score >= ANOMALY_THRESHOLDS[column]["moderate"]:
                severity = "moderate"
            elif abs_z_score >= ANOMALY_THRESHOLDS[column]["mild"]:
                severity = "mild"
            else:
                continue
                
            # Get timestamp
            timestamp = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.iloc[i]["timestamp"])
            
            # Create anomaly entry
            anomaly = {
                "timestamp": timestamp,
                "value": data[column].iloc[i],
                "expected_range": (
                    rolling_mean.iloc[i] - rolling_std.iloc[i],
                    rolling_mean.iloc[i] + rolling_std.iloc[i]
                ),
                "z_score": z_score,
                "severity": severity,
                "message": f"{severity.title()} anomaly detected in {column.replace('_', ' ')}"
            }
            
            column_anomalies.append(anomaly)
        
        if column_anomalies:
            anomalies[column] = column_anomalies
    
    return anomalies

def detect_rule_based_anomalies(data: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect anomalies using predefined rules and thresholds
    
    Args:
        data: DataFrame with time series data
        
    Returns:
        Dictionary with anomalies by category
    """
    if data.empty:
        return {}
    
    anomalies = {}
    
    # Check for out-of-range values
    for column, (min_val, max_val) in VALUE_RANGES.items():
        if column not in data.columns:
            continue
            
        column_anomalies = []
        
        for i, value in enumerate(data[column]):
            if pd.isna(value):
                continue
                
            # Check if value is out of expected range
            if value < min_val or value > max_val:
                # Get timestamp
                timestamp = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.iloc[i]["timestamp"])
                
                # Determine severity
                if value < min_val * 0.5 or value > max_val * 1.5:
                    severity = "severe"
                elif value < min_val * 0.7 or value > max_val * 1.3:
                    severity = "moderate"
                else:
                    severity = "mild"
                
                # Create anomaly entry
                anomaly = {
                    "timestamp": timestamp,
                    "value": value,
                    "expected_range": (min_val, max_val),
                    "severity": severity,
                    "message": f"{severity.title()} anomaly: {column.replace('_', ' ')} value {value} outside expected range"
                }
                
                column_anomalies.append(anomaly)
        
        if column_anomalies:
            anomalies[column] = column_anomalies
    
    # Special rules for specific conditions
    
    # Check for battery overheating
    if "battery_temperature" in data.columns:
        battery_temp_anomalies = []
        
        for i, temp in enumerate(data["battery_temperature"]):
            if pd.isna(temp):
                continue
                
            if temp > 40:  # Critical temperature threshold
                # Get timestamp
                timestamp = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.iloc[i]["timestamp"])
                
                # Determine severity
                if temp > 45:
                    severity = "severe"
                    message = f"CRITICAL: Battery temperature at {temp}°C - immediate action required!"
                elif temp > 42:
                    severity = "moderate"
                    message = f"WARNING: Battery temperature at {temp}°C - monitor closely!"
                else:
                    severity = "mild"
                    message = f"CAUTION: Battery temperature at {temp}°C - higher than recommended"
                
                # Create anomaly entry
                anomaly = {
                    "timestamp": timestamp,
                    "value": temp,
                    "expected_range": (15, 40),
                    "severity": severity,
                    "message": message
                }
                
                battery_temp_anomalies.append(anomaly)
        
        if battery_temp_anomalies:
            if "battery_temperature" not in anomalies:
                anomalies["battery_temperature"] = []
            anomalies["battery_temperature"].extend(battery_temp_anomalies)
    
    # Check for battery low state of charge
    if "battery_soc" in data.columns:
        battery_soc_anomalies = []
        
        for i, soc in enumerate(data["battery_soc"]):
            if pd.isna(soc):
                continue
                
            if soc < 20:  # Low battery threshold
                # Get timestamp
                timestamp = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.iloc[i]["timestamp"])
                
                # Determine severity
                if soc < 10:
                    severity = "severe"
                    message = f"CRITICAL: Battery at {soc}% - critically low charge!"
                elif soc < 15:
                    severity = "moderate"
                    message = f"WARNING: Battery at {soc}% - very low charge"
                else:
                    severity = "mild"
                    message = f"CAUTION: Battery at {soc}% - lower than recommended"
                
                # Create anomaly entry
                anomaly = {
                    "timestamp": timestamp,
                    "value": soc,
                    "expected_range": (20, 100),
                    "severity": severity,
                    "message": message
                }
                
                battery_soc_anomalies.append(anomaly)
        
        if battery_soc_anomalies:
            if "battery_soc" not in anomalies:
                anomalies["battery_soc"] = []
            anomalies["battery_soc"].extend(battery_soc_anomalies)
    
    # Check for solar panel production during daytime
    if all(col in data.columns for col in ["solar_power", "irradiance", "timestamp"]):
        solar_anomalies = []
        
        for i in range(len(data)):
            timestamp = data.iloc[i]["timestamp"] if "timestamp" in data.columns else data.index[i]
            solar_power = data.iloc[i]["solar_power"]
            irradiance = data.iloc[i]["irradiance"]
            
            # Check if it's daytime (between 6 AM and 6 PM)
            hour = timestamp.hour if isinstance(timestamp, datetime) else pd.to_datetime(timestamp).hour
            
            if 6 <= hour <= 18 and irradiance > 200 and solar_power < 0.5:
                # During daytime with good irradiance but low solar power
                
                # Create anomaly entry
                anomaly = {
                    "timestamp": timestamp,
                    "value": solar_power,
                    "irradiance": irradiance,
                    "severity": "moderate",
                    "message": f"Low solar production ({solar_power} kW) despite good irradiance ({irradiance} W/m²)"
                }
                
                solar_anomalies.append(anomaly)
        
        if solar_anomalies:
            if "solar_production" not in anomalies:
                anomalies["solar_production"] = []
            anomalies["solar_production"].extend(solar_anomalies)
    
    return anomalies

def detect_ml_anomalies(data: pd.DataFrame, 
                       columns_to_check: Optional[List[str]] = None,
                       contamination: float = 0.05) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect anomalies using machine learning (Isolation Forest)
    
    Args:
        data: DataFrame with time series data
        columns_to_check: Specific columns to use for anomaly detection
        contamination: Expected proportion of anomalies in the data
        
    Returns:
        Dictionary with anomalies by category
    """
    if data.empty or len(data) < 10:  # Need enough data points
        return {}
    
    if not columns_to_check:
        columns_to_check = [col for col in data.columns if col in ANOMALY_THRESHOLDS]
    
    # Ensure all columns exist in the data
    columns_to_check = [col for col in columns_to_check if col in data.columns]
    
    if not columns_to_check:
        return {}
    
    anomalies = {}
    
    try:
        # Prepare data for isolation forest
        X = data[columns_to_check].copy()
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train isolation forest
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Get anomaly scores (-1 for anomalies, 1 for normal)
        anomaly_labels = model.fit_predict(X_scaled)
        anomaly_scores = model.decision_function(X_scaled)
        
        # Find anomalies
        for i, label in enumerate(anomaly_labels):
            if label == -1:  # Anomaly
                # Get timestamp
                timestamp = data.index[i] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.iloc[i]["timestamp"])
                
                # Determine which feature contributed most to the anomaly
                feature_contributions = {}
                for j, col in enumerate(columns_to_check):
                    value = data.iloc[i][col]
                    mean = X[col].mean()
                    std = X[col].std() or 1  # Avoid division by zero
                    z_score = abs((value - mean) / std)
                    feature_contributions[col] = z_score
                
                primary_feature = max(feature_contributions, key=feature_contributions.get)
                
                # Determine severity based on anomaly score
                score = abs(anomaly_scores[i])
                if score > 0.7:
                    severity = "severe"
                elif score > 0.5:
                    severity = "moderate"
                else:
                    severity = "mild"
                
                # Create anomaly entry
                anomaly = {
                    "timestamp": timestamp,
                    "primary_feature": primary_feature,
                    "value": data.iloc[i][primary_feature],
                    "anomaly_score": score,
                    "severity": severity,
                    "message": f"{severity.title()} anomaly detected in system behavior, primarily in {primary_feature.replace('_', ' ')}"
                }
                
                # Group by primary feature
                if primary_feature not in anomalies:
                    anomalies[primary_feature] = []
                anomalies[primary_feature].append(anomaly)
    
    except Exception as e:
        # If ML detection fails, return empty results
        print(f"Error in ML anomaly detection: {e}")
        return {}
    
    return anomalies

def aggregate_anomalies(statistical_anomalies: Dict[str, List[Dict[str, Any]]],
                        rule_based_anomalies: Dict[str, List[Dict[str, Any]]],
                        ml_anomalies: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Combine anomalies from different detection methods
    
    Args:
        statistical_anomalies: Anomalies detected with statistical methods
        rule_based_anomalies: Anomalies detected with rule-based methods
        ml_anomalies: Anomalies detected with machine learning
        
    Returns:
        Dictionary with combined anomalies by category
    """
    all_anomalies = {}
    
    # Combine all sources of anomalies
    for source in [statistical_anomalies, rule_based_anomalies, ml_anomalies]:
        for category, anomaly_list in source.items():
            if category not in all_anomalies:
                all_anomalies[category] = []
            all_anomalies[category].extend(anomaly_list)
    
    # For each category, sort anomalies by timestamp and severity
    for category in all_anomalies:
        all_anomalies[category].sort(key=lambda x: (x["timestamp"], 
                                                   {"severe": 3, "moderate": 2, "mild": 1}.get(x["severity"], 0)),
                                     reverse=True)  # Most recent and severe first
    
    return all_anomalies

def detect_anomalies(data: pd.DataFrame, 
                    use_statistical: bool = True,
                    use_rule_based: bool = True,
                    use_ml: bool = True,
                    window_size: int = 24) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect anomalies using multiple methods
    
    Args:
        data: DataFrame with time series data
        use_statistical: Whether to use statistical methods
        use_rule_based: Whether to use rule-based methods
        use_ml: Whether to use machine learning
        window_size: Size of the rolling window for statistical analysis
        
    Returns:
        Dictionary with anomalies by category
    """
    statistical_anomalies = {}
    rule_based_anomalies = {}
    ml_anomalies = {}
    
    if use_statistical:
        statistical_anomalies = detect_statistical_anomalies(data, window_size)
    
    if use_rule_based:
        rule_based_anomalies = detect_rule_based_anomalies(data)
    
    if use_ml and len(data) >= 10:
        ml_anomalies = detect_ml_anomalies(data)
    
    # Combine all anomalies
    all_anomalies = aggregate_anomalies(
        statistical_anomalies,
        rule_based_anomalies,
        ml_anomalies
    )
    
    return all_anomalies

def get_anomaly_summary(anomalies: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generate a summary of detected anomalies
    
    Args:
        anomalies: Dictionary with anomalies by category
        
    Returns:
        Dictionary with anomaly summary stats
    """
    total_count = 0
    severe_count = 0
    moderate_count = 0
    mild_count = 0
    categories = {}
    
    for category, anomaly_list in anomalies.items():
        category_count = len(anomaly_list)
        total_count += category_count
        
        category_severe = sum(1 for a in anomaly_list if a["severity"] == "severe")
        category_moderate = sum(1 for a in anomaly_list if a["severity"] == "moderate")
        category_mild = sum(1 for a in anomaly_list if a["severity"] == "mild")
        
        severe_count += category_severe
        moderate_count += category_moderate
        mild_count += category_mild
        
        categories[category] = {
            "count": category_count,
            "severe": category_severe,
            "moderate": category_moderate,
            "mild": category_mild
        }
    
    return {
        "total": total_count,
        "severe": severe_count,
        "moderate": moderate_count,
        "mild": mild_count,
        "categories": categories,
        "has_severe": severe_count > 0,
        "has_moderate": moderate_count > 0,
        "has_mild": mild_count > 0
    }