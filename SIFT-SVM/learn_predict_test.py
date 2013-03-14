'''
Created on 14.03.2013

@author: andi
'''

from os.path import isdir, basename, join, splitext
import os
from glob import glob
import algo
from numpy import sqrt
from PIL import Image, ImageDraw

PATCH_SIZE = 32
PATCH_OFFSET_STEPS = 1

# lon between 180 E and 180 W
# lat between  90 N and  90 S
#       min lon  min lat   max lon  max lat
#BBOX=(11.60339,48.17708,11.61304,48.18326) ; DOP_SIZE=(1500, 1000); f = 'A'  # between Grasmeier and Crailsheimerstr.
BBOX =(11.59221,48.17038-0.05,11.61233,48.18380-0.05) ; DOP_SIZE=(2000, 2000); f = 'C' # > 4 times areas as above.

#important: a must be smaller than c, b must be smaller then d



#DATASETPATH = 'data/train_real/'
DATASETPATH = '../data/patchesB' + str(PATCH_SIZE) + '-' + str(PATCH_OFFSET_STEPS)
DATASETPATH2 = '../data/patches' + f + str(PATCH_SIZE) + '-' + str(PATCH_OFFSET_STEPS)

SIFT_CODEBOOK = '../data/codebook'
SVM_MODEL_FILE = '../data/svm.pkl'
TMP_DIR = '../data/tmp/train/'#algo.__clear_dir('data/tmp/train/')

EXTENSIONS = [".png"]






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
    import patch_generator

    patch_generator.generate_patches(BBOX, DOP_SIZE,
        patch_size=PATCH_SIZE,
        offset_steps=PATCH_OFFSET_STEPS,
        target_folder=DATASETPATH,
        data_folder='dop' + f,
        force_refresh=False
    )


    try:
        os.makedirs(TMP_DIR)
    except:
        None

    algo.__clear_dir(TMP_DIR)

    cats = [0,1]
    ncats = len(cats)

    print ""
    print "---------------------"
    print "## loading the images and extracting the sift features"

    # list files
    all_files = get_imgfiles(DATASETPATH)
    all_labels = {}
    all_weights = {}
    for i in all_files:
        certainty = float(i.replace("\\","/").rpartition("/")[2].partition("_")[0])
        label = 1 if certainty > 0 else 0
        all_labels[i] = label
        all_weights[i] = certainty if label == 1 else 1-certainty


    # extract features
    featureCount = algo.extract_features(all_files, TMP_DIR)

    # generate codebook
    clusterCount = int(sqrt(featureCount))
    algo.gen_codebook(TMP_DIR, clusterCount, SIFT_CODEBOOK,
                      batch_size = algo.BATCH_SIZE if algo.BATCH_SIZE >= clusterCount else clusterCount)

    # generate histograms
    algo.compute_histograms(TMP_DIR, SIFT_CODEBOOK, TMP_DIR)

    # train svm
    algo.train_svm(TMP_DIR, all_labels, SVM_MODEL_FILE, all_weights = all_weights)

    print "calculating predictions"

    predictions = algo.predict(SVM_MODEL_FILE, SIFT_CODEBOOK, DATASETPATH2, TMP_DIR)


    img = Image.open('dop' +f + '/dop-annotated.png').convert('RGBA')
    overlay = Image.new('RGBA', img.size, 0)
    draw = ImageDraw.Draw(overlay)

    print "\n\nPredictions:"
    for filepath, is_building in predictions.items():
        filename = os.path.basename(filepath)
        coverage, x, y = os.path.splitext(filename)[0].split('_')
        x = int(x); y = int(y)
        #print '{coverage}: {is_building}'.format(coverage=coverage, is_building=is_building[0])
        if is_building[0] == 1:
            draw.rectangle([x,y,x+PATCH_SIZE, y+PATCH_SIZE], fill=(0x8a, 0x2b, 0xe2, 0x55), outline='grey')
        else:
            draw.rectangle([x,y,x+PATCH_SIZE, y+PATCH_SIZE], fill=(0xff, 0xff, 0, 0x55), outline='grey')

    combined = Image.blend(img, overlay, 0.3)
    combined.show()
    combined.save('../prediction_' + f + 'result_' + str(PATCH_SIZE) + '_o=' + str(PATCH_OFFSET_STEPS) + '.png')

    print 'done'
