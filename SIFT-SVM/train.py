'''
Created on 08.03.2013

@author: andre
'''

import argparse
import algo
from numpy import sqrt
import patch_generator
import random
import os


''' CONFIG '''
TMP_DIR_TRAINING = '../data/tmp/train'
TMP_DIR_VALIDATION = '../data/tmp/validate'

DATASET_DIR = '../data/patches'
TRAININGSET_DIR = DATASET_DIR + "/train"
VALIDATIONSET_DIR = DATASET_DIR + "/validate"

SIFT_CODEBOOK_FILE = '../data/codebook'
SVM_MODEL_FILE = '../data/svm.pkl'

SATELLITE_IMG_BBOX=(11.60339,48.17708,11.61304,48.18326) ; SATELLITE_IMG_SIZE=(1500, 1000) ; SATELLITE_IMG_TMP="dopA.png" # between Grasmeier and Crailsheimerstr.
#SATELLITE_IMG_BBOX =(11.59221,48.17038,11.61233,48.18380) ; SATELLITE_IMG_SIZE=(2000, 2000) ; SATELLITE_IMG_TMP="dopB.png" # bigger as above.
#important: a must be smaller than c, b must be smaller then d


HYPERPARAMETERS_OPTIONS = {
    "patch_size": [48, 96],
    "patch_offset": [1,2],
    "codebook_size": [          # codebook size depending on overall sift key-point count
        lambda n: int(sqrt(n)),
        lambda n: 2*int(sqrt(n)),
        lambda n: 200
    ],
    "svm_c": [10, 100, 1000],
    "svm_gamma": [0.1, 0.2, 0.5, 1]
}
"""HYPERPARAMETERS_OPTIONS = {
    "patch_size": [48],
    "patch_offset": [1],
    "codebook_size": [          # codebook size depending on overall sift key-point count
        lambda n: int(sqrt(n))
     ],
    "svm_c": [1000],
    "svm_gamma": [1]
}"""



''' HELPERS '''
def parse_arguments():
    parser = argparse.ArgumentParser(description='train a visual bag of words model')
    parser.add_argument('-d', help='path to the dataset', required=False, default=DATASET_DIR)
    args = parser.parse_args()
    return args




