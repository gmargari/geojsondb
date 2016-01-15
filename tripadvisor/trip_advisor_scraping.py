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
    [ "http://www.tripadvisor.com/Attractions-g189473-PAGENUMBER-Activities-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html", 4, "poi" ],
    [ "http://www.tripadvisor.com/Restaurants-g189473-PAGENUMBER-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html", 20, "restaurant" ],
]

#===============================================================================
# createGeoJSONFeature ()
#===============================================================================
def createGeoJSONFeature(name, url, tags, longitude, latitude, feature_type):
    return {
        "type": "Feature",
        "properties": {
            "name" : name,
            "url" : url,
            "tag" : tags,
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
def getLonLat(poiurl):
    soup = BeautifulSoup(urlopen(poiurl).read(), "lxml")
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
# parsePoiPage ()
#===============================================================================
def parsePoiPage(soup, urlprefix):
    features = []
    for elem in soup.select("div.wrap.al_border.attraction_element"):
        fullurl = urlprefix + elem.select("div.property_title")[0].select("a")[0]['href']
        name = elem.select("div.property_title")[0].select("a")[0].text
        try:
            tags = [ tag.text for tag in elem.select("div.p13n_reasoning_v2")[0].select("span") ]
        except:
            tags = [ ]
        lonlat = getLonLat(fullurl)
        if (not isinstance(lonlat, list)):
            continue
        feature = createGeoJSONFeature(name, fullurl, tags, lonlat[0], lonlat[1], "POI")
        features.append(feature)
        print "  Parsed: " + fullurl

    return features

#===============================================================================
# parseRestaurantPage ()
#===============================================================================
def parseRestaurantPage(soup, urlprefix):
    features = []
    for elem in soup.select("div.shortSellDetails"):
        fullurl = urlprefix + elem.find_all('h3')[0].find_all('a')[0]['href']
        name = (elem.select("h3.title")[0].select("a")[0].text).strip()
        try:
            tags = [ tag.text for tag in elem.select("div.cuisines")[0].find_all('a') ]
        except:
            tags = [ ]
        lonlat = getLonLat(fullurl)
        if (not isinstance(lonlat, list)):
            continue
        feature = createGeoJSONFeature(name, fullurl, tags, lonlat[0], lonlat[1], "Restaurant")
        features.append(feature)
        print "  Parsed: " + fullurl

    return features

#===============================================================================
# main ()
#===============================================================================
def main():
    features = []
    for [ baseurl, maxpage, pagetype ] in baseurl_maxpage_list:
        # trip advisor pages are numbered oa0, oa30, oa60, etc.
        for page_inc in range(0, maxpage * 30, 30):
            url = baseurl.replace('PAGENUMBER', 'oa' + str(page_inc))
            print "Base: " + url
            try:
                hostname = urlparse(url).hostname
            except:
                break
            soup = BeautifulSoup(urlopen(url).read(), "lxml")
            urlprefix = "http://" + hostname + "/"
            if (pagetype == "poi"):
                page_features = parsePoiPage(soup, urlprefix)
            elif (pagetype == "restaurant"):
                page_features = parseRestaurantPage(soup, urlprefix)
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
