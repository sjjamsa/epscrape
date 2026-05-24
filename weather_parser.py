import re
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_conditions_timestamp(s: str):
    if not isinstance(s, str):
        return None

    # Clean whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Extract time + date part
    match = re.search(
        r"(\d{1,2}:\d{2})\s+\w+day,\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})",
        s
    )

    if not match:
        return None

    time_str, month_str, day, year = match.groups()

    # Parse components
    dt_naive = datetime.strptime(
        f"{year} {month_str} {day} {time_str}",
        "%Y %B %d %H:%M"
    )

    # Helsinki timezone (handles DST automatically)
    helsinki = ZoneInfo("Europe/Helsinki")
    dt_local = dt_naive.replace(tzinfo=helsinki)

    return dt_local.isoformat()

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s


def parse_number_unit(s: str):
    match = re.match(r"^(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z°/% ]+)?$", s)
    if not match:
        return None

    value_str, unit = match.groups()
    value_str = value_str.replace(",", ".")

    try:
        value = float(value_str)
    except ValueError:
        return None

    return {
        "value": value,
        "unit": unit.strip() if unit else None
    }

def parse_wind(s: str):
    s = normalize(s)

    if s in {"--", "-", "—", "°", "-- °"}:
        return {"direction": None, "degrees": None}

    dir_match = re.search(r"^[A-Za-z]+", s)
    deg_match = re.search(r"(\d+)\s*°", s)

    if not dir_match and not deg_match:
        return None

    return {
        "direction": dir_match.group(0) if dir_match else None,
        "degrees": int(deg_match.group(1)) if deg_match else None
    }

def split_time(s: str):
    parts = [p.strip() for p in s.split("|")]
    if len(parts) == 2:
        return parts[0], parts[1]
    return s, None

def old_parse_weather_value(s: str):
    if not isinstance(s, str):
        return {"str": str(s)}

    s = normalize(s)

    # Step 1: split optional time
    main, time = split_time(s)

    # Step 2: missing value
    if main in {"--", "-", "—"}:
        return {"value": None, "unit": None, "time": time}

    # Step 3: wind direction case
    if re.search(r"\b[NSEW]{1,3}\b", main) or "°" in main and re.search(r"[A-Za-z]", main):
        parsed = parse_wind(main)
        if parsed:
            if time:
                parsed["time"] = time
            return parsed

    # Step 4: number + unit (temperature, pressure, wind speed, etc.)
    parsed = parse_number_unit(main)
    if parsed:
        if time:
            parsed["time"] = time
        return parsed

    # Step 5: fallback
    return {"str": s}

def parse_weather_value(s: str):
    if not isinstance(s, str):
        return {"str": str(s)}

    s = normalize(s)

    main, time = split_time(s)

    # missing
    if main in {"--", "-", "—"}:
        return {"value": None, "unit": None, "time": time}

    # 1. NUMBER + UNIT FIRST (temperature, pressure, wind speed)
    num_unit = parse_number_unit(main)
    if num_unit:
        if time:
            num_unit["time"] = time
        return num_unit

    # 2. WIND ONLY if it does NOT match number+unit
    wind = parse_wind(main)
    if wind:
        if time:
            wind["time"] = time
        return wind

    # fallback
    return {"str": s}