''' MAIN '''
if __name__ == '__main__':

    # init
    args = parse_arguments()
    DATASET_DIR = args.d
    
    cats = [0,1]
    ncats = len(cats)
    
    
    # generate and prepare folders
    algo.__try_mkdirs(DATASET_DIR)
    algo.__try_mkdirs(TRAININGSET_DIR)
    algo.__try_mkdirs(VALIDATIONSET_DIR)
    algo.__try_mkdirs(TMP_DIR_TRAINING)
    algo.__try_mkdirs(TMP_DIR_VALIDATION)
    
    algo.__clear_dir(DATASET_DIR)
    algo.__clear_dir(TRAININGSET_DIR)
    algo.__clear_dir(VALIDATIONSET_DIR)
    
    
    # do training
    performances = []   # keep track of different parameter performances
    
    
    # iterate over different patch_sizes
    for patch_size in HYPERPARAMETERS_OPTIONS['patch_size']:
            
        hyperparameters = {}    # keep track of current hyperparameters
        performance = {}        # keep track of current performance
        
        hyperparameters['patch_size'] = patch_size
        print "HYPERPARAMETER: patch_size = " + str(patch_size)
        
        # iterate over different patch_offsets
        for patch_offset in HYPERPARAMETERS_OPTIONS['patch_offset']:
            hyperparameters['patch_offset'] = patch_offset
            print "HYPERPARAMETER: patch_offset = " + str(patch_offset)
        
            # generate patches
            print "---------------------"
            print "## generating patches from '" + SATELLITE_IMG_TMP + "' (" + str(SATELLITE_IMG_SIZE[0])+"x"+str(SATELLITE_IMG_SIZE[1]) + "; " + str(SATELLITE_IMG_BBOX) + ")"
            patch_generator.generate_patches(SATELLITE_IMG_BBOX, SATELLITE_IMG_SIZE, 
                patch_size=hyperparameters['patch_size'], 
                offset_steps=hyperparameters['patch_offset'],
                target_folder=DATASET_DIR,
                force_refresh=False,
                tmp_img_file=SATELLITE_IMG_TMP,
                tmp_dir=TMP_DIR_TRAINING
            )
            print ""
                    
            
            # iterate over different codebook_sizes
            dataset_split = 0
            for codebook_size in HYPERPARAMETERS_OPTIONS['codebook_size']:
                hyperparameters['codebook_size'] = codebook_size
                print "HYPERPARAMETER: codebook_size = " + str(codebook_size)
        
                # undo dataset splitting
                if dataset_split:
                    all_files = algo.get_imgfiles(TRAININGSET_DIR)
                    all_files.extend(algo.get_imgfiles(VALIDATIONSET_DIR))
                    
                    for f in all_files:
                        os.rename(f, DATASET_DIR + "/" + os.path.basename(f))
                    
        
                # list files
                all_files = algo.get_imgfiles(DATASET_DIR)
                all_labels = {}
                all_weights = {}
                for i in all_files:
                    certainty = float(i.replace("\\","/").rpartition("/")[2].partition("_")[0])
                    label = 1 if certainty > 0 else 0
                    all_labels[os.path.basename(i)] = label
                    all_weights[os.path.basename(i)] = certainty if label == 1 else 1-certainty
                
            
                # split into training and validation set
                print "---------------------"
                print "## splitting into training and validation set"
                
                dataset_size = len(all_files)
                trainingset_size = int(0.7 * dataset_size)
                validationset_size = dataset_size - trainingset_size
                performance['dataset_size'] = dataset_size
                performance['trainingset_size'] = trainingset_size
                performance['validationset_size'] = validationset_size
                
                i=0;
                for f in all_files:
                    forTraining = 0
                    if i < dataset_size:
                        rnd = random.randint(1, dataset_size)
                        forTraining = 1 if (rnd > validationset_size) else 0
                    os.rename(f, (TRAININGSET_DIR if forTraining else VALIDATIONSET_DIR) + "/" + os.path.basename(f))
                    i += 1 if forTraining else 0
                validation_files = algo.get_imgfiles(VALIDATIONSET_DIR)
        
                for j in range(i, trainingset_size):
                    index = j - i
                    os.rename(validation_files[index], TRAININGSET_DIR + "/" + os.path.basename(validation_files[index]))
            
                training_files = algo.get_imgfiles(TRAININGSET_DIR)
                validation_files = algo.get_imgfiles(VALIDATIONSET_DIR)
                dataset_split = 1
                
            
                # extract features
                print ""
                print "---------------------"
                print "## extracting SIFT features"
                algo.__clear_dir(TMP_DIR_TRAINING)
                featureCount = algo.extract_features(training_files, TMP_DIR_TRAINING)
                performance['sift_feature_count'] = featureCount
                
                
                # generate codebook
                print "---------------------"
                print "## generating bag-of-words codebook"
                clusterCount = hyperparameters['codebook_size'](featureCount)
                performance['codebook_size'] = clusterCount
                algo.gen_codebook(
                                  TMP_DIR_TRAINING, 
                                  clusterCount,
                                  SIFT_CODEBOOK_FILE,
                                  batch_size = algo.BATCH_SIZE if algo.BATCH_SIZE >= clusterCount else clusterCount)
                print "saved codebook to '" + SIFT_CODEBOOK_FILE + "'"
                
                
                # generate histograms
                print "---------------------"
                print "## generating histograms of the training examples"
                algo.compute_histograms(
                                        TMP_DIR_TRAINING,
                                        SIFT_CODEBOOK_FILE,
                                        TMP_DIR_TRAINING)
                
                
                # iterate over different svm_c
                for svm_c in HYPERPARAMETERS_OPTIONS['svm_c']:
                    hyperparameters['svm_c'] = svm_c
                    print "HYPERPARAMETER: svm_c = " + str(svm_c)
                    
                    
                    # iterate over different svm_gamma
                    for svm_gamma in HYPERPARAMETERS_OPTIONS['svm_gamma']:
                        hyperparameters['svm_gamma'] = svm_gamma
                        print "HYPERPARAMETER: svm_gamma = " + str(svm_gamma)
                    
                        
                        # train svm
                        print "---------------------"
                        print "## training svm"
                        algo.train_svm(
                                       TMP_DIR_TRAINING,
                                       all_labels,
                                       SVM_MODEL_FILE+str(len(performances)),
                                       all_weights = all_weights,
                                       C = hyperparameters['svm_c'],
                                       gamma = hyperparameters['svm_gamma']
                                       )
                        performance['hyperparameters'] = hyperparameters
                        
                        
                        # validate svm
                        print "---------------------"
                        print "## validating svm"
                        
                        TP = 0
                        FP = 0
                        TN = 0
                        FN = 0
                        
                        R = 0
                        I = 0
                        for f in validation_files:
                            if all_labels[os.path.basename(f)] == 1:
                                R += 1
                            else:
                                I += 1
                        
                        algo.__clear_dir(TMP_DIR_VALIDATION)
                        predictions = algo.predict(SVM_MODEL_FILE+str(len(performances)), SIFT_CODEBOOK_FILE, VALIDATIONSET_DIR, TMP_DIR_VALIDATION)
                        for f,p in predictions.items():
                            if p[0] == 1:
                                if all_labels[os.path.basename(f)] == 1:
                                    TP += 1
                                else:
                                    FP += 1
                            else:
                                if all_labels[os.path.basename(f)] == 1:
                                    FN += 1
                                else:
                                    TN += 1
                        TPR = float(TP) / float(R)
                        FPR = float(FP) / float(I)
                        performance['performance'] = {
                            "TP": TP,
                            "FP": FP,
                            "TN": TN,
                            "FN": FN,
                            "R": R,
                            "I": I,
                            "TPR": TPR,
                            "FPR": FPR,
                            "TPR/FPR": (TPR/FPR) if FPR!=0 else float("inf")
                        }
                        performances.append(performance)
    
    
    # pick best classifier
    best = 0
    for (i,p) in enumerate(performances):
        if p['performance']['TPR/FPR'] > performances[best]['performance']['TPR/FPR']:
            best = i
    os.remove(SVM_MODEL_FILE)
    os.rename(SVM_MODEL_FILE+str(best), SVM_MODEL_FILE)
    for i in range(len(performances)):
        if i != best:
            os.remove(SVM_MODEL_FILE+str(i))
    
    
    # finish
    print ""
    print ""
    print "TRAINING SUCCEEDED"
    print "saved svm to '" + SVM_MODEL_FILE + "'"
    print performances
