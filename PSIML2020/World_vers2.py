# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 23:02:34 2020

@author: Milosh Yokich
"""
import numpy as np
from PIL import Image

def find_image(im, tpl, th):
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
       
 
    



with open(r'C:\Users\milos\Desktop\PSIML\homework\public_map\inputs\0.txt', "r") as text:
            test_case = text.read().splitlines()
            txt ="C:/Users/milos/Desktop/PSIML/homework/public_map/set/"
            for i,test in enumerate(test_case):
                test_case[i] = test.replace(r'@@DATASET_DIR@@/', txt)
import time
start_time = time.time()
               
map_path = test_case[0]
number_of_templates = int(test_case[1])
dimensions = test_case[2]


#map_path = input()
image = Image.open(map_path)
#number_of_templates = int(input())
#dimensions = input()
image = np.array(image)
loc_list = []


x = 0
y = 0
th = 1
counter = 0
image_path_list = []

for i in range(number_of_templates): 
    #image_path = input()
    #image_path_list.append(input())
    template = np.array(Image.open(test_case[i+3]))
    y, x = find_image(image, template, th)
    if x == 0 and y ==0 :
        counter+=1
    print(str(x)+ ','+str(y))
    if counter == 5: #algoriam vrv vise ne radi zbog zasumljenih slika
        break
    
print("--- %s seconds ---" % (time.time() - start_time))
    
        
   