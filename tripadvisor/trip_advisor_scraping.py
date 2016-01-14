#!/usr/bin/python
from bs4 import BeautifulSoup
from urllib2 import urlopen
from time import sleep # be nice
from urlparse import urlparse
import json
import sys
import re

urls = [
    "http://www.tripadvisor.com/Attractions-g189473-Activities-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
    "http://www.tripadvisor.com/Attractions-g189473-Activities-oa30-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
    "http://www.tripadvisor.com/Attractions-g189473-Activities-oa60-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
    "http://www.tripadvisor.com/Attractions-g189473-Activities-oa90-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
]

#===============================================================================
# getPoiName ()
#===============================================================================
def getPoiName(elem):
    return elem.select("div.property_title")[0].select("a")[0].text

#===============================================================================
# getUrl ()
#===============================================================================
def getUrl(elem, baseurl):
    urlsuffix = elem.select("div.property_title")[0].select("a")[0]['href']
    return baseurl + "/" + urlsuffix

#===============================================================================
# getTags ()
#===============================================================================
def getTags(elem):
    return [ tag.text for tag in elem.select("div.p13n_reasoning_v2")[0].select("span") ]

#===============================================================================
# getLonLat ()
#===============================================================================
def getLonLat(poiurl):
    # Get javascript
    soup = BeautifulSoup(urlopen(poiurl).read(), "lxml")
    # Find element that contains the "CurrentCenter.png" and lat,lon
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
# main ()
#===============================================================================
def main():
    features = []
    for url in urls:
        hostname = urlparse(url).hostname
        soup = BeautifulSoup(urlopen(url).read(), "lxml")
        for elem in soup.select("div.wrap.al_border.attraction_element"):
            poiname = getPoiName(elem)
            fullurl = getUrl(elem, "http://" + hostname)
            tags = getTags(elem)
            lonlat = getLonLat(fullurl)
            if (not isinstance(lonlat, list)):
                continue
            longitude = lonlat[0]
            latitude = lonlat[1]

            # Each poi -> GeoJSON feature
            feature = {
                "type": "Feature",
                "properties": {
                    "name" : poiname,
                    "url" : fullurl,
                    "tag" : tags,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [ float(longitude), float(latitude) ]
                }
            }
            features.append(feature)

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
