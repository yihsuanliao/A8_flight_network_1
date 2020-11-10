# import libraries
import requests
import lxml.html
import re
import pandas as pd
import networkx as nx
from geographiclib.geodesic import Geodesic
geod = Geodesic.WGS84
import matplotlib as plt

# use curl 99.74.38.205:30003 -o"livedata.csv" to load live data into file --> doesn't meet the requirement
# f = pd.read_csv("livedata.csv")
# print(f)


def cal_distance(last_latitude, last_longitude, airport_latitude, airport_longitude):
    d = round(geod.Inverse(last_latitude, last_longitude, airport_latitude, airport_longitude)['s12'] / 1852.0, 2)
    return d


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
g = nx.DiGraph()
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
        last_lat = 0
        last_long = 0
        distance = 0
        for j in range(len(route)):
            airport_data = airports.loc[airports["ident"] == route[j]]
            airport_name = airport_data["name"]
            # type(airport_name)是一個series
            # 取出對應的機場名稱了，之後加入graph變成node
            airport_name = airport_name.values[0]
            # Chicago O'Hare International Airport
            # Louisville Muhammad Ali International Airport

            airport_lat = airport_data["latitude_deg"].values[0]
            airport_long = airport_data["longitude_deg"].values[0]
            if j != 0:
                distance = cal_distance(airport_lat, airport_long, last_lat, last_long)
            last_lat = airport_lat
            last_long = airport_long
            print(distance)
            country_name = airport_data["iso_country"].values[0] # US
            countries_data = (countries.loc[countries["code"] == country_name])["name"].values[0]
            print(airport_name)
            print("countries_data", countries_data)
            g.add_node(route[j], name=airport_name, country=countries_data, latitude=airport_lat, longitude=airport_long)
            if j != 0:
                g.add_edge(route[j - 1], route[j], distance=distance)
            print("show nodes data", nx.get_node_attributes(g, 'longitude'))
            print("show edges:", g.edges.data())

# plt.draw_networkx_nodes(g, pos[list(g.nodes)])
