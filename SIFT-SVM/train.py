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
import json


''' CONFIG '''
IMG_BBOX=(11.60339,48.17708,11.61304,48.18326) ; IMG_SIZE=(1500, 1000) ; IMG_NAME="dopA" # between Grasmeier and Crailsheimerstr.
#IMG_BBOX =(11.59221,48.17038,11.61233,48.18380) ; IMG_SIZE=(2000, 2000) ; IMG_NAME="dopB" # bigger as above.
#important: a must be smaller than c, b must be smaller then d


TMP_DIR_TRAINING = '../data/tmp/train'
TMP_DIR_VALIDATION = '../data/tmp/validate'

DATASET_DIR = '../data/patches'
TRAININGSET_DIR = DATASET_DIR + "/train"
VALIDATIONSET_DIR = DATASET_DIR + "/validate"

SIFT_CODEBOOK_FILE = '../data/codebook'
SVM_MODEL_FILE = '../data/svm.pkl'
HYPERPARAMETERS_FILE = '../data/svm.pkl.info.json'



"""HYPERPARAMETERS_OPTIONS = {
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
"""
HYPERPARAMETERS_OPTIONS = {
    "patch_size": [48],
    "patch_offset": [1],
    "codebook_size": [          # codebook size depending on overall sift key-point count
        lambda n: int(sqrt(n))
     ],
    "svm_c": [1000],
    "svm_gamma": [1]
}



''' HELPERS '''
def parse_arguments():
    parser = argparse.ArgumentParser(description='train a visual bag of words model')
    parser.add_argument('-d', help='path to the dataset', required=False, default=DATASET_DIR)
    args = parser.parse_args()
    return args
def __gen_info_filename(i, performance):
    return SVM_MODEL_FILE+str(i)+"-"+("{0:.2f}".format(performance['performance']["TPR/FPR"]))+".info.json"



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
            print "## generating patches from '" + IMG_NAME + "' (" + str(IMG_SIZE[0])+"x"+str(IMG_SIZE[1]) + "; " + str(IMG_BBOX) + ")"
            patch_generator.generate_patches(IMG_BBOX, IMG_SIZE,
                patch_size=hyperparameters['patch_size'], 
                offset_steps=hyperparameters['patch_offset'],
                target_folder=DATASET_DIR,
                force_refresh=False,
                data_folder=IMG_NAME
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
                        try:
                            os.rename(f, DATASET_DIR + "/" + os.path.basename(f))
                        except:
                            print "ERROR, file already exists: " + f + " -> " + DATASET_DIR + "/" + os.path.basename(f)
                    
        
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
                    try:
                        os.rename(f, (TRAININGSET_DIR if forTraining else VALIDATIONSET_DIR) + "/" + os.path.basename(f))
                    except:
                        print "ERROR, file already exists: " + f + " -> " + (TRAININGSET_DIR if forTraining else VALIDATIONSET_DIR) + "/" + os.path.basename(f)
                    i += 1 if forTraining else 0
                validation_files = algo.get_imgfiles(VALIDATIONSET_DIR)
        
                for j in range(i, trainingset_size):
                    index = j - i
                    try:
                        os.rename(validation_files[index], TRAININGSET_DIR + "/" + os.path.basename(validation_files[index]))
                    except:
                        print "ERROR, file already exists: " + validation_files[index] + " -> " + TRAININGSET_DIR + "/" + os.path.basename(validation_files[index])
            
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
                currentCodebook = SIFT_CODEBOOK_FILE+str(len(performances))
                clusterCount = hyperparameters['codebook_size'](featureCount)
                hyperparameters['codebook_size'] = clusterCount
                performance['codebook_size'] = clusterCount
                algo.gen_codebook(
                                  TMP_DIR_TRAINING, 
                                  clusterCount,
                                  currentCodebook,
                                  batch_size = algo.BATCH_SIZE if algo.BATCH_SIZE >= clusterCount else clusterCount)
                print "saved codebook to '" + currentCodebook + "'"
                performance['codebook'] = currentCodebook
                
                
                # generate histograms
                print "---------------------"
                print "## generating histograms of the training examples"
                algo.compute_histograms(
                                        TMP_DIR_TRAINING,
                                        currentCodebook,
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
                        predictions = algo.predict(SVM_MODEL_FILE+str(len(performances)), currentCodebook, VALIDATIONSET_DIR, TMP_DIR_VALIDATION)
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
                        
                        with open(__gen_info_filename(len(performances), performance), "w") as f:
                            f.write(json.dumps(performance))
                            
                        performances.append(performance)
    
    
    # pick best classifier
    best = 0
    for (i,p) in enumerate(performances):
        if p['performance']['TPR/FPR'] > performances[best]['performance']['TPR/FPR']:
            best = i
    print ""
    print ""
    print "FINISHED"
    print "found best classifier: #" + str(best) + " out of " + str(len(performances))
    print "dataset size: " + str(performances[best]['trainingset_size']) + " training + " + str(performances[best]['validationset_size']) + " validation = " + str(performances[best]['dataset_size']) + " total"
    print "hyper-parameters: " + str(performances[best]['hyperparameters'])
    
    algo.__try_remove(SVM_MODEL_FILE)
    os.rename(SVM_MODEL_FILE+str(best), SVM_MODEL_FILE)
    algo.__try_remove(SIFT_CODEBOOK_FILE)
    os.rename(performances[best]['codebook'], SIFT_CODEBOOK_FILE)
    algo.__try_remove(HYPERPARAMETERS_FILE)
    os.rename(__gen_info_filename(best, performances[best]), HYPERPARAMETERS_FILE)
    """for i in range(len(performances)):
        if i != best:
            algo.__try_remove(SVM_MODEL_FILE+str(i))
            algo.__try_remove(performances[i]['codebook'])
            algo.__try_remove(__gen_info_filename(i, performances[i]))"""
    
    
    # finish
    print ""
    print ""
    print "TRAINING SUCCEEDED"
    print "saved codebook to '" + SIFT_CODEBOOK_FILE + "'"
    print "saved svm to '" + SVM_MODEL_FILE + "'"
    print "saved hyperparameters etc to '" + HYPERPARAMETERS_FILE + "'"
    print performances
