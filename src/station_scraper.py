import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

VALID_LINES = ['1', '2', '3', '4', '6', '7', 'B', 'C', 'D', 'E', 'F']

'''
TODO: Fix '5' and '2'
'''
def main():
    lines = VALID_LINES.copy()
    stations = pd.DataFrame(columns=['Station', 'Entrances', 'Primary Line', 'Lines'])
    for line in lines:
        # Get the stations on the given line
        scraper = StationScraper(line)

        # if line == lines[-1]:
        #     line_df = scraper.get_page(save=True) \
        #         .parse_stations()
        # else:
        line_df = scraper.get_page_from_html('html_pages/{0}.html'.format(line)) \
            .parse_stations()




        # Create a CSV for the line. This CSV will be used to make the connections between station nodes
        line_df.to_csv('data/{0}.csv'.format(line), index=False)

        # Add the station name and lines to another CSV. This CSV will be used to create the nodes
        del line_df['Order'], line_df['Express']
        stations = pd.concat([stations, line_df])

        # Sleep to prevent possible IP ban
        # time.sleep(15)

    stations.to_csv('data/subway_stations.csv', index=False)


class StationScraper:

    def __init__(self, line):
        self.url = "https://new.mta.info/maps/subway-line-maps/{0}-line".format(str(line))
        self.page = None
        self.line = line

    def get_page(self, save=False):
        self.page = requests.get(self.url).content
        if save:
            self._save()
        return self

    def _save(self):
        with open('html_pages/{0}.html'.format(self.line), 'w', encoding='utf-8') as f:
            f.write(str(self.page))
            f.close()

    def _make_soup(self):
        return BeautifulSoup(self.page, 'html.parser')

    def get_page_from_html(self, f):
        try:
            with open(f, 'r') as f:
                self.page = f.read()
                f.close()
            return self
        except FileNotFoundError:
            raise FileNotFoundError

    def parse_stations(self):
        # Soup of Text Map Page for the given line
        soup = self._make_soup()

        # List of tables for each borough containing the stops for the given line in that borough
        station_table = soup.findAll("table", {"class", "mta-table-bordered"})
        boroughs = soup.findAll("h2", {"class": "mta-text-5xl mta-mt-500 mta-mb-050"})
        print(boroughs)
        results = [['Station', 'Order', 'Borough', 'Entrances', 'Primary Line', 'Express', 'Lines']]
        order = 0
        # Iterate through each borough table and get the stations
        for table, bor in zip(station_table, boroughs):

            # Get all of the stations for each borough, their features (local/express), and their transfers
            borough = bor.text.upper()\
                .replace('STATIONS', '')\
                .replace('BRANCH', '')\
                .replace('THE', '')\
                .lstrip().rstrip()
            if borough == "EASTCHESTER DYRE AVENUE" or borough == "NEREID AVENUE":
                borough = "BRONX"
                # order = 0

            stations = table.findAll("td", {"class", "col_0"})
            features = table.findAll("td", {"class", "col_4"})
            transfers = table.findAll("td", {"class", "col_3"})
            entrances = table.findAll("td", {"class", "col_1"})
            for i in range(0, len(stations)):

                # Get the name of each station in a given borough
                station_name = stations[i].find("p").text.lstrip().rstrip()
                station_name = self.fix_station_name(station_name)
                # Get the entrances
                entrance = entrances[i].find("p").text.lstrip().rstrip()
                entrance = entrance.replace('Avenue', 'Ave')\
                    .replace('Road', 'Rd')\
                    .replace('Street', 'St')\

                # Cleaned Entrances
                cleaned_entrances = entrance.split(',')[0]
                # cleaned_entrances = [x.lstrip().rstrip() for x in cleaned_entrances]


                # Add all of the lines in transfers and express from features to the comma-separated list of lines
                lines = self.line
                station_feature = features[i].find("p").text

                # Add $line-express if express is a feature
                is_express = False
                if 'express' in station_feature or 'expres' in station_feature:
                    is_express = True
                    lines += ',' + self.line + ' Express'

                # Add all of the transfer lines to the list of lines
                temp = transfers[i].find("p").text \
                    .rstrip().lstrip() \
                    .strip(' ').split(',')

                other_lines = [x.lstrip().rstrip()[0] for x in temp if x != ' ' and 'TRANSFER' not in x.upper() and "BUS" not in x.upper()]
                # other_lines = [x for x in other_lines if x in VALID_LINES]

                # Need to fix transfers for certain lines and stations
                if self.line == "3" and station_name == "Times Square-42 St":
                    other_lines[-1] = "2"
                if self.line == "1" and station_name == "Times Square-42 St":
                    other_lines[-1] = "3"
                    other_lines.append("7")

                if self.line == "C" and station_name == "Fulton St":
                    other_lines.append("3")

                other_lines = [x for x in other_lines if x in VALID_LINES]
                other_lines = ','.join(other_lines)
                lines += ',' + other_lines


                # Append results to output
                results.append([station_name, order, borough, cleaned_entrances, self.line, is_express, lines])

                # Increment order indicator
                order += 1

        return pd.DataFrame(results[1:], columns=results[0])


    def fix_station_name(self, station_name):
        temp = station_name.split('-')
        station_name = "-".join([x.lstrip().rstrip() for x in temp])
        fixed_station_name = station_name

        if station_name == "42 St Grand Central":
            fixed_station_name = "Grand Central 42 St"

        if station_name == "Atlantic Ave- Barclays Cty" or station_name == "Atlantic Av-Barclays Ctr":
            fixed_station_name = "Atlantic Ave-Barclays Ctr"

        if station_name == "Crown Hts Utica Av":
            fixed_station_name = "Crown Heights-Utica Av"

        if station_name == "Pelham Plwy":
            fixed_station_name = "Pelham Pkwy"

        if station_name == "Times Sq-42 St":
            fixed_station_name = "Times Square-42 St"

        if station_name == "Eastern Parkway-Brooklyn Museum":
            fixed_station_name = "Eastern Pkwy Brooklyn Museum"

        if station_name == "34 St-Penn Station":
            fixed_station_name = "34 St Penn Station"

        if station_name == "B'way-Lafayette St" or station_name == "B\\'way-Lafayette St" or station_name == "Bleeker St":
            fixed_station_name = "Bleecker St"

        if station_name == "161 Yankee Stadium":
            fixed_station_name = "161 St Yankee Stadium"


        if station_name == "Cathedral Pkwy (110 St)":
            fixed_station_name = "Cathedral Parkway (110 St)"

        if station_name == 'W 4 Wash Sq' or station_name == "W 4  St Wash Sq":
            fixed_station_name = "W 4 St Wash Sq"

        if station_name == "51 St":
            fixed_station_name = "Lexington Ave/ 53 St"

        if station_name == "Court Sq":
            fixed_station_name = "Court Sq-23 St"

        if station_name == "Forest Hills 71 Av":
            fixed_station_name = "Forest Hills-71 Av"

        if station_name == "Jay St MetroTech":
            fixed_station_name = "Jay St-MetroTech"

        if station_name == "Jackson Hts Roosevelt Av" or station_name == "Jackson Hts-Roosevelt Av":
            fixed_station_name = "Jackson Heights-Roosevelt Av"

        return fixed_station_name


if __name__ == "__main__":
    main()
