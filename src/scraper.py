from src.models import SubwayStation
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import numpy as np
import geocoder

CODES = "https://moovitapp.com/index/en/public_transit-lines-NYCNJ-121-855111"
SITE = "https://moovitapp.com/index/en/"


def yieldLineLinks():
    arr = []
    resp = requests.get(CODES)
    soup = BeautifulSoup(resp.content, 'html.parser')
    with open('html_pages/content.html', 'w', encoding='utf-8') as f:
        f.write(str(resp.content))
        f.close()
    for list_item in soup.find_all("li", {"class": "line-item"}):
        a = list_item.find("a")
        href = a['href']
        line_name = href.split('-')[2]
        arr.append([line_name, SITE + href])
    return arr


def save(name, content):
    with open('html_pages/{0}.html'.format(name), 'w', encoding='utf-8') as f:
        f.write(str(content))


class StationScraper:
    def __init__(self, line, url):
        self.line = line
        self.url = url

    def scrape(self):
        try:
            return requests.get(self.url)
        except requests.exceptions.RequestException as e:
            print("{}: Couldn't connect to {}".format(e, self.url))
            return None


class Parser:
    def __init__(self, content):
        self.content = content
        self.soup = BeautifulSoup(content, 'html.parser')

    def get_station_names(self):
        station_names = []
        for wrapper in self.soup.find_all("div", {"class": "stop-wrapper"}):
            station_name = ' '.join(wrapper.find("h3").text.split(' ')[:-1])
            station_names.append(station_name)
        return np.array(station_names).T

    def get_station_lines(self):
        station_lines = []
        for wrapper in self.soup.find_all("div", {"class": "stop-wrapper"}):
            lines = wrapper.find("h3").text.split(' ')[-1][1:-1]
            station_lines.append(lines)
        return np.array(station_lines).T

    def get_station_entrances(self):
        station_entrances = []
        for wrapper in self.soup.find_all("div", {"class": "stop-wrapper"}):
            text = wrapper.find("span").text
            if text == '' or text is None:
                entrance = ''
            else:
                entrance = text.split(',')[0].lstrip().rstrip()
            station_entrances.append(entrance)
        return np.array(station_entrances).T

    def get_station_boroughs(self):
        station_boroughs = []
        for wrapper in self.soup.find_all("div", {"class": "stop-wrapper"}):
            text = wrapper.find("span").text
            if text == '' or text is None:
                borough = ''
            else:
                borough = text.split(',')[1].lstrip().rstrip()
            station_boroughs.append(borough)
        return np.array(station_boroughs).T



def get_coordinates(addresses, boroughs):
    latitude = []
    longitude = []
    for address, borough in zip(addresses, boroughs):
        try:
            g = geocoder.osm('{}, {}, New York'.format(address, borough)).json
            latitude.append(g['lat'])
            longitude.append(g['lng'])
        except:
            latitude.append(None)
            longitude.append(None)

    return np.array(latitude).T, np.array(longitude).T



if __name__ == "__main__":
    folder = "html_pages"
    pages = os.listdir(folder)
    pages = ['{}/{}'.format(folder, page) for page in pages if len(page) <= 7]

    columns = ['station_name', 'borough', 'entrance', 'lines', 'latitude', 'longitude']
    output = pd.DataFrame(columns=columns)

    for page in pages:
        with open(page, 'r') as f:
            content = f.read()
        parser = Parser(content)
        stations = parser.get_station_names()
        lines = parser.get_station_lines()
        entrances = parser.get_station_entrances()
        boroughs = parser.get_station_boroughs()
        latitude, longitude = get_coordinates(addresses=entrances, boroughs=boroughs)
        csv = pd.DataFrame(np.column_stack((stations, boroughs, entrances, lines, latitude, longitude)), columns=columns)
        csv.to_csv('data/{}.csv'.format(page.split('/')[1].split('.')[0]),
                   index=False)

    exit(0)