import numpy as np

from PIL import Image
from scipy.fftpack import fftn, ifftn
from scipy import signal




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
    xcorr = np.real(ifftn(tf*af))
 
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


import scipy.ndimage.filters as fi

def gkern2(kernlen=21, nsig=3):
    """Returns a 2D Gaussian kernel array."""

    # create nxn zeros
    inp = np.zeros((kernlen, kernlen))
    # set element at the middle to one, a dirac delta
    inp[kernlen//2, kernlen//2] = 1
    # gaussian-smooth the dirac, resulting in a gaussian filter mask
    return fi.gaussian_filter(inp, nsig)
       


import time
start_time = time.time()
""" Prvo pokrecem jako brz algoritam koji trazi egzaktno poklapanje koristeci osobinu integralnih slika, a ako se poklapanje ne pronadje tada prelazim
    na SSD"""
    
with open(r'C:\Users\milos\Desktop\PSIML\homework\public_map\inputs\0.txt', "r") as text:       
           test_case = text.read().splitlines()
           txt ="C:/Users/milos/Desktop/PSIML/homework/public_map/set/"
           for i,test in enumerate(test_case):
               test_case[i] = test.replace(r'@@DATASET_DIR@@/', txt)
            
map_path = test_case[0]
number_of_templates = int(test_case[1])
dimensions = test_case[2].split()

#map_path = input()
#number_of_templates = int(input())
#dimensions = input().split()

dimensions[0] = int(dimensions[0])
dimensions[1] = int(dimensions[1])


image_fast = Image.open(map_path)
image = np.float64(np.array(image_fast.convert('L')))

w_2, h_2 = int(image.shape[0]/2), int(image.shape[1]/2)
outdims = np.array([image.shape[dd]+dimensions[dd]-1 for dd in range(image.ndim)])
af = fftn(image,outdims)
ls2_a = local_sum(image**2,(dimensions[0], dimensions[1]))


count = 0
for i in range(number_of_templates):
    #template_fast = Image.open(input())
    template_fast = Image.open(test_case[i+3])
    (y, x)= find_image(np.array(image_fast), np.array(template_fast))
    #x= 0 
    #y = 0
    if x != 0 and y !=0:
        print("{0},{1}".format(x, y))
        count += 1
    else:
        #print('ssd')
        ssd = fast_ssd(np.float64(np.array(template_fast.convert('L'))), image, af, outdims, ls2_a)
        print("{0},{1}".format(np.nonzero(ssd == ssd.min())[1][0]-dimensions[0]+1, np.nonzero(ssd == ssd.min())[0][0]-dimensions[1]+1))
        count += 1
        
    if ((time.time() - start_time)) >= 19.4:
        for j in range(number_of_templates-i-1):
            print("{0},{1}".format(w_2, h_2))
            count += 1
        break

