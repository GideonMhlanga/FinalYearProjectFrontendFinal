"""
Blockchain Integration Module for Solar-Wind Hybrid Monitoring System

This module handles the integration with Ethereum blockchain for
tamper-proof logging of energy generation and consumption data.
The blockchain provides immutable, verifiable records of energy metrics
that can be used for auditing, certification, or energy trading purposes.

Features:
1. Secure data logging to blockchain
2. Verification of previously logged data
3. Viewing historical energy logs from the blockchain
4. Simple smart contract interactions for energy credits
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from web3 import Web3
# The geth_poa_middleware import has been removed as it's not available in the current web3 version
import streamlit as st

# Import database for storing blockchain logs
from database import db

# Use an Ethereum testnet or your own local blockchain
# For production, you would use a real Ethereum network or a specific energy blockchain
# Default to using a test network (Sepolia testnet)
DEFAULT_PROVIDER_URL = "https://eth-sepolia.g.alchemy.com/v2/demo"

# Smart contract ABI (Application Binary Interface) for the energy logging contract
# This is a simplified example, in a real implementation, you would have a deployed contract
ENERGY_LOG_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "dataHash", "type": "string"},
            {"internalType": "string", "name": "description", "type": "string"}
        ],
        "name": "logEnergyData",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "getEnergyLog",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "string", "name": "", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getLogCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class BlockchainLogger:
    """
    Class for handling blockchain logging operations
    """
    def __init__(self, provider_url=None, contract_address=None, private_key=None):
        """
        Initialize the blockchain logger
        
        Args:
            provider_url: URL for the blockchain provider (Infura, Alchemy, etc.)
            contract_address: Address of the deployed energy logging smart contract
            private_key: Private key for signing transactions (should be stored securely)
        """
        # If no provider URL is provided, use the environment variable or default
        self.provider_url = provider_url or os.environ.get("BLOCKCHAIN_PROVIDER_URL", DEFAULT_PROVIDER_URL)
        
        # If no contract address is provided, use the environment variable
        self.contract_address = contract_address or os.environ.get("ENERGY_CONTRACT_ADDRESS")
        
        # If no private key is provided, use the environment variable
        self.private_key = private_key or os.environ.get("BLOCKCHAIN_PRIVATE_KEY")
        
        # Set up Web3 connection - use simulation mode if no credentials are available
        self.simulation_mode = not (self.contract_address and self.private_key)
        
        if not self.simulation_mode:
            self.web3 = Web3(Web3.HTTPProvider(self.provider_url))
            # PoA middleware is not used as it's not available in the current web3 version
            
            # Set up the contract interface
            self.contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.contract_address),
                abi=ENERGY_LOG_ABI
            )
            
            # Get the account address from the private key
            self.account = self.web3.eth.account.from_key(self.private_key)
        else:
            # In simulation mode, we'll store logs locally
            self.local_logs = []
            self.simulation_log_file = "simulated_blockchain_logs.json"
            self._load_simulation_logs()
    
    def _load_simulation_logs(self):
        """Load simulated logs from JSON file if it exists"""
        try:
            if os.path.exists(self.simulation_log_file):
                with open(self.simulation_log_file, 'r') as f:
                    self.local_logs = json.load(f)
        except Exception as e:
            print(f"Error loading simulation logs: {e}")
            self.local_logs = []
    
    def _save_simulation_logs(self):
        """Save simulated logs to JSON file"""
        try:
            with open(self.simulation_log_file, 'w') as f:
                json.dump(self.local_logs, f, indent=2)
        except Exception as e:
            print(f"Error saving simulation logs: {e}")
    
    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """
        Calculate a hash for the provided energy data
        
        Args:
            data: Dictionary containing energy data to hash
            
        Returns:
            String representation of the hash
        """
        # Convert the data dictionary to a sorted JSON string
        data_str = json.dumps(data, sort_keys=True)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def log_energy_data(self, data: Dict[str, Any], description: str = "") -> Tuple[bool, str]:
        """
        Log energy data to the blockchain
        
        Args:
            data: Dictionary containing energy data to log
            description: Optional description of the data
            
        Returns:
            Tuple of (success, transaction_hash or message)
        """
        try:
            # Calculate hash of the data
            data_hash = self.calculate_data_hash(data)
            
            # Get the current timestamp
            timestamp = int(time.time())
            
            if self.simulation_mode:
                # In simulation mode, just store the data locally
                log_entry = {
                    "id": len(self.local_logs),
                    "timestamp": timestamp,
                    "dataHash": data_hash,
                    "description": description,
                    "data": data,  # In simulation we store the actual data too
                    "simulatedTxHash": hashlib.sha256(f"{timestamp}{data_hash}".encode()).hexdigest()
                }
                
                self.local_logs.append(log_entry)
                self._save_simulation_logs()
                
                # Also save to database
                data_json_str = json.dumps(data)
                db.save_blockchain_log(
                    data_type="energy_log",
                    data_hash=data_hash,
                    transaction_hash=log_entry["simulatedTxHash"],
                    description=description,
                    data_json=data_json_str,
                    blockchain_network="Simulation",
                    status="confirmed"
                )
                
                return True, log_entry["simulatedTxHash"]
            else:
                # For real blockchain interaction
                # Build the transaction
                tx = self.contract.functions.logEnergyData(
                    timestamp,
                    data_hash,
                    description
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                    'gas': 2000000,
                    'gasPrice': self.web3.eth.gas_price
                })
                
                # Sign the transaction
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                
                # Send the transaction
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                # Wait for transaction receipt
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                tx_hex = self.web3.to_hex(tx_hash)
                
                # Save transaction to database if successful
                if tx_receipt["status"] == 1:
                    # Save to database
                    data_json_str = json.dumps(data)
                    db.save_blockchain_log(
                        data_type="energy_log",
                        data_hash=data_hash,
                        transaction_hash=tx_hex,
                        description=description,
                        data_json=data_json_str,
                        blockchain_network=self.web3.eth.chain_id,
                        status="confirmed"
                    )
                
                return tx_receipt["status"] == 1, tx_hex
        
        except Exception as e:
            return False, f"Error logging to blockchain: {str(e)}"
    
    def verify_energy_data(self, data: Dict[str, Any], blockchain_hash: str) -> bool:
        """
        Verify that the energy data matches the hash stored on the blockchain
        
        Args:
            data: The energy data to verify
            blockchain_hash: The hash retrieved from the blockchain
            
        Returns:
            True if the data matches the hash, False otherwise
        """
        # Calculate the hash of the current data
        current_hash = self.calculate_data_hash(data)
        
        # Compare with the hash from the blockchain
        return current_hash == blockchain_hash
    
    def get_energy_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent energy logs from the blockchain
        
        Args:
            count: Number of logs to retrieve
            
        Returns:
            List of energy log dictionaries
        """
        if self.simulation_mode:
            # In simulation mode, get logs from the database
            try:
                # Get logs from database
                db_logs = db.get_blockchain_logs(limit=count)
                
                # Convert them to the same format as our simulation logs
                logs = []
                for log in db_logs:
                    log_entry = {
                        "id": log["id"],
                        "timestamp": log["timestamp"],
                        "dataHash": log["data_hash"],
                        "description": log["description"],
                        "simulatedTxHash": log["transaction_hash"]
                    }
                    
                    # Add data if available
                    if log["data"] is not None:
                        log_entry["data"] = log["data"]
                    
                    logs.append(log_entry)
                
                return logs
            except Exception as e:
                print(f"Error getting logs from database: {e}")
                # Fall back to local file if database fails
                return self.local_logs[-count:] if self.local_logs else []
        else:
            # For real blockchain interaction
            try:
                # Get the total log count
                log_count = self.contract.functions.getLogCount().call()
                
                # Get the most recent logs
                logs = []
                for i in range(max(0, log_count - count), log_count):
                    timestamp, data_hash, description = self.contract.functions.getEnergyLog(i).call()
                    logs.append({
                        "id": i,
                        "timestamp": timestamp,
                        "dataHash": data_hash,
                        "description": description
                    })
                
                return logs
            
            except Exception as e:
                print(f"Error getting energy logs: {e}")
                return []

    def get_blockchain_status(self) -> Dict[str, Any]:
        """
        Get current status of the blockchain connection
        
        Returns:
            Dictionary with status information
        """
        if self.simulation_mode:
            # Get statistics from the database
            try:
                stats = db.get_blockchain_statistics()
                log_count = stats["total_logs"]
            except:
                # Fall back to local logs if database query fails
                log_count = len(self.local_logs)
                
            return {
                "connected": True,
                "mode": "Simulation",
                "log_count": log_count,
                "network": "Local Simulation",
                "contract_address": "Simulated Contract"
            }
        else:
            try:
                connected = self.web3.is_connected()
                if connected:
                    network_id = self.web3.eth.chain_id
                    network_name = {
                        1: "Ethereum Mainnet",
                        5: "Goerli Testnet",
                        11155111: "Sepolia Testnet",
                        137: "Polygon Mainnet",
                        80001: "Mumbai Testnet"
                    }.get(network_id, f"Unknown Network (ID: {network_id})")
                    
                    log_count = self.contract.functions.getLogCount().call()
                    
                    return {
                        "connected": True,
                        "mode": "Live Blockchain",
                        "network": network_name,
                        "log_count": log_count,
                        "contract_address": self.contract_address,
                        "account_address": self.account.address
                    }
                else:
                    return {
                        "connected": False,
                        "mode": "Blockchain",
                        "error": "Not connected to provider"
                    }
            except Exception as e:
                return {
                    "connected": False,
                    "mode": "Blockchain",
                    "error": str(e)
                }

# Create a global instance
blockchain_logger = BlockchainLogger()