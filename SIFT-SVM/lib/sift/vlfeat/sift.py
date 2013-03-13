from PIL import Image
import os
import numpy as np
from pylab import *


def process_image(imagename,resultname,params="--edge-thresh 10 --peak-thresh 5"):
	""" process an image and save the results in a file"""

	if imagename[-3:] != 'pgm':
		#create a pgm file
		im = Image.open(imagename).convert('L')
		im.save('tmp.pgm')
		imagename = 'tmp.pgm'

	cmmd = str("lib\\sift\\vlfeat\\bin\\sift.exe "+imagename+" --output="+resultname+
				" "+params)
	cmmd = str("lib/sift/vlfeat/bin/maci64/sift "+imagename+" --output="+resultname+" "+params)
	print cmmd
	os.system(cmmd)
	print 'processed', imagename, 'to', resultname


def read_features_from_file(filename):
	""" read feature properties and return in matrix form"""
	f = np.loadtxt(filename)
	try:
		ret = f[:,:4],f[:,4:] # feature locations, descriptors
	except:
		ret = np.array([]),np.array([])
	return ret


def write_features_to_file(filename,locs,desc):
	""" save feature location and descriptor to file"""
	np.savetxt(filename,np.hstack((locs,desc)))


def match(desc1,desc2):
	""" for each descriptor in the first image, 
		select its match in the second image.
		input: desc1 (descriptors for the first image), 
		desc2 (same for second image). """
	
	desc1 = np.array([d/np.linalg.norm(d) for d in desc1])
	desc2 = np.array([d/np.linalg.norm(d) for d in desc2])
	
	dist_ratio = 0.6
	desc1_size = desc1.shape
	
	matchscores = np.zeros((desc1_size[0],1))
	desc2t = desc2.T #precompute matrix transpose
	for i in range(desc1_size[0]):
		dotprods = np.dot(desc1[i,:],desc2t) #vector of dot products
		dotprods = 0.9999*dotprods
		#inverse cosine and sort, return index for features in second image
		indx = np.argsort(np.arccos(dotprods))
		
		#check if nearest neighbor has angle less than dist_ratio times 2nd
		if np.arccos(dotprods)[indx[0]] < dist_ratio * np.arccos(dotprods)[indx[1]]:
			matchscores[i] = int(indx[0])
	
	return matchscores


def appendimages(im1,im2):
	""" return a new image that appends the two images side-by-side."""
	
	#select the image with the fewest rows and fill in enough empty rows
	rows1 = im1.shape[0]    
	rows2 = im2.shape[0]
	
	if rows1 < rows2:
		im1 = np.concatenate((im1,np.zeros((rows2-rows1,im1.shape[1]))), axis=0)
	elif rows1 > rows2:
		im2 = np.concatenate((im2,np.zeros((rows1-rows2,im2.shape[1]))), axis=0)
	#if none of these cases they are equal, no filling needed.
	
	return np.concatenate((im1,im2), axis=1)



def match_twosided(desc1,desc2):
	""" two-sided symmetric version of match(). """
	
	matches_12 = match(desc1,desc2)
	matches_21 = match(desc2,desc1)
	
	ndx_12 = matches_12.nonzero()[0]
	
	#remove matches that are not symmetric
	for n in ndx_12:
		if matches_21[int(matches_12[n])] != n:
			matches_12[n] = 0
	
	return matches_12

