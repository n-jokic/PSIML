# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 01:19:48 2020

@author: Milosh Yokich
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""





def addToDict(answerDictionary, file, text, code):
    if len(answerDictionary[code]) == 0:
        answerDictionary[code] = [-1,-1]
    
   
    if fnmatch.fnmatch(file, 'ca*.txt'): 
        if text == "Yes" : 
            answerDictionary[code][1] = 1
        elif text == "No":
            answerDictionary[code][1] = 0 
                
    elif fnmatch.fnmatch(file, 'wpa*.txt') :
        answerDictionary[code][0] = int(text[:-1])
        
def countQuestion(question_list):
    PQ = 0
    EQ = 0
    NQ = 0
    EPQ = 0
    ENQ = 0
    if question_list[1] == 1:
        PQ = 1
        
        if question_list[0] != -1:
            EQ=1
            EPQ=1
            
    elif question_list[1] == 0:
        NQ = 1
        
        if question_list[0] != -1:
            EQ=1
            ENQ = 1
        
    return PQ, NQ, EQ, EPQ, ENQ

def predict(question, wisePerson, treshold):
    prediction = 0
    T = 0;
    F = 0;
    
    if(wisePerson >= treshold):
        prediction = 1
     
    if prediction + question == 2:
        T = 1
        return T,F #true positive answer
    
    if prediction + question == 1:
        if question == 0:
            F = 1
            return T,F #flase positive answer
        
        return T,F #other
    return T,F
    
        
def calculate(answerDictionary, Th):
    posQ =0
    negQ =0
    evalQ =0
    evalPQ =0
    evalNQ =0
    TP =0
    FP =0
    for key in answerDictionary:
        ansList = answerDictionary[key]
    
        PQ, NQ, EQ, EPQ, ENQ = countQuestion(ansList)
        posQ += PQ
        negQ += NQ
        evalQ += EQ
        evalPQ += EPQ
        evalNQ += ENQ
    
        T,F = predict(ansList[1], ansList[0], Th)
        TP += T
        FP += F
    return posQ, negQ, evalQ, TP, FP, evalPQ, evalNQ
    

import os
import fnmatch
from collections import defaultdict

answerDictionary = defaultdict(list)


input_path = input()


for root, dirs, files in os.walk(input_path):
     for file in files:
        code = ''.join(x for x in file if x.isdigit())
        
        with open(os.path.join(root, file), "r") as text:
            addToDict(answerDictionary, file, text.readline(4), code)  
            



Th = 70;
posQ, negQ, evalQ, TP, FP, evalPQ, evalNQ = calculate(answerDictionary, Th)

posQ, negQ, evalQ, TP, FP, evalPQ, evalNQ = calculate(answerDictionary, Th)

if evalPQ!=0 and evalNQ!=0 :
    old_TPR = TP / evalPQ
    old_FPR = FP / evalNQ

    
    if old_FPR != 1 - old_TPR:
        left = 0
        right = 100
        mid = 50
        newEER = 0
        FPR = old_FPR
        TPR = old_TPR
        
        while FPR != (1 - TPR ): #binary search
            TP = 0 
            FP = 0
            oldEER = newEER
            for key in answerDictionary:
                ansList = answerDictionary[key]
                T,F = predict(ansList[1], ansList[0], mid)
                TP += T
                FP += F
                
            TPR = TP / evalPQ
            FPR = FP / evalNQ
                
            if FPR > 1 - TPR:
                left = mid
            else:
                right = mid
                        
            mid = (left+right)/2
        
            newEER = FPR
            
            if oldEER == newEER:
                FPR = (oldEER+newEER)/2    
                break
         
        Th = mid
        top = 1000  
        step = (100-mid)/top
        previousTPR,previousFPR = TPR, FPR
        
        for i in range(top): #cheking if we found true maximum
            Th += step
            for key in answerDictionary:
                ansList = answerDictionary[key]
                T,F = predict(ansList[1], ansList[0], Th)
                TP += T
                FP += F
            FPR = FP / evalNQ
            TPR = TP / evalPQ
            if abs(previousTPR+previousFPR - 1) > abs(TPR+FPR - 1):
                previousTPR,previousFPR = TPR, FPR
            else:
                break
            
        
        FPR = previousFPR
        
            
    EER = FPR  
                
    print("{0},{1},{2},{3},{4},{5}".format(posQ, negQ, round(evalQ,3), round(old_TPR,3), round(old_FPR,3), round(EER,3)))
  
else:
    if len(answerDictionary) == 0:
        print(',,,,,')
    else:
        if evalNQ == 0 and evalPQ != 0:
            print("{0},{1},{2},{3},{4},{5}".format(posQ, negQ, evalQ, old_TPR, '', ''))
        if evalNQ != 0 and evalPQ == 0:
            print("{0},{1},{2},{3},{4},{5}".format(posQ, negQ, evalQ, '', old_FPR, ''))
        if evalNQ == 0 and evalPQ == 0:
            print("{0},{1},{2},{3},{4},{5}".format(posQ, negQ, evalQ, '', '', ''))
        

    
    
        