#!/usr/local/bin/python2.7
# encoding: utf-8
'''
test1 -- testing wms server

test1 is a description
'''

from PIL import Image, ImageDraw
import numpy as np
import os
import sys

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

patch_size=96

force_refresh = False;

if not os.path.exists("dop.png") or force_refresh:
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



if not os.path.exists("osm-data.json") or force_refresh:

    query = '[out:json];way["building"](' + str(min_lat) + ',' + str(min_lon) + ',' + str(max_lat) + ',' + str(max_lon) + ');out qt body;>;out skel;'
    import urllib
    url = 'http://overpass-api.de/api/interpreter?data=' + urllib.quote_plus(query)
    
    import urllib2
    
    json_file = urllib2.urlopen(url)
    f = open('osm-data.json', 'w')
    f.write(json_file.read())
    f.close()


json_file = open('osm-data.json', 'r')
print "parsing json document"
import json
data = json.load(json_file)


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

try:
    os.mkdir('patches'+str(patch_size))
except:
    None

import shapely.geometry

print "doing buildings processing"


img_raw = img.copy()
draw = ImageDraw.Draw(img) 
bmap = Image.new('1', size, 0)
bdraw = ImageDraw.Draw(bmap)

for building in buildings:
    sys.stdout.write('.')
    ring = [nodes[node_id] for node_id in building['nodes']];
    area = shapely.geometry.Polygon(ring)
    draw.rectangle(area.bounds, outline='blue') 
    draw.polygon(ring, outline='red')
    bdraw.polygon(ring, fill=1)
    center = area.representative_point()



for x in xrange(0,size[0],patch_size):
    for y in xrange(0,size[1],patch_size):  
        box = [x, y, x+patch_size, y+patch_size]
        
        #calculate coverage: how many pixels in current patch are part of a building?
        patch = bmap.crop(box)
        pixel = patch.load()
        result = 0
        for i in range(0, patch_size):
            for j in range(0, patch_size):
                result += pixel[i, j]
        coverage = result / float(patch_size**2)
        if (coverage != 0.0) and (coverage != 1.0): 
            patch.save('patches{size}/{coverage:.3f}_{x:04d}_{y:04d}_mask.png'.format(x=x, y=y, coverage=coverage,size=patch_size))
            
        #draw.rectangle(box, fill=0xffffff ) 
        #crop patch and save to file
        patch = img_raw.crop(box)
        patch.save('patches{size}/{coverage:.3f}_{x:04d}_{y:04d}.png'.format(x=x, y=y, coverage=coverage,size=patch_size))
        


#img.show()  
#bmap.show()      
print "done"    

#import pdb; pdb.set_trace()

