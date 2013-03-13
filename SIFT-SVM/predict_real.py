'''
Created on 08.03.2013

@author: andre
'''
import algo

### NEEDS: svm model + codebook file (k-means clusters for generating the histograms)
SVM_MODEL_PATH = '../data/svm.pkl'
CODEBOOK_FILE = '../data/codebook'

DATASETPATH = "../data/patches/test"
TMP_DIR = algo.__clear_dir('data/tmp/test/')


if (__name__ == "__main__"):
            
    algo.__clear_dir(TMP_DIR)
    predictions = algo.predict(SVM_MODEL_PATH, CODEBOOK_FILE, DATASETPATH, TMP_DIR)
    
    print "\n\nPredictions:"
    for img in predictions:
        print img + ": " + str(predictions[img])
