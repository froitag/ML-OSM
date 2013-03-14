'''
Created on 08.03.2013

@author: andre
'''

from os import makedirs
import argparse
import algo
from numpy import sqrt
import patch_generator

DATASET_DIR = '../data/patches'
TMP_DIR = '../data/tmp/train/'

SIFT_CODEBOOK_FILE = '../data/codebook'
SVM_MODEL_FILE = '../data/svm.pkl'

SATELLITE_IMG_BBOX=(11.60339,48.17708,11.61304,48.18326) ; SATELLITE_IMG_SIZE=(1500, 1000) ; SATELLITE_IMG_TMP="dopA.png" # between Grasmeier and Crailsheimerstr.
#SATELLITE_IMG_BBOX =(11.59221,48.17038,11.61233,48.18380) ; SATELLITE_IMG_SIZE=(2000, 2000) ; SATELLITE_IMG_TMP="dopB.png" # bigger as above.
#important: a must be smaller than c, b must be smaller then d


def parse_arguments():
    parser = argparse.ArgumentParser(description='train a visual bag of words model')
    parser.add_argument('-d', help='path to the dataset', required=False, default=DATASET_DIR)
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    # init
    args = parse_arguments()
    DATASET_DIR = args.d
    
    cats = [0,1]
    ncats = len(cats)
    
    
    # generate and prepare folders
    try:
        makedirs(DATASET_DIR)
    except:
        None
    algo.__clear_dir(DATASET_DIR)
    try:
        makedirs(TMP_DIR)
    except:
        None
    algo.__clear_dir(TMP_DIR)
    
    
    # generate patches
    print "---------------------"
    print "## generating patches from '" + SATELLITE_IMG_TMP + "' (" + str(SATELLITE_IMG_SIZE[0])+"x"+str(SATELLITE_IMG_SIZE[1]) + "; " + str(SATELLITE_IMG_BBOX) + ")"
    patch_generator.generate_patches(SATELLITE_IMG_BBOX, SATELLITE_IMG_SIZE, 
        patch_size=48, 
        offset_steps=1,
        target_folder=DATASET_DIR,
        force_refresh=False,
        tmp_img_file=SATELLITE_IMG_TMP,
        tmp_dir=TMP_DIR
    )


    # list files
    all_files = algo.get_imgfiles(DATASET_DIR)
    all_labels = {}
    all_weights = {}
    for i in all_files:
        certainty = float(i.replace("\\","/").rpartition("/")[2].partition("_")[0])
        label = 1 if certainty > 0 else 0
        all_labels[i] = label
        all_weights[i] = certainty if label == 1 else 1-certainty
    
    
    # extract features
    print ""
    print "---------------------"
    print "## extracting SIFT features"
    featureCount = algo.extract_features(all_files, TMP_DIR)


    # generate codebook
    print "---------------------"
    print "## generating bag-of-words codebook"
    clusterCount = int(sqrt(featureCount))
    algo.gen_codebook(
                      TMP_DIR, 
                      clusterCount,
                      SIFT_CODEBOOK_FILE,
                      batch_size = algo.BATCH_SIZE if algo.BATCH_SIZE >= clusterCount else clusterCount)
    print "saved codebook to '" + SIFT_CODEBOOK_FILE + "'"
    
    
    # generate histograms
    print "---------------------"
    print "## generating histograms of the training examples"
    algo.compute_histograms(
                            TMP_DIR,
                            SIFT_CODEBOOK_FILE,
                            TMP_DIR)
    
    # train svm 
    print "---------------------"
    print "## training svm"
    algo.train_svm(
                   TMP_DIR,
                   all_labels,
                   SVM_MODEL_FILE,
                   all_weights = all_weights
                   )    
    print "saved svm to '" + SVM_MODEL_FILE + "'"
    
    print ""
    print "TRAINING SUCCEEDED"
