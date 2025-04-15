import time
import json
import spidev
from pymodbus.client import ModbusSerialClient
from paho.mqtt import client as mqtt
import logging
import ssl

# Configuration
HIVE_MQTT_BROKER = "4ad81ef75d944ea19791360d57b55735.s1.eu.hivemq.cloud"
HIVE_MQTT_PORT = 8883
HIVE_MQTT_TOPIC = "soalr/pzem-017"
HIVE_USER = "hivemq.webclient.1744393295548"
HIVE_PASS = "9BD8C42AbvfdrsFI,!*<"
PZEM_PORT = "/dev/ttyUSB0"
ACS712_CHANNEL = 0
ACS_ZERO = 1.65  # Calibrate this!
ACS_SENSITIVITY = 0.185

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnergyMonitor:
    def __init__(self):
        # PZEM-017 Setup
        self.pzem = ModbusSerialClient(
            method='rtu',
            port=PZEM_PORT,
            baudrate=9600,
            timeout=1
        )
        
        # ACS712 Setup
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1350000
        
        # MQTT Client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(HIVE_USER, HIVE_PASS)
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.mqtt_client.connect(HIVE_MQTT_BROKER, HIVE_MQTT_PORT)
        self.mqtt_client.loop_start()

    def read_pzem(self):
        try:
            if self.pzem.connect():
                response = self.pzem.read_input_registers(0x0000, 10, slave=1)
                return {
                    "voltage": response.registers[0] / 10.0,
                    "current": response.registers[1] / 1000.0,
                    "power": response.registers[3] / 10.0,
                    "energy": response.registers[5] / 1000.0
                }
        except Exception as e:
            logger.error(f"PZEM Error: {e}")
            return None
        finally:
            self.pzem.close()

    def read_acs712(self):
        try:
            adc = self.spi.xfer2([1, (8 + ACS712_CHANNEL) << 4, 0])
            raw = ((adc[1] & 3) << 8) + adc[2]
            voltage = (raw / 1023.0) * 5.0
            current = (voltage - ACS_ZERO) / ACS_SENSITIVITY
            return round(current, 2)
        except Exception as e:
            logger.error(f"ACS712 Error: {e}")
            return None

    def run(self):
        while True:
            start_time = time.time()
            
            solar_data = self.read_pzem()
            load_current = self.read_acs712()
            
            if solar_data and load_current is not None:
                payload = {
                    "timestamp": int(time.time()),
                    "solar": solar_data,
                    "load": {
                        "current": load_current,
                        "power": load_current * solar_data["voltage"]  # P = I*V
                    }
                }
                
                self.mqtt_client.publish(
                    HIVE_MQTT_TOPIC,
                    json.dumps(payload),
                    qos=1
                )
                logger.info(f"Published: {json.dumps(payload, indent=2)}")
            
            time.sleep(max(0, 5 - (time.time() - start_time)))

if __name__ == "__main__":
    monitor = EnergyMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        monitor.spi.close()
        monitor.mqtt_client.disconnect()