#!/bin/env python
# -*- coding: utf-8 -*-

import os
import pdb
import json

"""
Created on Fri Mar 29 09:42:21 2024

PJD 29 Mar 2024    - Initial code, get sorted dates from files
"""

f = "230703_cmip3.json"
with open(f, "r") as fH:
    cm3 = json.load(fH)

print(len(cm3.keys()))

## loop through entries
dates = []
for count, key in enumerate(cm3.keys()):
    print(count)
    if "!" in key:
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

## sort dates
dates.sort()
print("first:", dates[0])
print("last: ", dates[-1])
