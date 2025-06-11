#!/bin/env python
# -*- coding: utf-8 -*-

# import os
# import pdb
import json

"""
Created on Fri Mar 29 09:42:21 2024

This script interrogates a json file containing CMIP3 data paths

PJD 29 Mar 2024 - Initial code, get sorted dates from files
PJD 11 Jun 2025 - Added queries of filename and path lengths; updated to 230723_cmip3.json (was 230703)
"""

f = "230723_cmip3.json"
with open(f, "r") as fH:
    cm3 = json.load(fH)

print(len(cm3.keys()))

## loop through entries
dates = []
lenPath, lenFileName, lenComp = [[0, 0, 0] for _ in range(3)]
for count, key in enumerate(cm3.keys()):
    print(count)
    if "!" in key:
        # skip !_cmorCount, !_fileCount, !bad*
        continue
    elif cm3[key] == {}:
        continue  # '/p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1'
    else:
        fileDict = cm3[key]
        # print(fileDict)
        fileKey = [k for k in fileDict][0]
        date = fileDict[fileKey]["date"][0]
        # print(date)
        dates.append(date)
        # print(dates)
        # ascertain lengths
        lenPath1 = len(key)
        if lenPath1 > lenPath[1]:
            lenPath = [count, lenPath1, key]
        lenFileName1 = len(fileKey)
        if lenFileName1 > lenFileName[1]:
            lenFileName = [count, lenFileName1, fileKey]
        lenComp1 = len(key) + len(fileKey)
        if lenComp1 > lenComp[1]:
            lenComp = [count, lenComp1, key, fileKey]

## sort dates
dates.sort()
print("first:", dates[0])
print("last: ", dates[-1])

# %% print len* info
print("lenPath:    ", lenPath)
print("lenFileName:", lenFileName)
print("lenComp:    ", lenComp)
