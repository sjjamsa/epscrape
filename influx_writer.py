from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import json
from secrets import *



client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = client.write_api(write_options=SYNCHRONOUS)



def write_weather(data: dict):
    timestamp = data.get("updated")

    # parse timestamp if you already converted it to ISO earlier
    time = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None

    points = []

    
    for sensor in data.get("sensors", {}).get("summary",{}) + data.get("sensors", {}).get("wind",{}) :
        #print(' ')
        #print(sensor)
        for key, val in sensor.items():
            #print(val)

            if key == 'name':
                name = val
            
            if not isinstance(val, list):
                #print('nolist')
                continue

            use_val = 0 # default
            if name == "Wind Gust Speed" or  name == "Avg Wind Speed":
                use_val = 1
                name += " (10min)"
            
            if "value" not in val[use_val] and 'degrees' not in val[use_val]:
                #print('novalues')
                continue

                        
            p = (
                Point("tower")
                .tag("sensor", name)
            )

            
            # add unit as tag if available
            if "value" in val[use_val]:
                if val[use_val].get("unit"):
                    p = p.tag("unit", val[use_val]["unit"])

                
                    # field value (Influx requires numeric or string field)
                    p = p.field("value", float(val[use_val]['value']) if val[use_val]['value'] is not None else None)
            elif "degrees" in val[use_val]:
                    p = p.tag("unit", "deg")

                
                    # field value (Influx requires numeric or string field)
                    p = p.field("value", float(val[use_val]['degrees']) if val[use_val]['degrees'] is not None else None)

            # optional timestamp
            if time:
                p = p.time(time)

            #print(p)
            points.append(p)

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

if __name__ == "__main__":
    import glob

    files=glob.glob('data/*')

    #print(files)
    #exit()

    for file in files:
        print(file)
        with open(file,'r') as f:
            data = json.load(f)
            write_weather(data)

