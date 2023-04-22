# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 00:56:00 2020

@author: Milosh Yokich
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 19:09:30 2020

@author: Milosh Yokich
"""


from collections import defaultdict
import json
import time





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
    coeffUpp = (frame - lower)/distance# lower......frame...upper --> coefUpp>coeffLow
   
    
    return [frameDictionary[upper][i]*coeffUpp + frameDictionary[lower][i]*coeffLow for i in range(len(frameDictionary[upper]))]


    
def interpolateFrames(parsed, key, sortedKey):
    
    if len(sortedKey) == sortedKey[-1] - sortedKey[0] + 1: #checking if sortedKey is filled, 
        #if len(sortedKey) == sortedKey[-1] - sortedKey[0] + 1 then we have something like 1 2 3 ... 10
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
        
        if len(parsedJoints[key]) == 0:
            continue
        
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
            if counter == 3:
                break
   
        
        
        
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




def cleanUp(positionMatrix):
    
    case = 1
    while len(positionMatrix)!= 0:
    
        if case == 1 :
            case = findSingularValues(positionMatrix)
            continue
        
        if case == 2:
            case = findNameWithMaxValue(positionMatrix)
            continue
        
    return positionMatrix
    
                


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
            
            if my_dict[key][name] > maximum : #important, equality must be >=! Becaose we are interested in cases like: 1 2 5 and not 1 2 5 5
                maximum = my_dict[key][name]
                maximum_count+=1
                maximum_name = name
                
            if len(my_dict[key]) == 0: #pop key if there are no valid values left
                my_dict.pop(key, None)
                break
                
                
        
                  
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
            
            
    return 2 #magic number :(





def findMax(nameDict):
    maximum = 0
    next_best = 0
    name_max = ''
    for name in nameDict:
        if nameDict[name] >= maximum:
            maximum = nameDict[name]
            name_max = name
            
       
    for name in nameDict:
        if nameDict[name] >= next_best: #important, it has to be >= because next_best can be == maximum, ex. : 1 2 3 3, next best is 3! 
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
                                #score is calculated as next best value in dictionary[B] after we remove box A from joint B
    score_list = list()
    
    for key in list(my_dict.keys()):  #locating where box A has max value in dictioanry[B] for joint B
        next_best, maximum = findMax(my_dict[key])
        try:
            if my_dict[key][find_name] == maximum and maximum != 0:
                score_list.append((key, next_best))
        except KeyError:
            continue
    
    if len(score_list) == 0 : #we are looking for name that has 1 max value at at least 1 joint
        findNameWithMaxValue(my_dict, find_name)
        return
    
    key, minimum = score_list[0] #we are looking for place that has "worst" replacement box
      
    for value in score_list:  
        curr_key, curr_val = value
        if curr_val < minimum:
            minimum = curr_val
            key = curr_key
            
    print("{0}:{1}".format(key, find_name))
    my_dict.pop(key, None)
    removeName(my_dict, find_name)
    
    
    




box_path = input()
with open(box_path, "r") as text:
    boxes = text.read();

joint_path = input() 
with open(joint_path, "r") as text:
    joints = text.read();
    

            

parsedJoints = parsedJoint(json.loads(joints))
parsedBoxes = parsedBox(json.loads(boxes))


positionMatrix = calculatePosMat(parsedJoints, parsedBoxes)
positionMatrix = cleanUp(positionMatrix)



   
                        
                        
                
                
        
        

                
        
            
