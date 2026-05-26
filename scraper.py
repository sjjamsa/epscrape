from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from weather_parser import *
from influx_writer import write_weather
from secrets import *



def parse_weather_string(s: str):
    if not isinstance(s, str):
        return {"str": str(s)}

    s = s.strip()

    # Split value and optional time
    parts = [p.strip() for p in s.split("|")]

    main = parts[0] if len(parts) > 0 else ""
    time = parts[1] if len(parts) > 1 else None

    # Match: number + unit (supports comma decimal separator)
    match = re.match(r"^(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z%°/]+)?$", main)

    if not match:
        return {"str": s}

    value_str, unit = match.groups()

    # Normalize decimal comma -> dot
    value_str = value_str.replace(",", ".")

    try:
        value = float(value_str)
    except ValueError:
        return {"str": s}

    result = {
        "value": value,
        "unit": unit
    }

    if time:
        result["time"] = time

    return result

def transform(value):
    #return parse_weather_string(value)
    return parse_weather_value(value)

def walk_json(obj, fn):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "values" and isinstance(v, list):
                obj[k] = [fn(x) for x in v]
            else:
                obj[k] = walk_json(v, fn)
        return obj

    elif isinstance(obj, list):
        return [walk_json(item, fn) for item in obj]

    else:
        return obj


    
def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    result = []

    rows = soup.select("tr.data-row")

    for row in rows:
        cols = row.find_all("td")

        item = {
            "name": cols[0].get_text(strip=True),
            "l10n_id": cols[0].get("data-l10n-id"),
            "values": [
                col.get_text(strip=True)
                for col in cols[1:]
        ]
        }

        result.append(item)
    return result


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="networkidle", timeout=3000)
    page.wait_for_timeout(3000)

    blocks = {
        "summary": page.query_selector("div.summary-block"),
        "wind": page.query_selector("div.wind-block"),
        "rain": page.query_selector("div.rain-block"),
    }
    columns={"summary": ["Current","Daily Highs","Daily Lows"],
             "wind": ["2 Minute","10 Minute"],
             "rain": ["Rate","hour","Day","Month","Year","Storm"],
             }
    # summary.

    updated =page.query_selector("span#conditionsUpdated").inner_html()

    jsons={}
    for name, el in blocks.items():
        if el:
            html = el.inner_html()
            #with open(f"{name}.html", "w", encoding="utf-8") as f:
            #    f.write(html)
            result = parse_html(html)
            #print(result)
            jsons[name]= result
            #jsons.append( json.dumps(result, indent=2) )
            #print(json.dumps(result, indent=2))


    browser.close()

    print(updated)
#    print(jsons)

combined = {
    "updated": updated,
    "columns": columns,
    "sensors": jsons
}

cleaned = walk_json(combined, transform)
cleaned['updated'] = parse_conditions_timestamp(combined['updated'])


with open("data/{}.json".format(cleaned['updated']), "w", encoding="utf-8") as f:
    f.write( json.dumps(cleaned, indent=2, ensure_ascii=False)) 

write_weather(cleaned)

#print(json.dumps(cleaned, indent=2))
