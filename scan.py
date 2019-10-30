import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import pymysql
from wx import Weather
import re
from DomCollector import DOMCollector


class CHPLogger:
    INCIDENT_TABLE = "TBL_Incidents"

    def __init__(self, weather):

        self.weather = weather
        self.dispatchCenters = [
            'GGCC',  # Golden Gate
            'BFCC',  # Bakersfield
            'BSCC',  # Barstow
            'BICC',  # Bishop
            'BCCC',  # Border
            'CHCC',  # Chico
            'ECCC',  # El Centro
            'FRCC',  # Fresno
            'HMCC',  # Humbold
            'ICCC',  # Indio
            'INCC',  # Inland
            'LACC',  # Los Angeles
            'MRCC',  # Merced
            'MYCC',  # Monterey
            'OCCC',  # Orange
            'RDCC',  # Redding
            'SACC',  # Sacramento
            'SLCC',  # San Luis Obispo
            'SKCCSTCC',  # Stockton
            'SUCC',  # Susanville
            'TKCC',  # Truckee
            'UKCC',  # Ukiah
            'VTCC',  # Ventura
            'YKCC',  # Yreka
        ]

        self.dispatch_names = {
            'BFCC': 'Bakersfield',
            'BSCC': 'Barstow',
            'BICC': 'Bishop',
            'BCCC': 'San Diego',
            'CHCC': 'Chico',
            'ECCC': 'El Centro',
            'FRCC': 'Fresno',
            'GGCC': 'Oakland',
            'HMCC': 'Shasta',
            'ICCC': 'Indio',
            'INCC': 'San Bernardino',
            'LACC': 'Los Angeles',
            'MRCC': 'Merced',
            'MYCC': 'Monterey',
            'OCCC': 'Santa Ana',
            'RDCC': 'Redding',
            'SACC': 'Sacramento',
            'SLCC': 'San Luis Obispo',
            'SKCCSTCC': 'Stockton',
            'SUCC': 'Susanville',
            'TKCC': 'Truckee',
            'UKCC': 'Ukiah',
            'VTCC': 'Ventura',
            'YKCC': 'Yreka'
        }

    def extractData(self):
        domCollector = DOMCollector()
        all_data = {}

        for dispatch in self.dispatchCenters:
            all_data[dispatch] = domCollector.GetDispatch(dispatch)

        for dispatch in self.dispatchCenters:
            self.store_events(dispatch, all_data[dispatch])

    def ignoreEvent(self, itype):
        if itype.startswith(u'Road/Weather'):
            return True
        if itype.startswith(u'CLOSURE of'):
            return True
        if itype.startswith(u'Assist'):
            return True
        if itype.startswith(u'Traffic Advisory'):
            return True
        if itype.startswith(u'Traffic Hazard'):
            return True
        if itype.startswith(u'Report of Fire'):
            return True
        if itype.startswith(u'Request CalTrans'):
            return True
        if itype.startswith(u'ESCORT for Road'):
            return True
        if itype.startswith(u'SILVER Alert'):
            return True
        if itype.startswith(u'Amber Alert'):
            return True
        if itype.startswith(u'Hazardous Materials'):
            return True

    def buildIncidentIdentifier(self, incidentID, yesterday=False):
        tt = datetime.now().timetuple()
        idoy = tt.tm_yday
        if yesterday:
            idoy -= 1
            if idoy == 0:
                idoy = 365
        year = str(tt.tm_year)
        # first 2 digits are year, followed by julian day of year, followed by chp issued incident id
        yeardig1 = year[2]
        yeardig2 = year[3]
        day_of_year = str(idoy)
        iid = yeardig1 + yeardig2 + day_of_year + incidentID
        return iid, idoy

    def find_special(self, area, location):
        special = ["Boulder Creek", "BOULDER CREEK", "Felton", "FELTON", "Ben Lomond", "BEN LOMOND", "Tehachapi",
                   "Aptos", "APTOS", "Watsonville", "WATSONVILLE", "Woodside", "WOODSIDE", "Paso Robles", "King City",
                   "Los Gatos", "LOS GATOS", "Tehachapi", "Healdsburg", "Cloverdale", "Sonora", "Goleta", "Baker",
                   "Parker Dam"]
        # hack to prevent Bakersfield from becoming 'Baker'
        if area == 'Bakersfield':
            return area
        for item in special:
            if item in location:
                return item
        return area

    def unicode_to_str(self, udata):
        details = eval(udata)
        details = details.replace('\\n', '\n')
        return details

    def merge_details(self, details, prev_details):
        new_text = details.splitlines()
        prev_text = prev_details.splitlines()
        if new_text == prev_text:
            return
        new_details = []
        for index in range(250):
            st = "[{}]".format(index+1)
            found = False
            for line in new_text:
                if line.find(st) >= 0:
                    new_details.append(line)
                    found = True
            if not found:
                for line in prev_text:
                    if line.find(st) >= 0:
                        new_details.append(line)
        result = "\r\n".join(new_details)
        return result

    def store_events(self, dispatch, data_dict):

        print "Processing {}".format(dispatch)
        # no current incident data
        if data_dict is None:
            return
        conn = pymysql.connect(host='192.168.100.142', port=3306, user='mimosa', passwd='mimosa',
                               db='chplog_db',
                               autocommit=True)
        cur = conn.cursor()
        for item in data_dict:
            try:
                data = data_dict[item]
                itype = data[3]
                loc1 = data[4]
                loc2 = data[5]
                loc3 = data[6]
                details = data[7]
                details = conn.escape(details)
                area = loc3.lstrip()
                location = loc1 + ' ' + loc2 + ' - ' + loc3
                location = location.replace(u'\xa0', u' ')
                fsp = location[-3:]
                if self.ignoreEvent(itype):
                    continue
                # no FSP or MAZE/COZE
                if fsp != 'FSP':
                    callCenter = dispatch
                    incidentID = data[1]
                    loctext = location

                    # CHP incident ids roll over at midnight, so we are prepending the
                    # julian date as part of the iid for the database
                    # This eliminates incorrect updates going to an older record.
                    #
                    iid, idoy = self.buildIncidentIdentifier(incidentID)

                    # Check if this event is already in the database
                    #
                    sql = "SELECT COUNT(*) from {} where dispatchcenter = '{}' and CHPIncidentID = '{}'".format(
                        CHPLogger.INCIDENT_TABLE,
                        callCenter, iid)
                    try:
                        cur.execute(sql)
                    except Exception as e:
                        continue
                    result = 0
                    for row in cur:
                        result = row[0]
                    doInsert = False

                    # if not in the database, insert it
                    if result == 0:
                        doInsert = True
                        #
                        # Check if this event is a day overlap event. Check incident id, location, dispatch center match for yesterday
                        #
                        iid2, idoy = self.buildIncidentIdentifier(incidentID, yesterday=True)
                        siid2 = str(iid2)
                        loc2 = re.escape(loctext.encode('utf-8'))

                        sql = "SELECT COUNT(*) FROM {} WHERE dispatchcenter = '{}' and CHPIncidentID='{}' and location = '{}'".format(
                            CHPLogger.INCIDENT_TABLE,
                            callCenter, siid2, loc2)
                        try:
                            cur.execute(sql)
                        except Exception as e:
                            print e
                            continue
                        result = 0
                        for row in cur:
                            result = row[0]
                        #
                        # Found matching incident from prior day. Use data to update only
                        #
                        if result == 1:
                            doInsert = False
                            iid = iid2
                    area = self.find_special(area, loc2)
                    if len(area) == 0:
                        area = self.dispatch_names[callCenter]
                    weather_dict = self.weather.get_wx(area)
                    if weather_dict is None:
                        currentTemp = 0
                        conditions = "Unknown station"
                    else:
                        currentTemp = weather_dict["Temperature"]
                        conditions = weather_dict["Conditions"]
                    # if not in the database, insert it
                    if doInsert:
                        sqla = "insert into {} (currentTemp,currentWeather,startime,endtime,dispatchcenter,CHPIncidentID,type,location, area,DetailText) values ".format(
                            CHPLogger.INCIDENT_TABLE)

                        values = "({},'{}',NOW(),NOW(),'{}','{}','{}','{}','{}',{});".format(currentTemp, conditions,
                                                                                          callCenter,
                                                                                          iid, itype, loc2, area,
                                                                                          details)
                        sql = sqla + values
                    else:
                        sql = "SELECT DetailText from {} where dispatchcenter = '{}' and CHPIncidentID = '{}' limit 1".format(CHPLogger.INCIDENT_TABLE, callCenter, iid)
                        cur.execute(sql)
                        prev_details = ""
                        for row in cur:
                            prev_details = str(row[0])
                        details = self.unicode_to_str(details)
                        details = self.merge_details(details, prev_details)
                        sql = "UPDATE {} set DetailText = {}, endtime = NOW(), type='{}' where dispatchcenter = '{}' and CHPIncidentID = '{}'".format(
                            CHPLogger.INCIDENT_TABLE,
                            details, itype, callCenter, iid)
                    try:
                        cur.execute(sql)
                    except Exception as e:
                        print e.message
                        continue
            except Exception as e:
                print e

        cur.close()
        conn.close()

    # fixup orphaned end time where incident p
    #
    def fixupTime(self):
        conn = pymysql.connect(host='192.168.100.142', port=3306, user='mimosa', passwd='mimosa', db='chplog_db',
                               autocommit=True)
        cur = conn.cursor()
        sql = "UPDATE {} set endtime = NOW() where startime = endtime".format(CHPLogger.INCIDENT_TABLE)
        cur.execute(sql)
        cur.close()
        conn.close()

    # early am
    #
    def isEarlyAm(self):
        now = datetime.now()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        # midnight to 12:15
        #
        if seconds_since_midnight < 1200:
            return True
        return False

    # IsNightTime
    #
    def isNightTime(self):
        now = datetime.now()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        # midnight to 6am
        #
        if seconds_since_midnight < 21600:
            return True
        return False


def main():
    # loop forever
    idx = 1
    getWeather = 0
    weather = Weather()
    chp_logger = CHPLogger(weather)
    weather.update_stations()
    while 1:
        print("Getting data for iteration " + str(idx))
        try:
            chp_logger.extractData()
        except Exception as e:
            print e.message
        print("Start Delay")
        if chp_logger.isNightTime():
            time.sleep(800)  # wait 15 minutes
        else:
            time.sleep(600)  # wait 10 minutes
        chp_logger.fixupTime()
        getWeather += 1
        if getWeather > 3:
            weather.update_stations()
            getWeather = 0
        idx += 1


if __name__ == "__main__":
    main()
