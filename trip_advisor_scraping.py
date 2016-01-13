#!/usr/bin/python
from bs4 import BeautifulSoup
from urllib2 import urlopen
from time import sleep # be nice
from urlparse import urlparse
import json
import sys
import re


# Attractions
urls = [
"http://www.tripadvisor.com/Attractions-g189473-Activities-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
"http://www.tripadvisor.com/Attractions-g189473-Activities-oa30-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
"http://www.tripadvisor.com/Attractions-g189473-Activities-oa60-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
"http://www.tripadvisor.com/Attractions-g189473-Activities-oa90-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html",
]
userId = "tripadvisor_poiscrapper"

url = "http://www.tripadvisor.com/Attractions-g189473-Activities-Thessaloniki_Thessaloniki_Region_Central_Macedonia.html#ATTRACTION_LIST"
for url in urls:
    hostname = urlparse(url).hostname
    soup = BeautifulSoup(urlopen(url).read(), "lxml")

    for elem in soup.select("div.wrap.al_border.attraction_element"):
        poiname = elem.select("div.property_title")[0].select("a")[0].text
        urlsuf  = elem.select("div.property_title")[0].select("a")[0]['href']
        tags    = [ tag.text for tag in elem.select("div.p13n_reasoning_v2")[0].select("span") ]
        fullurl = "http://" + hostname + "/" + urlsuf


        # Get javascript
        soup = BeautifulSoup(urlopen(fullurl).read(), "lxml")
        # Find element that contains the "CurrentCenter.png" and lat,lon
        for script in soup.find_all('script'):
            latlon = re.findall("(?<=CurrentCenter.png\|)(.*)(?=\&language)", script.text)
            if (latlon):
        # Match text between "CurrentCenter.png|" and "&language". Will get something like "40.6383,22.94802"
        #latlon = re.findall("(?<=CurrentCenter.png\|)(.*)(?=\&language)", script_69)
                latlon_arr = latlon[0].split(",")
                latitude = latlon_arr[0]
                longitude = latlon_arr[1]
                break

        poi = {
            "name" : poiname,
            "url" : fullurl,
            "tags" : tags,
            "latitude" : latitude,
            "longitude" : longitude,
            "userId" : userId,
        }
        print json.dumps(poi)


