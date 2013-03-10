#!/usr/local/bin/python2.7
# encoding: utf-8
'''
test1 -- testing wms server

test1 is a description
'''

from PIL import Image, ImageDraw
from numpy import array, concatenate

'''
from pyproj import Proj
wgs84 = Proj(init='epsg:4326')
gk4 = Proj(init='epsg:31468')
'''

# lon between 180 E and 180 W
# lat between  90 N and  90 S
#                                          min lon  min lat   max lon  max lat
bbox=(min_lon, min_lat, max_lon, max_lat)=(11.60339,48.17708,11.61304,48.18326) #important: a must be smaller than c, b must be smaller then d
#bbox=(11.61722,48.18219,11.62081,48.18458)

#size=(1000, 1000)
size=(1500, 1000)

patch_size=array([20, 20])

if False:
    from owslib.wms import WebMapService
    wms = WebMapService('http://geodaten.bayern.de/ogc/ogc_dop200_oa.cgi?', version='1.1.1')
    
    print "getting dop image from wms server"
    img = wms.getmap(
        layers=['adv_dop200c'],
        srs='EPSG:4326', # WGS84
        #srs='EPSG:31468', # GK4
        bbox=bbox,
        size=size,
        format='image/png'
    )
    
    import cStringIO
    imgIO = cStringIO.StringIO(img.read())
    try:
        img = Image.open(imgIO)
        #img.show()
    except:
        print imgIO.read();   
    
    img.save("dop.png")

else:
    print "loading dop from disk"
    img = Image.open("dop.png")



query = '[out:json];way["building"](' + str(min_lat) + ',' + str(min_lon) + ',' + str(max_lat) + ',' + str(max_lon) + ');out qt body;>;out skel;'

import urllib
url = 'http://overpass-api.de/api/interpreter?data=' + urllib.quote_plus(query)

import json
import urllib2

print "parsing json document"
data = json.load(urllib2.urlopen(url))


scale = (
    size[0] / (max_lon - min_lon), 
    size[1] / (max_lat - min_lat)
);

# lonlat to 2d pixel
def ll2px (ll):
    (lon, lat) = ll
    px = (lon - min_lon) * scale[0]
    py = (max_lat - lat) * scale[1]

    return (px, py)
 


nodes = {}
buildings = []
print "creating buildings"

for element in data['elements']:
    if element['type'] == u'way':
        buildings.append(element);      
    elif element['type'] == u'node':
        lonlat = (element['lon'], element['lat'])
        nodes[int(element['id'])] = ll2px(lonlat)
    else:
        raise Exception("unexpected osm element type")

#import rtree


img_raw = img.copy()

draw = ImageDraw.Draw(img) 

draw.rectangle([100, 100, 120, 120], fill='blue')

import os
try:
    os.mkdir('patches')
except:
    None


for building in buildings:
    area = [];
    box = [None, None, None, None];
    for node_id in building['nodes']:
        coords = nodes[node_id]
        area.append(coords)
        # update bounding box
        if (box[0] is None) or (coords[0] < box[0]):
            box[0] = coords[0]
        if (box[1] is None) or (coords[1] < box[1]):
            box[1] = coords[1]
        if coords[0] > box[2]:
            box[2] = coords[0]
        if coords[1] > box[3]:
            box[3] = coords[1]
   
    draw.rectangle(box, outline='blue') 
    draw.polygon(area, outline='red')
    center = array([(box[0]+box[2])/2, (box[1]+box[3])/2])    
    patch_box = list(concatenate((center-patch_size/2, center+patch_size/2)).astype(int))
    
    # TODO check if center or patchbox is outside of the image

    
    draw.rectangle(patch_box, outline='green')
    patch = img_raw.crop(patch_box)
    patch.save('patches/' + str(building['id']) + '_c.png')
   
    

img.show()        
    

#import pdb; pdb.set_trace()

