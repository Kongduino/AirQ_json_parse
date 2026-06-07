import json
import argparse
from pathlib import Path

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

def main():
    parser = argparse.ArgumentParser(
        description="Parse escaped JSON content from data.value in a JSON file."
    )
    parser.add_argument(
        "input_file",
        help="Path to the JSON file that needs to be parsed, for example: TEST.json"
    )
    args = parser.parse_args()
    input_file = Path(args.input_file)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not input_file.is_file():
        raise ValueError(f"Input path is not a file: {input_file}")
    extract(input_file)

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
    with output_raw_file.open("w", encoding="utf-8") as f:
        json.dump(parsed_value, f, ensure_ascii=False, indent=4)
    # Replace data.value with the parsed JSON object
    data["data"]["value"] = parsed_value
    data["data"]["dataType"] = "object"
    # Write the full JSON structure with parsed data.value
    with output_full_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Generated: {output_full_file}")
    print(f"Generated: {output_raw_file}")

if __name__ == "__main__":
    main()
