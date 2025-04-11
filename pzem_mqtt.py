#!/usr/bin/env python3
import time
import json
from pymodbus.client import ModbusSerialClient
import paho.mqtt.client as mqtt
import ssl
from datetime import datetime
import logging

# Configuration
MQTT_BROKER = "your-cluster.s1.eu.hivemq.cloud"  # Your HiveMQ cluster address
MQTT_PORT = 8883
MQTT_TOPIC = "solar/pzem"
MQTT_USER = "your-hivemq-username"
MQTT_PASS = "your-hivemq-password"
MODBUS_PORT = "/dev/ttyUSB0"  # Update with your actual port
SLAVE_ADDRESS = 1  # PZEM-017 default address
UPDATE_INTERVAL = 5  # seconds

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PZEM017Reader:
    def __init__(self):
        self.modbus = ModbusSerialClient(
            method='rtu',
            port=MODBUS_PORT,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1
        )
        
        self.mqtt_client = mqtt.Client()
        self._setup_mqtt()
        
    def _setup_mqtt(self):
        """Configure MQTT client with TLS"""
        self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.mqtt_client.tls_set(
            ca_certs=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS
        )
        self.mqtt_client.tls_insecure_set(False)
        
    def connect_mqtt(self):
        """Establish MQTT connection with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                self.mqtt_client.loop_start()
                logger.info("Successfully connected to MQTT broker")
                return True
            except Exception as e:
                logger.error(f"MQTT connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Max connection retries reached")
                    return False
    
    def read_sensor_data(self):
        """Read all available metrics from PZEM-017"""
        try:
            if not self.modbus.connect():
                logger.error("Modbus connection failed")
                return None
                
            response = self.modbus.read_input_registers(address=0, count=10, slave=SLAVE_ADDRESS)
            
            if response.isError():
                logger.error(f"Modbus error: {response}")
                return None
                
            return {
                "voltage": response.registers[0] / 10.0,        # V
                "current": response.registers[1] / 1000.0,      # A
                "power": response.registers[3] / 10.0,          # W
                "energy": response.registers[5] / 1000.0,       # kWh
                "frequency": response.registers[7] / 10.0,      # Hz
                "power_factor": response.registers[8] / 100.0,  # PF
                "alarms": response.registers[9]                 # Alarm status
            }
            
        except Exception as e:
            logger.error(f"Read error: {str(e)}")
            return None
            
        finally:
            self.modbus.close()
    
    def publish_data(self):
        """Main execution loop"""
        while True:
            start_time = time.time()
            
            sensor_data = self.read_sensor_data()
            if sensor_data:
                payload = {
                    "timestamp": int(time.time()),
                    "data": sensor_data
                }
                
                try:
                    result = self.mqtt_client.publish(
                        MQTT_TOPIC,
                        json.dumps(payload),
                        qos=1
                    )
                    
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        logger.info(f"Published data: {json.dumps(payload)}")
                    else:
                        logger.error(f"Publish failed: {result.rc}")
                        
                except Exception as e:
                    logger.error(f"MQTT publish error: {str(e)}")
            
            # Calculate sleep time to maintain consistent interval
            processing_time = time.time() - start_time
            sleep_time = max(0, UPDATE_INTERVAL - processing_time)
            time.sleep(sleep_time)

if __name__ == "__main__":
    reader = PZEM017Reader()
    
    if reader.connect_mqtt():
        try:
            reader.publish_data()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            reader.mqtt_client.disconnect()
            reader.modbus.close()
    else:
        logger.error("Failed to establish MQTT connection. Exiting.")