"""
IS590 PR - Assignment 8
Group: Team 05
Author: Enshi Wang (netID) student num.
        Vivian Liao (yhliao4) 661311697
        Cheng Chen Yang (ccy3) 657920840
We discussed the steps and worked together through each questions via zoom.

TODO: ask teacher about output and coverage is not working.
TODO: reduce reluctant codes.
"""


# Import libraries.
import requests
import pandas as pd
import networkx as nx
from geographiclib.geodesic import Geodesic
geod = Geodesic.WGS84
import sys
from collections import defaultdict
import math


def cal_distance(last_latitude, last_longitude, airport_latitude, airport_longitude):
    """
    Calculate the distance between two airports
    :param last_latitude: the next latitude
    :param last_longitude: the next longtitude
    :param airport_latitude: the original latitude
    :param airport_longitude: the original longitude
    :return: the distance between 2 airports
    >>> cal_distance(-41.32, 174.81, 40.96, -5.50)
    10777.36
    >>> cal_distance(41.32, 174.81, 40.96, 5.50)
    5846.85
    """
    d = round(geod.Inverse(last_latitude, last_longitude, airport_latitude, airport_longitude)['s12'] / 1852.0, 2)
    return d


# result = open("result.txt", 'w')


def output(graph):
    """
    Display the output of the results.
    :param graph:
    :return:
    """
    one = get_distinct_airports(graph)
    print("Number of distinct airport:", one)
    two = get_distinct_countries(graph)
    print("All distinct countries with airports:", two)
    three = get_percentage(graph)
    print("Percentage of edges:", three)
    four = is_strong_connected(graph)
    print("The graph is strongly connected:", four)
    five_1 = is_weak_connected(graph)
    print("The graph is weakly connected:", five_1)
    five_2 = get_dead_ends(graph)
    print("All airports that are 'dead ends':", five_2)


# Query 1
def get_distinct_airports(graph: dict) -> int:
    """
    Calculate the distinct airports that have been discovered.
    :param graph:
    :return: n: number of distinct airports
    """
    n = len(nx.get_node_attributes(graph, 'name'))
    return n
# answer: 58567


# Query 2
def get_distinct_countries(graph: dict) -> list:
    """
    Function for listing all the distinct countries with airports in the graph.
    :param graph:
    :return: clist: list of the countries
    """
    # create an empty list
    clist = []
    country = nx.get_node_attributes(graph, 'country') # {"KORD": United States...}
    for key in country:
        c = country[key]
        if c not in clist:
            clist.append(c)
    return clist


# Query 3
def get_percentage(graph: dict) -> float:
    """
    Function for displaying the percentage of edges where the reverse edge also exists.
    :param graph:
    :return:the percentage of edges where the reverse edge also exists.
    """
    ans = nx.reciprocity(graph, nodes=None)
    # answer: 0.41047120418848165
    return ans


# Query 4
def is_strong_connected(graph: dict) -> bool:
    """
    Function for displaying if the graph is "strongly connected".
    :param graph:
    :return: True: the graph is strongly connected; False:the graph is not strongly connected
    """
    ans = nx.is_strongly_connected(graph)
    return ans


# Query 5 - 1
def is_weak_connected(graph: dict) -> bool:
    """
    Function for displaying if the graph is "weakly connected".
    :param graph:
    :return:True: the graph is strongly connected; False:the graph is not strongly connected
    """
    ans = nx.is_weakly_connected(graph)
    return ans


# Query 5 - 2
def get_dead_ends(graph) -> list:
    """
    List all airports that are "dead ends"
    :param graph:
    :return: output the airports that are dead ends
    """
    out = nx.out_degree_centrality(graph)
    out_result = []
    for key in out:
        if out[key] == 0.0:  # dead end
            out_result.append(key)
    return out_result


def get_time(l: str) -> int:
    """
    Get the time from the data and convert it into usable numbers.
    :param l:
    :return:list of time
    """
    # retrieve timestamp from line
    t = l[9].strip()
    t = t[0:8]
    t = t.split(":")
    t = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])  # 0
    return t


def get_info(data): # airport data
    """
    Get the information needed from the data file.
    :param data:
    :return: data information needed
    """
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
    """
    This is the main function to process airport data, call other functions and add nodes.
    :return:
    """
    dic = defaultdict(list)
    callsign_uni = []
    g = nx.DiGraph()
    startpoint = math.inf
    for line in sys.stdin:
        line = line.split(",")
        callsign = line[10].strip()
        timestamp = get_time(line)
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
                        info = get_info(airport_data)
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

    # Load data and create as variables.
    airports = pd.read_csv("airports.csv")
    countries = pd.read_csv("countries.csv")
    main()