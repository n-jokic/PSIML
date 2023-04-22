# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 17:11:34 2020

@author: Milosh Yokich
"""

import numpy as np

from PIL import Image
try:
        import anfft as _anfft
        # measure == True for self-optimisation of repeat Fourier transforms of 
        # similarly-shaped arrays
        def fftn(A,shape=None):
                if shape != None:
                        A = _checkffttype(A)
                        A = procrustes(A,target=shape,side='after',padval=0)
                return _anfft.fftn(A,measure=True)
        def ifftn(B,shape=None):
                if shape != None:
                        B = _checkffttype(B)
                        B = procrustes(B,target=shape,side='after',padval=0)
                return _anfft.ifftn(B,measure=True)
        def _checkffttype(C):
                # make sure input arrays are typed correctly for FFTW
                if C.dtype == 'complex256':
                        # the only incompatible complex type --> complex64
                        C = np.complex128(C)
                elif C.dtype not in ['float32','float64','complex64','complex128']:
                        # any other incompatible type --> float64
                        C = np.float64(C)
                return C
# Otherwise use the normal scipy fftpack ones instead (~2-3x slower!)
except ImportError:
        from scipy.fftpack import fftn, ifftn

def procrustes(a,target,side='both',padval=0):
        """
        Forces an array to a target size by either padding it with a constant or
        truncating it
 
        Arguments:
                a       Input array of any type or shape
                target  Dimensions to pad/trim to, must be a list or tuple
        """
 
        try:
                if len(target) != a.ndim:
                        raise TypeError('Target shape must have the same number of dimensions as the input')
        except TypeError:
                raise TypeError('Target must be array-like')
 
        try:
                b = np.ones(target,a.dtype)*padval
        except TypeError:
                raise TypeError('Pad value must be numeric')
        except ValueError:
                raise ValueError('Pad value must be scalar')
 
        aind = [slice(None,None)]*a.ndim
        bind = [slice(None,None)]*a.ndim
 
        # pad/trim comes after the array in each dimension
        if side == 'after':
                for dd in xrange(a.ndim):
                        if a.shape[dd] > target[dd]:
                                aind[dd] = slice(None,target[dd])
                        elif a.shape[dd] < target[dd]:
                                bind[dd] = slice(None,a.shape[dd])
 
        # pad/trim comes before the array in each dimension
        elif side == 'before':
                for dd in xrange(a.ndim):
                        if a.shape[dd] > target[dd]:
                                aind[dd] = slice(a.shape[dd]-target[dd],None)
                        elif a.shape[dd] < target[dd]:
                                bind[dd] = slice(target[dd]-a.shape[dd],None)
 
        # pad/trim both sides of the array in each dimension
        elif side == 'both':
                for dd in xrange(a.ndim):
                        if a.shape[dd] > target[dd]:
                                diff = (a.shape[dd]-target[dd])/2.
                                aind[dd] = slice(np.floor(diff),a.shape[dd]-np.ceil(diff))
                        elif a.shape[dd] < target[dd]:
                                diff = (target[dd]-a.shape[dd])/2.
                                bind[dd] = slice(np.floor(diff),target[dd]-np.ceil(diff))
        
        else:
                raise Exception('Invalid choice of pad type: %s' %side)
 
        b[bind] = a[aind]
 
        return b
        
def local_sum(a,tshape):

	# zero-padding
	a = ndpad(a,tshape)

	# difference between shifted copies of an array along a given dimension
	def shiftdiff(a,tshape,shiftdim):
		ind1 = [slice(None,None),]*a.ndim
		ind2 = [slice(None,None),]*a.ndim
		ind1[shiftdim] = slice(tshape[shiftdim],a.shape[shiftdim]-1)
		ind2[shiftdim] = slice(0,a.shape[shiftdim]-tshape[shiftdim]-1)
		return a[tuple(ind1)] - a[tuple(ind2)]
    
	for dd in range(a.ndim):
		a = np.cumsum(a,dd)
		a = shiftdiff(a,tshape,dd)
	return a

def ndpad(a,npad=None):
	
	if npad == None:
		npad = np.ones(a.ndim)
	elif np.isscalar(npad):
		npad = (npad,)*a.ndim
	elif len(npad) != a.ndim:
		raise Exception('Length of npad (%i) does not match the '\
				'dimensionality of the input array (%i)' 
				%(len(npad),a.ndim))
	
	# initialise padded output
	padsize = [a.shape[dd]+2*npad[dd] for dd in range(a.ndim)]
	b = np.ones(padsize,a.dtype)*0

	# construct an N-dimensional list of slice objects
	ind = [slice(int(np.floor(npad[dd])),int(a.shape[dd]+np.floor(npad[dd]))) for dd in range(a.ndim)]
	
	# fill in the non-pad part of the array
	b[tuple(ind)] = a
	return b

def trim(a,target):
	
	b = np.ones(target,a.dtype)*0
	
	aind = [slice(None,None)]*a.ndim
	bind = [slice(None,None)]*a.ndim

	for dd in range(a.ndim):
		if a.shape[dd] > target[dd]:
			diff = (a.shape[dd]-target[dd])/2.
			aind[dd] = slice(int(np.floor(diff)),int(a.shape[dd]-np.ceil(diff)))
		elif a.shape[dd] < target[dd]:
			diff = (target[dd]-a.shape[dd])/2.
			bind[dd] = slice(int(np.floor(diff)),int(target[dd]-np.ceil(diff)))

	b[tuple(bind)] = a[tuple(aind)]

	return b

def ndflip(a):
	ind = (slice(None,None,-1),)*a.ndim
	return a[ind]

def fast_ssd(t,a,af, outdims, ls2_a):
    tf = fftn(ndflip(t),outdims)
 
    # 'non-normalized' cross-correlation
    xcorr = ifftn(tf*af)
 
        # quadratic sum of the template
    tsum2 = np.sum(t**2.)
 
        # now we need to make sure xcorr is the same size as ls2_a
    xcorr = trim(xcorr,ls2_a.shape)
 
        # SSD between template and image
    ssd = ls2_a + tsum2 - 2.*xcorr
 
        # normalise to between 0 and 1
    ssd -= ssd.min()
    ssd /= ssd.max()
 
    return ssd

def find_image(im, tpl):
    im = np.atleast_3d(im)
    tpl = np.atleast_3d(tpl)
    H, W, D = im.shape[:3]
    h, w = tpl.shape[:2]

    # Integral image and template sum per channel
    sat = im.cumsum(1).cumsum(0)
    tplsum = np.array([tpl[:, :, i].sum() for i in range(D)])

    # Calculate lookup table for all the possible windows
    iA, iB, iC, iD = sat[:-h, :-w], sat[:-h, w:], sat[h:, :-w], sat[h:, w:] 
    lookup = iD - iB - iC + iA
    # Possible matches
    possible_match = np.where(np.logical_and.reduce([lookup[..., i] == tplsum[i] for i in range(D)]))

    # Find exact match
    for y, x in zip(*possible_match):
        if np.all(im[y+1:y+h+1, x+1:x+w+1] == tpl):
            return (y+1, x+1)

    return 0, 0


import time
start_time = time.time()
""" Prvo pokrecem jako brz algoritam koji trazi egzaktno poklapanje koristeci osobinu integralnih slika, a ako se poklapanje ne pronadje tada prelazim
    na SSD"""
    
#with open(r'C:\Users\milos\Desktop\PSIML\homework\public_map\inputs\4.txt', "r") as text:       
#           test_case = text.read().splitlines()
#           txt ="C:/Users/milos/Desktop/PSIML/homework/public_map/set/"
#           for i,test in enumerate(test_case):
#               test_case[i] = test.replace(r'@@DATASET_DIR@@/', txt)
            
#map_path = test_case[0]
#number_of_templates = int(test_case[1])
#dimensions = test_case[2].split()

map_path = input()
number_of_templates = int(input())
dimensions = input().split()

dimensions[0] = int(dimensions[0])
dimensions[1] = int(dimensions[1])
dimensions.append(3)

image_fast = Image.open(map_path)
image = np.float64(np.array(image_fast.convert('LA')))

w_2, h_2 = int(image.shape[0]/2), int(image.shape[0]/2)
outdims = np.array([image.shape[dd]+dimensions[dd]-1 for dd in range(image.ndim)])
af = fftn(image,outdims)
ls2_a = local_sum(image**2,(dimensions[0], dimensions[1], 3))


for i in range(number_of_templates):
    template_fast = Image.open(input())
    #template_fast = Image.open(test_case[i+3])
    (y, x)= find_image(np.array(image_fast), np.array(template_fast))
    #x= 0 
    #y = 0
    if x != 0 and y !=0:
        print("{0},{1}".format(x, y))
    else:
        #print('ssd')
        ssd = fast_ssd(np.float64(np.array(template_fast.convert('LA'))), image, af, outdims, ls2_a)
        print("{0},{1}".format(np.nonzero(ssd == ssd.min())[1][0]-dimensions[0]+1, np.nonzero(ssd == ssd.min())[0][0]-dimensions[1]+1))
        
    if ((time.time() - start_time)) >= 19.4:
        for j in range(number_of_templates-i - 1):
            print("{0},{1}".format(w_2, h_2))
        break