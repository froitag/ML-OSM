'''
Created on 08.03.2013

@author: andre
'''

if __name__ == '__main__':
    from lib.sift.win import sift
    #import lib.sift.win.sift
    from PIL import Image
    from pylab import *
    
    print "no"
    sift.process_image('data/box.pgm','data/box.sift')
    print "JO"
    l,d = sift.read_features_from_file('data/box.sift')
    
    im = array(Image.open('data/box.pgm'))
    figure()
    sift.plot_features(im,l,True)
    gray()
    
    sift.process_image('data/scene.pgm','data/scene.sift')
    l2,d2 = sift.read_features_from_file('data/scene.sift')
    im2 = array(Image.open('data/scene.pgm'))    
    
    m = sift.match_twosided(d,d2)
    figure()
    sift.plot_matches(im,im2,l,l2,m)

    gray()
    show()
    pass