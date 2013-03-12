#!/usr/local/bin/python2.7
# encoding: utf-8
'''
test1 -- testing patch_generator

'''

import patch_generator


# lon between 180 E and 180 W
# lat between  90 N and  90 S
#     min lon  min lat   max lon  max lat
bbox=(11.60339,48.17708,11.61304,48.18326) 
#important: a must be smaller than c, b must be smaller then d

size=(1500, 1000)

patch_generator.generate_patches(bbox, size, 
    patch_size=48, 
    offset_steps=2,
    target_folder='patches48o.2',
    force_refresh=False
)

print ""     
print "done"    

