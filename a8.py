# import libraries
import requests
import lxml.html
import re
import pandas as pd

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
# print(af)
# save unique flight number
flight_num = (af.loc[af["Callsign/FlightNum"].notna()])["Callsign/FlightNum"].unique()
# get request from website and load into json
for i in range(len(flight_num)):
    flight_num[i] = flight_num[i].strip()
    url = "https://opensky-network.org/api/routes?callsign=" + flight_num[i]
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        print(r.json())
