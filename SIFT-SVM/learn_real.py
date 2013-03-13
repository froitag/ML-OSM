'''
Created on 08.03.2013

@author: andre
'''

from os.path import isdir, basename, join, splitext
from os import makedirs
from glob import glob
import argparse
import algo
from numpy import sqrt

#DATASETPATH = 'data/train_real/'
DATASETPATH = 'C:/Users/andre/Dropbox/ML-HA/Final Project/grid_patches20'
SIFT_CODEBOOK = 'data/codebook' 
SVM_MODEL_FILE = 'data/svm.pkl'
TMP_DIR = 'data/tmp/train/'#algo.__clear_dir('data/tmp/train/')

EXTENSIONS = [".jpg", ".bmp", ".png", ".pgm", ".tif", ".tiff"]


def parse_arguments():
    parser = argparse.ArgumentParser(description='train a visual bag of words model')
    parser.add_argument('-d', help='path to the dataset', required=False, default=DATASETPATH)
    args = parser.parse_args()
    return args

def get_categories(datasetpath):
    cat_paths = [files
                 for files in glob(datasetpath + "/*")
                  if isdir(files)]
    cat_paths.sort()
    cats = [basename(cat_path) for cat_path in cat_paths]
    return cats

def get_imgfiles(path):
    all_files = []
    all_files.extend([join(path, basename(fname)).replace("\\","/")
                    for fname in glob(path + "/*")
                    if splitext(fname)[-1].lower() in EXTENSIONS])
    return all_files



if __name__ == '__main__':
    try:
        makedirs(TMP_DIR)
    except:
        None

    algo.__clear_dir(TMP_DIR)
    args = parse_arguments()
    datasetpath = args.d
    
    cats = [0,1]
    ncats = len(cats)
    
    
    print "---------------------"
    print "## loading the images and extracting the sift features"
    
    # list files
    all_files = get_imgfiles(datasetpath)
    all_labels = {}
    all_weights = {}
    for i in all_files:
        certainty = float(i.replace("\\","/").rpartition("/")[2].partition("_")[0])
        label = 1 if certainty > 0 else 0
        all_labels[i] = label
        all_weights[i] = certainty if label == 1 else 1-certainty
        
    '''all_labels = {}
    class0 = get_imgfiles("data/train/0/")
    for f in class0:
        all_labels[f] = 0
    class1 = [f for f in get_imgfiles("data/train/1/")]
    for f in class1:
        all_labels[f] = 1
    all_files = class0
    all_files.extend(f for f in class1)'''
    
    # extract features
    featureCount = algo.extract_features(all_files, TMP_DIR)

    # generate codebook
    clusterCount = int(sqrt(featureCount))
    algo.gen_codebook(
                      TMP_DIR, 
                      clusterCount,
                      SIFT_CODEBOOK,
                      batch_size = algo.BATCH_SIZE if algo.BATCH_SIZE >= clusterCount else clusterCount)
    
    # generate histograms
    algo.compute_histograms(
                            TMP_DIR,
                            SIFT_CODEBOOK,
                            TMP_DIR)
    
    # train svm 
    algo.train_svm(
                   TMP_DIR,
                   all_labels,
                   SVM_MODEL_FILE,
                   all_weights = all_weights
                   )
