'''
Created on 08.03.2013

@author: andre
'''
import algo
import os
import patch_generator
from PIL import Image, ImageDraw
import json

### NEEDS: svm model + codebook file (k-means clusters for generating the histograms)
SVM_MODEL_FILE = '../data/svm.pkl'
SIFT_CODEBOOK_FILE = '../data/codebook'
HYPERPARAMETERS_FILE = '../data/svm.pkl.info.json'

DATASET_DIR = '../data/patches/test'
TMP_DIR = '../data/tmp/test/'

SATELLITE_IMG_BBOX=(11.60339,48.17708,11.61304,48.18326) ; SATELLITE_IMG_SIZE=(1500, 1000) ; SATELLITE_IMG_TMP="dopA.png" # between Grasmeier and Crailsheimerstr.
SATELLITE_IMG_VISUALIZATION_INPUT="dopA-annotated.png"
SATELLITE_IMG_VISUALIZATION_OUTPUT="../data/dopA-predictions.png"
#SATELLITE_IMG_BBOX =(11.59221,48.17038,11.61233,48.18380) ; SATELLITE_IMG_SIZE=(2000, 2000) ; SATELLITE_IMG_TMP="dopB.png" # bigger as above.
#SATELLITE_IMG_VISUALIZATION_INPUT="dopB-annotated.png"
#SATELLITE_IMG_VISUALIZATION_OUTPUT="dopB-predictions.png"
#important: a must be smaller than c, b must be smaller then d


if (__name__ == "__main__"):
    
    # init
    try:
        os.makedirs(DATASET_DIR)
    except:
        None
    algo.__clear_dir(DATASET_DIR)
    try:
        os.makedirs(TMP_DIR)
    except:
        None
    algo.__clear_dir(TMP_DIR)
    
    with open(HYPERPARAMETERS_FILE, "r") as f:
        params = json.loads(f.read())
    
    
    # generate patches
    print "---------------------"
    print "## generating patches from '" + SATELLITE_IMG_TMP + "' (" + str(SATELLITE_IMG_SIZE[0])+"x"+str(SATELLITE_IMG_SIZE[1]) + "; " + str(SATELLITE_IMG_BBOX) + ")"
    patch_generator.generate_patches(SATELLITE_IMG_BBOX, SATELLITE_IMG_SIZE, 
        patch_size=params['hyperparameters']['patch_size'], 
        offset_steps=params['hyperparameters']['patch_offset'],
        target_folder=DATASET_DIR,
        force_refresh=False,
        tmp_img_file=SATELLITE_IMG_TMP,
        tmp_dir=TMP_DIR
    )
    
    # predict
    print "---------------------"
    print "## predicting"
    predictions = algo.predict(SVM_MODEL_FILE, SIFT_CODEBOOK_FILE, DATASET_DIR, TMP_DIR)
    
    
    # generate visualization
    print "---------------------"
    print "## generating visualization"
    threshold = 0.4
    
    img = Image.open(SATELLITE_IMG_VISUALIZATION_INPUT)
    overlay = Image.new('RGB', img.size, 0)
    draw = ImageDraw.Draw(overlay)  
    
    print "\n\nPredictions:"
    for filepath, is_building in predictions.items():
        filename = os.path.basename(filepath)
        print filename
        coverage, x, y = os.path.splitext(filename)[0].split('_')
        x = int(x); y = int(y)
        print '{coverage}: {is_building}'.format(coverage=coverage, is_building=is_building[0])
        if is_building[0] == 1:
            draw.rectangle([x,y,x+48, y+48], fill='violet')
        else:
            draw.rectangle([x,y,x+48, y+48], fill='yellow')
    
    combined = Image.blend(img, overlay, 0.3) 
    combined.show()  
    combined.save(SATELLITE_IMG_VISUALIZATION_OUTPUT) 
    
    print "saved visualization to '" + SATELLITE_IMG_VISUALIZATION_OUTPUT + "' (violet := building detected; yellow := no building detected) "


print 'done'

