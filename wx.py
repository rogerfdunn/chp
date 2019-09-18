
from bs4 import BeautifulSoup
import requests

class Weather:

    def __init__(self):

        self.CityDict = {
            'Boulder Creek': 'Boulder Creek',
            'Ben Lomond': 'Ben Lomond',
            'Felton': 'Felton',
            'Aptos': 'Aptos',
            'Watsonville': 'Watsonville',
            'Indio': 'Indio',
            'Trinity River': 'Trinity Center',
            'Bakersfield': 'Bakersfield',
            'BF': 'Bakersfield',
            'Barstow': 'Barstow',
            'BS': 'Barstow',
            'Bridgeport': 'Bridgeport',
            'Bishop': 'Bishop',
            'Oceanside': 'Oceanside',
            'El Cajon': 'El Cajon',
            'Temecula': 'Temecula',
            'San Diego': 'San Diego',
            'Moorpark': 'Los Angeles',
            'Hanford': 'Hanford',
            'Redding': 'Redding',
            'Williams': 'Williams',
            'Morongo Basin': 'Joshua Tree National Park',
            'Antelope Valley': 'Antelope Valley',
            'Mount Shasta': 'Mount Shasta',
            'Chico': 'Chico',
            'Oroville': 'Oroville',
            'Victorville': 'Victorville',
            'Willows': 'Willows',
            'Yuba Sutter': 'Yuba City',
            'Winterhaven': 'Winterhaven',
            'Fresno': 'Fresno',
            'San Francisco': 'San Francisco',
            'Oakland': 'Oakland',
            'Dublin': 'Dublin',
            'San Jose': 'San Jose',
            'Hayward': 'Hayward',
            'Contra Costa': 'Contra Costa',
            'Redwood City': 'Redwood City',
            'Humboldt': 'Humboldt',
            'Riverside': 'Riverside',
            'Rancho Cucamonga': 'Rancho Cucamonga',
            'Santa Fe Springs': 'Santa Fe Springs',
            'Central LA': 'Los Angeles',
            'Baldwin Park': 'Baldwin Park',
            'Crescent City': 'Crescent City',
            'LA': 'Los Angeles',
            'SA': 'Sacramento',
            'MY': 'Salinas',
            'Mojave': 'Mojave',
            'West Valley': 'Los Angeles',
            'East LA': 'Los Angeles',
            'OCCC': 'Santa Ana',
            'West LA': 'Los Angeles',
            'South LA': 'Los Angeles',
            'Blythe': 'Blythe',
            'Newhall': 'Newhall',
            'IC': 'Palm Springs',
            'FR': 'Fresno',
            'IN': 'San Bernardino',
            'Clear Lake': 'Clear Lake',
            'Porterville': 'Porterville',
            'El Centro': 'El Centro',
            'UK': 'Ukiah',
            'SLCC': 'San Luis Obispo',
            'ST': 'Stockton',
            'EC': 'El Centro',
            'Santa Rosa': 'Santa Rosa',
            'Napa': 'Napa',
            'Visalia': 'Visalia',
            'Castro Valley': 'Castro Valley',
            'Solano': 'Solano',
            'Healdsburg': 'Healdsburg',
            'Santa Barbara': 'Santa Barbara',
            'Altadena': 'Altadena',
            'Madera': 'Madera',
            'HM': 'Humboldt',
            'Modesto': 'Modesto',
            'Buttonwillow': 'Buttonwillow',
            'Los Banos': 'Los Banos',
            'Santa Cruz': 'Santa Cruz',
            'Hollister Gilroy': 'Gilroy',
            'King City': 'King City',
            'Monterey': 'Monterey',
            'Monterey Dispatch': 'Salinas',
            'Westminster': 'Westminster',
            'Santa Ana': 'Santa Ana',
            'OC': 'Santa Ana',
            'Red Bluff': 'Red Bluff',
            'North Sac': 'Sacramento',
            'East Sac': 'Sacramento',
            'South Sac': 'Sacramento',
            'Auburn': 'Auburn',
            'Placerville': 'Placerville',
            'Davis': 'Davis',
            'Woodland': 'Woodland',
            'Templeton': 'Templeton',
            'San Luis Obispo': 'San Luis Obispo',
            'SL': 'San Luis Obispo',
            'Buellton': 'Buellton',
            'Stockton': 'Stockton',
            'San Andreas': 'San Andreas',
            'Tracy': 'Tracy',
            'Quincy': 'Quincy',
            'Susanville': 'Susanville',
            'CCCC': 'Contra Costa',
            'SU': 'Susanville',
            'Gold Run': 'Gold Run',
            'Ukiah': 'Ukiah',
            'Ventura': 'Ventura',
            'Yreka': 'Yreka',
            'Truckee': 'Truckee',
            'TK': 'Truckee',
            'MR': 'Merced',
            'Sonora': 'Sonora',
            'VTCC': 'Ventura',
            'South Lake': 'South Lake Tahoe',
            "Los Gatos": "Los Gatos",
            "Woodside": "Woodside",
            "WOODSIDE": "Woodside",
            'Needles': 'Needles',
            'San Bernardino': 'San Bernardino',
            'Santa Maria': 'Santa Maria',
            'Paso Robles': 'Paso Robles',
            'CH': 'Chico',
            'Marin': 'Marin',
            'Merced': 'Merced',
            'Alturas': 'Alturas',
            'Garberville': 'Garberville',
            'Capistrano': 'Capistrano',
            'LACC': 'Los Angeles',
            'Coalinga': 'Coalinga',
            'Fort Tejon': 'Fort Tejon',
            'Mariposa': 'Mariposa',
            'Merced Dispatch': 'Merced',
            'GG': 'Palo Alto',
            'Arrowhead': 'Arrowhead',
            'Grass Valley': 'Grass Valley',
            'Amador': 'Amador',
            'Oakhurst': 'Oakhurst',
            'San Gorgonio Pass': 'San Gorgonio Pass',
        }

        self.currentConditions = {}
        for name, station in self.CityDict.items():
            self.currentConditions[station] = {"Temperature": 0, "Conditions": ""}

    def get_station(self, name):
        url = "https://www.google.com/search"
        s = name.replace(" ", "+")
        param = "current+weather+{}+ca".format(s)
        params = {"q": param}
        try:
            response = requests.get(url, params=params)
        except Exception:
            return None
        doc = response.text
        return doc

    def update_stations(self):
        print "updating weather station data"
        for station in self.CityDict.values():
            print "getting {} weather data".format(station)
            doc = self.get_station(station)
            if doc is None:
                continue
            bs = BeautifulSoup(doc, 'html.parser')
            temperature_section = bs.find_all('div', attrs={'class': 'BNeawe iBp4i AP7Wnd'})
            cnt = len(temperature_section)
            if cnt == 2:
                target = str(temperature_section[1])
                temp = target[33:]
                z = temp.find("F<") - 2
                temp = temp[:z]
                self.currentConditions[station]["Temperature"] = temp
            conditions_section = bs.find_all('div', attrs={'class': 'BNeawe tAd8D AP7Wnd'})
            if len(conditions_section) > 1:
                c = str(conditions_section[1])
                s = c.find("\n")
                con = []
                s = s + 1
                while (c[s] != '<'):
                    con.append(c[s])
                    s += 1
                conditions = ''.join(con)
                self.currentConditions[station]["Conditions"] = conditions


    def get_wx(self, location):
        if location in self.CityDict:
            station = self.CityDict[location]
            return self.currentConditions[station]

        else:
            return None
