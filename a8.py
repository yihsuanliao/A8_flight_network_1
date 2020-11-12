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
import sys
import datetime, threading
from collections import defaultdict

airports = pd.read_csv("airports.csv")
countries = pd.read_csv("countries.csv")


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


result = open("result.txt", 'w')

"""
def output(l):
    print(l)
    threading.Timer(5, output).start()
"""
"""
startpoint = line[9] # (row1) # '00:18:19.169'
startpoint = startpoint.split(":") # ['00', '18', '19.169']
startpoint = int(startpoint[1])
interval = 5
if line[9] == startpoint + interval: # 0 + 5
    -> output data
    startpoint = line[9] # 5
"""
# TODO: complete this function




dic = defaultdict(list)
callsign_uni = []
g = nx.DiGraph()
startpoint = 0

for line in sys.stdin:
    line = line.split(",")
    callsign = line[10].strip()
    timestamp = line[9].strip()
    # print(timestamp[0:8])
    timestamp = timestamp[0:8]
    timestamp = timestamp.split(":")
    timestamp = int(timestamp[0]) * 3600 + int(timestamp[1]) * 60 + int(timestamp[2]) # 0
    interval = 5 * 60
    # print(startpoint)
    if timestamp == startpoint + interval:  # 0 + 5 = 5
        # TODO: create a output function and call

        # -> output data write a function
        #output()
        startpoint = timestamp # 5
        print("startpoint: ", startpoint)
    if callsign != "": # if callsign has value
        aircrafthex = line[4]
        if callsign not in dic[aircrafthex]: # we only want the unique callsigns for one aircrafthex
            dic[aircrafthex].append(callsign) # like {'a': [1, 2, 3], 'z': [6, 7]}
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
                    airport_name = airport_data["name"].values[0]
                    # type(airport_name)is a series
                    # Chicago O'Hare International Airport
                    # Louisville Muhammad Ali International Airport
                    # print(airport_name)
                    airport_lat = airport_data["latitude_deg"].values[0]
                    airport_long = airport_data["longitude_deg"].values[0]
                    country_name = airport_data["iso_country"].values[0]  # US
                    countries_data = (countries.loc[countries["code"] == country_name])["name"].values[0] # United States
                    # add node and those information
                    g.add_node(route[k], name=airport_name, country=countries_data, latitude=airport_lat,
                               longitude=airport_long)
                    if k != 0:  # if k = 0, there will be no distance
                        if g.has_edge(route[k - 1], route[k]) is False:  # if edge not exist, calculate distance
                            distance = cal_distance(airport_lat, airport_long, last_lat, last_long)
                            g.add_edge(route[k - 1], route[k], Flights=[callsign], distance=distance)
                        else:
                            # update flights attribute (append)
                            g[route[k - 1]][route[k]]['Flights'].append(callsign)
                    last_lat = airport_lat
                    last_long = airport_long
                    # if len(route) > 2:
                    # print("show nodes data", nx.get_node_attributes(g, 'longitude'))
                    # print("show nodes data", g.nodes)
                    # print("show edges:", g.edges.data())


# How many distinct airports have been discovered?
##print(airports['id'].nunique())
# answer: 58567

# List all the distinct countries with airports in the graph.
aircraft_list = pd.DataFrame(airports.groupby(['iso_country'])['name'].unique())
country_name = pd.DataFrame(countries.groupby(['code'])['name'].unique())
distinct_countries = pd.merge(aircraft_list,country_name, left_index = True, right_index = True, how = 'left').rename(columns = {"name_x": "Airports", "name_y": "Country"})
##print(distinct_countries)
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
out = nx.out_degree_centrality(g)
out_result = []
for key in out:
    # print(key)
    if out[key] == 0.0: # dead end
        out_result.append(key)
print("dead end: ", out_result)
"""Algorithms to calculate reciprocity in a directed graph."""



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
#the above is the source code from python documentation
overall_reciprocity(g)

def strongly_connected_components(G):
    preorder = {}
    lowlink = {}
    scc_found = {}
    scc_queue = []
    i = 0     # Preorder counter
    for source in G:
        if source not in scc_found:
            queue = [source]
            while queue:
                v = queue[-1]
                if v not in preorder:
                    i = i + 1
                    preorder[v] = i
                done = 1
                v_nbrs = G[v]
                for w in v_nbrs:
                    if w not in preorder:
                        queue.append(w)
                        done = 0
                        break
                if done == 1:
                    lowlink[v] = preorder[v]
                    for w in v_nbrs:
                        if w not in scc_found:
                            if preorder[w] > preorder[v]:
                                lowlink[v] = min([lowlink[v], lowlink[w]])
                            else:
                                lowlink[v] = min([lowlink[v], preorder[w]])
                    queue.pop()
                    if lowlink[v] == preorder[v]:
                        scc_found[v] = True
                        scc = {v}
                        while scc_queue and preorder[scc_queue[-1]] > preorder[v]:
                            k = scc_queue.pop()
                            scc_found[k] = True
                            scc.add(k)
                        yield scc
                    else:
                        scc_queue.append(v)

def is_strongly_connected(G):

    if len(G) == 0:
        raise nx.NetworkXPointlessConcept(
            """Connectivity is undefined for the null graph.""")

    print('If the graph is strongly connected?',len(list(strongly_connected_components(G))[0]) == len(G))
#the above is the source code from python documentation
is_strongly_connected(g)

def weakly_connected_components(G):
    seen = set()
    for v in G:
        if v not in seen:
            c = set(_plain_bfs(G, v))
            yield c
            seen.update(c)
def _plain_bfs(G, source):

    Gsucc = G.succ
    Gpred = G.pred

    seen = set()
    nextlevel = {source}
    while nextlevel:
        thislevel = nextlevel
        nextlevel = set()
        for v in thislevel:
            if v not in seen:
                yield v
                seen.add(v)
                nextlevel.update(Gsucc[v])
                nextlevel.update(Gpred[v])

def is_weakly_connected(G):
    """
    >>> g
    >>> is_weakly_connected(g)
    True
    """
    if len(G) == 0:
        raise nx.NetworkXPointlessConcept(
            """Connectivity is undefined for the null graph.""")

    print('If the graph is weekly connected?',len(list(weakly_connected_components(G))[0]) == len(G))

# the above is the source code from python documentation
is_weakly_connected(g)