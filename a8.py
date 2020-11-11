# import libraries
import requests
import lxml.html
import re
import pandas as pd
import networkx as nx
#from python_utils import not_implemented_for
from networkx import NetworkXError
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
# flight_num = (af.loc[af["Callsign/FlightNum"].notna()])["Callsign/FlightNum"].unique()
callsign_lst = []
# select distinct aircrafthex to callsign
af = af.dropna(subset = ['Callsign/FlightNum'])
af2 = pd.DataFrame(af.groupby(['AircraftHex'])['Callsign/FlightNum'].unique())
# print(af2)
# aircraft_unique = list(af2.index)
aircraft_num = af2.shape[0] # 1032
callsign_col = af2["Callsign/FlightNum"]
g = nx.DiGraph()
# get request from website and load into json
for i in range(aircraft_num):
    #print("!") # 只是用來區分不同的fight_num跑出來的結果
    callsign_num = len(callsign_col.values[i]) # 有可能一個航班有一到三個callsign
    for j in range(callsign_num):
        flight_num = af2["Callsign/FlightNum"].values[i][j].strip()
        if flight_num not in callsign_lst:
            callsign_lst.append(flight_num)
            #print(callsign_lst)
            url = "https://opensky-network.org/api/routes?callsign=" + flight_num
            r = requests.get(url)
            if r.status_code == requests.codes.ok:
                route = r.json()["route"]
                #if len(route) > 2:
                    #print(route) # ['KORD', 'KSDF']
                # 以下迴圈跑route中的點並取出需要的資訊
                last_lat = 0
                last_long = 0
                distance = 0
                for k in range(len(route)):
                    airport_data = airports.loc[airports["ident"] == route[k]]
                    airport_name = airport_data["name"]
                    # type(airport_name)是一個series
                    # 取出對應的機場名稱了，之後加入graph變成node
                    airport_name = airport_name.values[0]
                    # Chicago O'Hare International Airport
                    # Louisville Muhammad Ali International Airport
                    #print(airport_name)

                    airport_lat = airport_data["latitude_deg"].values[0]
                    airport_long = airport_data["longitude_deg"].values[0]
                    if k != 0:
                        distance = cal_distance(airport_lat, airport_long, last_lat, last_long)
                    last_lat = airport_lat
                    last_long = airport_long
                    #print(distance)
                    country_name = airport_data["iso_country"].values[0] # US
                    countries_data = (countries.loc[countries["code"] == country_name])["name"].values[0]
                    #print(airport_name)
                    #print("countries_data", countries_data)
                    g.add_node(route[k], name=airport_name, country=countries_data, latitude=airport_lat, longitude=airport_long)
                    if k != 0:
                        g.add_edge(route[k - 1], route[k], distance=distance)
                    #if len(route) > 2:
                        #print("show nodes data", nx.get_node_attributes(g, 'longitude'))
                        #print("show nodes data", g.nodes)
                        #print("show edges:", g.edges.data())
# TODO: a LIST of all FlightNumbers seen that fly that same route
# 若FlightNumbers是指aircrafthex的話，再問問看是不是一個callsign只會有一個飛行路線，是的話跑callsign的list，然後看哪些aircrafthex有包含該callsign，就代表這些aircrafthex有相同的飛行路線
# 若是指callsign的話，就要把route拿出來，然後看和哪些callsign的route相符合 可能創個dic，key用route?，value用callsign
# 每跑一個callsign，就加到route的dic裡面，然後全部callsign跑完之後再處理attribute: flight？或是有其他方法(ex: 有沒有update之類的語法)

# select distinct aircrafthex to callsign
#af1 = pd.DataFrame(af.groupby(['Callsign/FlightNum'])['AircraftHex'].unique())
#af = af.dropna(subset = ['Callsign/FlightNum'])
#af2 = pd.DataFrame(af.groupby(['AircraftHex'])['Callsign/FlightNum'].unique())
#print("af2")
#print(af2)


# How many distinct airports have been discovered?
print(airports['id'].nunique())
# answer: 58567

# List all the distinct countries with airports in the graph.
aircraft_list = pd.DataFrame(airports.groupby(['iso_country'])['name'].unique())
country_name = pd.DataFrame(countries.groupby(['code'])['name'].unique())
distinct_countries = pd.merge(aircraft_list,country_name, left_index = True, right_index = True, how = 'left').rename(columns = {"name_x": "Airports", "name_y": "Country"})
print(distinct_countries)
# will have 242x2 rows

# Display the percentage of edges where the reverse edge also exists. That means where it’s possible to fly
# directly from airport A to B, then directly back to A. [This is easy with the networkx reciprocity() function]
nx.reciprocity(g, nodes = None)  # 算出來不知道對不對
# answer: 0.41047120418848165

# Display if the graph is "strongly connected". That means it’s possible to somehow fly from each known airport
# to any other. Use the is_strongly_connected() function!
nx.is_strongly_connected(g)
# 這裡還要再改，應該要是很多個true跟false，但我出來只有一個false


# Usually it will not be strongly connected. When it’s not, output these:
## Display if the graph is "weakly connected"? That means ignoring direction of flight segments, do all the airports have some sequence of flights connecting to the others? Use the is_weakly_connected() function.
## Giventherouteswehavesofar,listallairportsthatare"deadends"(fromwhichnoknownflight leaves).

"""Algorithms to calculate reciprocity in a directed graph."""


__all__ = ["overall_reciprocity"]

def overall_reciprocity(G):
    """Compute the reciprocity for the whole graph.
    See the doc of reciprocity for the definition.
    Parameters
    ----------
    G : graph
       A networkx graph
    """
    n_all_edge = G.number_of_edges()
    n_overlap_edge = (n_all_edge - G.to_undirected().number_of_edges()) * 2

    if n_all_edge == 0:
        raise NetworkXError("Not defined for empty graphs")
    print('The percentage of edges where the reverse edge also exists.',float(n_overlap_edge) / float(n_all_edge))

overall_reciprocity(g)