'''
Created on 12.03.2013

@author: andi
'''

from PIL import Image, ImageDraw
import os
import sys


debug = 1

def get_dop(bbox, size):
    from owslib.wms import WebMapService
    wms = WebMapService('http://geodaten.bayern.de/ogc/ogc_dop200_oa.cgi?', version='1.1.1')
    
    img = wms.getmap(
        layers=['adv_dop200c'],
        srs='EPSG:4326', # WGS84
        #srs='EPSG:31468', # GK4
        bbox=bbox,
        size=size,
        format='image/png'
    )
    
    # TODO 
    import cStringIO
    imgIO = cStringIO.StringIO(img.read())
    try:
        img = Image.open(imgIO)
        #img.show()
    except:
        print imgIO.read();   
    
    return img

def generate_patches(bbox, size, patch_size, target_folder = 'patches', force_refresh = False, offset_steps=1):

    if not os.path.exists("dop.png") or force_refresh:
        print "getting dop image from wms server"
        img = get_dop(bbox, size)
        img.save("dop.png")
    
    else:
        print "loading dop from disk"
        img = Image.open("dop.png")
    
    (min_lon, min_lat, max_lon, max_lat) = bbox
     
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
    
    # lonlon to 2d pixel
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
    
    try:
        os.mkdir(target_folder)
    except:
        None
    
    
    if debug > 0:
        img_raw = img.copy()
        draw = ImageDraw.Draw(img) 
        import shapely.geometry
    else:
        img_raw = img
       
    bmap = Image.new('1', size, 0)
    bdraw = ImageDraw.Draw(bmap)    

    print "buildings processing"

    for building in buildings:
        ring = [nodes[node_id] for node_id in building['nodes']];
        if debug > 0:
            area = shapely.geometry.Polygon(ring)
            draw.rectangle(area.bounds, outline='blue') 
            draw.polygon(ring, outline='red')
        bdraw.polygon(ring, fill=1)
        #center = area.representative_point()
    
    
    print "generating patches"
    for x in xrange(0, size[0]-patch_size, patch_size/offset_steps):
        sys.stdout.write('.')
        for y in xrange(0, size[1]-patch_size, patch_size/offset_steps): 
             
            box = [x, y, x+patch_size, y+patch_size]
            
            #calculate coverage: how many pixels in current patch are part of a building?
            patch = bmap.crop(box)
            pixel = patch.load()
            result = 0

            #sum up black pixel to get coverage
            for i in range(0, patch_size):
                for j in range(0, patch_size):
                    result += pixel[i, j]       
            coverage = result / float(patch_size**2)
            
            file_name = '{folder}/{coverage:.3f}_{x:04d}_{y:04d}'.format(
                    x=x, y=y, coverage=coverage,folder=target_folder
                )
            
            #save mask for the not extreme cases
            if (coverage != 0.0) and (coverage != 1.0): 
                patch.save(file_name + '_mask.png')    
            #draw.rectangle(box, fill=0xffffff ) 
            
            #crop patch and save to file
            patch = img_raw.crop(box)
            patch.save(file_name + '.png')
            
    if debug > 0:                
        img.show()  
        bmap.show() 
    