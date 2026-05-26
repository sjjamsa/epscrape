import os

required = [
    "URL",
    "INFLUX_URL",
    "INFLUX_TOKEN",
    "INFLUX_ORG",
    "INFLUX_BUCKET"
]

for key in required:
    value = os.environ.get(key)

    if not value:
        raise RuntimeError(f"Missing env variable: {key}")

URL           = os.environ["URL"]
INFLUX_URL    = os.environ["INFLUX_URL"]
INFLUX_TOKEN  = os.environ["INFLUX_TOKEN"]
INFLUX_ORG    = os.environ["INFLUX_ORG"]
INFLUX_BUCKET = os.environ["INFLUX_BUCKET"]
