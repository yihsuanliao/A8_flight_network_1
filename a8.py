# import libraries
import requests
import lxml.html
import re
import pandas as pd
import networkx as nx
from geographiclib.geodesic import Geodesic
geod = Geodesic.WGS84

# use curl 99.74.38.205:30003 -o"livedata.csv" to load live data into file --> doesn't meet the requirement
# f = pd.read_csv("livedata.csv")
# print(f)

def load_adsb_file(filename: str) -> pd.DataFrame:
    """Load a file efficiently, retaining only the most useful columns & rows.
    The original DateLogged & TimeLogged get replaced by 'LoggedAt', as datetime64. Uses Pandas read_csv() with its compression='infer' option.
    :param filename: The path to the ADS-B data file. It may be compressed.
    """
    csv_columns = ['MessageType', 'TransmissionType', 'SessionID','AircraftID', 'AircraftHex', 'FlightRecorderNum', 'DateGenerated', 'TimeGenerated', 'DateLogged', 'TimeLogged', 'Callsign/FlightNum', 'Altitude', 'GroundSpeed', 'Track/Heading', 'Latitude', 'Longitude', 'VerticalRate', 'SquawkCode', 'Alert (Squawk Change)', 'Emergency', 'SPI', 'OnGround']
    columns_wanted = ['AircraftHex', 'DateLogged', 'TimeLogged', 'Callsign/FlightNum', 'Altitude', 'GroundSpeed', 'VerticalRate', 'OnGround', 'Latitude', 'Longitude']
    df = pd.read_csv(filepath_or_buffer=filename, compression='infer', names=csv_columns, usecols=columns_wanted, dtype={'Altitude': 'Int32', 'GroundSpeed': 'Float32', 'Track/Heading': 'Float32', })
    # Parse dates into proper datetime64:
    df['LoggedAt'] = pd.to_datetime(df['DateLogged'] + ' ' + df['TimeLogged'],
    format='%Y/%m/%d', errors='coerce')
    del df['DateLogged']
    del df['TimeLogged']
    return df
# load in the file
airtraffic = 'airtraffic_20200710.csv'
af = load_adsb_file(airtraffic)
airports = pd.read_csv("airports.csv")
countries = pd.read_csv("countries.csv")
# print(af)

# save unique flight number
flight_num = (af.loc[af["Callsign/FlightNum"].notna()])["Callsign/FlightNum"].unique()
# get request from website and load into json
for i in range(len(flight_num)):
    print("!") # 只是用來區分不同的fight_num跑出來的結果
    flight_num[i] = flight_num[i].strip()
    url = "https://opensky-network.org/api/routes?callsign=" + flight_num[i]
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        route = r.json()["route"]
        print(route) # ['KORD', 'KSDF']
        # 以下迴圈跑route中的點並取出需要的資訊
        for j in range(len(route)):
            airport_data = airports.loc[airports["ident"] == route[j]]
            airport_name = airport_data["name"]
            # type(airport_name)是一個series
            # 取出對應的機場名稱了，之後加入graph變成node
            airport_name = airport_name.values[0]
            # Chicago O'Hare International Airport
            # Louisville Muhammad Ali International Airport

            airport_lat = airport_data["latitude_deg"]
            airport_long = airport_data["longitude_deg"]
            position = []
            position.append(airport_lat, airport_long)

            print(airport_name)
            # G = nx.Graph()
            # G.add_node("airport_name")
            # 可能需要設last_position, current_position之類的變數來儲存位置，因為底下要算距離
            # geographic和networkx已經import了，可以直接用(geod, nx)


