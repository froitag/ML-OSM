'''
Created on 08.03.2013

@author: andre
'''
from sklearn import svm
from numpy import loadtxt
import learn
import cPickle

from cPickle import load
from learn import extractSift, computeHistograms, writeHistogramsToFile

### NEEDS: svm model + codebook file (k-means clusters for generating the histograms)
SVM_MODEL_PATH = 'data/train/svm.pkl'
CODEBOOK_FILE = 'data/train/codebook.file'


HISTOGRAMS_FILE = 'data/test/testdata.svm'
        

DATASETPATH = "data/test/"

if (__name__ == "__main__"):
    with open(SVM_MODEL_PATH, 'rb') as fid:
        crf = cPickle.load(fid)
            
    
    print "---------------------"
    print "## extract Sift features"
    all_files = []
    all_files_labels = {}
    all_features = {}
    
    model_file = SVM_MODEL_PATH
    codebook_file = CODEBOOK_FILE
    
    
    files = learn.get_imgfiles(DATASETPATH)
    all_features = extractSift(files)
    for i in files:
        all_files_labels[i] = 0  # label is unknown
    
    print "---------------------"
    print "## loading codebook from " + codebook_file
    with open(codebook_file, 'rb') as f:
        codebook = load(f)
    
    print "---------------------"
    print "## computing visual word histograms"
    all_word_histgrams = {}
    for imagefname in all_features:
        word_histgram = computeHistograms(codebook, all_features[imagefname])
        all_word_histgrams[imagefname] = word_histgram
    
    print "---------------------"
    print "## write the histograms to file to pass it to the svm"
    nclusters = codebook.shape[0]
    writeHistogramsToFile(nclusters,
                          all_files_labels,
                          files,
                          all_word_histgrams,
                          HISTOGRAMS_FILE)
    
    print "---------------------"
    print "## test data with svm"
    inp = loadtxt(HISTOGRAMS_FILE, ndmin=2)
    samples = inp[::,1::]
    for i in range(len(files)):
        print files[i] + ": "
        print crf.predict(samples[i])