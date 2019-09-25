import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import pymysql
from wx import Weather
import re

url = 'http://cad.chp.ca.gov/Traffic.aspx'

dispatchCenters = [
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

dispatch_names = {
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

# Form data for submission
#
payload = {
    'ddlcomcenter': 'none',
    'ListMap': 'radList',
    'ddlResources': 'Choose One',
    'ddlSearches': 'Choose One',
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__LASTFOCUS': '',
}

# This will be used to gather secondary data from incidents. This data may or may not be present on the CHP server.
#
levelTwoLinks = []
levelTwoID = {}


# build searchable incident using dispatch incident, unique id for dispatchcenter


def buildIncidentIdentifier(incidentID, yesterday=False):
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


# For debugging - save a buffer to disk for examination
#
def saveToFile(doc):
    # file_ = open('debug.txt', 'w')
    # file_.write(doc)
    # file_.close()
    pass


# fixup orphaned end time where incident p
#
def fixupTime():
    conn = pymysql.connect(host='localhost', port=3306, user='mimosa', passwd='mimosa', db='chplog_db', autocommit=True)
    cur = conn.cursor()
    sql = "UPDATE TBL_Incidents set endtime = NOW() where startime = endtime;"
    cur.execute(sql)
    cur.close()
    conn.close()


# store data into MySQL database
#
def storeDetails(data, idx, k):
    callCenter = dispatchCenters[idx]
    incidentID, doy = buildIncidentIdentifier(levelTwoID[levelTwoLinks[k]])

    conn = pymysql.connect(host='localhost', port=3306, user='mimosa', passwd='mimosa', db='chplog_db', autocommit=True)
    cur = conn.cursor()

    data2 = conn.escape(data)
    callCenter2 = conn.escape(callCenter)
    incidentID2 = conn.escape(incidentID)

    # sql = "select DetailText from TBL_Incidents where dispatchcenter = " + callCenter2 + " and CHPIncidentID = " + incidentID2
    # cur.execute(sql)
    # for row in cur:
    #    result = row[0]

    sql = "UPDATE TBL_Incidents set DetailText = " + data2 + "where dispatchcenter = " + callCenter2 + " and CHPIncidentID = " + incidentID2
    cur.execute(sql)

    cur.close()
    conn.close()


def find_special(area, location):
    special = ["Boulder Creek", "BOULDER CREEK", "Felton", "FELTON", "Ben Lomond", "BEN LOMOND", "Tehachapi",
               "Aptos", "APTOS", "Watsonville", "WATSONVILLE", "Woodside", "WOODSIDE", "Paso Robles", "King City",
               "Los Gatos", "LOS GATOS", "Tehachapi", "Healdsburg", "Cloverdale", "Sonora", "Goleta", "Baker",
               "Parker Dam"]
    for item in special:
        if item in location:
            return item
    return area


def ignoreEvent(itype):
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


# store data into MySQL database
#
def storeRecord(data, rowIndex):
    try:
        itype = data[4]
        loc1 = data[5]
        loc2 = data[6]
        loc3 = data[7]
        area = loc3.lstrip()
        location = loc1 + ' ' + loc2 + ' - ' + loc3
        location = location.replace(u'\xa0', u' ')
        fsp = location[-3:]

        if ignoreEvent(itype):
            return

        # no FSP or MAZE/COZE
        if fsp != 'FSP':
            conn = pymysql.connect(host='localhost', port=3306, user='mimosa', passwd='mimosa', db='chplog_db',
                                   autocommit=True)
            cur = conn.cursor()

            callCenter = data[0]
            incidentID = data[2]

            loctext = location

            if incidentID == '01828':
                print 'sup'

            # used in the form as a parameter to obtain more detail about this incident
            #
            rtext = 'Select$' + str(rowIndex)
            global levelTwoID
            global levelTwoLinks

            levelTwoLinks.append(rtext)
            levelTwoID[rtext] = incidentID

            # CHP incident ids roll over at midnight, so we are prepending the
            # julian date as part of the iid for the database
            # This eliminates incorrect updates going to an older record.
            #
            iid, idoy = buildIncidentIdentifier(incidentID)

            # Check if this event is already in the database
            #
            sql = "SELECT COUNT(*) from TBL_Incidents where dispatchcenter = '{}' and CHPIncidentID = '{}'".format(
                callCenter, iid)

            try:
                cur.execute(sql)
            except Exception as e:
                print sql
                print e
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
                iid2, idoy = buildIncidentIdentifier(incidentID, yesterday=True)
                siid2 = str(iid2)
                loc2 = re.escape(loctext.encode('utf-8'))

                sql = "SELECT COUNT(*) FROM TBL_Incidents WHERE dispatchcenter = '{}' and CHPIncidentID='{}' and location = '{}'".format(
                    callCenter, siid2, loc2)

                try:
                    cur.execute(sql)
                except Exception as e:
                    print e
                    print sql
                    return
                result = 0
                for row in cur:
                    result = row[0]
                #
                # Found matching incident from prior day. Use data to update only
                #
                if result == 1:
                    doInsert = False
                    iid = iid2
            area = find_special(area, loc2)
            if len(area) == 0:
                area = dispatch_names[callCenter]
            weather_dict = weather.get_wx(area)
            if weather_dict is None:
                currentTemp = 0
                conditions = "Unknown station"
            else:
                currentTemp = weather_dict["Temperature"]
                conditions = weather_dict["Conditions"]
            # if not in the database, insert it
            if doInsert:
                sqla = "insert into TBL_Incidents(currentTemp,currentWeather,startime,endtime,dispatchcenter,CHPIncidentID,type,location, area) values "
                values = "({},'{}',NOW(),NOW(),'{}','{}','{}','{}','{}');".format(currentTemp, conditions, callCenter,
                                                                                  iid, itype, loc2, area)
                sql = sqla + values
            else:
                sql = "UPDATE TBL_Incidents set endtime = NOW(), type='{}' where dispatchcenter = '{}' and CHPIncidentID = '{}'".format(
                    itype, callCenter, iid)

            # saveToFile(sql)
            # print sql
            try:
                cur.execute(sql)
            except Exception as e:
                print e.message
                print sql

            cur.close()
            conn.close()
    except Exception as e:
        print e


# parse the main html document
#
def parseDom(doc, index):
    # Extract the data from html, if present
    #
    try:
        bs = BeautifulSoup(doc, 'html.parser')

        # Look for the gvIncidents table
        #
        table = bs.find(lambda tag: tag.name == 'table' and tag.has_key('id') and tag['id'] == "gvIncidents")

        if table is not None:
            cnt = 0
            rowIndex = -1  # first row is the header
            rows = table.find_all(lambda tag: tag.name == 'tr')
            for tr in rows:
                cols = tr.findAll('td')
                list = []
                list.append(dispatchCenters[index])
                for td in cols:
                    text = ''.join(td.find(text=True))
                    list.append(text)
                    cnt += 1
                if cnt:
                    storeRecord(list, rowIndex)
                rowIndex += 1
    except Exception as e:
        print e


# parse the main html document
#
def parseDetails(doc, index, k):
    details = ''
    # Extract the data from html, if present
    #
    bs = BeautifulSoup(doc, 'html.parser')

    # Look for the gvIncidents table
    #
    table = bs.find(lambda tag: tag.name == 'table' and tag.has_key('id') and tag['id'] == "tblDetails")

    if table is not None:
        rows = table.find_all(lambda tag: tag.name == 'tr')
        for tr in rows:
            cols = tr.findAll('td')
            for td in cols:
                text = ''.join(td.find(text=True))
                details += text
            details += '\n'
    storeDetails(details, index, k)


# main loop
#
def extractData():
    for index in range(len(dispatchCenters)):
        payload['ddlcomcenter'] = dispatchCenters[index]
        payload['__EVENTTARGET'] = ''
        payload['__EVENTARGUMENT'] = ''

        # reference the shared array here, clear it
        #
        global levelTwoLinks
        levelTwoLinks = []

        # Send a POST request to the url with the form data
        #
        try:
            response = requests.post(url, payload)
        except Exception as e:
            print e.message
            return

        doc = response.text

        try:
            parseDom(doc, index)
        except Exception as e:
            print e
            continue

        # gather the secondary incident data, if any
        #
        payload['__EVENTTARGET'] = 'gvIncidents'

        for k in range(len(levelTwoLinks)):
            payload['__EVENTARGUMENT'] = levelTwoLinks[k]

            # secondary post
            #
            s = requests.Session()
            s.headers.update({'Referer': 'http://cad.chp.ca.gov/traffic.aspx'})
            s.headers.update(
                {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0`'})
            try:
                response = requests.post(url, payload)
            except Exception as e:
                print e.message
                return

            doc = response.text
            parseDetails(doc, index, k)


# early am
#
def isEarlyAm():
    now = datetime.now()
    seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

    # midnight to 12:15
    #
    if seconds_since_midnight < 1200:
        return True
    return False


# IsNightTime
#
def isNightTime():
    now = datetime.now()
    seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

    # midnight to 6am
    #
    if seconds_since_midnight < 21600:
        return True
    return False


# main entry
#
if __name__ == '__main__':
    # loop forever
    idx = 1
    getWeather = 0
    weather = Weather()
    weather.update_stations()
    while 1:
        print("Getting data for iteration " + str(idx))
        try:
            extractData()
        except Exception as e:
            print e.message
        print("Start Delay")
        if isNightTime():
            time.sleep(800)  # wait 15 minutes
        else:
            time.sleep(600)  # wait 10 minutes
        fixupTime()
        getWeather += 1
        if getWeather > 3:
            weather.update_stations()
            getWeather = 0
        idx += 1
