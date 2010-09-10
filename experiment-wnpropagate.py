#!/usr/bin/env python

from wnpropagate import *
import yaml, pickle, shelve
import sys
import csv
import numpy
import random
#sys.path.append("../evaluation/")
from evaluator import *

POS = "positive"
NEG = "negative"
OBJ = "objective"
MISSING = "missing"

######################################################################

# WN_ROOT = "/Volumes/CHRIS/Downloads/WordNet-2.0/dict/"
WN_ROOT = "/Volumes/CHRIS/Documents/data/corpora/nltk_data/corpora/wordnet/"

def run():

    output_shelve_filename = "wnpropagate-tags-results.shelve"

    # Seed sets.
    turney_littman_positive = ["excellent", "good", "nice", "positive", "fortunate", "correct", "superior"]
    turney_littman_negative = ["nasty","bad", "poor", "negative", "unfortunate", "wrong", "inferior"]
    objective = ["administrative", "financial", "geographic", "constitute", "analogy", "ponder",
                 "material", "public", "department", "measurement", "visual"]

    # Synsets.
    synsets_list = [
        create_seed_synsets(turney_littman_positive, pos='a'),
        create_seed_synsets(turney_littman_negative, pos='a'),
        create_seed_synsets(objective) ]

    # micro = yaml.load(file('goldstandards/micrownop-combined-synsets.yaml'))

    negative = ["trouble.n.04", "ugly.a.01", "sadness.n.01", "neutralize.v.04", "icky.s.01", "asshole.n.01", "affliction.n.01", "atrocious.s.03"]
    positive = ["able.s.02", "benevolent.a.03", "cozy.s.01", "interest.v.01", "majestic.s.01", "polish.n.02", "progress.v.01", "safety.n.01"]
    objective = ["together.r.02", "shark.n.01", "rhythm.n.01", "hundred.n.01", "augment.v.01", "federal.a.02", "subsequent.a.01", "term.v.01", "yield.n.02"]

    corpus_reader = nltk.corpus.WordNetCorpusReader(WN_ROOT)

    positive = map((lambda x : corpus_reader.synset(x)), positive)
    negative = map((lambda x : corpus_reader.synset(x)), negative)
    objective = map((lambda x : corpus_reader.synset(x)), objective)
    
    synsets_list = [positive, objective, negative] 
    t = wordnet_sense_propagate(synsets_list, 20)

    all_iterations = shelve.open(output_shelve_filename)
    
    # pos_list, neg_list, and obj_list each contain the seed sets as
    # their 0th elements, and then 20 more elements, for a total
    # length of 21.  Store the results in the dictionary format used
    # for evaluation.
    for i in range(0,21):
        print "\t", i

        positive = t[0][i]
        objective = t[1][i]
        negative = t[2][i]
        
#         d = {}
#         for synset in positive:
#             d[synset.name] = {POS:1.0, NEG:0.0}
#         for synset in negative:
#             d[synset.name] = {POS:0.0, NEG:1.0}
#         for synset in objective:
#             d[synset.name] = {POS:0.0, NEG:0.0}

        d = {}
        for synset in positive:
            for lemma in synset.lemmas:
                d[(lemma.name, synset.pos)] = {POS:1.0, NEG:0.0}
        for synset in negative:
            for lemma in synset.lemmas:
                d[(lemma.name, synset.pos)] = {POS:0.0, NEG:1.0}
        for synset in objective:
            for lemma in synset.lemmas:
                d[(lemma.name, synset.pos)] = {POS:0.0, NEG:0.0}
        
        all_iterations[str(i)] = d
    # Close the database.
    all_iterations.close()

run()

#evaluate("wnpropagate-results-micrownop.shelve", yaml.load(file('goldstandards/micrownop-combined-synsets.yaml'))

         
         
    
