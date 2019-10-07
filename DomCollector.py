import requests
from bs4 import BeautifulSoup


class DOMCollector:

    def __init__(self):
        self.levelTwoLinks = []
        self.levelTwoID = {}
        self.url = 'http://cad.chp.ca.gov/Traffic.aspx'
        self.payload = {
            'ddlcomcenter': 'none',
            'ListMap': 'radList',
            'ddlResources': 'Choose One',
            'ddlSearches': 'Choose One',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
        }

    def GetDispatch(self, dispatch):
        self.levelTwoLinks = []
        self.levelTwoID = {}
        self.payload['ddlcomcenter'] = dispatch
        self.payload['__EVENTTARGET'] = ''
        self.payload['__EVENTARGUMENT'] = ''
        content = {}
        # Send a POST request to the url with the form data
        #
        try:
            response = requests.post(self.url, self.payload)
        except Exception as e:
            print e.message
            return None
        doc = response.text
        try:
            bs = BeautifulSoup(doc, 'html.parser')
            # Look for the gvIncidents table
            #
            table = bs.find(lambda tag: tag.name == 'table' and tag.has_key('id') and tag['id'] == "gvIncidents")

            if table is not None:
                index = 0
                skip_header = 1
                rows = table.find_all(lambda tag: tag.name == 'tr')
                # for each incident
                for tr in rows:
                    cols = tr.findAll('td')
                    content[index] = []
                    # for each column in incident
                    for td in cols:
                        text = ''.join(td.find(text=True))
                        content[index].append(text)
                    if skip_header:
                        skip_header = False
                        continue
                    rtext = 'Select$' + str(index)
                    detail_dom = self.getDetails(token=rtext)
                    detail_text = self.get_detail_text(detail_dom)
                    content[index].append(detail_text)
                    index += 1
            else:
                return None
        except Exception as e:
            print e
            return None
        return content

    def get_detail_text(self, doc):
        details = ''
        bs = BeautifulSoup(doc, 'html.parser')
        table = bs.find(lambda tag: tag.name == 'table' and tag.has_key('id') and tag['id'] == "tblDetails")
        if table is not None:
            rows = table.find_all(lambda tag: tag.name == 'tr')
            for tr in rows:
                cols = tr.findAll('td')
                for td in cols:
                    text = ''.join(td.find(text=True))
                    details += text
                details += '\n'
        return details

    def getDetails(self, token):
        self.payload['__EVENTARGUMENT'] = token
        self.payload['__EVENTTARGET'] = 'gvIncidents'
        s = requests.Session()
        s.headers.update({'Referer': 'http://cad.chp.ca.gov/traffic.aspx'})
        s.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0`'})
        try:
            response = requests.post(self.url, self.payload)
        except Exception as e:
            print e.message
            return None
        return response.text
