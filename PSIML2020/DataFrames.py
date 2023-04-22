# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 19:09:30 2020

@author: Milosh Yokich
"""


import os
import fnmatch
from collections import defaultdict
import json
import time
import numpy as np


def isInside(boxPosition, jointPosition):
    if len(boxPosition) == 0:
        return 0
    
    if boxPosition[2] < jointPosition[0]: #check if Xbox < Xdot, Xbox = left corner of box
        if boxPosition[3] < jointPosition[1]: #check if Ybox > Ydot, Ydot = left corner of box
            if (boxPosition[2] + boxPosition[1]) > jointPosition[0]: #check if Xbox + width > Xdot, Xbox = left corner of box
                if (boxPosition[3] + boxPosition[0]) > jointPosition[1]: #check if Ybox - height < Ydot, Ydot = left corner of box
                    return 1
    return 0

def findFrame(i, frame, sortedKeyBox):
    
    if i >= len(sortedKeyBox): #iterator i helps us find the position of upper and lower bound
        i = len(sortedKeyBox) -1
        
    if sortedKeyBox[i] == frame:
        return frame, frame
    
    if(frame > sortedKeyBox[i]):
        lower = sortedKeyBox[i]
        
        while frame > sortedKeyBox[i]:
            lower = sortedKeyBox[i]
            if lower == sortedKeyBox[-1]: #there exists no valid upper frame
                return -1, -1
            i += 1
        
        upper = sortedKeyBox[i]
       
        
    if(frame < sortedKeyBox[i]):
        upper = sortedKeyBox[i]
        
        while frame < sortedKeyBox[i]:
            if i == 0 :#there exists no valid lower frame
                return -1, -1
            i-=1
            
        lower = sortedKeyBox[i]
        upper = sortedKeyBox[i+1]
        
    return upper, lower

def interpolation(upper, lower, frame, frameDictionary):
    distance = upper - lower
    coeffLow = (upper - frame)/distance
    coeffUpp = (frame - lower)/distance
   
    
    return [frameDictionary[upper][i]*coeffUpp + frameDictionary[lower][i]*coeffLow for i in range(len(frameDictionary[upper]))]
    
def interpolateFrames(parsed, key, sortedKey):
    
    if len(sortedKey) == 0:
        return 'False'
    
    if len(sortedKey) == sortedKey[-1] - sortedKey[0] + 1:
        return 'False'
    
    for i, value in enumerate(sortedKey):
        i+=1
        
        if i == len(sortedKey):
            break
        
        if - sortedKey[i-1] + sortedKey[i] != 1:
            middle_frame = sortedKey[i-1]+int((-sortedKey[i-1] + sortedKey[i])/2)     
            parsed[key][middle_frame] = interpolation(sortedKey[i], sortedKey[i-1], middle_frame, parsed[key])
    
    return 'True'
        

def calculatePosMat(parsedJoints, ParsedBoxes):
    
    positionMatrix = defaultdict(dict)
    for key in parsedJoints:
        for name in parsedBoxes:
            positionMatrix[key][name] = 0
            
    for key in parsedJoints:
        start_time = time.time()
        
        
        condition = 'True'
        
        counter = 0
        while condition:
            counter+=1
            sortedKeyJ = sorted(parsedJoints[key].keys())
            condition = interpolateFrames(parsedJoints, key, sortedKeyJ)
            if time.time() - start_time > 0.5:
                condition = 'False'
            if condition == 'False':
                break
            if counter == 2:
                break
   
        
        if len (sortedKeyJ) == 0:
            continue
        
        for name in parsedBoxes:
            sortedKeyB = sorted(parsedBoxes[name].keys())
            
            if len(sortedKeyB) == 0:   
                continue
        
            for i, frame in enumerate(sortedKeyJ):
                upper, lower = findFrame(i, frame, sortedKeyB)
                
                if upper == -1: 
                    continue
            
                if upper != lower: #if upper == lower then parsedBoxes[name][frame] already exists
                    parsedBoxes[name][frame] = interpolation(upper, lower, frame, parsedBoxes[name])
            
                positionMatrix[key][name] += isInside(parsedBoxes[name][frame], parsedJoints[key][frame])
            
    return positionMatrix


def parsedJoint(joints):
    parsedJoints = defaultdict(dict)
    
    for frame in joints['frames']:
        for joint in frame['joints']:
            parsedJoints[joint['identity']][frame['frame_index']] = [joint['joint']['x'], joint['joint']['y']];
    return parsedJoints

def parsedBox(boxes): 
    parsedBoxes = defaultdict(dict)
    
    for frame in boxes['frames']:
        for box in frame['bounding_boxes']:
            parsedBoxes[box['identity']][frame['frame_index']] = [box['bounding_box']['h'], box['bounding_box']['w'],box['bounding_box']['x'], box['bounding_box']['y']];
    return parsedBoxes

def cleanUp(posMat):
    
    for key in list(posMat):
        maximum = 0
        key_max = '0'
        name_max = '0'
        for key2 in list(posMat):
            for name in list(posMat[key2]):
                if posMat[key2][name] > maximum:
                    maximum = posMat[key2][name]
                    key_max = key2
                    name_max = name
                    
        if maximum == 0:
            continue
        posMat[key_max][name_max] = -1
        
        for name in list(posMat[key_max]):
            if name != name_max:
                posMat[key_max][name] = -2
                
        for key2 in list(posMat):
            for name in list(posMat[key2]):
                if name == name_max:
                    if key2 != key_max:
                        posMat[key2][name] =-2
    return posMat
                


def findSingularValues(my_dict):
    
    for key in list(my_dict.keys()):
        
        if len(my_dict[key]) == 0: #pop key if there are no valid values left
            my_dict.pop(key, None)
            continue
        
        maximum = 0
        maximum_count = 0
        maximum_name = ''
        
        for name in list(my_dict[key].keys()):
            
            if my_dict[key][name] == 0: 
                my_dict[key].pop(name, None) #we are clearing matrix from 0 values
                continue
            
        if len(my_dict[key]) == 0: #pop key if there are no valid values left
            my_dict.pop(key, None)
            break
            
            if my_dict[key][name] > maximum :
                maximum = my_dict[key][name]
                maximum_count+=1
                maximum_name = name
                  
        if len(my_dict[key]) == 1: #Singular values have priority
            find_name = list(my_dict[key].keys())[0]
            print("{0}:{1}".format(key, find_name))
            my_dict.pop(key, None)
            removeName(my_dict, find_name)
            continue
        
        if maximum_count == 1:
            print("{0}:{1}".format(key, maximum_name))
            my_dict.pop(key, None)
            removeName(my_dict, maximum_name)
            continue
            
            
    return 2

def findMax(nameDict):
    maximum = 0
    next_best = 0
    name_max = ''
    for name in nameDict:
        if nameDict[name] >= maximum:
            maximum = nameDict[name]
            name_max = name
            
       
    for name in nameDict:
        if nameDict[name] >= next_best:
            if name != name_max:
                next_best = nameDict[name]
            
    return next_best, maximum

def removeName(my_dict, name):
    for key in list(my_dict.keys()):
        for find_name in list(my_dict[key].keys()):
            if name == find_name:
                my_dict[key].pop(name, None)
                
            if len(my_dict[key]) == 0:
                return
                
                
def findNameWithMaxValue(my_dict, avoid = ''):
    
    if len(my_dict) == 0: #return 3 means that we are ending the loop
        return 3
    
    for key in list(my_dict.keys()):
        for name in list(my_dict[key].keys()):
            if avoid != name:
                pairUp(my_dict, name)
                return 1
            

def pairUp(my_dict, find_name): #we are looking for joints where find_name has max value and then calculating "score" for each place
    
    score_list = list()
    
    for key in list(my_dict.keys()):
        next_best, maximum = findMax(my_dict[key])
        try:
            if maximum != 0:
                if my_dict[key][find_name] == maximum:
                    score_list.append((key, next_best))
        except KeyError:
            continue
    
    if len(score_list) == 0 : #we are looking for name that has 1 max value at at least 1 joint
        findNameWithMaxValue(my_dict, find_name)
        return
    
    key, minimum = score_list[0]
      
    for value in score_list:  
        curr_key, curr_val = value
        if curr_val < minimum:
            minimum = curr_val
            key = curr_key
            
    print("{0}:{1}".format(key, find_name))
    my_dict.pop(key, None)
    removeName(my_dict, find_name)
    
def filterFrames(box_dict, joint_dict):
    k = 3.9
    
    for key in list(joint_dict.keys()):
        std_x = 0
        std_y = 0
        frame_list = sorted(list(joint_dict[key].keys()))
        d = len(frame_list)
        
        mean_x = 0
        mean_y = 0
        
        if d <= 1:
            continue
        
        
        for frame in frame_list:
            mean_x +=joint_dict[key][frame][0]
            mean_y +=joint_dict[key][frame][1]
            
        mean_x/=d
        mean_y/=d
        
        for frame in frame_list:
            std_x  += (joint_dict[key][frame][0]-mean_x)**2
            std_y += (joint_dict[key][frame][1]-mean_y)**2
            
        std_x = np.sqrt(std_x/(d-1))
        std_y = np.sqrt(std_y/(d-1))
        
        if len(frame_list) > 1:
            prev = joint_dict[key][frame_list[0]]
            for frame in frame_list[1::]:
                if abs(prev[0] - joint_dict[key][frame][0]) >k*std_x:
                    joint_dict[key].pop(frame, None)
                    continue
                if abs(prev[1] - joint_dict[key][frame][1])>k*std_y:
                    joint_dict[key].pop(frame, None)
                    continue
                    prev = joint_dict[key][frame]
                    
        
    for name in list(box_dict.keys()):
        std_w = 0
        std_h = 0
        std_x = 0
        std_y = 0
        
        mean_x = 0
        mean_y = 0
        mean_h = 0
        mean_w = 0
        
        frame_list = sorted(list(box_dict[name].keys()))
        d = len(frame_list)
        
        if d <= 1:
            continue
        
       
        
        for frame in frame_list:
            mean_h +=box_dict[name][frame][0]
            mean_w +=box_dict[name][frame][1]
            mean_x +=box_dict[name][frame][2]
            mean_y +=box_dict[name][frame][3]
            
        mean_x/=d
        mean_y/=d
        mean_h/=d
        mean_w/=d
        
        for frame in frame_list:
            std_h += (box_dict[name][frame][0]-mean_h)**2
            std_w += (box_dict[name][frame][1]-mean_w)**2
            std_x += (box_dict[name][frame][2]-mean_x)**2
            std_y += (box_dict[name][frame][3]-mean_y)**2
        
        std_x = np.sqrt(std_x/(d-1))
        std_y = np.sqrt(std_y/(d-1))
        std_w = np.sqrt(std_w/(d-1))
        std_h = np.sqrt(std_h/(d-1))
            
            
        if len(frame_list) > 1:
            prev = box_dict[name][frame_list[0]]
            for frame in frame_list[1::]:
                if abs(prev[0] - box_dict[name][frame][0]) >k*std_h:
                    box_dict[name].pop(frame, None)
                    continue
                if abs(prev[1] - box_dict[name][frame][1])>k*std_w:
                    box_dict[name].pop(frame, None)
                    continue
                if abs(prev[2] - box_dict[name][frame][2]) >k*std_x:
                    box_dict[name].pop(frame, None)
                    continue
                if abs(prev[3] - box_dict[name][frame][3])>k*std_y:
                    box_dict[name].pop(frame, None)
                    continue
                prev = box_dict[name][frame]
        

        
    

    
with open(r'C:\Users\milos\Desktop\PSIML\homework\public\inputs\14.txt', "r") as text:
    test_case = text.read().splitlines()
    txt =r"C:\Users\milos\Desktop\PSIML\homework\public\set"
    for i,test in enumerate(test_case):
        test_case[i] = test.replace(r'@@DATASET_DIR@@', txt)

#box_path = input()  
box_path = test_case[0]
with open(box_path, "r") as text:
    boxes = text.read();
#joint_path = input()  
joint_path = test_case[1]
with open(joint_path, "r") as text:
    joints = text.read();
            

parsedJoints = parsedJoint(json.loads(joints))
parsedBoxes = parsedBox(json.loads(boxes))






positionMatrix = calculatePosMat(parsedJoints, parsedBoxes)

for x in positionMatrix:
    for y in positionMatrix[x]:
        if positionMatrix[x][y] != 0:
            print('(' + str(x) + ', ' + str(y) + ')' + ': '+ str(positionMatrix[x][y]))

#positionMatrix = cleanUp(positionMatrix)

case = 1
while len(positionMatrix)!= 0:
    
    if case == 1 :
        case = findSingularValues(positionMatrix)
        continue
    
    if case == 2:
        case = findNameWithMaxValue(positionMatrix)
        continue

"""
#interpolation testing

