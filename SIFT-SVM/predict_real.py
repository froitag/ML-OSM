'''
Created on 08.03.2013

@author: andre
'''
import algo
import os
from PIL import Image, ImageDraw

### NEEDS: svm model + codebook file (k-means clusters for generating the histograms)
SVM_MODEL_PATH = '../data/svm.pkl'
CODEBOOK_FILE = '../data/codebook'

DATASETPATH = '../data/patches48'
TMP_DIR = '../data/tmp/test/'


if (__name__ == "__main__"):
    try:
        os.makedirs(TMP_DIR)
    except:
        None        
    
    algo.__clear_dir(TMP_DIR)
    
    
    predictions = algo.predict(SVM_MODEL_PATH, CODEBOOK_FILE, DATASETPATH, TMP_DIR)

    
    img = Image.open('../data_acquisition/dop-annotated.png')
    overlay = Image.new('RGB', img.size, 0)
    draw = ImageDraw.Draw(overlay)  
    
    print "\n\nPredictions:"
    for filepath, is_building in predictions.items():
        filename = os.path.basename(filepath)
        coverage, x, y = os.path.splitext(filename)[0].split('_')
        x = int(x); y = int(y)
        #print '{coverage}: {is_building}'.format(coverage=coverage, is_building=is_building[0])
        if is_building[0] == 1:
            draw.rectangle([x,y,x+48, y+48], fill='violet')
        else:
            draw.rectangle([x,y,x+48, y+48], fill='yellow')
    
    combined = Image.blend(img, overlay, 0.3) 
    combined.show()  
    combined.save('../prediction_result.png')


print 'done'

