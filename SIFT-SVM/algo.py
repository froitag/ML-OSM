'''
Created on 11.03.2013

@author: andre
'''
from os import unlink
from sklearn.cluster import MiniBatchKMeans
import numpy as np
from glob import glob
from os.path import basename, join, splitext
import scipy.cluster.vq as vq
from sklearn import svm
import cPickle
import numpy
import os

import platform
if platform.system() != 'Darwin':
    from lib.sift.lowe import sift # windows and linux only
else:
    print "vlfeat"
    from lib.sift.vlfeat import sift

BATCH_SIZE=50
KM_N_INIT=10
KM_MAX_NO_IMPROVEMENT=10

SIFTBATCH_EXTENSION="siftbatch"
HISTOGRAMBATCH_EXTENSION="histogrambatch"

EXTENSIONS = [".jpg", ".bmp", ".png", ".pgm", ".tif", ".tiff"]


def extract_features(image_files, DIR_TO_DUMP_TO, batch_size=BATCH_SIZE):
    ''' extract features from all files in `image_files` and dumps them in batches into `DIR_TO_DUMP_TO`'''
    ''' returns total count of features '''
    
    batch = {}
    batchCounter = 0
    imgCounter = 0
    featureCount = 0
    for img in image_files:
        batch[img] = __extract_features_from_image_file(img, sift_tmp_file=DIR_TO_DUMP_TO+"/tmp.sift")
        featureCount += batch[img].shape[0]
        imgCounter += 1
        
        if (imgCounter % batch_size) == 0:
            batchCounter += 1
            with open(DIR_TO_DUMP_TO+"/batch"+str(batchCounter)+"."+SIFTBATCH_EXTENSION, "wb") as f:
                cPickle.dump(batch, f, protocol=cPickle.HIGHEST_PROTOCOL)
            batch = {}
    if batch:
        with open(DIR_TO_DUMP_TO+"/batch"+str(batchCounter+1)+"."+SIFTBATCH_EXTENSION, "wb") as f:
            cPickle.dump(batch, f, protocol=cPickle.HIGHEST_PROTOCOL)

    try:
        os.remove("tmp.pgm")
    except:
        None

    return featureCount


def gen_codebook(sift_features_dir, cluster_count, DUMP_TO_FILE, batch_size=BATCH_SIZE):
    mbk = MiniBatchKMeans(init='k-means++', n_clusters=cluster_count, batch_size=BATCH_SIZE,
                      n_init=KM_N_INIT, max_no_improvement=KM_MAX_NO_IMPROVEMENT, verbose=0)
    
    if batch_size < cluster_count:
        raise Exception("batch_size must be greater than cluster_count!")
    
    files = __get_sift_batches_from_dir(sift_features_dir)
    
    
    batch = []
    i=0
    for sfile in files:
        with open(sfile, "rb") as f:
            siftbatch = cPickle.load(f)
        for imgfile in siftbatch:            
            for feature in siftbatch[imgfile]:
                batch.append(feature)
                i += 1
                
                if (i % batch_size) == 0:
                    mbk.partial_fit(batch)
                    batch = []
    if batch:
        mbk.partial_fit(batch)
        
    with open(DUMP_TO_FILE, 'wb') as f:
        cPickle.dump(mbk.cluster_centers_, f, protocol=cPickle.HIGHEST_PROTOCOL)
        
    return


def compute_histograms(sift_features_dir, codebook_file, DUMP_TO_DIR, batch_size=BATCH_SIZE):
    files = __get_sift_batches_from_dir(sift_features_dir)
    with open(codebook_file, "rb") as f:
        codebook = cPickle.load(f)
    
    batch = {}
    batchCounter = 0
    i=0
    for hfile in files:
        with open(hfile, "rb") as f:
            siftbatch = cPickle.load(f)
        for imgfile in siftbatch:
            if len(siftbatch[imgfile]) > 0:
                histogram = __compute_histogram(codebook, siftbatch[imgfile])
                batch[imgfile] = histogram
                i += 1
                
                if (i % batch_size) == 0:
                    batchCounter += 1
                    with open(DUMP_TO_DIR+"/batch"+str(batchCounter)+"."+HISTOGRAMBATCH_EXTENSION, "wb") as f:
                        cPickle.dump(batch, f, protocol=cPickle.HIGHEST_PROTOCOL)
                    batch = {}
    if batch:
        with open(DUMP_TO_DIR+"/batch"+str(batchCounter+1)+"."+HISTOGRAMBATCH_EXTENSION, "wb") as f:
            cPickle.dump(batch, f, protocol=cPickle.HIGHEST_PROTOCOL)

    return