import matplotlib.pyplot as plt
import matplotlib



plt.close('all')

KEY = '0'
NAME = 'B'
filterFrames(parsedBoxes, parsedJoints)

x_j_old = []
y_j_old =[]
for key in parsedJoints:    
    if key != KEY:
            continue
    sortedKeyJ_old = sorted(parsedJoints[key].keys())
    break
for name in parsedBoxes:
    if name != NAME:
            continue
    sortedKeyB_old = sorted(parsedBoxes[name].keys())
    break





for i in sortedKeyJ_old: 
    for key in parsedJoints:  
        if key != KEY:
            continue
        x_j_old.append(parsedJoints[key][i][0])
        y_j_old.append(parsedJoints[key][i][1])
        break

x_b_old=[]
y_b_old=[]
for i in sortedKeyB_old:
    for name in parsedBoxes:
        if name != NAME:
            continue
        x_b_old.append(parsedBoxes[name][i][2])
        y_b_old.append(parsedBoxes[name][i][3])
        break






for key in parsedJoints:   
    if key != KEY:
            continue
    sortedKeyJ = sorted(parsedJoints[key].keys())
    break
for name in parsedBoxes:
    if name != NAME:
            continue
    sortedKeyB= sorted(parsedBoxes[name].keys())
    break

    
 







