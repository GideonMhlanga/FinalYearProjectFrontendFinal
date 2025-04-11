import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# Import database and utilities
from database import db
from data_generator import data_generator
from utils import format_power, get_status_color
from blockchain_integration import blockchain_logger

# Set page configuration
st.set_page_config(
    page_title="Blockchain Energy Logs",
    page_icon="🔗",
    layout="wide"
)

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in to access this page.")
    st.stop()

# Page title
st.title("Blockchain Energy Logs")
st.markdown("### Tamper-Proof Energy Production Records")

# Overview of blockchain integration
st.markdown("""
This page provides blockchain integration for your solar-wind hybrid system. 
Your energy production data is securely recorded on the blockchain, providing 
an immutable and verifiable record that can be used for:

- **Energy Certification**: Prove your renewable energy production
- **Carbon Credits**: Support claims for renewable energy credits
- **Audit Trails**: Maintain tamper-proof records for compliance
- **Energy Trading**: Enable peer-to-peer energy trading with verified production data
""")

# Get blockchain status
blockchain_status = blockchain_logger.get_blockchain_status()

# Create tabs for different blockchain views
tabs = st.tabs([
    "Blockchain Status", 
    "Log Energy Data", 
    "View Energy Logs",
    "Verify Records"
])

# Blockchain Status tab
with tabs[0]:
    st.subheader("Blockchain Connection Status")
    
    # Display blockchain connection status
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        status_color = "green" if blockchain_status["connected"] else "red"
        connection_text = "Connected" if blockchain_status["connected"] else "Disconnected"
        
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {'rgba(0, 255, 0, 0.1)' if blockchain_status['connected'] else 'rgba(255, 0, 0, 0.1)'};">
            <h3 style="margin:0;">Status: <span style="color: {status_color};">{connection_text}</span></h3>
            <p><strong>Mode:</strong> {blockchain_status["mode"]}</p>
            <p><strong>Network:</strong> {blockchain_status.get("network", "N/A")}</p>
            <p><strong>Energy Logs:</strong> {blockchain_status.get("log_count", 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with status_col2:
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: rgba(0, 0, 0, 0.05);">
            <h3 style="margin:0;">Blockchain Details</h3>
            <p><strong>Contract Address:</strong> {blockchain_status.get("contract_address", "N/A")}</p>
            <p><strong>Account Address:</strong> {blockchain_status.get("account_address", "N/A")}</p>
            <p><strong>Provider URL:</strong> {blockchain_logger.provider_url if not blockchain_logger.simulation_mode else "Local Simulation"}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show statistics from the database
    st.subheader("Blockchain Log Statistics")
    
    # Get blockchain statistics from the database
    blockchain_stats = db.get_blockchain_statistics()
    
    # Create columns for stats
    stat_col1, stat_col2 = st.columns(2)
    
    with stat_col1:
        st.metric("Total Energy Logs", blockchain_stats.get("total_logs", 0))
        
        # Display log types
        if "by_data_type" in blockchain_stats and blockchain_stats["by_data_type"]:
            st.subheader("Log Types")
            for data_type, count in blockchain_stats.get("by_data_type", {}).items():
                st.text(f"{data_type}: {count} logs")
    
    with stat_col2:
        # Display blockchain networks
        if "by_network" in blockchain_stats and blockchain_stats["by_network"]:
            st.subheader("Blockchain Networks")
            for network, count in blockchain_stats.get("by_network", {}).items():
                st.text(f"{network}: {count} logs")
        
        # Display latest log info
        if "latest_log" in blockchain_stats and blockchain_stats["latest_log"]:
            latest = blockchain_stats["latest_log"]
            st.subheader("Latest Recorded Log")
            st.text(f"Type: {latest.get('data_type', 'Unknown')}")
            if "timestamp" in latest:
                timestamp = latest["timestamp"]
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                st.text(f"Time: {timestamp}")
            st.text(f"Description: {latest.get('description', 'N/A')}")
            
    # Show visualization of log distribution if there's enough data
    # Make sure blockchain_stats is defined here too
    if not 'blockchain_stats' in locals():
        blockchain_stats = db.get_blockchain_statistics()
    
    if "by_data_type" in blockchain_stats and len(blockchain_stats["by_data_type"]) > 1:
        st.subheader("Log Distribution")
        
        # Create pie chart of log types
        fig = px.pie(
            values=list(blockchain_stats["by_data_type"].values()),
            names=list(blockchain_stats["by_data_type"].keys()),
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4,
            title="Energy Log Types"
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Help text for setting up blockchain integration
    st.markdown("### How to Configure Real Blockchain Integration")
    
    if blockchain_status["mode"] == "Simulation":
        st.info("""
        **The system is currently running in simulation mode.**
        
        To enable real blockchain integration, you need to set the following environment variables:
        
        1. `BLOCKCHAIN_PROVIDER_URL`: Your Ethereum provider URL (Infura, Alchemy, etc.)
        2. `ENERGY_CONTRACT_ADDRESS`: Address of the deployed energy logging smart contract
        3. `BLOCKCHAIN_PRIVATE_KEY`: Private key for the blockchain account (keep this secure!)
        
        Contact your administrator to set up these credentials.
        """)
    
    # Display information about blockchain benefits
    st.markdown("### Benefits of Blockchain Integration")
    
    benefit_col1, benefit_col2 = st.columns(2)
    
    with benefit_col1:
        st.markdown("""
        **Immutability and Security**
        
        - Data cannot be altered or deleted once recorded
        - Cryptographic verification ensures data integrity
        - Distributed ledger eliminates single points of failure
        - Secure proof of energy production history
        """)
    
    with benefit_col2:
        st.markdown("""
        **Transparency and Trust**
        
        - All participants can verify the same information
        - No need for trusted third parties
        - Automated smart contracts for energy trading
        - Publicly verifiable renewable energy certificates
        """)

# Log Energy Data tab
with tabs[1]:
    st.subheader("Record Energy Data to Blockchain")
    
    st.markdown("""
    This interface allows you to manually record energy production data to the blockchain.
    The system also automatically logs daily production summaries.
    """)
    
    # Form for logging energy data
    with st.form("blockchain_log_form"):
        # Options for data to log
        log_type = st.selectbox(
            "Select Data Type to Log",
            options=[
                "Current Production Snapshot",
                "Daily Energy Summary",
                "Weekly Energy Summary",
                "Custom Data"
            ]
        )
        
        # Description field
        description = st.text_input(
            "Log Description (optional)",
            value=f"{log_type} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Show a preview of the data that will be logged
        st.subheader("Data Preview")
        
        if log_type == "Current Production Snapshot":
            # Get current system data
            data_to_log = data_generator.generate_current_data()
            
            # Remove some fields for clarity in display
            display_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "solar_power": f"{data_to_log['solar_power']:.2f} kW",
                "wind_power": f"{data_to_log['wind_power']:.2f} kW",
                "total_generation": f"{data_to_log['total_generation']:.2f} kW",
                "battery_soc": f"{data_to_log['battery']['soc']:.1f}%",
                "irradiance": f"{data_to_log['environmental']['irradiance']:.1f} W/m²",
                "wind_speed": f"{data_to_log['environmental']['wind_speed']:.1f} m/s",
                "temperature": f"{data_to_log['environmental']['temperature']:.1f}°C"
            }
            
            st.json(display_data)
            
        elif log_type == "Daily Energy Summary":
            # Get energy summary for the day
            daily_data = data_generator.get_historical_data(timeframe="day")
            
            if not daily_data.empty:
                # Calculate energy produced (kWh) from power (kW) data
                # Assuming data points are at 15-minute intervals (0.25 hours)
                interval_hours = 0.25
                solar_energy = (daily_data['solar_power'] * interval_hours).sum()
                wind_energy = (daily_data['wind_power'] * interval_hours).sum()
                total_energy = solar_energy + wind_energy
                
                # Calculate peak powers
                peak_solar = daily_data['solar_power'].max()
                peak_wind = daily_data['wind_power'].max()
                peak_total = daily_data['total_generation'].max()
                
                # Calculate averages
                avg_solar = daily_data['solar_power'].mean()
                avg_wind = daily_data['wind_power'].mean()
                
                # Create summary
                display_data = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_energy_produced": f"{total_energy:.2f} kWh",
                    "solar_energy": f"{solar_energy:.2f} kWh",
                    "wind_energy": f"{wind_energy:.2f} kWh",
                    "peak_solar_power": f"{peak_solar:.2f} kW",
                    "peak_wind_power": f"{peak_wind:.2f} kW",
                    "peak_total_power": f"{peak_total:.2f} kW",
                    "average_solar_power": f"{avg_solar:.2f} kW",
                    "average_wind_power": f"{avg_wind:.2f} kW",
                    "solar_percentage": f"{(solar_energy / total_energy * 100):.1f}%",
                    "wind_percentage": f"{(wind_energy / total_energy * 100):.1f}%"
                }
                
                # Data to actually log to blockchain (without formatting)
                data_to_log = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_energy_produced": float(total_energy),
                    "solar_energy": float(solar_energy),
                    "wind_energy": float(wind_energy),
                    "peak_solar_power": float(peak_solar),
                    "peak_wind_power": float(peak_wind),
                    "peak_total_power": float(peak_total),
                    "average_solar_power": float(avg_solar),
                    "average_wind_power": float(avg_wind),
                    "solar_percentage": float(solar_energy / total_energy * 100),
                    "wind_percentage": float(wind_energy / total_energy * 100)
                }
                
                st.json(display_data)
            else:
                st.warning("No data available for daily summary")
                data_to_log = {}
                
        elif log_type == "Weekly Energy Summary":
            # Get energy summary for the week
            weekly_data = data_generator.get_historical_data(timeframe="week")
            
            if not weekly_data.empty:
                # Calculate energy produced (kWh) from power (kW) data
                # Assuming data points are at hourly intervals (1 hour) for weekly data
                interval_hours = 1.0
                solar_energy = (weekly_data['solar_power'] * interval_hours).sum()
                wind_energy = (weekly_data['wind_power'] * interval_hours).sum()
                total_energy = solar_energy + wind_energy
                
                # Calculate daily averages
                days_in_data = (weekly_data['timestamp'].max() - weekly_data['timestamp'].min()).total_seconds() / (24 * 3600)
                days_in_data = max(1, days_in_data)  # Ensure we don't divide by zero
                
                daily_avg_total = total_energy / days_in_data
                daily_avg_solar = solar_energy / days_in_data
                daily_avg_wind = wind_energy / days_in_data
                
                # Create summary
                display_data = {
                    "week_ending": datetime.now().strftime("%Y-%m-%d"),
                    "days_included": f"{days_in_data:.1f}",
                    "total_energy_produced": f"{total_energy:.2f} kWh",
                    "solar_energy": f"{solar_energy:.2f} kWh",
                    "wind_energy": f"{wind_energy:.2f} kWh",
                    "daily_average_total": f"{daily_avg_total:.2f} kWh/day",
                    "daily_average_solar": f"{daily_avg_solar:.2f} kWh/day",
                    "daily_average_wind": f"{daily_avg_wind:.2f} kWh/day",
                    "solar_percentage": f"{(solar_energy / total_energy * 100):.1f}%",
                    "wind_percentage": f"{(wind_energy / total_energy * 100):.1f}%"
                }
                
                # Data to actually log to blockchain (without formatting)
                data_to_log = {
                    "week_ending": datetime.now().strftime("%Y-%m-%d"),
                    "days_included": float(days_in_data),
                    "total_energy_produced": float(total_energy),
                    "solar_energy": float(solar_energy),
                    "wind_energy": float(wind_energy),
                    "daily_average_total": float(daily_avg_total),
                    "daily_average_solar": float(daily_avg_solar),
                    "daily_average_wind": float(daily_avg_wind),
                    "solar_percentage": float(solar_energy / total_energy * 100),
                    "wind_percentage": float(wind_energy / total_energy * 100)
                }
                
                st.json(display_data)
            else:
                st.warning("No data available for weekly summary")
                data_to_log = {}
                
        else:  # Custom Data
            st.markdown("Enter custom JSON data to log:")
            custom_data = st.text_area(
                "Custom Data (JSON format)",
                value='{\n  "custom_timestamp": "' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '",\n  "value1": 123.45,\n  "value2": "Sample data"\n}'
            )
            
            try:
                data_to_log = json.loads(custom_data)
                st.json(data_to_log)
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your input.")
                data_to_log = {}
        
        # Submit button
        submit_button = st.form_submit_button("Log to Blockchain")
    
    # Handle form submission
    if submit_button and data_to_log:
        with st.spinner("Recording data to blockchain..."):
            # Add a slight delay to simulate blockchain processing
            time.sleep(1.5)
            
            # Log the data to blockchain
            success, tx_hash = blockchain_logger.log_energy_data(data_to_log, description)
            
            if success:
                st.success(f"Successfully logged data to blockchain!")
                st.code(f"Transaction Hash: {tx_hash}")
                
                # Log the blockchain record to the system logs
                db.add_system_log(
                    log_type="blockchain",
                    message=f"Energy data recorded to blockchain",
                    details={
                        "tx_hash": tx_hash,
                        "description": description,
                        "data_type": log_type
                    }
                )
                
            else:
                st.error(f"Failed to log data to blockchain: {tx_hash}")

# View Energy Logs tab
with tabs[2]:
    st.subheader("View Blockchain Energy Logs")
    
    # Refresh button
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    # Get logs from blockchain (these come from database in simulation mode)
    energy_logs = blockchain_logger.get_energy_logs(count=20)
    
    # Also get statistics from the database
    try:
        blockchain_stats = db.get_blockchain_statistics()
    except Exception as e:
        # Create empty stats if database call fails
        blockchain_stats = {
            "total_logs": 0,
            "by_data_type": {},
            "by_network": {},
            "latest_log": None
        }
        st.error(f"Could not retrieve blockchain statistics: {str(e)}")
    
    if energy_logs:
        # Display logs in a table
        log_data = []
        
        for log in energy_logs:
            timestamp = log.get("timestamp")
            if isinstance(timestamp, (int, float)):
                # Convert Unix timestamp to datetime
                timestamp = datetime.fromtimestamp(timestamp)
            else:
                # Try to parse any other format
                try:
                    timestamp = datetime.fromisoformat(str(timestamp))
                except:
                    timestamp = "Unknown"
            
            log_data.append({
                "ID": log.get("id", "N/A"),
                "Timestamp": timestamp,
                "Description": log.get("description", ""),
                "Hash": log.get("dataHash", "")[:10] + "..." if log.get("dataHash") else "N/A",
                "Tx Hash": log.get("simulatedTxHash", "")[:10] + "..." if log.get("simulatedTxHash") else "N/A"
            })
        
        # Create a DataFrame and display it
        log_df = pd.DataFrame(log_data)
        st.dataframe(log_df, use_container_width=True)
        
        # Select a log to view details
        selected_log_id = st.selectbox("Select a log to view details", options=[log["id"] for log in energy_logs])
        
        # Find the selected log
        selected_log = next((log for log in energy_logs if log["id"] == selected_log_id), None)
        
        if selected_log:
            st.subheader("Log Details")
            
            # Display log details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**ID:** {selected_log.get('id', 'N/A')}")
                timestamp = selected_log.get("timestamp")
                if isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(f"**Timestamp:** {timestamp}")
                st.markdown(f"**Description:** {selected_log.get('description', '')}")
            
            with col2:
                st.markdown(f"**Data Hash:** {selected_log.get('dataHash', 'N/A')}")
                if "simulatedTxHash" in selected_log:
                    st.markdown(f"**Transaction Hash:** {selected_log.get('simulatedTxHash', 'N/A')}")
                else:
                    st.markdown(f"**Transaction Hash:** {selected_log.get('txHash', 'N/A')}")
            
            # If we have the actual data (in simulation mode), display it
            if "data" in selected_log:
                st.subheader("Recorded Data")
                st.json(selected_log["data"])
                
                # Create visualizations if we have appropriate data
                if all(k in selected_log["data"] for k in ["solar_energy", "wind_energy"]):
                    st.subheader("Energy Production Visualization")
                    
                    # Create pie chart for energy sources
                    fig = px.pie(
                        values=[selected_log["data"]["solar_energy"], selected_log["data"]["wind_energy"]],
                        names=["Solar", "Wind"],
                        color_discrete_sequence=["#FFD700", "#4682B4"],
                        hole=0.4,
                        title="Energy Production Distribution"
                    )
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=10, r=10, t=30, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#262730" if st.session_state.theme == "light" else "#FAFAFA")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No energy logs found on the blockchain.")
        
        st.markdown("""
        To create energy logs, go to the 'Log Energy Data' tab and record your energy data.
        
        In a production system, energy logs would be automatically created at regular intervals
        (daily or hourly) to maintain a continuous record of energy production.
        """)

# Verify Records tab
with tabs[3]:
    st.subheader("Verify Blockchain Records")
    
    st.markdown("""
    This tool allows you to verify the integrity of energy data by comparing it with the
    blockchain record. This ensures that production data hasn't been tampered with.
    """)
    
    # Method selection
    verify_method = st.radio(
        "Select Verification Method",
        options=["Verify with Data Hash", "Upload Data File"]
    )
    
    if verify_method == "Verify with Data Hash":
        # Form for hash verification
        col1, col2 = st.columns(2)
        
        with col1:
            # Input for the hash from blockchain
            blockchain_hash = st.text_input(
                "Blockchain Data Hash",
                placeholder="Enter the hash from the blockchain record"
            )
        
        with col2:
            # JSON data to verify
            verify_data = st.text_area(
                "Energy Data (JSON format)",
                placeholder='{"solar_power": 3.5, "wind_power": 2.1, ...}'
            )
        
        # Verify button
        if st.button("Verify Data Integrity") and blockchain_hash and verify_data:
            try:
                # Parse the JSON data
                data_to_verify = json.loads(verify_data)
                
                # Calculate the hash of the provided data
                calculated_hash = blockchain_logger.calculate_data_hash(data_to_verify)
                
                # Compare with the blockchain hash
                if calculated_hash == blockchain_hash:
                    st.success("✅ Data Integrity Verified! The data matches the blockchain record.")
                    st.markdown(f"**Calculated Hash:** `{calculated_hash}`")
                else:
                    st.error("❌ Data Integrity Verification Failed! The data does not match the blockchain record.")
                    st.markdown(f"**Calculated Hash:** `{calculated_hash}`")
                    st.markdown(f"**Blockchain Hash:** `{blockchain_hash}`")
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your input.")
    else:
        st.info("File upload verification coming soon. Please use the hash verification method.")
        
        # Placeholder for file upload verification
        uploaded_file = st.file_uploader("Upload JSON data file", type=["json"])
        blockchain_hash = st.text_input(
            "Blockchain Data Hash",
            placeholder="Enter the hash from the blockchain record"
        )
        
        if uploaded_file is not None and blockchain_hash and st.button("Verify File"):
            try:
                # Read and parse the JSON file
                file_content = uploaded_file.read().decode("utf-8")
                data_to_verify = json.loads(file_content)
                
                # Calculate the hash of the file data
                calculated_hash = blockchain_logger.calculate_data_hash(data_to_verify)
                
                # Compare with the blockchain hash
                if calculated_hash == blockchain_hash:
                    st.success("✅ File Integrity Verified! The file matches the blockchain record.")
                    st.markdown(f"**Calculated Hash:** `{calculated_hash}`")
                else:
                    st.error("❌ File Integrity Verification Failed! The file does not match the blockchain record.")
                    st.markdown(f"**Calculated Hash:** `{calculated_hash}`")
                    st.markdown(f"**Blockchain Hash:** `{blockchain_hash}`")
            except Exception as e:
                st.error(f"Error verifying file: {str(e)}")
    
    # Help information
    with st.expander("How Verification Works"):
        st.markdown("""
        **How Blockchain Verification Works:**
        
        1. When energy data is recorded to the blockchain, a secure hash of the data is calculated 
           using the SHA-256 algorithm.
        
        2. This hash is a unique "fingerprint" of the data that will change if even a single 
           character in the data is modified.
        
        3. The hash is stored on the blockchain, which is immutable and tamper-proof.
        
        4. To verify data integrity, the same hashing algorithm is applied to the data in question.
        
        5. If the newly calculated hash matches the hash stored on the blockchain, the data is 
           verified to be identical to what was originally recorded.
        
        This process ensures that energy production data cannot be manipulated after it has been 
        recorded, providing a trustworthy record for auditing, certification, or trading purposes.
        """)

# Footer information
st.divider()
st.caption("Blockchain integration is currently running in simulation mode. Contact your system administrator to configure real blockchain connectivity.")