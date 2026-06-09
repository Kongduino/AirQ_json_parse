import json, argparse, time, requests
from pathlib import Path
from meshtastic.protobuf import portnums_pb2, telemetry_pb2
from meshtastic import BROADCAST_ADDR
from secrets import *

# aiqRefNUM = "xxxxxxx"
# ipAddress = '10.0.1.x'

# For connection over serial
import meshtastic.serial_interface
#interface = meshtastic.serial_interface.SerialInterface(devPath="/dev/tty.xxxxxxxxx")

# For connection over TCP
import meshtastic.tcp_interface
interface = meshtastic.tcp_interface.TCPInterface(hostname=ipAddress, noProto=False)

print(interface)

def parse_escaped_json(value):
    """
    Parse an escaped JSON string into a real JSON object.
    Supported cases:
    1. Normal JSON string:
       {"sen55": {...}}
    2. Double-escaped JSON string:
       {\"sen55\": {...}}
    """
    if not isinstance(value, str):
        return value
    # Try to parse directly first
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    # Try to unescape one layer, then parse again
    try:
        unescaped = json.loads(f'"{value}"')
        return json.loads(unescaped)
    except json.JSONDecodeError:
        pass
    # Fallback: replace escaped quotes manually
    fixed_value = value.replace('\\"', '"')
    return json.loads(fixed_value)

def extract(input_file):
    # Generate output file names based on the input file name
    output_full_file = input_file.with_name(f"{input_file.stem}_parsed.json")
    output_raw_file = input_file.with_name(f"{input_file.stem}_raw_parsed.json")
    # Read the input JSON file
    with input_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Check required fields
    if "data" not in data:
        raise KeyError("Missing field: data")
    if "value" not in data["data"]:
        raise KeyError("Missing field: data.value")
    # Parse data.value
    raw_value = data["data"]["value"]
    parsed_value = parse_escaped_json(raw_value)
    # Write only the parsed raw content
#    with output_raw_file.open("w", encoding="utf-8") as f:
#        json.dump(parsed_value, f, ensure_ascii=False, indent=4)
    # Replace data.value with the parsed JSON object
#    data["data"]["value"] = parsed_value
#    data["data"]["dataType"] = "object"
    # Write the full JSON structure with parsed data.value
#    with output_full_file.open("w", encoding="utf-8") as f:
#        json.dump(data, f, ensure_ascii=False, indent=4)
#    print(f"Generated: {output_full_file}")
#    print(f"Generated: {output_raw_file}")
    return parsed_value

url = "https://ezdata2.m5stack.com/api/v2/" + aiqRefNUM + "/dataMacByKey/raw"
response = requests.get(url)

# Ensure the request succeeded
response.raise_for_status()

# Save the file content locally
with open("/tmp/raw.txt", "wb") as file:
    file.write(response.content)

input_file = Path("/tmp/raw.txt")
if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")
if not input_file.is_file():
    raise ValueError(f"Input path is not a file: {input_file}")
parsed_value = extract(input_file)
print(parsed_value)


telemetry_data = telemetry_pb2.Telemetry()
telemetry_data.time = int(time.time())
telemetry_data.air_quality_metrics.pm25_standard = int(parsed_value.get('sen55').get('pm2.5'))
telemetry_data.air_quality_metrics.pm10_standard = int(parsed_value.get('sen55').get('pm10.0'))
telemetry_data.air_quality_metrics.pm40_standard = int(parsed_value.get('sen55').get('pm4.0'))
telemetry_data.air_quality_metrics.pm_voc_idx = parsed_value.get('sen55').get('voc')
telemetry_data.air_quality_metrics.pm_nox_idx = parsed_value.get('sen55').get('nox')
telemetry_data.air_quality_metrics.pm_temperature = parsed_value.get('sen55').get('temperature')
telemetry_data.air_quality_metrics.pm_humidity = parsed_value.get('sen55').get('humidity')
telemetry_data.air_quality_metrics.co2 = parsed_value.get('scd40').get('co2')

print(telemetry_data)

interface.sendData(
    telemetry_data,
    destinationId=BROADCAST_ADDR,
    portNum=portnums_pb2.PortNum.TELEMETRY_APP,
    wantResponse=False,
)
# time.sleep(30)
# 
# telemetry_data = telemetry_pb2.Telemetry()
# telemetry_data.time = int(time.time())
# telemetry_data.environment_metrics.temperature = parsed_value.get('sen55').get('temperature')
# telemetry_data.environment_metrics.relative_humidity = parsed_value.get('sen55').get('humidity')
# telemetry_data.environment_metrics.barometric_pressure = 0
# telemetry_data.environment_metrics.gas_resistance = 0
# telemetry_data.environment_metrics.voltage = 0
# telemetry_data.environment_metrics.current = 0
# telemetry_data.environment_metrics.iaq = 0
# telemetry_data.environment_metrics.distance = 0
# telemetry_data.environment_metrics.lux = 0
# telemetry_data.environment_metrics.white_lux = 0
# telemetry_data.environment_metrics.ir_lux = 0
# telemetry_data.environment_metrics.uv_lux = 0
# telemetry_data.environment_metrics.wind_direction = 0
# telemetry_data.environment_metrics.wind_speed = 0
# telemetry_data.environment_metrics.wind_gust = 0
# telemetry_data.environment_metrics.wind_lull = 0
# telemetry_data.environment_metrics.weight = 0
# print(telemetry_data)
# 
# interface.sendData(
#     telemetry_data,
#     destinationId=BROADCAST_ADDR,
#     portNum=portnums_pb2.PortNum.TELEMETRY_APP,
#     wantResponse=False,
# )

interface.close()
