
import scipy

import numpy as np
from  scipy import ndimage
from PIL import Image
from scipy.fftpack import fftn, ifftn

import matplotlib.pyplot as plt


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
    
	if a.shape == target:
		return a
	
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

def fast_ssd(t,af, outdims, ls2_a):
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



def buildImagePyramid( im, dimensions ):
    
	images = []
	pind = [] 
	step = 1

    
	count = 0
	while min(int(dimensions[0]/step), int(dimensions[1]/step)) >= 10 and count < 1: # Stop building the pyramid when the image is too small
        
         
		count +=1
		step *= 2
		pind.append(im.shape)
		images.append(im)
    
		lopassedIm = 2*ndimage.filters.gaussian_filter(im, 1)

		# Downsample lowpassed image

		lopassedIm = lopassedIm[0:lopassedIm.shape[0]:2,0:lopassedIm.shape[1]:2]
        
		# Recurse on the lowpassed image

		im = lopassedIm
        

        
       

	# Add a residual level for the remaining low frequencies
	

	images.append(im)
	pind.append(im.shape)

	return (images, pind)
		


import time
start_time = time.time()
""" Prvo pokrecem jako brz algoritam koji trazi egzaktno poklapanje koristeci osobinu integralnih slika, a ako se poklapanje ne pronadje tada prelazim
    na SSD"""
    
with open(r'C:\Users\milos\Desktop\PSIML\homework\public_map\inputs\8.txt', "r") as text:       
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
plt.close('all')




(images, pind) = buildImagePyramid(image, dimensions) #We are building Gaussian image pyramid
plt.figure()
plt.imshow(images[0])
plt.figure()
plt.imshow(images[1])





w_2, h_2 = int(image.shape[0]/2), int(image.shape[0]/2)



count = 0


################ FIRST PASS ################################### 
test, printed =0,0
#template_fast = Image.open(input())
template_fast = Image.open(test_case[+3])
(y, x)= find_image(np.array(image_fast), np.array(template_fast))
 
if x != 0 and y !=0:
    print("{0},{1}".format(x, y))
    count += 1
    printed+=1
else:
    image = images[-1]
    
    (templates, tind) = buildImagePyramid(np.float64(np.array(template_fast.convert('L'))), dimensions) #We are building Gaussian image pyramid
        
 
    
        
    first_outdims = np.array([image.shape[dd]+ tind[-1][dd] -1 for dd in range(image.ndim)])
    first_fft = fftn(np.float64(image), first_outdims)
        
    k = len(tind) #len(tind) <= len(pind)!!!
    
    last_fft = first_fft
    outdims = first_outdims
        
    x_left = 0
    x_right = 0
    y_left = 0
    y_right = 0
        
    if k  > 1:
            
        ls2_a = local_sum(image**2,(tind[k - 1][1], tind[k - 1][0]))           
        ssd = fast_ssd(templates[k - 1], last_fft, outdims, ls2_a)
        
        (y_approx, x_approx) = (np.nonzero(ssd == ssd.min())[0][0], np.nonzero(ssd == ssd.min())[1][0])
            
        
        w, h = int(1.5*tind[k  -2][1]), int(1.5*tind[k -2][0])
        x_lim, y_lim = pind[k  - 2][1], pind[k - 2][0]
                       
        x_left = 2*x_approx - w
        if x_left < 0 :
            x_left = 0
            
        x_right = 2*x_approx  + w
        if x_right >=  x_lim:
            x_right = x_lim - 1
            
        y_left = 2*y_approx  - h
        if y_left < 0:
                y_left = 0
                
        y_right = 2*y_approx  + h
        if y_right >= y_lim :
            y_right = y_lim
            
            
        
        image = images[k - 2][y_left:y_right, x_left:x_right]
        outdims = np.array([image.shape[dd] + tind[k - 2][dd] - 1 for dd in range(image.ndim)])
        last_fft = fftn(image,outdims)
            
        ls2_a = local_sum(image**2,(dimensions[1], dimensions[0]))     
        ssd = fast_ssd(templates[0], last_fft, outdims, ls2_a)
        print("{0},{1}".format(np.nonzero(ssd == ssd.min())[1][0] + x_left - dimensions[1] + 1, np.nonzero(ssd == ssd.min())[0][0]+y_left - dimensions[0]))
        printed+=1   
      






############# SECOND PASS ####################33

for i in range(number_of_templates - 1):
    #template_fast = Image.open(input())
    template_fast = Image.open(test_case[i+3])
    (y, x)= find_image(np.array(image_fast), np.array(template_fast))

    if x != 0 and y !=0:
        print("{0},{1}".format(x, y))
        count += 1
        printed+=1
    else:
        
        image = images[-1]
        (templates, tind) = buildImagePyramid(np.float64(np.array(template_fast.convert('L'))), dimensions) #We are building Gaussian image pyramid

        
        outdims = first_outdims
        last_fft = first_fft
        
        x_left = 0
        x_right = 0
        y_left = 0
        y_right = 0
        
        if k > 1 :
            
            ls2_a = local_sum(image**2,(tind[k - 1][1], tind[k - 1][0]))           
            

            ssd = fast_ssd(templates[k - 1], last_fft, outdims, ls2_a)
        
            (y_approx, x_approx) = (np.nonzero(ssd == ssd.min())[0][0], np.nonzero(ssd == ssd.min())[1][0])
            
        
            w, h = int(1.5*tind[k  -2][1]), int(1.5*tind[k -2][0])
            x_lim, y_lim = pind[k  - 2][1], pind[k - 2][0]
                       
            x_left = 0
            x_right = 0
            y_left = 0
            y_right = 0
            x_left = 2*(x_approx + x_left) - w
            if x_left < 0 :
                x_left = 0
                
            x_right = 2*(x_approx + x_right) + w
            if x_right >=  x_lim:
                x_right = x_lim - 1
                
            y_left = 2*(y_approx + y_left) - h
            if y_left < 0:
                y_left = 0
                
            y_right = 2*(y_approx + y_right) + h
            if y_right >= y_lim :
                y_right = y_lim
                
            
            
            image = images[k - 2][y_left:y_right, x_left:x_right]
            outdims = np.array([image.shape[dd] + tind[k - 2][dd] - 1 for dd in range(image.ndim)])
            last_fft = fftn(image,outdims)
            
        ls2_a = local_sum(image**2,(dimensions[1], dimensions[0]))     
        ssd = fast_ssd(templates[0], last_fft, outdims, ls2_a)

        
        
        print("{0},{1}".format(np.nonzero(ssd == ssd.min())[1][0] + x_left - dimensions[1] + 1, np.nonzero(ssd == ssd.min())[0][0]+y_left - dimensions[0]))
        printed+=1
      
        
    if ((time.time() - start_time)) >= 3.4:
        for j in range(number_of_templates-i-2):
            print("{0},{1}".format(w_2, h_2))
            test +=1
        break
    
print(test, printed, 'num of temp', number_of_templates)
