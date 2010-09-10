#!/usr/bin/env python

import sys
import yaml, shelve
import numpy
from copy import deepcopy
from dicts import DefaultDict

######################################################################

POS = "positive"
NEG = "negative"
OBJ = "objective"
MISSING = "missing"
CATS = [POS, NEG, OBJ, MISSING]

AT_LEAST_AS_STRONG = "at least as strong"
STRONGER = "stronger"
WEAKER = "weaker"
EQUAL = "equal"

WN_POS = ('a', 'n', 'r', 'v')

def basic_polarity(word, eval_dict, missingval=None):
    if not word in eval_dict:
        return missingval
    val_dict = eval_dict[word]
    if val_dict[POS] == val_dict[NEG]:
        return OBJ
    elif val_dict[POS] > val_dict[NEG]:
        return POS
    elif val_dict[POS] < val_dict[NEG]:
        return NEG
    else:
        raise Exception("Unrecognized polarity information in %s" % val_dict)

def comparative_polarity(word1, word2, eval_dict):
    pol1 = basic_polarity(word1, eval_dict)
    pol2 = basic_polarity(word2, eval_dict) 
    if pol1 != pol2:
        return None
    else:
        max_val1 = max(eval_dict[word1].values())
        max_val2 = max(eval_dict[word2].values())
        if numpy.abs(max_val1) > numpy.abs(max_val2):
            return STRONGER
        elif numpy.abs(max_val1) < numpy.abs(max_val2):
            return WEAKER
        else:
            return EQUAL

def accuracy(cm, cats):
    correct = sum([cm[cat][cat] for cat in cats])
    total = sum([sum(cm[cat].values()) for cat in cats])
    if total:
        return float(correct) / float(total)
    else:
        return 0.0

def precision(cm, cats):
    p = {}
    for cat in cats:
        tp = cm[cat][cat]
        # base = tp + fp
        base = sum([cm[cat2][cat] for cat2 in cats])
        if base:
            p[cat] = float(tp) / float(base)
        else:
            p[cat] = 0.0
    return p
              
def recall(cm, cats):
    r = {}
    for cat in cats:
        tp = cm[cat][cat]
        # base = tp + fn
        base = sum([cm[cat][cat2] for cat2 in cats])
        if base:
            r[cat] = float(tp) / float(base)
        else:
            r[cat] = 0.0
    return r

def f1(prec, rec, cats):
    f = {}
    for cat in cats:
        num = prec[cat] * rec[cat]
        den = prec[cat] + rec[cat]
        if den:
            f[cat] = (num / den) * 2
        else:
            f[cat] = 0.0
    return f

def micro_average(cm, cats):
    tp = sum([cm[key][key] for key in cats])    
    fp = sum([cm[key1][key2] for key1 in cats for key2 in cats if key1 != key2])
    fn = fp
    tn =  (2 * tp) + fn
    cm_micro = {
        True:  {True: tp, False: fn},
        False: {True: fp, False: tn} }
    return cm_micro
    
    
######################################################################

"""
See http://alias-i.com/lingpipe/docs/api/com/aliasi/classify/ConfusionMatrix.html

cm = {
    'Cabernet': {'Cabernet': 9, 'Syrah': 3, 'Pinot': 0},
    'Syrah':    {'Cabernet': 3, 'Syrah': 5, 'Pinot': 1},
    'Pinot':    {'Cabernet': 1, 'Syrah': 1, 'Pinot': 4} }

print micro_average(cm, ['Cabernet', 'Syrah', 'Pinot'])
"""
