#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 1 16:38:34 2023

PJD  1 Aug 2023     - Written to validate binary identical copies of CMIP5 ozone forcing data are written
PJD  3 Aug 2023     - Updated to print to screen - all checkout ok!

@author: durack1
"""

# %% imports
import datetime
import hashlib
import os
import pdb

# %% function defs


def getFileStats(filePath):
    if os.path.isfile(filePath):
        fileStats = os.stat(filePath)
        fileSizeBytes = fileStats.st_size
        fileModTime = datetime.datetime.fromtimestamp(fileStats.st_mtime)
        fileModTime = makeDate(
            fileModTime.year, fileModTime.month, fileModTime.day, False
        )
    else:
        print("File:", filePath, "not a valid file")
        fileSizeBytes = 0.0
        fileModTime = 0.0

    return fileSizeBytes, fileModTime


def getSha256(filePath, print=False):
    with open(filePath, "rb") as f:
        bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(bytes).hexdigest()
        if print:
            print(readable_hash)

    return readable_hash


def makeDate(year, month, day, check):
    date = "-".join([str(year), str(month), str(day)])
    # print("makeDate: date =", date)
    # pdb.set_trace()
    if check:
        date = checkDate(date)

    return date


# old and new dir paths
oldPath = "/p/css03/esgf_publish/cmip3/ipcc/cmip5/ozone/"
newPath = "/p/user_pub/work/input4MIPs/CMIP5/ozone/"

for cmPath in [
    oldPath,
]:
    count = 0
    for root, dirs, files in os.walk(cmPath):
        if files:
            # print("files:", files)
            files.sort()  # sort to process sequentially
            for c1, fileName in enumerate(files):
                print("{:06d}".format(count), "fileName:", fileName)
                for path in [oldPath, newPath]:
                    filePath = os.path.join(oldPath, fileName)
                    print("filePath_1:", filePath)
                    # get sha256, fileSizeBytes, fileModTime
                    sha256_1 = getSha256(filePath)
                    fileSizeBytes_1, fileModTime_1 = getFileStats(filePath)
                    filePath = os.path.join(newPath, fileName)
                    print("filePath_2:", filePath)
                    sha256_2 = getSha256(filePath)
                    fileSizeBytes_2, fileModTime_2 = getFileStats(filePath)
                    # print
                    print("sha256_1:", sha256_1)
                    print("sha256_2:", sha256_2)
                    print("fileSizeBytes_1:", fileSizeBytes_1)
                    print("fileSizeBytes_2:", fileSizeBytes_2)
                    if (sha256_1 != sha256_2) or (fileSizeBytes_1 != fileSizeBytes_2):
                        print("fileName:", fileName, "- inconsistent")
                        pdb.set_trace()

                count = count + 1  # file counter

# Now order values by sha256