x_j = []
y_j =[]
for i in sortedKeyJ:
    
    for key in parsedJoints: 
        if key != KEY:
            continue
        x_j.append(parsedJoints[key][i][0])
        y_j.append(parsedJoints[key][i][1])
        break

x_b=[]
y_b=[]
for i in sortedKeyB:
    for name in parsedBoxes:
        if name != NAME:
            continue
        x_b.append(parsedBoxes[name][i][2])
        y_b.append(parsedBoxes[name][i][3])
        break

fig=plt.figure(figsize=(10,8))

size = 1.5
ax1 = plt.subplot(2,2,1)
ax2 = plt.subplot(2,2,2)
ax3 = plt.subplot(2,2,3)
ax4 = plt.subplot(2,2,4)
ax1.title.set_text('x_j')
ax2.title.set_text('y_j')
ax3.title.set_text('x_b')
ax4.title.set_text('y_b')

ax1.plot(sortedKeyJ, x_j, markersize =size, color = 'b')
ax2.plot(sortedKeyJ, y_j, markersize =size, color = 'b')   


ax3.plot(sortedKeyB, x_b, markersize =size, color = 'b')
ax4.plot(sortedKeyB, y_b, markersize =size, color = 'b')  


ax1.plot(sortedKeyJ_old, x_j_old,'ro',markersize=size, color = 'r')
ax2.plot(sortedKeyJ_old, y_j_old,'ro', markersize=size, color = 'r')
  

ax3.plot(sortedKeyB_old, x_b_old, 'ro',markersize=size, color = 'r')
ax4.plot(sortedKeyB_old, y_b_old,'ro',markersize=size, color = 'r') 

fig.suptitle('('+str(KEY) + ':' + str(NAME) + ')')
plt.show()
 """   
    
    

    
                        
                        
                        
                
                
        
        

                
        
            
