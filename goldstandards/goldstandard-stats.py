#!/usr/bin/env python

from dicts import DefaultDict
import csv
import yaml

POS = "positive"
NEG = "negative"
OBJ = "objective"

def to_csv(d,output_filename):
    w = csv.writer(file(output_filename, 'w'))
    w.writerow(["Word", "Tag", "Index", "Polarity", "Positive", "Negative", "Objective"])
    rows = []
    for key, val_dict in d.iteritems():
        word = ""
        tag = ""
        index = ""
        if len(key) == 2:
            word, tag = key
        else:
            fields = key.split(".")
            word, tag, index = fields[0:3]
        if tag == "s":
            tag = "a"
        polarity = basic_polarity(val_dict)
        objective = 1.0 - (val_dict[POS] + val_dict[NEG])
        rows.append([word, tag, index, polarity, val_dict[POS], val_dict[NEG], objective])
    w.writerows(rows)

def by_sentiment_and_pos_table(d):
    tbl = by_sentiment_and_pos(d)
    s = format_tabular(tbl)
    return s

def by_sentiment_and_pos(d):
    tbl = DefaultDict(DefaultDict(0))
    for key, val_dict in d.iteritems():
        fields = key.split(".")
        word, tag, index = fields[0:3]
        polarity = basic_polarity(val_dict)
        tbl[tag][polarity] += 1
    return tbl
        
def basic_polarity(val_dict):
    if val_dict[POS] > val_dict[NEG]:
        return POS
    elif val_dict[POS] < val_dict[NEG]:
        return NEG
    else:
        return OBJ

def format_tabular(tbl):
    s = "\\begin{tabular}[t]{r r r r}\n"
    s += " & " + " & ".join(["Positive", "Negative", "Objective"]) + "\\\\\n"
    for tag in sorted(tbl.keys()):
        row = [tag]
        for polarity in (POS, NEG, OBJ):
            row.append(tbl[tag][polarity])
        s += " & ".join(map(str, row)) + "\\\\\n"
    s += "\\end{tabular}"
    return s


    

tags = yaml.load(file('micrownop-combined-tags.yaml'))
lemmas = yaml.load(file('micrownop-combined-lemmas.yaml'))
synsets = yaml.load(file('micrownop-combined-synsets.yaml'))
to_csv(tags, 'micrownop-combined-tags.csv')
to_csv(lemmas, 'micrownop-combined-lemmas.csv')
to_csv(synsets, 'micrownop-combined-synsets.csv')

