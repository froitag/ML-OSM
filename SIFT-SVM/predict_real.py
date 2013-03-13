'''
Created on 08.03.2013

@author: andre
'''
import algo
import os

### NEEDS: svm model + codebook file (k-means clusters for generating the histograms)
SVM_MODEL_PATH = '../data/svm.pkl'
CODEBOOK_FILE = '../data/codebook'

DATASETPATH = '../data/patches48/test'
TMP_DIR = '../data/tmp/test/'


if (__name__ == "__main__"):
    try:
        os.makedirs(TMP_DIR)
    except:
        None        
    
    algo.__clear_dir(TMP_DIR)
    predictions = algo.predict(SVM_MODEL_PATH, CODEBOOK_FILE, DATASETPATH, TMP_DIR)
    
    print "\n\nPredictions:"
    for filepath, is_building in predictions.items():
        filename = os.path.basename(filepath)
        coverage, x, y = os.path.splitext(filename)[0].split('_')
        print '{coverage}: {is_building}'.format(coverage=coverage, is_building=is_building[0])


print 'done'

