# import libraries
import requests
import pandas as pd
import networkx as nx
from geographiclib.geodesic import Geodesic
geod = Geodesic.WGS84
import sys
from collections import defaultdict
import math

def cal_distance(last_latitude, last_longitude, airport_latitude, airport_longitude):
    """ Calculate the distance between two airports
    :param last_latitude:
    :param last_longitude:
    :param airport_latitude:
    :param airport_longitude:
    :return:
    >>> d = cal_distance(-41.32, 174.81, 40.96, -5.50)
    10777.36
    >>> d = cal_distance(41.32, 174.81, 40.96, 5.50)
    5846.85
    """
    d = round(geod.Inverse(last_latitude, last_longitude, airport_latitude, airport_longitude)['s12'] / 1852.0, 2)
    return d


# result = open("result.txt", 'w')


def output(graph):
    one = q1(graph)
    print("Q1:", one)
    two = q2(graph)
    print("Q2:", two)
    three = q3(graph)
    print("Q3:", three)
    four = q4(graph)
    print("Q4:", four)
    five_1 = q5_1(graph)
    print("Q5_1:", five_1)
    five_2 = q5_2(graph)
    print("Q5_2:", five_2)


def q1(graph: dict) -> int:
    # How many distinct airports have been discovered?
    n = len(nx.get_node_attributes(graph, 'name'))
    return n
# answer: 58567


def q2(graph: dict) -> list:
    # List all the distinct countries with airports in the graph.
    clist = []
    country = nx.get_node_attributes(graph, 'country') # {"KORD": United States...}
    for key in country:
        c = country[key]
        if c not in clist:
            clist.append(c)
    return clist


def q3(graph: dict) -> float:
    # Display the percentage of edges where the reverse edge also exists. That means where it’s possible to fly
    # directly from airport A to B, then directly back to A. [This is easy with the networkx reciprocity() function]
    ans = nx.reciprocity(graph, nodes=None)  # 算出來不知道對不對
    # answer: 0.41047120418848165
    return ans


def q4(graph: dict) -> bool:
    # Display if the graph is "strongly connected". That means it’s possible to somehow fly from each known airport
    # to any other. Use the is_strongly_connected() function!
    ans = nx.is_strongly_connected(graph)
    # 這裡還要再改，應該要是很多個true跟false，但我出來只有一個false
    return ans


def q5_1(graph: dict) -> bool:
    # Usually it will not be strongly connected. When it’s not, output these:
    # Display if the graph is "weakly connected"? That means ignoring direction of flight segments,
    # do all the airports have some sequence of flights connecting to the others?
    # Use the is_weakly_connected() function.
    ans = nx.is_weakly_connected(graph)
    return ans


def q5_2(graph) -> list:
    # Given the routes we have so far, list all airports that are "dead ends" (from which no known flight leaves).
    out = nx.out_degree_centrality(graph)
    out_result = []
    for key in out:
        if out[key] == 0.0:  # dead end
            out_result.append(key)
    return out_result


def time(l: str) -> int:
    # retrieve timestamp from line
    t = l[9].strip()
    t = t[0:8]
    t = t.split(":")
    t = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])  # 0
    return t


def getinfo(data): # airport data
    node_info = []
    node_info.append(data["name"].values[0])
    # Chicago O'Hare International Airport
    # Louisville Muhammad Ali International Airport
    node_info.append(data["latitude_deg"].values[0])
    node_info.append(data["longitude_deg"].values[0])
    country_name = data["iso_country"].values[0]  # US
    countries_data = (countries.loc[countries["code"] == country_name])["name"].values[0]  # United States
    node_info.append(countries_data)
    return node_info

def main():
    dic = defaultdict(list)
    callsign_uni = []
    g = nx.DiGraph()
    startpoint = math.inf
    for line in sys.stdin:
        line = line.split(",")
        callsign = line[10].strip()
        timestamp = time(line)
        interval = 15 * 60
        # when inputting a new data, setting a new startpoint from the first line in the new data
        # (it should be less than the old one)
        if timestamp <= startpoint:
            startpoint = timestamp
        # output the result every 15 minutes
        if timestamp >= startpoint + interval:  # 0 + 5 = 5
            output(g)
            startpoint = timestamp # 5
            print()
            # print(startpoint)
        if callsign != "":  # if callsign has value
            aircrafthex = line[4]
            if callsign not in dic[aircrafthex]:  # we only want the unique callsigns for one aircrafthex
                dic[aircrafthex].append(callsign)  # like {'a': [1, 2, 3], 'z': [6, 7]}
            # check if callsign appeared before
            # create a list for unique callsign, since we only need to get information from callsign when we first see it
            if callsign not in callsign_uni:
                callsign_uni.append(callsign)
                url = "https://opensky-network.org/api/routes?callsign=" + callsign
                r = requests.get(url)
                if r.status_code == requests.codes.ok:
                    route = r.json()["route"]
                    last_lat = 0
                    last_long = 0
                    distance = 0
                    for k in range(len(route)):
                        # get information(mane, lat, long, country) from each element in route
                        airport_data = airports.loc[airports["ident"] == route[k]]
                        info = getinfo(airport_data)
                        # print(info) # name, lat, long, country
                        # add node and those information
                        g.add_node(route[k], name=info[0], country=info[3], latitude=info[1],
                                   longitude=info[2])
                        if k != 0:  # if k = 0, there will be no distance
                            if g.has_edge(route[k - 1], route[k]) is False:  # if edge not exist, calculate distance
                                distance = cal_distance(info[1], info[2], last_lat, last_long)
                                g.add_edge(route[k - 1], route[k], Flights=[callsign], distance=distance)
                            else:
                                # update flights attribute (append)
                                g[route[k - 1]][route[k]]['Flights'].append(callsign)
                        last_lat = info[1]
                        last_long = info[2]
                        # print("show nodes data", g.nodes)
                        # print("show edges:", g.edges.data())


if __name__ == "__main__":

    # load data
    airports = pd.read_csv("airports.csv")
    countries = pd.read_csv("countries.csv")
    main()