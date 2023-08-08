#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 7 14:20:34 2023

PJD  7 Aug 2023     - Written to collect file information allowing
                      binary identical CMIP3 copies to be excluded
PJD  7 Aug 2023     - Moved function defs to CMIP3Lib
PJD  8 Aug 2023     - Added writeJson function

@author: durack1
"""

# %% imports
import datetime
import numpy as np
import os

# %% function defs
from CMIP3Lib import getFileStats, getSha256, writeJson

# set times
timeNow = datetime.datetime.now()
timeFormatDir = timeNow.strftime("%y%m%d")
timeBegin = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

# set paths
cm3Paths = [
    "/p/css03/esgf_publish/cmip3",
    "/p/css03/scratch/ipcc2_deleteme_July2020",
]

# preallocate
fileDict = {}
fileDict["!_timeBegin"] = timeBegin
count = 0

for cmPath in cm3Paths:
    for root, dirs, files in os.walk(cmPath):
        if files:
            # print("files:", files)
            files.sort()  # sort to process sequentially
            for c1, fileName in enumerate(files):
                # catch erroneous files
                if fileName == "listing_20080409.txt":
                    print("badFile:", "listing_20080409.txt", "skipping")
                    continue
                filePath = os.path.join(root, fileName)
                print("filePath:", filePath)
                # get sha256, fileSizeBytes, fileModTime
                sha256 = getSha256(filePath)
                fileSizeBytes, fileModTime = getFileStats(filePath)
                # print
                print(
                    "{:06d}".format(count),
                    "sha256:",
                    sha256,
                    "fileSizeBytes:",
                    fileSizeBytes,
                )
                # add file entry to dictionary
                fileDict[sha256] = {}
                fileDict[sha256][filePath] = {}
                fileDict[sha256][filePath]["fileSizeBytes"] = fileSizeBytes
                fileDict[sha256][filePath]["fileModTime"] = fileModTime
                count = count + 1  # file counter

            # write json if count
            if ~np.mod(count, 10):
                writeJson(fileDict, "cmip3-sha256", timeFormatDir)

# cleanup
timeEnd = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
fileDict["!_timeEnd"] = timeEnd
writeJson(fileDict, "cmip3-sha256", timeFormatDir)
