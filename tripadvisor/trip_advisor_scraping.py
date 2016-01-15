#!/usr/bin/python
from bs4 import BeautifulSoup
from urllib2 import urlopen
from time import sleep # be nice
from urlparse import urlparse
import json
import sys
import re

baseurl_maxpage_list = [
    # base ulr must contain the "-PAGENUMBER-" part. Number next to url is max page number to fetch
    [ "http://www.tripadvisor.com/Attractions-g189473-PAGENUMBER-Activities-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html", 4, "attraction" ],
    [ "http://www.tripadvisor.com/Restaurants-g189473-PAGENUMBER-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html", 20, "restaurant" ],
]

#===============================================================================
# AttractionParser ()
#===============================================================================
class AttractionParser:

    #===========================================================================
    # getElements ()
    #===========================================================================
    @staticmethod
    def getElements(soup):
        return soup.select("div.wrap.al_border.attraction_element")

    #===========================================================================
    # getName ()
    #===========================================================================
    @staticmethod
    def getName(elem):
        return elem.select("div.property_title")[0].select("a")[0].text

    #===========================================================================
    # getUrl ()
    #===========================================================================
    @staticmethod
    def getUrl(elem):
        return elem.select("div.property_title")[0].select("a")[0]['href']

    #===========================================================================
    # getTags ()
    #===========================================================================
    @staticmethod
    def getTags(elem):
        try:
            return [ tag.text for tag in elem.select("div.p13n_reasoning_v2")[0].select("span") ]
        except:
            return [ ]

#===============================================================================
# RestauranParser ()
#===============================================================================
class RestaurantParser:

    #===========================================================================
    # getElements ()
    #===========================================================================
    @staticmethod
    def getElements(soup):
        return soup.select("div.shortSellDetails")

    #===========================================================================
    # getName ()
    #===========================================================================
    @staticmethod
    def getName(elem):
        return elem.select("h3.title")[0].select("a")[0].text

    #===========================================================================
    # getUrl ()
    #===========================================================================
    @staticmethod
    def getUrl(elem):
        return elem.find_all('h3')[0].find_all('a')[0]['href']

    #===========================================================================
    # getTags ()
    #===========================================================================
    @staticmethod
    def getTags(elem):
        try:
            return [ tag.text for tag in elem.select("div.cuisines")[0].find_all('a') ]
        except:
            return [ ]

#===============================================================================
# createGeoJSONFeature ()
#===============================================================================
def createGeoJSONFeature(name, url, tags, longitude, latitude, feature_type):
    return {
        "type": "Feature",
        "properties": {
            "name" : name,
            "url" : url,
            "tags" : tags,
            "type" : feature_type,
        },
        "geometry": {
            "type": "Point",
            "coordinates": [ float(longitude), float(latitude) ]
        }
    }

#===============================================================================
# getLonLat ()
#===============================================================================
def getLonLat(url):
    soup = BeautifulSoup(urlopen(url).read(), "lxml")
    for script in soup.find_all('script'):
        # Match text between "CurrentCenter.png|" and "&language". Will get something like "40.6383,22.94802"
        latlon = re.findall("(?<=CurrentCenter.png\|)(.*)(?=\&language)", script.text)
        if (latlon):
            latlon_arr = latlon[0].split(",")
            latitude = latlon_arr[0]
            longitude = latlon_arr[1]
            return [ longitude, latitude ]
    return -1

#===============================================================================
# parsePage ()
#===============================================================================
def parsePage(soup, urlprefix, pagetype, parser):
    features = []
    for elem in parser.getElements(soup):
        try:
            fullurl = urlprefix + parser.getUrl(elem)
            name = parser.getName(elem).strip()
            tags = parser.getTags(elem)
            lonlat = getLonLat(fullurl)
            longitude = lonlat[0]
            latitude = lonlat[1]
        except:
            continue
        feature = createGeoJSONFeature(name, fullurl, tags, longitude, latitude, pagetype)
        features.append(feature)
        print "  Parsed: " + fullurl

    return features

#===============================================================================
# main ()
#===============================================================================
def main():
    features = []
    for [ baseurl, maxpage, pagetype ] in baseurl_maxpage_list:
        # tripadvisor url pages are numbered oa0, oa30, oa60, etc.
        for page_inc in range(0, maxpage * 30, 30):
            url = baseurl.replace('PAGENUMBER', 'oa' + str(page_inc))
            print "Base: " + url
            try:
                hostname = urlparse(url).hostname
            except:
                break
            soup = BeautifulSoup(urlopen(url).read(), "lxml")
            urlprefix = "http://" + hostname + "/"
            if (pagetype == "attraction"):
                page_features = parsePage(soup, urlprefix, pagetype, AttractionParser)
            elif (pagetype == "restaurant"):
                page_features = parsePage(soup, urlprefix, pagetype, RestaurantParser)
            if (len(page_features) > 0):
                features = features + page_features

    # Finalize GeoJSON format
    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }
    print json.dumps(geojson, sort_keys=True)

if __name__ == "__main__":
    main()