def train_svm(histogram_dir, all_labels, FILE_TO_DUMP_TO, all_weights=None, C=1000, gamma=1):
    files = __get_histogram_batches_from_dir(histogram_dir)
    
    samples = []
    labels = []
    weights = []
    
    for hfile in files:
        with open(hfile, "rb") as f:
            hbatch = cPickle.load(f)
        for h in hbatch:
            samples.append(hbatch[h])
            labels.append(all_labels[os.path.basename(h)])
            weights.append(all_weights[os.path.basename(h)] if all_weights!=None and h in all_weights else 1)
        
    clf = svm.SVC(kernel='rbf') #kernel='linear'
    clf.C = C    
    clf.gamma = gamma

    clf.fit(samples, labels)#, sample_weight=weights)
    # save the classifier
    with open(FILE_TO_DUMP_TO, 'wb') as fid:
        cPickle.dump(clf, fid)   

def predict(svm_model_file, codebook_file, img_dir, tmp_dir):
    # list all files
    files = get_imgfiles(img_dir)
    
    # extract sift features
    extract_features(files, tmp_dir)
    
    # generate histograms
    compute_histograms(tmp_dir, codebook_file, tmp_dir)
    
    # load svm & predict
    with open(svm_model_file, 'rb') as fid:
        crf = cPickle.load(fid)
    
    predictions = {}
    histogram_files = __get_histogram_batches_from_dir(tmp_dir)
    for hfile in histogram_files:
        with open(hfile, "rb") as f:
            hbatch = cPickle.load(f)
        for img in hbatch:
            predictions[img] = crf.predict(hbatch[img])
            
    # add 0 predictions for images where SIFT didn't find features
    for f in files:
        if not(f in predictions):
            predictions[f] = [0]
    
    return predictions


''' HELPERS '''
def __extract_features_from_image_file(image_file, sift_tmp_file='tmp.sift'):
    sift.process_image(image_file, sift_tmp_file)
    _, descriptors = sift.read_features_from_file(sift_tmp_file)
    unlink(sift_tmp_file)
    return descriptors

def __compute_histogram(codebook, descriptors):
    code, _ = vq.vq(descriptors, codebook)
    histogram_of_words, _ = np.histogram(code,
                                              bins=range(codebook.shape[0] + 1),
                                              normed=True)
    
    if numpy.isnan(histogram_of_words).any():
        print "OH OH"
    return histogram_of_words

def __try_remove(f):
    try:
        os.remove(f)
    except:
        None
    return f

def __try_mkdirs(folder):
    try:
        os.makedirs(folder)
    except:
        None
    return folder
    
def __clear_dir(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e
    return folder

def __get_sift_batches_from_dir(d):
    return __get_files_from_dir(d, SIFTBATCH_EXTENSION)

def __get_histogram_batches_from_dir(d):
    return __get_files_from_dir(d, HISTOGRAMBATCH_EXTENSION)

def __get_files_from_dir(d, extension):
    files = []
    files.extend([join(d, basename(fname)).replace("\\","/")
                    for fname in glob(d + "/*")
                    if splitext(fname)[-1].lower() == "."+extension])
    return files

    
def get_imgfiles(path):
    all_files = []
    all_files.extend([join(path, basename(fname)).replace("\\","/")
                    for fname in glob(path + "/*")
                    if splitext(fname)[-1].lower() in EXTENSIONS])
    return all_files
    